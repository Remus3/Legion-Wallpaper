# arch: live LW state probe | section=tools | frozen=no
"""lw_facts.py - print live ground truth for the Legion Wallpaper project.

Designed to be invoked as a Claude Code SessionStart hook on Legion.
Output (markdown to stdout) is injected as additional context, so the
session starts with current state instead of relying on possibly-stale
memory entries.

Probes (all wrapped in their own try/except; total wall-clock is capped
by a shared budget well under the 8s hook timeout):
  - git: current branch, dirty file count, last 3 commits one line each.
  - Scheduled tasks matching LW-* via schtasks, state for each
    ("none registered yet" fallback - do NOT register tasks from here).
  - ops/runtime/health.json summary if the file exists, else
    "no runtime yet (product TBD)".
  - Pipeline digest: per-stage counts under images/, loose files in
    0.Originals awaiting intake, needs-attention count from
    ops/runtime/pipeline_state.json, PIPELINE_LOG.md last line.
    Degrades to "pipeline idle" when nothing is staged or probing fails.
  - WAKEUP_NOTES.md first non-empty line (session-notes freshness hint).

Cheap and idempotent. A single failing probe can never break session
start. Caller (the hook) gets stdout; non-zero exit just means
"couldn't probe" and is non-blocking.

Run manually any time:
  python tools/lw_facts.py
"""
from __future__ import annotations

import hashlib
import csv
import io
import json
import os
import stat
import subprocess
import sys
import time
from pathlib import Path

# SessionStart hook runs under windowless pythonw.exe; a console child would
# otherwise get a fresh console allocated - an on-screen + taskbar flash.
# CREATE_NO_WINDOW suppresses it (Windows-only; 0 elsewhere).
_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)

_ROOT = Path(__file__).resolve().parent.parent
_HEALTH = _ROOT / "ops" / "runtime" / "health.json"
_WAKEUP = _ROOT / "WAKEUP_NOTES.md"

# Cross-repo mail. UNREAD is a set of seen KEYS - each a name plus a content
# digest, see _inbox_entries() - and never an mtime watermark:
# a watermark advances on WRITE, so a session cleared or killed before anyone
# read the output moves it past a note nobody saw, and it also loses to
# timestamp-preserving delivery (cp -p, robocopy /COPY:T, restore-from-backup)
# and to clock skew. All three fail as SILENCE, indistinguishable from "no
# mail" - the exact failure class this channel produced twice on 2026-09-06.
# The record is per-machine state and lives gitignored under ops/runtime/.
# A paragraph defending the NAME key stood here until 2026-09-07 and is DELETED
# rather than reworded, on CS's argument that a reworded rationale keeps the
# authority of the original. It claimed a content key was the worse option
# because "an EDITED note would then read as already seen" - which is exactly
# inverted: an edit changes the content, so it changes the digest, so a content
# key SURFACES the edit and the name key is the one that hides it. It had also
# gone stale, describing a name key this module stopped using in 271a4f7.
# What the key actually is, and why, lives on _inbox_entries().
_INBOX = _ROOT / "moon_sync_inbox"
_SEEN = _ROOT / "ops" / "runtime" / "sync_inbox_seen.json"
# What the LAST report actually SHOWED. Acknowledgement is an intersection with
# this, never with the current listing: measured twice (6 notes 2026-09-05, 5
# notes 2026-09-06), `--mark-inbox-seen` marked notes that landed AFTER the
# session-start report and were never shown to anyone. That is the mtime
# watermark defect wearing the ACK as a costume instead of the report, and the
# ritual fix ("ack at session start") cannot close it - a note arriving a minute
# after the report is still in the listing when the ack runs.
_REPORTED = _ROOT / "ops" / "runtime" / "sync_inbox_reported.json"
_INBOX_SHOWN = 10


