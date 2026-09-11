"""Arms for the responder's run log, `ops/runtime/inbox_responder/runs.jsonl`.

WHY A LOG AT ALL. `LW-InboxResponder` fires every five minutes detached and
headless, with `stdout` going to `DEVNULL` because a scheduled task has nowhere
to put it. Before this file the only durable trace of a cycle was its side
effect: a reply note (AUTO) or nothing whatsoever (DRAFT, deferred, halted).
Which rule refused, and whether the gate RAN or COULD NOT RUN - the module's
own three-disposition distinction - survived nowhere.

WHAT IT IS NOT. It is not a liveness signal. `Get-ScheduledTaskInfo` already
carries `LastRunTime` and `LastTaskResult`, so an IDLE cycle writes nothing and
the arms below pin that: 288 cycles a day of "found nothing" would bury the
handful of lines that answer a question, and the question "did it run" already
has a better source. The log answers "what did it DO".

APPEND, NOT THE ATOMIC TMP-REPLACE the repo mandates elsewhere. A tmp-and-
replace rewrites the whole file per cycle, which is how an append-only ledger
loses history to a crash mid-copy; a single `write()` of one complete newline-
terminated line is the ledger pattern `.jsonl` already carries here. The arms
pin whole-line-at-a-time and valid-JSON-per-line, which is what makes a partial
line detectable rather than silent.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import lw_inbox_responder as responder  # noqa: E402


@pytest.fixture(autouse=True)
def _the_live_run_log_is_never_touched():
    """Same guard as `test_inbox_responder.py`, and it is needed MORE here:
    every arm below is about the log, so a forgotten `--runlog` would land in
    the operator's real tree and look exactly like a real cycle."""
    real = responder.RUNLOG_PATH
    before = real.stat().st_mtime_ns if real.exists() else None
    yield
    after = real.stat().st_mtime_ns if real.exists() else None
    assert after == before, f"an arm wrote the live run log at {real}"


def _inbox(tmp_path: Path, *names: str) -> Path:
    inbox = tmp_path / "moon_sync_inbox"
    inbox.mkdir(exist_ok=True)
    for name in names:
        (inbox / name).write_text(f"note {name}\n", encoding="utf-8")
    return inbox


def _run(tmp_path: Path, inbox: Path, *extra: str) -> int:
    """One cycle with every path pointed inside `tmp_path`."""
    return responder.main([
        "--once",
        "--inbox", str(inbox),
        "--state", str(tmp_path / "seen.json"),
        "--halt", str(tmp_path / "HALT"),
        "--runlog", str(tmp_path / "runs.jsonl"),
        *extra,
    ])


def _lines(tmp_path: Path) -> list[dict]:
    log = tmp_path / "runs.jsonl"
    if not log.exists():
        return []
    raw = log.read_text(encoding="utf-8")
    assert raw.endswith("\n"), "every record must be newline-terminated"
    return [json.loads(line) for line in raw.splitlines() if line.strip()]


def _baseline(tmp_path: Path, inbox: Path) -> None:
    """Get past the cold start so later cycles are ordinary ones."""
    _run(tmp_path, inbox)
    (tmp_path / "runs.jsonl").unlink(missing_ok=True)


# --------------------------------------------------------------------------
# What gets written
# --------------------------------------------------------------------------

def test_a_spawning_cycle_is_recorded(tmp_path, monkeypatch):
    """MIRROR ARM. The log must actually fire, or the arms below grade nothing."""
    inbox = _inbox(tmp_path, "2026-09-11-0001-from-RC-hello.md")
    _baseline(tmp_path, inbox)
    (inbox / "2026-09-11-0002-from-CS-second.md").write_text("x\n", encoding="utf-8")
    monkeypatch.setattr(responder, "spawn",
                        lambda p, dry_run=False: responder._auto("spawn", "pid 4242"))

    assert _run(tmp_path, inbox) == 0

    (record,) = _lines(tmp_path)
    assert record["event"] == "cycle"
    assert record["new_notes"] == 1
    assert record["deferred"] == 0
    assert record["spawned"][0]["note"] == "2026-09-11-0002-from-CS-second.md"
    assert record["spawned"][0]["verdict"] == responder.AUTO


