"""The tracked corpus, asked of git ONCE per test process (RRF-2.10).

MAIN REPO-REVIEW 2.10 (2026-10-08): the tree-wide hygiene guards each ran
their own `git ls-files -z` and re-read the tracked tree from disk (655
files, 9.66 MB). They now share this module: `tracked_files()` runs git once
and `read_bytes()` reads each file once, both cached for the process (one
xdist worker = one process). tests/conftest.py exposes the module as the
session-scoped `tracked_corpus` fixture.

TRACKEDNESS, NOT PRESENCE: the corpus is `git ls-files`, never a disk walk.
`read_text` matches `Path.read_text(encoding="utf-8")` byte for byte,
universal-newline translation included, so a guard that moved here sees the
same text it saw before.
"""
from __future__ import annotations

import subprocess
import sys
from functools import cache, lru_cache
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0) if sys.platform == "win32" else 0


@lru_cache(maxsize=1)
def tracked_files() -> tuple[str, ...]:
    """Every tracked path (repo-relative, forward slashes), sorted."""
    out = subprocess.run(["git", "ls-files", "-z"], cwd=REPO, capture_output=True,
                         check=True, stdin=subprocess.DEVNULL,
                         creationflags=_NO_WINDOW).stdout
    return tuple(sorted(p for p in out.decode("utf-8").split("\0") if p))


@cache
def read_bytes(rel: str) -> bytes:
    """The file's bytes, read once. OSError propagates (and is not cached)."""
    return (REPO / rel).read_bytes()


def read_text(rel: str, errors: str = "strict") -> str:
    """`Path.read_text(encoding="utf-8", errors=errors)`, from the cached bytes."""
    text = read_bytes(rel).decode("utf-8", errors)
    return text.replace("\r\n", "\n").replace("\r", "\n")