# DERIVED AT USE, NOT AT IMPORT. The three constants above are bound to the real
# root the moment this module is imported, so a caller that redirects `_ROOT` -
# which is what every test in the tree does, and the only redirection any of
# them was written to need - kept the REAL inbox, seen and reported paths.
# Measured 2026-09-11 by tracing the suite's own writes: `main()` under a
# patched `_ROOT` wrote the operator's live `sync_inbox_reported.json`, which is
# half of the report-then-acknowledge split, so the next `--mark-inbox-seen`
# would have acknowledged mail nobody was ever shown. That is the LEDGER 162
# defect re-entered through the suite. Patching three more names in one arm
# would have left the next arm to rediscover it; deriving here means `_ROOT` is
# sufficient, as it already appeared to be.


def _inbox_path() -> Path:
    return _ROOT / "moon_sync_inbox"


def _seen_path() -> Path:
    return _ROOT / "ops" / "runtime" / "sync_inbox_seen.json"


def _reported_path() -> Path:
    return _ROOT / "ops" / "runtime" / "sync_inbox_reported.json"
NEWLINE = chr(10)

# Shared wall-clock budget (seconds). The hook timeout is 8s; every
# subprocess gets min(its own cap, whatever budget remains), so the
# script as a whole finishes well under the hook limit even if some
# probe hangs to its cap.
_BUDGET_S = 6.0
_T0 = time.monotonic()


def _remaining() -> float:
    return _BUDGET_S - (time.monotonic() - _T0)


def _run(cmd: list[str], cap: float = 2.0) -> str | None:
    """Run a command; return stripped stdout on success else None. Never raises."""
    timeout = min(cap, _remaining())
    if timeout <= 0.1:
        return None
    try:
        p = subprocess.run(
            cmd, capture_output=True, timeout=timeout, text=True,
            encoding="utf-8", errors="replace", cwd=str(_ROOT),
            creationflags=_NO_WINDOW,
        )
        if p.returncode == 0:
            return p.stdout.strip()
    except Exception:  # noqa: BLE001 - a probe must never break the hook
        pass
    return None


# -- probes (each returns markdown lines; each is exception-proof) --------

def _git_lines(anomalies: list[str]) -> list[str]:
    try:
        branch = _run(["git", "branch", "--show-current"])
        if branch is None:
            return ["- git: not a git repo yet (or git unavailable)"]
        status = _run(["git", "status", "--porcelain"])
        dirty = len(status.splitlines()) if status else 0
        lines = [f"- git: branch={branch or '?'} dirty_files={dirty}"]
        log = _run(["git", "log", "--oneline", "-3"])
        if log:
            lines.append("- last 3 commits:")
            for ln in log.splitlines():
                lines.append(f"  - {ln}")
        else:
            lines.append("- last 3 commits: none yet (unborn branch)")
        return lines
    except Exception:  # noqa: BLE001
        anomalies.append("git probe crashed")
        return ["- git: probe failed"]


def _task_lines(anomalies: list[str]) -> list[str]:
    """LW-* scheduled tasks via schtasks CSV (documented convention: LW-*)."""
    try:
        out = _run(["schtasks", "/Query", "/FO", "CSV", "/NH"], cap=4.0)
        if out is None:
            return ["- scheduled tasks: probe unavailable"]
        rows: list[tuple[str, str]] = []
        for rec in csv.reader(io.StringIO(out)):
            if len(rec) < 3:
                continue
            name = rec[0].split("\\")[-1]
            if name.startswith("LW-"):
                rows.append((name, rec[2] or "?"))
        if not rows:
            return ["- scheduled tasks (LW-*): none registered yet"]
        lines = [f"- scheduled tasks ({len(rows)} LW-*):"]
        for name, state in sorted(set(rows)):
            lines.append(f"  - {name}: state={state}")
            if state.lower() == "disabled":
                anomalies.append(f"scheduled task {name} is Disabled")
        return lines
    except Exception:  # noqa: BLE001
        anomalies.append("schtasks probe crashed")
        return ["- scheduled tasks: probe failed"]


