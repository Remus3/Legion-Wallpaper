"""Per-frame amplitude for the DA logo pair matte.

The 63-slug batch (docs/_archive/2026-11/VEIL_BATCH_2026-11-15.md) showed the
pair matte's SHAPE is right but its fixed alpha 0.1511 is not: each frame's
residual tracked its own veil strength (225f +0.085 under-removed, fantasy-design
-0.075 over-removed). These tests pin the fix - keep the shape, fit the
amplitude per frame:

  * `fit_pair_alpha` recovers a known alpha on textured art (light and dark,
    hard-edged shapes crossing the logo edge) within FIT_TOL. Measured over
    108 synthetic frames (12 seeds x 3 levels x 3 alphas) at 960 and 1280 px:
    median |err| 0.002-0.003, p95 0.007-0.008, max 0.010 - this fixture's
    hard-edged blobs are harsher than real art. The +-0.005 acceptance on the
    real purchased pairs is measured, not unit-tested (no image is tracked):
    docs/_archive/2026-11/VEIL_ALPHA_FIT_2026-11-15.md;
  * it models the veil's dark halo just outside the edge, so the halo does not
    read as extra fill;
  * a frame veiled WEAKER than the fixed alpha (the over-removal / dark-imprint
    case) is fitted down, and its residual step goes to ~0;
  * fits are bounded (PAIR_FIT_BOUNDS) and a fit at a bound is FLAGGED;
  * `refine_pair_shift` finds a sub-pixel offset of the logo before the fit;
  * `overlay_prepass` uses the fitted alpha, records it, and still leaves every
    pixel outside the coverage byte-identical; `pair_fit=False` is the old path.

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

W_MARK = 245.0
H, W = 540, 960
FIT_TOL = 0.008
WINDOW = (0.42, 0.31, 0.58, 0.69)      # frame-normalized, like the real asset


def _logo_grid(gh=380, gw=300, ss=4):
    """A DA-logo-like coverage on the window grid: a slanted body with a notch
    and a hole, so the edge runs in every direction. Area-antialiased."""
    yy, xx = np.mgrid[0:gh * ss, 0:gw * ss].astype(np.float64)
    u, v = xx / (gw * ss), yy / (gh * ss)
    body = (v > 0.08) & (v < 0.92) & (u > 0.12 + 0.18 * v) & (u < 0.70 + 0.18 * v)
    notch = (v > 0.40) & (v < 0.55) & (u > 0.55 + 0.18 * v)
    hole = ((u - 0.45) ** 2 / 0.010 + (v - 0.30) ** 2 / 0.006) < 1.0
    m = (body & ~notch & ~hole).astype(np.float64)
    return m.reshape(gh, ss, gw, ss).mean(axis=(1, 3)).astype(np.float32)


def _pm(alpha=0.1511):
    return {"shape": _logo_grid(), "alpha": alpha,
            "W": np.array([W_MARK] * 3), "window": WINDOW, "ref": (1920, 1080),
            "sources": "synthetic"}


def _blur(a, k):
    from lw_clean_pass import _box_mean
    return _box_mean(_box_mean(a, k), k)


def _textured(h, w, seed, level=110.0):
    """Unrelated art: smooth shading, mid-frequency texture, hard-edged blobs
    that cross the logo edge, fine noise. `level` sets the mean brightness."""
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:h, 0:w] / float(max(h, w))
    out = np.zeros((h, w, 3))
    for c in range(3):
        ph = rng.uniform(0, 6.3, 4)
        out[..., c] = (level + 35 * np.sin(5 * xx + ph[0]) * np.cos(3 * yy + ph[1])
                       + 20 * np.sin(17 * xx + 11 * yy + ph[2]))
        out[..., c] += 12 * _blur(rng.normal(0, 1, (h, w)), 7) * 7
    for _ in range(14):
        cy, cx = rng.uniform(0.25, 0.75) * h, rng.uniform(0.35, 0.65) * w
        ry, rx = rng.uniform(8, 60), rng.uniform(8, 60)
        blob = ((np.arange(h)[:, None] - cy) / ry) ** 2 + (
            (np.arange(w)[None, :] - cx) / rx) ** 2 < 1.0
        out[blob] += rng.uniform(-45, 45, 3)
    out += rng.normal(0, 1.5, out.shape)
    return np.clip(out, 5, 225)


def _veil(art, alpha, shift=(0.0, 0.0), halo=True):
    """The DA veil model: fill alpha over the coverage + the dark halo outside."""
    pm = _pm()
    cov = ov.register_pair_matte(art.shape[:2], pm, shift=shift)
    hal = (ov.pair_halo_map(cov, art.shape[1]) if halo
           else np.zeros(cov.shape))
    a = (alpha * cov)[..., None]
    k = (alpha * hal)[..., None]
    return np.clip(np.rint(art * (1.0 - a - k) + a * W_MARK), 0, 255)


# ---------------------------------------------------------------- halo model
def test_halo_map_is_zero_inside_and_decays_outward():
    cov = ov.register_pair_matte((H, W), _pm())
    hal = ov.pair_halo_map(cov, W)
    assert hal.shape == cov.shape
    assert (hal[cov >= 0.999] == 0).all()
    assert hal.max() > 0.2              # ~0.35 x fill alpha just outside
    # far from the logo it is exactly zero
    assert hal[:20].max() == 0 and hal[:, :40].max() == 0
    # it decays outward: the mean over a near band beats a far band
    core = cov >= 0.5
    near = ov._dilate_bool(core, 7) & ~core
    far = ov._dilate_bool(core, 41) & ~ov._dilate_bool(core, 29)
    assert hal[near].mean() > 3 * hal[far].mean()


# ---------------------------------------------------------------- the fit
@pytest.mark.parametrize("alpha", [0.08, 0.15, 0.22])
@pytest.mark.parametrize("seed,level", [(1, 110.0), (2, 60.0), (3, 170.0)])
def test_fit_recovers_alpha_on_textured_art(alpha, seed, level):
    art = _textured(H, W, seed, level)
    img = _veil(art, alpha)
    cov = ov.register_pair_matte(img.shape[:2], _pm())
    fit = ov.fit_pair_alpha(img, cov, _pm())
    assert fit["alpha"] == pytest.approx(alpha, abs=FIT_TOL)
    assert fit["at_bound"] is None
    assert fit["windows"] > 50


def test_fit_models_the_halo_rather_than_reading_it_as_fill():
    # Without the halo term the dark rim outside makes the step look bigger;
    # the fit must land on the FILL alpha, not fill + halo.
    art = _textured(H, W, 4)
    img = _veil(art, 0.15, halo=True)
    cov = ov.register_pair_matte(img.shape[:2], _pm())
    with_model = ov.fit_pair_alpha(img, cov, _pm())["alpha"]
    no_model = ov.fit_pair_alpha(img, cov, _pm(), halo=())["alpha"]
    assert with_model == pytest.approx(0.15, abs=FIT_TOL)
    assert no_model > with_model + 0.01


def test_weak_veil_is_fitted_down_and_the_dark_imprint_goes_away():
    # The fantasy-design case: the frame's veil is WEAKER than the fixed
    # 0.1511, so the fixed inversion over-removes (negative residual step,
    # a dark imprint of the logo). The fitted alpha brings the residual to ~0.
    art = _textured(H, W, 5)
    img = _veil(art, 0.09)
    pm = _pm()
    cov = ov.register_pair_matte(img.shape[:2], pm)
    fixed, _ = ov.remove_overlay(img, None, pair=pm)
    resid_fixed = ov.pair_veil_alpha_hat(fixed, cov, pm["W"])
    fit = ov.fit_pair_alpha(img, cov, pm)
    pm_fit = dict(pm, alpha=fit["alpha"])
    fitted, _ = ov.remove_overlay(img, None, pair=pm_fit)
    resid_fit = ov.pair_veil_alpha_hat(fitted, cov, pm["W"])
    assert resid_fixed < -0.03
    assert abs(resid_fit) < abs(resid_fixed) / 3
    inside = cov >= 0.999
    err_fixed = np.abs(fixed.astype(float) - art)[inside].mean()
    err_fit = np.abs(fitted.astype(float) - art)[inside].mean()
    assert err_fit < err_fixed / 3


def test_strong_veil_is_fitted_up():
    # The 225f case: veil stronger than the fixed alpha, a faint logo stays.
    art = _textured(H, W, 6)
    img = _veil(art, 0.22)
    pm = _pm()
    cov = ov.register_pair_matte(img.shape[:2], pm)
    fit = ov.fit_pair_alpha(img, cov, pm)
    assert fit["alpha"] == pytest.approx(0.22, abs=FIT_TOL)
    fixed, _ = ov.remove_overlay(img, None, pair=pm)
    assert ov.pair_veil_alpha_hat(fixed, cov, pm["W"]) > 0.03


def test_fit_is_bounded_and_flags_the_bound():
    pm = _pm()
    art = _textured(H, W, 7)
    cov = ov.register_pair_matte((H, W), pm)
    lo, hi = ov.PAIR_FIT_BOUNDS
    strong = ov.fit_pair_alpha(_veil(art, 0.45), cov, pm)
    assert strong["alpha"] == pytest.approx(hi)
    assert strong["at_bound"] == "high"
    clean = ov.fit_pair_alpha(np.rint(art), cov, pm)
    assert clean["alpha"] == pytest.approx(lo)
    assert clean["at_bound"] == "low"


def test_fit_is_deterministic():
    art = _textured(H, W, 8)
    img = _veil(art, 0.13)
    cov = ov.register_pair_matte(img.shape[:2], _pm())
    a = ov.fit_pair_alpha(img, cov, _pm())
    b = ov.fit_pair_alpha(img.copy(), cov.copy(), _pm())
    assert a == b


def test_fit_on_empty_coverage_returns_the_prior_flagged():
    fit = ov.fit_pair_alpha(np.zeros((H, W, 3)), np.zeros((H, W)), _pm())
    assert fit["alpha"] == pytest.approx(0.1511)
    assert fit["at_bound"] == "no_edge"
    assert fit["windows"] == 0


# ---------------------------------------------------------------- registration
@pytest.mark.parametrize("shift", [(0.5, 1.5), (-1.0, -0.5), (0.0, 0.0)])
def test_refine_shift_finds_a_subpixel_offset(shift):
    art = _textured(H, W, 9)
    img = _veil(art, 0.15, shift=shift)
    dy, dx = ov.refine_pair_shift(img, _pm())
    assert dy == pytest.approx(shift[0], abs=0.5)
    assert dx == pytest.approx(shift[1], abs=0.5)
    cov = ov.register_pair_matte(img.shape[:2], _pm(), shift=(dy, dx))
    assert ov.fit_pair_alpha(img, cov, _pm())["alpha"] == pytest.approx(
        0.15, abs=FIT_TOL)


def test_refine_shift_starts_from_the_given_registration():
    art = _textured(H, W, 10)
    img = _veil(art, 0.15, shift=(3.0, -4.5))
    dy, dx = ov.refine_pair_shift(img, _pm(), shift=(3, -4))
    assert dy == pytest.approx(3.0, abs=0.5)
    assert dx == pytest.approx(-4.5, abs=0.5)


# ---------------------------------------------------------------- the lane
def _bgr(rgb):
    return np.ascontiguousarray(np.asarray(rgb)[:, :, ::-1]).astype(np.uint8)


def test_prepass_uses_the_fitted_alpha_and_records_it():
    art = _textured(H, W, 11)
    img = _veil(art, 0.20)
    pre, _mask, _roi, info = IO.overlay_prepass(_bgr(img), None, None,
                                                pair=_pm())
    p = info["pair"]
    assert p["used"] is True
    assert p["alpha"] == pytest.approx(0.1511, abs=1e-4)     # the asset's prior
    assert p["alpha_fit"] == pytest.approx(0.20, abs=FIT_TOL)
    assert p["at_bound"] is None
    assert len(p["shift_fit"]) == 2
    cov = ov.register_pair_matte((H, W), _pm(), shift=tuple(p["shift_fit"]))
    inside = cov >= 0.999
    got = pre[:, :, ::-1].astype(np.float64)
    assert np.abs(got - art)[inside].mean() < 1.5


def test_prepass_fit_leaves_outside_the_coverage_byte_identical():
    art = _textured(H, W, 12)
    img = _veil(art, 0.18)
    bgr = _bgr(img)
    pre, _mask, _roi, info = IO.overlay_prepass(bgr, None, None, pair=_pm())
    cov = ov.register_pair_matte((H, W), _pm(),
                                 shift=tuple(info["pair"]["shift_fit"]))
    out = cov <= 0
    assert np.array_equal(pre[out], bgr[out])


def test_prepass_pair_fit_off_is_the_fixed_alpha_path():
    art = _textured(H, W, 13)
    bgr = _bgr(_veil(art, 0.18))
    pre, mask, roi, info = IO.overlay_prepass(bgr, None, None, pair=_pm(),
                                              pair_fit=False)
    want, _ = ov.remove_overlay(bgr[:, :, ::-1].astype(np.float64), None,
                                pair=_pm())
    assert np.array_equal(pre, _bgr(want))
    assert "alpha_fit" not in info["pair"]


def test_prepass_flags_a_fit_at_the_bound():
    art = _textured(H, W, 14)
    bgr = _bgr(_veil(art, 0.45))
    _pre, _mask, _roi, info = IO.overlay_prepass(bgr, None, None, pair=_pm())
    assert info["pair"]["at_bound"] == "high"
    assert info["pair"]["alpha_fit"] == pytest.approx(ov.PAIR_FIT_BOUNDS[1])


# ---------------------------------------------------------------- own registration
# Batch 1's four "registration failures" (VEIL_ALPHA_FIT doc, section 4): the pair
# matte borrowed the COLLECTION template's registration, which art can drag
# (bamboo-gal: dx +30 px, the logo sits at +4) and which misses a zoomed frame
# (fantasy-design: the frame is a 1.2x centre crop, the template answered
# (43, -10) at 1.0). The pair now also registers ITSELF - scale about the frame
# centre x shift - and the better-scoring registration wins.
def _veil_at(art, alpha, scale, shift):
    pm = _pm()
    h, w = art.shape[:2]
    cov = ov.register_pair_matte((h, w), pm, shift=shift, scale=scale,
                                 centre=(h / 2.0, w / 2.0))
    hal = ov.pair_halo_map(cov, w)
    a = (alpha * cov)[..., None]
    k = (alpha * hal)[..., None]
    return np.clip(np.rint(art * (1.0 - a - k) + a * W_MARK), 0, 255)


def test_search_finds_a_zoomed_frame():
    art = _textured(H, W, 15)
    img = _veil_at(art, 0.15, 1.2, (0.0, 3.0))
    reg = ov.search_pair_registration(img, _pm())
    assert reg["scale"] == pytest.approx(1.2)
    assert reg["shift"][0] == pytest.approx(0.0, abs=4)
    assert reg["shift"][1] == pytest.approx(3.0, abs=4)
    assert reg["centre"] == pytest.approx((H / 2.0, W / 2.0))


def _with_template(monkeypatch, dy, dx, sc):
    monkeypatch.setattr(ov, "best_registration",
                        lambda image, tpl, *a, **k: (0.5, dy, dx, sc))
    monkeypatch.setattr(ov, "overlay_score", lambda *a, **k: 0.5)
    return {"dummy": True}


def test_prepass_overrides_a_template_that_missed_a_zoomed_frame(monkeypatch):
    art = _textured(H, W, 16)
    img = _veil_at(art, 0.15, 1.2, (0.0, 3.0))
    tpl = _with_template(monkeypatch, 43, -10, 1.0)
    pre, _m, _r, info = IO.overlay_prepass(_bgr(img), None, tpl, pair=_pm())
    p = info["pair"]
    assert p["reg_source"] == "search"
    assert p["scale_fit"] == pytest.approx(1.2)
    assert p["alpha_fit"] == pytest.approx(0.15, abs=FIT_TOL)
    cov = ov.register_pair_matte((H, W), _pm(), shift=(0.0, 3.0), scale=1.2,
                                 centre=(H / 2.0, W / 2.0))
    inside = cov >= 0.999
    assert np.abs(pre[:, :, ::-1].astype(np.float64) - art)[inside].mean() < 2.0


def test_prepass_overrides_a_dragged_template(monkeypatch):
    art = _textured(H, W, 17)
    img = _veil_at(art, 0.15, 1.0, (1.0, 2.0))
    tpl = _with_template(monkeypatch, 1, 15, 1.0)
    _pre, _m, _r, info, ring = IO.overlay_prepass(_bgr(img), None, tpl,
                                                  pair=_pm(), return_ring=True)
    p = info["pair"]
    assert p["reg_source"] == "search"
    assert p["shift_fit"][1] == pytest.approx(2.0, abs=0.75)
    # the LaMa ring follows the registration actually used
    cov = ov.register_pair_matte((H, W), _pm(), shift=(1.0, 2.0))
    assert np.array_equal(ring, ov.pair_edge_ring(
        ov.register_pair_matte((H, W), _pm(), shift=tuple(p["shift_fit"]),
                               scale=1.0, centre=(H / 2.0, W / 2.0))))
    assert ring[cov >= 0.5].mean() < 0.5


def test_prepass_keeps_a_good_template(monkeypatch):
    art = _textured(H, W, 18)
    img = _veil(art, 0.15)
    tpl = _with_template(monkeypatch, 0, 0, 1.0)
    _pre, _m, _r, info, ring = IO.overlay_prepass(_bgr(img), None, tpl,
                                                  pair=_pm(), return_ring=True)
    assert info["pair"]["reg_source"] == "template"
    # ring stays on the template registration it was swept on
    assert np.array_equal(ring, ov.pair_edge_ring(
        ov.register_pair_matte((H, W), _pm())))


def test_search_only_presence_needs_a_fit_above_the_lower_bound(monkeypatch):
    # The pair's own search found the logo on 3 frames batch 1 had called
    # veil-free (281-cleanup, 258-cleanup, fury-tempest-sona: logo + credit
    # visible), and one false hit (caitlyn-love: no logo; its fit sat at the
    # LOWER bound). Presence read only at a searched registration therefore
    # also needs the fitted amplitude off the lower bound.
    art = _textured(H, W, 19)
    bgr = _bgr(np.rint(art))
    cov = ov.register_pair_matte((H, W), _pm(), shift=(0.0, 9.0))
    monkeypatch.setattr(IO, "pair_registration", lambda rgb, pair, s, sc: {
        "shift": (0.0, 9.0), "scale": 1.0, "centre": None, "cov": cov,
        "source": "search", "score": [1.0, 2.0]})
    calls = iter([0.0, 0.12])       # template position, then searched position
    monkeypatch.setattr(ov, "pair_veil_alpha_hat", lambda *a, **k: next(calls))
    pre, _m, _r, info = IO.overlay_prepass(bgr, None, None, pair=_pm())
    assert info["pair"]["used"] is False
    assert info["pair"]["at_bound"] == "low"
    assert np.array_equal(pre, bgr)
