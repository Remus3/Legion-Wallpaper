"""MAIN REPO-REVIEW perf finding 2.3 (2026-10-08): kit-adoption ORDERs ran on
opus/high for ~15 min each, under a 3600 s ceiling. The responder's code-writing
run now gets effort medium and a 1800 s ceiling; pinned so a later edit that
raises either one goes red instead of quietly re-spending the budget."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import lw_inbox_responder as R  # noqa: E402


def test_code_run_timeout_is_1800s():
    assert R.RUN_TIMEOUT_S == 1800


def test_code_run_effort_is_medium():
    assert R.CODE_EFFORT == "medium"
