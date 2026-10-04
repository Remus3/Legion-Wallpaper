"""G2.seam_step - contour-normal seam step (research experiment R3 / E-SEAM-1).

The live G2.seam arm (`seam_ring_ssim`) is SSIM of the 8 px ring OUTSIDE the
mask against its own blur, i.e. ring texture: a perfect fill reads < 0.92 on
9/12 golden frames. seam_step measures the seam itself: per 16 px cell along
the mask contour, median(inner 1-3 px band) - median(outer 1-3 px band), and
the score is |median over cells| in luma levels. A fill offset against its ring
is a large coherent signed step; texture steps have random sign.

Calibrated 2026-10-04 (LEDGER 264): golden clean 0.01..2.36 vs seam_offset_24lv
21.64..24.83; the 26 real LaMa clean pairs 0.00..2.06 (0 over the bar), the
same pairs offset +24 14.35..; flag bar SEAM_STEP_MAX = 6.0 levels.

Live since R3b (LEDGER 266, tests/test_g2_seam_step_live.py): _auto_inpaint
passes it to verify_verdict; the ring-SSIM "seam" flag and G2.seam row retired.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tools"))

import lw_clean_pass as cp  # noqa: E402
import lw_gate_board as B  # noqa: E402


def _textured(h=144, w=256, seed=7):
    rng = np.random.default_rng(seed)
    base = rng.integers(40, 216, size=(h, w, 3)).astype(np.float64)
    return np.clip(base, 0, 255).astype(np.uint8)


def _box_mask(h=144, w=256, box=(60, 50, 180, 100)):
    m = np.zeros((h, w), dtype=bool)
    x0, y0, x1, y1 = box
    m[y0:y1, x0:x1] = True
    return m


def test_threshold_is_the_calibrated_bar():
    assert cp.SEAM_STEP_MAX == 6.0


def test_identity_fill_on_texture_reads_no_step():
    """A perfect inpaint on busy texture (fill == the art) has no seam; the old
    ring-SSIM arm reads such texture as a seam."""
    img = _textured()
    m = _box_mask()
    v = cp.seam_step(img, m)
    assert v < cp.SEAM_STEP_MAX, v
    assert cp.seam_ring_ssim(img, cp._ring_mask(m)) < cp.SEAM_SSIM_MIN


def test_offset_fill_reads_a_large_step_either_sign():
    img = _textured()
    m = _box_mask()
    for off in (24.0, -24.0):
        bad = B.fault_seam(img, m, off)
        v = cp.seam_step(bad, m)
        assert v > 15.0, (off, v)


def test_empty_mask_reads_zero():
    img = _textured()
    assert cp.seam_step(img, np.zeros(img.shape[:2], dtype=bool)) == 0.0


def test_grayscale_input_is_accepted():
    img = _textured()[..., 0]
    m = _box_mask()
    assert cp.seam_step(img, m) < cp.SEAM_STEP_MAX


def test_verify_flags_seam_step_only_when_given():
    base = cp.verify_verdict(1.0, 0.0, 0.0, False, 1.0)
    assert "seam_step" not in base["flags"]
    hi = cp.verify_verdict(1.0, 0.0, 0.0, False, 1.0, seam_step=cp.SEAM_STEP_MAX + 1)
    assert hi["verdict"] == "pass" and "seam_step" in hi["flags"]
    lo = cp.verify_verdict(1.0, 0.0, 0.0, False, 1.0, seam_step=cp.SEAM_STEP_MAX - 1)
    assert "seam_step" not in lo["flags"]


def _g2_subject():
    img = _textured()
    m = _box_mask()
    return {"slug": "textured", "before": img.copy(), "after": img.copy(), "mask": m,
            "box": (60, 50, 180, 100), "restored": img.copy()}


def test_board_registers_seam_step_row():
    board = B.lw_board(envs=("base",))
    names = {r.name for r in board.rows}
    assert "G2.seam_step" in names  # G2.seam retired in R3b (LEDGER 266)
    f = board.faults["G2.seam_step"]
    assert f.plant.__name__ == "seam_offset_24lv"
    assert f.amplitude and "LEDGER 264" in f.evidence


def test_board_proves_seam_step_on_a_textured_subject():
    board = B.lw_board(envs=("base",))
    row = next(r for r in board.rows if r.name == "G2.seam_step")
    p = board.prove_row(row, _g2_subject())
    assert p.state == B.PROVEN, p.detail


def test_loosening_the_seam_step_bar_flips_its_row_to_broken(monkeypatch):
    """Mutant: the live bar is loosened out of reach -> the row must not stay green."""
    monkeypatch.setattr(cp, "SEAM_STEP_MAX", 1e9)
    board = B.lw_board(envs=("base",))
    row = next(r for r in board.rows if r.name == "G2.seam_step")
    assert board.prove_row(row, _g2_subject()).state == B.BROKEN