def _health_lines(anomalies: list[str]) -> list[str]:
    try:
        if not _HEALTH.is_file():
            return ["- runtime: no runtime yet (product TBD) - ops/runtime/health.json absent"]
        h = json.loads(_HEALTH.read_text(encoding="utf-8"))
        pid = h.get("pid")
        alive = h.get("alive")
        mode = h.get("mode") or "?"
        version = h.get("lw_version") or h.get("version") or "?"
        lines = [
            f"- runtime health.json: pid={pid} alive={alive} mode={mode} "
            f"version={version} (keys={len(h)})"
        ]
        if alive is False:
            anomalies.append(f"runtime not alive (pid={pid})")
        return lines
    except Exception:  # noqa: BLE001
        anomalies.append("ops/runtime/health.json exists but unreadable/invalid")
        return ["- runtime health.json: UNREADABLE"]


# Stage folders exactly per the pipeline contract (docs/research/
# PIPELINE_STATE_MACHINE.md). 0.Originals holds loose intake files; stages
# 1-9 hold per-image subfolders; reference_pictures is the non-pipeline
# reference corpus.
_STAGE_FOLDERS = (
    "0.Originals",
    "1.First Pass Scratch",
    "2.First Pass Done",
    "3.Cleaning Scratch",
    "4.Cleaning Done",
    "5.Final Scratch",
    "6.Final Done",
    "7.Last Scratch",
    "8.End Review",
    "9.Image Backup",
)


def _pipeline_state_lines(anomalies: list[str], state_path: Path) -> list[str]:
    """needs-attention summary from ops/runtime/pipeline_state.json."""
    try:
        if not state_path.is_file():
            return ["- pipeline_state.json: absent (no scan yet)"]
        state = json.loads(state_path.read_text(encoding="utf-8"))
        counts = state.get("counts") or {}
        need = counts.get("anomalies")
        if need is None:
            need = len(state.get("anomalies") or [])
        line = f"- pipeline_state.json: needs_attention={need}"
        ts = state.get("generated_ts")
        if ts:
            line += f" (scanned {ts})"
        if need:
            anomalies.append(f"pipeline needs attention: {need} anomalies in pipeline_state.json")
        return [line]
    except Exception:  # noqa: BLE001 - a probe must never break the hook
        anomalies.append("pipeline_state.json exists but unreadable/invalid")
        return ["- pipeline_state.json: UNREADABLE"]


def _pipeline_log_line(log_path: Path) -> list[str]:
    """Last non-empty line of PIPELINE_LOG.md (never raises)."""
    try:
        if not log_path.is_file():
            return ["- PIPELINE_LOG.md: not present yet"]
        last = ""
        for ln in log_path.read_text(encoding="utf-8", errors="replace").splitlines():
            if ln.strip():
                last = ln.strip()
        if last:
            return [f"- PIPELINE_LOG.md last: {last}"]
        return ["- PIPELINE_LOG.md: present but empty"]
    except Exception:  # noqa: BLE001
        return ["- PIPELINE_LOG.md: probe failed"]


