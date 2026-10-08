"""The responder must never spawn on LW's OWN notes or on a TERMINAL note.

MEASURED 2026-10-03 from `ops/runtime/inbox_responder/runs.jsonl` (MAIN 0640,
digest-verified against MAIN's outbox):

    11:26:59Z  spawned on  2026-10-03-0700-from-LW-LANDED-C4-...      LW's own note
    11:36:59Z  spawned on  2026-10-03-0634-from-LW-RESPONDER-ACK-...
                           -TERMINAL-no-reply.md                       LW's own ack

An attended session wrote a record into LW's own inbox, the responder spawned
on it, that run acked it into the same inbox, and the responder spawned AGAIN
on the ack - a note whose own filename says TERMINAL no-reply. Each spawn is a
full headless session. The loop was held back only by the child's judgement,
which is not a gate.

TWO RULES, both checked in the PARENT before any spawn, both marking the note
seen and logging the skip:
  * SELF - sender code LW. LW's notes in LW's inbox are records, not mail.
  * TERMINAL - the filename carries a `terminal` or `no-reply` token, or the
    title line says TERMINAL or no reply, from any sender.

THE RULE IS THE KIT'S: `should_skip(name, "LW", head)`. Since FLEET KIT v4
(MAIN 1204, defect 2) TERMINAL means a WHOLE TERMINAL / NOREPLY / NO-REPLY
token in the name, or a head line that is ONLY such a marker; a sentence that
mentions the rule is not a marker, and ORDER / FIX / RULING notes are never
damped. v4 closed LW's reported gap (a bare `noreply` token is terminal again,
so its strict-xfail pin is removed) and narrowed v3's substring rule: a title
SENTENCE saying "terminal" or "no reply" no longer skips. That narrowing is
MAIN's rule and is pinned below as a v4 trade-off: a false spawn on a
non-LW ack costs one budgeted run, and LW's own notes are still caught by SELF.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import lw_inbox_responder as responder  # noqa: E402

# The two LW notes the responder actually spawned on, and LL's terminal receipt
# it spawned on the cycle before. Filenames verbatim from the live run log.
LW_LANDED = ("2026-10-03-0700-from-LW-LANDED-C4-290cbf80-LW-wrote-first-suite-GREEN-"
             "three-own-disk-attestations-and-LWs-diff-header-defect-owned.md")
LW_ACK = ("2026-10-03-0634-from-LW-RESPONDER-ACK-LW-0700-self-note-A1-digest-matches-"
          "A2-tip-fe71425-exit-1-3340-passed-19-skipped-1-failed-TERMINAL-no-reply.md")
LL_TERMINAL = ("2026-10-03-0126-from-LL-ANSWER-LW-0117-received-both-claims-re-measured-"
               "and-match-nothing-owed-terminal.md")
MAIN_FIX = ("2026-10-03-0640-from-MAIN-FIX-to-LW-your-responder-spawns-on-LWs-OWN-notes-"
            "including-a-TERMINAL-no-reply-ack-skip-self-and-terminal.md")


@pytest.fixture(autouse=True)
def _live_state_is_never_touched(monkeypatch, tmp_path):
    """Same isolation as the sibling responder files: the live kill switch is
    never read and the live run log is never written."""
    monkeypatch.setattr(responder, "HALT_PATH", tmp_path / "never-created-HALT")
    # Guarded at the writer, not by mtime: the ARMED responder appends to the
    # live file every few minutes (see test_inbox_responder.py).
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
    """Every note the cycle tried to spawn on. Never a real process."""
    calls: list[str] = []

    def _fake(path, dry_run=False, kind="inbox"):
        calls.append(Path(path).name)
        return responder._auto("spawn", "fake pid")

    monkeypatch.setattr(responder, "spawn", _fake)
    return calls


def _write(inbox: Path, name: str, body: str | None = None) -> None:
    # The default title must NOT echo the filename: it once did, and the title
    # rule then caught every filename marker, so a mutant that disabled the
    # filename rule outright went green (measured 2026-10-03).
    inbox.mkdir(exist_ok=True)
    text = body if body is not None else "# From RC - FYI\n\nbody\n"
    (inbox / name).write_text(text, encoding="utf-8")


def _run(tmp_path: Path, inbox: Path, *extra: str) -> dict:
    responder.main([
        "--once",
        "--inbox", str(inbox),
        "--state", str(tmp_path / "seen.json"),
        "--halt", str(tmp_path / "HALT"),
        "--runlog", str(tmp_path / "runs.jsonl"),
        *extra,
    ])
    log = tmp_path / "runs.jsonl"
    lines = log.read_text(encoding="utf-8").splitlines() if log.exists() else []
    return json.loads(lines[-1]) if lines else {}


@pytest.fixture
def inbox(tmp_path, spawns):
    """An inbox past its cold start, so the next cycle is an ordinary one."""
    box = tmp_path / "moon_sync_inbox"
    _write(box, "2026-10-01-0001-from-RC-FYI-baseline.md")
    _run(tmp_path, box)
    (tmp_path / "runs.jsonl").unlink(missing_ok=True)
    spawns.clear()
    return box


def _seen(tmp_path: Path) -> set[str]:
    data = json.loads((tmp_path / "seen.json").read_text(encoding="utf-8"))
    return {k.split("#")[0] for k in data["seen"]}


# --------------------------------------------------------------------------
# The two measured holes, replayed with the live filenames
# --------------------------------------------------------------------------

@pytest.mark.parametrize("name", [LW_LANDED, LW_ACK])
def test_lws_own_note_produces_zero_spawns(tmp_path, inbox, spawns, name):
    _write(inbox, name, f"# From LW - record\n\n{name}\n")

    record = _run(tmp_path, inbox)

    assert spawns == []
    assert name in _seen(tmp_path), "a skipped note must be marked seen, or it re-fires"
    (skip,) = record["skipped"]
    assert skip["note"] == name
    assert skip["reason"].startswith("self")


@pytest.mark.parametrize("name", [LL_TERMINAL,
                                  "2026-10-03-0900-from-RC-ANSWER-closed-TERMINAL.md",
                                  "2026-10-03-0901-from-CS-ACK-received-no-reply.md",
                                  "2026-10-03-0902-from-SS-ACK-received-noreply.md"])
def test_a_terminal_filename_produces_zero_spawns_from_any_sender(tmp_path, inbox, spawns, name):
    _write(inbox, name)

    record = _run(tmp_path, inbox)

    assert spawns == []
    assert name in _seen(tmp_path)
    (skip,) = record["skipped"]
    assert skip["reason"].startswith("terminal")


@pytest.mark.parametrize("marker", [
    "TERMINAL",
    "## TERMINAL - no reply",
    "**NO-REPLY.**",
])
def test_a_marker_only_head_line_produces_zero_spawns(tmp_path, inbox, spawns, marker):
    """The header half of MAIN's v4 rule: the filename is clean, a head line is
    ONLY a terminal marker."""
    name = "2026-10-03-0910-from-RC-ACK-received.md"
    _write(inbox, name, f"# From RC - ACK: received\n\n{marker}\n\nbody\n")

    record = _run(tmp_path, inbox)

    assert spawns == []
    assert record["skipped"][0]["reason"].startswith("terminal")


@pytest.mark.parametrize("title", [
    "# From LL - ANSWER to LW 0117: nothing owed. TERMINAL - no reply wanted.",
    "# From RC - ACK: received, terminal",
    "# From CS - ACK: received. No reply.",
])
def test_a_title_sentence_mentioning_terminal_is_acked_not_skipped(tmp_path, inbox, spawns,
                                                                    title):
    """PINNED v4 TRADE-OFF (MAIN 1204 defect 2): a sentence is not a marker, so
    these are still NOT skipped as terminal. CHANGED ON PURPOSE by FLEET-KIT v8
    item 14 (MAIN 0310): the note's class is ACK, and an ACK-family note gets a
    mechanical ack (marked seen + kit ledger line), never a spawn - "never
    answer an answer". Under v4 alone these spawned."""
    name = "2026-10-03-0910-from-RC-ACK-received.md"
    _write(inbox, name, f"{title}\n\nbody\n")

    record = _run(tmp_path, inbox)

    assert spawns == []
    assert record["skipped"] == []
    assert [a["note"] for a in record["acked"]] == [name]


