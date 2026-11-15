"""Build the DA logo veil PAIR MATTE from purchased clean / DA-preview pairs.

docs/_archive/2026-11/VEIL_PAIR_RESULT_2026-11-15.md measured the DA logo veil directly: a
purchased clean original registered onto its DA preview gives, per pixel,
`obs - orig = alpha (W - orig)`. Pooled locally (Gaussian sigma 2 px, over the
three channels) that yields a clean matte: the logo as one solid achromatic fill
(alpha ~0.14, W ~246-252), centred on the frame and scaled with it, identical
across artists. This script turns those pairs into the small numeric asset the
cleaner loads (`lw_clean_overlay.load_pair_matte`):

    shape   coverage in [0, 1] on a frame-normalized WINDOW around the logo,
            sampled on the `ref` grid: consensus of the pairs' logo masks,
            blurred sigma 1 ref px (the antialiased edge)
    alpha   scalar fill alpha: median over pairs of the interior median
    W       mark colour: per-channel fit inside the interior, pairs whose fit is
            unphysical (> 258, the dark/colour-drifted pair A) are dropped
    window  (x0, y0, x1, y1) frame-normalized; ref (w, h)

PUBLIC-REPO BOUNDARY. The output is a derivative of a third party's watermark,
so it is written under `ops/runtime/clean/` (gitignored) like every other
overlay cache, never tracked. The pairs themselves are the operator's purchased
originals and DA previews under `images/` (gitignored). Regeneration is
deterministic from the pairs:

    python tools/lw_veil_pair_matte.py --pair <veiled> <clean> --pair ...

`<clean>` may be an image (resized to the preview with a BOX filter and tone
matched outside the centre) or a `.npy` already registered to the preview.

Pure numpy + PIL (CI-safe); cv2/ECC is not needed - the previews are plain
whole-frame resizes (ECC residual < 0.09 px on all three pairs).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import deque

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lw_clean_overlay as OV  # noqa: E402

Image.MAX_IMAGE_PIXELS = None

POOL_SIGMA = 2.0            # local LSQ pooling, preview px (JPEG noise floor)
LOGO_THR = 0.07             # half the fill alpha: the edge midpoint
EDGE_SIGMA = 1.0            # ref px: the measured antialiased edge
W_INIT = 250.0
W_MAX_PHYSICAL = 258.0      # a mark brighter than white = ill-conditioned fit
WINDOW_PAD = 0.02           # frame-normalized slack around the logo
MIN_LOGO_FRAC = 0.002       # a logo under 0.2 percent of the frame is no logo
# Central box excluded from the tone fit (frame-normalized x0, y0, x1, y1): the
# logo (0.445-0.556, 0.342-0.659) and the credit line (to y 0.78) live in it.
TONE_EXCLUDE = (0.30, 0.25, 0.70, 0.85)


def _gauss1d(sigma):
    r = max(int(np.ceil(3.0 * sigma)), 1)
    x = np.arange(-r, r + 1, dtype=np.float64)
    k = np.exp(-0.5 * (x / sigma) ** 2)
    return k / k.sum(), r


def gauss_blur(arr2d, sigma):
    """Separable Gaussian blur, edge-replicated (pure numpy)."""
    a = np.asarray(arr2d, dtype=np.float64)
    if sigma <= 0:
        return a.copy()
    k, r = _gauss1d(sigma)
    p = np.pad(a, ((0, 0), (r, r)), mode="edge")
    t = sum(k[i] * p[:, i:i + a.shape[1]] for i in range(len(k)))
    p = np.pad(t, ((r, r), (0, 0)), mode="edge")
    return sum(k[i] * p[i:i + a.shape[0], :] for i in range(len(k)))


def _resize_rgb(arr, size_wh):
    """Float RGB resize with a BOX filter (area average, like INTER_AREA)."""
    a = np.asarray(arr, dtype=np.float32)
    return np.stack([np.asarray(Image.fromarray(np.ascontiguousarray(a[..., c]),
                                                mode="F").resize(size_wh, Image.BOX),
                                dtype=np.float64) for c in range(3)], axis=-1)


def tone_match(clean, veiled, exclude=TONE_EXCLUDE, iters=3):
    """3x3 colour matrix + offset (clean -> veiled), fitted OUTSIDE the veil."""
    h, w = veiled.shape[:2]
    use = np.ones((h, w), dtype=bool)
    ex0, ey0, ex1, ey1 = exclude
    use[int(ey0 * h):int(ey1 * h), int(ex0 * w):int(ex1 * w)] = False
    x = np.concatenate([clean.reshape(-1, 3), np.ones((h * w, 1))], axis=1)
    y = veiled.reshape(-1, 3)
    m = np.vstack([np.eye(3), np.zeros((1, 3))])
    for _ in range(iters):
        sel = use.ravel()
        if sel.sum() < 100:
            break
        m, *_ = np.linalg.lstsq(x[sel], y[sel], rcond=None)
        diff = gauss_blur((y - x @ m).mean(axis=1).reshape(h, w), 2.0)
        use = use & (np.abs(diff) <= 1.0)
    return (x @ m).reshape(h, w, 3)


def pooled_alpha(veiled, clean, w_mark, sigma=POOL_SIGMA):
    """Local LSQ of `obs - orig = a (W - orig)` over channels, Gaussian pooled."""
    d = veiled - clean
    g = np.asarray(w_mark, dtype=np.float64).reshape(1, 1, -1) - clean
    num = gauss_blur((d * g).sum(axis=2), sigma)
    den = gauss_blur((g * g).sum(axis=2), sigma)
    return num / np.maximum(den, 1.0)


def _largest_component(mask):
    """Largest 4-connected component of a bool mask (BFS, pure python)."""
    m = np.asarray(mask, dtype=bool)
    h, w = m.shape
    seen = np.zeros_like(m)
    best = None
    best_n = 0
    for y0, x0 in zip(*np.nonzero(m), strict=True):
        if seen[y0, x0]:
            continue
        comp = []
        q = deque([(y0, x0)])
        seen[y0, x0] = True
        while q:
            y, x = q.popleft()
            comp.append((y, x))
            for ny, nx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
                if 0 <= ny < h and 0 <= nx < w and m[ny, nx] and not seen[ny, nx]:
                    seen[ny, nx] = True
                    q.append((ny, nx))
        if len(comp) > best_n:
            best, best_n = comp, len(comp)
    out = np.zeros_like(m)
    if best:
        ys, xs = zip(*best, strict=True)
        out[list(ys), list(xs)] = True
    return out


def _fill_holes(mask):
    """Fill holes: background not 4-reachable from the bbox border."""
    m = np.asarray(mask, dtype=bool)
    if not m.any():
        return m
    ys, xs = np.nonzero(m)
    y0, y1 = max(ys.min() - 1, 0), min(ys.max() + 2, m.shape[0])
    x0, x1 = max(xs.min() - 1, 0), min(xs.max() + 2, m.shape[1])
    sub = m[y0:y1, x0:x1]
    padded = np.pad(sub, 1, constant_values=False)
    outside = _largest_component_from(~padded, (0, 0))
    filled = ~outside[1:-1, 1:-1]
    out = m.copy()
    out[y0:y1, x0:x1] = filled
    return out


def _largest_component_from(mask, seed):
    """Component of `mask` containing `seed` (BFS)."""
    h, w = mask.shape
    out = np.zeros_like(mask)
    q = deque([seed])
    out[seed] = True
    while q:
        y, x = q.popleft()
        for ny, nx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
            if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not out[ny, nx]:
                out[ny, nx] = True
                q.append((ny, nx))
    return out


def _fit_w(veiled, clean, interior):
    """Per-channel fit of `d = aW - a o` inside the interior -> (a_c, W_c)."""
    res = []
    for c in range(3):
        o = clean[..., c][interior]
        d = (veiled[..., c] - clean[..., c])[interior]
        x = np.stack([np.ones_like(o), -o], axis=1)
        (p, a), *_ = np.linalg.lstsq(x, d, rcond=None)
        res.append((float(a), float(p / a) if abs(a) > 1e-6 else float("nan")))
    return res


def _prepare(veiled, clean):
    v = np.asarray(veiled, dtype=np.float64)[..., :3]
    c = np.asarray(clean, dtype=np.float64)[..., :3]
    if c.shape != v.shape:
        c = _resize_rgb(c, (v.shape[1], v.shape[0]))
    return v, tone_match(c, v)


def _to_ref(mask_f, ref):
    """A per-pair float map resampled onto the ref grid (frame-normalized)."""
    return np.asarray(Image.fromarray(np.asarray(mask_f, dtype=np.float32),
                                      mode="F").resize(tuple(ref), Image.BILINEAR),
                      dtype=np.float64)


def build_pair_matte(pairs, ref=OV.PAIR_REF, sources=""):
    """[(veiled, clean)] -> pair matte dict. Raises ValueError with no veil."""
    if not pairs:
        raise ValueError("build_pair_matte needs at least one pair")
    prepared = [_prepare(v, c) for v, c in pairs]
    logos, interiors, fits = [], [], []
    for v, c in prepared:
        a = pooled_alpha(v, c, W_INIT)
        logo = _fill_holes(_largest_component(a > LOGO_THR))
        if logo.sum() < MIN_LOGO_FRAC * logo.size:
            raise ValueError("no veil found in a pair (largest component "
                             f"{int(logo.sum())} px)")
        er = max(int(round(3 * v.shape[1] / 1920.0)), 1)
        interior = OV._erode_bool(logo, 2 * er + 1)
        logos.append(logo)
        interiors.append(interior)
        fits.append(_fit_w(v, c, interior))
    ok = [f for f in fits if all(np.isfinite(wc) and wc <= W_MAX_PHYSICAL
                                 and ac > 0 for ac, wc in f)]
    w_mark = (np.median(np.array([[wc for _a, wc in f] for f in ok]), axis=0)
              if ok else np.full(3, W_INIT))
    w_mark = np.full(3, float(np.mean(w_mark)))      # achromatic, measured
    alphas = []
    for (v, c), interior in zip(prepared, interiors, strict=True):
        a = pooled_alpha(v, c, w_mark)
        alphas.append(float(np.median(a[interior])))
    cons = np.mean([_to_ref(lg.astype(np.float32), ref) for lg in logos], axis=0)
    core = cons >= 0.5
    shape_full = np.clip(gauss_blur(core.astype(np.float64), EDGE_SIGMA), 0, 1)
    shape_full[shape_full < OV.PAIR_COV_FLOOR] = 0.0
    rw, rh = int(ref[0]), int(ref[1])
    ys, xs = np.nonzero(shape_full > 0)
    px, py = int(round(WINDOW_PAD * rw)), int(round(WINDOW_PAD * rh))
    gx0, gx1 = max(xs.min() - px, 0), min(xs.max() + 1 + px, rw)
    gy0, gy1 = max(ys.min() - py, 0), min(ys.max() + 1 + py, rh)
    return {"shape": shape_full[gy0:gy1, gx0:gx1].astype(np.float32),
            "alpha": float(np.median(alphas)), "W": w_mark,
            "window": (gx0 / rw, gy0 / rh, gx1 / rw, gy1 / rh),
            "ref": (rw, rh), "sources": sources,
            "per_pair": [{"alpha": round(al, 4),
                          "fit": [[round(x, 4) for x in f] for f in fit],
                          "logo_px": int(lg.sum())}
                         for al, fit, lg in zip(alphas, fits, logos, strict=True)]}


def _load_any(path):
    if str(path).lower().endswith(".npy"):
        return np.load(path).astype(np.float64)
    with Image.open(path) as im:
        return np.asarray(im.convert("RGB"), dtype=np.float64)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="lw_veil_pair_matte")
    ap.add_argument("--pair", nargs=2, action="append", required=True,
                    metavar=("VEILED", "CLEAN"))
    ap.add_argument("--out", default=OV.PAIR_MATTE_PATH)
    ap.add_argument("--sources", default="",
                    help="short provenance label (e.g. DA deviation ids)")
    args = ap.parse_args(argv)
    pairs = [(_load_any(v), _load_any(c)) for v, c in args.pair]
    pm = build_pair_matte(pairs, sources=args.sources)
    OV.save_pair_matte(args.out, pm)
    print(json.dumps({"out": os.path.relpath(args.out, OV._ROOT),
                      "alpha": round(pm["alpha"], 4),
                      "W": [round(float(x), 1) for x in pm["W"]],
                      "window": [round(x, 4) for x in pm["window"]],
                      "shape": list(pm["shape"].shape),
                      "per_pair": pm["per_pair"]}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
