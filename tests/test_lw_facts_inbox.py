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
    """Rewrite, not union - so an archived note prunes automatically."""
    box = _inbox(tmp_path, "current.md")
    rec = _record(tmp_path, ["archived-and-gone.md"])
    lw_facts.mark_inbox_seen(inbox=box, seen_path=rec)
    doc = json.loads(rec.read_text(encoding="utf-8"))
    assert set(doc["seen"]) == {"current.md"}
    assert "UNREAD" not in "\n".join(_probe(box, rec))


def test_acknowledge_creates_the_record_when_absent(tmp_path):
    box = _inbox(tmp_path, "a.md")
    rec = tmp_path / "made" / "sync_inbox_seen.json"
    lw_facts.mark_inbox_seen(inbox=box, seen_path=rec)
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
