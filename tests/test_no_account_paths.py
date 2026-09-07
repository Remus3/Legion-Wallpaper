"""No tracked file may carry a real account's Windows home path.

Sibling of `tests/test_no_secret_literals.py`, and deliberately the same shape:
sweep `git ls-files`, flag one narrow diagnostic pattern, prove every detector
arm FIRES before the clean result is trusted, and keep the exemption list short,
named, and self-checking.

THE RULE. LW has been PUBLIC under Apache-2.0 since 2026-08-01, so every tracked
byte is world-readable one push after it lands. A hard-coded `C:\\Users\\<real
account>\\...` in a docstring, a command doc or a config buys nothing that an
environment lookup does not, and it publishes the operator's account name plus
the machine's directory layout. Severity is hygiene and blast radius, not a
credential leak - the neighbouring guard is the one that proves no key is
tracked - but hygiene is exactly the class that only stays fixed if something
checks it.

WHY THE ACCOUNT SEGMENT, NOT THE WHOLE PATH. Flagging `C:\\Users\\` outright
would flag the placeholder spellings this repo needs in order to DOCUMENT the
rule - ROADMAP.md and CLAUDE.md both have to write the shape down to explain it.
So the sweep parses the account segment and asks one question: is this a
placeholder, or is it somebody's real login? That also means a path pasted from
a DIFFERENT machine is caught, which a literal ban on one account name would
miss - the fleet shares an operator and a note channel, and a path pasted into
the wrong tree is exactly the accident this catches.

WHY THESE EXEMPTIONS. `docs/_archive/**` and dated artifacts are the standing
sweep exclusions named in CLAUDE.md ("immutable history / non-source"), and
`docs/LEDGER.md` / `docs/history_notes.md` are append-only records of what was
true when written. Rewriting history to change an account name was considered
and REJECTED (ROADMAP, 2026-09-07): the two prior rewrites cost sha-maps that
every citing doc still needs, and a force-push does not purge GitHub-side
unreachable objects anyway. So the decision is fix-forward, and these files are
the recorded cost of that decision rather than an oversight.

TRACKEDNESS, NOT PRESENCE. The corpus is `git ls-files`. Untracked working
files, gitignored keys and the operator's own scratch are none of this guard's
business; "this repository publishes an account name" is a statement about what
is tracked.
"""
from __future__ import annotations

import re
import subprocess
from functools import lru_cache
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

# `C:\Users\NAME`, `C:/Users/NAME`, the JSON/Python-escaped `C:\\Users\\NAME`,
# and the Git-Bash `/c/Users/NAME`. The separator alternatives are spelled out
# rather than folded into a character class so a doubled backslash cannot be
# read as one separator plus a literal backslash starting the account segment.
_SEP = r"(?:\\\\|\\|/)"
ACCOUNT_PATH = re.compile(
    r"(?:[A-Za-z]:|/[a-z])" + _SEP + r"Users" + _SEP
    # A backtick can never be part of a Windows account name, so it is excluded
    # from the segment: prose that ends a code span right after the separator
    # (`C:\Users\`) names nobody, and reading the closing backtick as an account
    # was a real false positive on this file's own first run.
    + r"(?P<account>[^\\/\s\"'`<>|:*?,;)\]}]+|<[^>]*>)"
)

# Spellings that name NOBODY. `<account>` is what ROADMAP.md and the git hooks
# use when they have to write the shape down; the rest are the conventional
# stand-ins a doc or a test fixture reaches for. `Public` and `Default` are real
# Windows built-ins that identify no person. Anything outside this set is
# treated as somebody's login, which is the point: a path pasted from another
# machine in the fleet is caught too.
PLACEHOLDER_ACCOUNTS = frozenset({
    "<account>", "<user>", "<username>", "<name>", "<you>",
    "%USERNAME%", "$USER", "$env:USERNAME",
    "example", "operator", "runner", "user", "username",
    "Public", "Default",
    # An elided segment in prose, e.g. .gitignore's "personal corpus
    # (C:\\Users\\...\\Pictures, Desktop\\Found)". It names nobody by
    # construction, and spelling it any other way would make the comment worse.
    "...",
})

# Files whose content is immutable history or a dated artifact. Named by rule,
# not one by one, because the rule is the one already written in CLAUDE.md's
# "Standing sweep exclusions". `_would_be_exempt` is the single decision point
# so the arms below can drive it.
_APPEND_ONLY = {
    "docs/LEDGER.md",
    "docs/history_notes.md",
}
_DATED = re.compile(r"\d{4}-\d{2}-\d{2}")

SELF_EXEMPT = {
    "tests/test_no_account_paths.py",
    # Plants user-profile-shaped strings as the fixtures that prove the hand-off
    # write gate REDACTS them. Its job is to carry this pattern, so scrubbing it
    # would delete the test rather than fix anything. `test_no_secret_literals`
    # exempts this same file for the same reason, which is the precedent.
    "tests/test_handoff_write_gate.py",
}


