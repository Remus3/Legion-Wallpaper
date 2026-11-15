"""Edge-ghost metric for the DA logo veil border (`tools/lw_veil_ghost.py`).

Pins, on hermetic fixtures:
  * a veil-free frame and a perfectly de-veiled frame read under the gate;
  * a bright outline, a dark outline and a mis-registered (double-edge)
    inversion read over it, and the reading grows monotonically with the
    injected error (the ranking property validated on the purchased pairs);
  * a strong art line crossing the edge does not read as a ghost (medians);
  * it never calls the pass-2 fit or the alpha fit (independent instrument);
  * empty coverage -> None, and `ghost_ok` refuses it.
"""
from __future__ import annotations

import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "tools"))
import lw_clean_overlay as ov  # noqa: E402
import lw_veil_ghost as gh  # noqa: E402
from lw_clean_pass import _box_mean  # noqa: E402

H, W = 720, 1280
WINDOW = (0.42, 0.31, 0.58, 0.69)


def _pm():
    gh_, gw, ss = 380, 300, 4
    yy, xx = np.mgrid[0:gh_ * ss, 0:gw * ss].astype(np.float64)
    u, v = xx / (gw * ss), yy / (gh_ * ss)
    body = (v > 0.08) & (v < 0.92) & (u > 0.12 + 0.18 * v) & (u < 0.70 + 0.18 * v)
    m = body.astype(np.float64).reshape(gh_, ss, gw, ss).mean(axis=(1, 3))
    return {"shape": m.astype(np.float32), "alpha": 0.15, "W": np.array([245.0] * 3),
            "window": WINDOW, "ref": (1920, 1080), "sources": "synthetic"}


def _art(seed=3):
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:H, 0:W] / float(W)
    base = 140 + 30 * np.sin(4 * xx + 1.0) * np.cos(3 * yy)
    base = base + _box_mean(rng.normal(0, 1, (H, W)), 9) * 25 + rng.normal(0, 1.0, (H, W))
    return np.repeat(np.clip(base, 5, 240)[..., None], 3, axis=2)


def _veiled(art, cov, a=0.15, wv=245.0):
    return art * (1 - a * cov[..., None]) + a * wv * cov[..., None]


def _deveil(img, cov, a=0.15, wv=245.0):
    c = cov[..., None]
    return np.clip((img - a * wv * c) / (1 - a * c), 0, 255)


@pytest.fixture(scope="module")
def base():
    pm = _pm()
    cov = ov.register_pair_matte((H, W), pm)
    return pm, cov, _art()


def test_veil_free_and_perfect_removal_read_under_the_gate(base):
    _pm_, cov, art = base
    r = gh.edge_ghost(art, cov)
    assert r["line_rms"] < 0.5 * gh.GHOST_LINE_GATE
    assert gh.ghost_ok(r)
    perfect = _deveil(_veiled(art, cov), cov)
    assert gh.ghost_ok(gh.edge_ghost(perfect, cov))


@pytest.mark.parametrize("sign", [+1, -1])
def test_outline_reads_over_the_gate_and_grows_with_amplitude(base, sign):
    _pm_, cov, art = base
    core = cov >= 0.5
    line = ov._dilate_bool(core, 3) & ~ov._erode_bool(core, 3)
    vals = []
    for amp in (0.0, 2.0, 4.0, 8.0):
        img = art + sign * amp * line[..., None]
        vals.append(gh.edge_ghost(img, cov)["line_rms"])
    assert vals == sorted(vals)
    assert vals[-1] > gh.GHOST_LINE_GATE
    assert not gh.ghost_ok(gh.edge_ghost(art + sign * 8.0 * line[..., None], cov))
    mean = gh.edge_ghost(art + sign * 8.0 * line[..., None], cov)["line_mean"]
    assert np.sign(mean) == sign


def test_misregistered_inversion_ranks_by_shift(base):
    pm, cov, art = base
    img = _veiled(art, cov)
    vals = []
    for dx in (0.0, 0.5, 1.0, 2.0):
        cov_s = ov.register_pair_matte((H, W), pm, shift=(0.0, dx))
        vals.append(gh.edge_ghost(_deveil(img, cov_s), cov)["line_rms"])
    assert vals == sorted(vals)
    assert vals[0] < gh.GHOST_LINE_GATE < vals[-1]


def test_an_art_line_across_the_edge_is_not_a_ghost(base):
    _pm_, cov, art = base
    img = art.copy()
    img[:, 630:633] -= 80.0          # a hard vertical ink line through the logo
    img[352:355, :] += 60.0          # and a horizontal one
    assert gh.ghost_ok(gh.edge_ghost(img, cov))


def test_never_calls_the_fit(base, monkeypatch):
    _pm_, cov, art = base

    def boom(*_a, **_k):
        raise AssertionError("the ghost metric must not call a fit")
    for name in ("fit_pair_edge", "pair_edge_offsets", "fit_pair_alpha",
                 "refine_pair_shift", "pair_residual_alpha", "remove_pair_edge"):
        monkeypatch.setattr(ov, name, boom)
    assert gh.edge_ghost(art, cov) is not None


def test_empty_coverage_is_none_and_not_ok():
    r = gh.edge_ghost(np.zeros((H, W, 3)), np.zeros((H, W)))
    assert r is None
    assert not gh.ghost_ok(r)
