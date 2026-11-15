"""Centre-overlay detector - the DeviantArt semi-transparent watermark.

ROADMAP `cleaning-detector-recall`. The recall census (2026-08-11,
`docs/_archive/2026-08/CLEAN_DETECTOR_RECALL_2026-08-11.md`) measured 14 false negatives over the
302 unrouted firstdones and found **11 of them are one object**: the DA centre
overlay - the site's logo plus `(C) NAME.DEVIANTART.COM`, alpha-composited over
the middle of the frame.

WHY A NEW DETECTOR RATHER THAN A LOWER THRESHOLD. That census also measured why
the existing stack cannot see it:
  * YOLO scores it 0.11-0.25 against a 0.35 detect floor, and TWO of the misses
    carry no box at any confidence - so it is partly a model limitation, not a
    threshold one;
  * EasyOCR returns garble for low-alpha text over busy art, so
    `is_watermark_text` never sees "deviantart";
  * its centroid is mid-frame, so every geometry rule in the gate would answer
    `qa` even if it were boxed.
Dropping the conf floor was measured to be the wrong lever: a low-conf box is a
good FLAG (13 of 17 low-conf `clean` images are real misses) but a bad AUTO
signal, and precision over the gated corpus is currently 0 false positives in 14
proposals (`docs/_archive/2026-08/CLEAN_DETECTOR_PRECISION_2026-08-11.md`).

WHAT IT EXPLOITS INSTEAD. The overlay is the SAME pixels at the SAME place on
every image the site serves. Median-stacking the high-pass of images that carry
it cancels the art and leaves the mark: measured on the corpus, the stack of the
11 positives renders the logo and the URL legibly, while the stack of 8
negatives renders nothing. So:

    template = median over marked frames of (luma - local mean), in the band
    score    = zero-mean normalized correlation of one frame's high-pass
               against that template, over the template's own support

Correlation is amplitude-normalised, which is the property that matters here:
the mark's alpha varies with the background it sits on, but its SHAPE does not.

The score FLAGS to `qa` and never routes to `auto` - see `gate_decision` in
`lw_clean_pass.py` and the invariants pinned in `tests/test_lw_clean_overlay.py`.

Pure numpy + PIL. No cv2, no torch, no GPU, so the whole thing runs in CI. The
estimated template is a derivative of a third party's watermark, so it is
CACHED UNDER `ops/runtime/` (gitignored) and rebuilt from the local corpus - it
is never tracked in this public repo.
"""
from __future__ import annotations

import os
import sys
import warnings

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lw_clean_pass import _box_mean, _to_gray  # noqa: E402

# The overlay sits at a fixed relative height. Measured over the corpus: every
# detected DA mark centroid lands at y/h ~ 0.69 (precision census) and the
# stacked template's structure spans roughly 0.60-0.72. The band is deliberately
# wider than that so a site tweak does not silently fall out of frame.
BAND = (0.55, 0.85)
# Keep the strongest 2 percent of template pixels as its support. The mark is a
# thin, sparse glyph set: correlating over the whole band would drown it in the
# residual art the median did not fully cancel.
SUPPORT_PCT = 98.0
HP_WIN = 9
# The mark is low-amplitude; clip so one hard art edge cannot dominate.
CLIP_LEVELS = 8.0
# Shift-search half-window, as a fraction of the FRAME (not the band): +-43px
# vertically and +-41px horizontally at 2560x1440. Both are measured - see
# overlay_score. They are separate constants because the band is only 30 percent
# of the frame's height, so one shared fraction would make the vertical window
# 6px and drop a real positive whose mark sits 33px off.
SHIFT_FRAC_Y = 0.030
SHIFT_FRAC_X = 0.016
# REMOVAL-ONLY scale registration (2026-08-12). The overlay is composited at a
# fixed size on the DA-served image, and a firstdone is that image resampled to
# 2560x1440 - so a frame whose source was a different resolution carries the
# mark at a different PIXEL size, which no shift can align. Measured over every
# flagged slug under 0.25 plus 110-cleanup: exactly two are mismatched, both at
# the SAME 1.12 (110-cleanup 0.1090 -> 0.5052, 122 0.1696 -> 0.6542), and both
# land in the range the well-registered frames occupy. Everything else peaks at
# 1.00. The grid is modest and centred on native; 1.12 must stay in it.
SCALE_GRID = (0.88, 0.92, 0.96, 1.00, 1.04, 1.08, 1.12, 1.16, 1.20)
# A non-native scale is accepted only when it is DECISIVE - see accept_scale.
SCALE_ACCEPT_RATIO = 2.0

# Removal knobs. MEDIAN_SIZE must exceed the mark's stroke width (~5px at
# 2560x1440) so the seed background loses the text but keeps the painting.
MEDIAN_SIZE = 15
MATTE_ITERS = 3              # regression <-> background re-estimate rounds
ALPHA_MAX = 0.95             # 1/(1-a) is singular at a = 1
ALPHA_FLOOR = 0.02           # below this, leave the pixel alone entirely
SUPPORT_DILATE = 9           # grow the template support to cover the alpha ramp
# Model-fit gates on the per-pixel regression. A pixel only gets an alpha if its
# cross-frame variation is real (VAR_FLOOR), is actually explained by the
# matting model (R2_FLOOR), and yields one alpha all three channels agree on.
VAR_FLOOR = 4.0              # levels^2 of background variation across frames
R2_FLOOR = 0.5
CHANNEL_SPREAD_MAX = 0.25
OPEN_SIZE = 3                # speck-removal opening on the recovered matte
# The mark's colour. Held CONSTANT on purpose - see _w_map for the measurement
# that killed the per-pixel version. The corpus overlay is near-white.
W_REF = (250.0, 250.0, 250.0)
# Gains searched by _fit_gain. The measured optimum on the corpus is 2.0, well
# inside the grid, so the fit is choosing rather than saturating.
GAIN_GRID = (0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 3.0)

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE_PATH = os.path.join(
    _ROOT, "ops", "runtime", "clean", "overlay_template.npz")
MATTE_PATH = os.path.join(
    _ROOT, "ops", "runtime", "clean", "overlay_matte.npz")

# REMOVAL needs a WIDER band than DETECTION does, and the difference is measured:
# BAND starts at 0.55h, but the DA logo's top edge sits at y/h ~ 0.506 on
# mecha-ahri (2560x1440: row 728 vs the band's row 792). Detection does not care -
# the credit line alone separates positives from art - but removal does: the
# clipped 64 rows are a flat semi-transparent veil the matting inversion never
# touches, and it stays legible after the pre-pass. The detector's BAND is
# CALIBRATED and pinned by tests (threshold 0.15 was measured on it), so removal
# gets its own band + its own cached pair rather than moving that constant.
REMOVAL_BAND = (0.45, 0.85)
WIDE_TEMPLATE_PATH = os.path.join(
    _ROOT, "ops", "runtime", "clean",
    "overlay_template_wide.npz")
WIDE_MATTE_PATH = os.path.join(
    _ROOT, "ops", "runtime", "clean", "overlay_matte_wide.npz")


def highpass(image, win: int = HP_WIN):
    """Luma minus its local mean - the same primitive the gate already uses."""
    arr = np.asarray(image, dtype=np.float64)
    g = _to_gray(arr)
    return g - _box_mean(g, win)


def band_of(arr2d, band=BAND):
    """The horizontal slice of a 2D array the overlay lives in."""
    h = arr2d.shape[0]
    return arr2d[int(h * band[0]):int(h * band[1]), :]


def _resize2d(arr2d, shape, nearest=False):
    """Resize a 2D float/bool array to `shape` (h, w) via PIL."""
    mode = Image.NEAREST if nearest else Image.BILINEAR
    src = np.asarray(arr2d)
    im = Image.fromarray(src.astype(np.float32), mode="F")
    out = im.resize((int(shape[1]), int(shape[0])), mode)
    res = np.asarray(out, dtype=np.float64)
    return res > 0.5 if nearest else res