def test_the_record_carries_the_rule_and_whether_the_gate_could_check(tmp_path, monkeypatch):
    """The whole point. CHECKED-AND-REFUSED and COULD-NOT-CHECK are different
    answers, and a log that flattens them repeats the defect the module exists
    to avoid."""
    inbox = _inbox(tmp_path, "2026-09-11-0001-from-RC-hello.md")
    _baseline(tmp_path, inbox)
    (inbox / "2026-09-11-0002-from-CS-second.md").write_text("x\n", encoding="utf-8")
    monkeypatch.setattr(responder, "spawn", lambda p, dry_run=False: responder.Disposition(
        responder.UNAVAILABLE, "spawn", "claude CLI is not on PATH", False))

    _run(tmp_path, inbox)

    (record,) = _lines(tmp_path)
    entry = record["spawned"][0]
    assert entry["verdict"] == responder.UNAVAILABLE
    assert entry["checked"] is False
    assert entry["reason"]


def test_every_record_carries_a_real_utc_timestamp(tmp_path, monkeypatch):
    """Cross-repo note FILENAMES carry a fictional clock that drifts per sender.
    The log sorts by its own stamp, so the stamp has to be the real one."""
    import datetime as dt

    inbox = _inbox(tmp_path, "2026-09-11-0001-from-RC-hello.md")
    _baseline(tmp_path, inbox)
    (inbox / "2026-09-11-0002-from-CS-second.md").write_text("x\n", encoding="utf-8")
    monkeypatch.setattr(responder, "spawn",
                        lambda p, dry_run=False: responder._auto("spawn", "pid 1"))
    before = dt.datetime.now(dt.UTC).replace(microsecond=0)

    _run(tmp_path, inbox)

    (record,) = _lines(tmp_path)
    stamp = dt.datetime.fromisoformat(record["ts"])
    assert stamp.tzinfo is not None, "a naive stamp is unreadable across machines"
    assert stamp >= before
    assert record["ts"].endswith("Z")


def test_a_deferred_remainder_is_recorded(tmp_path, monkeypatch):
    """A burst over the cap is the case where the operator most needs the count:
    the remainder is invisible until the next cycle picks it up."""
    inbox = _inbox(tmp_path, "2026-09-11-0000-from-RC-baseline.md")
    _baseline(tmp_path, inbox)
    for i in range(responder.MAX_SPAWNS_PER_CYCLE + 2):
        (inbox / f"2026-09-11-001{i}-from-CS-burst-{i}.md").write_text("x\n", encoding="utf-8")
    monkeypatch.setattr(responder, "spawn",
                        lambda p, dry_run=False: responder._auto("spawn", "pid 1"))

    _run(tmp_path, inbox)

    (record,) = _lines(tmp_path)
    assert record["new_notes"] == responder.MAX_SPAWNS_PER_CYCLE + 2
    assert record["deferred"] == 2
    assert len(record["spawned"]) == responder.MAX_SPAWNS_PER_CYCLE


def test_a_halted_cycle_is_recorded_with_its_reason(tmp_path):
    """A kill switch nobody can see the effect of is half a kill switch: the
    operator needs to tell HALTED apart from DEAD after the fact."""
    inbox = _inbox(tmp_path, "2026-09-11-0001-from-RC-hello.md")
    _baseline(tmp_path, inbox)
    (tmp_path / "HALT").write_text("stopped by hand during the 09-11 incident\n",
                                   encoding="utf-8")

    assert _run(tmp_path, inbox) == 0

    (record,) = _lines(tmp_path)
    assert record["event"] == "halted"
    assert "09-11 incident" in record["halted"]
    assert record["spawned"] == []


def test_a_cold_start_is_recorded_with_the_baselined_count(tmp_path):
    """The one cycle that reads 139 new notes and deliberately spawns nothing.
    Unlogged, it is indistinguishable from a responder that silently lost its
    state file and re-baselined over real mail."""
    inbox = _inbox(tmp_path, "a.md", "b.md", "c.md")

    assert _run(tmp_path, inbox) == 0

    (record,) = _lines(tmp_path)
    assert record["event"] == "cold_start"
    assert record["baselined"] == 3
    assert record["spawned"] == []


# --------------------------------------------------------------------------
# What does NOT get written
# --------------------------------------------------------------------------

def test_an_idle_cycle_writes_nothing(tmp_path):
    """288 no-op lines a day would bury the handful that answer a question, and
    liveness already has a better source in the scheduler's own LastRunTime."""
    inbox = _inbox(tmp_path, "2026-09-11-0001-from-RC-hello.md")
    _baseline(tmp_path, inbox)

    assert _run(tmp_path, inbox) == 0

    assert _lines(tmp_path) == []
    assert not (tmp_path / "runs.jsonl").exists()


