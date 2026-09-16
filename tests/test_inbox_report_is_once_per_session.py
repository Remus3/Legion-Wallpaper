"""Charter clause 4: each unread entry is SHOWN at most once per session id.

The sibling of `test_inbox_report_is_idempotent.py`, and deliberately its
opposite number. That file pins "reporting must not CONSUME the queue" - the
unread SET is identical on every fire. This file pins "reporting must not
REPEAT itself" - the same session must not be handed the same names again on
every operator message. Both properties have to hold at once, and the pair is
the only thing that says so: satisfying either one alone is trivial and wrong.
Delete the report record and the first passes while a watcher screams the same
block forty times a session; suppress on the seen set and the second passes
while the queue silently empties.

The three facts asserted here, in the order the prompt states them:

  1. three prompts inside ONE session id: the first prints the mail, the second
     and third print NOTHING;
  2. `mark_inbox_seen()` after those three prompts acknowledges ALL THREE notes
     - not the last fire's delta, which is empty, which is the defect a
     per-fire report record would have introduced the moment suppression
     landed. This is the load-bearing half: suppression and the ack scope are
     coupled, and getting suppression right while leaving the record a delta
     converts a noisy watcher into a silent one that acknowledges nothing;
  3. a DIFFERENT session id prints the mail again. Suppression is per session,
     never a global watermark - the failure class this whole channel keeps
     re-learning.

Plus the guards that stop this file going green for the wrong reason: a note
arriving mid-session is shown even though the session is already suppressed, a
missing session id fails OPEN (prints every time, suppresses nothing), and the
suppression record is a SEPARATE file from the report record.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import lw_facts as F  # noqa: E402

SID = "sess-0000-aaaa-1111"
OTHER_SID = "sess-9999-bbbb-2222"


@pytest.fixture
def inbox(tmp_path: Path) -> Path:
    d = tmp_path / "moon_sync_inbox"
    d.mkdir()
    (d / "2026-09-15-0100-from-RC-first.md").write_text("one\n", encoding="utf-8")
    (d / "2026-09-15-0200-from-CS-second.md").write_text("two\n", encoding="utf-8")
    (d / "2026-09-15-0300-from-LL-third.md").write_text("three\n", encoding="utf-8")
    return d


@pytest.fixture
def state(tmp_path: Path) -> tuple[Path, Path, Path]:
    """Empty seen set and report record; no suppression record at all yet."""
    seen = tmp_path / "sync_inbox_seen.json"
    reported = tmp_path / "sync_inbox_reported.json"
    shown = tmp_path / "sync_inbox_shown.json"
    seen.write_text(json.dumps({"seen": []}), encoding="utf-8")
    reported.write_text(json.dumps({"reported": []}), encoding="utf-8")
    return seen, reported, shown


def _prompt(inbox: Path, state: tuple[Path, Path, Path],
            sid: str | None) -> tuple[list[str], bool]:
    """One UserPromptSubmit fire. Returns (lines, did_it_print).

    Mirrors `main()`'s `--inbox-only` arm exactly: report, decide on `ctx`,
    then commit the suppression state AFTER the notional flush.
    """
    seen, reported, shown = state
    anomalies: list[str] = []
    ctx: dict = {}
    lines = F._inbox_lines(anomalies, inbox=inbox, seen_path=seen,
                           reported_path=reported, sid=sid,
                           shown_path=shown, ctx=ctx)
    F._commit_shown(ctx, sid, shown_path=shown)
    return lines, bool(ctx.get("new"))


def test_the_fixture_actually_has_three_unread_notes(inbox, state):
    """Guard the guard: an empty inbox passes every silence assertion below."""
    lines, printed = _prompt(inbox, state, SID)
    assert printed, lines
    assert any("3 UNREAD" in ln for ln in lines), lines


def test_the_second_and_third_prompt_of_a_session_print_nothing(inbox, state):
    """Fact 1. The names are shown once; the session is not told again."""
    first_lines, first_printed = _prompt(inbox, state, SID)
    assert first_printed, first_lines
    for n in (2, 3):
        lines, printed = _prompt(inbox, state, SID)
        assert not printed, f"prompt {n} printed again:\n  " + "\n  ".join(lines)


def test_mark_inbox_seen_after_three_prompts_acknowledges_all_three(inbox, state):
    """Fact 2, and the reason the report record must be cumulative.

    The third fire's delta is EMPTY. An ack scoped to that delta would mark
    nothing, and the operator - who has read all three notes - would be handed
    the same three again next session with no way to clear them.
    """
    seen, reported, shown = state
    for _ in range(3):
        _prompt(inbox, state, SID)

    n = F.mark_inbox_seen(inbox=inbox, seen_path=seen, reported_path=reported)
    assert n == 3, f"ack marked {n} of 3; report record was {reported.read_text()}"

    acked = {F._stable_name(k) for k in F._seen_names(seen)}
    assert acked == {
        "2026-09-15-0100-from-RC-first.md",
        "2026-09-15-0200-from-CS-second.md",
        "2026-09-15-0300-from-LL-third.md",
    }, acked

    # And the queue is now genuinely clear, in a fresh session.
    lines, printed = _prompt(inbox, state, OTHER_SID)
    assert not printed, lines
    assert any("0 unread" in ln for ln in lines), lines


def test_a_different_session_is_shown_the_mail_again(inbox, state):
    """Fact 3. Suppression is per session id, never a global watermark."""
    _prompt(inbox, state, SID)
    lines, printed = _prompt(inbox, state, OTHER_SID)
    assert printed, "a new session was silently suppressed"
    assert any("3 UNREAD" in ln for ln in lines), lines


def test_a_note_arriving_mid_session_is_still_shown(inbox, state):
    """Suppression is per ENTRY, not a per-session mute on the whole watcher.

    This is the common case on this channel, not an edge one - SessionStart
    fires once, so mail that lands while a session is live has only the
    per-prompt path to arrive on.
    """
    _prompt(inbox, state, SID)
    (inbox / "2026-09-15-0400-from-RSC-fourth.md").write_text("four\n",
                                                              encoding="utf-8")
    lines, printed = _prompt(inbox, state, SID)
    assert printed, "a note that arrived mid-session was suppressed"
    listed = [ln for ln in lines if ln.startswith("  - ")]
    assert len(listed) == 1, listed
    assert "fourth" in listed[0], listed


def test_an_edited_note_is_shown_again_in_the_same_session(inbox, state):
    """The key carries a content digest, so an EDIT moves it. A rewrite in
    place is exactly the case a name-keyed suppression store would hide."""
    _prompt(inbox, state, SID)
    (inbox / "2026-09-15-0100-from-RC-first.md").write_text("one, corrected\n",
                                                            encoding="utf-8")
    lines, printed = _prompt(inbox, state, SID)
    assert printed, "an edited note was suppressed under its old digest"
    assert any("from-RC-first" in ln for ln in lines), lines


def test_no_session_id_fails_open_and_prints_every_time(inbox, state):
    """Clause 4: no session id means print and write nothing.

    Failing CLOSED here would be the worst available outcome - a watcher that
    goes quiet precisely when it cannot tell which session it is in.
    """
    _seen, _reported, shown = state
    for n in range(3):
        lines, printed = _prompt(inbox, state, None)
        assert printed, f"fire {n} without a session id went silent: {lines}"
    assert not shown.exists(), \
        "a fire with no session id wrote suppression state anyway"


def test_the_suppression_store_is_not_the_report_record(inbox, state):
    """They are separate files on purpose: `mark_inbox_seen()` PRUNES the
    report record, and a prune that also cleared suppression would make an
    acknowledgement re-print everything it had just acknowledged."""
    seen, reported, shown = state
    _prompt(inbox, state, SID)
    assert shown.exists() and reported.exists()
    assert shown != reported
    assert F._shown_path().name == "sync_inbox_shown.json"
    assert F._shown_path() != F._reported_path()

    F.mark_inbox_seen(inbox=inbox, seen_path=seen, reported_path=reported)
    lines, printed = _prompt(inbox, state, SID)
    assert not printed, (
        "acknowledging inside a session un-suppressed the session:\n  "
        + "\n  ".join(lines))


def test_the_report_record_carries_the_session_it_belongs_to(inbox, state):
    """Cumulation is scoped by session id, so the id has to be ON the record.
    Without it the union would have no way to know when to start over."""
    _seen, reported, _shown = state
    _prompt(inbox, state, SID)
    doc = json.loads(reported.read_text(encoding="utf-8"))
    assert doc["sid"] == SID, doc


def test_a_new_session_starts_the_report_scope_over(inbox, state):
    """Cumulative WITHIN a session, never across. Carrying the scope forward
    would let an ack acknowledge mail shown to a session nobody read."""
    seen, reported, shown = state
    _prompt(inbox, state, SID)
    # A new session, and this time only one note is still on disk.
    (inbox / "2026-09-15-0200-from-CS-second.md").unlink()
    (inbox / "2026-09-15-0300-from-LL-third.md").unlink()
    _prompt(inbox, state, OTHER_SID)
    n = F.mark_inbox_seen(inbox=inbox, seen_path=seen, reported_path=reported)
    assert n == 1, f"ack marked {n}; record was {reported.read_text()}"
    assert shown.exists()
