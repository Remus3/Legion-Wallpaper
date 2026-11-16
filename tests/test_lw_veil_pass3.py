"""Pass-3 border fixes for the DA logo pair matte (2026-11-15).

Operator order: the pass-2 NEEDAUTHs still show LOCAL border defects - a dark
dot at the left-arm tip, LaMa blotches at the right arm's bottom edge, a faint
line on the left arm's top edge. Measured on the purchased pairs run through
the real upscale chain (docs/_archive/2026-11/VEIL_PASS3_2026-11-15.md):

  * the true local edge position, read against the ground-truth clean frame,
    is ~85 percent STATIC: a field along the matte contour (LOO correlation
    0.84-0.89 between pairs, p10/p90 -0.6/+0.8 ref px) that the per-frame
    offset (aggregated over 10 ref px, read from the art) only half recovers.
    At the bay end of the tip it is a ~0.7 px error the per-frame field cannot
    follow -> over-removal -> 2-3 dark pixels at the ring's inner boundary,
    which LaMa grows into a dot;
  * where the ring runs over a strong art edge at a shallow angle, LaMa
    cannot place that edge in a 5 px strip and smears colour across it, far
    outside what the veil could have done there.

These tests pin the fixes on hermetic fixtures whose veil edge is rendered
INDEPENDENTLY of the model (a hard contour rendered 8x finer, grown by a
STATIC location-dependent field, shifted, blurred):

  * `render_pair_grid` / `pair_grid_coords` agree and scale with the frame;
  * `pair_signed_distance(edge_corr=None)` is the pass-2 geometry byte for
    byte;
  * a static edge correction learned from two training frames
    (`pair_true_edge_offsets` + `build_pair_edge_corr`) removes the local
    residue on a held-out frame with different art and registration;
  * `pair_ring_envelope` contains the true art when the edge is off by less
    than its tolerance, and `bound_ring_fill` clamps an invented blotch while
    leaving a correct fill untouched and every pixel outside the region
    byte-identical;
  * `overlay_prepass(edge_corr=..., ring_bound=True)` records both and the
    defaults are the pass-2 path byte for byte.

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
GH, GW = 380, 300
# the bay end of the fixture's notch (grid u, v) and its frame position
BAY_UV = (0.636, 0.475)
BAY_YX = ((WINDOW[1] + BAY_UV[1] * (WINDOW[3] - WINDOW[1])) * H,
          (WINDOW[0] + BAY_UV[0] * (WINDOW[2] - WINDOW[0])) * W)


def _logo_grid(gh=GH, gw=GW, ss=4):
    yy, xx = np.mgrid[0:gh * ss, 0:gw * ss].astype(np.float64)
    u, v = xx / (gw * ss), yy / (gh * ss)
    body = (v > 0.08) & (v < 0.92) & (u > 0.12 + 0.18 * v) & (u < 0.70 + 0.18 * v)
    notch = (v > 0.40) & (v < 0.55) & (u > 0.55 + 0.18 * v)
    m = (body & ~notch).astype(np.float64)
    m = m.reshape(gh, ss, gw, ss).mean(axis=(1, 3))
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


def _static_error(yy, xx):
    """The template's STATIC shape error (frame px, + = true edge further
    out), as a function of position relative to the logo: a 1.2 px bump at
    the bay end of the notch and a +-0.6 px wobble along the top edge."""
    by, bx = BAY_YX
    bump = 1.2 * np.exp(-((yy - by) ** 2 + (xx - bx) ** 2) / (2 * 5.0 ** 2))
    top = (WINDOW[1] + 0.08 * (WINDOW[3] - WINDOW[1])) * H
    wob = 0.6 * np.sin(xx / 9.0) * np.exp(-((yy - top) ** 2) / (2 * 6.0 ** 2))
    return bump + wob


def _true_cov(shift=(0.0, 0.0), grow=0.5, sigma=0.35, ss=8):
    """The 'real' veil coverage: the matte's HARD contour rendered ss times
    finer, grown by `grow` plus the static error (which moves with the logo),
    shifted, area-averaged and blurred. Not the model's own rendering path."""
    pm = _pm()
    hi = ov.register_pair_matte((H * ss, W * ss), pm,
                                shift=(shift[0] * ss, shift[1] * ss))
    ys, xs = np.nonzero(hi > 0)
    # work on the logo's crop (frame-px aligned) to keep the fixture small
    fy0, fy1 = ys.min() // ss - 6, ys.max() // ss + 7
    fx0, fx1 = xs.min() // ss - 6, xs.max() // ss + 7
    core = hi[fy0 * ss:fy1 * ss, fx0 * ss:fx1 * ss] >= 0.5
    del hi
    yy, xx = np.mgrid[fy0 * ss:fy1 * ss, fx0 * ss:fx1 * ss].astype(np.float64)
    g = (grow + _static_error(yy / ss - shift[0], xx / ss - shift[1])) * ss
    del yy, xx
    cap = int(np.ceil(np.max(np.abs(g)))) + 2
    sdh = np.where(core, ov._edt_capped(~core, cap) - 0.5,
                   -(ov._edt_capped(core, cap) - 0.5))
    hard = (sdh + g > 0).astype(np.float64)
    ch, cw = fy1 - fy0, fx1 - fx0
    cov = np.zeros((H, W))
    cov[fy0:fy1, fx0:fx1] = hard.reshape(ch, ss, cw, ss).mean(axis=(1, 3))
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