def test_a_dry_run_writes_nothing(tmp_path, monkeypatch):
    """`--dry-run` records no state, and the log is state."""
    inbox = _inbox(tmp_path, "2026-09-11-0001-from-RC-hello.md")
    _baseline(tmp_path, inbox)
    (inbox / "2026-09-11-0002-from-CS-second.md").write_text("x\n", encoding="utf-8")
    monkeypatch.setattr(responder, "spawn",
                        lambda p, dry_run=False: responder._auto("spawn", "would launch"))

    assert _run(tmp_path, inbox, "--dry-run") == 0

    assert _lines(tmp_path) == []


# --------------------------------------------------------------------------
# The log never becomes the failure
# --------------------------------------------------------------------------

def test_an_unwritable_log_does_not_stop_the_cycle(tmp_path, monkeypatch):
    """DIRECTION THAT MATTERS. Observability is not worth a responder that dies
    when its disk is full - and on this box a full disk TRUNCATES rather than
    raising at open time, so this path is reachable."""
    inbox = _inbox(tmp_path, "2026-09-11-0001-from-RC-hello.md")
    _baseline(tmp_path, inbox)
    (inbox / "2026-09-11-0002-from-CS-second.md").write_text("x\n", encoding="utf-8")
    spawned: list[Path] = []

    def _spawn(path, dry_run=False):
        spawned.append(path)
        return responder._auto("spawn", "pid 7")

    monkeypatch.setattr(responder, "spawn", _spawn)

    def _boom(*a, **k):
        raise OSError("no space left on device")

    monkeypatch.setattr(responder, "_append_runlog", _boom)

    assert _run(tmp_path, inbox) == 0
    assert spawned, "the cycle must still have done its work"


def test_a_log_failure_is_reported_and_never_read_as_a_clean_cycle(tmp_path, capsys, monkeypatch):
    """COULD-NOT-WRITE is not WROTE. A swallowed failure turns an empty log into
    a claim that nothing happened, which is the false-GREEN shape this tree has
    measured repeatedly."""
    inbox = _inbox(tmp_path, "2026-09-11-0001-from-RC-hello.md")
    _baseline(tmp_path, inbox)
    capsys.readouterr()
    (inbox / "2026-09-11-0002-from-CS-second.md").write_text("x\n", encoding="utf-8")
    monkeypatch.setattr(responder, "spawn",
                        lambda p, dry_run=False: responder._auto("spawn", "pid 7"))
    monkeypatch.setattr(responder, "_append_runlog",
                        lambda *a, **k: (_ for _ in ()).throw(OSError("read-only fs")))

    _run(tmp_path, inbox)

    payload = json.loads(capsys.readouterr().out)
    assert "read-only fs" in payload["runlog_error"]


# --------------------------------------------------------------------------
# Shape of the file itself
# --------------------------------------------------------------------------

def test_the_log_appends_and_never_rewrites(tmp_path, monkeypatch):
    """The defect an atomic tmp-replace would introduce here: cycle two would
    silently erase cycle one."""
    inbox = _inbox(tmp_path, "2026-09-11-0000-from-RC-baseline.md")
    _baseline(tmp_path, inbox)
    monkeypatch.setattr(responder, "spawn",
                        lambda p, dry_run=False: responder._auto("spawn", "pid 1"))

    for i in range(3):
        (inbox / f"2026-09-11-000{i + 1}-from-CS-n{i}.md").write_text("x\n", encoding="utf-8")
        _run(tmp_path, inbox)

    records = _lines(tmp_path)
    assert len(records) == 3
    assert [r["new_notes"] for r in records] == [1, 1, 1]


def test_the_log_directory_is_created_on_demand(tmp_path, monkeypatch):
    """`ops/runtime/inbox_responder/` holds only the HALT file, so on a fresh
    clone the directory the log wants does not exist yet."""
    inbox = _inbox(tmp_path, "2026-09-11-0001-from-RC-hello.md")
    deep = tmp_path / "runtime" / "inbox_responder" / "runs.jsonl"
    responder.main(["--once", "--inbox", str(inbox),
                    "--state", str(tmp_path / "seen.json"),
                    "--halt", str(tmp_path / "HALT"),
                    "--runlog", str(deep)])

    assert deep.exists(), "a missing parent must not silently drop the record"


def test_the_default_log_sits_beside_the_kill_switch():
    """One directory for the responder's runtime state, and it is the gitignored
    one - this repo is PUBLIC and the log quotes note names and reasons."""
    assert responder.RUNLOG_PATH.parent == responder.HALT_PATH.parent
    assert responder.RUNLOG_PATH.name == "runs.jsonl"
    assert responder.RUNLOG_PATH.is_relative_to(responder.ROOT / "ops" / "runtime")
