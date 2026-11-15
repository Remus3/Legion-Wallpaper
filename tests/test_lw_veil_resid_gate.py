"""The veil batch gate's residual-alpha estimator (`pair_residual_alpha`).

Batch 2 (docs/_archive/2026-11/VEIL_ALPHA_FIT_2026-11-15.md) graded each
candidate with the batch-1 step estimator `pair_veil_alpha_hat` (inner strip
2-6 px vs outer strip 8-14 px across the logo edge). On the purchased
ground-truth frames that estimator reads 0.01-0.04 LOW and its error is set by
the art, so 15 of 24 slugs went to manual on the measuring stick, not on
residue. The replacement is pinned here:

  * it is a DIFFERENT measurement from the fit objective (`fit_pair_alpha`
    zeroes a strip-mean step by bisection): a colour matched filter that
    projects the high-passed candidate onto the veil's own high-passed
    signature (fill toward W over the coverage + the dark halo), weighted
    toward smooth art, with r shared by the three channels. It never calls the
    fit or the old step estimator (no self-grading);
  * it tracks a KNOWN residual - removal at alpha + e for e in -0.04..+0.04,
    under- and over-removal, varied alpha - on textured art, with the sign of
    the error (under-removal > 0, over-removal < 0);
  * it reads ~0 on veil-free art;
  * a smooth glow behind the logo (art lighting) that drags the old step
    estimator off by more than the gate threshold does not move it.

The +-0.005 acceptance on the real purchased pairs is measured, not
unit-tested (no image is tracked): docs/_archive/2026-11/VEIL_RESID_GATE_2026-11-15.md.
Hermetic: synthetic fixtures only, numpy + PIL, no corpus image, Linux-safe.
"""
from __future__ import annotations

import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "tools"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lw_clean_overlay as ov  # noqa: E402
from test_lw_veil_alpha_fit import (H, W, W_MARK, _pm, _textured,  # noqa: E402
                                    _veil)

# Fixture tolerance. Measured over the 45 tracking cases: |err| median 0.0041,
# p95 0.0052, max 0.0061 - this fixture's hard-edged blobs are harsher than art.
RESID_TOL = 0.0065


def _oracle(cand, art, cov):
    """True residual fill alpha: pooled LSQ of (cand - art) on (W - art) in
    the logo interior (the A/B/C ground-truth definition)."""
    core = ov._erode_bool(cov >= 0.999, 2 * ov._ref_px(4, cov.shape[1]) + 1)
    d = (np.asarray(cand, float) - art)[core]
    m = (W_MARK - art)[core]
    return float((d * m).sum() / (m * m).sum())


def _remove(img, alpha):
    out, _ = ov.remove_overlay(img, None, pair=_pm(alpha))
    return np.asarray(out, dtype=np.float64)


def _lit(h, w, seed=3):
    """Smoothly shaded art (painted lighting, soft texture, no hard blobs)."""
    from lw_clean_pass import _box_mean
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:h, 0:w] / float(w)
    chans = []
    for c in range(3):
        n = _box_mean(_box_mean(rng.normal(0, 1, (h, w)), 5), 5) * 30.0
        chans.append(90 + 30 * np.sin(4 * xx + c) * np.cos(3 * yy + 2 * c) + n)
    return np.stack(chans, axis=-1)


def _glow(h, w, amp=80.0):
    """Smooth art lighting centred on the logo window: brighter under it."""
    pm = _pm()
    x0, y0, x1, y1 = pm["window"]
    cy, cx = 0.5 * (y0 + y1) * h, 0.5 * (x0 + x1) * w
    sy, sx = 0.22 * h, 0.10 * w
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float64)
    g = amp * np.exp(-((yy - cy) ** 2 / (2 * sy * sy)
                       + (xx - cx) ** 2 / (2 * sx * sx)))
    return g[..., None]


# ------------------------------------------------------------ tracking truth
@pytest.mark.parametrize("e", [-0.04, -0.02, 0.0, 0.02, 0.04])
@pytest.mark.parametrize("alpha", [0.10, 0.16, 0.22])
@pytest.mark.parametrize("seed,level", [(1, 110.0), (2, 60.0), (3, 170.0)])
def test_residual_tracks_a_known_removal_error(e, alpha, seed, level):
    art = _textured(H, W, seed, level)
    img = _veil(art, alpha)
    cov = ov.register_pair_matte(img.shape[:2], _pm())
    cand = _remove(img, alpha + e)
    truth = _oracle(cand, art, cov)
    got = ov.pair_residual_alpha(cand, cov, _pm(), alpha + e)
    assert got == pytest.approx(truth, abs=RESID_TOL)