def _would_be_exempt(rel: str) -> bool:
    """True for the recorded exceptions. One decision point, so it is testable."""
    if rel in SELF_EXEMPT or rel in _APPEND_ONLY:
        return True
    if rel.startswith("docs/_archive/"):
        return True
    return bool(_DATED.search(Path(rel).name))


@lru_cache(maxsize=1)
def _tracked_files() -> tuple[str, ...]:
    """Every tracked path, asked of GIT rather than of the disk."""
    out = subprocess.run(
        ["git", "ls-files", "-z"], cwd=REPO_ROOT,
        capture_output=True, text=True, check=True,
    ).stdout
    return tuple(sorted(p for p in out.split("\0") if p))


def scan_text(text: str) -> list[str]:
    """Offending fragments in `text`. Pure, so the mutation arms can drive it."""
    hits: list[str] = []
    for match in ACCOUNT_PATH.finditer(text):
        account = match.group("account")
        if account in PLACEHOLDER_ACCOUNTS:
            continue
        hits.append(f"account path: {match.group(0)[:60]}")
    return hits


def sweep() -> tuple[int, list[str]]:
    """`(files_scanned, offenders)`. The COUNT is returned so arms can assert it."""
    scanned = 0
    offenders: list[str] = []
    for rel in _tracked_files():
        if _would_be_exempt(rel):
            continue
        try:
            text = (REPO_ROOT / rel).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        scanned += 1
        for hit in scan_text(text):
            offenders.append(f"{rel}: {hit}")
    return scanned, offenders


def test_the_sweep_selects_a_real_corpus():
    """Guard the guard: a sweep that scanned nothing would pass vacuously."""
    scanned, _ = sweep()
    assert scanned > 200, f"only {scanned} tracked files scanned - the corpus is wrong"


def test_no_tracked_file_carries_an_account_path():
    _, offenders = sweep()
    assert not offenders, (
        f"{len(offenders)} tracked account-path hit(s):\n  "
        + "\n  ".join(offenders)
        + "\nResolve it from the environment instead (USERPROFILE / LOCALAPPDATA "
        "/ `~`), or write a placeholder from PLACEHOLDER_ACCOUNTS if the path is "
        "prose that has to show the shape. This repo is PUBLIC.")


@pytest.mark.parametrize("planted", [
    r"C:\Users\Administrator\AppData\Local\Programs\Python\Python314\python.exe",
    "C:/Users/Administrator/Pictures",
    r'"transcript_dir": "C:\\Users\\Administrator\\.claude"',
    "/c/Users/Administrator/Desktop",
    r"D:\Users\jsmith\Desktop",
])
def test_a_planted_account_path_is_caught(planted):
    """Every detector arm proven to FIRE before the clean result is trusted.

    A clean sweep and an unarmed sweep look identical. The last arm is a
    DIFFERENT drive and a DIFFERENT account on purpose: the rule is about the
    class, not about one machine's spelling of it.
    """
    assert scan_text(planted), f"the sweep missed a planted account path: {planted}"


@pytest.mark.parametrize("innocent", [
    r"PY=${PYTHON:-C:/Users/<account>/AppData/Local/.../python.exe}",
    r"%LOCALAPPDATA%\Programs\Python\Python314\python.exe",
    r'Path(os.environ["USERPROFILE"]) / "Pictures"',
    "~/.claude/projects/C--Legion-Wallpaper",
    r"C:\Users\%USERNAME%\Desktop",
    r"C:\Legion Wallpaper\tools\lw_facts.py",
    "C:/Users/example/Desktop/LW-X.txt",
    # A code span closed right after the separator. Names nobody.
    r"prose: banning `C:\Users\`, because the docs must show the shape",
])
def test_a_legitimate_neighbour_survives(innocent):
    """The placeholders and the env lookups must stay legal or the guard gets deleted."""
    assert not scan_text(innocent), f"false positive on: {innocent}"


def test_the_exemption_rule_is_the_one_claude_md_already_states():
    """The exemptions are a RULE, so the rule itself is what gets asserted."""
    assert _would_be_exempt("docs/_archive/RESTORATION_PLAN_v1.md")
    assert _would_be_exempt("docs/LEDGER.md")
    assert _would_be_exempt("docs/MCP_LIFT_DIVE_2026-08-01.md")
    assert _would_be_exempt("docs/superpowers/plans/2026-07-04-golden-set.md")
    # Live source is never exempt, whatever it is named.
    assert not _would_be_exempt("tools/truth_gate.py")
    assert not _would_be_exempt(".githooks/pre-commit")
    assert not _would_be_exempt("CLAUDE.md")
    assert not _would_be_exempt("docs/OPERATIONS.md")


@pytest.mark.parametrize("exempt", sorted(SELF_EXEMPT))
def test_every_exempt_file_would_trip_the_sweep(exempt):
    """An exemption that is no longer load-bearing is reported, not left standing."""
    text = (REPO_ROOT / exempt).read_text(encoding="utf-8")
    assert scan_text(text), (
        f"{exempt} no longer trips the detector, so its exemption is dead "
        "weight - remove the exemption or restore the planted fixtures")


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