def _pipeline_lines(anomalies: list[str], root: Path | None = None) -> list[str]:
    """Pipeline digest for the session-start hook.

    root is injectable for tests (defaults to the repo root); everything is
    derived from it: images/ tree, ops/runtime/pipeline_state.json,
    PIPELINE_LOG.md. Cheap (one shallow scandir per stage folder) and
    exception-proof; degrades to "pipeline idle".
    """
    if root is None:
        root = _ROOT
    try:
        images = root / "images"
        lines: list[str] = []
        if not images.is_dir():
            lines.append("- pipeline idle - images/ tree not present")
        else:
            # 0.Originals: loose files awaiting intake ("new since last
            # intake" - intake removes files, so presence = pending).
            awaiting = 0
            orig = images / _STAGE_FOLDERS[0]
            if orig.is_dir():
                awaiting = sum(
                    1 for p in orig.iterdir() if p.is_file() and p.name != ".gitkeep"
                )
            # Stages 1-9: per-image subfolder counts.
            stage_counts: list[tuple[str, int]] = []
            staged_total = 0
            for stage in _STAGE_FOLDERS[1:]:
                d = images / stage
                n = sum(1 for p in d.iterdir() if p.is_dir()) if d.is_dir() else 0
                stage_counts.append((stage, n))
                staged_total += n
            ref = images / "reference_pictures"
            ref_n = (
                sum(1 for p in ref.iterdir() if p.is_file() and p.name != ".gitkeep")
                if ref.is_dir()
                else 0
            )
            if awaiting == 0 and staged_total == 0 and ref_n == 0:
                lines.append("- pipeline idle - no files staged under images/")
            else:
                lines.append(f"- 0.Originals: {awaiting} loose files awaiting intake")
                lines.append(
                    "- stages: "
                    + " | ".join(f"{name}={n}" for name, n in stage_counts)
                )
                lines.append(f"- reference_pictures: {ref_n} files")
        lines.extend(
            _pipeline_state_lines(anomalies, root / "ops" / "runtime" / "pipeline_state.json")
        )
        lines.extend(_pipeline_log_line(root / "PIPELINE_LOG.md"))
        return lines
    except Exception:  # noqa: BLE001 - a probe must never break the hook
        anomalies.append("pipeline probe crashed")
        return ["- pipeline: probe failed (treat as pipeline idle)"]


def _file_digest(p: Path) -> str:
    """sha256 of a file's CONTENTS, or the exception class if it cannot be read.

    An unreadable file contributes its failure rather than vanishing, so it
    MOVES the key instead of silently dropping out of it.
    """
    try:
        return hashlib.sha256(p.read_bytes()).hexdigest()
    except OSError as exc:
        return f"unreadable:{type(exc).__name__}"


_REPARSE = 0x400          # FILE_ATTRIBUTE_REPARSE_POINT
_WALK_BUDGET = 5000       # entries per drop, then the walk reports and stops


def _is_reparse(p: Path) -> bool:
    """True for a junction, a symlink, or any other reparse point.

    `Path.is_symlink()` alone is NOT enough and that is the whole finding: it is
    FALSE for an NTFS junction. CS measured a one-file payload reporting 32
    files because `rglob` descended one, and LW reproduced exactly that number
    here before this existed. The cost is not a wrong count - a junction over a
    large tree runs the walk past the hook's timeout, the hook is killed, and a
    killed hook surfaces NOTHING at all.
    """
    try:
        st = os.lstat(p)
    except OSError:
        return False
    return bool(getattr(st, "st_file_attributes", 0) & _REPARSE) or stat.S_ISLNK(st.st_mode)


def _walk_drop(d: Path) -> list[tuple[str, str]]:
    """`(relative posix path, digest-or-reason)` for a drop, without following links.

    Iterative and pruned rather than `rglob`, which cannot be told not to follow
    a junction. CS's rule is the shape: what cannot be digested is carried into
    the key WITH ITS REASON rather than skipped, so a file that turns
    unreadable, a link that appears, or a tree that blows the budget all MOVE
    the key instead of quietly leaving it equal.
    """
    out: list[tuple[str, str]] = []
    stack = [d]
    seen = 0
    while stack:
        cur = stack.pop()
        try:
            children = sorted(cur.iterdir())
        except OSError as exc:
            out.append((cur.relative_to(d).as_posix() or ".",
                        f"unreadable-dir:{type(exc).__name__}"))
            continue
        for q in children:
            seen += 1
            if seen > _WALK_BUDGET:
                out.append(("", f"budget-exceeded:{_WALK_BUDGET}"))
                return out
            rel = q.relative_to(d).as_posix()
            if _is_reparse(q):
                out.append((rel, "reparse-point"))
            elif q.is_dir():
                stack.append(q)
            elif q.is_file():
                out.append((rel, _file_digest(q)))
            else:
                out.append((rel, "unclassifiable"))
    return out