def test_the_three_live_notes_together_spawn_nothing(tmp_path, inbox, spawns):
    """The exact cycle shape that ran: LW record, LW ack, LL terminal receipt."""
    for name in (LW_LANDED, LW_ACK, LL_TERMINAL):
        _write(inbox, name)

    record = _run(tmp_path, inbox)

    assert spawns == []
    assert len(record["skipped"]) == 3
    assert record["spawned"] == []


# --------------------------------------------------------------------------
# Mirror arms - the gate must still let ordinary mail through
# --------------------------------------------------------------------------

def test_an_ordinary_sibling_note_still_spawns(tmp_path, inbox, spawns):
    name = "2026-10-03-0920-from-RC-REVIEW-please-measure.md"
    _write(inbox, name)

    record = _run(tmp_path, inbox)

    assert spawns == [name]
    assert record["skipped"] == []


def test_skips_never_consume_the_per_cycle_spawn_cap(tmp_path, inbox, spawns):
    """A burst of self and terminal notes must not starve real mail of its slots."""
    for i in range(responder.MAX_SPAWNS_PER_CYCLE):
        _write(inbox, f"2026-10-03-093{i}-from-LW-record-{i}.md")
    real = [f"2026-10-03-094{i}-from-RC-REVIEW-ask-{i}.md"
            for i in range(responder.MAX_SPAWNS_PER_CYCLE)]
    for name in real:
        _write(inbox, name)

    record = _run(tmp_path, inbox)

    assert sorted(spawns) == sorted(real)
    assert record["deferred"] == 0
    assert len(record["skipped"]) == responder.MAX_SPAWNS_PER_CYCLE


