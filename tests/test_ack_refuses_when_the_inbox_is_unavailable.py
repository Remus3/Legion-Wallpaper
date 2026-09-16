"""The acknowledge path must REFUSE when it could not see the inbox.

Provenance, and it is a defect LW HAD rather than one LW dodged. RSC split CS's
finding six into three consequences, the worst being an acknowledge path that
rewrites the seen store while printing success. LW measured that against an
UNREADABLE inbox on 2026-09-16, found it does not reproduce - `_inbox_entries`
raises before any write - and told four sibling trees so.

**That measurement was true and the conclusion drawn from it was too wide.**
RC then found the same destruction through a different door: an ABSENT inbox.
LW checked and reproduces it exactly. Measured, before this module existed:

    inbox exists?  False
    BEFORE seen:   ['PRECIOUS-WATERMARK']
    mark_inbox_seen RETURNED 0
    AFTER  seen:   []

Exit 0, a success line, and the watermark gone. The asymmetry RC named is
LW's too: the WATCHER treats an absent inbox as a recorded fault and prints
`absent at ... - no cross-repo mail channel`, while the ACKNOWLEDGE path treats
the identical condition as "no notes" and prunes everything to match. One
condition, two readings, and the DESTRUCTIVE one was the SILENT one.

It is reachable, not theoretical. `moon_sync_inbox/` is gitignored, so it is
absent in a fresh clone, absent in every worktree, and removable by a routine
clean.

**Absent is not empty.** A genuinely EMPTY inbox that LW can see must still
prune - that is the documented design, and it is how an archived note leaves
the record. The defect is treating COULD-NOT-LOOK as SAW-NOTHING.

The refusal probes explicitly rather than relying on an exception propagating
out of the enumerator (RC's design point): a later reader who wraps the
directory iteration in `except OSError: return []` - the exact mutant that
survived all 56 of RC's arms - must not be able to reintroduce the erasure
through the back door. Exit 3, following CS's caution that exit 2 is not
self-evidencing and RC's reasoning that 1 is an uncaught exception and 2 is the
conventional usage code, so neither can be told apart from a module that failed
to parse.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))

import lw_facts  # noqa: E402

WATERMARK = "PRECIOUS-WATERMARK-DO-NOT-ERASE"
REFUSE_CODE = 3


@pytest.fixture
def store(tmp_path: Path) -> tuple[Path, Path]:
    seen = tmp_path / "seen.json"
    reported = tmp_path / "reported.json"
    seen.write_text(json.dumps({"seen": [WATERMARK]}), encoding="utf-8")
    reported.write_text(json.dumps({"reported": [WATERMARK]}), encoding="utf-8")
    return seen, reported


def test_an_absent_inbox_refuses_and_leaves_the_store_byte_identical(
        tmp_path: Path, store: tuple[Path, Path]) -> None:
    """The defect RC found in itself and LW reproduced."""
    seen, reported = store
    before = seen.read_bytes()

    with pytest.raises(lw_facts.InboxUnavailable):
        lw_facts.mark_inbox_seen(inbox=tmp_path / "not_here",
                                 seen_path=seen, reported_path=reported)

    assert seen.read_bytes() == before, (
        "the acknowledge path rewrote the seen store for an inbox it could "
        "not even see - a blind read is recoverable, a blind read that WRITES "
        "is not")


def test_an_unreadable_inbox_refuses_too_and_does_not_rely_on_propagation(
        tmp_path: Path, store: tuple[Path, Path],
        monkeypatch: pytest.MonkeyPatch) -> None:
    """The other door, guarded EXPLICITLY rather than by an absent try/except.

    LW is protected here today by there being no `except OSError` around the
    iteration. That is an absence, and an absence is not a guard: the mutant
    that adds one survived every arm in RC's tree. This asserts the refusal
    happens even when the enumerator is made to swallow the error.
    """
    seen, reported = store
    inbox = tmp_path / "moon_sync_inbox"
    inbox.mkdir()
    (inbox / "2026-09-16-0001-from-RC-FYI-live.md").write_text("x", encoding="utf-8")
    before = seen.read_bytes()

    real_iterdir = Path.iterdir

    def deny(self: Path):
        if self == inbox:
            raise PermissionError(13, "Access is denied", str(self))
        return real_iterdir(self)

    monkeypatch.setattr(Path, "iterdir", deny)

    with pytest.raises((lw_facts.InboxUnavailable, OSError)):
        lw_facts.mark_inbox_seen(inbox=inbox, seen_path=seen,
                                 reported_path=reported)
    assert seen.read_bytes() == before


def test_a_genuinely_empty_inbox_STILL_PRUNES(
        tmp_path: Path, store: tuple[Path, Path]) -> None:
    """Guard the guard: the repair must not turn a real prune into a refusal.

    An empty-but-present inbox is the documented way an archived note leaves
    the record. A refusal here would be a regression wearing the repair's
    clothes, and it is the mutation most likely to be introduced by someone
    "hardening" this later.
    """
    seen, reported = store
    inbox = tmp_path / "moon_sync_inbox"
    inbox.mkdir()

    n = lw_facts.mark_inbox_seen(inbox=inbox, seen_path=seen,
                                 reported_path=reported)

    assert n == 0
    assert json.loads(seen.read_text(encoding="utf-8"))["seen"] == [], (
        "an inbox LW could SEE and that is genuinely empty must still prune")


def test_the_watcher_and_the_acknowledge_path_agree_about_an_absent_inbox(
        tmp_path: Path, store: tuple[Path, Path]) -> None:
    """RC's asymmetry arm, handed to the fleet as a one-minute check.

    Two code paths written at different times read the same condition. Before
    the repair the watcher called it a fault and the acknowledge path called it
    zero notes.
    """
    seen, reported = store
    absent = tmp_path / "not_here"
    anomalies: list[str] = []

    lines = lw_facts._inbox_lines(anomalies, inbox=absent, seen_path=seen,
                                  reported_path=reported, sid="s",
                                  shown_path=tmp_path / "shown.json", ctx={})
    watcher_says_absent = any("absent" in line.lower() for line in lines)

    try:
        lw_facts.mark_inbox_seen(inbox=absent, seen_path=seen,
                                 reported_path=reported)
        ack_says_absent = False
    except lw_facts.InboxUnavailable:
        ack_says_absent = True

    assert watcher_says_absent, f"the watcher no longer reports absence: {lines}"
    assert ack_says_absent is watcher_says_absent, (
        "the watcher and the acknowledge path disagree about an absent inbox - "
        "one condition, two readings, and the destructive one is the silent one")


def test_the_cli_refuses_at_exit_3_and_says_the_store_is_unchanged(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture) -> None:
    """The exit code the operator and any script actually see.

    Exercised through `main()`'s own dispatch rather than by calling
    mark_inbox_seen, because the mapping from the refusal to exit 3 lives in
    the CLI branch and nothing else grades it.
    """
    monkeypatch.setattr(lw_facts, "_inbox_path", lambda: tmp_path / "not_here")
    monkeypatch.setattr(lw_facts, "_seen_path", lambda: tmp_path / "seen.json")
    monkeypatch.setattr(lw_facts, "_reported_path",
                        lambda: tmp_path / "reported.json")
    monkeypatch.setattr(lw_facts, "_log_invocation",
                        lambda *a, **k: None)
    monkeypatch.setattr(sys, "argv", ["lw_facts.py", "--mark-inbox-seen"])

    rc = lw_facts.main()

    err = capsys.readouterr().err
    assert rc == REFUSE_CODE, f"expected exit {REFUSE_CODE}, got {rc}"
    assert "REFUSED" in err, f"the refusal is not announced: {err!r}"
    assert "UNCHANGED" in err, (
        f"the refusal does not say the store survived: {err!r}")
