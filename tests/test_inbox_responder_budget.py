"""Arms for the responder's UNIFORM budget (MAIN 0845, 2026-10-03).

WHY. MAIN measured the six responders capping six DIFFERENT things and relayed
the operator's order, verbatim: "increase the budget to be the same to all
siblings - and it needs to be x10 of whatever amount it is now". Every tree
carries the same five values, each ten times the only existing figure:

    runs started per 24 h        120   (SS 12)
    spawns per tick               30   (LW 3)
    turns per run                300   (RC 30, passed as --max-turns)
    hop budget (reply chain)     320   (RC 32) - NOT expressible here, see below
    replies per sender per 24 h   30   (RSC 3)

THE LEDGER IS THE RUN LOG. Both 24-hour knobs count AUTO spawns already
recorded in `runs.jsonl`; no second store was invented. A spawn that came back
UNAVAILABLE started no run and costs nothing. A note held back by a budget
stays UNSEEN, exactly like a note over the per-tick cap: deferred, not dropped.

COULD-NOT-READ IS NOT ZERO. A log that exists but cannot be read is not an
empty one, so the cycle spawns NOTHING and says why. An ABSENT log is a real
zero - the file is created by the first non-idle cycle.

HOP BUDGET. LW's notes carry no hop counter and no thread id, so a reply-chain
depth cannot be read off the channel. MAIN section 2 says to name the nearest
equivalent rather than invent a second mechanism: LW answers one hop per
incoming note, so the per-sender cap bounds LW's side of any chain at 30 hops
per sender per 24 h, below 320, and the self and terminal skips stop LW
answering itself. No HOP constant exists to be decorative.
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

def test_the_uniform_values_are_ten_times_the_measured_figures():
    assert responder.MAX_SPAWNS_PER_CYCLE == 30
    assert responder.MAX_RUNS_PER_24H == 120
    assert responder.MAX_TURNS_PER_RUN == 300
    assert responder.MAX_SPAWNS_PER_SENDER_24H == 30


def test_the_spawn_argv_caps_turns_per_run():
    argv = responder.spawn_argv(Path("moon_sync_inbox/note.md"))
    assert argv[argv.index("--max-turns") + 1] == str(responder.MAX_TURNS_PER_RUN)
    assert argv[-1].startswith("A new cross-repo note arrived"), "prompt stays last"


# --------------------------------------------------------------------------
# Runs started per 24 h
# --------------------------------------------------------------------------

def test_the_daily_run_budget_holds_back_what_it_cannot_afford(tmp_path, inbox, spawns):
    for i in range(4):
        _history(tmp_path, f"S{chr(65 + i)}", 29)        # 116 runs, no sender over its cap
    _history(tmp_path, "RSC", 3)                 # 119
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


# --------------------------------------------------------------------------
# Replies per sender per 24 h (one spawn answers at most one note, under A5)
# --------------------------------------------------------------------------

def test_a_sender_at_its_cap_waits_while_another_sender_is_answered(tmp_path, inbox, spawns):
    _history(tmp_path, "CS", 30)
    _write(inbox, "2026-10-03-0100-from-CS-again.md")
    _write(inbox, "2026-10-03-0101-from-RC-ask.md")

    payload = _run(tmp_path, inbox)

    assert spawns == ["2026-10-03-0101-from-RC-ask.md"]
    assert payload["deferred"] == 1
    assert payload["budget"]["sender_capped"] == ["CS"]


def test_one_cycle_cannot_overrun_a_senders_cap(tmp_path, inbox, spawns):
    _history(tmp_path, "LL", 28)
    for i in range(4):
        _write(inbox, f"2026-10-03-010{i}-from-LL-burst-{i}.md")

    payload = _run(tmp_path, inbox)

    assert len(spawns) == 2
    assert payload["deferred"] == 2


def test_an_unconstrained_cycle_reports_no_budget_block(tmp_path, inbox, spawns):
    _write(inbox, "2026-10-03-0100-from-RC-ask.md")

    payload = _run(tmp_path, inbox)

    assert spawns == ["2026-10-03-0100-from-RC-ask.md"]
    assert payload["budget"] == {"runs_24h": 0, "sender_capped": []}


# --------------------------------------------------------------------------
# The loop dampers MAIN says a 10x budget makes MORE important
# --------------------------------------------------------------------------

def test_self_and_terminal_notes_still_never_spawn_under_the_larger_budget(
        tmp_path, inbox, spawns):
    _write(inbox, "2026-10-03-0100-from-LW-RESPONDER-ACK-record.md")
    _write(inbox, "2026-10-03-0101-from-RC-ANSWER-done-TERMINAL-no-reply.md")
    _write(inbox, "2026-10-03-0102-from-RC-ask.md")

    payload = _run(tmp_path, inbox)

    assert spawns == ["2026-10-03-0102-from-RC-ask.md"]
    assert len(payload["skipped"]) == 2
