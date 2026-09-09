"""G1: prove the MS-SSIM arm BINDS, and prove it is not redundant with LPIPS.

WHY THIS FILE EXISTS. A sweep of every G1 audit recorded in the corpus
(719 audits carrying msssim, 2026-09-08) found the arm had NEVER bound - not
once, in either the flag band or the fail band:

    msssim   n=719  min 0.9814  p01 0.9900  median 0.9989  max 1.0000
    floors   pass >= 0.98, fail < 0.96
    arms that actually bound: halo_pct 112, band_delta 8, lpips 5, lap_ratio 4

By this repo's own rule - a gate arm nobody has seen fail asserts nothing -
that is indistinguishable from decoration until someone proves the arm CAN
fire. It also correlates with lpips at r = -0.872 over those same 719 audits,
which is the shape of a redundant metric.

WHAT THE MEASUREMENT ACTUALLY SHOWED. Both suspicions are WRONG, and the
numbers below are why. Measured 2026-09-08 with the real metric stack
(`.venv-metrics`, pyiqa, `lw_g1_gate.fr_metrics` at common scale) against a
real corpus frame degraded in the ways this pipeline could plausibly fail:

    case              msssim     lpips     dists
    blur r1           0.9981    0.0281    0.0633
    blur r3           0.9781    0.0994    0.1980
    blur r8           0.9327    0.1568    0.3531
    shift 16px        0.8598    0.1206    0.0704
    crop/zoom 20pct   0.8221    0.2482    0.1323
    wrong image       0.4900    0.8001    0.5777

Two things follow. (1) The floor is REACHABLE: blur r8 lands at 0.9327, well
under the 0.96 fail floor, so the arm is live rather than unreachable.
(2) MS-SSIM is the ONLY arm that catches a geometric error. A 16px shift is a
hard msssim FAIL at 0.8598 while lpips barely flags (0.1206) and dists sails
through at 0.0704 - better than dists scores on a blur the eye would not even
notice. Drop msssim and a misaligned frame ships.

So the arm has never bound because the pipeline has never emitted a misaligned
or badly-soft frame. It is a tripwire that has correctly never fired, and the
right response is to PIN that it still can - not to move the floor and not to
delete the arm.

DELIBERATELY NOT DONE: re-calibrating the msssim floor on those 719 samples.
Fitting a threshold to the outputs it will then gate is the exact
selection-contamination this pass was opened to look for. The floors stay
where AUDIT_GATES put them; this file constrains BEHAVIOUR instead.

HERMETIC. `verdict()` is pure stdlib, so every case below is a recorded metric
vector fed straight to it. Nothing here imports torch or pyiqa, opens an
image, or reads the corpus - it runs identically on CI Linux. The constants
are the measurement's output, quoted with their provenance above.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

import lw_g1_gate as G  # noqa: E402

TH = G.DEFAULT_G1_THRESHOLDS

# Measured vectors, 2026-09-08. See the module docstring for provenance.
BLUR_R1 = {"msssim": 0.9981, "lpips": 0.0281}
BLUR_R3 = {"msssim": 0.9781, "lpips": 0.0994}
BLUR_R8 = {"msssim": 0.9327, "lpips": 0.1568}
SHIFT_16PX = {"msssim": 0.8598, "lpips": 0.1206}
CROP_ZOOM = {"msssim": 0.8221, "lpips": 0.2482}
WRONG_IMAGE = {"msssim": 0.4900, "lpips": 0.8001}


def _v(metrics, thresholds=None):
    return G.verdict(metrics, TH if thresholds is None else thresholds)


def _named(reasons, arm):
    return any(r.startswith(arm) for r in reasons)


def test_a_clean_frame_passes():
    """The control. Without this the failing cases prove nothing."""
    assert _v(BLUR_R1)["verdict"] == "PASS"


def test_the_arm_reaches_its_flag_band():
    out = _v(BLUR_R3)
    assert out["verdict"] == "FLAG"
    assert _named(out["reasons"], "msssim"), out["reasons"]


def test_the_arm_reaches_its_fail_band():
    """0.9327 at blur r8 - the floor is not unreachable."""
    out = _v(BLUR_R8)
    assert out["verdict"] == "FAIL"
    assert _named(out["reasons"], "msssim"), out["reasons"]


def test_msssim_is_stricter_than_lpips_on_moderate_blur():
    """At blur r3 lpips still passes outright - msssim is what notices."""
    assert _v({"lpips": BLUR_R3["lpips"]})["verdict"] == "PASS"
    assert _v(BLUR_R3)["verdict"] == "FLAG"


def test_msssim_is_the_only_arm_that_catches_a_16px_shift():
    """THE non-redundancy proof, and the reason the arm is kept.

    lpips 0.1206 is a bare flag and dists 0.0704 is cleaner than it scores on
    an unnoticeable blur. Only msssim treats a misaligned frame as a failure.
    """
    without = _v({"lpips": SHIFT_16PX["lpips"]})
    assert without["verdict"] == "FLAG", "lpips alone would let a shift through"
    full = _v(SHIFT_16PX)
    assert full["verdict"] == "FAIL"
    assert _named(full["reasons"], "msssim"), full["reasons"]


def test_removing_the_arm_downgrades_a_misaligned_frame():
    """Mutation proof: the arm is load-bearing, not confirmatory.

    Delete the msssim rule and a 16px-misaligned frame stops being a FAIL and
    becomes a mere FLAG - which routes to vision audit instead of being
    rejected. If this test ever passes with the arm removed, the arm was
    decoration after all and this whole file is the evidence to revisit.
    """
    stripped = {k: v for k, v in TH.items() if k != "msssim"}
    assert _v(SHIFT_16PX, stripped)["verdict"] == "FLAG"
    assert _v(SHIFT_16PX)["verdict"] == "FAIL"


def test_catastrophic_mispairing_fails_hard():
    for case in (CROP_ZOOM, WRONG_IMAGE):
        out = _v(case)
        assert out["verdict"] == "FAIL"
        assert _named(out["reasons"], "msssim"), out["reasons"]


def test_dists_is_measured_but_NOT_gated():
    """Characterization, not an endorsement - this is a real gap.

    fr_metrics computes dists and every audit records it, and ADR-007 moved the
    common-scale budget specifically to recover dists for 63 of 230 images. But
    there is no dists entry in _METRIC_RULES or in DEFAULT_G1_THRESHOLDS, so
    nothing consumes it: the worst dists in the measurement above (0.5777, the
    wrong image entirely) changes no verdict. This test pins the CURRENT
    behaviour so that adding a dists rule is a deliberate act that has to come
    here and say so, rather than a silent change in what the gate means.
    """
    assert not any(name == "dists" for name, _, _ in G._METRIC_RULES)
    assert "dists" not in TH
    clean = {"msssim": 0.9990, "lpips": 0.0100}
    assert _v(clean)["verdict"] == "PASS"
    assert _v({**clean, "dists": 0.5777})["verdict"] == "PASS", (
        "a catastrophic dists is currently inert - if this now fails, a dists "
        "rule was added and the gate's meaning changed"
    )


def test_the_recorded_corpus_minimum_still_passes():
    """Guards the floor against a well-meaning tightening.

    The softest frame the corpus has ever produced measured 0.9814 across 719
    audits. A floor raised above that would start failing frames the pipeline
    already shipped, which is how a threshold fitted to its own outputs starts
    manufacturing failures.
    """
    assert _v({"msssim": 0.9814, "lpips": 0.05})["verdict"] == "PASS"
