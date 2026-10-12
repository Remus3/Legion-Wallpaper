"""LEDGER-ASCII (session 73): CLAUDE.md says ASCII only, yet every existing
guard was a glyph BANLIST - smart quotes and dashes (test_smart_quote_hygiene,
tools/precommit_gate.py), U+2026 / U+00A0, and two mojibake signatures
(test_mojibake_hygiene). A UTF-8 e-acute (U+00E9) is on none of those lists,
so one sat in docs/LEDGER.md (an entry quoting French "configure") with every
guard green. This sweep is the allowlist the rule actually states: every
tracked authored text file is 7-bit ASCII.

Exclusions are CLAUDE.md's sweep exclusions, no wider: *.log*, any _archive/
directory, dated artifacts (a basename carrying a YYYY-MM-DD stamp), .jsonl
ledgers, binaries (by extension or a NUL byte), .pyc / .git; plus
ops/fleet_kit/, which is MAIN's bytes vendored verbatim and never edited here
(a non-ASCII byte there is reported to MAIN, not fixed locally).

A test that needs a non-ASCII character spells it with an escape
("\\u2610", "caf\\xe9"), so the source stays ASCII and the value is the same.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

import gitdep

ROOT = Path(__file__).resolve().parent.parent

_SKIP_EXT = {
    ".pyc", ".pyd", ".db", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico",
    ".zip", ".gz", ".exe", ".dll", ".lnk", ".woff", ".woff2", ".ttf", ".bin",
    ".so", ".o", ".onnx", ".pth", ".safetensors", ".pdf", ".jsonl",
}
_LOG_RE = re.compile(r"\.log(\.\d+)?$", re.IGNORECASE)
_DATED_RE = re.compile(r"\d{4}-\d{2}-\d{2}")
_SKIP_PREFIXES = ("ops/fleet_kit/",)


def skipped(rel: str) -> bool:
    """True for a path CLAUDE.md's ASCII sweep exclusions cover."""
    parts = rel.split("/")
    name = parts[-1]
    return (rel.startswith(_SKIP_PREFIXES)
            or "_archive" in parts or ".git" in parts or "__pycache__" in parts
            or bool(_LOG_RE.search(name)) or bool(_DATED_RE.search(name))
            or Path(name).suffix.lower() in _SKIP_EXT)


def non_ascii(data: bytes) -> tuple[int, int] | None:
    """(line, byte offset) of the first byte above 0x7F, or None. A NUL in the
    first 8 KiB marks a binary file, which is not text and is not swept."""
    if b"\0" in data[:8192]:
        return None
    m = re.search(rb"[\x80-\xff]", data)
    if m is None:
        return None
    return data.count(b"\n", 0, m.start()) + 1, m.start()


def _tracked() -> list[str]:
    out = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, capture_output=True,
                         check=True).stdout
    return [p for p in out.decode("utf-8").split("\0") if p]


def test_the_rule_flags_a_lone_e_acute_that_every_banlist_missed():
    assert non_ascii("a configur\u00e9 b\n".encode("utf-8")) == (1, 10)
    assert non_ascii(b"plain\nascii\n") is None
    assert non_ascii(b"\0\xff binary") is None


def test_the_exclusions_are_claude_mds_and_no_wider():
    for rel in ("logs/2026-10-12.log", "logs/x.log.3", "docs/_archive/a.md",
                "docs/WIKI_SWAP_22_2026-08-01.md", "ops/loop/control/x.jsonl",
                "ops/fleet_kit/fleet_headless.py", "a/__pycache__/m.pyc"):
        assert skipped(rel), rel
    for rel in ("docs/LEDGER.md", "ROADMAP.md", "CLAUDE.md", "LW-NEXT-SESSION.txt",
                "tests/test_lw_checklist.py", "tools/lw_kit_adopt.py", "x.ps1"):
        assert not skipped(rel), rel


@gitdep.requires_git
def test_every_tracked_authored_text_file_is_7bit_ascii():
    files = [p for p in _tracked() if not skipped(p)]
    assert len(files) > 100, "the sweep selected almost nothing - it would pass vacuously"
    bad = []
    for rel in files:
        try:
            hit = non_ascii((ROOT / rel).read_bytes())
        except OSError:
            continue  # tracked but deleted in the working tree
        if hit:
            bad.append(f"{rel}:{hit[0]} (byte {hit[1]})")
    assert not bad, "non-ASCII in authored files (CLAUDE.md: ASCII only): " + ", ".join(bad)
