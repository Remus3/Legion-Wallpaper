"""Arms for the responder's live status file (MAIN 0915), written by the fleet kit.

Every tree publishes ONE file at the SAME relative path,
`ops/loop/control/inbox_status.json`, schema 1, read by the lane widget. Since
fleet kit v3 LW's own writer (`tools/lw_inbox_status.py`, PID probes, ETA
history) is DELETED: the kit's `write_status` writes the document, `kit.spawn`
writes "running" / "idle" around each run, and the responder's tick writes
"Checking Inbox" at its start and its end state with `next_tick` (the
scheduler's next fire, 5 minutes after this tick began).

LW's mapping onto MAIN's states, end of tick, in precedence order:
  halted   "Halted"              the kill switch file exists
  limit    "Turn Limit Reached"  the kit's rolling budget is spent
  refused  "Backing Off"         every spawn this tick was refused
  idle     "Idle"                otherwise (carries next_tick)

`conftest.py` points `lw_headless_env.FLEET_ROOT` at a tmp dir for every arm
and guards the kit's writer against the live directory.
"""
from __future__ import annotations

import datetime as dt
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import lw_headless_env as he  # noqa: E402
import lw_inbox_responder as responder  # noqa: E402

SCHEMA_1_KEYS = {"schema", "kit", "code", "updated", "state", "task", "task_started",
                 "task_eta_s", "next_tick", "runs_in_window", "runs_cap", "window_s",
                 "cap_frees_at"}


@pytest.fixture(autouse=True)
def _live_state_is_never_touched(monkeypatch, tmp_path):
    monkeypatch.setattr(responder, "HALT_PATH", tmp_path / "never-created-HALT")
    monkeypatch.setattr(responder, "RUNLOG_PATH", tmp_path / "runs.jsonl")


def _published() -> dict:
    path = Path(he.FLEET_ROOT) / he.kit.STATUS_REL
    return json.loads(path.read_text(encoding="ascii"))


def _inbox(tmp_path: Path) -> Path:
    box = tmp_path / "moon_sync_inbox"
    box.mkdir(exist_ok=True)
    (box / "2026-10-03-0900-from-RC-REVIEW-base.md").write_text("# From RC - x\n",
                                                                 encoding="utf-8")
    return box


def _main(tmp_path: Path, inbox: Path, *extra: str) -> int:
    return responder.main(["--once", "--inbox", str(inbox),
                           "--state", str(tmp_path / "seen.json"),
                           "--runlog", str(tmp_path / "runs.jsonl"), *extra])


def test_the_live_path_is_the_one_every_tree_shares():
    assert he.kit.STATUS_REL.as_posix() == "ops/loop/control/inbox_status.json"


@pytest.mark.skipif(shutil.which("git") is None, reason="git not on PATH")
@pytest.mark.parametrize("rel", ["ops/loop/control/inbox_status.json",
                                 "ops/loop/control/headless_budget.json",
                                 "ops/loop/control/headless_usage.jsonl"])
def test_the_kits_three_files_are_gitignored(rel):
    r = subprocess.run(["git", "check-ignore", "-v", "--no-index", rel], cwd=str(ROOT),
                       capture_output=True, text=True,
                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    assert r.returncode == 0, f"{rel} is not gitignored: {r.stdout}{r.stderr}"
    assert r.stdout.split("\t")[0].split(":")[-1].strip(), "empty pattern column"


def test_an_idle_tick_publishes_schema_1_with_next_tick(tmp_path, capsys):
    inbox = _inbox(tmp_path)
    before = dt.datetime.now(dt.UTC)
    assert _main(tmp_path, inbox) == 0
    doc = _published()
    assert set(doc) == SCHEMA_1_KEYS
    assert (doc["schema"], doc["kit"], doc["code"]) == (1, 3, "LW")
    assert (doc["state"], doc["task"]) == ("idle", "Idle")
    nxt = dt.datetime.fromisoformat(doc["next_tick"])
    assert before + dt.timedelta(minutes=4) < nxt <= dt.datetime.now(dt.UTC) + \
        dt.timedelta(minutes=5)
    assert (doc["runs_cap"], doc["window_s"]) == (120, 86400)


def test_a_halted_tick_publishes_halted(tmp_path, capsys):
    halt = tmp_path / "HALT"
    halt.write_text("stop", encoding="utf-8")
    _main(tmp_path, _inbox(tmp_path), "--halt", str(halt))
    assert (_published()["state"], _published()["task"]) == ("halted", "Halted")


def test_a_tick_announces_checking_inbox_before_it_reads(tmp_path, capsys, monkeypatch):
    seen = []
    real = responder.new_notes

    def _spy(inbox, state):
        seen.append(_published()["task"])
        return real(inbox, state)

    monkeypatch.setattr(responder, "new_notes", _spy)
    _main(tmp_path, _inbox(tmp_path))
    assert seen == ["Checking Inbox"]


def test_main_publishes_backing_off_when_the_gate_refuses(tmp_path, monkeypatch, capsys):
    inbox = _inbox(tmp_path)
    _main(tmp_path, inbox)
    (inbox / "2026-10-03-0915-from-CS-REVIEW-x.md").write_text("# From CS - x\n",
                                                               encoding="utf-8")
    monkeypatch.setattr(responder, "spawn", lambda *_a, **_k: responder.Disposition(
        responder.UNAVAILABLE, "spawn", "headless spawn refused: x", True))
    _main(tmp_path, inbox)
    assert (_published()["state"], _published()["task"]) == ("refused", "Backing Off")


def test_a_spent_budget_publishes_the_limit(tmp_path, capsys):
    b = he.budget()
    for _ in range(b.cap):
        b.record()
    _main(tmp_path, _inbox(tmp_path))
    doc = _published()
    assert (doc["state"], doc["task"]) == ("limit", "Turn Limit Reached")
    assert doc["runs_in_window"] == 120 and doc["cap_frees_at"]


def test_after_a_run_the_tick_ends_idle_with_the_run_counted(tmp_path, monkeypatch, capsys):
    inbox = _inbox(tmp_path)
    _main(tmp_path, inbox)
    (inbox / "2026-10-03-0915-from-CS-REVIEW-x.md").write_text("# From CS - x\n",
                                                               encoding="utf-8")

    def _spawned(*_a, **_k):
        he.budget().record()
        return responder._auto("spawn", "kit.spawn run rc 0")

    monkeypatch.setattr(responder, "spawn", _spawned)
    _main(tmp_path, inbox)
    doc = _published()
    assert (doc["state"], doc["runs_in_window"]) == ("idle", 1)
    assert doc["next_tick"]


def test_a_dry_run_publishes_nothing(tmp_path, capsys):
    _main(tmp_path, _inbox(tmp_path), "--dry-run")
    assert not (Path(he.FLEET_ROOT) / he.kit.STATUS_REL).exists()


def test_a_status_write_failure_never_fails_the_tick(tmp_path, monkeypatch, capsys):
    def _boom(*_a, **_k):
        raise OSError("disk full")

    monkeypatch.setattr(he.kit, "write_status", _boom)
    assert _main(tmp_path, _inbox(tmp_path)) == 0
    assert "status_error" in json.loads(capsys.readouterr().out)


def test_lws_own_status_writer_is_gone():
    assert not (ROOT / "tools" / "lw_inbox_status.py").exists()
    assert not hasattr(responder, "lw_inbox_status")
