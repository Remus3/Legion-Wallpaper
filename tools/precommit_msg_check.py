"""
tools/precommit_msg_check.py - commit-msg hook (Conventional Commits).

Ported 1:1 from RC scripts/precommit_msg_check.py (Phase 7) -
make Conventional Commits subject lines mechanical.

Validates the staged commit's subject line against the Conventional Commits
shape: `<type>(<scope>)?!?: <description>`. This hook prevents drift from
that convention.

The hook only inspects the SUBJECT line. Body and trailers are unrestricted.
Auto-generated subjects (Revert / fixup! / squash! / Reapply / amend!) are
skipped. Merge commits are NOT skipped (MAIN PUBREPO order 2b, 2026-10-15):
a merge commit (MERGE_HEAD present) or any subject starting with `merge` must
read exactly `merge: <topic>`, and a merge subject may not name an agent
worktree (worktree-agent-<hex>, agent-<hex>, .claude/worktrees). Git's default
`Merge branch '...'` subject is therefore refused: re-commit with -m.

Bypass with `--no-verify` if absolutely necessary; please don't make a habit
of it.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

TYPES = (
    "feat",
    "fix",
    "docs",
    "style",
    "refactor",
    "perf",
    "test",
    "build",
    "ci",
    "chore",
    "revert",
)

# <type>(<optional scope>)<optional !>: <space><non-space>...
SUBJECT_RE = re.compile(
    rf"^(?:{'|'.join(TYPES)})(?:\([\w./\- ]+\))?!?:\s+\S",
)

SKIP_PREFIXES = (
    "Revert ",
    "Reapply ",
    "fixup!",
    "squash!",
    "amend!",
)

SOFT_LINE_LIMIT = 100

MERGE_TEMPLATE = "merge: <topic>"
MERGE_SUBJECT_RE = re.compile(r"^merge: \S")
WORKTREE_NAME_RE = re.compile(
    r"worktree-agent-[0-9a-f]+|\bagent-[0-9a-f]{8,}|\.claude[\\/]worktrees",
    re.IGNORECASE,
)


def is_merging(repo: Path | None = None) -> bool:
    """True while a merge commit is being recorded (MERGE_HEAD exists)."""
    import subprocess
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--git-path", "MERGE_HEAD"],
            cwd=str(repo) if repo else None, capture_output=True, text=True,
            check=True, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return False
    path = Path(out)
    if not path.is_absolute() and repo is not None:
        path = Path(repo) / path
    return path.is_file()


def validate(subject: str, merging: bool = False) -> tuple[bool, str | None]:
    """Return (ok, error_message). error_message is None on success."""
    if not subject.strip():
        return False, "empty subject line"
    if merging or subject.startswith("Merge ") or subject.lower().startswith("merge"):
        if not MERGE_SUBJECT_RE.match(subject):
            return False, f"merge subject must read {MERGE_TEMPLATE}"
        if WORKTREE_NAME_RE.search(subject):
            return False, "merge subject names an agent worktree"
        return True, None
    if any(subject.startswith(p) for p in SKIP_PREFIXES):
        return True, None
    if not SUBJECT_RE.match(subject):
        return False, "subject does not match <type>(<scope>)?: <description>"
    return True, None


def _read_subject(msg_file: Path) -> str:
    raw = msg_file.read_text(encoding="utf-8", errors="replace")
    for line in raw.splitlines():
        if line.startswith("#"):
            continue
        if not line.strip():
            continue
        return line.rstrip()
    return ""


def main() -> int:
    if len(sys.argv) < 2:
        print("commit-msg: missing path argument", file=sys.stderr)
        return 1
    msg_file = Path(sys.argv[1])
    if not msg_file.exists():
        print(f"commit-msg: file not found: {msg_file}", file=sys.stderr)
        return 1

    subject = _read_subject(msg_file)
    ok, err = validate(subject, merging=is_merging())
    if not ok:
        print(
            "commit-msg: subject line rejected.\n"
            f"  reason:   {err}\n"
            f"  got:      {subject!r}\n"
            "  expected: <type>(<scope>)?: <description>\n"
            f"  types:    {', '.join(TYPES)}\n"
            "  example:  feat(tools): add commit-msg subject gate\n"
            "Bypass with --no-verify if absolutely necessary.",
            file=sys.stderr,
        )
        return 1

    if len(subject) > SOFT_LINE_LIMIT:
        # Warn-only: don't block, just nudge.
        print(
            f"commit-msg: subject is {len(subject)} chars (>{SOFT_LINE_LIMIT}); "
            "consider tightening.",
            file=sys.stderr,
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
