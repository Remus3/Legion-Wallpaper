"""The DA logo veil from PURCHASED CLEAN PAIRS - a frame-normalized matte.

docs/_archive/2026-11/VEIL_PAIR_RESULT_2026-11-15.md measured the veil directly, from two
purchased clean originals and their DA previews: ONE fixed object (the DA logo,
solid achromatic fill at alpha ~0.14, centred on the frame and scaled with it).
The collection estimator's support covered only 44 percent of it. A
shape x scalar matte from the pairs removed it on a held-out pair to residual
alpha 0.002 (old path 0.051).

These tests pin the seam that wires that matte into production:
  * the matte is a small NUMERIC asset on a frame-normalized window, saved and
    loaded atomically, absent -> None (the cleaner falls back to today's path);
  * registration maps it onto any frame size, plus the template's shift/scale;
  * `remove_overlay(..., pair=...)` inverts J = (I - aW)/(1 - a) over it and
    leaves every pixel outside it byte-identical;
  * a presence check reads the veil's own boundary step, so a clean frame is
    not "de-veiled";
  * the 1-3 px edge ring (+ halo band) becomes LaMa mask, after de-veiling;
  * the builder recovers alpha, W and the shape from synthetic pairs.

Hermetic: synthetic fixtures only, numpy + PIL, no corpus image, Linux-safe.
"""
from __future__ import annotations

import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "tools"))
import lw_clean_iopaint as IO  # noqa: E402
import lw_clean_overlay as ov  # noqa: E402
import lw_veil_pair_matte as PM  # noqa: E402

ALPHA = 0.14
W_MARK = 248.0
# The logo window, frame-normalized (x0, y0, x1, y1) - the measured DA logo bbox
# is 0.445 0.342 0.556 0.659; the fixture uses a box of the same proportions.
LOGO = (0.45, 0.35, 0.55, 0.65)


def _art(h, w, seed=0):
    """Smooth unrelated 'art' plus a little noise, mid-grey so nothing clips."""
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:h, 0:w] / float(max(h, w))
    base = np.stack([60 + 50 * np.sin(6 * xx + c) * np.cos(4 * yy - c)
                     + 30 * yy for c in (0.0, 1.1, 2.3)], axis=-1)
    return np.clip(base + 70 + rng.normal(0, 1.5, (h, w, 3)), 0, 255)


def _logo_cov(h, w, box=LOGO):
    """Exact area coverage of a frame-normalized box, per pixel (antialiased)."""
    x0, y0, x1, y1 = box[0] * w, box[1] * h, box[2] * w, box[3] * h
    xs = np.arange(w, dtype=np.float64)
    ys = np.arange(h, dtype=np.float64)
    cx = np.clip(np.minimum(xs + 1, x1) - np.maximum(xs, x0), 0, 1)
    cy = np.clip(np.minimum(ys + 1, y1) - np.maximum(ys, y0), 0, 1)
    return cy[:, None] * cx[None, :]


def _veil(art, cov, alpha=ALPHA, w_mark=W_MARK):
    a = (alpha * cov)[:, :, None]
    return (1.0 - a) * art + a * w_mark


def _pm(box=LOGO, ref=(1920, 1080), pad=0.02):
    """A frame-normalized pair matte drawn directly from the fixture box."""
    rw, rh = ref
    win = (box[0] - pad, box[1] - pad, box[2] + pad, box[3] + pad)
    full = _logo_cov(rh, rw, box)
    gx0, gy0 = int(round(win[0] * rw)), int(round(win[1] * rh))
    gx1, gy1 = int(round(win[2] * rw)), int(round(win[3] * rh))
    shape = full[gy0:gy1, gx0:gx1].astype(np.float32)
    window = (gx0 / rw, gy0 / rh, gx1 / rw, gy1 / rh)
    return {"shape": shape, "alpha": ALPHA,
            "W": np.array([W_MARK] * 3), "window": window, "ref": ref,
            "sources": "synthetic"}