def _veil(art, cov, alpha=ALPHA, halo_k=1.2):
    hal = ov.pair_halo_map(cov, W) * halo_k
    a = (alpha * cov)[..., None]
    k = (alpha * hal)[..., None]
    return np.clip(np.rint(art * (1.0 - a - k) + a * W_MARK), 0, 255)


def _shifted_geom(pm, shift, edge_corr=None):
    return ov.pair_signed_distance((H, W), pm, shift=shift, edge_corr=edge_corr)


def _bay_rms(img, art):
    by, bx = BAY_YX
    yy, xx = np.mgrid[0:H, 0:W]
    m = (yy - by) ** 2 + (xx - bx) ** 2 < 8.0 ** 2
    d = (np.asarray(img, dtype=np.float64) - art).mean(axis=2)
    return float(np.sqrt(np.mean(d[m] ** 2)))


def _edge_rms(img, art, cov, reach=6):
    core = cov >= 0.5
    band = ov._dilate_bool(core, 2 * reach + 1) & ~ov._erode_bool(core, 2 * reach + 1)
    d = (np.asarray(img, dtype=np.float64) - art).mean(axis=2)
    return float(np.sqrt(np.mean(d[band] ** 2)))


# ---------------------------------------------------------------- the grid
def test_render_grid_is_constant_scaled_and_zero_outside():
    pm = _pm()
    grid = np.full((GH, GW), 0.75)
    out = ov.render_pair_grid((H, W), pm, grid)
    yc, xc = int(0.5 * H), int(0.5 * W)
    assert out[yc, xc] == pytest.approx(0.75 * W / 1920.0, abs=1e-9)
    assert out[0, 0] == 0.0 and out[-1, -1] == 0.0
    big = ov.render_pair_grid((2 * H, 2 * W), pm, grid)
    assert big[2 * yc, 2 * xc] == pytest.approx(2 * out[yc, xc], abs=1e-9)


def test_grid_coords_agree_with_the_render():
    pm = _pm()
    gy_ramp = np.repeat(np.arange(GH, dtype=np.float64)[:, None], GW, axis=1)
    gx_ramp = np.repeat(np.arange(GW, dtype=np.float64)[None, :], GH, axis=0)
    sh, sc = (3.3, -2.1), 1.07
    ry = ov.render_pair_grid((H, W), pm, gy_ramp, shift=sh, scale=sc) / (W / 1920.0 * sc)
    rx = ov.render_pair_grid((H, W), pm, gx_ramp, shift=sh, scale=sc) / (W / 1920.0 * sc)
    ys, xs = np.array([300, 360, 420]), np.array([600, 640, 700])
    gy, gx = ov.pair_grid_coords(ys, xs, (H, W), pm, shift=sh, scale=sc)
    assert np.allclose(gy, ry[ys, xs], atol=1e-6)
    assert np.allclose(gx, rx[ys, xs], atol=1e-6)


def test_signed_distance_without_correction_is_the_pass2_geometry():
    pm = _pm()
    a = ov.pair_signed_distance((H, W), pm)
    b = ov.pair_signed_distance((H, W), pm, edge_corr=None)
    z = ov.pair_signed_distance((H, W), pm, edge_corr=np.zeros((GH, GW)))
    for k in ("sd", "ny", "nx"):
        assert (a[k] == b[k]).all()
        assert np.allclose(a[k], z[k], atol=1e-12)
    assert a["box"] == b["box"] == z["box"]