@pytest.mark.parametrize("name,body", [
    # A sender code that merely starts with LW is not LW.
    ("2026-10-03-0953-from-LWX-REVIEW-ask.md", None),
    ("2026-10-03-0954-from-RC-REVIEW-ordinary.md", "# From RC - REVIEW\n\nplease measure\n"),
])
def test_lookalikes_the_kit_still_lets_through(tmp_path, inbox, spawns, name, body):
    _write(inbox, name, body)

    _run(tmp_path, inbox)

    assert spawns == [name]


@pytest.mark.parametrize("name,body", [
    ("2026-10-03-0950-from-RC-FYI-tally.md",
     "# From RC - FYI: tally\n\nanswered: n/a (FYI, no reply requested)\n"),
    ("2026-10-03-0951-from-CS-REVIEW-the-terminals-list.md", None),
    ("2026-10-03-0952-from-SS-REVIEW-terminally-slow-suite.md", None),
])
def test_the_kits_whole_token_rule_lets_lookalikes_through(
        tmp_path, inbox, spawns, name, body):
    """Kit v4 (MAIN 1204 defect 2): whole tokens and marker-only lines. These
    skipped under v3's substring rule; they are ordinary mail again."""
    _write(inbox, name, body)

    record = _run(tmp_path, inbox)

    assert spawns == [name]
    assert record["skipped"] == []


def test_a_note_mentioning_LW_after_another_sender_is_not_self(tmp_path, inbox, spawns):
    """`from-RC-...-to-LW` is RC's mail TO LW - the first sender code wins."""
    name = "2026-10-03-0960-from-RC-FIX-to-LW-from-LW-quoted.md"
    _write(inbox, name)

    _run(tmp_path, inbox)

    assert spawns == [name]


def test_mains_own_fix_note_is_never_damped(tmp_path, inbox, spawns):
    """Under kit v3 this was a pinned false skip: MAIN 0640's own filename
    carries `TERMINAL-no-reply`, so the rule MAIN wrote caught the note that
    wrote it. Kit v4 (MAIN 1204 defect 2) never damps ORDER / FIX / RULING, so
    the FIX note spawns despite the marker token."""
    _write(inbox, MAIN_FIX, "# From MAIN - FIX to LW: an ack marked TERMINAL no-reply\n")

    record = _run(tmp_path, inbox)

    assert spawns == [MAIN_FIX]
    assert record["skipped"] == []


def test_a_dry_run_reports_skips_and_records_nothing(tmp_path, inbox, spawns):
    _write(inbox, LW_ACK)
    before = (tmp_path / "seen.json").read_bytes()

    responder.main(["--once", "--dry-run", "--inbox", str(inbox),
                    "--state", str(tmp_path / "seen.json"),
                    "--halt", str(tmp_path / "HALT"),
                    "--runlog", str(tmp_path / "runs.jsonl")])

    assert spawns == []
    assert (tmp_path / "seen.json").read_bytes() == before
    assert not (tmp_path / "runs.jsonl").exists()


def test_an_unreadable_note_falls_back_to_the_filename(tmp_path):
    """COULD-NOT-READ is not CLEAN: the filename rules still decide, and a
    missing file never raises out of the gate."""
    assert responder.skip_reason(tmp_path / LW_ACK).startswith("self")
    assert responder.skip_reason(tmp_path / "2026-10-03-0970-from-RC-x.md") is None