def scale2d_centered(arr2d, s: float):
    """PURE: rescale a 2D array by `s` about its centre, keeping its shape.

    Scaling UP crops the overflow, scaling DOWN pads with zero. Bool arrays stay
    bool (nearest), so a support or a mask survives the trip. s == 1.0 returns
    the input untouched, which is what keeps the scale-1.0 arm of
    `best_registration` bit-identical to the old translation-only path.
    """
    src = np.asarray(arr2d)
    if float(s) == 1.0:
        return src
    is_bool = src.dtype == bool
    h, w = src.shape
    nh, nw = max(int(round(h * s)), 1), max(int(round(w * s)), 1)
    res = _resize2d(src, (nh, nw), nearest=is_bool)
    out = np.zeros((h, w), dtype=bool if is_bool else np.float64)
    if nh >= h and nw >= w:
        oy, ox = (nh - h) // 2, (nw - w) // 2
        out[:, :] = res[oy:oy + h, ox:ox + w]
        return out
    ch, cw = min(nh, h), min(nw, w)
    sy, sx = max((nh - h) // 2, 0), max((nw - w) // 2, 0)
    dy, dx = max((h - nh) // 2, 0), max((w - nw) // 2, 0)
    out[dy:dy + ch, dx:dx + cw] = res[sy:sy + ch, sx:sx + cw]
    return out


def _scale_tpl(tpl, s):
    """A template rescaled about the band centre (template + support together)."""
    if float(s) == 1.0:
        return tpl
    return {"template": scale2d_centered(np.asarray(tpl["template"],
                                                    dtype=np.float64), s),
            "support": scale2d_centered(np.asarray(tpl["support"], dtype=bool), s),
            "band": tpl["band"], "n": tpl.get("n", 0)}


def accept_scale(scaled_score, native_score,
                 ratio: float = None) -> bool:
    """Is a non-native scale DECISIVE enough to register at?

    Frames that are correctly registered at 1.00 still wobble under a scale
    search - measured, at most 1.22x the native score (270f, 0.1548 -> 0.1889 at
    0.94) - while the two genuinely mismatched frames come in at 3.86x and 4.63x.
    So the gate sits at 2.0, far from both, and a refusal keeps scale 1.0: a
    wrong scale is a wrong edit, a refused one is only today's behaviour.

    A non-positive native score makes the ratio meaningless, so it never accepts.
    """
    ratio = SCALE_ACCEPT_RATIO if ratio is None else ratio
    if float(native_score) <= 0.0:
        return False
    return float(scaled_score) >= float(native_score) * float(ratio)


def best_registration(image, tpl, scales=None, max_shift=None, ratio=None):
    """(score, dy, dx, scale) - registration for REMOVAL, not for the gate.

    `best_shift` aligns translation only. Two frames in the flagged family carry
    the overlay at a different PIXEL SIZE and no shift can align them:
    `110-cleanup` 0.1090 -> 0.5052 and `122` 0.1696 -> 0.6542, both at 1.12,
    both landing in the range the well-registered frames already occupy. Every
    other flagged frame under 0.25 peaks at 1.00.

    THIS IS DELIBERATELY NOT WIRED INTO `overlay_score`. Measured on the top of
    the clean population, a max-over-scales lifts `wallpapersden-...-sejuani`
    from 0.1213 to 0.1537, over the 0.15 flag - a false positive manufactured by
    the search, the same lesson the shift window learned. Detection keeps the
    tight window; only removal, which runs on frames already judged to carry the
    mark, gets to look for the scale.
    """
    if not tpl:
        return (0.0, 0, 0, 1.0)
    scales = SCALE_GRID if scales is None else scales
    native = _correlate(image, tpl, max_shift)
    best, best_s = native, 1.0
    for s in scales:
        if float(s) == 1.0:
            continue
        cand = _correlate(image, _scale_tpl(tpl, s), max_shift)
        if cand[0] > best[0]:
            best, best_s = cand, float(s)
    if best_s != 1.0 and not accept_scale(best[0], native[0], ratio):
        return (native[0], native[1], native[2], 1.0)
    return (best[0], best[1], best[2], best_s)


def estimate_template(images, band=BAND, support_pct: float = SUPPORT_PCT):
    """Median high-pass of frames that carry the mark -> {template, support, band}.

    Every frame is reduced to its band, resized to the FIRST frame's band shape
    so a mixed-resolution corpus still stacks, then median-combined. The median
    (not the mean) is what makes one bright artwork unable to invent structure.
    """
    stack = []
    ref = None
    for im in images:
        b = band_of(highpass(im), band)
        if ref is None:
            ref = b.shape
        elif b.shape != ref:
            b = _resize2d(b, ref)
        stack.append(b)
    if not stack:
        raise ValueError("estimate_template needs at least one image")
    med = np.median(np.stack(stack), axis=0)
    thr = float(np.percentile(np.abs(med), support_pct))
    support = np.abs(med) >= max(thr, 1e-9)
    return {"template": med, "support": support, "band": tuple(band),
            "n": len(stack)}


def _cross_correlate(a, b):
    """Circular cross-correlation of two same-shape arrays (FFT, numpy only)."""
    return np.fft.irfft2(np.fft.rfft2(a) * np.conj(np.fft.rfft2(b)), s=a.shape)


def best_shift(image, tpl, max_shift=None):
    """(score, dy, dx) - the correlation peak and where it sat.

    Removal needs the WHERE as much as the whether: the matte is estimated in
    template coordinates, so each frame's mark has to be registered before the
    matting equation is inverted, or the reconstruction subtracts the mark from
    the wrong pixels. Integer pixels only for now; the R&D plan's sub-pixel
    alignment (section 3 item 2) is not implemented.
    """
    return _correlate(image, tpl, max_shift)


def overlay_score(image, tpl, max_shift=None) -> float:
    """Best masked normalized correlation of an image against the template.

    Returns a value in [-1, 1]; 0.0 for a flat frame, a missing template, or an
    empty support. The template is resized to the image's band when the frame
    size differs, so nothing here hard-codes 2560x1440.

    WHY A SHIFT SEARCH. The overlay's ABSOLUTE position moves between images
    even though its relative geometry is fixed: a firstdone is a crop plus a
    downscale of a source whose aspect ratio varies, so the mark lands a few
    dozen pixels off. Measured leave-one-ARTIST-out over the corpus positives:
    with no search the weakest positive scored -0.02 (indistinguishable from
    clean art); with the search it scores 0.100 while the strongest of 15
    reviewed clean frames reaches 0.071.

    The window is deliberately TIGHT (`SHIFT_FRAC` of the frame). Widening it to
    +-90px/+-200px was measured to lift the clean frames to 0.095 - a wider
    search buys the negatives more chances to find a lucky alignment than it
    buys the positives.

    Values are clipped to +-`CLIP_LEVELS` first. The mark is a LOW-amplitude
    structure; without the clip a single hard art edge inside the support
    dominates the correlation (measured: clipping lifts the positive median
    from 0.112 to 0.220 leave-one-artist-out).
    """
    return _correlate(image, tpl, max_shift)[0]


def _correlate(image, tpl, max_shift=None):
    """Shared core of overlay_score / best_shift -> (score, dy, dx)."""
    if not tpl:
        return (0.0, 0, 0)
    b = band_of(highpass(image), tpl["band"])
    t = np.asarray(tpl["template"], dtype=np.float64)
    s = np.asarray(tpl["support"], dtype=bool)
    if t.shape != b.shape:
        t = _resize2d(t, b.shape)
        s = _resize2d(s, b.shape, nearest=True)
    m = s.astype(np.float64)
    n = float(m.sum())
    if n <= 0:
        return (0.0, 0, 0)
    # Clip the IMAGE only. Clipping the template too looks symmetric and is a
    # bug: a strong template saturates to a constant on its own support, its
    # variance goes to zero and the correlation collapses to exactly 0.0. Found
    # by a synthetic fixture whose planted mark is far stronger than the real
    # overlay - on the corpus the template's values are a few levels, so the
    # clip never bit and the bug stayed invisible.
    x = np.clip(b, -CLIP_LEVELS, CLIP_LEVELS)
    if float(np.abs(x).max()) <= 1e-9:
        return (0.0, 0, 0)

    tm = t * m
    sum_t = float(tm.sum())
    den_t = max(float((t * t * m).sum()) - sum_t * sum_t / n, 1e-9)
    s1 = _cross_correlate(x, m)
    s2 = _cross_correlate(x * x, m)
    sxt = _cross_correlate(x, tm)
    num = sxt - s1 * (sum_t / n)
    den_x = np.maximum(s2 - s1 * s1 / n, 1e-9)
    ncc = num / np.sqrt(den_x * den_t)

    h, w = x.shape
    band = tpl["band"]
    frame_h = h / max(float(band[1]) - float(band[0]), 1e-6)
    fy, fx = (SHIFT_FRAC_Y, SHIFT_FRAC_X) if max_shift is None else (
        max_shift, max_shift)
    dy = np.fft.fftfreq(h, 1.0 / h).astype(int)
    dx = np.fft.fftfreq(w, 1.0 / w).astype(int)
    ky = np.abs(dy) <= max(1, int(fy * frame_h))
    kx = np.abs(dx) <= max(1, int(fx * w))
    win = ncc[np.ix_(ky, kx)]
    if win.size == 0:
        return (0.0, 0, 0)
    iy, ix = np.unravel_index(int(np.argmax(win)), win.shape)
    return (float(win[iy, ix]), int(dy[ky][iy]), int(dx[kx][ix]))


# ==========================================================================
# REMOVAL: recover (W, alpha) from the collection, then invert I = (1-a)J + aW
# ==========================================================================
def _fill_masked_columns(band_rgb, mask):
    """Background seed: erase the masked pixels and interpolate ACROSS COLUMNS.

    A median filter was the obvious seed and is the recorded failure of R&D
    method 4 - "alpha underestimated (median bg contaminated by dense text)".
    Inside a dense text line every pixel in the window is mark, so the median IS
    the mark and the regression sees no signal to fit. Interpolating from the
    nearest UNMASKED pixels cannot be contaminated that way - the seed never
    contains a mark pixel by construction.

    Down the COLUMNS, not along the rows: this mark is a text line, ~30px tall
    and ~1000px wide, so a row-wise fill has to bridge a thousand pixels of
    unknown art while a column-wise fill bridges thirty. Measured on the
    synthetic fixture, the row-wise seed biased alpha ~20 percent LOW.
    """
    out = np.array(band_rgb, dtype=np.float64, copy=True)
    h, w = mask.shape
    ys = np.arange(h)
    for x in range(w):
        m = mask[:, x]
        if not m.any():
            continue
        good = ~m
        if not good.any():
            continue
        for c in range(out.shape[-1]):
            out[m, x, c] = np.interp(ys[m], ys[good], band_rgb[good, x, c])
    return out


def _median_filter(band_rgb, size: int = MEDIAN_SIZE):
    """Median-filtered copy of a float RGB band - a first guess at the art.

    The mark's strokes are a few pixels wide, so a median wider than a stroke
    erases them while keeping the painting's structure. This is only the SEED:
    the R&D table records that a median background alone underestimates alpha
    where the text is dense (method 4), which is why estimate_matte iterates.
    """
    from PIL import ImageFilter
    u8 = np.clip(np.rint(band_rgb), 0, 255).astype(np.uint8)
    im = Image.fromarray(u8, mode="RGB").filter(ImageFilter.MedianFilter(size))
    return np.asarray(im, dtype=np.float64)


def _dilate_bool(mask, size: int = SUPPORT_DILATE):
    """Grow a boolean mask by `size` pixels (PIL MaxFilter, no cv2 needed)."""
    u8 = (np.asarray(mask, dtype=bool) * 255).astype(np.uint8)
    im = Image.fromarray(u8, mode="L").filter(
        __import__("PIL.ImageFilter", fromlist=["ImageFilter"]).MaxFilter(size))
    return np.asarray(im) > 127


def _open_bool(mask, size: int = OPEN_SIZE):
    """Morphological opening (erode then dilate) of a boolean mask, PIL only."""
    from PIL import ImageFilter
    u8 = (np.asarray(mask, dtype=bool) * 255).astype(np.uint8)
    im = Image.fromarray(u8, mode="L")
    im = im.filter(ImageFilter.MinFilter(size)).filter(
        ImageFilter.MaxFilter(size))
    return np.asarray(im) > 127


def _alpha_shape(stack_i, stack_j, w_ref):
    """Median over the collection of (I - J) / (W - J) - the matte's SHAPE.

    Per frame this ratio IS alpha wherever the model holds; the median over the
    collection is what kills each frame's seed error, which is the noise that
    defeated a per-pixel least-squares fit on the real corpus (its R^2 came out
    at 0.10 - the model explained a tenth of the cross-frame variation, so any
    R^2 gate either dropped 93 percent of the mark or let art through).

    The result is a SHAPE, not a calibrated alpha: this estimator is known to
    read low (R&D method 4, "alpha underestimated"), which `_fit_gain` corrects
    with one measured global factor.
    """
    num = stack_i - stack_j
    den = np.maximum(w_ref[None, None, None, :] - stack_j, 1.0)
    per_channel = np.median(np.clip(num / den, -0.2, 0.98), axis=0)
    return np.clip(per_channel.mean(axis=-1), 0.0, 1.0)


def _fit_gain(shape, region, frames, tpl, w_ref, gains=GAIN_GRID):
    """Pick the global alpha gain that best silences the DETECTOR.

    The estimator recovers the mark's shape reliably and its amplitude only up
    to a constant, so one scalar is fitted rather than assumed - and it is
    fitted against the thing that defines success: how loudly the overlay
    detector still fires after removal. Measured on the 15-frame corpus
    collection, mean post-removal score by gain: 1.0 -> 0.258, 1.5 -> 0.133,
    2.0 -> 0.120, 2.5 -> 0.141, 3.0 -> 0.166. A clear interior optimum, which is
    itself evidence the shape is right and only its scale was off.
    """
    best = (float("inf"), 1.0)
    for g in gains:
        alpha = np.where(region, np.clip(shape * g, 0.0, ALPHA_MAX), 0.0)
        matte = {"alpha": alpha, "W": _w_map(alpha, w_ref),
                 "band": tuple(tpl["band"]), "n": len(frames)}
        scores = []
        for arr, dy, dx in frames:
            cleaned, _ = remove_overlay(arr, matte, shift=(dy, dx))
            scores.append(overlay_score(cleaned.astype(np.float64), tpl))
        mean = float(np.mean(scores)) if scores else float("inf")
        if mean < best[0]:
            best = (mean, float(g))
    return best[1], best[0]


def _w_map(alpha, w_ref):
    """The mark's colour as a full map - constant, and deliberately so.

    Estimating W PER PIXEL is the textbook next step and was measured to
    DIVERGE on this corpus: alpha and W trade off (only their product is
    identifiable without a prior), so re-solving W per pixel and re-fitting drove
    the mean post-removal score 0.149 -> 0.174 -> 0.254 over three rounds while W
    drifted from ~154 to ~87. Dekel's answer is the matting-Laplacian plus IRLS
    priors that pin alpha independently; until that exists, one reference colour
    plus a fitted gain is the stable half of the model. Removing more than the
    detector can still see is not something this data supports.
    """
    return np.broadcast_to(np.asarray(w_ref, dtype=np.float64),
                           alpha.shape + (3,)).copy()


def estimate_matte(images, tpl=None, w_ref=W_REF, alpha_floor=ALPHA_FLOOR):
    """Recover {alpha, W} for the shared overlay from a collection of frames.

    Four steps, each one measured rather than assumed:

      1. REGISTER every frame to the template (`best_shift`). Pooling an
         unregistered collection is the plateau the R&D plan calls its "biggest
         missing piece".
      2. SEED the background by interpolating across the mark's own region, so
         no seed pixel can contain the mark (see `_fill_masked_columns`).
      3. SHAPE the matte as the median of (I-J)/(W-J) over the collection - the
         median is what survives per-frame seed error.
      4. FIT one global gain against the detector's own score (`_fit_gain`),
         because this estimator recovers the shape well and the amplitude only
         up to a constant.

    Outside the template's (dilated) support alpha is forced to zero, so removal
    can only ever touch pixels the detector says carry the mark. The returned
    dict carries `gain` and `score` so a later run can see what was fitted and
    how loud the detector still was.
    """
    band = tuple(tpl["band"]) if tpl else BAND
    frames, bands = [], []
    for im in images:
        arr = np.asarray(im, dtype=np.float64)
        dy = dx = 0
        if tpl is not None:
            _sc, dy, dx = best_shift(arr, tpl)
        frames.append((arr, dy, dx))
        b = band_of(arr, band)
        if dy or dx:
            b = np.roll(b, (-dy, -dx), axis=(0, 1))
        bands.append(b)
    if not bands:
        raise ValueError("estimate_matte needs at least one image")

    stack_i = np.stack(bands)
    if tpl is not None:
        support = np.asarray(tpl["support"], dtype=bool)
        if support.shape != stack_i.shape[1:3]:
            support = _resize2d(support, stack_i.shape[1:3], nearest=True)
        region = _dilate_bool(support)
    else:
        region = np.ones(stack_i.shape[1:3], dtype=bool)
    # A matte is SPATIALLY COHERENT - it is the shape of a glyph - so an
    # isolated pixel in the gap between two glyphs is noise, not a mark. The
    # opening drops 1-2px specks; every real stroke (4-6px wide at 2560x1440)
    # survives.
    region = _open_bool(region)

    seed = np.stack([_fill_masked_columns(b, region) for b in bands])
    w_ref = np.asarray(w_ref, dtype=np.float64)
    shape = np.where(region, _alpha_shape(stack_i, seed, w_ref), 0.0)

    gain, score = (1.0, float("nan"))
    if tpl is not None:
        gain, score = _fit_gain(shape, region, frames, tpl, w_ref)
    alpha = np.where(region, np.clip(shape * gain, 0.0, ALPHA_MAX), 0.0)
    alpha = np.where(alpha >= alpha_floor, alpha, 0.0)
    return {"alpha": alpha, "W": _w_map(alpha, w_ref), "band": band,
            "n": len(bands), "gain": gain, "score": score}


# ==========================================================================
# THE FLAT VEIL: the half of the mark a high-pass template cannot see
# ==========================================================================
# Background window for the whitening. It must be WIDER THAN THE VEIL (the logo
# is ~310px across at 2560x1440) or the median follows the veil and the interior
# reads as background: measured, a 201px window recovers interior alpha 0.028
# where a ~408px one recovers 0.060. cv2.medianBlur cannot go there at all (it
# asserts k < 16 above 8-bit ksize 5), so the window is built by downscaling,
# taking a small median, and scaling back - which is also what keeps this on
# numpy + PIL for CI.
VEIL_SCALE = 8
VEIL_MEDIAN_K = 51           # ~408px at VEIL_SCALE 8
VEIL_THR = 0.015             # consensus whitening -> candidate veil
# CONSENSUS, not median: art structure the median cannot cancel is high in a FEW
# frames, the veil is high in ALL of them, so the low quartile across the
# collection separates them where the median does not. Measured on the fixture:
# median leaves 19 percent of the art above threshold, the 25th percentile
# leaves 0.4 percent while keeping the veil.
VEIL_Q = 25.0
VEIL_SMOOTH_WIN = 15         # the veil is low-frequency; smooth before thresholding
VEIL_CLOSE = 51              # fill the holes a threshold leaves in a solid region
# The veil is a SOLID shape; the art residue 19 frames do not fully cancel is
# scratchy and thin. A big opening separates them where a threshold cannot: at
# 0.05 the raw support sprawls across x 643-2290 of the band.
VEIL_OPEN_R = 5
VEIL_RING = 8                # ring width used to read the boundary step
# 0.5 .. 10.0. The old grid stopped at 5.0 and the shipped matte fitted EXACTLY
# 5.0 - a boundary solution, which cannot be read as an optimum. Measured
# 2026-08-12 over 31 flagged frames, the objective does turn: it minimises at
# gain 3.75 (alpha 0.0999, err 14.29) and 5.0 is already worse (err 15.26). The
# grid now extends far enough that a ceiling hit means "no minimum", not "grid
# too short", and `_fit_veil_gain` says so.
VEIL_GAIN_GRID = tuple(round(0.5 + 0.25 * i, 2) for i in range(39))
VEIL_MIN_PX = 400            # below this the support is noise, not a veil
# The support ends INSIDE the veil's true edge (see `_veil_support`), so its
# boundary is not an edge of the ORIGINAL: measured over six corpus frames on
# 2026-08-12, the raw level step across it is |0.0-0.9| levels, while a
# hard-edged correction leaves 12.7-27.4. The correction is therefore ramped out
# instead of cut off. 16px is the knee of the sweep (introduced discontinuity
# mean 23.3 -> 3.4 at 8px -> 2.1 at 16px -> 1.7 at 24px -> 1.3 asymptote; the
# per-pixel p99 jump goes 11.8-16.1 -> 2.2-3.4), and the SMALLEST extension that
# clears it is the safest, because a ramp reaching past the veil darkens real art.
VEIL_FEATHER = 16


def _coarse_median(gray, scale: int = VEIL_SCALE, k: int = VEIL_MEDIAN_K):
    """Median over a window ~`scale * k` wide, via downscale -> median -> upscale.

    An exact median at that width is neither affordable in numpy nor available in
    cv2 (`k < 16`), and it is not needed: the quantity wanted is the level of the
    art AROUND the veil, which survives the downscale.
    """
    from PIL import ImageFilter
    h, w = gray.shape
    sc = max(int(scale), 1)
    small = Image.fromarray(np.clip(gray, 0, 255).astype(np.uint8), mode="L")
    small = small.resize((max(w // sc, 1), max(h // sc, 1)), Image.BILINEAR)
    small = small.filter(ImageFilter.MedianFilter(max(int(k) | 1, 3)))
    return np.asarray(small.resize((w, h), Image.BILINEAR), dtype=np.float64)


def _whiten(band_rgb, scale: int = VEIL_SCALE, k: int = VEIL_MEDIAN_K):
    """`(gray - bg) / (255 - bg)` - alpha for a near-white mark over `bg`."""
    g = np.asarray(band_rgb, dtype=np.float64).mean(axis=2)
    bg = _coarse_median(g, scale, k)
    return np.clip((g - bg) / np.clip(255.0 - bg, 1.0, None), 0.0, 1.0)


def _close_bool(mask, size: int):
    """Morphological closing (dilate then erode) - fills holes in a solid region."""
    from PIL import ImageFilter
    u8 = (np.asarray(mask, dtype=bool) * 255).astype(np.uint8)
    im = Image.fromarray(u8, mode="L")
    im = im.filter(ImageFilter.MaxFilter(max(int(size) | 1, 3)))
    im = im.filter(ImageFilter.MinFilter(max(int(size) | 1, 3)))
    return np.asarray(im) > 127


def _veil_support(raw, thr: float = VEIL_THR, open_r: int = VEIL_OPEN_R,
                  close_k: int = VEIL_CLOSE):
    """Threshold a SMOOTHED map, drop thin residue, then fill the solid region.

    Three steps because the failure modes are three: art residue is thin (the
    opening), a solid veil still thresholds ragged (the closing), and both are
    noisy at pixel scale (the smoothing, done by the caller).

    The support ends ~10px INSIDE the veil's true edge, and that is deliberate:
    over-reaching would darken real art by the full veil alpha, while the missing
    rim is exactly the strip the stroke mask hands to LaMa anyway.
    """
    sup = raw >= float(thr)
    if open_r and open_r >= 1:
        sup = _open_bool(sup, 2 * int(open_r) + 1)
    if close_k and close_k >= 3:
        sup = _close_bool(sup, close_k)
    return sup


def _fit_veil_gain(bands, support, raw_alpha, w_ref, ring: int = VEIL_RING,
                   gains=VEIL_GAIN_GRID):
    """Pick the gain whose removal leaves NO level step across the boundary.

    The whitening recovers the veil's shape and underreads its amplitude, so one
    scalar is fitted - against the most direct observable there is. Inside the
    veil `J = (I - aW)/(1-a)`; just outside, the art is untouched. The art itself
    is continuous across that line, so the right alpha is the one that makes the
    two ring means agree, averaged over the collection.
    """
    # Both rings stand OFF the support boundary by the same 2-3 ring widths, and
    # that symmetry is load-bearing. A ring flush against the support straddles
    # the veil's real edge - measured, a flush inner ring was only 56 percent
    # veil, which halved the step and so halved the recovered alpha.
    inner = (_erode_bool(support, 4 * int(ring) + 1)
             & ~_erode_bool(support, 6 * int(ring) + 1))
    outer = (_dilate_bool(support, 6 * int(ring) + 1)
             & ~_dilate_bool(support, 4 * int(ring) + 1))
    if not inner.any() or not outer.any():
        return 1.0, float("nan")
    best = (float("inf"), 1.0)
    for g in gains:
        a = float(np.clip(raw_alpha * g, 0.0, ALPHA_MAX))
        errs = []
        for b in bands:
            fixed = (b[inner] - a * w_ref[None, :]) / max(1.0 - a, 1e-3)
            errs.append(abs(float(fixed.mean()) - float(b[outer].mean())))
        mean = float(np.mean(errs))
        if mean < best[0]:
            best = (mean, float(g))
    if best[1] >= float(gains[-1]):
        # A gain ON the last grid point is not a minimum, it is where the search
        # ran out. The shipped 2026-08-11 matte did exactly this on the old
        # 0.5..5.0 grid and was recorded as an optimum; say it out loud instead.
        warnings.warn(f"veil gain hit the grid ceiling {gains[-1]} - the "
                      f"amplitude is a boundary solution, not a fitted optimum",
                      RuntimeWarning, stacklevel=2)
    return best[1], best[0]


def _erode_bool(mask, size: int):
    """Morphological erosion of a boolean mask (PIL MinFilter, no cv2)."""
    from PIL import ImageFilter
    u8 = (np.asarray(mask, dtype=bool) * 255).astype(np.uint8)
    im = Image.fromarray(u8, mode="L").filter(
        ImageFilter.MinFilter(max(int(size) | 1, 3)))
    return np.asarray(im) > 127


def estimate_veil(images, tpl=None, band=BAND, w_ref=W_REF, thr=VEIL_THR,
                  open_r: int = VEIL_OPEN_R, ring: int = VEIL_RING,
                  veil_scale: int = VEIL_SCALE, veil_k: int = VEIL_MEDIAN_K):
    """Recover the mark's FLAT region from a collection -> {alpha, support, raw}.

    `alpha` is a single number, not a map, and deliberately so: the veil IS one
    constant alpha over a solid shape, and a per-pixel map would only carry the
    art residue the median could not cancel INTO the correction. Registration
    uses the template when one is given, exactly as `estimate_matte` does.

    Returns support all-False (and alpha 0.0) when the collection carries no
    solid flat region - a clean corpus must not manufacture a veil.
    """
    band = tuple(tpl["band"]) if tpl is not None else tuple(band)
    bands = []
    for im in images:
        arr = np.asarray(im, dtype=np.float64)
        b = band_of(arr, band)
        if tpl is not None:
            _sc, dy, dx = best_shift(arr, tpl)
            if dy or dx:
                b = np.roll(b, (-dy, -dx), axis=(0, 1))
        bands.append(b)
    if not bands:
        raise ValueError("estimate_veil needs at least one image")

    stack = np.stack([_whiten(b, veil_scale, veil_k) for b in bands])
    raw_map = _box_mean(np.percentile(stack, VEIL_Q, axis=0), VEIL_SMOOTH_WIN)
    support = _veil_support(raw_map, thr, open_r)
    empty = {"alpha": 0.0, "raw": 0.0, "gain": 1.0, "step": float("nan"),
             "support": np.zeros(raw_map.shape, dtype=bool), "band": band}
    if int(support.sum()) < VEIL_MIN_PX:
        return empty
    raw = float(np.median(raw_map[support]))
    w_ref = np.asarray(w_ref, dtype=np.float64)
    gain, step = _fit_veil_gain(bands, support, raw, w_ref, ring)
    return {"alpha": float(np.clip(raw * gain, 0.0, ALPHA_MAX)), "raw": raw,
            "gain": gain, "step": step, "support": support, "band": band}


def _feather_out(sup, reach: int = VEIL_FEATHER):
    """Linear ramp 1.0 -> 0.0 over `reach` px OUTSIDE a boolean support.

    Successive 3x3 dilations, so this stays on PIL like the rest of the module
    (no scipy) and the ramp is in FRAME pixels - the caller resizes first.
    """
    out = sup.astype(np.float64)
    if not reach or reach < 1:
        return out
    cur = sup
    for i in range(1, int(reach) + 1):
        nxt = _dilate_bool(cur, 3)
        out[nxt & ~cur] = 1.0 - i / float(int(reach) + 1)
        cur = nxt
    return out


def veil_alpha_map(veil, shape=None, feather: int = VEIL_FEATHER):
    """The veil as an alpha map, full on its support and FEATHERED outward.

    The ramp is not cosmetic. The support deliberately stops inside the veil's
    true edge, so cutting the correction off at that line manufactures a level
    cliff the original never had - and the old answer to that cliff was to hand a
    ~25px ring of real art to LaMa, which is what deformed a face on the corpus's
    palest frame. Fading the correction out costs at most `alpha` on a strip that
    was already partly veiled, and it costs the filler nothing.
    """
    if not veil or not float(veil.get("alpha", 0.0)):
        return None
    sup = np.asarray(veil["support"], dtype=bool)
    if shape is not None and sup.shape != tuple(shape):
        sup = _resize2d(sup, shape, nearest=True)
    return float(veil["alpha"]) * _feather_out(sup, feather)


# ---------------------------------------------------------------------------
# PAIR MATTE (2026-11-15, docs/_archive/2026-11/VEIL_PAIR_RESULT_2026-11-15.md). The DA logo veil
# measured DIRECTLY from purchased clean originals against their DA previews:
# one solid achromatic fill (alpha ~0.14, W ~248), centred on the frame and
# scaled with it, identical across three artists. Stored frame-normalized - a
# coverage map over a small window of the frame, plus a scalar alpha and W - so
# one asset fits every frame size. Held-out pair: residual alpha 0.002 vs the
# collection veil's 0.051, whose support covers only 44 percent of the logo.
# A derivative of a third party's watermark, so it lives under ops/runtime/
# (gitignored) and is rebuilt by tools/lw_veil_pair_matte.py from the pairs.
PAIR_MATTE_PATH = os.path.join(
    _ROOT, "ops", "runtime", "clean", "da_veil_pair_matte.npz")
PAIR_REF = (1920, 1080)          # (w, h) of the grid the pixel knobs are in
PAIR_COV_FLOOR = 1e-3            # below this coverage the pixel is untouched
# Presence: alpha read from the veil's OWN boundary step, LOCALLY: inner strip
# vs outer strip means in a window along the edge, then the MEDIAN over the
# boundary. A global strip mean is not enough - on held-out C the art is 22
# levels darker inside the logo than around it, so the global estimator read
# -0.03 on the veiled frame. The local median, measured on the three purchased
# pairs: veiled 0.123 / 0.142 / 0.112, clean -0.021 / -0.013 / -0.073 (A/B/C).
PAIR_PRESENT_MIN = 0.05
PAIR_IN_STRIP = (2, 6)           # ref px inside the logo edge
PAIR_OUT_STRIP = (8, 14)         # ref px outside - past most of the halo
PAIR_STEP_WIN = 15               # ref px half-window of the local means
# The edge ring handed to LaMa AFTER de-veiling: the 1-2 px antialiased edge the
# shape cannot place to sub-pixel accuracy, plus the inner dark halo just
# outside (black-layer alpha 0.05 at -3 px). Ref px, scaled with the frame
# width. Swept on held-out C (after the inpaint_lama crop fix) - edge-band PSNR
# / high-pass RMS vs the clean: de-veiled only 29.37 / 5.09; ring 1/2 27.72 /
# 6.20; 1/3 28.75 / 5.53; 2/3 26.75 / 6.47; 2/5 25.36 / 7.21; 3/7 23.84 /
# 8.40. Every ring costs PSNR (LaMa invents, the clean is a JPEG-noisy
# reference); 1/3 is the cheapest one that visibly removes the outline ghost.
EDGE_RING_IN = 1
EDGE_RING_OUT = 3


def save_pair_matte(path, pm):
    """Atomic write of a frame-normalized pair matte (numbers only, no image)."""
    d = os.path.dirname(os.path.abspath(path))
    if d:
        os.makedirs(d, exist_ok=True)
    tmp = str(path) + ".tmp.npz"
    np.savez_compressed(
        tmp, shape=np.asarray(pm["shape"], dtype=np.float32),
        alpha=np.asarray([float(pm["alpha"])]),
        W=np.asarray(pm["W"], dtype=np.float64).reshape(3),
        window=np.asarray(pm["window"], dtype=np.float64).reshape(4),
        ref=np.asarray(pm["ref"], dtype=np.int64).reshape(2),
        sources=np.asarray(str(pm.get("sources", ""))))
    os.replace(tmp, path)
    return path


def load_pair_matte(path=PAIR_MATTE_PATH):
    """The pair matte, or None when absent / unreadable (caller falls back)."""
    if not path or not os.path.isfile(path):
        return None
    try:
        with np.load(path) as z:
            pm = {"shape": z["shape"].astype(np.float64),
                  "alpha": float(z["alpha"][0]),
                  "W": z["W"].astype(np.float64).reshape(3),
                  "window": tuple(float(v) for v in z["window"]),
                  "ref": tuple(int(v) for v in z["ref"]),
                  "sources": str(z["sources"]) if "sources" in z else ""}
    except Exception:   # noqa: BLE001 - a bad cache must degrade, not crash
        return None
    if pm["shape"].ndim != 2 or not 0.0 < pm["alpha"] < ALPHA_MAX:
        return None
    return pm


def _ref_px(n, frame_w, ref_w=PAIR_REF[0]):
    """A knob given in ref-grid px, in this frame's px (at least 1)."""
    return max(int(round(float(n) * float(frame_w) / float(ref_w))), 1)


def _span(a0, a1, n, c, d, s):
    """Output pixel range a normalized interval [a0, a1] can touch."""
    lo = c + s * (a0 * n - c) + d
    hi = c + s * (a1 * n - c) + d
    return max(int(np.floor(lo)) - 1, 0), min(int(np.ceil(hi)) + 1, n)


def register_pair_matte(frame_shape, pm, shift=(0, 0), scale=1.0, centre=None):
    """Coverage map (h, w) in [0, 1] of the pair matte on this frame.

    Frame geometry first (the window is frame-normalized), then the template's
    registration: `scale` about `centre` (default: the REMOVAL_BAND centre, the
    point `scale2d_centered` scales the band template about), then `shift`
    (dy, dx) in frame px - the order `remove_overlay` applies them to the
    collection matte. Bilinear, pixel-centre convention, exact zero outside.
    """
    h, w = int(frame_shape[0]), int(frame_shape[1])
    shape = np.asarray(pm["shape"], dtype=np.float64)
    gh, gw = shape.shape
    x0, y0, x1, y1 = (float(v) for v in pm["window"])
    s = float(scale) if scale else 1.0
    if centre is None:
        centre = (h * (REMOVAL_BAND[0] + REMOVAL_BAND[1]) / 2.0, w / 2.0)
    cy, cx = float(centre[0]), float(centre[1])
    dy, dx = (float(shift[0]), float(shift[1])) if shift else (0.0, 0.0)
    ox0, ox1 = _span(x0, x1, w, cx, dx, s)
    oy0, oy1 = _span(y0, y1, h, cy, dy, s)
    out = np.zeros((h, w), dtype=np.float64)
    if ox1 <= ox0 or oy1 <= oy0:
        return out
    # Downscaling (frame coarser than the grid) supersamples k x k per output
    # pixel so the result is AREA coverage, not a point sample that aliases
    # the edge; upscaling is plain bilinear (k = 1).
    kx = max(int(np.ceil(gw / max((x1 - x0) * w * s, 1e-9))), 1)
    ky = max(int(np.ceil(gh / max((y1 - y0) * h * s, 1e-9))), 1)
    padded = np.pad(shape, 1, mode="constant")
    val = np.zeros((oy1 - oy0, ox1 - ox0), dtype=np.float64)
    for sy in range(ky):
        v = np.arange(oy0, oy1, dtype=np.float64) + (sy + 0.5) / ky
        yn = (cy + (v - dy - cy) / s) / h
        # Window coords, +1 into a zero-padded copy of the shape so the
        # bilinear ramp falls to exactly 0 one grid cell past the window.
        iyc = np.clip((yn - y0) / (y1 - y0) * gh - 0.5 + 1.0, 0.0, gh + 1.0)
        jy = np.minimum(np.floor(iyc).astype(int), gh)
        fy = (iyc - jy)[:, None]
        for sx in range(kx):
            u = np.arange(ox0, ox1, dtype=np.float64) + (sx + 0.5) / kx
            xn = (cx + (u - dx - cx) / s) / w
            ixc = np.clip((xn - x0) / (x1 - x0) * gw - 0.5 + 1.0, 0.0, gw + 1.0)
            jx = np.minimum(np.floor(ixc).astype(int), gw)
            fx = (ixc - jx)[None, :]
            val += ((1 - fy) * (1 - fx) * padded[np.ix_(jy, jx)]
                    + (1 - fy) * fx * padded[np.ix_(jy, jx + 1)]
                    + fy * (1 - fx) * padded[np.ix_(jy + 1, jx)]
                    + fy * fx * padded[np.ix_(jy + 1, jx + 1)])
    val /= float(kx * ky)
    val[val < PAIR_COV_FLOOR] = 0.0
    out[oy0:oy1, ox0:ox1] = np.clip(val, 0.0, 1.0)
    return out


def _strips(coverage, inner, outer):
    """(inner strip, outer strip) masks around the coverage>=0.5 boundary."""
    w = coverage.shape[1]
    core = np.asarray(coverage) >= 0.5
    i0, i1 = (_ref_px(n, w) for n in inner)
    o0, o1 = (_ref_px(n, w) for n in outer)
    ins = _erode_bool(core, 2 * i0 + 1) & ~_erode_bool(core, 2 * i1 + 1)
    outs = _dilate_bool(core, 2 * o1 + 1) & ~_dilate_bool(core, 2 * o0 + 1)
    return ins, outs


def pair_veil_alpha_hat(image, coverage, w_mark):
    """Veil alpha read from THIS frame's boundary step; ~0 on a clean frame.

    Inside `I = J(1-a) + aW`; the art is continuous across the edge, so the
    local inner-vs-outer luma step is `a (W - I_out)`. Local means in a window
    along the edge, then the median over the boundary - robust to the art
    being darker or brighter under the logo as a whole.
    """
    g = np.asarray(image, dtype=np.float64)
    g = g.mean(axis=2) if g.ndim == 3 else g
    cov = np.asarray(coverage, dtype=np.float64)
    ins, outs = _strips(cov, PAIR_IN_STRIP, PAIR_OUT_STRIP)
    if not ins.any() or not outs.any():
        return 0.0
    k = 2 * _ref_px(PAIR_STEP_WIN, g.shape[1]) + 1
    ni = _box_mean(ins.astype(np.float64), k)
    no = _box_mean(outs.astype(np.float64), k)
    mi = _box_mean(g * ins, k) / np.maximum(ni, 1e-9)
    mo = _box_mean(g * outs, k) / np.maximum(no, 1e-9)
    core = cov >= 0.5
    edge = _dilate_bool(core, 3) & ~_erode_bool(core, 3)
    ok = edge & (ni > 0.05) & (no > 0.05)
    if not ok.any():
        return 0.0
    a = (mi - mo) / np.maximum(float(np.mean(w_mark)) - mo, 1.0)
    return float(np.median(a[ok]))


def pair_veil_present(image, coverage, w_mark, min_alpha=PAIR_PRESENT_MIN):
    """Is the DA logo veil on this frame where the pair matte says it is?"""
    return pair_veil_alpha_hat(image, coverage, w_mark) >= float(min_alpha)


def pair_edge_ring(coverage, inner: int = EDGE_RING_IN,
                   outer: int = EDGE_RING_OUT):
    """Bool ring `inner` ref px inside to `outer` ref px outside the logo edge."""
    cov = np.asarray(coverage, dtype=np.float64)
    core = cov >= 0.5
    if not core.any():
        return np.zeros(cov.shape, dtype=bool)
    w = cov.shape[1]
    ri, ro = _ref_px(inner, w), _ref_px(outer, w)
    return _dilate_bool(core, 2 * ro + 1) & ~_erode_bool(core, 2 * ri + 1)


# ---------------------------------------------------------------------------
# PER-FRAME AMPLITUDE (2026-11-15, docs/_archive/2026-11/VEIL_ALPHA_FIT_2026-11-15.md)
# The 63-slug batch showed the pair matte's SHAPE is right and its fixed alpha
# is not: each frame's residual tracked its own veil step (225f +0.085 under-
# removed, fantasy-design -0.075 over-removed). So the shape stays and the
# amplitude is fitted per frame, from the frame's own logo edge:
#   1. `refine_pair_shift`: sub-pixel registration of the coverage, maximizing
#      the correlation of the image gradient with the coverage gradient. On the
#      purchased pairs the logo sits up to 2 px off the consensus matte (C: +0.5,
#      +2.0 px at 1920) and a narrow step read through that offset is ~0.03 low.
#   2. `fit_pair_alpha`: the alpha whose inversion (fill + the measured dark
#      halo) leaves NO step across the edge: local means in a strip 2-6 ref px
#      inside vs 2-6 outside, windowed along the edge, median over the smoother
#      half of the windows (rough art across the edge is where art, not veil,
#      sets the step). Bisection inside PAIR_FIT_BOUNDS; a clamped fit is
#      flagged. Pairs A/B/C: fit - oracle +0.004 / -0.000 / +0.001.
# The halo is the black-layer alpha just outside the logo edge, per unit FILL
# alpha, by distance outside the edge in ref px - pairs B and C, VEIL_PAIR_RESULT
# step 5 (e.g. 0.052 / 0.062 black alpha at 2-3 px for fill ~0.148). It is used
# by the FIT only: inverting it was measured to cost the logo 1 dB on C, and the
# LaMa edge ring covers its strongest 3 px.
PAIR_HALO = ((0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 8.0, 10.0, 13.0, 16.0, 20.0,
              24.0, 30.0),
             (0.10, 0.19, 0.35, 0.31, 0.235, 0.176, 0.137, 0.118, 0.095, 0.056,
              0.036, 0.029, 0.011, 0.0))
PAIR_FIT_BOUNDS = (0.03, 0.30)   # outside this a frame is not the DA veil we know
PAIR_FIT_STRIP = (2.0, 6.0)      # ref px from the edge, same on both sides
PAIR_FIT_WIN = 15                # ref px half-window of the local means
PAIR_FIT_SMOOTH_Q = 50.0         # keep the smoother half of the windows
PAIR_FIT_ITERS = 18              # bisection steps (0.27 / 2^18: far below 1e-4)
PAIR_SHIFT_REACH = 2.5           # ref px searched around the given registration


def _edt_capped(feat, cap):
    """Euclidean distance to the nearest True of `feat`, exact up to `cap` px.

    Two separable brute-force passes (column distance, then the row minimum of
    g^2 + d^2) - numpy only, cost O(cap) array ops. Beyond `cap` it reads > cap.
    """
    feat = np.asarray(feat, dtype=bool)
    r = max(int(np.ceil(cap)), 1)
    big = float(r + 1)
    g = np.where(feat, 0.0, big)
    for d in range(1, r + 1):
        g[d:] = np.minimum(g[d:], np.where(feat[:-d], float(d), big))
        g[:-d] = np.minimum(g[:-d], np.where(feat[d:], float(d), big))
    g2 = g * g
    out = g2.copy()
    for d in range(1, r + 1):
        dd = float(d * d)
        out[:, d:] = np.minimum(out[:, d:], g2[:, :-d] + dd)
        out[:, :-d] = np.minimum(out[:, :-d], g2[:, d:] + dd)
    return np.sqrt(out)


def _halo_profile(halo):
    """(distances, values) arrays, or None for 'no halo' (an empty profile)."""
    if halo is None:
        halo = PAIR_HALO
    if len(halo) != 2 or not len(halo[0]):
        return None
    return (np.asarray(halo[0], dtype=np.float64),
            np.asarray(halo[1], dtype=np.float64))


def _signed_geometry(coverage, frame_w, cap_ref):
    """(core, distance inside, distance outside) in ref px, capped at cap_ref."""
    cov = np.asarray(coverage, dtype=np.float64)
    core = cov >= 0.5
    sc = float(PAIR_REF[0]) / float(frame_w)
    cap = cap_ref / sc + 2.0
    din = np.where(core, _edt_capped(~core, cap) * sc, 0.0)
    dout = np.where(core, 0.0, _edt_capped(core, cap) * sc)
    return core, din, dout


def pair_halo_map(coverage, frame_w, halo=None):
    """Black-layer alpha of the veil's dark halo per unit fill alpha, (h, w).

    Zero inside the logo and past the profile's reach; the profile is in ref px
    (scaled with `frame_w`). halo=() means a veil without a halo.
    """
    cov = np.asarray(coverage, dtype=np.float64)
    prof = _halo_profile(halo)
    if prof is None or not (cov >= 0.5).any():
        return np.zeros(cov.shape, dtype=np.float64)
    core, _din, dout = _signed_geometry(cov, frame_w, float(prof[0][-1]) + 1.0)
    h = np.interp(dout, prof[0], prof[1], right=0.0)
    return np.where(core, 0.0, h * (1.0 - cov))


def _luma(image):
    g = np.asarray(image, dtype=np.float64)
    return g.mean(axis=2) if g.ndim == 3 else g


def _crop_box(mask, pad, shape):
    ys, xs = np.nonzero(mask)
    h, w = int(shape[0]), int(shape[1])
    return (max(int(ys.min()) - pad, 0), min(int(ys.max()) + 1 + pad, h),
            max(int(xs.min()) - pad, 0), min(int(xs.max()) + 1 + pad, w))


def fit_pair_alpha(image, coverage, pm, halo=None, bounds=PAIR_FIT_BOUNDS):
    """Fit THIS frame's veil amplitude for the pair matte's shape.

    Returns {"alpha", "at_bound" (None | "low" | "high" | "no_edge"),
    "windows"}. The alpha is the one whose inversion - fill over `coverage`
    plus the halo (`pm["halo"]`, else PAIR_HALO; () for none) - leaves a zero
    median step across the logo edge (see the PER-FRAME AMPLITUDE note above).
    A fit that would leave `bounds` is clamped and flagged; a coverage with no
    usable edge returns the matte's own alpha, flagged "no_edge".
    """
    prior = float(pm["alpha"])
    wv = float(np.mean(pm["W"]))
    cov_full = np.asarray(coverage, dtype=np.float64)
    if halo is None:
        halo = pm.get("halo", None)
    prof = _halo_profile(halo)
    nothing = {"alpha": prior, "at_bound": "no_edge", "windows": 0}
    if not (cov_full >= 0.5).any():
        return nothing
    fw = cov_full.shape[1]
    reach = max(PAIR_FIT_STRIP[1] + PAIR_FIT_WIN,
                float(prof[0][-1]) if prof is not None else 0.0) + 4.0
    y0, y1, x0, x1 = _crop_box(cov_full > 0, _ref_px(reach, fw),
                               cov_full.shape)
    cov = cov_full[y0:y1, x0:x1]
    g = _luma(image)[y0:y1, x0:x1]
    core, din, dout = _signed_geometry(cov, fw, reach)
    if prof is not None:
        hal = np.where(core, 0.0, np.interp(dout, prof[0], prof[1], right=0.0)
                       * (1.0 - cov))
    else:
        hal = np.zeros(cov.shape)
    s0, s1 = PAIR_FIT_STRIP
    ins = core & (din >= s0) & (din < s1)
    outs = ~core & (dout >= s0) & (dout < s1)
    k = 2 * _ref_px(PAIR_FIT_WIN, fw) + 1
    ni = _box_mean(ins.astype(np.float64), k)
    no = _box_mean(outs.astype(np.float64), k)
    edge = core & (din <= 2.0)
    ok = edge & (ni > 0.02) & (no > 0.02)
    if int(ok.sum()) < 10:
        return nothing

    def deveil(a):
        return np.clip((g - a * cov * wv)
                       / np.maximum(1.0 - a * cov - a * hal, 1e-3), 0.0, 255.0)

    def strip_stats(j):
        mi = _box_mean(j * ins, k) / np.maximum(ni, 1e-9)
        mo = _box_mean(j * outs, k) / np.maximum(no, 1e-9)
        return mi, mo

    # Smoothness weights are fixed ONCE, at the matte's prior alpha, so the
    # window set does not move with the candidate alpha.
    j0 = deveil(prior)
    mi0, mo0 = strip_stats(j0)
    vi = _box_mean(j0 * j0 * ins, k) / np.maximum(ni, 1e-9) - mi0 ** 2
    vo = _box_mean(j0 * j0 * outs, k) / np.maximum(no, 1e-9) - mo0 ** 2
    rough = (np.sqrt(np.maximum(vi, 0.0)) + np.sqrt(np.maximum(vo, 0.0)))[ok]
    keep = rough <= np.percentile(rough, PAIR_FIT_SMOOTH_Q)
    n_win = int(keep.sum())

    def step(a):
        mi, mo = strip_stats(deveil(a))
        d = ((mi - mo) / np.maximum(wv - mo, 1.0))[ok][keep]
        return float(np.median(d))

    lo, hi = float(bounds[0]), float(bounds[1])
    if step(lo) <= 0.0:
        return {"alpha": lo, "at_bound": "low", "windows": n_win}
    if step(hi) >= 0.0:
        return {"alpha": hi, "at_bound": "high", "windows": n_win}
    for _ in range(PAIR_FIT_ITERS):
        mid = 0.5 * (lo + hi)
        if step(mid) > 0.0:
            lo = mid
        else:
            hi = mid
    return {"alpha": round(0.5 * (lo + hi), 5), "at_bound": None,
            "windows": n_win}


def _shift_int(a, dy, dx):
    """out(y, x) = a(y - dy, x - dx) for integer dy, dx; zero outside."""
    h, w = a.shape
    out = np.zeros_like(a)
    ys, yd = (slice(0, h - dy), slice(dy, h)) if dy >= 0 else (
        slice(-dy, h), slice(0, h + dy))
    xs, xd = (slice(0, w - dx), slice(dx, w)) if dx >= 0 else (
        slice(-dx, w), slice(0, w + dx))
    out[yd, xd] = a[ys, xs]
    return out


def _parabola_peak(sm, s0, sp):
    """Offset in (-0.5, 0.5) of the vertex of the parabola through 3 samples."""
    den = sm - 2.0 * s0 + sp
    if den >= 0.0:
        return 0.0
    return float(np.clip(0.5 * (sm - sp) / den, -0.5, 0.5))


def _grad_setup(g, c, clip_band_r):
    """Smoothed, clipped image gradient and coverage gradient for the score."""
    g = _box_mean(_box_mean(g, 3), 3)
    c = _box_mean(_box_mean(c, 3), 3)
    gy, gx = np.gradient(g)
    cy, cx = np.gradient(c)
    band = _dilate_bool(np.hypot(cy, cx) > 1e-3, 2 * clip_band_r + 3)
    mag = np.hypot(gy, gx)
    cap = float(np.percentile(mag[band], 90)) if band.any() else 0.0
    if cap <= 0:
        return None
    k = np.minimum(1.0, cap / np.maximum(mag, 1e-9))
    norm = float(np.sqrt((cy * cy + cx * cx).sum()))
    return gy * k * band, gx * k * band, cy, cx, max(norm, 1e-9)


def _score_grid(setup, r):
    """{(dy, dx): normalized sum(grad I . grad cov shifted)} for |d| <= r."""
    gy, gx, cy, cx, norm = setup
    return {(a, b): float((gy * _shift_int(cy, a, b)
                           + gx * _shift_int(cx, a, b)).sum()) / norm
            for a in range(-r, r + 1) for b in range(-r, r + 1)}


def refine_pair_shift(image, pm, shift=(0, 0), scale=1.0,
                      reach=PAIR_SHIFT_REACH, centre=None,
                      return_score: bool = False):
    """Sub-pixel (dy, dx) of the pair matte on this frame, near `shift`.

    The veil is the one image structure shaped like the coverage, so the shift
    that maximizes sum(grad I . grad coverage) over the edge band is the one
    that lines the matte up with it. Art gradients are clipped at their 90th
    percentile in the band so one strong art edge cannot steer the search.
    Integer shifts over +-`reach` ref px (exact, no resampling - an
    interpolated shift blurs the gradient and so biases the peak toward whole
    pixels), then a parabola through the peak's neighbours on each axis.
    `return_score` adds the peak score (normalized by the coverage gradient's
    norm, so registrations at different scales compare).
    """
    dy0, dx0 = (float(shift[0]), float(shift[1])) if shift else (0.0, 0.0)
    h, w = np.asarray(image).shape[:2]
    cov = register_pair_matte((h, w), pm, shift=(dy0, dx0), scale=scale,
                              centre=centre)
    if not (cov >= 0.5).any():
        return ((dy0, dx0), 0.0) if return_score else (dy0, dx0)
    r = max(int(np.ceil(reach * w / float(PAIR_REF[0]))), 1)
    y0, y1, x0, x1 = _crop_box(cov > 0, r + 6, (h, w))
    setup = _grad_setup(_luma(image)[y0:y1, x0:x1], cov[y0:y1, x0:x1], r)
    if setup is None:
        return ((dy0, dx0), 0.0) if return_score else (dy0, dx0)
    grid = _score_grid(setup, r + 1)
    by, bx = max(((a, b) for a in range(-r, r + 1) for b in range(-r, r + 1)),
                 key=lambda t: grid[t])
    fy = _parabola_peak(grid[(by - 1, bx)], grid[(by, bx)], grid[(by + 1, bx)])
    fx = _parabola_peak(grid[(by, bx - 1)], grid[(by, bx)], grid[(by, bx + 1)])
    out = (round(dy0 + by + fy, 3), round(dx0 + bx + fx, 3))
    return (out, grid[(by, bx)]) if return_score else out


# Pair-own registration (2026-11-15): batch 1's four "registration failures"
# were the COLLECTION template's registration, borrowed by the pair - art
# dragged it (bamboo-gal: dx +30 px, the logo sits at +4) or it missed a zoomed
# frame (fantasy-design is a 1.2x centre crop; the template said (43, -10) at
# 1.0). The pair registers itself too: scale about the FRAME centre (a zoom
# crop scales the logo about the frame centre, not about REMOVAL_BAND's) x a
# shift up to PAIR_SEARCH_REACH of the width, coarse at 1/PAIR_SEARCH_DS. It
# replaces the template only when it scores PAIR_SEARCH_MARGIN better, so the
# 59 frames the template already registered are not moved.
PAIR_SEARCH_SCALES = (0.88, 0.92, 0.96, 1.0, 1.04, 1.08, 1.12, 1.16, 1.20,
                      1.25, 1.33)
PAIR_SEARCH_REACH = 0.03
PAIR_SEARCH_DS = 4
PAIR_SEARCH_MARGIN = 1.25


def search_pair_registration(image, pm, scales=PAIR_SEARCH_SCALES,
                             reach=PAIR_SEARCH_REACH, ds=PAIR_SEARCH_DS):
    """Coarse pair-own registration -> {"shift", "scale", "centre", "score"}.

    Shift in full-frame px (multiples of `ds`), scale about the frame centre.
    """
    g = _luma(image)
    h, w = g.shape
    hs, ws = h // ds, w // ds
    small = g[:hs * ds, :ws * ds].reshape(hs, ds, ws, ds).mean(axis=(1, 3))
    r = max(int(np.ceil(reach * ws)), 1)
    best = None
    for sc in scales:
        cov = register_pair_matte((hs, ws), pm, scale=sc,
                                  centre=(hs / 2.0, ws / 2.0))
        if not (cov >= 0.5).any():
            continue
        y0, y1, x0, x1 = _crop_box(cov > 0, r + 4, (hs, ws))
        setup = _grad_setup(small[y0:y1, x0:x1], cov[y0:y1, x0:x1], 1)
        if setup is None:
            continue
        grid = _score_grid(setup, r)
        (a, b), v = max(grid.items(), key=lambda t: t[1])
        if best is None or v > best[0]:
            best = (v, sc, a, b)
    if best is None:
        return {"shift": (0.0, 0.0), "scale": 1.0, "centre": (h / 2.0, w / 2.0),
                "score": 0.0}
    return {"shift": (float(best[2] * ds), float(best[3] * ds)),
            "scale": float(best[1]), "centre": (h / 2.0, w / 2.0),
            "score": float(best[0])}


# ---------------------------------------------------------------------------
# BATCH GATE RESIDUAL (2026-11-15, docs/_archive/2026-11/VEIL_RESID_GATE_2026-11-15.md)
# The batch gate graded candidates with `pair_veil_alpha_hat` (inner 2-6 px vs
# outer 8-14 px strip step). On the purchased ground-truth frames A/B/C that
# reads 0.01-0.04 LOW with known removal errors, and the error is set by the
# art (asymmetric strips turn any lighting gradient across the edge into
# "veil"; the un-inverted halo darkens the outer strip). It also shares its
# kind of measurement with the fit (a strip-mean step). The gate now uses a
# different instrument: a colour MATCHED FILTER. The residual veil after an
# inversion at `alpha_used` is r * [(W - J) cov - J halo] per channel (the halo
# itself is divided out at alpha_used first - it is left in the image by
# design and is not fill residue). Box high-pass both the candidate and that
# signature at PAIR_RESID_HP ref px, weight each pixel by 1 / (local art energy
# left after the signature's local share + PAIR_RESID_C0), and solve one r
# shared by R, G, B: art edges of another hue or lighting that is locally
# linear project away. It never reads the fit or the old step estimator.
PAIR_RESID_HP = 12        # ref px half-width of the high-pass box
PAIR_RESID_C0 = 16.0      # art-energy floor of the smooth-art weight (levels^2)
PAIR_RESID_REACH = 40.0   # ref px around the logo the filter reads
PAIR_RESID_GATE = 0.02    # |residual alpha| bar (noise floor: see the doc)


def pair_residual_alpha(image, coverage, pm, alpha_used,
                        k_ref=PAIR_RESID_HP, c0=PAIR_RESID_C0):
    """Residual DA veil alpha left in a de-veiled candidate (the batch gate).

    `coverage` is the pair matte where the inversion put it (the fitted
    registration), `alpha_used` the alpha the inversion removed. > 0 means
    veil left (under-removal), < 0 a dark imprint (over-removal), ~0 clean;
    NaN when the coverage is empty. Read it on the ALGEBRAIC pre-pass frame
    (`pair_gate_frame`), not on the LaMa output: LaMa repaints the edge ring
    the filter reads (on A/B/C a post-LaMa read is 0.015 low on A and its
    slope against the true residual drops), while the fill residual it grades
    lives in the interior LaMa never touches. See the BATCH GATE RESIDUAL note.
    """
    cov_full = np.asarray(coverage, dtype=np.float64)
    if not (cov_full >= 0.5).any():
        return float("nan")
    img = np.asarray(image, dtype=np.float64)
    if img.ndim == 2:
        img = np.repeat(img[..., None], 3, axis=2)
    wv = np.broadcast_to(np.asarray(pm["W"], dtype=np.float64).reshape(-1),
                         (3,))
    fw = cov_full.shape[1]
    y0, y1, x0, x1 = _crop_box(cov_full > 0, _ref_px(PAIR_RESID_REACH, fw),
                               cov_full.shape)
    cov = cov_full[y0:y1, x0:x1]
    hal = pair_halo_map(cov, fw)
    keep = np.maximum(1.0 - float(alpha_used) * hal, 1e-3)
    k = 2 * _ref_px(k_ref, fw) + 1
    hg, ht = [], []
    for ch in range(3):
        g = img[y0:y1, x0:x1, ch] / keep
        bg = _box_mean(g, k)
        t = (wv[ch] - bg) * cov - bg * hal
        hg.append(g - bg)
        ht.append(t - _box_mean(t, k))
    sgt = hg[0] * ht[0] + hg[1] * ht[1] + hg[2] * ht[2]
    stt = ht[0] * ht[0] + ht[1] * ht[1] + ht[2] * ht[2]
    r0 = _box_mean(sgt, k) / np.maximum(_box_mean(stt, k), 1e-9)
    art = sum(_box_mean((a - r0 * b) ** 2, k) for a, b in zip(hg, ht, strict=True)) / 3.0
    wgt = 1.0 / (art + float(c0))
    den = float((wgt * stt).sum())
    if den <= 1e-9:
        return float("nan")
    return float((wgt * sgt).sum() / den)


def pair_gate_frame(candidate, prepass_roi, region, lama_mask_roi):
    """(pre-pass full frame, px where the candidate is NOT the pre-pass outside
    the LaMa mask) - the frame `pair_residual_alpha` grades.

    `prepass_roi` is the lane's `<slug>_iopaint_before.png` (the ROI after the
    algebraic pre-pass, before LaMa), `region` its (x0, y0, x1, y1) and
    `lama_mask_roi` the LaMa mask over that ROI. The candidate equals the
    pre-pass everywhere LaMa did not paint, so a residual read on the pre-pass
    IS the candidate's residual there; the mismatch count must be 0 or the
    reading does not describe the candidate (the gate then fails).
    """
    cand = np.asarray(candidate)
    x0, y0, x1, y1 = (int(v) for v in region)
    roi = np.asarray(prepass_roi)
    lm = np.asarray(lama_mask_roi).astype(bool)
    if roi.shape[:2] != (y1 - y0, x1 - x0) or lm.shape != roi.shape[:2]:
        raise ValueError("pre-pass ROI / mask do not match the region")
    frame = cand.copy()
    frame[y0:y1, x0:x1] = roi
    diff = np.any(cand[y0:y1, x0:x1] != roi, axis=-1) & ~lm
    return frame, int(diff.sum())


# ---------------------------------------------------------------------------
# PASS-2 EDGE PROFILE (2026-11-15, docs/_archive/2026-11/VEIL_PASS2_2026-11-15.md)
# The operator passed the per-frame alpha but the logo BORDER still ghosts.
# Measured on the purchased pairs run through the real first-pass chain (veiled
# and clean preview, both upscaled by IllustrationJaNai V3 + USM to 2560): the
# upscaled veil edge is ~1 px wide (the matte's bilinear ramp is ~3 px), it
# sits 0.5-1 px OUTSIDE the matte's 0.5 contour and ~0.4 px off vertically, the
# per-edge position wobbles by up to +-1 px against the consensus shape, and
# the dark halo outside reaches ~20 px (black alpha 0.03-0.06 at 4-8 px) - and
# was never inverted. So the pre-pass left a bright 2 px line on the edge, a
# faint bright line just inside the LaMa ring and a dark band outside it.
# Pass 2 re-renders the coverage from a SUB-PIXEL signed distance to the
# matte's contour, fits per frame a shift, an outward offset, an edge blur and
# the halo's amplitude / reach (alpha stays `fit_pair_alpha`'s), then a
# per-pixel offset along the contour, and inverts fill AND halo:
#   J = (I - a W P) / (1 - a P - a k h(d / t))
# Fit objective: art is locally PLANAR across the edge, so in windows centred
# near the edge J must be a plane - the SSE of a per-window plane fit to the
# de-veiled frame (robust log loss over the windows). The ghost gate
# (`lw_veil_ghost.edge_ghost`) is a different instrument on the OUTPUT frame.
PAIR_EDGE_SS = 4                  # supersampling of the contour render
PAIR_EDGE_REACH = 40.0            # ref px around the logo the model covers
PAIR_EDGE_WIN = 8.0               # ref px half-window of the planar-art fit
PAIR_EDGE_BAND = 10.0             # ref px from the edge the windows sit in
PAIR_EDGE_STEP = 3                # window-centre grid (frame px)
PAIR_EDGE_SIGMA0 = 0.8            # starting edge blur (frame px)
# (lo, hi) per parameter: dy, dx, d0, sigma in FRAME px; halo k, t unitless.
PAIR_EDGE_BOUNDS = ((-1.5, 1.5), (-1.5, 1.5), (-1.5, 2.0), (0.0, 2.0),
                    (0.0, 3.0), (0.6, 2.0))
PAIR_EDGE_ROUNDS = 3
PAIR_EDGE_ITERS = 14
# Local offset: per pixel along the contour, from aggregated local SSE curves.
PAIR_EDGE_LOCAL_GRID = tuple(round(-1.25 + 0.25 * i, 2) for i in range(11))
PAIR_EDGE_LOCAL_WIN = 6.0         # ref px half-window
PAIR_EDGE_LOCAL_BAND = 4.0        # ref px from the edge
PAIR_EDGE_LOCAL_AGG = 10.0        # ref px aggregation along the contour

_EDGE_Z = np.linspace(-3.0, 3.0, 25)
_EDGE_WZ = np.exp(-0.5 * _EDGE_Z * _EDGE_Z)
_EDGE_WZ /= _EDGE_WZ.sum()


def pair_signed_distance(frame_shape, pm, shift=(0, 0), scale=1.0, centre=None,
                         reach=PAIR_EDGE_REACH):
    """Sub-pixel signed distance (frame px, + inside) to the pair contour.

    Returns {"box": (y0, y1, x0, x1), "sd", "ny", "nx"} over a crop `reach`
    ref px around the logo. The contour is the 0.5 level of the registered
    coverage rendered PAIR_EDGE_SS times finer; near the edge the distance is
    the area mean of the fine distance (sub-pixel), further out the frame-res
    distance. (ny, nx) is the unit normal pointing into the logo.
    """
    h, w = int(frame_shape[0]), int(frame_shape[1])
    if centre is None:
        centre = (h * (REMOVAL_BAND[0] + REMOVAL_BAND[1]) / 2.0, w / 2.0)
    cov = register_pair_matte((h, w), pm, shift=shift, scale=scale, centre=centre)
    if not (cov >= 0.5).any():
        return None
    capf = float(reach) * w / float(PAIR_REF[0])
    y0, y1, x0, x1 = _crop_box(cov > 0, int(np.ceil(capf)) + 4, (h, w))
    ss = PAIR_EDGE_SS
    hi = register_pair_matte(
        (h * ss, w * ss), pm, shift=(float(shift[0]) * ss, float(shift[1]) * ss),
        scale=scale, centre=(float(centre[0]) * ss, float(centre[1]) * ss))
    hb = hi[y0 * ss:y1 * ss, x0 * ss:x1 * ss] >= 0.5
    capn = 3 * ss
    sdh = np.where(hb, _edt_capped(~hb, capn) - 0.5,
                   -(_edt_capped(hb, capn) - 0.5)) / ss
    hh, ww = y1 - y0, x1 - x0
    fine = sdh.reshape(hh, ss, ww, ss).mean(axis=(1, 3))
    core = cov[y0:y1, x0:x1] >= 0.5
    cf = capf + 2.0
    coarse = np.where(core, _edt_capped(~core, cf) - 0.5,
                      -(_edt_capped(core, cf) - 0.5))
    sd = np.where(np.abs(fine) < capn / ss - 0.6, fine, coarse)
    gy, gx = np.gradient(_box_mean(sd, 3))
    n = np.maximum(np.hypot(gy, gx), 1e-6)
    return {"box": (y0, y1, x0, x1), "sd": sd, "ny": gy / n, "nx": gx / n}


def pair_edge_profile(x, sigma):
    """Coverage of a hard edge at signed distance x (px), Gaussian-blurred."""
    x = np.asarray(x, dtype=np.float64)
    if sigma <= 1e-3:
        return np.clip(x + 0.5, 0.0, 1.0)
    out = np.zeros_like(x)
    for zi, wi in zip(_EDGE_Z, _EDGE_WZ, strict=True):
        out += wi * np.clip(x + 0.5 + float(sigma) * zi, 0.0, 1.0)
    return out


def _edge_sdp(geom, theta, offset=None):
    dy, dx, d0 = theta[0], theta[1], theta[2]
    sdp = geom["sd"] - (geom["ny"] * dy + geom["nx"] * dx) + d0
    return sdp if offset is None else sdp + offset


def pair_edge_maps(geom, frame_w, theta, alpha, offset=None):
    """(P fill coverage, G halo black alpha) over the geometry crop.

    theta = (dy, dx, d0, sigma, halo_k, halo_t); `offset` an optional
    per-pixel extra outward offset (frame px).
    """
    sdp = _edge_sdp(geom, theta, offset)
    p = pair_edge_profile(sdp, theta[3])
    prof = _halo_profile(None)
    dout = np.maximum(-sdp, 0.0) * float(PAIR_REF[0]) / float(frame_w)
    t = max(float(theta[5]), 1e-3)
    g = (float(alpha) * float(theta[4])
         * np.interp(dout / t, prof[0], prof[1], right=0.0)
         * (sdp < 0) * (1.0 - p))
    return p, g


class _PlanarSSE:
    """Per-window SSE of a plane fitted to the de-veiled luma (box sums)."""

    def __init__(self, g, geom, frame_w, w_mark, alpha, win_ref, band_ref, step):
        self.g, self.geom, self.fw = g, geom, frame_w
        self.wv, self.alpha = float(w_mark), float(alpha)
        self.k = 2 * _ref_px(win_ref, frame_w) + 1
        hh, ww = g.shape
        yy, xx = np.mgrid[0:hh, 0:ww].astype(np.float64)
        self.yy, self.xx = yy - hh / 2.0, xx - ww / 2.0
        sel = np.zeros((hh, ww), dtype=bool)
        sel[::step, ::step] = True
        bd = float(band_ref) * frame_w / float(PAIR_REF[0])
        self.cent = sel & (np.abs(geom["sd"]) < bd)

    def sse(self, theta, offset=None):
        p, gh = pair_edge_maps(self.geom, self.fw, theta, self.alpha, offset)
        m = 1.0 - self.alpha * p - gh
        t = self.g - self.alpha * self.wv * p
        u = (m, m * self.yy, m * self.xx)
        s = np.empty((int(self.cent.sum()), 3, 3))
        for i in range(3):
            for j in range(i, 3):
                v = _box_mean(u[i] * u[j], self.k)[self.cent]
                s[:, i, j] = v
                s[:, j, i] = v
        b = np.stack([_box_mean(ui * t, self.k)[self.cent] for ui in u], axis=-1)
        tt = _box_mean(t * t, self.k)[self.cent]
        sol = np.linalg.solve(s + np.eye(3) * 1e-6, b[..., None])[..., 0]
        return np.maximum(tt - (b * sol).sum(-1), 0.0)


def _golden(f, lo, hi, iters):
    gr = 0.6180339887498949
    a, b = float(lo), float(hi)
    c, d = b - gr * (b - a), a + gr * (b - a)
    fc, fd = f(c), f(d)
    for _ in range(int(iters)):
        if fc < fd:
            b, d, fd = d, c, fc
            c = b - gr * (b - a)
            fc = f(c)
        else:
            a, c, fc = c, d, fd
            d = a + gr * (b - a)
            fd = f(d)
    return 0.5 * (a + b)


def fit_pair_edge(image, geom, pm, alpha, rounds=PAIR_EDGE_ROUNDS,
                  iters=PAIR_EDGE_ITERS, bounds=PAIR_EDGE_BOUNDS):
    """Fit this frame's veil EDGE: shift, outward offset, blur, halo k / t.

    Alpha is given (the `fit_pair_alpha` result) and held. Coordinate descent,
    a golden-section search per parameter inside `bounds`, on a robust loss
    (mean log(sse + median start sse)) over every window. Returns {"theta": [dy, dx,
    d0, sigma, halo_k, halo_t], "cost", "cost0", "windows"}.
    """
    y0, y1, x0, x1 = geom["box"]
    fw = np.asarray(image).shape[1]
    g = _luma(image)[y0:y1, x0:x1]
    obj = _PlanarSSE(g, geom, fw, float(np.mean(pm["W"])), alpha,
                     PAIR_EDGE_WIN, PAIR_EDGE_BAND, PAIR_EDGE_STEP)
    theta = [0.0, 0.0, 0.0, PAIR_EDGE_SIGMA0, 1.0, 1.0]
    s0 = obj.sse(theta)
    if s0.size < 10:
        return {"theta": theta, "cost": float("nan"), "cost0": float("nan"),
                "windows": int(s0.size)}
    # Robust over ALL windows: log(sse + c). A fixed "smoother half" picked
    # at the start point keeps the windows the start model already explains,
    # which are the ones blind to the edge parameters (measured on the
    # fixture: dy -0.03 found for a true -0.4).
    c_floor = max(float(np.median(s0)), 1e-6)

    def cost(th):
        return float(np.mean(np.log(obj.sse(th) + c_floor)))
    c0 = cost(theta)
    for r in range(int(rounds)):
        for i in (2, 3, 0, 1, 4, 5):
            def f(v, i=i):
                th = list(theta)
                th[i] = v
                return cost(th)
            theta[i] = _golden(f, bounds[i][0], bounds[i][1],
                               iters if r == 0 else max(int(iters) - 2, 4))
    return {"theta": [round(float(v), 4) for v in theta], "cost": cost(theta),
            "cost0": c0, "windows": int(s0.size)}


def pair_edge_offsets(image, geom, pm, alpha, theta,
                      grid=PAIR_EDGE_LOCAL_GRID, agg_ref=PAIR_EDGE_LOCAL_AGG):
    """Per-pixel extra outward offset (frame px) along the contour.

    For each offset in `grid` the planar-window SSE is read at every pixel
    near the edge; the SSE curves are averaged along the contour (weight
    1 / (curve minimum + floor), so busy art counts less) and the minimum is
    refined by a parabola. Off the band the offset is carried outward by a
    wide masked mean, so the halo moves with its edge.
    """
    y0, y1, x0, x1 = geom["box"]
    fw = np.asarray(image).shape[1]
    g = _luma(image)[y0:y1, x0:x1]
    obj = _PlanarSSE(g, geom, fw, float(np.mean(pm["W"])), alpha,
                     PAIR_EDGE_LOCAL_WIN, PAIR_EDGE_LOCAL_BAND, 1)
    c = obj.cent
    grid = np.asarray(grid, dtype=np.float64)
    curves = np.zeros((len(grid),) + g.shape)
    for n, v in enumerate(grid):
        th = list(theta)
        th[2] = float(theta[2]) + float(v)
        curves[n][c] = obj.sse(th)
    smin = curves.min(axis=0)
    wgt = np.where(c, 1.0 / (smin / float(obj.k * obj.k) + 4.0), 0.0)
    ka = 2 * _ref_px(agg_ref, fw) + 1
    den = _box_mean(wgt, ka)
    agg = np.stack([_box_mean(cv * wgt, ka) / np.maximum(den, 1e-9)
                    for cv in curves])
    i = np.clip(np.argmin(agg, axis=0), 1, len(grid) - 2)
    yy, xx = np.indices(i.shape)
    sm, s0, sp = agg[i - 1, yy, xx], agg[i, yy, xx], agg[i + 1, yy, xx]
    dn = sm - 2.0 * s0 + sp
    frac = np.where(dn > 1e-12,
                    np.clip(0.5 * (sm - sp) / np.maximum(dn, 1e-12), -0.5, 0.5),
                    0.0)
    has = den > 1e-6
    off = np.where(has, grid[i] + frac * (grid[1] - grid[0]), 0.0)
    reach = 2 * _ref_px(30.0, fw) + 1
    num = _box_mean(off * has, reach)
    dd = _box_mean(has.astype(np.float64), reach)
    far = np.where(dd > 1e-6, num / np.maximum(dd, 1e-9), 0.0)
    return np.where(has, off, far)


def remove_pair_edge(image, pm, geom, alpha, theta, offset=None):
    """Invert fill AND halo with the fitted edge -> (uint8, changed, sd_adj).

    Pixels outside the geometry crop, and inside it where neither the fill
    nor the halo reaches, are copied through byte-for-byte; `changed` marks
    the support the inversion was allowed to touch. `sd_adj` is the fitted
    signed distance (frame px, full frame, -inf off the crop) - the LaMa ring
    is cut from it (`pair_edge_ring_sd`).
    """
    arr = np.asarray(image, dtype=np.float64)
    out = np.clip(np.rint(arr), 0, 255).astype(np.uint8)
    h, w = arr.shape[:2]
    changed = np.zeros((h, w), dtype=bool)
    sd_full = np.full((h, w), -np.inf)
    if geom is None:
        return out, changed, sd_full
    y0, y1, x0, x1 = geom["box"]
    p, gh = pair_edge_maps(geom, w, theta, alpha, offset)
    sd_full[y0:y1, x0:x1] = _edge_sdp(geom, theta, offset)
    a = float(alpha)
    wv = np.asarray(pm["W"], dtype=np.float64).reshape(1, 1, -1)
    crop = arr[y0:y1, x0:x1]
    keep = np.maximum(1.0 - a * p - gh, 1e-3)[..., None]
    j = np.clip((crop - a * wv * p[..., None]) / keep, 0.0, 255.0)
    hit = (p > PAIR_COV_FLOOR) | (gh > 1e-4)
    sub = out[y0:y1, x0:x1]
    sub[hit] = np.clip(np.rint(j), 0, 255).astype(np.uint8)[hit]
    changed[y0:y1, x0:x1] = hit
    return out, changed, sd_full


def pair_edge_ring_sd(sd_full, frame_w, inner=EDGE_RING_IN, outer=EDGE_RING_OUT):
    """The LaMa edge ring cut from the FITTED signed distance (ref px knobs)."""
    r = float(frame_w) / float(PAIR_REF[0])
    sd = np.asarray(sd_full)
    return (sd < inner * r) & (sd > -outer * r)


def remove_overlay(image, matte, shift=(0, 0), alpha_max=ALPHA_MAX, scale=1.0,
                   pair=None, require_present=False, pair_shift=None,
                   pair_scale=None, pair_centre=None):
    """Invert the matting equation -> (uint8 RGB, changed-pixel mask).

    `J = (I - a*W) / (1 - a)` reconstructs the partial-alpha ramp EXACTLY
    instead of asking a filler to invent it, which is the whole reason this path
    exists rather than another mask-and-inpaint (R&D section 0).

    Pixels with alpha 0 - everything outside the matte - are copied through
    byte-for-byte, so AG 1.3's outside-region identity holds by construction
    rather than by measurement. A missing matte is a no-op.

    `pair` (a `load_pair_matte` dict) is the PREFERRED veil: when given (and,
    with `require_present`, when this frame's boundary step shows the veil) it
    REPLACES the collection veil - full logo, frame geometry, no feather (its
    own antialiased edge is the ramp; VEIL_FEATHER exists only because the
    collection support stops inside the true edge). With the pair active the
    collection matte contributes NOTHING algebraic: measured on held-out C its
    low-alpha band-wide strokes cost 1.3 dB around the logo and 0.1 dB across
    the band (near 35.61 -> 34.31, far 39.24 -> 39.14 dB) and 1.8 dB on the logo
    itself; the credit line and edge go to the LaMa mask instead
    (`lw_clean_iopaint.overlay_prepass`), which still reads the collection
    matte. pair=None is today's path, byte for byte.

    `pair_shift` (dy, dx), float frame px, `pair_scale` and `pair_centre`
    register the pair on its own (the `refine_pair_shift` /
    `search_pair_registration` result) instead of the template's shift/scale.
    """
    arr = np.asarray(image, dtype=np.float64)
    out = np.clip(np.rint(arr), 0, 255).astype(np.uint8)
    h, w = arr.shape[:2]
    changed = np.zeros((h, w), dtype=bool)
    pair_cov = None
    if pair:
        pair_cov = register_pair_matte(
            (h, w), pair, shift=shift if pair_shift is None else pair_shift,
            scale=scale if pair_scale is None else pair_scale,
            centre=pair_centre)
        if not pair_cov.any() or (require_present and not pair_veil_present(
                arr, pair_cov, pair["W"])):
            pair_cov = None
    if pair_cov is not None:
        matte = None
    if not matte and pair_cov is None:
        return out, changed

    alpha_f = np.zeros((h, w), dtype=np.float64)
    w_f = np.zeros((h, w, 3), dtype=np.float64)
    if matte:
        band = tuple(matte["band"])
        y0, y1 = int(h * band[0]), int(h * band[1])
        bshape = (y1 - y0, w)
        alpha = np.asarray(matte["alpha"], dtype=np.float64)
        wm = np.asarray(matte["W"], dtype=np.float64)
        if alpha.shape != bshape:
            alpha = _resize2d(alpha, bshape)
            wm = np.stack([_resize2d(wm[..., c], bshape)
                           for c in range(wm.shape[-1])], axis=-1)
        # The FLAT VEIL rides along here and NOWHERE else: the inversion must
        # fix it (a filler cannot invent 310x240px of face), while the LaMa mask
        # must never see it. Combining by max keeps a stroke that crosses the
        # veil at its own, higher alpha rather than averaging the two.
        veil_map = veil_alpha_map(matte.get("veil"), bshape)
        if veil_map is not None:
            alpha = np.maximum(alpha, veil_map)
        # The registered SCALE is applied after the veil joins the alpha and
        # before the shift, because both were measured in template coordinates:
        # rescale first, then translate the rescaled mark into place. W rides
        # along per-channel so the inversion still subtracts the right colour.
        if float(scale) != 1.0:
            alpha = scale2d_centered(alpha, scale)
            wm = np.stack([scale2d_centered(wm[..., c], scale)
                           for c in range(wm.shape[-1])], axis=-1)
        dy, dx = (int(shift[0]), int(shift[1])) if shift else (0, 0)
        if dy or dx:
            alpha = np.roll(alpha, (dy, dx), axis=(0, 1))
            wm = np.roll(wm, (dy, dx), axis=(0, 1))
        alpha_f[y0:y1] = alpha
        w_f[y0:y1] = wm
    if pair_cov is not None:
        pa = float(pair["alpha"]) * pair_cov
        take = pa > alpha_f
        alpha_f[take] = pa[take]
        w_f[take] = np.asarray(pair["W"], dtype=np.float64).reshape(1, 3)

    a = np.clip(alpha_f, 0.0, alpha_max)[:, :, None]
    clean = np.clip((arr - a * w_f) / np.maximum(1.0 - a, 1e-3), 0.0, 255.0)
    hit = alpha_f > 0.0
    out[hit] = np.clip(np.rint(clean), 0, 255).astype(np.uint8)[hit]
    changed[hit] = True
    return out, changed


def save_matte(path, matte):
    """Atomic write of an estimated {alpha, W} matte."""
    d = os.path.dirname(os.path.abspath(path))
    if d:
        os.makedirs(d, exist_ok=True)
    tmp = str(path) + ".tmp.npz"
    veil = matte.get("veil") or {}
    extra = {}
    if veil.get("support") is not None and float(veil.get("alpha", 0.0)):
        extra = {"veil_support": np.asarray(veil["support"], dtype=bool),
                 "veil_alpha": np.asarray([float(veil["alpha"])]),
                 "veil_raw": np.asarray([float(veil.get("raw", 0.0))]),
                 "veil_gain": np.asarray([float(veil.get("gain", 1.0))]),
                 "veil_step": np.asarray([float(veil.get("step", float("nan")))])}
    np.savez_compressed(tmp, alpha=matte["alpha"], W=matte["W"],
                        band=np.asarray(matte["band"]),
                        n=np.asarray([matte.get("n", 0)]),
                        gain=np.asarray([matte.get("gain", 1.0)]),
                        score=np.asarray([matte.get("score", float("nan"))]),
                        **extra)
    os.replace(tmp, path)
    return path


def load_matte(path=MATTE_PATH):
    """Load a cached matte, or None when there is none (removal is a no-op)."""
    if not path or not os.path.isfile(path):
        return None
    with np.load(path) as z:
        veil = None
        if "veil_support" in z:
            veil = {"support": z["veil_support"].astype(bool),
                    "alpha": float(z["veil_alpha"][0]),
                    "raw": float(z["veil_raw"][0]),
                    "gain": float(z["veil_gain"][0]),
                    "step": float(z["veil_step"][0]),
                    "band": tuple(float(v) for v in z["band"])}
        return {"alpha": z["alpha"], "W": z["W"],
                "band": tuple(float(v) for v in z["band"]),
                "n": int(z["n"][0]) if "n" in z else 0,
                "gain": float(z["gain"][0]) if "gain" in z else 1.0,
                "score": float(z["score"][0]) if "score" in z else float("nan"),
                "veil": veil}


def save_template(path, tpl):
    """Atomic write (the pipeline may be reading an older template)."""
    d = os.path.dirname(os.path.abspath(path))
    if d:
        os.makedirs(d, exist_ok=True)
    # np.savez appends ".npz" unless the name already ends in it, so the temp
    # name must too - otherwise os.replace looks for a file that was never made.
    tmp = str(path) + ".tmp.npz"
    np.savez_compressed(tmp, template=tpl["template"],
                        support=tpl["support"], band=np.asarray(tpl["band"]),
                        n=np.asarray([tpl.get("n", 0)]))
    os.replace(tmp, path)
    return path


def load_template(path=TEMPLATE_PATH):
    """Load a cached template, or None when there is none (score then 0.0)."""
    if not path or not os.path.isfile(path):
        return None
    with np.load(path) as z:
        return {"template": z["template"], "support": z["support"].astype(bool),
                "band": tuple(float(v) for v in z["band"]),
                "n": int(z["n"][0]) if "n" in z else 0}


def load_image(path):
    """RGB float array for a path - the one place the detector touches disk."""
    with Image.open(path) as im:
        return np.asarray(im.convert("RGB"), dtype=np.float64)
