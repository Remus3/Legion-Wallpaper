"""Pass 5 of the DA logo veil (2026-11-15): seam and hue fixes on top of pass 4.

Operator review of pass 4: the credit line's bottom edge smudges, the logo's
border still shows faint ghost lines, and where the veil edge sits on plain
background the colour is not blended out (a hue step). Measured causes
(docs/_archive/2026-11/VEIL_PASS5_2026-11-15.md): the credit text box was
too short and too narrow for the big-font credit lines, the LaMa ring fill
leaves a level / colour step at its seams (green deficit: a magenta tint),
and a thin edge profile survives along the contour. Fixes:
`lw_veil_credit.locate_credit(rows=, half=)` with the pass-5 bounds, a
membrane (harmonic) seam correction of every LaMa fill, and a contour
profile subtraction; plus an independent ring-hue metric.

Hermetic: synthetic fixtures only, numpy + PIL (+ scipy where the module
lazily needs it), Linux-safe.
"""
from __future__ import annotations

import os
import sys

import numpy as np
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "tools"))
sys.path.insert(0, HERE)
pytest.importorskip("scipy")
import lw_clean_iopaint as IO  # noqa: E402
import lw_clean_overlay as ov  # noqa: E402
import lw_veil_credit as CR  # noqa: E402
import lw_veil_hue as HU  # noqa: E402
import lw_veil_pass5 as P5  # noqa: E402
from test_lw_veil_pass3 import ALPHA, GH, GW, H, W, W_MARK, _art, _pm  # noqa: E402

A_TXT, RIM = 0.145, 0.35


def _cov():
    return ov.register_pair_matte((H, W), _pm())


def _sd_frame(cov):
    """Signed distance (frame px, + inside), computed here independently."""
    core, din, dout = ov._signed_geometry(cov, W, 40.0)
    return (din - dout) * W / 1920.0


def _ghost(sd):
    """A thin outline left along the contour: bright inside, dark outside,
    and a green deficit (magenta tint) across the ring - all coherent."""
    g = (2.5 * np.exp(-((sd - 2.0) ** 2) / 0.8)
         - 2.0 * np.exp(-((sd + 1.0) ** 2) / 0.8))
    out = np.repeat(g[..., None], 3, axis=2)
    out[..., 1] -= 1.5 * (np.abs(sd) < 3.0)
    return out


def _band(sd, r):
    return np.abs(sd) < r


def _rms(a, b, m):
    d = (np.asarray(a, dtype=np.float64) - b)[m]
    return float(np.sqrt(np.mean(d * d)))


def _smooth_art(seed):
    """Plain background (where an outline shows): low-frequency colour plus
    1-level noise, no texture."""
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:H, 0:W] / float(W)
    out = np.zeros((H, W, 3))
    for c in range(3):
        ph = rng.uniform(0, 6.3, 3)
        out[..., c] = 120.0 + 30.0 * np.sin(4 * xx + ph[0]) * np.cos(3 * yy + ph[1])
    return out + rng.normal(0, 1.0, out.shape)


@pytest.fixture(scope="module")
def scene():
    cov = _cov()
    sd = _sd_frame(cov)
    return {"cov": cov, "sd": sd, "art": _smooth_art(31),
            "textured": _art(31, level=120.0)}


# ------------------------------------------------- contour profile subtraction
def test_profile_fix_removes_a_coherent_outline(scene):
    art, sd, cov = scene["art"], scene["sd"], scene["cov"]
    img = np.clip(np.rint(art + _ghost(sd)), 0, 255)
    allowed = np.ones((H, W), dtype=bool)
    out, info = P5.contour_profile_fix(img, cov, allowed)
    band = _band(sd, 6.0)
    before, after = _rms(img, art, band), _rms(out, art, band)
    assert after < 0.45 * before, (before, after)
    assert info["cells"] > 20


def test_profile_fix_leaves_clean_art_alone(scene):
    art, cov = scene["art"], scene["cov"]
    img = np.clip(np.rint(art), 0, 255)
    out, _info = P5.contour_profile_fix(img, cov, np.ones((H, W), dtype=bool))
    assert _rms(out, img, _band(scene["sd"], 6.0)) < 0.3
    # textured art: the 9 px texture leaks into the per-cell fit; the change
    # stays bounded (measured 0.94 levels RMS) and capped
    tex = np.clip(np.rint(scene["textured"]), 0, 255)
    out, _info = P5.contour_profile_fix(tex, cov, np.ones((H, W), dtype=bool))
    assert _rms(out, tex, _band(scene["sd"], 6.0)) < 1.2
    assert np.abs(out.astype(float) - tex).max() <= P5.PROFILE_CAP + 1.0


