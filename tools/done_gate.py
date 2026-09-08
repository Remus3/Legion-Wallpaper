#!/usr/bin/env python3
r"""done_gate: prove the /done gate graded the exact tree that gets pushed.

# arch: binding end-of-session gate - asserts gate-tree == pushed-tree

WHY THIS EXISTS. CS found it on 2026-09-07 as a pre-push RACE: its hook graded
one sha while the remote ended at another, so a commit shipped that no suite had
seen. LW has no pre-push hook, so LW cannot have that race - LW has the same
hole in a WORSE form, because it is not a race at all. It is the documented
order of the ritual: run the full suite, THEN edit ROADMAP + LEDGER + WAKEUP,
THEN commit everything and push. Every session shipped living-doc edits the
graded run never saw, deterministically, and CI catching nothing was luck.

The fix is ordering, and ordering alone is a sentence in a markdown file that
nothing checks. This module is the assertion that makes the ordering provable:

  bind         the tree is clean at gate time, the checks run against it, the
               tree did not move WHILE they ran, and the graded sha is recorded
  verify-push  the sha the remote now carries is that same graded sha

The receipt is the join between the two halves. It lives under `ops/runtime/`
(gitignored, so writing it cannot dirty the very tree it is grading) and it is
written ATOMICALLY per the CLAUDE.md hard rule - a reader may poll mid-write.

WHAT "CLEAN" MEANS HERE. `git status --porcelain` and not `git diff HEAD`:
the acceptance line names `git diff HEAD`, but that is a SUBSET. It misses an
untracked authored file - exactly the shape of a new test module a session just
wrote and has not staged, which would be graded by the local run and then never
pushed. Ignored files are excluded (no `--ignored`), so runtime droppings and
the receipt itself stay invisible.

THE REMOTE SHA IS ASKED OF THE REMOTE. `git rev-parse origin/main` reads a
local cache that a failed push leaves stale, which would make this gate agree
with itself about a push that never landed. `git ls-remote` asks the server.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

# CREATE_NO_WINDOW: 0 on non-Windows so the module still imports/tests in CI.
# Windows-only flag; every spawn carries it (no console flash on Legion).
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_RECEIPT = ROOT / "ops" / "runtime" / "done_gate.json"

# The checks the binding gate runs. Kept as argv lists, not a shell string, so
# the tests can substitute a trivial one and the real thing cannot word-split.
DEFAULT_CHECKS: list[list[str]] = [
    [sys.executable, "-m", "ruff", "check", "."],
    [sys.executable, "-m", "pytest", "tests/", "-q"],
    [sys.executable, "tools/drift_guard.py"],
]


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True, text=True, errors="replace", creationflags=NO_WINDOW,
    )


def head_sha(repo: Path) -> str:
    """Full sha of HEAD, or an empty string when there is no commit yet."""
    r = _git(repo, "rev-parse", "HEAD")
    return r.stdout.strip() if r.returncode == 0 else ""


def tree_dirt(repo: Path) -> list[str]:
    """Porcelain lines for everything git would refuse to call clean.

    Superset of `git diff HEAD`: staged, unstaged AND untracked. Ignored files
    are left out, which is what keeps the receipt from dirtying its own tree.
    """
    r = _git(repo, "status", "--porcelain")
    return [ln for ln in r.stdout.splitlines() if ln.strip()]


def stash_depth(repo: Path) -> int:
    """How many stash entries exist. Recorded, never fatal.

    A stash does not change the tree being graded, so it cannot break the
    property. It is worth writing down anyway: a session that stashed its work
    is a session whose author believes something is still outstanding.
    """
    r = _git(repo, "stash", "list")
    return len([ln for ln in r.stdout.splitlines() if ln.strip()])


def remote_head_sha(repo: Path, remote: str, branch: str) -> str:
    """Ask the REMOTE what it carries. Empty when unreachable or unreadable."""
    r = _git(repo, "ls-remote", remote, f"refs/heads/{branch}")
    if r.returncode != 0:
        return ""
    for ln in r.stdout.splitlines():
        parts = ln.split()
        if len(parts) == 2:
            return parts[0].strip()
    return ""


def write_receipt(path: Path, data: dict) -> None:
    """Atomic write - a consumer may poll mid-write (CLAUDE.md hard rule)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(data, indent=2) + "\n", encoding="ascii")
    tmp.replace(path)


def read_receipt(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="ascii"))
    except (OSError, ValueError):
        return None