def _drop_digest(d: Path) -> str:
    """Digest of a payload directory, over what is actually ON DISK.

    RC's algorithm, re-implemented from its prose so all five agree: one line
    per file holding the drop-relative POSIX path, a NUL, then that file's
    sha256; sorted, joined with newlines, hashed once. The PATH inside each line
    is what makes two files swapping contents a change.

    NOT the digest of `MANIFEST.sha256`. RC measured the trap and it is real
    here too: a payload edited without regenerating its manifest keys IDENTICAL,
    so keying on the manifest means trusting the sender to have rebuilt it -
    exactly the assumption a watcher exists to remove. The manifest is still
    worth shipping; it just cannot be the key.
    """
    lines = [f"{rel}\0{mark}" for rel, mark in _walk_drop(d)]
    joined = "\n".join(sorted(lines))
    return hashlib.sha256(joined.encode("utf-8", "replace")).hexdigest()


def _inbox_entries(inbox: Path) -> list[tuple[str, str]]:
    """`(key, display)` per inbox entry, sorted by display.

    KEY AND DISPLAY ARE DIFFERENT THINGS and conflating them was the defect.
    The key carries a content digest so an in-place EDIT re-reports; the display
    stays the bare name so the report a human reads is not a wall of hashes.
    Measured 2026-09-07 on this tree, after RC measured the same on its own: a
    note corrected IN PLACE moved nothing the watcher could see, and this
    channel has already sent notes under a CORRECTION heading.

    `_`-prefixed entries are drafts and stay excluded.
    """
    if not inbox.is_dir():
        return []
    out: list[tuple[str, str]] = []
    for p in inbox.iterdir():
        if p.name.startswith("_"):
            continue
        if _is_reparse(p):
            # Reported, never followed and never opened. A link is a claim about
            # somewhere else; the watcher's job is to say that it arrived.
            out.append((f"{p.name}#reparse", f"{p.name} (? link, not followed)"))
        elif p.is_dir():
            walked = _walk_drop(p)
            n = sum(1 for _, mark in walked if len(mark) == 64)
            odd = sorted({m.split(":")[0] for _, m in walked if len(m) != 64})
            manifest = " +manifest" if (p / "MANIFEST.sha256").is_file() else ""
            note = f", ? {'/'.join(odd)}" if odd else ""
            plural = "" if n == 1 else "s"
            out.append((f"{p.name}/#{_drop_digest(p)[:12]}",
                        f"{p.name}/ ({n} file{plural}{manifest}{note})"))
        elif p.is_file():
            out.append((f"{p.name}#{_file_digest(p)[:12]}", p.name))
        else:
            # NEITHER, which an `if`/`elif` with no `else` dropped off the end of
            # the loop: a dangling link, a name Windows normalises away, or a
            # file deleted between the listing and the classification. CS
            # measured two real deliverables going invisible under exit 0.
            out.append((f"{p.name}#unclassifiable",
                        f"{p.name} (? neither file nor directory)"))
    return sorted(out, key=lambda e: e[1])


def _inbox_names(inbox: Path) -> list[str]:
    """The KEYS, which is what the seen set stores and compares."""
    return [key for key, _ in _inbox_entries(inbox)]