def test_edge_corr_round_trips(tmp_path):
    grid = np.random.default_rng(0).normal(0, 0.3, (GH, GW)).astype(np.float32)
    p = ov.save_pair_edge_corr(str(tmp_path / "corr.npz"), grid,
                               sources="synthetic", n_frames=2)
    got = ov.load_pair_edge_corr(p)
    assert got["n_frames"] == 2 and got["sources"] == "synthetic"
    assert np.allclose(got["grid"], grid)
    assert ov.load_pair_edge_corr(str(tmp_path / "missing.npz")) is None


# ---------------------------------------------------------------- learn -> apply
@pytest.fixture(scope="module")
def learned():
    pm = _pm()
    samples = []
    for seed, sh in ((3, (0.3, -0.2)), (4, (-0.25, 0.35))):
        art = _art(seed)
        img = _veil(art, _true_cov(shift=sh))
        geom = _shifted_geom(pm, sh)
        th = ov.fit_pair_edge(img, geom, pm, ALPHA, rounds=1, iters=10)["theta"]
        got = ov.pair_true_edge_offsets(img, art, geom, pm, ALPHA, th)
        gy, gx = ov.pair_grid_coords(got["ys"], got["xs"], (H, W), pm, shift=sh)
        samples.append((gy, gx, got["v"] * 1920.0 / W))
    grid = ov.build_pair_edge_corr(samples, (GH, GW))
    # held-out frame: other art, other registration
    sh = (-0.1, -0.3)
    art = _art(5)
    img = _veil(art, _true_cov(shift=sh))
    out = {"pm": pm, "grid": grid, "art": art, "img": img,
           "cov": _true_cov(shift=sh)}
    for name, corr in (("p2", None), ("p3", grid)):
        geom = _shifted_geom(pm, sh, edge_corr=corr)
        th = ov.fit_pair_edge(img, geom, pm, ALPHA, rounds=1, iters=10)["theta"]
        off = ov.pair_edge_offsets(img, geom, pm, ALPHA, th)
        pre, ch, sd = ov.remove_pair_edge(img, pm, geom, ALPHA, th, offset=off)
        out[name] = {"pre": pre, "geom": geom, "theta": th, "off": off,
                     "changed": ch}
    return out


def test_learned_correction_finds_the_static_bump(learned):
    pm, grid = learned["pm"], learned["grid"]
    gy, gx = ov.pair_grid_coords(np.array([BAY_YX[0]]), np.array([BAY_YX[1]]),
                                 (H, W), pm)
    v = grid[int(round(gy[0])), int(round(gx[0]))] * W / 1920.0
    assert v > 0.5          # the 1.2 px bump, pooled over a few px
    assert np.isfinite(grid).all()


def test_static_correction_removes_the_bay_end_residue_on_a_held_out_frame(learned):
    art = learned["art"]
    e2 = _bay_rms(learned["p2"]["pre"], art)
    e3 = _bay_rms(learned["p3"]["pre"], art)
    assert e3 < 0.6 * e2
    # and the whole border is not worse
    assert (_edge_rms(learned["p3"]["pre"], art, learned["cov"])
            < _edge_rms(learned["p2"]["pre"], art, learned["cov"]))


# ---------------------------------------------------------------- bounded ring
def test_envelope_contains_the_art_when_the_edge_is_off_by_less_than_delta(learned):
    pm, art, img = learned["pm"], learned["art"], learned["img"]
    st = learned["p3"]
    th = list(st["theta"])
    th[2] += 0.5            # the model edge 0.5 px off: inside the tolerance
    lo, hi = ov.pair_ring_envelope(img, pm, st["geom"], ALPHA, th,
                                   offset=st["off"])
    _p, _c, sd = ov.remove_pair_edge(img, pm, st["geom"], ALPHA, th, offset=st["off"])
    ring = ov.pair_edge_ring_sd(sd, W)
    inside = (art >= lo - 1e-6) & (art <= hi + 1e-6)
    assert inside[ring].mean() > 0.97
    assert (hi >= lo).all()


