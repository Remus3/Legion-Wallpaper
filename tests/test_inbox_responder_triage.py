"""FLEET-KIT v8 item 14 (MAIN 0310): the responder classifies FIRST.

LW has no separate lane loop for mail - `tools/lw_inbox_responder.py` IS the
loop for inbox purposes (MAIN 0310 section 4). Per tick it now runs the kit's
free `fleet_inbox.classify()` before anything can spawn:

  skip   - own note / TERMINAL / no-reply: marked seen, nothing else;
  ack    - ACK / INFORMATION / TERMINAL / ANSWER class, or past the hop limit:
           marked seen + a ledger line, NO spawn, NO note;
  work   - ORDER / FIX / RULING: the existing child run, kind="inbox";
  triage - anything else: ONE run with the kit's TRIAGE_SPAWN (sonnet, effort
           low), kind="triage"; parse_verdict() decides NOREPLY / ACK / ANSWER.

Outbound notes are capped at 6 per local day (ORDER / FIX / RULING exempt) and
every note the responder writes carries a `HOP: <n>` line.

Hermetic: every spawn is intercepted at `lw_headless_env.spawn` (conftest
already points the kit's FLEET_ROOT at a tmp dir), the carrier row and the
outbox are tmp paths, and the clock is the real one only for the local day.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import lw_inbox_responder as responder  # noqa: E402

fi = responder.fleet_inbox


@pytest.fixture(autouse=True)
def _isolated(monkeypatch, tmp_path):
    """No arm reads the operator's HALT, carriers or outbox, or writes the live log."""
    monkeypatch.setattr(responder, "HALT_PATH", tmp_path / "never-HALT")
    monkeypatch.setattr(responder, "RUNLOG_PATH", tmp_path / "live-runs-never.jsonl")
    monkeypatch.setattr(responder, "CARRIERS_PATH", tmp_path / "carriers.json")
    monkeypatch.setattr(responder, "OUTBOX", tmp_path / "lw_outbox")


@pytest.fixture
def spawns(monkeypatch):
    """Every headless run, recorded at the kit adapter; none starts."""
    calls: list[dict] = []
    replies: dict[str, str] = {}

    def _fake(prompt, **kw):
        calls.append({"prompt": prompt, **kw})
        return {"rc": 0, "model": kw.get("model"), "effort": kw.get("effort"),
                "duration_s": 1, "result": replies.get(kw.get("note"), "VERDICT: ACK")}

    monkeypatch.setattr(responder.lw_headless_env, "spawn", _fake)
    _fake.calls, _fake.replies = calls, replies
    return _fake


def _tick(tmp_path: Path, inbox: Path) -> dict:
    import io
    from contextlib import redirect_stdout
    buf = io.StringIO()
    with redirect_stdout(buf):
        assert responder.main(["--once", "--inbox", str(inbox),
                               "--state", str(tmp_path / "seen.json"),
                               "--runlog", str(tmp_path / "runs.jsonl")]) == 0
    return json.loads(buf.getvalue())


@pytest.fixture
def inbox(tmp_path, spawns):
    box = tmp_path / "moon_sync_inbox"
    box.mkdir()
    (box / "2026-10-01-0001-from-RC-FYI-baseline.md").write_text("old", encoding="utf-8")
    assert _tick(tmp_path, box)["cold_start"] is True
    assert spawns.calls == []
    return box


def _write(inbox: Path, name: str, body: str = "body\n") -> Path:
    p = inbox / name
    p.write_text(body, encoding="utf-8")
    return p


def _fleet_root() -> Path:
    return Path(responder.lw_headless_env.FLEET_ROOT)


# --------------------------------------------------------------------------
# ack class: zero spawns, a ledger line, no note
# --------------------------------------------------------------------------

