"""No tracked file may carry an API key or token as a literal.

Ported from Resin Compute's `tests/test_no_secret_literals.py`, delivered
verbatim to `moon_sync_inbox/from-RSC-verbatim/` and credited. RSC's payload was
scrubbed before it was sent - unlike the drop that had to be pulled the same
night - so this port carries RSC's shape and LW's specifics.

THE RULE, operator instruction 2026-09-06: every API key on this machine lives
in a MACHINE-level environment variable, and no repository in the fleet carries
one inline. LW's own keys sit in gitignored `API-Key-*.txt` files at the repo
root. This guard is the half that keeps the property true after a sweep, and it
matters more here than in a private tree: LW has been PUBLIC under Apache-2.0
since 2026-08-01, so the window between a committed literal and a world-readable
one is a single push.

WHY A NAIVE "LONG RANDOM STRING" RULE IS THE WRONG SHAPE - RSC's argument,
which holds identically here. This tree is full of legitimate high-entropy
literals: `tests/test_loop_concurrency.py` pins sha256 digests of the shared
governor files, and those pins are the entire mechanism by which three
repositories prove they carry identical bytes. A guard that flagged them would
be deleted inside a day, and deleting a guard is how a property stops being
checked. So the sweep looks for the two shapes that are diagnostic of a SECRET
and never of a digest:

  1. A VENDOR-PREFIXED TOKEN - `sk-ant-`, `ghp_`, `AIza`, `RGAPI-`. A hash never
     carries a vendor prefix.
  2. A KNOWN SECRET NAME BOUND TO A LITERAL. The NAME is the evidence; the
     value's entropy is irrelevant.

Binding one of those names to an ENV LOOKUP is the correct destination and stays
legal. The point of the rule is to move secrets into the environment, so the
guard must not punish the place they were moved to.

TRACKEDNESS, NOT PRESENCE. The corpus is `git ls-files`, not a disk walk: LW's
live keys sit in gitignored files by design, and "this repository carries a
secret" is a statement about what is tracked. A disk walk would flag the correct
arrangement and teach everyone to ignore the guard.
"""
from __future__ import annotations

import re
import subprocess
from functools import lru_cache
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

# Vendor prefixes that identify a real credential. RGAPI- is the Riot key shape
# and stays in the set even though LW does not use one: the five repos on this
# box share an operator, and a key pasted into the wrong tree is exactly the
# accident this catches.
VENDOR_TOKEN = re.compile(
    r"(?:sk-ant-[A-Za-z0-9_\-]{16,}"
    r"|sk-[A-Za-z0-9]{20,}"
    r"|ghp_[A-Za-z0-9]{30,}"
    r"|github_pat_[A-Za-z0-9_]{30,}"
    r"|AIza[A-Za-z0-9_\-]{30,}"
    r"|RGAPI-[0-9a-f\-]{30,}"
    r"|xox[bapsr]-[A-Za-z0-9\-]{20,})"
)

# The secret-bearing names in use on this machine, plus LW's own two vendors.
# Held as a literal set rather than read from the live environment: a guard that
# asked the environment would go SILENT on a machine where the variables are not
# set, which is every CI runner and every fresh clone.
SECRET_NAMES = (
    "ANTHROPIC_API_KEY",
    "ANTHROPIC_USAGE_KEY",
    "GEMINI_API_KEY",
    "NIMBLE_API_KEY",
    "RIOT_API_KEY",
    "GITHUB_PERSONAL_ACCESS_TOKEN",
    "DEVIANTART_CLIENT_SECRET",
    "SAUCENAO_API_KEY",
)

# `NAME = "value"` / `"NAME": "value"` / `NAME=value`. Length is deliberately not
# part of the test: a short value bound to one of these names is either a secret
# or a placeholder, and a placeholder should be an env reference too.
SECRET_BINDING = re.compile(
    r"(?:" + "|".join(SECRET_NAMES) + r")"
    r"\"?\s*[:=]\s*"
    r"(?P<value>\"[^\"]*\"|'[^']*'|[^\s,}]+)"
)

# Referencing the environment is the CORRECT pattern and stays legal.
ENV_REFERENCE = re.compile(
    r"(?:os\.environ|getenv|GetEnvironmentVariable|\$env:|\$\{?[A-Z_]+\}?|%[A-Z_]+%"
    r"|secrets\.|vars\.|MOVED-TO-|<[^>]*>|xxx|XXX|placeholder|PLACEHOLDER"
    # A bare `$name` is a VARIABLE, never a literal. `tools/gemini_audit.ps1`
    # reads the key with GetEnvironmentVariable and re-exports it as
    # `$env:GEMINI_API_KEY = $key` - the correct destination, flagged by a
    # first cut of this guard that only knew `$env:` and `${NAME}`.
    r"|^\$[A-Za-z_][A-Za-z0-9_]*$)"
)

