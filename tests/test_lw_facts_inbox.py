"""Unread cross-repo mail is surfaced at SESSION START, keyed on FILENAMES.

WHY THIS EXISTS (ROADMAP `sync-inbox-visible-at-session-start`): before this,
LW had no watcher on `moon_sync_inbox/` of any kind - measured, not assumed:
`grep -rl moon_sync_inbox tools/ ops/ scripts/ .claude/` returned nothing and
none of the three scheduled tasks touched it. A cross-repo note sat unread
until a human happened to mention it. RC's 22:05 note on 2026-09-06 was seen at
22:20 only because the operator said mail was coming.

The design is the one all five converged on (RC's CONVERGENCE CHARTER v1,
section 1): report from the SessionStart hook. One directory listing, no
daemon, no console flash, and it survives `/clear` BY CONSTRUCTION because a
`/clear` IS a session start.

**Unread is a set of seen FILENAMES, never an mtime watermark.** This is the
load-bearing decision and `test_a_seen_file_with_a_new_mtime_stays_read` plus
`test_an_old_file_never_seen_is_unread` are the pair that pins it. A watermark
advances on WRITE, so a session cleared or killed before anyone read the output
moves it past a note nobody saw, unrecoverably - "unread" was never a property
of the file. A watermark also loses to timestamp-preserving delivery (`cp -p`,
`robocopy /COPY:T`, restore-from-backup) and to clock skew. All three fail as
SILENCE, indistinguishable from "no mail", which is the exact failure class
this channel produced twice on 2026-09-06.

The hook REPORTS and never acknowledges: `test_the_probe_never_writes_the_record`.
An unacknowledged note re-reports next session rather than being lost.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import lw_facts  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


def _inbox(tmp_path, *names):
    box = tmp_path / "moon_sync_inbox"
    box.mkdir(exist_ok=True)
    for n in names:
        (box / n).write_text("body\n", encoding="ascii")
    return box


def _record(tmp_path, names):
    rec = tmp_path / "sync_inbox_seen.json"
    rec.write_text(json.dumps({"seen": list(names)}), encoding="ascii")
    return rec


def _probe(box, rec, anomalies=None):
    return lw_facts._inbox_lines(anomalies if anomalies is not None else [],
                                 inbox=box, seen_path=rec)


def _probe_r(box, rec, rep, anomalies=None):
    """_probe with the report record wired - the ack path depends on it."""
    return lw_facts._inbox_lines(anomalies if anomalies is not None else [],
                                 inbox=box, seen_path=rec, reported_path=rep)


# ---------------------------------------------------------------------------
# 1. the report
# ---------------------------------------------------------------------------
def test_an_unseen_note_is_reported_unread(tmp_path):
    box = _inbox(tmp_path, "2026-09-06-2340-from-RC-charter.md")
    lines = _probe(box, tmp_path / "absent.json")
    text = "\n".join(lines)
    assert "1 UNREAD" in text
    assert "2026-09-06-2340-from-RC-charter.md" in text


def test_everything_seen_reports_no_unread(tmp_path):
    box = _inbox(tmp_path, "a.md", "b.md")
    rec = _record(tmp_path, ["a.md", "b.md"])
    text = "\n".join(_probe(box, rec))
    assert "UNREAD" not in text
    assert "0 unread" in text


def test_underscore_drafts_are_excluded(tmp_path):
    box = _inbox(tmp_path, "_draft-not-sent-yet.md", "real.md")
    text = "\n".join(_probe(box, tmp_path / "absent.json"))
    assert "_draft-not-sent-yet.md" not in text
    assert "1 UNREAD" in text


def test_a_missing_inbox_is_reported_not_crashed(tmp_path):
    anomalies: list[str] = []
    lines = _probe(tmp_path / "nope", tmp_path / "absent.json", anomalies)
    assert lines and "moon_sync_inbox" in lines[0]
    assert anomalies == []


def test_the_listing_is_capped_but_says_how_many_it_hid(tmp_path):
    box = _inbox(tmp_path, *[f"note-{i:02d}.md" for i in range(25)])
    text = "\n".join(_probe(box, tmp_path / "absent.json"))
    assert "25 UNREAD" in text
    assert "more" in text


# ---------------------------------------------------------------------------
# 2. FILENAMES, not a watermark - the pair that pins the decision
# ---------------------------------------------------------------------------
def test_a_seen_file_with_a_new_mtime_stays_read(tmp_path):
    """An mtime watermark would re-report this; a filename set must not."""
    box = _inbox(tmp_path, "seen.md")
    rec = _record(tmp_path, ["seen.md"])
    import os
    import time
    os.utime(box / "seen.md", (time.time() + 10_000, time.time() + 10_000))
    assert "UNREAD" not in "\n".join(_probe(box, rec))


def test_an_old_file_never_seen_is_unread(tmp_path):
    """Timestamp-preserving delivery (cp -p / robocopy /COPY:T / a restore)
    lands a note with an OLD mtime. A watermark loses it in silence."""
    box = _inbox(tmp_path, "delivered-with-old-mtime.md")
    import os
    os.utime(box / "delivered-with-old-mtime.md", (1_000_000, 1_000_000))
    rec = _record(tmp_path, ["something-else.md"])
    assert "1 UNREAD" in "\n".join(_probe(box, rec))


# ---------------------------------------------------------------------------
# 3. report and acknowledge are SEPARATE actions
# ---------------------------------------------------------------------------
def test_the_probe_never_writes_the_record(tmp_path):
    box = _inbox(tmp_path, "unread.md")
    rec = tmp_path / "sync_inbox_seen.json"
    _probe(box, rec)
    assert not rec.exists(), "the hook acknowledged; it must only report"


def test_an_unacknowledged_note_re_reports(tmp_path):
    box = _inbox(tmp_path, "unread.md")
    rec = tmp_path / "sync_inbox_seen.json"
    first = "\n".join(_probe(box, rec))
    second = "\n".join(_probe(box, rec))
    assert "1 UNREAD" in first and "1 UNREAD" in second


def test_acknowledge_rewrites_the_set_from_the_current_listing(tmp_path):
    """Rewrite, not union - so an archived note prunes automatically.

    `reported_path` is injected rather than defaulted: without it this reads the
    REAL ops/runtime record off this machine and passes or fails on whatever the
    last live session happened to be shown.
    """
    box = _inbox(tmp_path, "current.md")
    rec = _record(tmp_path, ["archived-and-gone.md"])
    lw_facts.mark_inbox_seen(inbox=box, seen_path=rec,
                             reported_path=tmp_path / "no-report.json")
    doc = json.loads(rec.read_text(encoding="utf-8"))
    assert set(doc["seen"]) == {"current.md"}
    assert "UNREAD" not in "\n".join(_probe(box, rec))


def test_acknowledge_creates_the_record_when_absent(tmp_path):
    box = _inbox(tmp_path, "a.md")
    rec = tmp_path / "made" / "sync_inbox_seen.json"
    lw_facts.mark_inbox_seen(inbox=box, seen_path=rec,
                             reported_path=tmp_path / "no-report.json")
    assert set(json.loads(rec.read_text(encoding="utf-8"))["seen"]) == {"a.md"}


# ---------------------------------------------------------------------------
# 4. a probe must never break session start
# ---------------------------------------------------------------------------
def test_a_corrupt_record_degrades_to_everything_unread(tmp_path):
    """Fail LOUD, not silent: a broken record must not read as 'no mail'."""
    box = _inbox(tmp_path, "a.md")
    rec = tmp_path / "sync_inbox_seen.json"
    rec.write_text("{not json", encoding="ascii")
    anomalies: list[str] = []
    assert "1 UNREAD" in "\n".join(_probe(box, rec, anomalies))


def test_the_probe_returns_lines_rather_than_raising_on_a_file_as_inbox(tmp_path):
    notafolder = tmp_path / "moon_sync_inbox"
    notafolder.write_text("not a directory\n", encoding="ascii")
    anomalies: list[str] = []
    assert _probe(notafolder, tmp_path / "absent.json", anomalies)


# ---------------------------------------------------------------------------
# 5. the charter's own classification decides what is an ANOMALY
# ---------------------------------------------------------------------------
def test_an_unread_review_or_action_note_raises_an_anomaly(tmp_path):
    box = _inbox(tmp_path, "2026-09-06-2340-from-RC-REVIEW-charter-v2.md")
    anomalies: list[str] = []
    _probe(box, tmp_path / "absent.json", anomalies)
    assert any("REVIEW" in a or "response" in a for a in anomalies)


def test_an_unread_fyi_note_does_not_raise_an_anomaly(tmp_path):
    box = _inbox(tmp_path, "2026-09-06-2310-from-RC-FYI-winmutex-pinned.md")
    anomalies: list[str] = []
    text = "\n".join(_probe(box, tmp_path / "absent.json", anomalies))
    assert "1 UNREAD" in text
    assert anomalies == []


# ---------------------------------------------------------------------------
# 6. wiring: the record is per-machine state and the hook actually emits this
# ---------------------------------------------------------------------------
def test_the_record_lives_in_gitignored_runtime_state():
    rel = lw_facts._SEEN.relative_to(ROOT).as_posix()
    assert rel == "ops/runtime/sync_inbox_seen.json"
    out = subprocess.run(["git", "check-ignore", rel], cwd=str(ROOT),
                         capture_output=True, text=True, timeout=30)
    assert out.returncode == 0, "the seen record must not be tracked"


def test_the_hook_output_carries_the_sync_inbox_section():
    out = subprocess.run([sys.executable, str(ROOT / "tools" / "lw_facts.py")],
                         cwd=str(ROOT), capture_output=True, text=True, timeout=60)
    assert out.returncode == 0, out.stderr
    assert "## Sync inbox" in out.stdout


# ---------------------------------------------------------------------------
# 7. acknowledge only what was REPORTED
#
# MEASURED TWICE, on 2026-09-05 (6 notes) and again on 2026-09-06 (5 notes):
# `--mark-inbox-seen` acknowledged EVERY note in the inbox, including notes that
# landed AFTER the session-start report printed. Those notes were never shown to
# anyone and were marked read anyway - the mtime-watermark defect this design
# replaced, wearing the acknowledgement as a costume instead of the report.
#
# The ritual fix ("ack at session start, not at wrap") does not close it: a note
# that arrives one minute after the report is still in the listing when the ack
# runs. So the mechanism has to carry it. The report now RECORDS what it showed,
# and the acknowledgement marks only that.
# ---------------------------------------------------------------------------
def _reported(tmp_path):
    return tmp_path / "sync_inbox_reported.json"


def test_the_report_records_what_it_showed(tmp_path):
    box = _inbox(tmp_path, "a.md", "b.md")
    rep = _reported(tmp_path)
    _probe_r(box, tmp_path / "absent.json", rep)
    assert set(json.loads(rep.read_text(encoding="utf-8"))["reported"]) == {"a.md", "b.md"}


def test_a_note_that_lands_after_the_report_is_not_acknowledged(tmp_path):
    """THE incident, both times it happened."""
    box = _inbox(tmp_path, "read-me.md")
    rec = tmp_path / "sync_inbox_seen.json"
    rep = _reported(tmp_path)
    _probe_r(box, rec, rep)

    (box / "arrived-mid-session.md").write_text("body\n", encoding="ascii")
    lw_facts.mark_inbox_seen(inbox=box, seen_path=rec, reported_path=rep)

    seen = set(json.loads(rec.read_text(encoding="utf-8"))["seen"])
    assert seen == {"read-me.md"}, "a note nobody was shown was marked read"
    assert "arrived-mid-session.md" in "\n".join(_probe_r(box, rec, rep))


def test_acknowledge_still_prunes_a_note_that_left_the_inbox(tmp_path):
    """Pruning is why the set is rewritten rather than unioned - keep it."""
    box = _inbox(tmp_path, "current.md")
    rec = _record(tmp_path, ["archived-and-gone.md"])
    rep = _reported(tmp_path)
    _probe_r(box, rec, rep)
    lw_facts.mark_inbox_seen(inbox=box, seen_path=rec, reported_path=rep)
    assert set(json.loads(rec.read_text(encoding="utf-8"))["seen"]) == {"current.md"}


def test_an_absent_report_record_falls_back_to_the_current_listing(tmp_path):
    """A tree that has never run the hook still gets a baseline in one command.

    Documented on purpose: this is the ONLY path that marks an unreported note,
    and it exists so the first ack on a fresh tree is not a no-op. Once the hook
    has run once the record exists and the intersection rule applies.
    """
    box = _inbox(tmp_path, "a.md", "b.md")
    rec = tmp_path / "sync_inbox_seen.json"
    n = lw_facts.mark_inbox_seen(inbox=box, seen_path=rec,
                                 reported_path=tmp_path / "never-written.json")
    assert n == 2
    assert set(json.loads(rec.read_text(encoding="utf-8"))["seen"]) == {"a.md", "b.md"}


def test_mark_all_is_the_deliberate_baseline_escape_hatch(tmp_path):
    box = _inbox(tmp_path, "shown.md")
    rec = tmp_path / "sync_inbox_seen.json"
    rep = _reported(tmp_path)
    _probe_r(box, rec, rep)
    (box / "never-shown.md").write_text("body\n", encoding="ascii")
    lw_facts.mark_inbox_seen(inbox=box, seen_path=rec, reported_path=rep, all_notes=True)
    assert set(json.loads(rec.read_text(encoding="utf-8"))["seen"]) == {
        "shown.md", "never-shown.md"}


def test_an_already_seen_note_stays_seen_when_a_new_one_is_reported(tmp_path):
    """The reported set is what the LAST report showed, so union with the old
    seen set - otherwise acking today un-acks everything read yesterday."""
    box = _inbox(tmp_path, "old.md", "new.md")
    rec = _record(tmp_path, ["old.md"])
    rep = _reported(tmp_path)
    _probe_r(box, rec, rep)          # shows only new.md; old.md is already seen
    lw_facts.mark_inbox_seen(inbox=box, seen_path=rec, reported_path=rep)
    assert set(json.loads(rec.read_text(encoding="utf-8"))["seen"]) == {"old.md", "new.md"}


def test_the_report_record_lives_in_gitignored_runtime_state():
    rel = lw_facts._REPORTED.relative_to(ROOT).as_posix()
    assert rel == "ops/runtime/sync_inbox_reported.json"
    out = subprocess.run(["git", "check-ignore", rel], cwd=str(ROOT),
                         capture_output=True, text=True, timeout=30)
    assert out.returncode == 0, "the report record must not be tracked"


def test_writing_the_report_record_cannot_break_session_start(tmp_path):
    """A probe must never take the live-state block down with it."""
    box = _inbox(tmp_path, "a.md")
    unwritable = tmp_path / "as-a-file"
    unwritable.write_text("not a directory\n", encoding="ascii")
    anomalies: list[str] = []
    lines = lw_facts._inbox_lines(anomalies, inbox=box,
                                  seen_path=tmp_path / "absent.json",
                                  reported_path=unwritable / "nested" / "rep.json")
    assert "1 UNREAD" in "\n".join(lines)


# ---------------------------------------------------------------------------
# 8. the inbox is more than top-level .md
#
# MEASURED 2026-09-07, on RC's tree first and then on this one: the watcher
# globbed top-level `*.md` only, so a payload DIRECTORY was invisible. RC
# invented the `from-<CODE>-verbatim/` convention, asked four repos to
# reciprocate in it, and shipped a watcher that could not see it - it reported
# zero of 70 files CS sent. LW had `from-RSC-verbatim/` (10 entries) and a
# top-level `slots.py.proposed-3repo` sitting unreported the same way.
#
# A watcher that reports nothing looks exactly like an empty inbox. That is the
# shape of every defect this channel found: silent, and indistinguishable from
# healthy.
#
# A DIRECTORY is ONE entry, not N: the unit a reader acts on is the payload, and
# listing 70 files as 70 notes buries the real notes beside them. The entry
# carries the FILE COUNT so a payload that GROWS re-reports instead of matching
# the acknowledgement already on file.
# ---------------------------------------------------------------------------
def _payload(tmp_path, name, *files):
    box = tmp_path / "moon_sync_inbox"
    box.mkdir(exist_ok=True)
    d = box / name
    d.mkdir(exist_ok=True)
    for f in files:
        p = d / f
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("body\n", encoding="ascii")
    return box


def test_a_payload_directory_is_one_entry_carrying_its_file_count(tmp_path):
    box = _payload(tmp_path, "from-RC-verbatim", "a.py", "b.py", "tests/c.py")
    text = "\n".join(_probe(box, tmp_path / "absent.json"))
    assert "1 UNREAD" in text
    assert "from-RC-verbatim/ (3 files," in text
    assert "a.py" not in text, "the payload's files must not be listed one by one"


def test_a_payload_that_grows_re_reports_after_being_acknowledged(tmp_path):
    """The count is IN the entry so an acknowledged payload cannot absorb new
    files silently - the failure mode that made a 70-file drop invisible."""
    box = _payload(tmp_path, "from-CS-verbatim", "a.py")
    rec = tmp_path / "sync_inbox_seen.json"
    rep = _reported(tmp_path)
    _probe_r(box, rec, rep)
    lw_facts.mark_inbox_seen(inbox=box, seen_path=rec, reported_path=rep)
    assert "UNREAD" not in "\n".join(_probe_r(box, rec, rep))

    (box / "from-CS-verbatim" / "b.py").write_text("body\n", encoding="ascii")
    text = "\n".join(_probe_r(box, rec, rep))
    assert "1 UNREAD" in text and "(2 files," in text


def test_a_non_md_top_level_file_is_reported(tmp_path):
    box = _inbox(tmp_path, "note.md")
    (box / "slots.py.proposed-3repo").write_text("payload\n", encoding="ascii")
    text = "\n".join(_probe(box, tmp_path / "absent.json"))
    assert "slots.py.proposed-3repo" in text, (
        "a top-level payload that is not .md was invisible to the watcher")


def test_underscore_prefixed_entries_are_still_excluded(tmp_path):
    box = _inbox(tmp_path, "real.md", "_draft.md")
    (box / "_scratch").mkdir()
    (box / "_scratch" / "x.py").write_text("body\n", encoding="ascii")
    text = "\n".join(_probe(box, tmp_path / "absent.json"))
    assert "1 UNREAD" in text
    assert "_draft.md" not in text and "_scratch" not in text


def test_an_empty_payload_directory_still_reports(tmp_path):
    """Zero files is a real state - a directory created and never filled."""
    box = _payload(tmp_path, "from-LL-verbatim")
    text = "\n".join(_probe(box, tmp_path / "absent.json"))
    assert "from-LL-verbatim/ (0 files," in text


def test_a_replaced_file_re_reports_even_though_the_count_is_unchanged(tmp_path):
    """RC shipped the `(N files)` key and refuted it within the hour: a sender
    who REPLACES a file leaves the count equal, so the payload reads as already
    seen. That is the mtime-watermark defect again - a key that stays equal
    while the thing it names has moved."""
    box = _payload(tmp_path, "from-RC-verbatim", "a.py")
    rec = tmp_path / "sync_inbox_seen.json"
    rep = _reported(tmp_path)
    _probe_r(box, rec, rep)
    lw_facts.mark_inbox_seen(inbox=box, seen_path=rec, reported_path=rep)
    assert "UNREAD" not in "".join(_probe_r(box, rec, rep))

    (box / "from-RC-verbatim" / "a.py").write_text(
        "a completely different body\n", encoding="ascii")
    assert "1 UNREAD" in "".join(_probe_r(box, rec, rep)), (
        "a REPLACED file must re-report - the count alone cannot see it")


def test_a_manifest_keys_the_payload_when_the_sender_ships_one(tmp_path):
    """RC's proposed convention: `MANIFEST.sha256` in the payload, and the
    watcher keys on the manifest rather than walking every file."""
    box = _payload(tmp_path, "from-CS-verbatim", "a.py", "b.py")
    man = box / "from-CS-verbatim" / "MANIFEST.sha256"
    man.write_text("aaaa  a.py\nbbbb  b.py\n", encoding="ascii")
    first = "".join(_probe(box, tmp_path / "absent.json"))
    man.write_text("cccc  a.py\nbbbb  b.py\n", encoding="ascii")
    second = "".join(_probe(box, tmp_path / "absent.json"))
    assert first != second, (
        "the payload key must move when MANIFEST.sha256 changes")
