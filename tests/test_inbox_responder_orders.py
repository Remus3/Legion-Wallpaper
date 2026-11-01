"""Arms for the responder's pending-ORDER list (MAIN 2026-11-01-1223 items 1, 2).

Kit v27: `mark_seen` queues a WORK note and only `mark_work_done` closes it. The
responder reads the list first on every tick and closes a row only on evidence,
an ANSWER of ours in the outbox naming the note's sha256 or file name.
"""
from __future__ import annotations

import contextlib
import io
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import lw_inbox_responder as responder  # noqa: E402

fi = responder.fleet_inbox
he = responder.lw_headless_env

NAME = "2026-11-01-1223-from-MAIN-ORDER-to-LW-thing-ONE-ANSWER.md"


@pytest.fixture
def world(tmp_path, monkeypatch):
    box = tmp_path / "inbox"
    box.mkdir()
    outbox = tmp_path / "outbox"
    outbox.mkdir()
    monkeypatch.setattr(responder, "OUTBOX", outbox)
    monkeypatch.setattr(responder, "HALT_PATH", tmp_path / "never-created-HALT")
    return box, outbox


def _queue(box: Path) -> tuple[Path, str]:
    note = box / NAME
    note.write_text("# From MAIN - ORDER\nORDER HOP: 1\n", encoding="ascii")
    d = fi.Decision(fi.WORK, "ORDER", "MAIN", "order", 1)
    row = fi.enqueue_work(he.FLEET_ROOT, note, d)
    return note, row["sha256"]


def _pending_marker() -> list:
    path = Path(he.FLEET_ROOT) / fi.PENDING_REL
    return json.loads(path.read_text(encoding="ascii"))["pending"]


def test_a_queued_order_stays_open_with_no_reply(world):
    box, _outbox = world
    _queue(box)
    res = responder.reconcile_orders()
    assert res == {"pending_orders": [NAME], "orders_closed": []}
    assert [r["note"] for r in _pending_marker()] == [NAME]


def test_a_reply_that_names_another_note_closes_nothing(world):
    box, outbox = world
    _queue(box)
    (outbox / "2026-11-01-1300-from-LW-ANSWER-to-MAIN-other-TERMINAL.md").write_text(
        "HOP: 2\nsha256 " + "0" * 64 + "\n", encoding="ascii")
    assert responder.reconcile_orders()["orders_closed"] == []
    assert len(fi.pending_work(he.FLEET_ROOT)) == 1


def test_a_non_answer_file_naming_the_digest_closes_nothing(world):
    box, outbox = world
    _, sha = _queue(box)
    (outbox / "2026-11-01-1300-from-LW-INFORMATION-to-MAIN-x.md").write_text(sha, encoding="ascii")
    assert responder.reconcile_orders()["orders_closed"] == []


@pytest.mark.parametrize("by", ["sha256", "name"])
def test_an_answer_naming_the_order_closes_the_row_with_a_done_line(world, by):
    box, outbox = world
    _, sha = _queue(box)
    reply = "2026-11-01-1300-from-LW-ANSWER-to-MAIN-1223-TERMINAL.md"
    (outbox / reply).write_text(f"HOP: 2\n{sha if by == 'sha256' else NAME}\n", encoding="ascii")
    res = responder.reconcile_orders()
    assert res == {"pending_orders": [], "orders_closed": [NAME]}
    assert fi.pending_work(he.FLEET_ROOT) == []
    assert _pending_marker() == []
    lines = (Path(he.FLEET_ROOT) / fi.WORK_REL).read_text(encoding="utf-8").splitlines()
    done = json.loads(lines[-1])
    assert (done["op"], done["outcome"]) == ("done", f"answered: {reply}")


def test_a_dry_run_reads_the_list_and_closes_nothing(world):
    box, outbox = world
    _, sha = _queue(box)
    (outbox / "2026-11-01-1300-from-LW-ANSWER-to-MAIN-1223.md").write_text(sha, encoding="ascii")
    assert responder.reconcile_orders(dry_run=True)["orders_closed"] == []
    assert len(fi.pending_work(he.FLEET_ROOT)) == 1


