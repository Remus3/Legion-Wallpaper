"""LOG-LEAK: a headless refusal raised inside a test never reaches the LIVE logs/.

`lw_headless_env.log_refusal` appends to `logs/YYYY-MM-DD.log` (LOG_DIR) unless
a caller passes `log_dir`. The responder (tools/lw_inbox_responder.py), the loop
executor (ops/loop/executor.py), the loop oracle and the CI watchdog all call it
WITHOUT `log_dir`, so every arm that drove one of them into a refusal without
also patching LOG_DIR wrote "headless spawn refused: run budget exhausted
(120/120)" into the operator's live daily log (measured 2026-10-10:
test_a_spent_budget_launches_nothing and
test_a_spent_kit_budget_stops_the_cycle_and_spawns_nothing, one line each).

The guard is suite-wide, not per-arm: the env seam LW_HEADLESS_LOG_DIR is a
declared runtime root (lw_race_guards.ENV_ROOTS -> tmp_path for every test,
inherited by child interpreters), and conftest also points LOG_DIR at tmp_path
for the case where the kit test guard is switched off.
"""
from __future__ import annotations

import datetime as dt
import os
import subprocess
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import lw_headless_env as he  # noqa: E402
import lw_race_guards as rg  # noqa: E402

LIVE = ROOT / "logs"


def _live_today() -> str:
    path = LIVE / f"{dt.datetime.now():%Y-%m-%d}.log"
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def test_the_log_dir_seam_is_a_declared_runtime_root():
    assert rg.ENV_ROOTS.get(he.LOG_DIR_ENV) == "logs"


def test_a_refusal_without_log_dir_lands_under_tmp_never_the_live_dir(tmp_path):
    marker = f"leak-probe-{uuid.uuid4().hex}"
    he.log_refusal(marker, "run budget exhausted (120/120)")
    assert marker not in _live_today()
    hits = [p for p in tmp_path.rglob("*.log") if marker in p.read_text(encoding="utf-8")]
    assert len(hits) == 1


def test_a_child_interpreter_inherits_the_redirect(tmp_path):
    marker = f"leak-probe-{uuid.uuid4().hex}"
    code = ("import sys; sys.path.insert(0, sys.argv[1]); import lw_headless_env as he; "
            "he.log_refusal(sys.argv[2], 'run budget exhausted (120/120)')")
    subprocess.run([sys.executable, "-c", code, str(ROOT / "tools"), marker],
                   check=True, timeout=60, env=dict(os.environ),
                   creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    assert marker not in _live_today()
    assert any(marker in p.read_text(encoding="utf-8") for p in tmp_path.rglob("*.log"))


def test_production_still_resolves_the_repo_logs_dir(monkeypatch):
    monkeypatch.delenv(he.LOG_DIR_ENV, raising=False)
    monkeypatch.setattr(he, "LOG_DIR", LIVE)
    assert he.default_log_dir() == LIVE
    monkeypatch.setenv(he.LOG_DIR_ENV, "")
    assert he.default_log_dir() == LIVE, "an EMPTY value means unset"


def test_an_explicit_log_dir_still_wins(tmp_path):
    he.log_refusal("explicit", "x", log_dir=tmp_path / "mine")
    assert list((tmp_path / "mine").glob("*.log"))
