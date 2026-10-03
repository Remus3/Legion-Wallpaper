"""An auditor that could not run must not advance the last-known-clean anchor.

Measured 2026-10-03 by reading `ops/loop/loop_controller.py`: `auditor()` mapped
the oracle's None sentinel (timeout, CLI error, or a REFUSED headless proxy) to
"VERDICT: CLEAN", and the cycle loop advanced `last_clean_sha` on anything not
REGRESS. So an un-audited cycle left every later audit window for good - with
the proxy refused, every cycle of a run passed un-audited and the eventual
first real audit saw none of them. N3's goal stands (a flaky auditor must not
BLOCK a cycle); the fix is a third verdict, UNAUDITED, that neither blocks nor
moves the anchor, so the next successful audit covers the skipped commits.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _load_controller():
    sys.path.insert(0, str(ROOT / "ops" / "loop"))
    spec = importlib.util.spec_from_file_location(
        "lw_loop_controller_unaudited", ROOT / "ops" / "loop" / "loop_controller.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


lc = _load_controller()


def _stub_audit_inputs(monkeypatch, oracle_result):
    monkeypatch.setattr(lc, "audit_range", lambda c, n: f"{c}..{n}")
    monkeypatch.setattr(lc, "git", lambda *a: "diff")
    monkeypatch.setattr(lc, "oracle", lambda *a, **k: oracle_result)


def test_auditor_error_is_UNAUDITED_not_CLEAN(monkeypatch):
    _stub_audit_inputs(monkeypatch, None)
    verdict = lc.auditor("aaa", "bbb", "aaa")
    assert lc.verdict_kind(verdict) == "UNAUDITED", verdict


def test_a_real_clean_verdict_still_reads_CLEAN(monkeypatch):
    _stub_audit_inputs(monkeypatch, "VERDICT: CLEAN\nfine")
    assert lc.verdict_kind(lc.auditor("aaa", "bbb", "aaa")) == "CLEAN"


def test_verdict_kinds():
    assert lc.verdict_kind("VERDICT: REGRESS\nx") == "REGRESS"
    assert lc.verdict_kind("  verdict: regress") == "REGRESS"
    assert lc.verdict_kind("VERDICT: UNAUDITED\nx") == "UNAUDITED"
    assert lc.verdict_kind("VERDICT: CLEAN\nx") == "CLEAN"


def test_anchor_moves_only_on_CLEAN():
    assert lc.next_clean_anchor("VERDICT: CLEAN\nok", "old", "new") == "new"
    assert lc.next_clean_anchor("VERDICT: REGRESS\nbad", "old", "new") == "old"
    assert lc.next_clean_anchor("VERDICT: UNAUDITED\nerr", "old", "new") == "old"


def test_the_cycle_loop_uses_the_helper():
    """The anchor rule must live in one place; the loop must not re-inline it."""
    src = (ROOT / "ops" / "loop" / "loop_controller.py").read_text(encoding="utf-8")
    assert "last_clean_sha = next_clean_anchor(" in src
    assert "if not regress:\n            last_clean_sha = new_sha" not in src
