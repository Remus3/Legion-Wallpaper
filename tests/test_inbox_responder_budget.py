"""Arms for the responder's UNIFORM budget: ONE number (MAIN 0855, 2026-10-03).

WHY. The operator, relayed by MAIN 0855 (digest-verified), verbatim: "have all
tree's / siblings at the same amount; IE: 120". Every tree carries ONE budget:
at most 120 headless runs started per rolling 24 hours (SS's 12, x10).

MAIN 0845 had also set four other knobs (spawns per tick 30, turns per run 300,
hop budget 320, replies per sender per 24 h 30). 0855 RETRACTED them as MAIN's
reading, not the operator's, and ordered each restored to its pre-0845 value:

    runs started per 24 h        none -> 120   KEPT
    spawns per tick              3              restored (0845 had made it 30)
    turns per run                none           restored (no --max-turns)
    hop budget                   none           never had a constant here
    replies per sender per 24 h  none           restored (no per-sender cap)

The arms below pin both halves: the one number, and the absence of the four.

THE LEDGER IS THE RUN LOG. The 24-hour budget counts AUTO spawns already
recorded in `runs.jsonl`; no second store was invented. A spawn that came back
UNAVAILABLE started no run and costs nothing. A note held back by the budget
stays UNSEEN, exactly like a note over the per-tick cap: deferred, not dropped.

COULD-NOT-READ IS NOT ZERO. A log that exists but cannot be read is not an
empty one, so the cycle spawns NOTHING and says why. An ABSENT log is a real
zero - the file is created by the first non-idle cycle.
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


@pytest.fixture(autouse=True)
def _live_state_is_never_touched(monkeypatch, tmp_path):
    """Same isolation as the sibling responder files: the live kill switch is
    never read and the live run log is never written (guarded at the writer)."""
    monkeypatch.setattr(responder, "HALT_PATH", tmp_path / "never-created-HALT")
    real = responder.RUNLOG_PATH.resolve()
    original = responder._append_runlog
    hits: list[str] = []

    def _guarded(path, record):
        if Path(path).resolve() == real:
            hits.append(str(path))
            raise RuntimeError("test arm wrote the live run log")
        return original(path, record)

    monkeypatch.setattr(responder, "_append_runlog", _guarded)
    yield
    assert hits == [], f"an arm wrote the live run log at {real}: {hits}"


@pytest.fixture
def spawns(monkeypatch):
    """Every note the cycle tried to spawn on, in order. Never a real process."""
    seen: list[str] = []

    def _fake(path, dry_run=False):
        seen.append(Path(path).name)
        return responder._auto("spawn", "fake pid")

    monkeypatch.setattr(responder, "spawn", _fake)
    return seen


@pytest.fixture
def inbox(tmp_path):
    """A baselined inbox: the cold start is behind it, the run log is empty."""
    box = tmp_path / "moon_sync_inbox"
    box.mkdir()
    _write(box, "2026-10-03-0000-from-RC-baseline.md")
    _run(tmp_path, box)
    (tmp_path / "runs.jsonl").unlink(missing_ok=True)
    return box


def _write(box: Path, name: str) -> None:
    (box / name).write_text(f"# From {name.split('-from-')[1].split('-')[0]}\n",
                            encoding="utf-8")


def _run(tmp_path: Path, box: Path) -> dict:
    """One cycle, every path inside `tmp_path`; returns the printed payload."""
    import contextlib
    import io

    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        rc = responder.main(["--once", "--inbox", str(box),
                             "--state", str(tmp_path / "seen.json"),
                             "--runlog", str(tmp_path / "runs.jsonl")])
    assert rc == 0
    return json.loads(out.getvalue())


def _ago(hours: float) -> str:
    stamp = dt.datetime.now(dt.UTC) - dt.timedelta(hours=hours)
    return stamp.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _history(tmp_path: Path, sender: str, count: int, *, hours_ago: float = 1.0,
             verdict: str = responder.AUTO) -> None:
    """`count` past spawns on `sender`'s notes, as the run log records them."""
    spawned = [{"note": f"2026-10-02-{i:04d}-from-{sender}-past.md", "verdict": verdict,
                "reason": "detached headless session pid 1", "checked": True}
               for i in range(count)]
    record = {"ts": _ago(hours_ago), "event": "cycle", "new_notes": count,
              "deferred": 0, "skipped": [], "spawned": spawned}
    with (tmp_path / "runs.jsonl").open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record) + "\n")


# --------------------------------------------------------------------------
# The values
# --------------------------------------------------------------------------

def test_the_budget_is_one_number_120_runs_per_24h():
    assert responder.MAX_RUNS_PER_24H == 120


def test_the_per_tick_cap_is_back_at_its_pre_0845_value():
    assert responder.MAX_SPAWNS_PER_CYCLE == 3, "MAIN 0855 restored 30 -> 3"


@pytest.mark.parametrize("retracted", ["MAX_TURNS_PER_RUN", "MAX_SPAWNS_PER_SENDER_24H"])
def test_the_retracted_0845_knobs_do_not_exist(retracted):
    """None before 0845, so restoring them means there is no such knob at all."""
    assert not hasattr(responder, retracted)