# Files whose JOB is to carry these patterns. Exempt BY NAME so the exemption
# stays a short visible list rather than a rule that quietly widens. The arm
# below asserts this file would actually TRIP the sweep, so an exemption that
# stopped being load-bearing gets reported rather than left standing.
SELF_EXEMPT = {
    "tests/test_no_secret_literals.py",
    # Plants a fake `sk-` literal as the fixture that proves the hand-off
    # write gate refuses secret-shaped content. Same category as this file.
    "tests/test_handoff_write_gate.py",
}


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
    for match in VENDOR_TOKEN.finditer(text):
        hits.append(f"vendor-prefixed token: {match.group(0)[:12]}...")
    for match in SECRET_BINDING.finditer(text):
        # Strip the markup a DOC wraps a code sample in before deciding. The
        # guard is about the VALUE, not the punctuation around it: LEDGER prose
        # quoting `$env:GEMINI_API_KEY = $key` inside a markdown code span
        # captured the value as "$key`" and failed the anchored env test, which
        # turned CI red on a docs-only commit describing this very guard.
        value = match.group("value").strip("`'\"*_,;)]}")
        if ENV_REFERENCE.search(value):
            continue
        hits.append(f"secret name bound to a literal: {match.group(0)[:48]}")
    return hits


def sweep() -> tuple[int, list[str]]:
    """`(files_scanned, offenders)`. The COUNT is returned so arms can assert it."""
    scanned = 0
    offenders: list[str] = []
    for rel in _tracked_files():
        if rel in SELF_EXEMPT:
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


def test_no_tracked_file_carries_a_secret_literal():
    _, offenders = sweep()
    assert not offenders, (
        "tracked file(s) carry a credential literal:\n  " + "\n  ".join(offenders)
        + "\nMove it to a machine-level environment variable and reference it. "
        "This repo is PUBLIC: a commit here is one push from world-readable.")


@pytest.mark.parametrize("planted", [
    'ANTHROPIC_API_KEY = "sk-ant-api03-notarealkeyjustafixture"',
    '"GEMINI_API_KEY": "AIzaSyFAKEFAKEFAKEFAKEFAKEFAKEFAKEFAKE"',
    "GITHUB_PERSONAL_ACCESS_TOKEN=ghp_000111222333444555666777888999aaabbb",
    'SAUCENAO_API_KEY = "0123456789abcdef"',
])
def test_a_planted_secret_is_caught(planted):
    """Each detector arm proven to FIRE before the clean result above is trusted.

    A clean sweep and an unarmed sweep look identical, which is the shape of
    every defect the cross-repo channel found on 2026-09-06.
    """
    assert scan_text(planted), f"the sweep missed a planted secret: {planted}"


@pytest.mark.parametrize("innocent", [
    "SHA = '629c3d511d2500f92d25fbe102a7a8c73644c027291f46b8796565a1e839f865'",
    'ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]',
    'GEMINI_API_KEY: "${GEMINI_API_KEY}"',
    "SAUCENAO_API_KEY=%SAUCENAO_API_KEY%",
    'DEVIANTART_CLIENT_SECRET = "<set in the machine environment>"',
    # A doc quoting the correct pattern inside a markdown code span. This is
    # the CI-red case, kept as an arm so the normalisation cannot regress.
    "prose: `$env:GEMINI_API_KEY = $key` is the correct destination",
])
def test_a_legitimate_neighbour_survives(innocent):
    """The digests and the env lookups must stay legal or the guard gets deleted."""
    assert not scan_text(innocent), f"false positive on: {innocent}"


def test_the_self_exemption_is_narrow_and_real():
    assert SELF_EXEMPT == {"tests/test_no_secret_literals.py",
                           "tests/test_handoff_write_gate.py"}, (
        "the exemption list grew. Every entry has to be a file whose JOB is to "
        "carry these patterns, and each one weakens the sweep by a whole file.")


@pytest.mark.parametrize("exempt", sorted(SELF_EXEMPT))
def test_every_exempt_file_would_trip_the_sweep(exempt):
    """An exemption that is no longer load-bearing is reported, not left standing."""
    text = (REPO_ROOT / exempt).read_text(encoding="utf-8")
    assert scan_text(text), (
        f"{exempt} no longer trips the detector, so its exemption is dead "
        "weight - remove the exemption or restore the planted fixtures")
