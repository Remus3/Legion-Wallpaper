"""G1.cambi_delta - CAMBI banding arm (research experiment R1 / E-BAND-1).

CAMBI (Netflix contrast-aware multiscale banding index, libvmaf) with
max_log_contrast=5, measured on the 2560x1440 output with no downscale, as a
delta against the source resized to the output size. Measured 2026-10-04 on
the 12 golden pairs (LEDGER 263): clean delta max 1.21, posterize_8 delta
min 3.00, so a flag bar of 2.0 separates 12/12.

ffmpeg (with libvmaf) is optional: CI has none. Absent or failing ffmpeg is a
DEGRADED reading - the metric returns None, the live verdict skips it like any
missing key, and the gate board reads the row UNKNOWN (never green). The
ffmpeg-dependent tests skip where CAMBI cannot run.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import lw_g1_gate as g1  # noqa: E402
import lw_gate_board as B  # noqa: E402


def _ramp(w=1280, h=720):
    r = np.tile(np.linspace(16, 240, w)[None, :, None], (h, 1, 3))
    return np.rint(r).astype(np.uint8)


def _cambi_runs():
    return g1.cambi_score(_ramp(256, 144)) is not None


needs_cambi = pytest.mark.skipif(not _cambi_runs(), reason="ffmpeg with libvmaf cambi absent")


# ------------------------------------------------------------ live table
def test_cambi_delta_is_a_live_flag_arm():
    assert g1.DEFAULT_G1_THRESHOLDS["cambi_delta"] == {"flag": 2.0}
    assert ("cambi_delta", "flag_over", "cambi_delta") in g1._METRIC_RULES
    assert g1.CAMBI_MAX_LOG_CONTRAST == 5


def test_verdict_flags_cambi_delta_over_the_bar():
    r = g1.verdict({"cambi_delta": 3.0}, g1.DEFAULT_G1_THRESHOLDS)
    assert r["verdict"] == "FLAG"
    assert any(x.startswith("cambi_delta") for x in r["reasons"])
    assert g1.verdict({"cambi_delta": 1.2}, g1.DEFAULT_G1_THRESHOLDS)["verdict"] == "PASS"


# ------------------------------------------------------------ degraded paths
def test_cambi_is_none_when_ffmpeg_absent(monkeypatch):
    monkeypatch.setattr(g1, "_ffmpeg_exe", lambda: None)
    assert g1.cambi_score(_ramp(64, 36)) is None
    assert g1.cambi_delta(_ramp(64, 36), _ramp(64, 36)) is None


def test_cambi_is_none_when_ffmpeg_cannot_start(monkeypatch, tmp_path):
    monkeypatch.setattr(g1, "_ffmpeg_exe", lambda: str(tmp_path / "no-such-ffmpeg.exe"))
    assert g1.cambi_score(_ramp(64, 36)) is None


def test_board_row_is_unknown_never_green_without_ffmpeg(monkeypatch):
    monkeypatch.setattr(g1, "_ffmpeg_exe", lambda: None)
    board = B.lw_board(envs=("base",))
    row = next(r for r in board.rows if r.name == "G1.cambi_delta")
    subj = {"slug": "ramp", "source_rgb": _ramp(64, 36), "output_rgb": _ramp(128, 72),
            "backend": "ijn"}
    p = board.prove_row(row, subj)
    assert p.state == B.UNKNOWN
    assert "measurement returned no value" in p.detail  # degraded, no raw error text


# ------------------------------------------------------------ registry
def test_board_registers_cambi_row_with_posterize_fault():
    board = B.lw_board(envs=("base",))
    names = {r.name for r in board.rows}
    assert "G1.cambi_delta" in names
    f = board.faults["G1.cambi_delta"]
    assert f.name == "posterize_8" and f.amplitude and f.evidence


# ------------------------------------------------------------ real CAMBI
@needs_cambi
def test_cambi_mlc5_sees_posterize_8_on_a_ramp():
    clean = _ramp()
    banded = B.fault_posterize(clean, B.BAND_STEP)
    assert g1.cambi_delta(clean, clean) == pytest.approx(0.0, abs=1e-6)
    d = g1.cambi_delta(clean, banded)
    assert d > g1.DEFAULT_G1_THRESHOLDS["cambi_delta"]["flag"], d


@needs_cambi
def test_cambi_delta_resizes_the_source_to_the_output():
    src = _ramp(640, 360)
    out = _ramp(1280, 720)
    d = g1.cambi_delta(src, out)
    assert d is not None and abs(d) < g1.DEFAULT_G1_THRESHOLDS["cambi_delta"]["flag"]


@needs_cambi
def test_board_proves_cambi_row_on_a_ramp():
    board = B.lw_board(envs=("base",))
    row = next(r for r in board.rows if r.name == "G1.cambi_delta")
    subj = {"slug": "ramp", "source_rgb": _ramp(640, 360), "output_rgb": _ramp(),
            "backend": "ijn"}
    p = board.prove_row(row, subj)
    assert p.state == B.PROVEN, p.detail


@needs_cambi
def test_deleting_the_cambi_threshold_flips_its_row_to_broken(monkeypatch):
    """Mutant: the live table loses its cambi bar -> the row must not stay green."""
    th = {k: v for k, v in g1.DEFAULT_G1_THRESHOLDS.items() if k != "cambi_delta"}
    monkeypatch.setattr(g1, "DEFAULT_G1_THRESHOLDS", th)
    board = B.lw_board(envs=("base",))
    row = next(r for r in board.rows if r.name == "G1.cambi_delta")
    subj = {"slug": "ramp", "source_rgb": _ramp(640, 360), "output_rgb": _ramp(),
            "backend": "ijn"}
    assert board.prove_row(row, subj).state == B.BROKEN
