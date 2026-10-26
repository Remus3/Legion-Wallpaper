"""No tracked text file may carry an absolute machine path (PUBPATH).

THE RULE. MAIN ORDER PUBPATH (2026-10-15): this repo is PUBLIC, so a tracked
`<drive>:\\...` path publishes the machine's directory layout one push after it
lands. Tools resolve their roots at run time (`tools/lw_paths.py`: repo_root(),
tools_dir(), user_home(), local_app_data()); prose uses a placeholder
(`<repo>`, `<RC>`, `%SystemDrive%\\Tools`, `%ProgramData%`, `%ProgramFiles%`,
`%USERPROFILE%`, `%LOCALAPPDATA%`).

WHAT IS FLAGGED. An absolute drive-letter path - one letter, a colon, then a
backslash, a doubled (escaped) backslash or a forward slash - that does not
follow a letter or digit (so `https://`, `HKCU:\\` and `$env:X\\` are not
paths), plus the Git-Bash user-profile spelling `/c/Users/`. Wider than its two
siblings on purpose: `tests/test_no_account_paths.py` parses only the account
segment of `<drive>:\\Users\\<name>`, and `tests/test_no_hardcoded_c_paths.py`
only LW's own root in code files. This one is the whole class, every text file.

THE ALLOWLIST is per prefix, short, and every entry says why and must still be
load-bearing (an entry with no hits fails `test_every_allowlist_entry_is_load_bearing`).
History is allowlisted rather than rewritten (MAIN's decision: no history
rewrite, the paths are low-sensitivity).
"""
from __future__ import annotations

import re
from pathlib import Path

import gitdep
import tracked_corpus

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

ABSOLUTE_PATH = re.compile(
    r"(?<![A-Za-z0-9_])[A-Za-z]:(?:\\\\|\\|/)"
    r"|(?<![A-Za-z0-9_.])/[a-z]/Users/")

# Path prefix (directory ends in "/") or exact file -> reason.
ALLOWLIST: dict[str, str] = {
    "docs/_archive/": "archived history, immutable (CLAUDE.md sweep exclusion)",
    "docs/LEDGER.md": "append-only ledger: records where the tree lived when written",
    "docs/history_notes.md": "append-only history record",
    "docs/claude-md-history.md": "verbatim pre-condense CLAUDE.md text, a record",
    "scratchpad/": "dated one-off artifacts, never rewritten",
    "tests/": "fixtures: drive-path strings are the input under test",
    "ops/loop/slots.py": "byte-identical with RC by contract (DEFAULT_ROOT); never edited alone",
}


def _allowed(rel: str) -> bool:
    return any(rel == k or (k.endswith("/") and rel.startswith(k)) for k in ALLOWLIST)


def scan_text(text: str) -> list[int]:
    """1-based line numbers carrying an absolute machine path. Pure."""
    return [i for i, line in enumerate(text.splitlines(), 1)
            if ABSOLUTE_PATH.search(line)]


def _text(rel: str) -> str | None:
    try:
        raw = tracked_corpus.read_bytes(rel)
    except OSError:
        return None
    if b"\0" in raw[:8192]:
        return None
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return None


def sweep(include_allowed: bool = False) -> tuple[int, dict[str, list[int]]]:
    scanned = 0
    hits: dict[str, list[int]] = {}
    for rel in tracked_corpus.tracked_files():
        if not include_allowed and _allowed(rel):
            continue
        text = _text(rel)
        if text is None:
            continue
        scanned += 1
        lines = scan_text(text)
        if lines:
            hits[rel] = lines
    return scanned, hits


@gitdep.requires_git
def test_the_sweep_selects_a_real_corpus():
    scanned, _ = sweep()
    assert scanned > 200, f"only {scanned} tracked text files scanned - corpus wrong"


@gitdep.requires_git
def test_no_tracked_file_carries_an_absolute_machine_path():
    _, hits = sweep()
    rows = [f"{rel}:{n}" for rel, lines in sorted(hits.items()) for n in lines]
    assert not rows, (
        f"{len(rows)} absolute machine path line(s) in tracked files:\n  "
        + "\n  ".join(rows[:80])
        + "\nResolve the path at run time (tools/lw_paths.py) or write a "
        "placeholder (<repo>, %SystemDrive%\\Tools, %ProgramData%, ...). PUBLIC repo.")


@gitdep.requires_git
def test_every_allowlist_entry_is_load_bearing():
    _, hits = sweep(include_allowed=True)
    dead = [k for k in ALLOWLIST
            if not any(rel == k or (k.endswith("/") and rel.startswith(k)) for rel in hits)]
    assert not dead, f"allowlist entries with no hits (remove them): {dead}"


@pytest.mark.parametrize("planted", [
    r"repo lives at E:\Legion Wallpaper",
    "File Explorer > E:/Legion Wallpaper/images/0.Originals",
    r'"root": "C:' r'\\Legion Wallpaper\\pipeline"',  # split: hardcoded-root guard
    r"D:\Sidecars\LW",
    "[x](file:///C:/Legion%20Wallpaper/images/a.png)",
    r"pythonw (C:\Tools\lw-clean\venv)",
    "cd /c/Users/example/Desktop",
    r"default C:\ProgramData\lw-loop\slots",
])
def test_a_planted_absolute_path_is_caught(planted):
    assert scan_text(planted), f"the sweep missed: {planted}"


@pytest.mark.parametrize("innocent", [
    "https://example.com/a/b",
    r"<repo>\tools\lw_monitor.py",
    r"%SystemDrive%\Tools\lw-clean\venv",
    r"%ProgramData%\lw-loop\slots",
    r"Get-Item HKCU:\Software\X",
    r"$env:LOCALAPPDATA\Programs",
    "[x](../../../images/a.png)",
    "family=Inter:wght@400",
    "at 23:31Z the check ran",
    r"<drive>:\\x and <drive>:/x differ",
    "/e/ is not flagged without /Users/",
])
def test_a_legitimate_neighbour_survives(innocent):
    assert not scan_text(innocent), f"false positive on: {innocent}"


def test_the_allowlist_is_short():
    assert len(ALLOWLIST) <= 8, "the allowlist grew - scrub instead of exempting"
