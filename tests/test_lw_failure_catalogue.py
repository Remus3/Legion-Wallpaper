"""Failure catalogues (directive P2-8, tools/lw_failure_catalogue.py).

Every major tool's skill doc ends with symptom | cause | how it was caught |
fix | LEDGER, each row tracing to a real LEDGER item. drift_guard runs the
check; these tests pin the check itself and its wiring.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

import drift_guard as DG  # noqa: E402
import lw_failure_catalogue as FC  # noqa: E402

HEAD = "| Symptom | Cause | How it was caught | Fix | LEDGER |\n|---|---|---|---|---|\n"


def _doc(tmp_path, rows, name="tool.md"):
    p = tmp_path / name
    p.write_text("# Tool\n\n## Failure catalogue\n\n" + HEAD + rows, encoding="ascii")
    return p


def _ledger(tmp_path, ids):
    p = tmp_path / "LEDGER.md"
    p.write_text("".join(f"{i}. DONE **x**\n" for i in ids), encoding="ascii")
    return p


ROW = "| s | c | caught | fixed | LEDGER {n} |\n"


def test_the_tracked_catalogues_pass():
    assert FC.check() == []


def test_missing_section_is_a_problem(tmp_path):
    p = tmp_path / "t.md"
    p.write_text("# Tool\n\nno table\n", encoding="ascii")
    assert "no '## Failure catalogue'" in FC.check({"t": p}, _ledger(tmp_path, [1]))[0]


def test_row_citing_a_ledger_item_that_does_not_exist(tmp_path):
    rows = "".join(ROW.format(n=n) for n in (1, 2, 3, 4, 99))
    probs = FC.check({"t": _doc(tmp_path, rows)}, _ledger(tmp_path, [1, 2, 3, 4]))
    assert probs == ["t: row 5 cites LEDGER 99, which does not exist"]


def test_row_with_no_ledger_citation(tmp_path):
    rows = "".join(ROW.format(n=n) for n in (1, 2, 3, 4)) + "| s | c | k | f | - |\n"
    probs = FC.check({"t": _doc(tmp_path, rows)}, _ledger(tmp_path, [1, 2, 3, 4]))
    assert any("cites no LEDGER" in p for p in probs)


def test_too_few_rows(tmp_path):
    probs = FC.check({"t": _doc(tmp_path, ROW.format(n=1))}, _ledger(tmp_path, [1]))
    assert any("rows" in p for p in probs)


def test_drift_guard_runs_the_catalogue_check(monkeypatch):
    called = []
    monkeypatch.setattr(DG, "check_failure_catalogues", lambda *a, **k: called.append(1))
    for name in [n for n in dir(DG) if n.startswith("check_") and n != "check_failure_catalogues"]:
        monkeypatch.setattr(DG, name, lambda *a, **k: None)
    DG.problems.clear()
    DG.notes.clear()
    DG.main()
    assert called == [1]


def test_drift_guard_reports_catalogue_problems_as_breaches(monkeypatch):
    monkeypatch.setattr(FC, "check", lambda *a, **k: ["first pass: no table"])
    DG.problems.clear()
    DG.check_failure_catalogues()
    assert DG.problems == ["FAILURE CATALOGUE: first pass: no table"]
    DG.problems.clear()


def test_catalogues_do_not_live_in_claude_md():
    text = (FC.ROOT / "CLAUDE.md").read_text(encoding="utf-8")
    assert FC.HEADING not in text