def _tick(tmp_path: Path, box: Path) -> dict:
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        rc = responder.main(["--once", "--inbox", str(box), "--state", str(tmp_path / "seen.json"),
                             "--runlog", str(tmp_path / "runs.jsonl")])
    assert rc == 0
    return json.loads(out.getvalue())


def test_the_tick_reads_the_pending_list_first_and_reports_it(world, tmp_path, monkeypatch):
    box, _outbox = world
    _queue(box)
    order: list[str] = []
    real = fi.pending_work

    def _spy(root):
        order.append("pending")
        return real(root)

    monkeypatch.setattr(fi, "pending_work", _spy)
    real_fetch = responder._entries
    monkeypatch.setattr(responder, "_entries",
                        lambda p: (order.append("inbox"), real_fetch(p))[1])
    payload = _tick(tmp_path, box)
    assert order[:2] == ["pending", "inbox"]
    assert payload["pending_orders"] == [NAME]


def test_the_tick_closes_a_row_answered_by_its_own_child(world, tmp_path, monkeypatch):
    """The real order of a tick: the child writes the reply, THEN the tick's
    mark_seen queues the row; the end-of-tick read has to close it."""
    box, outbox = world
    _tick(tmp_path, box)                      # the cold start baseline
    note = box / NAME
    note.write_text("# From MAIN - ORDER\nORDER HOP: 1\n", encoding="ascii")

    def _child(path, dry_run=False, kind="inbox"):
        (outbox / "2026-11-01-1300-from-LW-ANSWER-to-MAIN-1223.md").write_text(
            NAME, encoding="ascii")
        return responder._auto("spawn", "fake pid")

    monkeypatch.setattr(responder, "spawn", _child)
    monkeypatch.setattr(responder, "main_provenance", lambda *_a, **_k: "MATCH", raising=False)
    payload = _tick(tmp_path, box)
    assert [s["note"] for s in payload["spawned"]] == [NAME]
    assert payload["orders_closed"] == [NAME]
    assert payload["pending_orders"] == []
    assert fi.pending_work(he.FLEET_ROOT) == []


def test_a_broken_queue_never_fails_the_tick(world, tmp_path, monkeypatch):
    box, _outbox = world

    def _boom(_root):
        raise OSError("disk")

    monkeypatch.setattr(fi, "pending_work", _boom)
    assert _tick(tmp_path, box)["orders_error"] == "OSError: disk"


def test_the_child_is_told_a_reply_must_name_the_order(world):
    box, _outbox = world
    note, _ = _queue(box)
    assert "closes its row" in responder.inbox_cost_rule(note)


# ------------------------------------------------------------ item 2, the gate's cap

def _machine_cap(tmp_path: Path, monkeypatch, cap: int) -> None:
    cfg = tmp_path / "lanes.json"
    cfg.write_text(json.dumps({"runs_cap": {"LW": cap}}), encoding="ascii")
    monkeypatch.setenv("FLEET_LANES_CONFIG", str(cfg))


def test_the_gate_reads_the_machine_cap_not_the_kit_constant(tmp_path, monkeypatch):
    _machine_cap(tmp_path, monkeypatch, 500)
    b = he.budget()
    assert b.cap == 500
    for _ in range(120):
        b.record()
    capped, budget = responder.within_budget([1, 2, 3, 4])
    assert (capped, budget) == ([1, 2, 3], {"runs_24h": 120})


def test_the_gate_still_stops_at_the_machine_cap(tmp_path, monkeypatch):
    _machine_cap(tmp_path, monkeypatch, 130)
    b = he.budget()
    for _ in range(130):
        b.record()
    assert responder.within_budget([1])[0] == []


def test_the_gate_reads_the_default_with_no_machine_config():
    assert he.budget().cap == he.kit.RUNS_CAP == 120


def test_the_constant_read_is_gone_from_the_responder():
    text = (ROOT / "tools" / "lw_inbox_responder.py").read_text(encoding="ascii")
    assert "kit.RUNS_CAP" not in text