@pytest.mark.parametrize("name", [
    "2026-10-05-0001-from-RC-ACK-got-it.md",
    "2026-10-05-0002-from-CS-INFORMATION-fyi-numbers.md",
    "2026-10-05-0003-from-SS-ANSWER-to-LW-0250-measured.md",
    "2026-10-05-0004-from-MAIN-RESPONDER-ANSWER-x.md",
])
def test_an_ack_class_note_spawns_nothing_and_is_marked_seen(tmp_path, inbox, spawns, name):
    _write(inbox, name)
    payload = _tick(tmp_path, inbox)
    assert spawns.calls == []
    assert payload["spawned"] == []
    assert [a["note"] for a in payload["acked"]] == [name]
    assert responder.new_notes(inbox, tmp_path / "seen.json") == []
    ledger = [json.loads(ln) for ln in (_fleet_root() / fi.SEEN_REL).read_text(
        encoding="utf-8").splitlines()]
    assert [(d["note"], d["action"]) for d in ledger] == [(name, fi.ACK)]
    rec = json.loads((tmp_path / "runs.jsonl").read_text(encoding="utf-8").splitlines()[-1])
    assert rec["event"] == "cycle" and [a["note"] for a in rec["acked"]] == [name]
    assert not (_fleet_root() / fi.OUTBOUND_REL).exists()


def test_a_note_past_the_hop_limit_is_acked_not_triaged(tmp_path, inbox, spawns):
    name = "2026-10-05-0005-from-RC-QUESTION-about-x.md"
    _write(inbox, name, "# From RC - QUESTION\n\nHOP: 2\n\nwhy?\n")
    payload = _tick(tmp_path, inbox)
    assert spawns.calls == []
    assert [a["note"] for a in payload["acked"]] == [name]


def test_acks_never_consume_the_per_cycle_spawn_cap(tmp_path, inbox, spawns):
    for i in range(responder.MAX_SPAWNS_PER_CYCLE + 2):
        _write(inbox, f"2026-10-05-01{i:02d}-from-RC-ACK-n{i}.md")
    order = "2026-10-05-0200-from-MAIN-ORDER-to-LW-do-x.md"
    _write(inbox, order)
    payload = _tick(tmp_path, inbox)
    assert [c["note"] for c in spawns.calls] == [order]
    assert len(payload["acked"]) == responder.MAX_SPAWNS_PER_CYCLE + 2


# --------------------------------------------------------------------------
# work class: the existing child run, kind="inbox"
# --------------------------------------------------------------------------

@pytest.mark.parametrize("cls", ["ORDER", "FIX", "RULING"])
def test_a_work_note_spawns_the_child_with_kind_inbox(tmp_path, inbox, spawns, cls):
    name = f"2026-10-05-0300-from-RC-{cls}-to-LW-do-x.md"
    _write(inbox, name)
    payload = _tick(tmp_path, inbox)
    (call,) = spawns.calls
    assert call["kind"] == "inbox"
    assert call["note"] == name
    assert call["extra"] == responder.RESPONDER_EXTRA      # the existing escalation path
    assert [(s["note"], s["kind"]) for s in payload["spawned"]] == [(name, "inbox")]
    assert responder.new_notes(inbox, tmp_path / "seen.json") == []


def test_the_child_prompt_carries_the_hop_line_and_the_outbound_cap(tmp_path):
    note = tmp_path / "2026-10-05-0301-from-MAIN-ORDER-to-LW-x.md"
    note.write_text("# From MAIN - ORDER to LW\n\nHOP: 1\n", encoding="utf-8")
    prompt = responder.spawn_prompt(note)
    assert "HOP: 2" in prompt
    assert "--outbound-check" in prompt and "--outbound-record" in prompt
    assert "ORDER, FIX or RULING" in prompt
    prompt.encode("ascii")


def test_a_work_note_at_the_hop_limit_is_still_worked_but_told_not_to_reply(tmp_path):
    note = tmp_path / "2026-10-05-0302-from-RC-ORDER-to-LW-x.md"
    note.write_text("# From RC - ORDER\n\nHOP: 2\n", encoding="utf-8")
    assert fi.classify(note.name, "LW", note.read_text(encoding="utf-8")).action == fi.WORK
    assert "send NO reply note" in responder.spawn_prompt(note)


# --------------------------------------------------------------------------
# triage: exactly one sonnet/low run, kind="triage"
# --------------------------------------------------------------------------

