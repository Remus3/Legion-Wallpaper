"""Arms for the responder's UNIFORM budget: ONE number (MAIN 0855, 2026-10-03).

WHY. The operator, relayed by MAIN 0855 (digest-verified), verbatim: "have all
tree's / siblings at the same amount; IE: 120". Since fleet kit v3 that one
number is the KIT's: `RunBudget` (RUNS_CAP 120 per rolling WINDOW_S 86400),
persisted in `ops/loop/control/headless_budget.json` and shared by every LW
headless path. The responder keeps only its per-tick burst cap of 3.

MAIN 0845's other knobs were RETRACTED by 0855 and stay absent:

    runs started per 24 h        120 (the kit's RunBudget)
    spawns per tick              3              restored (0845 had made it 30)
    turns per run                none           restored (no --max-turns)
    replies per sender per 24 h  none           restored (no per-sender cap)

A note held back by the budget stays UNSEEN: deferred, not dropped.

KNOWN KIT GAP, reported to MAIN and pinned xfail(strict) below: the kit's
RunBudget reads an unreadable budget file as ZERO runs (could-not-read reads as
zero), where LW's old run-log budget spawned nothing.
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


def _history(count: int) -> None:
    """`count` runs already started in the kit's rolling window."""
    b = responder.lw_headless_env.budget()
    for _ in range(count):
        b.record()


# --------------------------------------------------------------------------
# The values
# --------------------------------------------------------------------------

def test_the_budget_is_one_number_the_kits_120_runs_per_24h():
    kit = responder.lw_headless_env.kit
    assert (kit.RUNS_CAP, kit.WINDOW_S) == (120, 86400)
    assert responder.lw_headless_env.budget().cap == 120
    assert not hasattr(responder, "MAX_RUNS_PER_24H"), "one budget, the kit's"


def test_the_per_tick_cap_is_back_at_its_pre_0845_value():
    assert responder.MAX_SPAWNS_PER_CYCLE == 3, "MAIN 0855 restored 30 -> 3"


@pytest.mark.parametrize("retracted", ["MAX_TURNS_PER_RUN", "MAX_SPAWNS_PER_SENDER_24H"])
def test_the_retracted_0845_knobs_do_not_exist(retracted):
    assert not hasattr(responder, retracted)


def test_the_spawn_carries_no_turn_cap():
    assert "--max-turns" not in responder.RESPONDER_EXTRA, "MAIN 0855 retracted it"
    assert responder.spawn_prompt(Path("moon_sync_inbox/note.md")).startswith(
        "A new cross-repo note arrived")


# --------------------------------------------------------------------------
# Runs started per 24 h
# --------------------------------------------------------------------------

def test_the_daily_run_budget_holds_back_what_it_cannot_afford(tmp_path, inbox, spawns):
    _history(119)
    for i in range(3):
        _write(inbox, f"2026-10-03-010{i}-from-RC-ask-{i}.md")

    payload = _run(tmp_path, inbox)

    assert spawns == ["2026-10-03-0100-from-RC-ask-0.md"]
    assert payload["deferred"] == 2
    assert payload["budget"]["runs_24h"] == 119
    held = responder.new_notes(inbox, tmp_path / "seen.json")
    assert len(held) == 2, "held back means deferred, never dropped"


def test_runs_older_than_a_day_cost_nothing(tmp_path, inbox, spawns):
    b = responder.lw_headless_env.budget()
    b.path.parent.mkdir(parents=True, exist_ok=True)
    old = b.clock() - b.window - 60
    b.path.write_text(json.dumps({"starts": [old] * 150}), encoding="ascii")
    _write(inbox, "2026-10-03-0100-from-RC-ask.md")

    _run(tmp_path, inbox)

    assert spawns == ["2026-10-03-0100-from-RC-ask.md"]


def test_a_full_budget_spawns_nothing_and_publishes_the_limit(tmp_path, inbox, spawns):
    _history(120)
    _write(inbox, "2026-10-03-0100-from-RC-ask.md")

    payload = _run(tmp_path, inbox)

    assert spawns == []
    assert payload["deferred"] == 1
    kit = responder.lw_headless_env.kit
    status = json.loads((Path(responder.lw_headless_env.FLEET_ROOT) / kit.STATUS_REL)
                        .read_text(encoding="ascii"))
    assert (status["state"], status["task"]) == ("limit", "Turn Limit Reached")


@pytest.mark.xfail(strict=True, reason="kit v3 gap: RunBudget reads an unreadable "
                   "budget file as zero runs; reported to MAIN, not patched")
def test_an_unreadable_budget_spawns_nothing(tmp_path, inbox, spawns):
    b = responder.lw_headless_env.budget()
    b.path.parent.mkdir(parents=True, exist_ok=True)
    b.path.write_text("{not json", encoding="ascii")
    _write(inbox, "2026-10-03-0100-from-RC-ask.md")

    _run(tmp_path, inbox)

    assert spawns == []


def test_one_cycle_cannot_overrun_the_daily_budget(tmp_path, inbox, spawns):
    _history(118)
    for i in range(3):
        _write(inbox, f"2026-10-03-010{i}-from-RC-ask-{i}.md")

    payload = _run(tmp_path, inbox)

    assert len(spawns) == 2
    assert payload["deferred"] == 1


# --------------------------------------------------------------------------
# No per-sender cap (MAIN 0855 retracted 0845's replies-per-sender knob)
# --------------------------------------------------------------------------

def test_one_senders_volume_never_binds_below_the_daily_budget(tmp_path, inbox, spawns):
    _history(100)
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