def test_residual_sign_follows_under_and_over_removal():
    art = _textured(H, W, 5)
    img = _veil(art, 0.16)
    cov = ov.register_pair_matte(img.shape[:2], _pm())
    under = ov.pair_residual_alpha(_remove(img, 0.12), cov, _pm(), 0.12)
    exact = ov.pair_residual_alpha(_remove(img, 0.16), cov, _pm(), 0.16)
    over = ov.pair_residual_alpha(_remove(img, 0.20), cov, _pm(), 0.20)
    assert under > 0.03 and over < -0.03
    assert abs(exact) <= RESID_TOL
    assert under > exact > over


def test_veil_free_art_reads_zero():
    for seed, level in ((1, 110.0), (2, 60.0), (3, 170.0), (6, 140.0)):
        art = np.rint(_textured(H, W, seed, level))
        cov = ov.register_pair_matte(art.shape[:2], _pm())
        assert abs(ov.pair_residual_alpha(art, cov, _pm(), 0.0)) <= RESID_TOL


# ------------------------------------------------- art that fools the old gate
@pytest.mark.parametrize("e", [-0.02, 0.0, 0.02])
def test_a_glow_behind_the_logo_fools_the_old_step_but_not_the_new(e):
    # Lighting brighter under the logo: the old asymmetric strips (inner
    # 2-6 px, outer 8-14 px) read the glow's slope as veil (+0.045 here).
    art = np.clip(_lit(H, W) + _glow(H, W), 5, 225)
    img = _veil(art, 0.16)
    cov = ov.register_pair_matte(img.shape[:2], _pm())
    cand = _remove(img, 0.16 + e)
    truth = _oracle(cand, art, cov)
    old = ov.pair_veil_alpha_hat(cand, cov, _pm()["W"])
    new = ov.pair_residual_alpha(cand, cov, _pm(), 0.16 + e)
    assert abs(old - truth) > ov.PAIR_RESID_GATE        # the old stick is off
    assert new == pytest.approx(truth, abs=RESID_TOL)   # the new one is not


# ------------------------------------------------------------ no self-grading
def test_gate_never_calls_the_fit_or_the_old_step(monkeypatch):
    def boom(*a, **k):
        raise AssertionError("the gate must not grade the fitter with itself")
    monkeypatch.setattr(ov, "fit_pair_alpha", boom)
    monkeypatch.setattr(ov, "pair_veil_alpha_hat", boom)
    monkeypatch.setattr(ov, "_strips", boom)
    art = _textured(H, W, 1)
    img = _veil(art, 0.15)
    cov = ov.register_pair_matte(img.shape[:2], _pm())
    ov.pair_residual_alpha(_remove(img, 0.15), cov, _pm(), 0.15)


def test_empty_coverage_reads_nan():
    cov = np.zeros((H, W))
    assert np.isnan(ov.pair_residual_alpha(np.zeros((H, W, 3)), cov, _pm(), 0.15))


def test_gate_threshold_constant():
    # Kept at 0.02 unless the noise floor on veil-free frames says otherwise -
    # the derivation is in VEIL_RESID_GATE_2026-11-15.md.
    assert 0.005 <= ov.PAIR_RESID_GATE <= 0.03


# ------------------------------------------- the gate reads the pre-pass frame
def test_gate_frame_rebuilds_the_prepass_and_counts_mismatch():
    rng = np.random.default_rng(0)
    pre = rng.integers(0, 256, (60, 80, 3), dtype=np.uint8)
    lama = np.zeros((20, 30), dtype=bool)
    lama[5:10, 5:12] = True
    cand = pre.copy()
    cand[20:40, 30:60][lama] = 7                   # LaMa painted only its mask
    frame, bad = ov.pair_gate_frame(cand, pre[20:40, 30:60], (30, 20, 60, 40),
                                    lama)
    assert bad == 0
    assert (frame == pre).all()
    cand[25, 31] = cand[25, 31] ^ 1                # a change LaMa did not make
    _f, bad = ov.pair_gate_frame(cand, pre[20:40, 30:60], (30, 20, 60, 40),
                                 lama)
    assert bad == 1


def test_gate_frame_rejects_a_mismatched_roi():
    with pytest.raises(ValueError):
        ov.pair_gate_frame(np.zeros((60, 80, 3), np.uint8),
                           np.zeros((10, 10, 3), np.uint8), (0, 0, 20, 20),
                           np.zeros((10, 10), bool))
