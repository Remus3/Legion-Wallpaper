"""An unreadable inbox must never be mistaken for an empty one.

Provenance: CS found the shape (finding six of REVIEW 1c0be827c496) and said it
could not manufacture a real permission denial. RSC manufactured one and
reported on 2026-09-16 that it reproduces in their tree as THREE defects, not
one, because every caller of their entry enumerator got "empty" for
"unreadable":

  1. a clean "nothing unread" line printed over live notes,
  2. every held key derived as RETRACTED, fabricating withdrawals - and a
     withdrawal is the one inbox event with no on-disk artifact left to check
     it against,
  3. the acknowledge path REWROTE the seen store to an empty object while
     printing that it had marked notes read.

The third cannot be recovered from: a blind read is survivable, a blind read
that WRITES is not.

LW measured all three against its own code on 2026-09-16 using a REAL deny ACE
and has none of them: `_inbox_entries` RAISES rather than returning empty, so
`mark_inbox_seen` aborts with the record untouched, and the report path's own
catch degrades to "probe failed" with `commit=False` so nothing is suppressed.

These arms exist so that stays true. The failure they forbid is a future
"robustness" change wrapping the enumerator in `except OSError: return []` -
which would look like an improvement and would install all three defects at
once.

WHY THE FAULT IS INJECTED RATHER THAN APPLIED WITH icacls, stated because the
first version of this module did use a real deny ACE and had to be withdrawn:
a deny ACE is host- and location-dependent. Measured here - the same
`icacls /deny` that a scratch directory honoured was applied successfully
(rc 0) to a `tempfile.mkdtemp()` directory and NOT honoured, in the parent
process or in a fresh child. An arm built on it skipped every run. A test that
always skips asserts nothing, which is precisely the defect class this round
is about, so the real-ACL measurement stays a one-off recorded in LEDGER 210
and the standing arms inject the fault at the boundary instead. That also
makes them run on Linux CI, where LW's suite actually gates.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))

import lw_facts  # noqa: E402

WATERMARK = "PRECIOUS-WATERMARK-DO-NOT-ERASE"


@pytest.fixture
def unreadable_inbox(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A real directory holding a real note, whose LISTING raises.

    The note is real so that an arm cannot pass by there being nothing to
    miss - the whole defect is reporting "empty" while live mail sits there.
    """
    inbox = tmp_path / "moon_sync_inbox"
    inbox.mkdir()
    (inbox / "2026-09-16-0001-from-RC-FYI-live-note.md").write_text(
        "# From RC - FYI: a live note that must not be read as absent\n",
        encoding="utf-8")

    real_iterdir = Path.iterdir

    def deny(self: Path):
        if self == inbox:
            raise PermissionError(13, "Access is denied", str(self))
        return real_iterdir(self)

    monkeypatch.setattr(Path, "iterdir", deny)
    return inbox


def test_the_fixture_actually_denies_and_the_note_is_really_there(
        unreadable_inbox: Path) -> None:
    """Guard the guard: prove the fault took, and that it is not just an empty dir.

    RSC's portability lesson, generalised - an arm that grades a fault which
    never happened passes for the wrong reason.
    """
    assert unreadable_inbox.is_dir(), "the inbox must still LOOK present"
    with pytest.raises(PermissionError):
        list(unreadable_inbox.iterdir())
    # and the note really exists, read by a path the fault does not cover
    assert (unreadable_inbox / "2026-09-16-0001-from-RC-FYI-live-note.md").is_file()


def test_the_enumerator_raises_rather_than_reporting_empty(
        unreadable_inbox: Path) -> None:
    """The root defect. Everything else in this module follows from it."""
    with pytest.raises(OSError):
        lw_facts._inbox_entries(unreadable_inbox)


def test_acknowledging_an_unreadable_inbox_does_not_touch_the_seen_store(
        unreadable_inbox: Path, tmp_path: Path) -> None:
    """RSC's defect three - the one that destroys durable state."""
    seen = tmp_path / "seen.json"
    reported = tmp_path / "reported.json"
    seen.write_text(json.dumps({"seen": [WATERMARK]}), encoding="utf-8")
    reported.write_text(json.dumps({"reported": [WATERMARK]}), encoding="utf-8")
    before = seen.read_bytes()

    with pytest.raises(OSError):
        lw_facts.mark_inbox_seen(inbox=unreadable_inbox, seen_path=seen,
                                 reported_path=reported)

    assert seen.read_bytes() == before, (
        "the acknowledge path rewrote the seen store while the inbox was "
        "unreadable - destruction of the durable state the watcher exists to "
        "keep, triggered by a permission bit")
    assert WATERMARK in json.loads(seen.read_text(encoding="utf-8"))["seen"]


def test_the_report_degrades_loudly_and_suppresses_nothing(
        unreadable_inbox: Path, tmp_path: Path) -> None:
    """RSC's defects one and two: no clean line, and nothing committed.

    `commit=False` is what stops a crash from narrowing the NEXT fire's output.
    A probe that measured nothing must not mark anything shown.
    """
    seen = tmp_path / "seen.json"
    seen.write_text(json.dumps({"seen": []}), encoding="utf-8")
    reported = tmp_path / "reported.json"
    reported.write_text(json.dumps({"reported": []}), encoding="utf-8")
    shown = tmp_path / "shown.json"
    anomalies: list[str] = []
    ctx: dict = {}

    lines = lw_facts._inbox_lines(
        anomalies, inbox=unreadable_inbox, seen_path=seen,
        reported_path=reported, sid="test-session", shown_path=shown, ctx=ctx)

    blob = " ".join(lines).lower()
    assert "probe failed" in blob, f"the report did not say it failed: {lines}"
    assert "unread: none" not in blob and "0 unread" not in blob, (
        f"the report printed a clean line over a live note: {lines}")
    assert anomalies, "a crashed probe recorded no anomaly"
    assert ctx.get("commit") is False, (
        "a probe that measured nothing must not commit its half-built sets - "
        "committing here would suppress notes this run never showed")
    assert ctx.get("new") is True, (
        "a failed probe must not be allowed to read as 'nothing new'")
