"""Pass-2 edge profile for the DA logo pair matte.

The operator passed the per-frame alpha but the logo BORDER still ghosts
(docs/_archive/2026-11/VEIL_PASS2_2026-11-15.md). On the purchased pairs run
through the real upscale chain the veil edge is ~1 px wide (the matte's ramp
~3 px), sits up to 1 px outside the matte contour and a fraction of a pixel
off, and its dark halo reaches ~20 px and was never inverted. These tests pin
the fix on hermetic fixtures whose veil edge is rendered INDEPENDENTLY of the
model (a hard contour rendered 8x finer, dilated, shifted, Gaussian-blurred):

  * `pair_signed_distance` is sub-pixel and signed (+ inside);
  * `fit_pair_edge` recovers a known sub-pixel shift, outward offset and blur;
  * `remove_pair_edge` with the fit leaves far less edge residue than the
    a2eb6c3 / 8aa837f inversion (`remove_overlay` at the refined shift), and
    inverts the halo (the dark band outside goes);
  * per-pixel offsets (`pair_edge_offsets`) absorb a contour that wobbles;
  * outside the declared support every pixel is byte-identical;
  * `overlay_prepass(edge_fit=True)` uses it and records the fit, and the
    default (`edge_fit=False`) is the old path byte for byte.

Hermetic: synthetic fixtures only, numpy + PIL, Linux-safe.
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
from lw_clean_pass import _box_mean  # noqa: E402

W_MARK = 245.0
H, W = 720, 1280
WINDOW = (0.42, 0.31, 0.58, 0.69)
ALPHA = 0.15


def _logo_grid(gh=380, gw=300, ss=4):
    yy, xx = np.mgrid[0:gh * ss, 0:gw * ss].astype(np.float64)
    u, v = xx / (gw * ss), yy / (gh * ss)
    body = (v > 0.08) & (v < 0.92) & (u > 0.12 + 0.18 * v) & (u < 0.70 + 0.18 * v)
    notch = (v > 0.40) & (v < 0.55) & (u > 0.55 + 0.18 * v)
    m = (body & ~notch).astype(np.float64)
    m = m.reshape(gh, ss, gw, ss).mean(axis=(1, 3))
    # the consensus matte is SOFT (blurred), like the real asset
    return _box_mean(_box_mean(m, 3), 3).astype(np.float32)


def _pm(alpha=ALPHA):
    return {"shape": _logo_grid(), "alpha": alpha,
            "W": np.array([W_MARK] * 3), "window": WINDOW, "ref": (1920, 1080),
            "sources": "synthetic"}


def _gauss(a, sigma):
    if sigma <= 0:
        return a
    r = int(np.ceil(3 * sigma))
    k = np.exp(-0.5 * (np.arange(-r, r + 1) / sigma) ** 2)
    k /= k.sum()
    p = np.pad(a, r, mode="edge")
    p = np.apply_along_axis(lambda z: np.convolve(z, k, mode="valid"), 0, p)
    return np.apply_along_axis(lambda z: np.convolve(z, k, mode="valid"), 1, p)


def _true_cov(shift=(0.0, 0.0), grow=0.0, sigma=0.0, wobble=0.0, ss=8):
    """The 'real' veil coverage: a HARD contour of the matte rendered ss times
    finer, grown by `grow` px (optionally wobbling along x), shifted, then
    area-averaged and blurred. Not the model's own rendering path."""
    pm = _pm()
    hi = ov.register_pair_matte((H * ss, W * ss), pm,
                                shift=(shift[0] * ss, shift[1] * ss),
                                centre=(H * ss * 0.65, W * ss / 2.0))
    core = hi >= 0.5
    g = grow * ss
    if wobble:
        xx = np.arange(W * ss)[None, :] / ss
        g = (grow + wobble * np.sin(xx / 23.0)) * ss
    dist_out = ov._edt_capped(core, int(np.ceil(np.max(np.abs(g)))) + 2)
    dist_in = ov._edt_capped(~core, int(np.ceil(np.max(np.abs(g)))) + 2)
    sdh = np.where(core, dist_in - 0.5, -(dist_out - 0.5))
    hard = (sdh + g > 0).astype(np.float64)
    cov = hard.reshape(H, ss, W, ss).mean(axis=(1, 3))
    return np.clip(_gauss(cov, sigma), 0.0, 1.0)


