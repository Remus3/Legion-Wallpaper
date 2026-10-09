# arch: on-disk file census for repo reviews | section=tools | frozen=no
"""lw_repo_inventory.py - count every file on disk in the repo, by class.

Built for the REPO-REVIEW ORDER (MAIN 2246 s8): the review accepts only when
the reviewed file count equals the on-disk count - tracked, untracked and
ignored alike, `.git` internals excluded. Large binary trees (images, venvs,
model weights) are reviewed as classes, so the census groups every file into
exactly one class keyed by (top-level folder, extension, git status).

Walk: os.walk from the repo root, symlinks / junctions NOT followed, any
directory named `.git` pruned. Status: `git ls-files -z` (tracked) and
`git ls-files -z --others --exclude-standard` (untracked); every other file
on disk is ignored.

Usage:
  python tools/lw_repo_inventory.py count            # one line: total
  python tools/lw_repo_inventory.py census [--json]  # status / top / classes
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_NOWIN = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def walk(root: Path) -> list[str]:
    """Every regular file under root as a posix relative path; .git pruned."""
    out: list[str] = []
    root = Path(root)
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        dirnames[:] = [d for d in dirnames if d != ".git"
                       and not os.path.islink(os.path.join(dirpath, d))]
        rel = Path(dirpath).relative_to(root).as_posix()
        for name in filenames:
            full = os.path.join(dirpath, name)
            if os.path.islink(full):
                continue
            out.append(name if rel == "." else f"{rel}/{name}")
    return out


def _git_list(root: Path, *args: str) -> set[str]:
    res = subprocess.run(["git", "-c", "core.quotepath=off", "ls-files", "-z", *args],
                         cwd=str(root), capture_output=True, check=True,
                         creationflags=_NOWIN)
    return {p for p in res.stdout.decode("utf-8", "replace").split("\0") if p}


def _ext(path: str) -> str:
    name = path.rsplit("/", 1)[-1]
    if "." not in name.lstrip("."):
        return "(none)"
    return "." + name.rsplit(".", 1)[-1].lower()


def census(root: Path = ROOT) -> dict:
    root = Path(root)
    files = walk(root)
    tracked = _git_list(root)
    untracked = _git_list(root, "--others", "--exclude-standard")
    by_status: Counter = Counter()
    by_top: Counter = Counter()
    classes: Counter = Counter()
    for f in files:
        status = ("tracked" if f in tracked
                  else "untracked" if f in untracked else "ignored")
        top = f.split("/", 1)[0] if "/" in f else "(root)"
        by_status[status] += 1
        by_top[top] += 1
        classes[(top, _ext(f), status)] += 1
    return {
        "total": len(files),
        "by_status": {k: by_status[k] for k in ("tracked", "untracked", "ignored")
                      if by_status[k]},
        "by_top": dict(by_top),
        "classes": [{"top": t, "ext": e, "status": s, "count": n}
                    for (t, e, s), n in sorted(classes.items())],
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("cmd", choices=("count", "census"))
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--root", default=str(ROOT))
    a = ap.parse_args(argv)
    c = census(Path(a.root))
    if a.cmd == "count":
        print(c["total"])
        return 0
    if a.json:
        print(json.dumps(c, indent=1, sort_keys=True))
        return 0
    print(f"total {c['total']}  " + "  ".join(f"{k} {v}" for k, v in c["by_status"].items()))
    for top, n in sorted(c["by_top"].items(), key=lambda kv: -kv[1]):
        print(f"{n:>8}  {top}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
