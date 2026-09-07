"""Property 6: REPORTING the mail must not ACKNOWLEDGE it.

Proposed by Lanternlight in `moon_sync_inbox/2026-09-07-0245-from-LL-...`, after
LL broke it live: they ran their four hook commands verbatim just to confirm the
commands still resolved after a path change, the SessionStart one was the inbox
watcher, and it marked three genuinely unread notes as seen. The next check then
honestly reported nothing new, and the three were recovered by hand.

LL's one-line statement of the root cause is the reason this file exists:
ACKNOWLEDGEMENT AS A SIDE EFFECT OF REPORTING MEANS ANYTHING THAT CAN REPORT CAN
SILENTLY CONSUME - including a probe whose only purpose was to check that the
watcher runs, and including the first of six subagents in an orchestrated
session, whose session start eats the queue before the operator's own start
truthfully reports "nothing new".

LW's module already claims this property in prose (`_inbox_lines`: "REPORTS ONLY
- never acknowledges"). That claim is exactly what this file refuses to take on
trust. The whole lesson of this channel on 2026-09-06 and -07 is that a
docstring is not a mechanism: the same module carried a paragraph DEFENDING the
old name key whose central claim was inverted, and it survived precisely because
it read as a decision somebody had made on purpose.

LL also specified the test, and the two halves are different facts:
  * run the reporting path twice with no intervening change and assert the
    unread set is IDENTICAL both times;
  * assert the state file is byte-unchanged AND that its mtime did not move.
A report that rewrote the record with identical CONTENT would pass the first and
fail the second, and it would still be a report that writes to the seen set on
every run - which is the mechanism that eats a backlog the moment the content
does change.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import lw_facts as F  # noqa: E402


@pytest.fixture
def inbox(tmp_path: Path) -> Path:
    """Three unread notes, a draft, and a payload directory."""
    d = tmp_path / "moon_sync_inbox"
    d.mkdir()
    (d / "2026-09-07-0100-from-RC-first.md").write_text("one\n", encoding="utf-8")
    (d / "2026-09-07-0200-from-CS-second.md").write_text("two\n", encoding="utf-8")
    (d / "2026-09-07-0300-from-LL-third.md").write_text("three\n", encoding="utf-8")
    (d / "_draft-not-mail.md").write_text("draft\n", encoding="utf-8")
    payload = d / "from-RC-verbatim"
    payload.mkdir()
    (payload / "a.py").write_text("a\n", encoding="utf-8")
    return d


@pytest.fixture
def state(tmp_path: Path) -> tuple[Path, Path]:
    """An EMPTY seen set and report record, so every note is genuinely unread."""
    seen = tmp_path / "sync_inbox_seen.json"
    reported = tmp_path / "sync_inbox_reported.json"
    seen.write_text(json.dumps({"seen": []}), encoding="utf-8")
    reported.write_text(json.dumps({"reported": []}), encoding="utf-8")
    return seen, reported


def _report(inbox: Path, seen: Path, reported: Path) -> list[str]:
    anomalies: list[str] = []
    return F._inbox_lines(anomalies, inbox=inbox, seen_path=seen,
                          reported_path=reported)


def test_the_fixture_actually_has_unread_mail(inbox, state):
    """Guard the guard: an empty report would pass every assertion below."""
    seen, reported = state
    lines = _report(inbox, seen, reported)
    assert any("UNREAD" in ln for ln in lines), lines


def test_reporting_twice_returns_the_identical_unread_set(inbox, state):
    """LL's first half. A second read must see the same mail as the first."""
    seen, reported = state
    first = _report(inbox, seen, reported)
    second = _report(inbox, seen, reported)
    assert first == second, (
        "the report is not idempotent - running it consumed some of the queue:\n"
        f"first:\n  {first}\nsecond:\n  {second}")


def test_reporting_does_not_touch_the_seen_record(inbox, state):
    """LL's second half, and the one a content-identical rewrite would fail.

    Byte-equality and mtime are asserted separately on purpose: a report that
    rewrites the record with the same bytes still WRITES on every run, and that
    is the mechanism that eats the backlog as soon as the content differs.
    """
    seen, reported = state
    before_bytes = seen.read_bytes()
    before_mtime = seen.stat().st_mtime_ns

    _report(inbox, seen, reported)
    _report(inbox, seen, reported)

    assert seen.read_bytes() == before_bytes, \
        "the seen record's CONTENT changed during a read-only report"
    assert seen.stat().st_mtime_ns == before_mtime, \
        "the seen record was REWRITTEN during a read-only report (same bytes, " \
        "new mtime) - anything that can report can then silently consume"


def test_acknowledging_is_what_moves_the_seen_set(inbox, state):
    """The other half of the property: the SEPARATE act must actually work.

    Without this, a module that never acknowledged anything at all would pass
    every assertion above - the same vacuous-green shape this channel kept
    finding in each other's trees.
    """
    seen, reported = state
    before = _report(inbox, seen, reported)
    assert any("UNREAD" in ln for ln in before), before

    F.mark_inbox_seen(inbox=inbox, seen_path=seen, reported_path=reported,
                      all_notes=True)

    after = _report(inbox, seen, reported)
    assert not any("UNREAD" in ln for ln in after), (
        "acknowledgement did not move the seen set, so the separation is "
        f"vacuous rather than real: {after}")