# ---------------------------------------------------------------- persistence
def test_save_load_roundtrip(tmp_path):
    pm = _pm()
    p = tmp_path / "pair.npz"
    ov.save_pair_matte(str(p), pm)
    got = ov.load_pair_matte(str(p))
    assert got is not None
    assert np.allclose(got["shape"], pm["shape"])
    assert got["alpha"] == pytest.approx(ALPHA)
    assert np.allclose(got["W"], W_MARK)
    assert np.allclose(got["window"], pm["window"])
    assert tuple(got["ref"]) == (1920, 1080)
    assert not list(tmp_path.glob("*.tmp*")), "atomic write left a temp file"


def test_missing_matte_loads_as_none(tmp_path):
    assert ov.load_pair_matte(str(tmp_path / "absent.npz")) is None
    assert ov.load_pair_matte(None) is None


def test_corrupt_or_incomplete_matte_loads_as_none(tmp_path):
    bad = tmp_path / "bad.npz"
    bad.write_bytes(b"not an npz")
    assert ov.load_pair_matte(str(bad)) is None
    part = tmp_path / "part.npz"
    np.savez(str(part), shape=np.ones((4, 4), np.float32))
    assert ov.load_pair_matte(str(part)) is None


def test_default_path_is_gitignored_runtime():
    # A derivative of a third party's watermark: never tracked, like the other
    # overlay caches (module docstring of lw_clean_overlay).
    rel = os.path.relpath(ov.PAIR_MATTE_PATH, ov._ROOT).replace("\\", "/")
    assert rel.startswith("ops/runtime/")
    assert rel.endswith(".npz")


# ---------------------------------------------------------------- registration
@pytest.mark.parametrize("frame", [(216, 384), (432, 768), (360, 640)])
def test_register_lands_on_the_normalized_box(frame):
    h, w = frame
    cov = ov.register_pair_matte((h, w), _pm())
    want = _logo_cov(h, w)
    assert cov.shape == (h, w)
    # Area and centroid agree with the exact coverage at this frame size.
    assert cov.sum() == pytest.approx(want.sum(), rel=0.03)
    yy, xx = np.mgrid[0:h, 0:w]
    for grid in (yy, xx):
        assert (cov * grid).sum() / cov.sum() == pytest.approx(
            (want * grid).sum() / want.sum(), abs=0.35)
    assert np.abs(cov - want).max() < 0.35


def test_register_applies_shift_in_frame_pixels():
    h, w = 216, 384
    base = ov.register_pair_matte((h, w), _pm())
    moved = ov.register_pair_matte((h, w), _pm(), shift=(3, -5))
    assert np.allclose(moved[3:, :-5], base[:-3, 5:], atol=1e-6)


def test_register_scale_grows_about_the_centre():
    h, w = 216, 384
    base = ov.register_pair_matte((h, w), _pm())
    big = ov.register_pair_matte((h, w), _pm(), scale=1.2,
                                 centre=(h / 2.0, w / 2.0))
    assert big.sum() == pytest.approx(base.sum() * 1.44, rel=0.05)
    yy, xx = np.mgrid[0:h, 0:w]
    assert (big * xx).sum() / big.sum() == pytest.approx(
        (base * xx).sum() / base.sum(), abs=0.5)


def test_register_is_zero_far_outside_the_logo():
    cov = ov.register_pair_matte((216, 384), _pm())
    assert cov[:40].max() == 0.0 and cov[:, :100].max() == 0.0


# ---------------------------------------------------------------- inversion
def test_pair_inversion_recovers_the_art_and_leaves_outside_identical():
    h, w = 432, 768
    art = _art(h, w)
    veiled = np.clip(np.rint(_veil(art, _logo_cov(h, w))), 0, 255)
    out, changed = ov.remove_overlay(veiled, None, pair=_pm())
    inside = _logo_cov(h, w) > 0.99
    err = np.abs(out.astype(np.float64) - art)[inside]
    assert err.mean() < 1.0
    # residual alpha: re-estimate a from (out, art) -> ~0
    assert float(np.abs(out.astype(np.float64)[inside] - art[inside]).max()) < 3
    outside = ~changed
    assert outside.any()
    assert np.array_equal(out[outside], veiled.astype(np.uint8)[outside])
    assert not changed[:40].any()


