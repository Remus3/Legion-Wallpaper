"""Arms for `tools/lw_inbox_status.py`, the responder's live status file (MAIN 0915).

The lane widget is a read-only observer that reads ONE file per tree at the same
relative path, `ops/loop/control/inbox_status.json`, schema 1. These arms pin
the schema, the basic task names, the ETA rule (median of the last 10 completed
instances, null under 3 - never a guess), the window arithmetic, the atomic
write, and how the responder's `main` drives it on each kind of tick.

Every arm runs against injected paths: `tests/conftest.py` redirects both module
paths into `tmp_path` and spies the writer, so no arm can write the live file.
"""
from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import lw_inbox_responder as responder  # noqa: E402
import lw_inbox_status as status  # noqa: E402

# Captured at import, BEFORE the conftest redirect, so the arm pinning the real
# default reads the real default.
REAL_STATUS_PATH = status.STATUS_PATH
REAL_STATE_PATH = status.STATE_PATH

T0 = dt.datetime(2026, 10, 3, 14, 0, 0, tzinfo=dt.UTC)
KEYS = {"schema", "code", "updated", "state", "task", "task_started", "task_eta_s",
        "next_tick", "runs_in_window", "runs_cap", "window_s", "cap_frees_at"}


def _never_alive(_pid, _spawned):
    return False


def _always_alive(_pid, _spawned):
    return True


def _record(tmp_path, *, now=T0, probe=_never_alive, **kw):
    kw.setdefault("halted", False)
    kw.setdefault("refused", False)
    kw.setdefault("spawn_times", [])
    return status.record(now=now, probe=probe, next_tick=now + dt.timedelta(minutes=5), **kw)


def _published() -> dict:
    return json.loads(status.STATUS_PATH.read_text(encoding="utf-8"))


# --- the contract --------------------------------------------------------

def test_the_live_path_is_the_one_every_tree_shares():
    assert REAL_STATUS_PATH == ROOT / "ops" / "loop" / "control" / "inbox_status.json"