def test_profile_fix_never_touches_outside_allowed(scene):
    art, sd, cov = scene["art"], scene["sd"], scene["cov"]
    img = np.clip(np.rint(art + _ghost(sd)), 0, 255).astype(np.uint8)
    allowed = _band(sd, 6.0) & (np.arange(W)[None, :] < W // 2)
    out, _info = P5.contour_profile_fix(img, cov, allowed)
    assert out.dtype == np.uint8
    assert np.array_equal(out[~allowed], img[~allowed])
    assert not np.array_equal(out[allowed], img[allowed])


def test_profile_fix_is_capped(scene):
    art, sd, cov = scene["art"], scene["sd"], scene["cov"]
    img = np.clip(np.rint(art + 8.0 * _ghost(sd)), 0, 255)
    out, _info = P5.contour_profile_fix(img, cov, np.ones((H, W), dtype=bool))
    assert np.abs(out.astype(float) - img).max() <= P5.PROFILE_CAP + 1.0


# --------------------------------------------------------- membrane seam fix
def test_membrane_removes_a_fill_offset_and_keeps_the_fill_detail(scene):
    art, sd = scene["art"], scene["sd"]
    region = (sd > -4.5) & (sd < 3.0)
    tex = np.random.default_rng(5).normal(0, 1.5, (H, W, 1))
    fill = art + tex
    img = art.copy()
    img[region] = fill[region] + np.array([3.0, -2.5, 3.5])   # LaMa drift
    out, corr = P5.membrane_fill(img, region)
    assert np.array_equal(out[~region], img[~region])
    before = _rms(img, fill, region)
    after = _rms(out, fill, region)
    assert after < 0.35 * before, (before, after)
    # the correction is smooth: no detail of its own
    both = region[:, 1:] & region[:, :-1]
    assert np.abs(np.diff(corr, axis=1)[both]).max() < 1.0


def test_membrane_ignores_an_art_edge_crossing_the_seam(scene):
    art, sd = scene["art"].copy(), scene["sd"]
    region = (sd > -4.5) & (sd < 3.0)
    art[:, W // 2:] += 40.0                       # a hard art edge across the ring
    img = art.copy()
    out, _corr = P5.membrane_fill(img, region)    # a perfect fill: nothing to do
    assert _rms(out, art, region) < 0.6


# ------------------------------------------------------------ credit line box
def _big_credit(cov):
    """A credit line in the BIG font: lower and wider than pass 4's box."""
    ly0, ly1, lx0, lx1 = CR.logo_box(cov)
    lh = float(ly1 - ly0)
    cx = 0.5 * (lx0 + lx1)
    t0, t1 = int(ly1 + 0.066 * lh), int(ly1 + 0.147 * lh)
    half = 0.735 * lh
    fill = np.zeros((H, W), dtype=bool)
    x = int(cx - half)
    while x < cx + half - 6:
        fill[t0:t1, x:x + 7] = True
        x += 11
    k = max(int(round(0.0065 * lh)), 1)          # ~3 px at 2560 (lh 460)
    shadow = np.zeros((H, W), dtype=bool)
    shadow[k:, k:] = fill[:-k, :-k]              # drop shadow down-right
    shadow &= ~fill
    return fill, shadow, cx, lh


def test_pass4_box_misses_the_big_credit_line_and_pass5_holds_it():
    cov = _cov()
    fill, shadow, cx, lh = _big_credit(cov)
    seed = fill & (np.abs(np.arange(W)[None, :] - cx) < 0.45 * lh)
    old = CR.credit_box_mask((H, W), CR.locate_credit(seed, cov))
    assert not old[fill | shadow].all()           # the pass-4 defect
    loc = CR.locate_credit(seed, cov, rows=P5.CREDIT_ROWS, half=P5.CREDIT_HALF)
    new = CR.credit_box_mask((H, W), loc)
    assert new[fill | shadow].all()
    # and it is a bounded box, not the frame
    assert new.sum() < 2.6 * lh * 0.16 * lh * 1.2


def test_pass5_box_reads_the_reach_in_the_text_rows_only():
    cov = _cov()
    fill, _s, cx, lh = _big_credit(cov)
    seed = fill & (np.abs(np.arange(W)[None, :] - cx) < 0.45 * lh)
    ly1 = CR.logo_box(cov)[1]
    junk = seed.copy()
    # art the detection also marks, in the box's extra rows only, far out
    junk[int(ly1 + 0.150 * lh), int(cx + 1.0 * lh) - 30:int(cx + 1.0 * lh)] = True
    a = CR.locate_credit(seed, cov, rows=P5.CREDIT_ROWS, half=P5.CREDIT_HALF)
    b = CR.locate_credit(junk, cov, rows=P5.CREDIT_ROWS, half=P5.CREDIT_HALF)
    assert a == b


def test_locate_credit_defaults_are_the_pass4_box():
    cov = _cov()
    fill, _s, cx, lh = _big_credit(cov)
    a = CR.locate_credit(fill, cov)
    b = CR.locate_credit(fill, cov, rows=CR.CREDIT_ROWS, half=CR.CREDIT_HALF)
    assert a == b


# --------------------------------------------------------------- hue metric
def test_hue_metric_ranks_ring_tints_and_reads_clean_art_low(scene):
    art, sd, cov = scene["art"], scene["sd"], scene["cov"]
    ring = (sd > -4.0) & (sd < 3.0)
    vals = []
    for g in (0.0, 1.0, 2.0, 4.0):
        img = art.copy()
        img[ring, 1] -= g                          # green deficit = magenta
        vals.append(HU.ring_hue_step(np.clip(np.rint(img), 0, 255), cov)["ring_de"])
    assert vals[0] < HU.HUE_GATE
    assert vals == sorted(vals) and vals[-1] > 3 * vals[0] + 0.5, vals


def test_hue_metric_never_calls_the_fixes(scene, monkeypatch):
    def boom(*a, **k):
        raise AssertionError("the metric must not call the fix")
    for name in ("contour_profile_fix", "membrane_fill", "seam_fix"):
        monkeypatch.setattr(P5, name, boom)
    r = HU.ring_hue_step(np.clip(np.rint(scene["art"]), 0, 255), scene["cov"])
    assert r is not None and np.isfinite(r["ring_de"])


# ---------------------------------------------------------- the lane, pass 5
@pytest.fixture()
def lane(tmp_path, monkeypatch):
    import contextlib

    import lw_clean_pass as C
    pm = _pm()
    monkeypatch.setattr(IO.OV, "load_pair_matte", lambda *a, **k: pm)
    monkeypatch.setattr(IO.OV, "load_pair_edge_corr",
                        lambda *a, **k: {"grid": np.zeros((GH, GW)), "sources": "t",
                                         "n_frames": 2})
    monkeypatch.setattr(IO.OV, "load_pair_alpha_field",
                        lambda *a, **k: {"grid": np.ones((GH, GW)), "sources": "t",
                                         "n_frames": 2, "kappa": 1.0})
    monkeypatch.setattr(IO, "load_overlay_pair", lambda: (None, None))
    monkeypatch.setattr(IO.OV, "load_template", lambda *a, **k: None)
    monkeypatch.setattr(C, "_cuda_device", lambda: "cpu")
    monkeypatch.setattr(C, "gpu_lock", lambda *a, **k: contextlib.nullcontext())
    monkeypatch.setattr(IO, "_load_lama", lambda dev=None: (None, "cpu"))
    art = _art(41, level=120.0)
    cov = _cov()
    a = (ALPHA * cov)[..., None]
    img = np.clip(np.rint(art * (1 - a) + a * W_MARK), 0, 255)
    from PIL import Image
    src = tmp_path / "s_cleaninitial.png"
    Image.fromarray(img.astype(np.uint8)).save(src)

    def drifting_lama(roi, mask, lama):
        # LaMa's colour drift: the masked pixels come back as the local art
        # (here: the ROI itself) shifted by a magenta tint
        out = np.asarray(roi, dtype=np.float64).copy()
        m = np.asarray(mask) > 127
        out[m] += np.array([3.0, -3.0, 3.0])        # BGR order, +B -G +R
        return np.clip(np.rint(out), 0, 255).astype(np.uint8)
    monkeypatch.setattr(IO, "inpaint_once", drifting_lama)
    return {"src": str(src), "art": art, "cov": cov, "tmp": tmp_path}


def test_clean_slug_pass5_records_and_fixes_the_ring_seam(lane):
    import json
    from PIL import Image
    run = {}
    for name, kw in (("p4", {"pass4": True}), ("p5", {"pass5": True})):
        rec = IO.clean_slug("s", image=lane["src"], overlay=True,
                            out_dir=str(lane["tmp"] / name),
                            log=lambda *a, **k: None, **kw)
        assert rec["status"] == "cleaned", rec
        run[name] = (rec, np.asarray(Image.open(rec["cand"]).convert("RGB"),
                                     dtype=np.float64))
    side = json.load(open(lane["tmp"] / "p5" / "s_iopaint.json"))
    info = side["params"]["overlay"]["pass5"]
    assert info["membrane_px"] > 0 and info["profile"]["cells"] > 0
    rec5, c5 = run["p5"]
    rec4, c4 = run["p4"]
    x0, y0, x1, y1 = rec5["region"]
    m = np.zeros((H, W), dtype=bool)
    m[y0:y1, x0:x1] = np.asarray(Image.open(rec5["mask_png"])) > 127
    ring = m & (np.abs(_sd_frame(lane["cov"])) < 6.0)
    # the green deficit LaMa left in the ring is gone in pass 5
    g4 = (c4[..., 1] - 0.5 * (c4[..., 0] + c4[..., 2]))[ring].mean()
    g5 = (c5[..., 1] - 0.5 * (c5[..., 0] + c5[..., 2]))[ring].mean()
    ga = (lane["art"][..., 1] - 0.5 * (lane["art"][..., 0] + lane["art"][..., 2]))[ring].mean()
    assert abs(g5 - ga) < 0.4 * abs(g4 - ga), (g4, g5, ga)
    # outside the declared mask + edge support pass 5 equals pass 4
    sup = np.asarray(Image.open(side["params"]["overlay"]["edge_support"])) > 127
    out = ~(sup | m)
    assert np.array_equal(c5[out], c4[out])