def test_without_pair_removal_is_the_legacy_path():
    h, w = 216, 384
    art = np.clip(np.rint(_art(h, w)), 0, 255)
    alpha = np.zeros((int(h * 0.3), w))
    alpha[20:30, 100:200] = 0.3
    matte = {"alpha": alpha, "W": np.full(alpha.shape + (3,), 250.0),
             "band": (0.55, 0.85)}
    a, ca = ov.remove_overlay(art, matte)
    b, cb = ov.remove_overlay(art, matte, pair=None)
    assert np.array_equal(a, b) and np.array_equal(ca, cb)


def test_pair_replaces_the_legacy_collection_veil():
    # The legacy veil (support inside the band only) must NOT be applied on top
    # of the pair veil - two veils over one logo would double-correct it.
    h, w = 432, 768
    art = _art(h, w)
    veiled = np.clip(np.rint(_veil(art, _logo_cov(h, w))), 0, 255)
    band = (0.45, 0.85)
    bh = int(h * band[1]) - int(h * band[0])
    sup = np.zeros((bh, w), dtype=bool)
    sup[0:60, 340:430] = True
    matte = {"alpha": np.zeros((bh, w)), "W": np.full((bh, w, 3), 250.0),
             "band": band, "veil": {"support": sup, "alpha": 0.14}}
    out, _ = ov.remove_overlay(veiled, matte, pair=_pm())
    inside = _logo_cov(h, w) > 0.99
    assert np.abs(out.astype(np.float64) - art)[inside].mean() < 1.0


def _credit_matte(h, w):
    band = (0.45, 0.85)
    y0 = int(h * band[0])
    bh = int(h * band[1]) - y0
    alpha = np.zeros((bh, w))
    alpha[100:106, 300:500] = 0.3          # a credit line BELOW the logo
    return {"alpha": alpha, "W": np.full((bh, w, 3), 250.0), "band": band}, y0


def test_pair_active_drops_the_collection_strokes_from_the_algebra():
    # Measured on held-out C: the collection matte's low-alpha strokes cost
    # 1.3 dB around the logo once the pair carries the veil. They go to LaMa.
    h, w = 432, 768
    art = np.clip(np.rint(_veil(_art(h, w), _logo_cov(h, w))), 0, 255)
    matte, y0 = _credit_matte(h, w)
    _, changed = ov.remove_overlay(art, matte, pair=_pm())
    assert not changed[y0 + 100:y0 + 106, 300:500].any()
    assert changed[_logo_cov(h, w) > 0.99].all()


def test_pair_active_the_credit_line_still_reaches_the_lama_mask():
    h, w = 432, 768
    art = np.clip(np.rint(_veil(_art(h, w), _logo_cov(h, w))), 0, 255)
    bgr = np.ascontiguousarray(art[:, :, ::-1]).astype(np.uint8)
    matte, y0 = _credit_matte(h, w)
    _pre, mask_full, roi, info, ring = IO.overlay_prepass(
        bgr, matte, None, pair=_pm(), return_ring=True)
    assert info["pair"]["used"] is True
    assert (mask_full[y0 + 100:y0 + 106, 300:500] == 255).all()
    assert roi[3] >= y0 + 106


def test_collection_strokes_apply_when_the_veil_is_not_detected():
    h, w = 432, 768
    art = np.clip(np.rint(_art(h, w, seed=6)), 0, 255)
    matte, y0 = _credit_matte(h, w)
    _, changed = ov.remove_overlay(art, matte, pair=_pm(), require_present=True)
    assert changed[y0 + 100:y0 + 106, 300:500].all()


