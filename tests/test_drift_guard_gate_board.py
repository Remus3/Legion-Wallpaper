"""drift_guard: the fault-proven gate board arm (directive P0-3).

drift_guard reads ops/runtime/gate_proofs.json through
lw_gate_board.check_proofs_acked and breaches on any registered gate that is
not PROVEN unless a tracked, adjudicated ack entry covers it. These tests pin
the WIRING (the arm runs from main, problems become BREACH lines under their
own class, notes stay notes); the ack semantics live in test_lw_gate_board.py.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

import drift_guard as DG  # noqa: E402
import lw_gate_board  # noqa: E402


def _reset():
    DG.problems.clear()
    DG.notes.clear()


def test_problems_become_gate_board_breaches(monkeypatch):
    _reset()
    monkeypatch.setattr(lw_gate_board, "check_proofs_acked",
                        lambda *a, **k: (["gate G1.x is BROKEN"], []))
    DG.check_gate_proofs()
    assert DG.problems == ["GATE BOARD: gate G1.x is BROKEN"]
    _reset()


def test_notes_stay_notes(monkeypatch):
    _reset()
    monkeypatch.setattr(lw_gate_board, "check_proofs_acked",
                        lambda *a, **k: ([], ["ACKNOWLEDGED G1.y BROKEN 0/12"]))
    DG.check_gate_proofs()
    assert DG.problems == []
    assert DG.notes == ["GATE BOARD: ACKNOWLEDGED G1.y BROKEN 0/12"]
    _reset()


def test_a_crashing_check_is_a_breach_not_a_pass(monkeypatch):
    _reset()

    def boom(*a, **k):
        raise ValueError("bad table")
    monkeypatch.setattr(lw_gate_board, "check_proofs_acked", boom)
    DG.check_gate_proofs()
    assert DG.problems and "ValueError" in DG.problems[0]
    _reset()


def test_main_runs_the_gate_board_arm(monkeypatch):
    """Mutation guard: a check that main() never calls asserts nothing."""
    called = []
    monkeypatch.setattr(DG, "check_gate_proofs", lambda *a, **k: called.append(1))
    for name in [n for n in dir(DG) if n.startswith("check_") and n != "check_gate_proofs"]:
        monkeypatch.setattr(DG, name, lambda *a, **k: None)
    _reset()
    DG.main()
    assert called == [1], "check_gate_proofs is not wired into main()"
    _reset()