def test_bound_ring_fill_clamps_a_blotch_and_keeps_a_correct_fill(learned):
    pm, art, img = learned["pm"], learned["art"], learned["img"]
    st = learned["p3"]
    lo, hi = ov.pair_ring_envelope(img, pm, st["geom"], ALPHA, st["theta"],
                                   offset=st["off"])
    _p, _c, sd = ov.remove_pair_edge(img, pm, st["geom"], ALPHA, st["theta"],
                                     offset=st["off"])
    ring = ov.pair_edge_ring_sd(sd, W)
    ideal = np.asarray(st["pre"]).copy()
    ideal[ring] = np.clip(np.rint(art[ring]), 0, 255).astype(np.uint8)
    blot = ideal.copy()
    yy, xx = np.nonzero(ring)
    k = np.argsort(xx)[: max(len(xx) // 40, 30)]
    blot[yy[k], xx[k]] = np.clip(art[yy[k], xx[k]] + [90.0, -60.0, 40.0], 0, 255)
    got_ideal = ov.bound_ring_fill(ideal, lo, hi, ring)
    got_blot = ov.bound_ring_fill(blot, lo, hi, ring)
    assert got_ideal.dtype == np.uint8
    # a correct fill is (all but) untouched
    assert (got_ideal != ideal).any(axis=-1)[ring].mean() < 0.03
    # the blotch is pulled back into the physically possible band
    e_before = np.abs(blot[yy[k], xx[k]].astype(float) - art[yy[k], xx[k]]).mean()
    e_after = np.abs(got_blot[yy[k], xx[k]].astype(float) - art[yy[k], xx[k]]).mean()
    assert e_after < 0.35 * e_before
    # outside the region: byte-identical
    assert (got_blot[~ring] == blot[~ring]).all()


# ---------------------------------------------------------------- the lane
def _bgr(img):
    return np.ascontiguousarray(np.asarray(img)[:, :, ::-1].astype(np.uint8))


def test_prepass_pass3_defaults_are_the_pass2_path(learned):
    bgr = _bgr(learned["img"])
    a = IO.overlay_prepass(bgr, None, None, pair=learned["pm"], return_ring=True,
                           edge_fit=True)
    b = IO.overlay_prepass(bgr, None, None, pair=learned["pm"], return_ring=True,
                           edge_fit=True, edge_corr=None, ring_bound=False)
    assert (a[0] == b[0]).all() and (a[4] == b[4]).all()
    assert "_ring_env" not in b[3]
    assert b[3]["pair"]["edge_fit"].get("edge_corr") is False


def test_prepass_pass3_records_the_correction_and_the_envelope(learned):
    bgr = _bgr(learned["img"])
    pre, mask, roi, info, ring = IO.overlay_prepass(
        bgr, None, None, pair=learned["pm"], return_ring=True, edge_fit=True,
        edge_corr=learned["grid"], ring_bound=True)
    assert info["pair"]["edge_fit"]["edge_corr"] is True
    lo, hi = info.pop("_ring_env")
    assert lo.shape == hi.shape == bgr.shape
    assert (hi[ring] >= lo[ring]).all()
    # the envelope is in the frame's (BGR) channel order, like the frame
    fill = bgr.copy()
    fill[ring] = 0
    got = IO.apply_ring_bound(fill, (lo, hi), ring)
    assert (got[~ring] == fill[~ring]).all()
    assert (got[ring] >= np.floor(lo[ring]) - 1).all()


# ---------------------------------------------------------------- scale
def test_refine_scale_finds_a_scale_between_the_search_steps():
    """blood-moon was registered at the search grid's 1.08 for a true ~1.065:
    off by up to +-2 px across the logo, which the edge fit then smeared
    (dy and d0 at their bounds). The fine scale search recovers it."""
    pm = _pm()
    true_s = 1.018
    cov = ov.register_pair_matte((H, W), pm, scale=true_s)
    art = _art(7)
    img = _veil(art, np.clip(_gauss(cov, 0.4), 0, 1))
    got = ov.refine_pair_scale(img, pm, shift=(0.0, 0.0), scale=1.0)
    assert got["scale"] == pytest.approx(true_s, abs=0.004)
    assert got["score"] >= got["score0"]
    # already right: it stays put
    again = ov.refine_pair_scale(img, pm, shift=got["shift"], scale=true_s)
    assert again["scale"] == pytest.approx(true_s, abs=0.003)


def test_prepass_pass3_info_is_json_serializable(learned):
    """The lane writes info into the manifest params (json.dumps); the first
    live pass-3 run died on an ndarray in it."""
    import json
    bgr = _bgr(learned["img"])
    _pre, _m, _roi, info = IO.overlay_prepass(
        bgr, None, None, pair=learned["pm"], edge_fit=True,
        edge_corr=learned["grid"], ring_bound=True)
    for k in ("_edge_support", "_edge_cov", "_ring_env"):
        info.pop(k)
    json.dumps(info)


def test_clean_slug_pass3_end_to_end_with_a_stub_inpainter(learned, tmp_path, monkeypatch):
    """clean_slug(pass3=True): the ring fill is clamped, only inside the mask,
    and the manifest params stay JSON (the first live run shadowed `region`
    with the clamp's boolean map and died in json.dumps)."""
    import contextlib
    import json

    from PIL import Image

    import lw_clean_pass as C
    src = tmp_path / "s_cleaninitial.png"
    Image.fromarray(np.asarray(learned["img"]).astype(np.uint8)).save(src)
    monkeypatch.setattr(IO.OV, "load_pair_matte", lambda *a, **k: learned["pm"])
    monkeypatch.setattr(IO.OV, "load_pair_edge_corr",
                        lambda *a, **k: {"grid": learned["grid"], "sources": "t", "n_frames": 2})
    monkeypatch.setattr(IO, "load_overlay_pair", lambda: (None, None))
    monkeypatch.setattr(IO.OV, "load_template", lambda *a, **k: None)
    monkeypatch.setattr(C, "_cuda_device", lambda: "cpu")
    monkeypatch.setattr(C, "gpu_lock", lambda *a, **k: contextlib.nullcontext())
    monkeypatch.setattr(IO, "_load_lama", lambda dev=None: (None, "cpu"))

    def blotchy(roi, mask, lama):      # a "LaMa" that paints the mask magenta
        out = np.asarray(roi).copy()
        out[np.asarray(mask) > 127] = (255, 0, 255)
        return out
    monkeypatch.setattr(IO, "inpaint_once", blotchy)
    rec = IO.clean_slug("s", image=str(src), overlay=True, pass3=True,
                        out_dir=str(tmp_path / "out"), log=lambda *a, **k: None)
    assert rec["status"] == "cleaned", rec
    assert all(isinstance(v, int) for v in rec["region"])
    side = json.load(open(tmp_path / "out" / "s_iopaint.json"))
    rb = side["params"]["overlay"]["ring_bound"]
    assert rb["clamped_px"] > 0.9 * rb["region_px"] > 0
    cand = np.asarray(Image.open(rec["cand"]).convert("RGB")).astype(float)
    art = learned["art"]
    _p, _c, sd = ov.remove_pair_edge(learned["img"], learned["pm"],
                                     learned["p3"]["geom"], ALPHA,
                                     learned["p3"]["theta"])
    ring = ov.pair_edge_ring_sd(sd, W)
    # magenta (~120 levels off) never survives in the ring: the clamp holds
    # it to the veil band, which is never narrower than pre-pass +- PAIR_RING_TOL
    assert np.abs(cand[ring] - art[ring]).mean() < ov.PAIR_RING_TOL + 4.0


def test_envelope_never_clamps_a_fill_within_tol_of_the_pre_pass(learned):
    """261f with a purely physical band (tol 0): where the pre-pass residue
    exceeded the band, the clamp put the fill back onto the residual line
    LaMa had removed (ghost 0.54 -> 0.66 at the top corner). A change of up
    to PAIR_RING_TOL levels from the pre-pass is always allowed."""
    pm, img = learned["pm"], learned["img"]
    st = learned["p3"]
    lo, hi = ov.pair_ring_envelope(img, pm, st["geom"], ALPHA, st["theta"],
                                   offset=st["off"])
    lo0, hi0 = ov.pair_ring_envelope(img, pm, st["geom"], ALPHA, st["theta"],
                                     offset=st["off"], tol=0.0)
    _p, _c, sd = ov.remove_pair_edge(img, pm, st["geom"], ALPHA, st["theta"],
                                     offset=st["off"])
    ring = ov.pair_edge_ring_sd(sd, W)
    pre = np.asarray(st["pre"]).astype(np.float64)
    shifted = np.clip(pre + ov.PAIR_RING_TOL - 4.0, 0, 255).astype(np.uint8)
    keep = ov.bound_ring_fill(shifted, lo, hi, ring)
    assert (keep[ring] == shifted[ring]).mean() > 0.98
    cut = ov.bound_ring_fill(shifted, lo0, hi0, ring)
    assert (cut[ring] != shifted[ring]).any(axis=-1).mean() > 0.3