def test_the_live_path_and_the_state_file_are_gitignored():
    import subprocess
    for path in (REAL_STATUS_PATH, REAL_STATE_PATH):
        rel = path.relative_to(ROOT).as_posix()
        out = subprocess.run(["git", "check-ignore", "-v", rel], cwd=ROOT,
                             capture_output=True, text=True,
                             creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        # Parse the PATTERN column: a trailing-slash quirk can exit 0 with an
        # empty pattern (memory reference-git-check-ignore-false-green).
        pattern = out.stdout.split("\t")[0].split(":")[-1] if out.stdout else ""
        assert out.returncode == 0 and pattern and not pattern.startswith("!"), (rel, out.stdout)


def test_the_published_document_has_exactly_schema_1s_keys(tmp_path):
    doc = _record(tmp_path)
    assert set(doc) == KEYS
    assert _published() == doc
    assert doc["schema"] == 1 and doc["code"] == "LW"
    assert doc["runs_cap"] == responder.MAX_RUNS_PER_24H == 120
    assert doc["window_s"] == 86400


def test_every_task_name_is_basic_and_fits_24_chars():
    assert status.TASKS == ("Idle", "Checking Inbox", "Waiting for Slot", "Running Session",
                            "Delivering Notes", "Committing", "Backing Off", "Halted",
                            "Turn Limit Reached")
    assert all(len(t) <= 24 for t in status.TASKS)


def test_timestamps_are_local_iso_with_an_offset(tmp_path):
    doc = _record(tmp_path)
    for key in ("updated", "task_started", "next_tick"):
        parsed = dt.datetime.fromisoformat(doc[key])
        assert parsed.utcoffset() is not None, key
        assert parsed == T0 if key != "next_tick" else parsed == T0 + dt.timedelta(minutes=5)


def test_the_write_is_atomic_and_leaves_no_temp_file(tmp_path):
    _record(tmp_path)
    leftovers = [p.name for p in status.STATUS_PATH.parent.iterdir() if p.suffix == ".tmp"]
    assert leftovers == []


def test_a_missing_control_directory_is_created(tmp_path, monkeypatch):
    deep = tmp_path / "a" / "b" / "inbox_status.json"
    monkeypatch.setattr(status, "STATUS_PATH", deep)
    _record(tmp_path)
    assert deep.is_file()


# --- state resolution ----------------------------------------------------

def test_a_quiet_tick_is_idle(tmp_path):
    doc = _record(tmp_path)
    assert (doc["state"], doc["task"]) == ("idle", "Idle")


def test_halted_outranks_everything(tmp_path):
    doc = _record(tmp_path, halted=True, refused=True, probe=_always_alive,
                  new_children=[(101, T0.timestamp())], spawn_times=[T0] * 120)
    assert (doc["state"], doc["task"]) == ("halted", "Halted")


def test_a_live_child_is_a_running_session(tmp_path):
    doc = _record(tmp_path, probe=_always_alive, new_children=[(101, T0.timestamp())],
                  spawn_times=[T0])
    assert (doc["state"], doc["task"]) == ("running", "Running Session")
    assert doc["runs_in_window"] == 1


def test_a_full_window_is_the_turn_limit(tmp_path):
    doc = _record(tmp_path, spawn_times=[T0 - dt.timedelta(hours=20)] + [T0] * 119)
    assert (doc["state"], doc["task"]) == ("limit", "Turn Limit Reached")
    assert doc["runs_in_window"] == 120
    # The OLDEST counted run ages out first.
    assert dt.datetime.fromisoformat(doc["cap_frees_at"]) == T0 + dt.timedelta(hours=4)


def test_a_refused_spawn_is_backing_off(tmp_path):
    doc = _record(tmp_path, refused=True)
    assert (doc["state"], doc["task"]) == ("refused", "Backing Off")


def test_runs_outside_the_window_do_not_count(tmp_path):
    doc = _record(tmp_path, spawn_times=[T0 - dt.timedelta(hours=25), T0 - dt.timedelta(hours=1)])
    assert doc["runs_in_window"] == 1
    assert dt.datetime.fromisoformat(doc["cap_frees_at"]) == T0 + dt.timedelta(hours=23)


def test_no_runs_means_nothing_frees(tmp_path):
    assert _record(tmp_path)["cap_frees_at"] is None


def test_an_unreadable_run_log_publishes_null_not_zero(tmp_path):
    doc = _record(tmp_path, spawn_times=None)
    assert doc["runs_in_window"] is None and doc["cap_frees_at"] is None
    assert doc["state"] == "idle"


# --- continuity and the ETA rule ----------------------------------------

def test_a_task_keeps_its_start_across_ticks(tmp_path):
    _record(tmp_path)
    doc = _record(tmp_path, now=T0 + dt.timedelta(minutes=10))
    assert dt.datetime.fromisoformat(doc["task_started"]) == T0
    assert doc["task_eta_s"] is None


def test_a_child_is_tracked_across_ticks_until_it_dies(tmp_path):
    alive = {101}
    probe = lambda pid, _spawned: pid in alive  # noqa: E731
    _record(tmp_path, probe=probe, new_children=[(101, T0.timestamp())])
    later = _record(tmp_path, now=T0 + dt.timedelta(minutes=5), probe=probe)
    assert later["task"] == "Running Session"
    assert dt.datetime.fromisoformat(later["task_started"]) == T0
    alive.clear()
    ended = _record(tmp_path, now=T0 + dt.timedelta(minutes=10), probe=probe)
    assert ended["task"] == "Idle"
    assert dt.datetime.fromisoformat(ended["task_started"]) == T0 + dt.timedelta(minutes=10)


def test_the_eta_is_the_median_of_the_last_ten_and_null_under_three(tmp_path):
    assert status.eta_s([]) is None
    assert status.eta_s([60, 120]) is None
    assert status.eta_s([60, 120, 600]) == 120
    # Only the last ten count: over all 14 the median is 1, over the last ten 100.
    assert status.eta_s([1] * 8 + [100] * 6) == 100
    assert status.eta_s([10, 20, 30, 40]) == 25


def test_completed_sessions_feed_the_running_eta(tmp_path):
    t = T0
    for minutes in (10, 20, 30):
        _record(tmp_path, now=t, probe=_always_alive, new_children=[(7, t.timestamp())])
        t += dt.timedelta(minutes=minutes)
        _record(tmp_path, now=t)
        t += dt.timedelta(minutes=5)
    doc = _record(tmp_path, now=t, probe=_always_alive, new_children=[(7, t.timestamp())])
    assert doc["task"] == "Running Session"
    assert doc["task_eta_s"] == 20 * 60


def test_a_corrupt_state_file_starts_fresh(tmp_path):
    status.STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    status.STATE_PATH.write_text("{not json", encoding="utf-8")
    doc = _record(tmp_path)
    assert doc["task"] == "Idle"


def test_checking_inbox_is_published_without_breaking_idle_continuity(tmp_path):
    _record(tmp_path)
    later = T0 + dt.timedelta(minutes=5)
    shown = status.announce("Checking Inbox", now=later, spawn_times=[],
                            next_tick=later + dt.timedelta(minutes=5))
    assert (shown["state"], shown["task"]) == ("running", "Checking Inbox")
    assert _published() == shown
    doc = _record(tmp_path, now=later + dt.timedelta(seconds=2))
    assert doc["task"] == "Idle"
    assert dt.datetime.fromisoformat(doc["task_started"]) == T0


# --- the PID probe --------------------------------------------------------

def test_a_real_child_is_alive_then_dead_and_the_start_guard_binds():
    import os
    import subprocess
    import time
    launched = time.time()
    proc = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"],
                            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    try:
        assert status.pid_alive(proc.pid, launched) is True
        # Start-time guard: a process created far from the recorded launch is
        # a reused PID, not our child. Windows only - POSIX has no portable
        # creation time, so there the probe is existence only.
        if os.name == "nt":
            assert status.pid_alive(proc.pid, launched - 3600) is False
            assert status.pid_alive(proc.pid, launched + 3600) is False
    finally:
        proc.kill()
        proc.wait(timeout=10)
    assert status.pid_alive(proc.pid, launched) is False


def test_a_dead_pid_is_not_alive():
    assert status.pid_alive(2 ** 22 + 3, 0.0) is False


# --- the responder drives it ---------------------------------------------

def _inbox(tmp_path: Path, *names: str) -> Path:
    inbox = tmp_path / "moon_sync_inbox"
    inbox.mkdir(exist_ok=True)
    for name in names:
        (inbox / name).write_text(f"# From CS - note\n{name}\n", encoding="utf-8")
    return inbox


def _main(tmp_path: Path, inbox: Path, *extra: str) -> int:
    return responder.main(["--once", "--inbox", str(inbox),
                           "--state", str(tmp_path / "seen.json"),
                           "--runlog", str(tmp_path / "runs.jsonl"), *extra])


def test_main_publishes_idle_on_a_quiet_tick(tmp_path, capsys):
    inbox = _inbox(tmp_path)
    _main(tmp_path, inbox)  # cold start
    _main(tmp_path, inbox)
    assert _published()["task"] == "Idle"


def test_main_publishes_halted(tmp_path, monkeypatch, capsys):
    halt = tmp_path / "HALT"
    halt.write_text("", encoding="utf-8")
    monkeypatch.setattr(responder, "HALT_PATH", halt)
    _main(tmp_path, _inbox(tmp_path))
    assert (_published()["state"], _published()["task"]) == ("halted", "Halted")


def test_main_publishes_a_running_session_for_a_spawn(tmp_path, monkeypatch, capsys):
    inbox = _inbox(tmp_path)
    _main(tmp_path, inbox)
    (inbox / "2026-10-03-0915-from-CS-REVIEW-x.md").write_text("# From CS - x\n", encoding="utf-8")
    monkeypatch.setattr(responder, "spawn", lambda *_a, **_k: responder.Disposition(
        responder.AUTO, "spawn", "fake", True, 4242))
    monkeypatch.setattr(status, "pid_alive", lambda pid, _s: pid == 4242)
    monkeypatch.setattr(responder, "MAX_RUNS_PER_24H", 7)
    _main(tmp_path, inbox)
    doc = _published()
    assert (doc["state"], doc["task"], doc["runs_in_window"]) == ("running", "Running Session", 1)
    # The responder's OWN budget constant is what the widget sees, not a copy.
    assert doc["runs_cap"] == 7


def test_main_publishes_backing_off_when_the_gate_refuses(tmp_path, monkeypatch, capsys):
    inbox = _inbox(tmp_path)
    _main(tmp_path, inbox)
    (inbox / "2026-10-03-0915-from-CS-REVIEW-x.md").write_text("# From CS - x\n", encoding="utf-8")
    monkeypatch.setattr(responder, "spawn", lambda *_a, **_k: responder.Disposition(
        responder.UNAVAILABLE, "spawn", "headless spawn refused: x", True))
    _main(tmp_path, inbox)
    assert (_published()["state"], _published()["task"]) == ("refused", "Backing Off")


def test_a_dry_run_publishes_nothing(tmp_path, capsys):
    _main(tmp_path, _inbox(tmp_path), "--dry-run")
    assert not status.STATUS_PATH.exists()


def test_a_status_write_failure_never_fails_the_tick(tmp_path, monkeypatch, capsys):
    def _boom(_path, _doc):
        raise OSError("disk full")
    monkeypatch.setattr(status, "write_atomic", _boom)
    assert _main(tmp_path, _inbox(tmp_path)) == 0
    assert "status_error" in json.loads(capsys.readouterr().out)


def test_spawn_reports_the_child_pid(tmp_path, monkeypatch):
    class _Proc:
        pid = 31337
    monkeypatch.setattr(responder.shutil, "which", lambda _n: r"C:\fake\claude.exe")
    monkeypatch.setattr(responder.lw_headless_env, "child_env", lambda **_k: {})
    monkeypatch.setattr(responder.subprocess, "Popen", lambda *_a, **_k: _Proc())
    note = tmp_path / "2026-10-03-0915-from-CS-x.md"
    note.write_text("x", encoding="utf-8")
    assert responder.spawn(note).pid == 31337