# ---------------------------------------------------------------- presence
def test_presence_reads_the_veil_on_a_veiled_frame_and_not_on_a_clean_one():
    h, w = 432, 768
    art = _art(h, w, seed=3)
    cov = ov.register_pair_matte((h, w), _pm())
    veiled = np.clip(np.rint(_veil(art, _logo_cov(h, w))), 0, 255)
    a_v = ov.pair_veil_alpha_hat(veiled, cov, W_MARK)
    a_c = ov.pair_veil_alpha_hat(np.rint(art), cov, W_MARK)
    assert a_v == pytest.approx(ALPHA, abs=0.03)
    assert abs(a_c) < 0.03
    assert ov.pair_veil_present(veiled, cov, W_MARK)
    assert not ov.pair_veil_present(np.rint(art), cov, W_MARK)


def test_absent_veil_leaves_the_frame_alone_when_gated():
    h, w = 432, 768
    art = np.clip(np.rint(_art(h, w, seed=4)), 0, 255)
    out, changed = ov.remove_overlay(art, None, pair=_pm(), require_present=True)
    assert not changed.any()
    assert np.array_equal(out, art.astype(np.uint8))


# ---------------------------------------------------------------- edge ring
def test_edge_ring_straddles_the_boundary():
    h, w = 1080, 1920
    cov = ov.register_pair_matte((h, w), _pm())
    ring = ov.pair_edge_ring(cov, inner=2, outer=4)
    x0, x1 = int(LOGO[0] * w), int(LOGO[2] * w)
    yc = h // 2
    row = ring[yc]
    # the left edge: 2 px in, 4 px out
    assert row[x0 - 4:x0 + 2].all()
    assert not row[x0 - 7] and not row[x0 + 5]
    assert not ring[yc, (x0 + x1) // 2], "deep interior is not ring"
    assert ring.sum() < 0.25 * (cov > 0.5).sum()


def test_edge_ring_scales_with_the_frame_width():
    small = ov.pair_edge_ring(ov.register_pair_matte((540, 960), _pm()),
                              inner=2, outer=4)
    big = ov.pair_edge_ring(ov.register_pair_matte((1080, 1920), _pm()),
                            inner=2, outer=4)
    # perimeter AND ring width both double: area ~ 4x per linear doubling
    assert big.sum() / small.sum() == pytest.approx(4.0, rel=0.25)


def test_edge_ring_is_empty_for_empty_coverage():
    assert not ov.pair_edge_ring(np.zeros((50, 80))).any()


# ---------------------------------------------------------------- LaMa mask
def test_prepass_with_pair_adds_the_ring_to_the_mask_and_roi():
    h, w = 432, 768
    art = _art(h, w)
    veiled = np.clip(np.rint(_veil(art, _logo_cov(h, w))), 0, 255)
    bgr = np.ascontiguousarray(veiled[:, :, ::-1]).astype(np.uint8)
    pre, mask_full, roi, info, ring = IO.overlay_prepass(
        bgr, None, None, pair=_pm(), return_ring=True)
    assert ring.any()
    assert (mask_full[ring] == 255).all()
    rx0, ry0, rx1, ry1 = roi
    ys, xs = np.nonzero(ring)
    assert rx0 <= xs.min() and xs.max() < rx1 and ry0 <= ys.min() and ys.max() < ry1
    assert info["pair"]["used"] is True
    # de-veiled inside, before LaMa ever runs
    inside = _logo_cov(h, w) > 0.99
    assert np.abs(pre[:, :, ::-1].astype(np.float64) - art)[inside].mean() < 1.0


def test_prepass_without_pair_is_unchanged():
    h, w = 432, 768
    bgr = np.clip(np.rint(_art(h, w)), 0, 255).astype(np.uint8)
    band = (0.45, 0.85)
    bh = int(h * band[1]) - int(h * band[0])
    alpha = np.zeros((bh, w))
    alpha[100:110, 300:500] = 0.3
    matte = {"alpha": alpha, "W": np.full((bh, w, 3), 250.0), "band": band}
    a = IO.overlay_prepass(bgr, matte, None)
    b = IO.overlay_prepass(bgr, matte, None, pair=None)
    assert len(a) == 4
    assert np.array_equal(a[0], b[0]) and np.array_equal(a[1], b[1])
    assert a[2] == b[2]


def test_prepass_pair_absent_veil_falls_back():
    h, w = 432, 768
    bgr = np.clip(np.rint(_art(h, w, seed=5)), 0, 255).astype(np.uint8)
    pre, mask_full, roi, info, ring = IO.overlay_prepass(
        bgr, None, None, pair=_pm(), return_ring=True)
    assert info["pair"]["used"] is False
    assert not ring.any()
    assert np.array_equal(pre, bgr)


# ---------------------------------------------------------------- builder
def _pair(h, w, seed):
    art = _art(h, w, seed=seed)
    veiled = np.clip(np.rint(_veil(art, _logo_cov(h, w))), 0, 255)
    return veiled, art


def test_builder_recovers_alpha_w_and_shape_from_synthetic_pairs():
    pairs = [_pair(540, 960, 11), _pair(536, 954, 12)]
    pm = PM.build_pair_matte(pairs, ref=(960, 540))
    assert pm["alpha"] == pytest.approx(ALPHA, abs=0.01)
    assert np.mean(pm["W"]) == pytest.approx(W_MARK, abs=8)
    cov = ov.register_pair_matte((540, 960), pm)
    want = _logo_cov(540, 960)
    inter = ((cov > 0.5) & (want > 0.5)).sum()
    union = ((cov > 0.5) | (want > 0.5)).sum()
    assert inter / union > 0.93
    x0, y0, x1, y1 = pm["window"]
    assert x0 < LOGO[0] and y0 < LOGO[1] and x1 > LOGO[2] and y1 > LOGO[3]
    assert (x1 - x0) < 0.3 and (y1 - y0) < 0.5


def test_builder_accepts_a_clean_at_a_larger_size():
    veiled, art = _pair(270, 480, 13)
    from PIL import Image
    big = np.asarray(Image.fromarray(np.clip(art, 0, 255).astype(np.uint8))
                     .resize((960, 540), Image.BICUBIC), dtype=np.float64)
    pm = PM.build_pair_matte([(veiled, big)], ref=(480, 270))
    assert pm["alpha"] == pytest.approx(ALPHA, abs=0.015)


def test_builder_refuses_pairs_without_a_veil():
    art = _art(270, 480, seed=14)
    with pytest.raises(ValueError):
        PM.build_pair_matte([(np.rint(art), art)], ref=(480, 270))


def test_pair_active_drops_the_collection_seed_inside_the_logo_box():
    # The collection matte traces the logo outline at its old, partial
    # support; with the pair active that seed is art, not a stroke (held-out C:
    # keeping it cost the logo 7.9 dB once LaMa ran). Only the ring stays.
    h, w = 432, 768
    art = np.clip(np.rint(_veil(_art(h, w), _logo_cov(h, w))), 0, 255)
    bgr = np.ascontiguousarray(art[:, :, ::-1]).astype(np.uint8)
    matte, y0 = _credit_matte(h, w)
    ly, lx = int(0.50 * h) - y0, int(0.50 * w)
    matte["alpha"][ly:ly + 6, lx - 20:lx + 20] = 0.3   # an 'outline' in the logo
    _pre, mask_full, _roi, _info, ring = IO.overlay_prepass(
        bgr, matte, None, pair=_pm(), return_ring=True)
    inside = mask_full[y0 + ly:y0 + ly + 6, lx - 20:lx + 20] == 255
    assert not (inside & ~ring[y0 + ly:y0 + ly + 6, lx - 20:lx + 20]).any()
    assert (mask_full[y0 + 100:y0 + 106, 300:500] == 255).all()