def _seen_names(seen_path: Path) -> set[str]:
    """The acknowledged set. A missing or corrupt record reads as EMPTY, so
    everything re-reports - degrading to noise, never to silence."""
    try:
        doc = json.loads(seen_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return set()
    names = doc.get("seen") if isinstance(doc, dict) else doc
    if not isinstance(names, list):
        return set()
    return {n for n in names if isinstance(n, str)}


def _reported_names(reported_path: Path) -> set[str] | None:
    """What the last report showed. None = no usable record (never reported)."""
    try:
        doc = json.loads(reported_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    names = doc.get("reported") if isinstance(doc, dict) else doc
    if not isinstance(names, list):
        return None
    return {n for n in names if isinstance(n, str)}


def _write_reported(reported_path: Path, names: list[str]) -> None:
    """Record what was shown. Best effort by contract: this runs inside the
    SessionStart hook and must never be the reason the hook fails."""
    try:
        reported_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = reported_path.with_name(reported_path.name + ".tmp")
        tmp.write_text(
            json.dumps({"reported": names,
                        "at": time.strftime("%Y-%m-%dT%H:%M:%S")}, indent=2)
            + "\n",
            encoding="utf-8", newline="\n")
        tmp.replace(reported_path)
    except OSError:
        pass


def _stable_name(key: str) -> str:
    """A key with its content digest stripped - the part a rewrite preserves.

    Keys are `<name>#<digest12>` for a note and `<name>/#<digest12>` for a
    drop, so everything up to the first `#` is the on-disk name (the drop keeps
    its trailing slash, which is what distinguishes the two in a report).
    """
    return key.split("#", 1)[0]


def _withdrawn_keys(present: list[str], seen: set[str],
                    reported: set[str] | None) -> list[str]:
    """Keys the operator was SHOWN or acknowledged that are no longer on disk.

    The comparison is on the stable NAME, not the key. Once keys carry a
    digest, an in-place EDIT and a RETRACTION both move the key, so a raw key
    comparison reports an edited note in two contradictory sections at once -
    UNREAD because its new key is unseen, WITHDRAWN because its old key is
    absent. An edit keeps its name; only a retraction loses it.

    The baseline is `reported | seen`, never `seen` alone. RC's 2026-09-07
    incident - the one that proved this is worth a line of code, when it pulled
    50 files back out of four inboxes - was notes LISTED at session start and
    pulled before anyone ran the ack. Those live in the report record only, so
    a seen-only baseline would score the motivating case as a non-event.
    """
    here = {_stable_name(k) for k in present}
    baseline = seen | (reported or set())
    return sorted(k for k in baseline if _stable_name(k) not in here)


def _withdrawn_lines(gone: list[str], anomalies: list[str]) -> list[str]:
    """The report half. A withdrawal is an ANOMALY, not an informational line.

    It is the only inbox event that carries no artifact: the operator cannot
    go and read the thing that changed, so if this line is missed there is
    nothing left on disk to notice later.

    Withdrawn keys are carried in the REPORT record until the ack prunes them
    (the ack keeps `(seen | reported) AND still present`, and a withdrawn name
    is by definition not present). Reporting a withdrawal exactly once would
    put it back in the watermark's failure class: a session cleared before
    anyone read the output would lose it with nothing on disk to recover from.
    """
    if not gone:
        return []
    shown = gone[-_INBOX_SHOWN:]
    lines = [f"- moon_sync_inbox: {len(gone)} WITHDRAWN since shown "
             f"(pulled by the sender, no longer on disk)"]
    lines.extend(f"  - {name}" for name in shown)
    if len(gone) > _INBOX_SHOWN:
        lines.append(f"  - ... and {len(gone) - _INBOX_SHOWN} more")
    anomalies.append(
        f"{len(gone)} inbox note(s) WITHDRAWN after being shown: "
        f"{', '.join(shown[-3:])}")
    return lines


def _inbox_lines(anomalies: list[str], inbox: Path | None = None,
                 seen_path: Path | None = None,
                 reported_path: Path | None = None) -> list[str]:
    """Unread cross-repo notes. REPORTS ONLY - never acknowledges.

    Acknowledging here would make "unread" a property of whether this hook ran
    rather than of whether anyone read the note, which is the watermark defect
    in a different costume. `mark_inbox_seen()` is the separate action, so an
    unacknowledged note re-reports next session instead of being lost.

    Exception-proof by contract: this runs inside the SessionStart hook, and a
    crash here would take the whole live-state block with it - worse than a
    missed mail line.
    """
    inbox = _inbox_path() if inbox is None else inbox
    seen_path = _seen_path() if seen_path is None else seen_path
    reported_path = _reported_path() if reported_path is None else reported_path
    try:
        if not inbox.is_dir():
            return [f"- moon_sync_inbox: absent at {inbox} - no cross-repo mail channel"]
        entries = _inbox_entries(inbox)
        seen = _seen_names(seen_path)
        names = [k for k, _ in entries]
        # The KEY decides unread; the DISPLAY is what a human reads. An entry
        # whose content changed carries a new key under the same display.
        unread_pairs = [(k, d) for k, d in entries if k not in seen]
        unread = [k for k, _ in unread_pairs]
        withdrawn_keys = _withdrawn_keys(names, seen,
                                         _reported_names(reported_path))
        gone = sorted({_stable_name(k) for k in withdrawn_keys})
        if not unread:
            _write_reported(reported_path, withdrawn_keys)
            return ([f"- moon_sync_inbox: 0 unread of {len(names)} notes"]
                    + _withdrawn_lines(gone, anomalies))
        lines = [f"- moon_sync_inbox: {len(unread)} UNREAD of {len(names)} notes"]
        shown_pairs = unread_pairs[-_INBOX_SHOWN:]
        shown = [k for k, _ in shown_pairs]
        _write_reported(reported_path, shown + withdrawn_keys)
        for _, display in shown_pairs:
            lines.append(f"  - {display}")
        if len(unread) > _INBOX_SHOWN:
            lines.append(f"  - ... and {len(unread) - _INBOX_SHOWN} more, oldest first")
        lines.append("- acknowledge (only after reading): "
                     "python tools/lw_facts.py --mark-inbox-seen")
        lines.extend(_withdrawn_lines(gone, anomalies))
        # CHARTER v2 section 1 classifies in the title: REVIEW- wants a reply
        # from all five before the sender proceeds and ACTION- is blocking, so
        # an unread one of those is a real anomaly. FYI- is not.
        wanted = [d for _, d in unread_pairs if "REVIEW-" in d or "ACTION-" in d]
        if wanted:
            anomalies.append(
                f"{len(wanted)} unread REVIEW-/ACTION- inbox note(s) awaiting a "
                f"response: {', '.join(wanted[-3:])}")
        return lines
    except Exception:  # noqa: BLE001 - a probe must never break the hook
        anomalies.append("moon_sync_inbox probe crashed")
        return ["- moon_sync_inbox: probe failed"]


def mark_inbox_seen(inbox: Path | None = None, seen_path: Path | None = None,
                    reported_path: Path | None = None,
                    all_notes: bool = False) -> int:
    """Acknowledge the notes the last report actually SHOWED. Returns the count.

    NOT the current listing. Measured twice - 6 notes on 2026-09-05 and 5 on
    2026-09-06 - acknowledging the listing marked notes that landed AFTER the
    session-start report and that nobody had been shown. That is the watermark
    defect this design exists to avoid, moved from the report to the ack, and
    the "ack at session start" ritual cannot close it: a note arriving a minute
    after the report is still in the listing when the ack runs.

    So the rule is: seen = (already seen OR reported) AND still present.
    Unioning with the old set keeps yesterday's reading; intersecting with the
    listing keeps the automatic pruning of an archived note, which is why the
    record is rewritten rather than appended to.

    Two deliberate exits from that rule, both explicit:
      * NO report record at all (a tree where the hook has never run) falls
        back to the listing, so a first baseline is still one command;
      * `all_notes=True` (`--mark-inbox-seen --all`) is the operator's
        deliberate baseline reset.

    Atomic write - the hook may read the record mid-run.
    """
    inbox = _inbox_path() if inbox is None else inbox
    seen_path = _seen_path() if seen_path is None else seen_path
    reported_path = _reported_path() if reported_path is None else reported_path
    listing = _inbox_names(inbox)
    reported = _reported_names(reported_path)
    if all_notes or reported is None:
        names = listing
    else:
        keep = _seen_names(seen_path) | reported
        names = [n for n in listing if n in keep]
    seen_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = seen_path.with_name(seen_path.name + ".tmp")
    tmp.write_text(
        json.dumps({"seen": names, "marked_at": time.strftime("%Y-%m-%dT%H:%M:%S")},
                   indent=2) + "\n",
        encoding="utf-8", newline="\n")
    tmp.replace(seen_path)
    # The REPORT record is pruned to what is still present, for the same reason
    # the seen set is: the withdrawal set is derived from `reported | seen`, so
    # a withdrawn name left in here re-derives itself on every run and can never
    # be cleared. Measured live on 2026-09-07 - six real withdrawals reported
    # correctly, then reported again after the operator had acknowledged them.
    # It prunes only names that have LEFT the inbox, so it cannot acknowledge
    # anything: a note still on disk keeps its entry either way.
    if reported is not None:
        still_here = set(listing)
        _write_reported(reported_path,
                        sorted(k for k in reported if k in still_here))
    return len(names)


def _wakeup_lines(anomalies: list[str]) -> list[str]:
    try:
        if not _WAKEUP.is_file():
            return ["- WAKEUP_NOTES.md: not present yet"]
        for ln in _WAKEUP.read_text(encoding="utf-8", errors="replace").splitlines():
            if ln.strip():
                return [f"- WAKEUP_NOTES.md first line: {ln.strip()}"]
        return ["- WAKEUP_NOTES.md: present but empty"]
    except Exception:  # noqa: BLE001
        anomalies.append("WAKEUP_NOTES.md unreadable")
        return ["- WAKEUP_NOTES.md: probe failed"]


def main() -> int:
    # Acknowledgement is a SEPARATE action from the report, deliberately: the
    # hook must never mark mail read on the session's behalf.
    # --inbox-only: the UserPromptSubmit half of the watcher. SessionStart
    # fires ONCE, so a note that lands while a session is live is invisible
    # until the next start - and that is the COMMON case on this channel
    # (measured by LL: one drop grew by two files eleven minutes apart inside a
    # single session). This runs on every operator message, including the first
    # one after a /clear, and prints NOTHING when nothing is unread: a hook that
    # speaks on every prompt trains the reader to skip it. It REPORTS only -
    # acknowledgement stays a separate explicit act, so a subagent starting
    # cannot mark the operator queue read.
    if "--inbox-only" in sys.argv[1:]:
        anomalies: list[str] = []
        lines = _inbox_lines(anomalies)
        if any("UNREAD" in ln for ln in lines):
            sys.stdout.write(NEWLINE.join(lines) + NEWLINE)
        return 0

    if "--mark-inbox-seen" in sys.argv[1:]:
        every = "--all" in sys.argv[1:]
        n = mark_inbox_seen(all_notes=every)
        # Name the mode honestly: with no report record yet the ack falls back
        # to the listing, and calling that "what the report showed" would be
        # the same false reassurance the whole change is removing.
        if every:
            how = "EVERY note - deliberate baseline"
        elif _reported_names(_reported_path()) is None:
            how = "EVERY note - no report record yet, baseline"
        else:
            how = "the notes the last report showed"
        sys.stdout.write(
            f"marked {n} inbox note(s) seen ({how}) -> {_seen_path()}\n")
        return 0

    out: list[str] = []
    out.append("# LW live state (lw_facts.py)\n")
    out.append(f"_probed at {time.strftime('%Y-%m-%d %H:%M:%S')}_\n")

    anomalies: list[str] = []

    out.append("## Repo\n")
    out.extend(_git_lines(anomalies))

    out.append("\n## Scheduled tasks\n")
    out.extend(_task_lines(anomalies))

    out.append("\n## Runtime\n")
    out.extend(_health_lines(anomalies))

    out.append("\n## Pipeline\n")
    out.extend(_pipeline_lines(anomalies))

    out.append("\n## Sync inbox\n")
    out.extend(_inbox_lines(anomalies))

    out.append("\n## Session notes\n")
    out.extend(_wakeup_lines(anomalies))

    # -- Anomaly summary first if any (matches rc_facts.py output style) --
    if anomalies:
        head = "## ! Anomalies\n\n" + "\n".join(f"- {a}" for a in anomalies) + "\n\n"
        sys.stdout.write(head)
    sys.stdout.write("\n".join(out) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