def test_an_unclassified_note_gets_exactly_one_triage_run(tmp_path, inbox, spawns):
    name = "2026-10-05-0400-from-RC-QUESTION-how-many-tests.md"
    _write(inbox, name, "# From RC - QUESTION\n\nhow many tests?\n")
    payload = _tick(tmp_path, inbox)
    (call,) = spawns.calls
    assert call["kind"] == "triage"
    assert call["note"] == name
    for key in ("model", "effort", "timeout"):
        assert call[key] == fi.TRIAGE_SPAWN[key]
    # LW's floors live in hooks: the kit refuses --bare with floors_in_hooks
    # (fleet_headless.check_door), so the one TRIAGE_SPAWN key LW overrides.
    assert call["bare"] is False
    assert call["prompt"] == fi.triage_prompt(name, "# From RC - QUESTION\n\nhow many tests?\n")
    assert not call.get("extra")                 # triage does no work
    assert [(s["note"], s["kind"], s["triage"]) for s in payload["spawned"]] == [
        (name, "triage", "ACK")]
    assert responder.new_notes(inbox, tmp_path / "seen.json") == []
    ledger = (_fleet_root() / fi.SEEN_REL).read_text(encoding="utf-8")
    assert '"verdict": "ACK"' in ledger


def test_a_triage_answer_goes_out_as_one_batched_note_with_a_hop_line(tmp_path, inbox, spawns):
    dest = tmp_path / "rc_inbox"
    dest.mkdir()
    (tmp_path / "carriers.json").write_text(json.dumps({"RC": {"inbox": str(dest)}}),
                                            encoding="utf-8")
    names = ["2026-10-05-0500-from-RC-QUESTION-a.md", "2026-10-05-0501-from-RC-QUESTION-b.md"]
    for n in names:
        _write(inbox, n)
        spawns.replies[n] = f"VERDICT: ANSWER\nanswer for {n}"
    payload = _tick(tmp_path, inbox)
    (out,) = list(dest.iterdir())
    body = out.read_text(encoding="ascii")
    assert "HOP: 2" in body.splitlines()
    assert all(f"## Re {n}" in body for n in names)
    assert "-from-LW-ANSWER-to-RC-" in out.name
    assert (responder.OUTBOX / out.name).read_bytes() == out.read_bytes()
    (sent,) = payload["outbound"]
    assert sent["sent"] is True and sent["reached"] == "1/1" and sent["parts"] == 2
    assert fi.OutboundCap(_fleet_root()).used() == 1


def test_a_triage_answer_with_no_carrier_row_is_logged_not_lost(tmp_path, inbox, spawns):
    name = "2026-10-05-0502-from-CS-QUESTION-a.md"
    _write(inbox, name)
    spawns.replies[name] = "VERDICT: ANSWER\nthe answer"
    payload = _tick(tmp_path, inbox)
    (held,) = payload["outbound"]
    assert held["sent"] is False and "carrier" in held["why"]
    assert held["answers"] == [{"note": name, "text": "the answer"}]
    assert fi.OutboundCap(_fleet_root()).used() == 0


# --------------------------------------------------------------------------
# outbound cap: 6 a day, ORDER / FIX / RULING exempt
# --------------------------------------------------------------------------

def _spend_cap(n: int = fi.OUTBOUND_CAP) -> None:
    cap = fi.OutboundCap(_fleet_root())
    for i in range(n):
        assert cap.record(f"spent-{i}.md", "ANSWER", "RC") is not None


def test_cap_exhaustion_blocks_a_seventh_non_exempt_note(tmp_path, inbox, spawns):
    _spend_cap()
    dest = tmp_path / "rc_inbox"
    dest.mkdir()
    (tmp_path / "carriers.json").write_text(json.dumps({"RC": {"inbox": str(dest)}}),
                                            encoding="utf-8")
    name = "2026-10-05-0600-from-RC-QUESTION-seventh.md"
    _write(inbox, name)
    spawns.replies[name] = "VERDICT: ANSWER\nwould be the seventh"
    payload = _tick(tmp_path, inbox)
    assert list(dest.iterdir()) == []
    (held,) = payload["outbound"]
    assert held["sent"] is False and "cap" in held["why"]
    assert fi.OutboundCap(_fleet_root()).used() == fi.OUTBOUND_CAP


def test_the_outbound_cli_refuses_the_seventh_and_exempts_orders(capsys):
    _spend_cap()
    assert responder.main(["--outbound-check", "ANSWER"]) == 1
    assert json.loads(capsys.readouterr().out)["allow"] is False
    assert responder.main(["--outbound-check", "ORDER"]) == 0
    assert json.loads(capsys.readouterr().out)["allow"] is True


def test_the_outbound_cli_records_a_note(capsys):
    assert responder.main(["--outbound-record", "x.md", "ANSWER", "MAIN"]) == 0
    capsys.readouterr()
    assert fi.OutboundCap(_fleet_root()).used() == 1
