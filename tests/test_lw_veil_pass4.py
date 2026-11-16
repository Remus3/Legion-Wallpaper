"""Pass-4 fixes for the DA logo veil (2026-11-15).

Operator review after pass 3: "still some off color on the veil - and the
signature line needs work ... there are still after edit shading and
inconsistency remaining". Measured on the purchased pairs run through the real
upscale chain (docs/_archive/2026-11/VEIL_PASS4_2026-11-15.md):

  * the fill alpha is not one scalar: it falls from the logo's top to its
    foot (the same static field on A, B and C) and the per-frame fit, read at
    the edge, sits under the true alpha - a scalar inversion leaves a
    top-to-foot shading and, on chromatic art, a tint;
  * the credit line is the same semi-transparent white text with a dark rim,
    centred under the logo; the lane missed its end glyphs and repainted the
    art between them.

Hermetic fixtures: a veil with an independent top-to-foot alpha ramp
composited on synthetic art; a synthetic credit line of glyph blocks (white
fill + dark rim) over art. numpy + PIL only, Linux-safe.
"""
from __future__ import annotations

import os
import sys

import numpy as np
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "tools"))
sys.path.insert(0, HERE)
import lw_clean_iopaint as IO  # noqa: E402
import lw_clean_overlay as ov  # noqa: E402
import lw_veil_credit as CR  # noqa: E402
import lw_veil_shading as SH  # noqa: E402
from test_lw_veil_pass3 import (  # noqa: E402
    ALPHA, GH, GW, H, W, W_MARK, WINDOW, _art, _pm)

THETA = [0.0, 0.0, 0.0, 0.35, 0.0, 1.0]     # no shift / offset, no halo
RAMP = 0.24                                   # alpha falls 24 percent top->foot


def _geom(pm, shift=(0.0, 0.0)):
    return ov.pair_signed_distance((H, W), pm, shift=shift)


def _ramp_full(pm, shift=(0.0, 0.0)):
    """The TRUE per-pixel alpha multiplier: a linear top-to-foot fall across
    the logo, written in frame coordinates (independent of the grid code)."""
    cov = ov.register_pair_matte((H, W), pm, shift=shift)
    ys = np.nonzero(cov >= 0.5)[0]
    yc, lh = 0.5 * (ys.min() + ys.max()), float(ys.max() - ys.min())
    yy = np.arange(H, dtype=np.float64)[:, None] * np.ones((1, W))
    return 1.0 + 0.1 - RAMP * (yy - yc) / lh   # mean 1.1: the fit's bias


def _veil_ramp(art, pm, alpha, shift=(0.0, 0.0)):
    geom = _geom(pm, shift)
    y0, y1, x0, x1 = geom["box"]
    p, _g = ov.pair_edge_maps(geom, W, THETA, alpha)
    a = np.zeros((H, W))
    a[y0:y1, x0:x1] = alpha * p
    a = a * _ramp_full(pm, shift)
    return np.clip(np.rint(art * (1 - a[..., None]) + a[..., None] * W_MARK), 0, 255)


def _interior(pm, shift=(0.0, 0.0), inset=4.0):
    geom = _geom(pm, shift)
    m = np.zeros((H, W), dtype=bool)
    y0, y1, x0, x1 = geom["box"]
    m[y0:y1, x0:x1] = geom["sd"] * 1920.0 / W > inset
    return m


def _logo_grid_bool(pm):
    return np.asarray(pm["shape"], dtype=np.float64) > 0.5


@pytest.fixture(scope="module")
def field():
    pm = _pm()
    frames = []
    for seed, sh in ((11, (0.0, 0.0)), (12, (2.0, -3.0))):
        art = _art(seed, level=110.0)
        img = _veil_ramp(art, pm, ALPHA, sh)
        num, den = ov.pair_true_alpha_sums(img, art, _interior(pm, sh), (H, W),
                                           pm, shift=sh)
        frames.append((num, den, ALPHA))
    grid, info = ov.build_pair_alpha_field(frames, _logo_grid_bool(pm), sigma=6.0)
    return {"pm": pm, "grid": grid, "info": info}


