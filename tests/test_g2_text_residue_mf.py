"""G2.text_residue_mf - re-inpaint matched filter (research R2 / E-MIM-1).

The live OCR+MSER residue arm is BROKEN 0/12 (fires on restored busy art,
misses the +4-level credit line). residue_mf re-inpaints the (dilated) stroke
mask of the old mark on the CLEANED image with LaMa and reads the signed
median of luma(image) - luma(re-inpaint) over the stroke pixels: a faint
residue is a coherent same-sign offset along the strokes; a clean fill
re-inpaints to itself up to LaMa's error, which the median suppresses.

Measured 2026-10-04 (LEDGER 267, shipped function): golden clean |median|
max 2.00 vs credit_line_4lv min 4.00 (12/12); 26 real LaMa clean pairs max
1.94 (0 FP),
the same pairs + credit_line_4lv min 3.89. Flag bar RESIDUE_MF_MAX = 3.0.
Not computed in the live verify yet (ROADMAP R2b).
"""
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tools"))

import lw_clean_pass as cp  # noqa: E402
import lw_gate_board as B  # noqa: E402


def _flat_lama(image, mask):
    """Fake reconstructor: fills the hole with the mean of the unmasked pixels
    (exact background on flat art, so it cannot rebuild a residue)."""
    a = np.asarray(image.convert("RGB"), dtype=np.float64)
    m = np.asarray(mask.convert("L")) > 127
    out = a.copy()
    out[m] = a[~m].mean(axis=0)
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))


def _subject(h=200, w=640):
    img = np.full((h, w, 3), 100, dtype=np.uint8)
    box = (80, 120, 560, 180)
    mask = np.zeros((h, w), dtype=bool)
    x0, y0, x1, y1 = box
    mask[y0:y1, x0:x1] = True
    return {"slug": "flat", "before": img.copy(), "after": img.copy(), "mask": mask,
            "box": box, "restored": img.copy()}


def test_bar_is_the_calibrated_value():
    assert cp.RESIDUE_MF_MAX == 3.0


def test_clean_reads_zero_and_four_level_residue_reads_four():
    s = _subject()
    strokes = B.stroke_mask(s["box"], s["restored"].shape[:2])
    assert strokes.sum() > 500
    assert abs(cp.residue_mf(s["restored"], strokes, _flat_lama)) < 0.5
    res = B.fault_text(s["restored"], s["box"], levels=4.0)
    v = cp.residue_mf(res, strokes, _flat_lama)
    assert 3.5 < v < 4.5, v


def test_empty_strokes_read_zero():
    s = _subject()
    assert cp.residue_mf(s["restored"], np.zeros(s["mask"].shape, bool), _flat_lama) == 0.0


def test_verify_flags_residue_mf_only_when_given_either_sign():
    assert "residue_mf" not in cp.verify_verdict(1.0, 0.0, 0.0, False, 1.0)["flags"]
    for v in (cp.RESIDUE_MF_MAX + 0.5, -(cp.RESIDUE_MF_MAX + 0.5)):
        r = cp.verify_verdict(1.0, 0.0, 0.0, False, 1.0, residue_mf=v)
        assert r["verdict"] == "pass" and "residue_mf" in r["flags"]
    lo = cp.verify_verdict(1.0, 0.0, 0.0, False, 1.0, residue_mf=cp.RESIDUE_MF_MAX - 0.5)
    assert "residue_mf" not in lo["flags"]


def test_board_registers_the_row_in_the_clean_env():
    board = B.lw_board(envs=("clean",))
    row = next(r for r in board.rows if r.name == "G2.text_residue_mf")
    assert row.env == "clean" and row.gate == "G2"
    f = board.faults["G2.text_residue_mf"]
    assert f.plant.__name__ == "credit_line_4lv"
    assert "LEDGER 267" in f.evidence
    assert "G2.text_residue_mf" not in {r.name for r in B.lw_board(envs=("base",)).rows}


def test_board_proves_the_row_with_a_faithful_reconstructor(monkeypatch):
    monkeypatch.setattr(B, "_lama", lambda: _flat_lama)
    board = B.lw_board(envs=("clean",))
    row = next(r for r in board.rows if r.name == "G2.text_residue_mf")
    p = board.prove_row(row, _subject())
    assert p.state == B.PROVEN, p.detail


def test_loosening_the_bar_flips_the_row_to_broken(monkeypatch):
    monkeypatch.setattr(B, "_lama", lambda: _flat_lama)
    monkeypatch.setattr(cp, "RESIDUE_MF_MAX", 1e9)
    board = B.lw_board(envs=("clean",))
    row = next(r for r in board.rows if r.name == "G2.text_residue_mf")
    assert board.prove_row(row, _subject()).state == B.BROKEN