def _art(seed=1, level=150.0):
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:H, 0:W] / float(W)
    out = np.zeros((H, W, 3))
    for c in range(3):
        ph = rng.uniform(0, 6.3, 3)
        out[..., c] = level + 30 * np.sin(4 * xx + ph[0]) * np.cos(3 * yy + ph[1])
    out += _box_mean(rng.normal(0, 1, (H, W)), 9)[..., None] * 25
    out += rng.normal(0, 1.0, out.shape)
    return np.clip(out, 5, 240)


def _veil(art, cov, alpha=ALPHA, halo_k=1.4):
    hal = ov.pair_halo_map(cov, W) * halo_k
    a = (alpha * cov)[..., None]
    k = (alpha * hal)[..., None]
    return np.clip(np.rint(art * (1.0 - a - k) + a * W_MARK), 0, 255)


def _edge_rms(img, art, cov, reach=8):
    core = cov >= 0.5
    band = ov._dilate_bool(core, 2 * reach + 1) & ~ov._erode_bool(core, 2 * reach + 1)
    d = (np.asarray(img, dtype=np.float64) - art).mean(axis=2)
    return float(np.sqrt(np.mean(d[band] ** 2)))


def _halo_mean(img, art, cov):
    core = cov >= 0.5
    band = ov._dilate_bool(core, 25) & ~ov._dilate_bool(core, 9)
    return float((np.asarray(img, dtype=np.float64) - art).mean(axis=2)[band].mean())


@pytest.fixture(scope="module")
def case():
    """One fitted frame shared by the fit tests (the fit is the slow part)."""
    art = _art(1)
    cov_t = _true_cov(shift=(-0.4, 0.3), grow=0.7, sigma=0.4)
    img = _veil(art, cov_t)
    pm = _pm()
    geom = ov.pair_signed_distance((H, W), pm)
    fit = ov.fit_pair_edge(img, geom, pm, ALPHA)
    return {"art": art, "cov": cov_t, "img": img, "pm": pm, "geom": geom,
            "fit": fit}


# ---------------------------------------------------------------- geometry
def test_signed_distance_is_signed_and_subpixel():
    pm = _pm()
    geom = ov.pair_signed_distance((H, W), pm)
    sd = geom["sd"]
    y0, y1, x0, x1 = geom["box"]
    cov = ov.register_pair_matte((H, W), pm)[y0:y1, x0:x1]
    assert (sd[cov >= 0.999] > 0).all()
    assert (sd[cov <= 0.001] < 0).all()
    near = np.abs(sd) < 1.0
    # not quantized to the pixel-centre half-integers
    frac = np.abs(sd[near] * 2 - np.rint(sd[near] * 2))
    assert (frac > 0.05).mean() > 0.3
    assert np.allclose(np.hypot(geom["ny"], geom["nx"])[near], 1.0, atol=1e-3)


def test_signed_distance_none_without_coverage():
    pm = dict(_pm(), window=(1.5, 1.5, 1.6, 1.6))
    assert ov.pair_signed_distance((H, W), pm) is None


def test_edge_profile_is_a_monotone_step():
    x = np.linspace(-6, 6, 121)
    for s in (0.0, 0.5, 1.5):
        p = ov.pair_edge_profile(x, s)
        assert (np.diff(p) >= -1e-12).all()
        assert p[0] < 0.01 and p[-1] > 0.99
        assert ov.pair_edge_profile(np.array([0.0]), s)[0] == pytest.approx(0.5, abs=1e-6)


# ---------------------------------------------------------------- the fit
def test_fit_recovers_shift_offset_and_blur(case):
    th = case["fit"]["theta"]
    # shift is measured against the matte's own contour, offset is outward
    assert th[0] == pytest.approx(-0.4, abs=0.3)
    assert th[1] == pytest.approx(0.3, abs=0.3)
    assert th[2] == pytest.approx(0.7, abs=0.35)
    assert th[3] < 1.0
    assert th[4] > 0.5        # the halo is found
    assert case["fit"]["cost"] < case["fit"]["cost0"]


def test_pass2_inversion_beats_the_old_inversion_at_the_edge(case):
    art, img, pm, geom, cov = case["art"], case["img"], case["pm"], case["geom"], case["cov"]
    th = case["fit"]["theta"]
    new, changed, _sd = ov.remove_pair_edge(img, pm, geom, ALPHA, th)
    shift = ov.refine_pair_shift(img, pm)
    old, _ = ov.remove_overlay(img, None, pair=dict(pm, alpha=ALPHA), pair_shift=shift)
    e_new, e_old = _edge_rms(new, art, cov), _edge_rms(old, art, cov)
    assert e_new < 0.5 * e_old
    # the halo is inverted: the dark band outside the edge goes
    assert _halo_mean(old, art, cov) < -1.0
    assert abs(_halo_mean(new, art, cov)) < 0.5 * abs(_halo_mean(old, art, cov))


