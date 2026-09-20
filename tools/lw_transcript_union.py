"""lw_transcript_union - close a split Claude transcript store by line-level union.

THE DEFECT (measured 2026-09-20, write-up docs/TRANSCRIPT_UNION_2026-09-20.md)

`~/.claude/projects` held TWO store keys encoding one tree:

    C--Legion-Wallpaper   65 files, 343,655,472 B, written this minute   <- canonical
    C--LegionWallpaper      4 files,  13,409,469 B, last 2026-09-12      <- stray

Three session UUIDs existed under BOTH keys, and for two of them the STRAY copy was
the longer record. The three shapes were NOT the same:

  cf160e3d  575 lines both sides, byte-identical                       -> no-op
  a89cfc16  canon 1036 / stray 1037 lines, canon-only 0                -> stray superset by 1
  d3d7c8f7  canon 216 / stray 426 lines, uuid intersection ZERO        -> CONTINUATION TAIL

The third is the interesting one and the premise for this tool had it wrong. It is not a
divergent fork and not a superset: the canonical copy covers 21:53:27 -> 22:05:12 and the
stray covers 22:05:13 -> 22:32:09, the uuid sets are disjoint, and the stray's very first
record is parented on `881ef3fa-42c6-4a87-b834-dea45a4f16a7`, which is the canonical
copy's LAST uuid. One session was written into two keys across a mid-session key flip.
Appending the stray after the canonical bytes therefore reconstructs the original causal
order exactly - it is not merely lossless, it is correct.

Every `cwd` in both copies of all three sessions is `C:\\LegionWallpaper` (no space), a
path that does not exist. A phantom cwd, not a second checkout - and note it is phantom in
the CANONICAL copies too, so cwd does not distinguish the two keys.

UNION SEMANTICS

Multiset union keyed on each record's stable id:

  * key = the record's `uuid` when it has one;
  * key = the record's raw bytes when it does not. 384 of 1036 lines in a89cfc16 carry no
    `uuid` (`queue-operation`, `last-prompt`, `custom-title`, `bridge-session`,
    `atis-latch`, `mode`) and many are byte-identical repeats, so a set-based union would
    silently DROP records. Output count per key is max(canon_count, stray_count).
  * an unparseable line keys on its own bytes and is kept.

Output = every canonical line in its original order, then any stray record beyond what
canon already held, in the stray's own order. No record is dropped and no record's bytes
are rewritten - lines are copied verbatim, never re-serialized.

SAFETY

  * `--dry-run` is the DEFAULT; `--apply` is opt-in.
  * the pre-union canonical file is backed up to the backup dir BEFORE the replace;
  * the canonical file is written atomically (tmp in the same dir, then os.replace);
  * the STRAY directory is never touched - not deleted, not moved. Closing the split is a
    separate decision the operator owns;
  * the run REFUSES (exit 3) if the RUNNING session's own transcript
    (`$CLAUDE_CODE_SESSION_ID.jsonl`) sits in the canonical dir, if any target is locked
    for writing, or if the canonical dir holds a file modified in the last 120 s. A live
    session writes into that directory continuously, including the session running this
    tool, and unioning a file under a live writer would lose whatever it appends between
    the read and the replace.

    The session-id check is the LOAD-BEARING one. The mtime window alone is insufficient:
    measured 2026-09-20, this session's transcript had last been flushed 353.8s ago while
    the session was plainly live, because Claude Code batches flushes. A guard resting on
    the mtime alone would have passed a live writer through.

No subprocess is spawned, so there is no console-flash surface to guard.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_CANON_KEY = "C--Legion-Wallpaper"
DEFAULT_STRAY_KEY = "C--LegionWallpaper"

#: A canonical-dir file touched more recently than this (seconds) means a LIVE session.
LIVE_WINDOW_S = 120

#: Backups land here, one `<uuid>.canon.bak` per unioned file.
DEFAULT_BACKUP_DIR = Path(r"C:\Legion Wallpaper\ops\runtime\transcript_union")


class Refusal(Exception):
    """A safety guard fired. The caller maps this to exit 3."""


# --------------------------------------------------------------------------- union

def record_key(line: str) -> tuple[str, str]:
    """A stable identity for one .jsonl line.

    ('u', uuid) when the record carries a `uuid`, else ('raw', line) so that
    uuid-less records dedupe on their exact bytes and keep their multiplicity.
    """
    try:
        rec = json.loads(line)
    except (ValueError, TypeError):
        return ("raw", line)
    if isinstance(rec, dict):
        uuid = rec.get("uuid")
        if isinstance(uuid, str) and uuid:
            return ("u", uuid)
    return ("raw", line)


def read_lines(path: Path) -> list[str]:
    """Raw lines with their bytes intact, blank lines dropped (they are not records).

    newline="" is load-bearing: universal-newline translation would turn a CRLF record
    into an LF one on the way back out, which would rewrite bytes we promised not to.
    """
    with open(path, encoding="utf-8", newline="") as fh:
        return [line for line in fh if line.strip()]


def union_lines(canon_lines: list[str], stray_lines: list[str]) -> tuple[list[str], list[str]]:
    """Multiset union. Returns (output_lines, stray_only_lines_appended)."""
    canon_counts = Counter(record_key(line) for line in canon_lines)
    seen: Counter[tuple[str, str]] = Counter()
    appended: list[str] = []
    for line in stray_lines:
        key = record_key(line)
        seen[key] += 1
        if seen[key] > canon_counts[key]:
            appended.append(line)
    return canon_lines + appended, appended


def verify_preserved(canon_lines: list[str], out_lines: list[str]) -> bool:
    """True when every pre-union canonical line survives, WITH its multiplicity."""
    before, after = Counter(canon_lines), Counter(out_lines)
    return all(after[line] >= n for line, n in before.items())


# --------------------------------------------------------------------------- guards

def probe_write_lock(path: Path) -> bool:
    """Best-effort: True when another process appears to hold `path` open for writing.

    Opening for append is the cheapest portable probe - on Windows a handle opened
    without FILE_SHARE_WRITE makes this raise. It can FALSE-GREEN when the holder did
    share write access, which is exactly why the session-id check is the load-bearing
    guard and this is only a further line of defence.
    """
    try:
        with open(path, "ab"):
            return False
    except OSError:
        return True


def newest_mtime(directory: Path) -> tuple[float, Path | None]:
    newest, which = 0.0, None
    if not directory.is_dir():
        return newest, which
    for entry in directory.iterdir():
        if not entry.is_file():
            continue
        mtime = entry.stat().st_mtime
        if mtime > newest:
            newest, which = mtime, entry
    return newest, which


def assert_safe(
    canon_dir: Path,
    stray_dir: Path,
    *,
    now: float,
    window: float = LIVE_WINDOW_S,
    lock_probe=probe_write_lock,
    self_session_id: str | None = None,
) -> None:
    """Raise Refusal if a live session is writing, or a target file is locked.

    Three checks, strongest first. `self_session_id` is the deterministic one and the
    mtime window is a backstop, NOT the other way round - see the session-id check below.
    """
    # 1. The running session's own transcript. Measured 2026-09-20: this session's
    #    transcript had last been flushed 353.8s ago while the session was plainly live,
    #    so the 120s mtime window below passes a live writer straight through. Claude Code
    #    batches flushes; the session id does not lie about liveness.
    if self_session_id:
        live = canon_dir / f"{self_session_id}.jsonl"
        if live.exists():
            raise Refusal(
                f"{live.name} is the RUNNING session's own transcript and it lives in the "
                "canonical store - this process is itself a live writer there. Re-run from "
                "a session whose transcript is not in this directory, or when none is open."
            )
    newest, which = newest_mtime(canon_dir)
    if which is not None and (now - newest) < window:
        raise Refusal(
            f"{which.name} in the canonical store was modified "
            f"{now - newest:.1f}s ago (window {window:.0f}s) - a LIVE session is writing "
            "there. Re-run when no session is open on this project."
        )
    for directory in (canon_dir, stray_dir):
        if not directory.is_dir():
            continue
        for entry in sorted(directory.iterdir()):
            if entry.is_file() and lock_probe(entry):
                raise Refusal(f"{entry.name} is locked / open for writing by another process.")


# --------------------------------------------------------------------------- plan

@dataclass
class FilePlan:
    name: str
    action: str                    # "union" | "copy" | "noop"
    canon_path: Path | None
    stray_path: Path
    canon_lines: list[str] = field(default_factory=list)
    out_lines: list[str] = field(default_factory=list)
    appended: int = 0

    @property
    def bytes_before(self) -> int:
        return self.canon_path.stat().st_size if self.canon_path and self.canon_path.exists() else 0

    @property
    def bytes_after(self) -> int:
        if self.action == "copy":
            return self.stray_path.stat().st_size
        return sum(len(line.encode("utf-8")) for line in self.out_lines)

    @property
    def backup_name(self) -> str:
        return self.name.split(".")[0] + ".canon.bak"


def plan(canon_dir: Path, stray_dir: Path) -> list[FilePlan]:
    """One FilePlan per file in the stray store. Canon-only files are left alone."""
    plans: list[FilePlan] = []
    for stray_path in sorted(stray_dir.iterdir()) if stray_dir.is_dir() else []:
        if not stray_path.is_file():
            continue
        canon_path = canon_dir / stray_path.name
        if not canon_path.exists():
            plans.append(FilePlan(stray_path.name, "copy", None, stray_path))
            continue
        if stray_path.suffix != ".jsonl":
            same = canon_path.read_bytes() == stray_path.read_bytes()
            plans.append(FilePlan(stray_path.name, "noop" if same else "copy", canon_path, stray_path))
            continue
        canon_lines = read_lines(canon_path)
        out_lines, appended = union_lines(canon_lines, read_lines(stray_path))
        plans.append(FilePlan(
            stray_path.name,
            "noop" if not appended else "union",
            canon_path,
            stray_path,
            canon_lines=canon_lines,
            out_lines=out_lines,
            appended=len(appended),
        ))
    return plans


# --------------------------------------------------------------------------- apply

def apply_plan(plans: list[FilePlan], backup_dir: Path, canon_dir: Path | None = None) -> list[FilePlan]:
    """Execute the plan. Backup first, then an atomic replace. Returns what changed."""
    changed = [p for p in plans if p.action in ("union", "copy")]
    if not changed:
        return []
    backup_dir.mkdir(parents=True, exist_ok=True)
    for fp in changed:
        if fp.action == "copy":
            target = (fp.canon_path or (canon_dir / fp.name if canon_dir else None))
            if target is None:
                raise ValueError(f"no canonical target for {fp.name}")
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists():
                shutil.copy2(target, backup_dir / fp.backup_name)
            tmp = target.with_suffix(target.suffix + ".uniontmp")
            shutil.copy2(fp.stray_path, tmp)
            os.replace(tmp, target)
            continue
        assert fp.canon_path is not None
        # BACKUP BEFORE THE REPLACE - the recovery path must exist before we mutate.
        shutil.copy2(fp.canon_path, backup_dir / fp.backup_name)
        tmp = fp.canon_path.with_suffix(fp.canon_path.suffix + ".uniontmp")
        tmp.write_text("".join(fp.out_lines), encoding="utf-8", newline="")
        os.replace(tmp, fp.canon_path)
    return changed


# --------------------------------------------------------------------------- cli

def _print_plan(plans: list[FilePlan], applying: bool) -> None:
    head = "APPLY" if applying else "DRY-RUN (nothing written; pass --apply to act)"
    print(f"lw_transcript_union - {head}")
    if not plans:
        print("  nothing to do: the stray store holds no files")
        return
    for fp in plans:
        before_lines = len(fp.canon_lines)
        after_lines = len(fp.out_lines)
        if fp.action == "union":
            print(f"  UNION {fp.name}")
            print(f"        lines {before_lines} -> {after_lines} (+{fp.appended} stray-only)")
            print(f"        bytes {fp.bytes_before} -> {fp.bytes_after}")
            print(f"        backup -> {fp.backup_name}")
        elif fp.action == "copy":
            print(f"  COPY  {fp.name}  ({fp.bytes_after} B, no canonical counterpart to merge)")
        else:
            print(f"  NOOP  {fp.name}  (already identical)")
    print("  the stray store is left in place, untouched.")


def _print_verification(changed: list[FilePlan]) -> None:
    print("VERIFICATION")
    ok = True
    for fp in changed:
        if fp.action == "copy":
            print(f"  {fp.name}: copied, {fp.bytes_after} B (no pre-union counterpart)")
            continue
        assert fp.canon_path is not None
        after = read_lines(fp.canon_path)
        preserved = verify_preserved(fp.canon_lines, after)
        ok = ok and preserved
        print(f"  {fp.name}: lines {len(fp.canon_lines)} -> {len(after)}, "
              f"bytes {fp.bytes_after} -> {fp.canon_path.stat().st_size}")
        print(f"    all pre-union canonical lines present: {'yes' if preserved else 'NO'}")
    print(f"  overall: {'OK' if ok else 'FAILED - restore from the backup dir'}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Union a split Claude transcript store, losslessly.")
    ap.add_argument("--apply", action="store_true", help="perform the union (default is a dry run)")
    ap.add_argument("--canon-dir", default=None, help="canonical store key directory")
    ap.add_argument("--stray-dir", default=None, help="stray store key directory")
    ap.add_argument("--backup-dir", default=str(DEFAULT_BACKUP_DIR))
    ap.add_argument("--window", type=float, default=LIVE_WINDOW_S,
                    help="live-session mtime window in seconds (do not weaken this)")
    ap.add_argument("--session-id", default=None,
                    help="running session id; defaults to $CLAUDE_CODE_SESSION_ID")
    args = ap.parse_args(argv)

    root = Path(os.path.expanduser("~/.claude/projects"))
    canon_dir = Path(args.canon_dir) if args.canon_dir else root / DEFAULT_CANON_KEY
    stray_dir = Path(args.stray_dir) if args.stray_dir else root / DEFAULT_STRAY_KEY
    backup_dir = Path(args.backup_dir)

    if not stray_dir.is_dir():
        print(f"stray store {stray_dir} does not exist - nothing to union.")
        return 0
    if not canon_dir.is_dir():
        print(f"REFUSE: canonical store {canon_dir} does not exist.")
        return 3

    import time
    session_id = args.session_id or os.environ.get("CLAUDE_CODE_SESSION_ID")
    refusal: Refusal | None = None
    try:
        assert_safe(canon_dir, stray_dir, now=time.time(), window=args.window,
                    self_session_id=session_id)
    except Refusal as exc:
        refusal = exc

    # The guard gates the APPLY, where the data risk is. A dry run writes nothing and so
    # cannot lose a byte - it stays usable as a preview and says an apply would refuse.
    if refusal is not None and args.apply:
        print(f"REFUSE (exit 3): {refusal}")
        print("This is the correct outcome while a session is open. Do NOT weaken the guard.")
        return 3

    plans = plan(canon_dir, stray_dir)
    _print_plan(plans, args.apply)
    if refusal is not None:
        print(f"  WOULD REFUSE on --apply (exit 3): {refusal}")
    if not args.apply:
        return 0
    changed = apply_plan(plans, backup_dir, canon_dir=canon_dir)
    _print_verification(changed)
    return 0


if __name__ == "__main__":
    sys.exit(main())
