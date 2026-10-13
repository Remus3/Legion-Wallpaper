"""Sibling trees by CODE, never by display name (RRF-3.2, MAIN README-AUDIT 3.2).

A sibling tree is named by its channel code (docs/CHANNEL.md section 0) in
every tracked file outside docs/_archive/. Its display name differs per tree
and per machine and, in a PUBLIC repo, publishes the machine's layout.

HASH-PINNED NAME LIST. The list cannot be tracked as text - it would be the
thing it forbids - so PINS holds sha256 over each name's squashed KEY
(lowercase, ASCII alphanumerics only), grouped by code. A retired or former
name stays pinned: it still leaks.

MATCH RULE. One token ([A-Za-z0-9]+) or two adjacent tokens joined by one
space, "-" or "_", whose squashed key hashes to a pin, in any case. The one
exemption is NOUN_PINS: two names are also ordinary English ("a research
s...", a painted moon), so those two count only with an UPPERCASE first
letter (LEDGER 2108 recorded the noun false positive once already).

    python tools/sibling_names.py sweep         # exit 1 on any hit (pre-push)
    python tools/sibling_names.py key "<name>"  # print a new name's pin

`sibling_dir(code)` finds a sibling checkout beside this one by key, so code
that needs a sibling's directory never spells its name either.
"""
from __future__ import annotations

import hashlib
import os
import re
import subprocess
import sys
from collections.abc import Callable, Iterable
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

PINS: dict[str, frozenset[str]] = {
    "RC": frozenset({"31b7b4524353f6bc4b537721762098e03e0fcf6adf806592800e20b6737e0ead",
                     "9f54c11a7b6498f3067c45cc93cf1f8b13fac99d9945898bdbe21238285126e0"}),
    "RSC": frozenset({"7ced9b5c15ea13387768712f866b1d8eb356fc04fb5229d614d4c2439a7fa028"}),
    "RM": frozenset({"7090b0d1264d1c015c5deddfb6793ffb4d6ff97bc5bff08720b1dd88c3c9a4b8"}),       # archived 2026-09-06
    "LL": frozenset({"f36ea92bcaacd356443d9cc3bc2f4c1affd1781606835b01d4ed6f375e8ffb11"}),
    "CS": frozenset({"fb2bf312602976940589568006c0f841640e0ba9c077554bef1a37a6572f10ba"}),
    "SS": frozenset({"df5e69a6000eaee68a8f7f7baa620ac6401fef79ba563ff7acec9d4ecef7888b"}),
    "EW": frozenset({"47771beb620894b44e587c56c3703bea99675b822729749e2dd25bc78e674fd5"}),
}
_BY_HASH = {h: code for code, hs in PINS.items() for h in hs}
# Pins whose name is also an ordinary English noun phrase: these alone need an
# UPPERCASE first letter to count (LEDGER 2108 - the noun matched a tree name).
NOUN_PINS = frozenset({
    "df5e69a6000eaee68a8f7f7baa620ac6401fef79ba563ff7acec9d4ecef7888b",
    "7090b0d1264d1c015c5deddfb6793ffb4d6ff97bc5bff08720b1dd88c3c9a4b8",
})

# Never swept: the archive (dated history, kept as written) and the
# append-only machine ledgers / logs (CLAUDE.md sweep exclusions).
SKIP_PREFIXES = ("docs/_archive/",)
SKIP_SUFFIXES = (".jsonl", ".log")

_TOKEN = re.compile(r"[A-Za-z0-9]+")
_JOIN = (" ", "-", "_")


def key(name: str) -> str:
    """The squashed key: lowercase ASCII alphanumerics only."""
    return re.sub(r"[^a-z0-9]", "", name.lower())


def _code(text: str) -> str | None:
    digest = hashlib.sha256(key(text).encode("ascii", "ignore")).hexdigest()
    if digest in NOUN_PINS and not text[:1].isupper():
        return None
    return _BY_HASH.get(digest)


def code_for(name: str) -> str | None:
    """The code whose pin `name` hashes to, or None."""
    return _code(name)


def finditer(text: str) -> Iterable[tuple[int, int, str]]:
    """(start, end, code) for every pinned display name in `text`."""
    toks = list(_TOKEN.finditer(text))
    i = 0
    while i < len(toks):
        t = toks[i]
        nxt = toks[i + 1] if i + 1 < len(toks) else None
        if nxt is not None and text[t.end():nxt.start()] in _JOIN:
            code = _code(t.group(0) + nxt.group(0))
            if code:
                yield t.start(), nxt.end(), code
                i += 2
                continue
        code = _code(t.group(0))
        if code:
            yield t.start(), t.end(), code
        i += 1


def find(text: str) -> list[tuple[int, str]]:
    """[(1-based line, code)] for every pinned display name in `text`."""
    return [(text.count("\n", 0, s) + 1, c) for s, _e, c in finditer(text)]


def skipped(rel: str) -> bool:
    return rel.startswith(SKIP_PREFIXES) or rel.endswith(SKIP_SUFFIXES)


def sweep(files: Iterable[str], read: Callable[[str], bytes]) -> list[tuple[str, int, str]]:
    """[(rel, line, code)] over `files` (repo-relative), skipping the archive,
    the append-only ledgers and binaries (a NUL in the first 8 KiB)."""
    hits = []
    for rel in files:
        if skipped(rel):
            continue
        data = read(rel)
        if b"\0" in data[:8192]:
            continue
        text = data.decode("utf-8", "replace")
        hits += [(rel, ln, c) for ln, c in find(text)]
    return hits


def siblings_dir() -> Path:
    """The directory sibling checkouts sit in: `LW_SIBLINGS_DIR`, else this
    checkout's parent (same seam as tools/lw_paths.sibling_repo)."""
    base = os.environ.get("LW_SIBLINGS_DIR")
    return Path(base) if base else ROOT.parent


def sibling_dir(code: str) -> Path:
    """`code`'s checkout beside this one, found by KEY, so a sibling is located
    without its name being spelled. A git checkout wins over a plain directory.
    None found: a path under the siblings dir that does not exist (a CI runner)."""
    pins = PINS[code]
    base = siblings_dir()
    found = []
    try:
        entries = sorted(base.iterdir())
    except OSError:
        entries = []
    for entry in entries:
        digest = hashlib.sha256(key(entry.name).encode("ascii", "ignore")).hexdigest()
        if digest in pins and entry.is_dir():
            found.append(entry)
    for entry in found:
        if (entry / ".git").exists():
            return entry
    return found[0] if found else base / f"<{code}>"


def _tracked() -> list[str]:
    out = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, capture_output=True,
                         check=True, stdin=subprocess.DEVNULL,
                         creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)).stdout
    return [p for p in out.decode("utf-8").split("\0") if p]


def _read(rel: str) -> bytes:
    try:
        return (ROOT / rel).read_bytes()
    except OSError:
        return b""


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if args[:1] == ["key"] and len(args) == 2:
        print(hashlib.sha256(key(args[1]).encode("ascii", "ignore")).hexdigest())
        return 0
    if args == ["sweep"]:
        hits = sweep(_tracked(), _read)
        for rel, ln, code in hits:
            print(f"{rel}:{ln}: sibling display name - write the code {code}")
        if hits:
            print(f"sibling_names: {len(hits)} hit(s); docs/_archive/ is the only "
                  "place a display name may stay (RRF-3.2)")
        return 1 if hits else 0
    print("usage: sibling_names.py sweep | key <name>", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