# ---------------------------------------------------------------- the field
def test_field_learns_the_fall_and_the_fit_bias(field):
    g, pm = field["grid"], field["pm"]
    logo = _logo_grid_bool(pm)
    rows = np.nonzero(logo.any(axis=1))[0]
    top = g[rows[: len(rows) // 5]][logo[rows[: len(rows) // 5]]].mean()
    foot = g[rows[-len(rows) // 5:]][logo[rows[-len(rows) // 5:]]].mean()
    assert top > foot + 0.12          # the true fall is 0.24 over the height
    assert field["info"]["kappa_mean"] > 1.0   # the fixture's fit sits low


def test_field_removes_the_shading_on_a_held_out_frame(field):
    pm, grid = field["pm"], field["grid"]
    sh = (-1.5, 2.5)
    art = _art(13, level=110.0)
    img = _veil_ramp(art, pm, ALPHA, sh)
    geom = _geom(pm, sh)
    inner = _interior(pm, sh, inset=6.0)
    ys = np.nonzero(inner)[0]
    top = inner & (np.arange(H)[:, None] < ys.min() + (ys.max() - ys.min()) / 4)
    foot = inner & (np.arange(H)[:, None] > ys.max() - (ys.max() - ys.min()) / 4)
    out = {}
    for name, f in (("scalar", None),
                    ("field", ov.pair_alpha_field_crop((H, W), pm, grid, geom,
                                                       shift=sh))):
        pre, _c, _s = ov.remove_pair_edge(img, pm, geom, ALPHA, THETA,
                                          alpha_field=f)
        d = (pre.astype(np.float64) - art).mean(axis=2)
        out[name] = (d[top].mean() - d[foot].mean(), np.abs(d[inner]).mean())
    assert abs(out["scalar"][0]) > 3.0            # the shading the operator saw
    assert abs(out["field"][0]) < 0.35 * abs(out["scalar"][0])
    assert out["field"][1] < 0.5 * out["scalar"][1]


def test_remove_without_field_is_the_pass3_inversion_byte_for_byte(field):
    pm = field["pm"]
    img = _veil_ramp(_art(14), pm, ALPHA)
    geom = _geom(pm)
    a = ov.remove_pair_edge(img, pm, geom, ALPHA, THETA)
    b = ov.remove_pair_edge(img, pm, geom, ALPHA, THETA, alpha_field=None)
    assert all((x == y).all() for x, y in zip(a, b, strict=True))
    ones = np.ones(geom["sd"].shape)
    c = ov.remove_pair_edge(img, pm, geom, ALPHA, THETA, alpha_field=ones)
    assert np.abs(c[0].astype(int) - a[0].astype(int)).max() <= 1
    lo, hi = ov.pair_ring_envelope(img, pm, geom, ALPHA, THETA)
    lo2, hi2 = ov.pair_ring_envelope(img, pm, geom, ALPHA, THETA, alpha_field=None)
    assert (lo == lo2).all() and (hi == hi2).all()


def test_envelope_follows_the_field(field):
    pm = field["pm"]
    img = _veil_ramp(_art(15), pm, ALPHA)
    geom = _geom(pm)
    f = np.full(geom["sd"].shape, 1.3)
    lo, _hi = ov.pair_ring_envelope(img, pm, geom, ALPHA, THETA, tol=0.0)
    lo2, _hi2 = ov.pair_ring_envelope(img, pm, geom, ALPHA, THETA, tol=0.0,
                                      alpha_field=f)
    y0, y1, x0, x1 = geom["box"]
    inside = geom["sd"] > 3
    # a stronger veil inverts to darker art: the band's floor moves down
    assert (lo2[y0:y1, x0:x1][inside] <= lo[y0:y1, x0:x1][inside] + 1e-9).all()
    assert (lo2[y0:y1, x0:x1][inside] < lo[y0:y1, x0:x1][inside] - 1).mean() > 0.5


def test_render_ratio_is_unitless_and_one_off_the_window():
    pm = _pm()
    grid = np.full((GH, GW), 1.25)
    out = ov.render_pair_ratio((H, W), pm, grid, shift=(2.0, -1.0), scale=1.05)
    assert out[int(0.5 * H), int(0.5 * W)] == pytest.approx(1.25, abs=1e-9)
    assert out[0, 0] == 1.0 and out[-1, -1] == 1.0
    assert WINDOW[0] < 0.5 < WINDOW[2]


def test_alpha_field_round_trips_and_rejects_a_bad_file(tmp_path, field):
    p = ov.save_pair_alpha_field(str(tmp_path / "f.npz"), field["grid"],
                                 sources="synthetic", n_frames=2, kappa=1.07)
    got = ov.load_pair_alpha_field(p)
    assert got["n_frames"] == 2 and got["kappa"] == pytest.approx(1.07)
    assert np.allclose(got["grid"], field["grid"], atol=1e-6)
    bad = ov.save_pair_alpha_field(str(tmp_path / "b.npz"),
                                   np.full((GH, GW), 3.0))
    assert ov.load_pair_alpha_field(bad) is None
    assert ov.load_pair_alpha_field(str(tmp_path / "missing.npz")) is None


def _bgr(img):
    return np.ascontiguousarray(np.asarray(img)[:, :, ::-1].astype(np.uint8))


def test_prepass_field_default_is_the_pass3_path_and_records_the_field(field):
    pm = field["pm"]
    bgr = _bgr(_veil_ramp(_art(16), pm, ALPHA))
    a = IO.overlay_prepass(bgr, None, None, pair=pm, return_ring=True, edge_fit=True)
    b = IO.overlay_prepass(bgr, None, None, pair=pm, return_ring=True, edge_fit=True,
                           alpha_field=None)
    assert (a[0] == b[0]).all() and "alpha_field" not in b[3]["pair"]
    c = IO.overlay_prepass(bgr, None, None, pair=pm, return_ring=True, edge_fit=True,
                           alpha_field=field["grid"])
    assert "alpha_field" in c[3]["pair"]
    assert (c[0] != a[0]).any()


# ---------------------------------------------------------------- shading metric
def test_shading_metric_ranks_alpha_errors_and_reads_clean_art_low(field):
    pm = field["pm"]
    art = _art(17, level=110.0)
    img = _veil_ramp(art, pm, ALPHA)
    geom = _geom(pm)
    cov = ov.register_pair_matte((H, W), pm)
    truth_f = ov.pair_alpha_field_crop((H, W), pm, np.ones((GH, GW)), geom)
    y0, y1, x0, x1 = geom["box"]
    true_f = _ramp_full(pm)[y0:y1, x0:x1]
    reads = []
    for err in (0.0, 0.1, 0.25, 0.5):
        f = true_f * (1.0 - err) + truth_f * err * 1.0
        pre, _c, _s = ov.remove_pair_edge(img, pm, geom, ALPHA, THETA, alpha_field=f)
        reads.append(SH.boundary_step(pre, cov)["step_de_rms"])
    assert reads == sorted(reads)
    assert reads[-1] > reads[0] + 0.25
    clean = SH.boundary_step(art, cov)["step_de_rms"]
    assert clean < SH.SHADING_GATE


def test_shading_metric_never_calls_the_fit_or_the_field(monkeypatch):
    pm = _pm()
    cov = ov.register_pair_matte((H, W), pm)

    def boom(*a, **k):
        raise AssertionError("the metric must stay independent of the fix")
    for name in ("fit_pair_alpha", "fit_pair_edge", "render_pair_ratio",
                 "pair_alpha_field_crop", "remove_pair_edge"):
        monkeypatch.setattr(SH.OV, name, boom)
    assert SH.boundary_step(_art(18), cov) is not None


# ---------------------------------------------------------------- credit line
A_TXT = 0.145
RIM = 0.25


def _credit_scene(seed=21, n_glyphs=14):
    """Art + the logo coverage + a centred credit line of glyph blocks (white
    fill A_TXT, a 2 px dark rim RIM) in the fixed text row."""
    pm = _pm()
    cov = ov.register_pair_matte((H, W), pm)
    r0, r1, cx, lh = CR.credit_rows(cov)
    art = _art(seed, level=120.0)
    th = r1 - r0
    gw, gap = int(0.6 * th), int(0.25 * th)
    total = n_glyphs * gw + (n_glyphs - 1) * gap
    x = int(cx - total / 2)
    fill = np.zeros((H, W), dtype=bool)
    for _ in range(n_glyphs):
        fill[r0 + 4:r1 - 4, x:x + gw] = True
        fill[r0 + 4 + th // 3:r0 + 4 + th // 3 + 3, x + 2:x + gw - 2] = False
        x += gw + gap
    rim = CR._dilate(fill, 2) & ~fill
    img = art * (1 - A_TXT * fill[..., None]) + A_TXT * W_MARK * fill[..., None]
    img = img * (1 - RIM * rim[..., None])
    return {"art": art, "img": np.clip(np.rint(img), 0, 255), "cov": cov,
            "fill": fill, "rim": rim, "span": (int(cx - total / 2), x - gap)}


def test_locate_mirrors_the_detected_reach_to_cover_both_ends():
    s = _credit_scene()
    seed = np.zeros((H, W), dtype=bool)
    # the lane's detection found only the LEFT half of the text
    xl, xr = s["span"]
    seed[s["fill"] & (np.arange(W)[None, :] < 0.5 * (xl + xr))] = True
    loc = CR.locate_credit(seed, s["cov"])
    assert loc is not None
    c0, c1 = loc["cols"]
    assert c0 <= xl and c1 >= xr                  # both end glyphs inside
    r0, r1 = loc["rows"]
    ys = np.nonzero(s["fill"] | s["rim"])[0]
    assert r0 - 2 <= ys.min() and ys.max() < r1 + 2
    assert CR.locate_credit(np.zeros((H, W), dtype=bool), s["cov"]) is None


def test_credit_box_holds_every_glyph_and_its_rim():
    s = _credit_scene(n_glyphs=18)
    seed = s["fill"] & (np.arange(W)[None, :] > 0.5 * sum(s["span"]))   # right half
    box = CR.credit_box_mask((H, W), CR.locate_credit(seed, s["cov"]))
    assert box[s["fill"] | s["rim"]].all()
    # and it stays a text box: no taller than the row, not the whole frame
    ys = np.nonzero(box.any(axis=1))[0]
    assert ys.max() - ys.min() < 0.12 * H


def test_clean_slug_pass4_masks_the_whole_credit_box_and_keeps_the_ring(
        field, tmp_path, monkeypatch):
    import contextlib
    import json

    from PIL import Image

    import lw_clean_pass as C
    s = _credit_scene(seed=22)
    pm = field["pm"]
    img = _veil_ramp(s["img"], pm, ALPHA)
    src = tmp_path / "s_cleaninitial.png"
    Image.fromarray(img.astype(np.uint8)).save(src)
    monkeypatch.setattr(IO.OV, "load_pair_matte", lambda *a, **k: pm)
    monkeypatch.setattr(IO.OV, "load_pair_edge_corr",
                        lambda *a, **k: {"grid": np.zeros((GH, GW)), "sources": "t",
                                         "n_frames": 2})
    monkeypatch.setattr(IO.OV, "load_pair_alpha_field",
                        lambda *a, **k: {"grid": field["grid"], "sources": "t",
                                         "n_frames": 2, "kappa": 1.0})
    monkeypatch.setattr(IO, "load_overlay_pair", lambda: (None, None))
    monkeypatch.setattr(IO.OV, "load_template", lambda *a, **k: None)
    monkeypatch.setattr(C, "_cuda_device", lambda: "cpu")
    monkeypatch.setattr(C, "gpu_lock", lambda *a, **k: contextlib.nullcontext())
    monkeypatch.setattr(IO, "_load_lama", lambda dev=None: (None, "cpu"))
    # the lane's own detection found only the LEFT half of the text
    left = s["fill"] & (np.arange(W)[None, :] < 0.5 * sum(s["span"]))
    seen = {}

    def stub(roi, mask, lama):
        seen["mask"] = np.asarray(mask).copy()
        return np.asarray(roi).copy()
    monkeypatch.setattr(IO, "inpaint_once", stub)
    orig_prepass = IO.overlay_prepass

    def prepass_with_seed(*a, **k):
        res = list(orig_prepass(*a, **k))
        res[1] = res[1].copy()
        res[1][left] = 255
        return tuple(res)
    monkeypatch.setattr(IO, "overlay_prepass", prepass_with_seed)
    rec = IO.clean_slug("s", image=str(src), overlay=True, pass4=True,
                        out_dir=str(tmp_path / "out"), log=lambda *a, **k: None)
    assert rec["status"] == "cleaned", rec
    side = json.load(open(tmp_path / "out" / "s_iopaint.json"))
    cr = side["params"]["overlay"]["credit"]
    assert cr["found"] is True
    assert "alpha_field" in side["params"]["overlay"]["pair"]
    x0, y0, x1, y1 = rec["region"]
    full_mask = np.zeros((H, W), dtype=bool)
    full_mask[y0:y1, x0:x1] = seen["mask"] > 127
    assert full_mask[s["fill"] | s["rim"]].all()       # both ends, the rim too
    _p, _c, sd = ov.remove_pair_edge(img, pm, _geom(pm), ALPHA, THETA)
    ring = ov.pair_edge_ring_sd(sd, W)
    assert full_mask[ring].mean() > 0.9                # the logo ring stays