def bind(repo: Path, receipt: Path, checks: list[list[str]] | None = None,
         verbose: bool = True) -> int:
    """Grade a clean tree and record which sha was graded.

    Exit 2 = the ordering property is broken (dirty tree, or the tree moved
    while the checks ran). Exit 1 = the tree was gradeable and a check failed.
    Only exit 0 licenses the push.
    """
    checks = DEFAULT_CHECKS if checks is None else checks

    dirt = tree_dirt(repo)
    if dirt:
        if verbose:
            print("done_gate: REFUSED - tree is dirty at gate time, so the run "
                  "would grade something other than what gets pushed:")
            for ln in dirt[:20]:
                print(f"  {ln}")
            if len(dirt) > 20:
                print(f"  ... and {len(dirt) - 20} more")
            print("done_gate: commit (or discard) every authored edit FIRST, "
                  "then re-run the gate. That is the whole point of the gate.")
        return 2

    graded = head_sha(repo)
    if not graded:
        if verbose:
            print("done_gate: REFUSED - no HEAD commit to grade")
        return 2

    results = []
    failed = False
    for cmd in checks:
        r = subprocess.run(cmd, cwd=str(repo), creationflags=NO_WINDOW)
        results.append({"cmd": cmd, "returncode": r.returncode})
        if verbose:
            print(f"done_gate: check {' '.join(cmd)} -> {r.returncode}")
        if r.returncode != 0:
            failed = True

    # The tree must not have moved WHILE the checks ran. This is CS's race, and
    # it is the one failure the pre-run check above cannot see.
    after_dirt = tree_dirt(repo)
    after_head = head_sha(repo)
    if after_dirt or after_head != graded:
        if verbose:
            print("done_gate: REFUSED - the tree MOVED while the checks ran "
                  f"(head {graded[:12]} -> {after_head[:12]}, "
                  f"{len(after_dirt)} dirty path(s)); the result grades a tree "
                  "that no longer exists")
        return 2

    write_receipt(receipt, {
        "graded_sha": graded,
        "clean": True,
        "stash_depth": stash_depth(repo),
        "checks": results,
        "passed": not failed,
        "bound_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    })
    if failed:
        if verbose:
            print(f"done_gate: RED on {graded[:12]} - do not push")
        return 1
    if verbose:
        print(f"done_gate: GREEN and BOUND to {graded[:12]} - push this sha, "
              "and author nothing before you do")
    return 0


def verify_push(repo: Path, receipt: Path, remote: str, branch: str,
                verbose: bool = True) -> int:
    """Assert the remote now carries exactly the sha the gate graded."""
    data = read_receipt(receipt)
    if data is None:
        if verbose:
            print(f"done_gate: REFUSED - no readable receipt at {receipt}; "
                  "the gate never bound, so nothing proves what was graded")
        return 2
    graded = str(data.get("graded_sha") or "")
    if not data.get("passed"):
        if verbose:
            print(f"done_gate: REFUSED - receipt for {graded[:12]} is RED")
        return 2

    now = head_sha(repo)
    if now != graded:
        if verbose:
            print(f"done_gate: REFUSED - HEAD is {now[:12]} but the gate graded "
                  f"{graded[:12]}; work landed after the gate and was never graded")
        return 2

    pushed = remote_head_sha(repo, remote, branch)
    if not pushed:
        if verbose:
            print(f"done_gate: REFUSED - could not read {remote}/{branch} from "
                  "the remote itself")
        return 2
    if pushed != graded:
        if verbose:
            print(f"done_gate: REFUSED - {remote}/{branch} is {pushed[:12]} but "
                  f"the gate graded {graded[:12]}; the pushed tree is ungraded")
        return 2

    if verbose:
        print(f"done_gate: VERIFIED - {remote}/{branch} = HEAD = graded "
              f"{graded[:12]}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="binding /done gate")
    ap.add_argument("mode", choices=("bind", "verify-push"))
    ap.add_argument("--repo", default=str(ROOT))
    ap.add_argument("--receipt", default=str(DEFAULT_RECEIPT))
    ap.add_argument("--remote", default="origin")
    ap.add_argument("--branch", default=None, help="default: the current branch")
    ap.add_argument("--skip-checks", action="store_true",
                    help="bind the sha without re-running the checks; for "
                         "wiring probes only, never for a real /done")
    a = ap.parse_args(argv)

    repo = Path(a.repo).resolve()
    receipt = Path(a.receipt)
    if a.mode == "bind":
        return bind(repo, receipt, checks=[] if a.skip_checks else None)

    branch = a.branch
    if not branch:
        r = _git(repo, "rev-parse", "--abbrev-ref", "HEAD")
        branch = r.stdout.strip() or "main"
    return verify_push(repo, receipt, a.remote, branch)


if __name__ == "__main__":
    raise SystemExit(main())