def test_outside_the_support_is_byte_identical(case):
    img, pm, geom = case["img"], case["pm"], case["geom"]
    new, changed, sd = ov.remove_pair_edge(img, pm, geom, ALPHA, case["fit"]["theta"])
    src = np.clip(np.rint(img), 0, 255).astype(np.uint8)
    assert new.dtype == np.uint8
    assert (new[~changed] == src[~changed]).all()
    y0, y1, x0, x1 = geom["box"]
    assert not changed[:y0].any() and not changed[y1:].any()
    assert not changed[:, :x0].any() and not changed[:, x1:].any()
    assert np.isinf(sd[0, 0]) and sd[0, 0] < 0


def test_ring_is_cut_from_the_fitted_distance(case):
    _new, _ch, sd = ov.remove_pair_edge(case["img"], case["pm"], case["geom"],
                                        ALPHA, case["fit"]["theta"])
    ring = ov.pair_edge_ring_sd(sd, W)
    r = W / 1920.0
    assert ring.any()
    assert (sd[ring] < ov.EDGE_RING_IN * r).all()
    assert (sd[ring] > -ov.EDGE_RING_OUT * r).all()


def test_local_offsets_follow_a_wobbling_contour():
    art = _art(2)
    cov_t = _true_cov(grow=0.4, wobble=0.8, sigma=0.3)
    img = _veil(art, cov_t)
    pm = _pm()
    geom = ov.pair_signed_distance((H, W), pm)
    th = ov.fit_pair_edge(img, geom, pm, ALPHA, rounds=1, iters=10)["theta"]
    off = ov.pair_edge_offsets(img, geom, pm, ALPHA, th)
    glob, _c, _s = ov.remove_pair_edge(img, pm, geom, ALPHA, th)
    loc, _c, _s = ov.remove_pair_edge(img, pm, geom, ALPHA, th, offset=off)
    assert off.shape == geom["sd"].shape
    assert _edge_rms(loc, art, cov_t) < 0.8 * _edge_rms(glob, art, cov_t)


def test_fit_is_deterministic(case):
    again = ov.fit_pair_edge(case["img"].copy(), case["geom"], case["pm"], ALPHA)
    assert again["theta"] == case["fit"]["theta"]


# ---------------------------------------------------------------- the lane
def _bgr(img):
    return np.ascontiguousarray(np.asarray(img)[:, :, ::-1].astype(np.uint8))


def test_prepass_default_is_the_old_path_byte_for_byte(case):
    bgr = _bgr(case["img"])
    a = IO.overlay_prepass(bgr, None, None, pair=case["pm"], return_ring=True)
    b = IO.overlay_prepass(bgr, None, None, pair=case["pm"], return_ring=True,
                           edge_fit=False)
    assert (a[0] == b[0]).all() and (a[4] == b[4]).all()
    assert "edge_fit" not in a[3]["pair"]


def test_prepass_edge_fit_records_the_fit_and_cuts_the_new_ring(case):
    bgr = _bgr(case["img"])
    pre, mask, roi, info, ring = IO.overlay_prepass(
        bgr, None, None, pair=case["pm"], return_ring=True, edge_fit=True)
    ef = info["pair"]["edge_fit"]
    assert len(ef["theta"]) == 6 and ef["local_offsets"] is True
    assert info["pair"]["ring_px"] == int(ring.sum())
    assert (mask[ring] == 255).all()
    support = info.pop("_edge_support")
    cov = info.pop("_edge_cov")
    assert cov.shape == support.shape and cov.dtype == np.float32
    assert 0.0 <= cov.min() and cov.max() <= 1.0 and (cov > 0.5).any()
    src = case["img"].astype(np.uint8)[:, :, ::-1]
    assert (pre[~support] == src[~support]).all()
    old = IO.overlay_prepass(bgr, None, None, pair=case["pm"])[0]
    art = case["art"][:, :, ::-1]
    assert _edge_rms(pre, art, case["cov"]) < _edge_rms(old, art, case["cov"])