def test_the_spawn_argv_carries_no_turn_cap():
    argv = responder.spawn_argv(Path("moon_sync_inbox/note.md"))
    assert "--max-turns" not in argv, "MAIN 0855 retracted turns per run"
    assert argv[-1].startswith("A new cross-repo note arrived"), "prompt stays last"


# --------------------------------------------------------------------------
# Runs started per 24 h
# --------------------------------------------------------------------------

def test_the_daily_run_budget_holds_back_what_it_cannot_afford(tmp_path, inbox, spawns):
    for i in range(4):
        _history(tmp_path, f"S{chr(65 + i)}", 29)        # 116 runs
    _history(tmp_path, "RSC", 3)                         # 119
    for i in range(3):
        _write(inbox, f"2026-10-03-010{i}-from-RC-ask-{i}.md")

    payload = _run(tmp_path, inbox)

    assert spawns == ["2026-10-03-0100-from-RC-ask-0.md"]
    assert payload["deferred"] == 2
    assert payload["budget"]["runs_24h"] == 119
    assert len(responder.new_notes(inbox, tmp_path / "seen.json")) == 2, \
        "held back means deferred, never dropped"


def test_runs_older_than_a_day_cost_nothing(tmp_path, inbox, spawns):
    for i in range(5):
        _history(tmp_path, f"S{chr(65 + i)}", 30, hours_ago=25)
    _write(inbox, "2026-10-03-0100-from-RC-ask.md")

    _run(tmp_path, inbox)

    assert spawns == ["2026-10-03-0100-from-RC-ask.md"]


def test_a_spawn_that_never_started_costs_nothing(tmp_path, inbox, spawns):
    for i in range(5):
        _history(tmp_path, f"S{chr(65 + i)}", 30, verdict=responder.UNAVAILABLE)
    _write(inbox, "2026-10-03-0100-from-RC-ask.md")

    _run(tmp_path, inbox)

    assert spawns == ["2026-10-03-0100-from-RC-ask.md"]


def test_a_torn_log_line_is_skipped_not_fatal(tmp_path, inbox, spawns):
    _history(tmp_path, "CS", 2)
    with (tmp_path / "runs.jsonl").open("a", encoding="utf-8") as fh:
        fh.write('{"ts": "2026-10-03T00:00:00Z", "event": "cyc')
    _write(inbox, "2026-10-03-0100-from-RC-ask.md")

    payload = _run(tmp_path, inbox)

    assert spawns == ["2026-10-03-0100-from-RC-ask.md"]
    assert payload["budget"]["runs_24h"] == 2


def test_an_unreadable_log_spawns_nothing_and_says_so(tmp_path, inbox, spawns):
    """COULD-NOT-READ is not ZERO: a directory where the log should be."""
    (tmp_path / "runs.jsonl").mkdir()
    _write(inbox, "2026-10-03-0100-from-RC-ask.md")

    payload = _run(tmp_path, inbox)

    assert spawns == []
    assert payload["deferred"] == 1
    assert payload["budget"]["error"]
    assert len(responder.new_notes(inbox, tmp_path / "seen.json")) == 1


def test_one_cycle_cannot_overrun_the_daily_budget(tmp_path, inbox, spawns):
    _history(tmp_path, "CS", 118)
    for i in range(3):
        _write(inbox, f"2026-10-03-010{i}-from-RC-ask-{i}.md")

    payload = _run(tmp_path, inbox)

    assert len(spawns) == 2
    assert payload["deferred"] == 1


# --------------------------------------------------------------------------
# No per-sender cap (MAIN 0855 retracted 0845's replies-per-sender knob)
# --------------------------------------------------------------------------

def test_one_senders_volume_never_binds_below_the_daily_budget(tmp_path, inbox, spawns):
    """100 runs on CS's notes in a day: only the ONE number may hold CS back."""
    _history(tmp_path, "CS", 100)
    for i in range(3):
        _write(inbox, f"2026-10-03-010{i}-from-CS-again-{i}.md")

    payload = _run(tmp_path, inbox)

    assert len(spawns) == 3
    assert payload["deferred"] == 0


def test_an_unconstrained_cycle_reports_only_the_run_count(tmp_path, inbox, spawns):
    _write(inbox, "2026-10-03-0100-from-RC-ask.md")

    payload = _run(tmp_path, inbox)

    assert spawns == ["2026-10-03-0100-from-RC-ask.md"]
    assert payload["budget"] == {"runs_24h": 0}


# --------------------------------------------------------------------------
# The loop dampers MAIN 0845 s3 (kept by 0855 s3) says every tree must carry
# --------------------------------------------------------------------------

def test_self_and_terminal_notes_still_never_spawn_under_the_daily_budget(
        tmp_path, inbox, spawns):
    _write(inbox, "2026-10-03-0100-from-LW-RESPONDER-ACK-record.md")
    _write(inbox, "2026-10-03-0101-from-RC-ANSWER-done-TERMINAL-no-reply.md")
    _write(inbox, "2026-10-03-0102-from-RC-ask.md")

    payload = _run(tmp_path, inbox)

    assert spawns == ["2026-10-03-0102-from-RC-ask.md"]
    assert len(payload["skipped"]) == 2
