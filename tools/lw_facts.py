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
  C:/Users/Administrator/AppData/Local/Programs/Python/Python314/python.exe tools/lw_facts.py
"""
from __future__ import annotations

import hashlib
import csv
import io
import json
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

# Cross-repo mail. UNREAD is a set of seen FILENAMES, never an mtime watermark:
# a watermark advances on WRITE, so a session cleared or killed before anyone
# read the output moves it past a note nobody saw, and it also loses to
# timestamp-preserving delivery (cp -p, robocopy /COPY:T, restore-from-backup)
# and to clock skew. All three fail as SILENCE, indistinguishable from "no
# mail" - the exact failure class this channel produced twice on 2026-09-06.
# The record is per-machine state and lives gitignored under ops/runtime/.
# KNOWN COST, accepted rather than designed around (RC, 2026-09-07): a
# RENAMED note reads as new mail, because the key is the name. Keying on a
# content hash trades it for a worse failure - an EDITED note would then read
# as already seen, and an edit is the case you most want surfaced. A false
# 'new mail' costs one glance; a missed correction costs whatever it was for.
# mark_inbox_seen() rewriting from the CURRENT listing makes this self-heal.
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


def _payload_key(d: Path) -> str:
    """A payload directory's entry text, and the thing the seen set keys on.

    RC proposed `(N files)` and refuted it inside the hour: a sender who
    REPLACES a file leaves the count equal, so the payload reads as already
    seen. That is the mtime-watermark defect again - a key that stays equal
    while the thing it names has moved.

    So the key is a DIGEST, and it comes from one of two places:

      * `MANIFEST.sha256` if the sender shipped one (RC's proposed convention):
        one file read, and the key moves whenever any listed file does.
      * otherwise a walk over (relpath, size, mtime_ns), which needs no
        cooperation from the sender and still moves when a file is replaced.

    The COUNT stays in the visible text because it is what a reader acts on;
    it is no longer what the key rests on. Hashing is over metadata, not
    content: this runs inside a SessionStart hook with a few seconds of budget,
    and a same-size same-mtime replacement is a case that degrades to a missed
    report rather than to a wrong one - the sender ships a manifest to close it.
    """
    files = sorted(q for q in d.rglob("*") if q.is_file())
    manifest = d / "MANIFEST.sha256"
    h = hashlib.sha256()
    if manifest.is_file():
        try:
            h.update(manifest.read_bytes())
            return f"{d.name}/ ({len(files)} files, m:{h.hexdigest()[:8]})"
        except OSError:
            pass
    for q in files:
        try:
            st = q.stat()
            h.update(str(q.relative_to(d)).encode("utf-8", "replace"))
            h.update(f"|{st.st_size}|{st.st_mtime_ns}|".encode("ascii"))
        except OSError:
            h.update(b"|unreadable|")
    return f"{d.name}/ ({len(files)} files, {h.hexdigest()[:8]})"


def _inbox_names(inbox: Path) -> list[str]:
    """Current listing. `_`-prefixed drafts excluded, everything else counted.

    NOT top-level `*.md`. Measured 2026-09-07 on RC's tree and then on this one:
    the watcher globbed top-level `.md` only, so a payload DIRECTORY was
    invisible - RC invented the `from-<CODE>-verbatim/` convention, asked four
    repos to reciprocate in it, and reported zero of the 70 files CS sent. LW
    had `from-RSC-verbatim/` and a top-level `slots.py.proposed-3repo` sitting
    unreported the same way. A watcher that reports nothing looks exactly like
    an empty inbox.

    A DIRECTORY is ONE entry, never N: the unit a reader acts on is the payload,
    and listing 70 files individually buries the real notes beside them. The
    entry carries a DIGEST so a payload that grows OR CHANGES re-reports rather
    than matching the acknowledgement already on file - see `_payload_key`.
    """
    if not inbox.is_dir():
        return []
    out: list[str] = []
    for p in inbox.iterdir():
        if p.name.startswith("_"):
            continue
        if p.is_dir():
            out.append(_payload_key(p))
        elif p.is_file():
            out.append(p.name)
    return sorted(out)


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
    inbox = _INBOX if inbox is None else inbox
    seen_path = _SEEN if seen_path is None else seen_path
    reported_path = _REPORTED if reported_path is None else reported_path
    try:
        if not inbox.is_dir():
            return [f"- moon_sync_inbox: absent at {inbox} - no cross-repo mail channel"]
        names = _inbox_names(inbox)
        unread = [n for n in names if n not in _seen_names(seen_path)]
        if not unread:
            _write_reported(reported_path, [])
            return [f"- moon_sync_inbox: 0 unread of {len(names)} notes"]
        lines = [f"- moon_sync_inbox: {len(unread)} UNREAD of {len(names)} notes"]
        shown = unread[-_INBOX_SHOWN:]
        _write_reported(reported_path, shown)
        for n in shown:
            lines.append(f"  - {n}")
        if len(unread) > _INBOX_SHOWN:
            lines.append(f"  - ... and {len(unread) - _INBOX_SHOWN} more, oldest first")
        lines.append("- acknowledge (only after reading): "
                     "python tools/lw_facts.py --mark-inbox-seen")
        # CHARTER v2 section 1 classifies in the title: REVIEW- wants a reply
        # from all five before the sender proceeds and ACTION- is blocking, so
        # an unread one of those is a real anomaly. FYI- is not.
        wanted = [n for n in unread if "REVIEW-" in n or "ACTION-" in n]
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
    inbox = _INBOX if inbox is None else inbox
    seen_path = _SEEN if seen_path is None else seen_path
    reported_path = _REPORTED if reported_path is None else reported_path
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
    if "--mark-inbox-seen" in sys.argv[1:]:
        every = "--all" in sys.argv[1:]
        n = mark_inbox_seen(all_notes=every)
        # Name the mode honestly: with no report record yet the ack falls back
        # to the listing, and calling that "what the report showed" would be
        # the same false reassurance the whole change is removing.
        if every:
            how = "EVERY note - deliberate baseline"
        elif _reported_names(_REPORTED) is None:
            how = "EVERY note - no report record yet, baseline"
        else:
            how = "the notes the last report showed"
        sys.stdout.write(
            f"marked {n} inbox note(s) seen ({how}) -> {_SEEN}\n")
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
