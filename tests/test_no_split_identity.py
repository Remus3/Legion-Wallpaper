"""No tracked file may carry the operator's identity, even SPLIT into fragments.

Sibling of `tests/test_no_account_paths.py` and `tests/test_no_secret_literals.py`,
and the correction to both. Written on Lanternlight's 2026-09-07 2035 note.

THE BLINDNESS. Every whole-token sweep for a sensitive string is silently a
claim that the string is CONTIGUOUS. Lanternlight's address sat split across
adjacent lines of a tracked file, 26 characters apart and in reversed order, and
EVERY guard reported clean - including the guard written for exactly that
address. The split was not adversarial: the session DOCUMENTING the leak wrote
it. LW then reproduced the same failure in the plainest possible form. The
2026-09-07 purge (LEDGER 172) took the operator's address out of history and out
of two docs, and the three artifacts that RECORD the purge - WAKEUP_NOTES.md,
`docs/LEDGER.md` item 172 and `docs/_archive/2026-09-07-sha-rewrite-map.md` -
re-published it CONTIGUOUSLY, five times, into a PUBLIC repo. It survived
because nothing checked: LW had no email guard at all.

WHAT THIS GUARD DOES DIFFERENTLY. It never looks at the raw bytes. It reduces
each tracked file to a NORMALIZED view - lowercase, `[a-z0-9]` only - which
deletes every separator a split can be made of: newlines, spaces, quotes,
backticks, markdown emphasis, comment markers, list bullets. `close.` on one
line and a surname on the next reads as one token in that view, and so does a
break in the middle of a word. It then scans the view AND its reverse, so text
written backwards is caught the same way.

WHAT IT STILL CANNOT SEE, stated rather than implied. Two fragments separated by
UNRELATED text (Lanternlight's 26 characters) do not become adjacent under
normalisation. The answer is not a cleverer window, it is the choice of
fragment: each pinned fragment must be distinctive ON ITS OWN, so no assembly is
required to recognise it. `SENSITIVE_FRAGMENTS` is chosen on that rule, and any
fragment added later has to meet it.

WHY DIGESTS AND NOT LITERALS. A guard that spelled out the string it forbids
would publish the string - which is precisely how the three artifacts above
leaked it. So each fragment is pinned as `(first character, length, sha256)` and
the sweep hashes only the windows that start with that character. The first
character and the length are the price of a scan that is linear rather than
6.6 MB of hashing per fragment; neither reconstructs anything.

WHY NO EXEMPTIONS. `test_no_account_paths` exempts append-only history because
rewriting it was weighed and rejected. That reasoning does not carry here: the
operator's decision in LEDGER 172 was that this identity leaves the tree, and an
append-only file is still a world-readable file. The corpus is every tracked
file, and the guard's own fixtures are synthetic, so it needs no self-exemption.
"""
from __future__ import annotations

import subprocess
import sys
from functools import lru_cache
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "tools"))
sys.path.insert(0, str(REPO_ROOT / "tests"))

from split_scan import (  # noqa: E402  (path shim above)
    SENSITIVE_FRAGMENTS,
    normalize,
    pin,
    scan_fragments,
)
from test_no_account_paths import _would_be_exempt  # noqa: E402  (path shim above)

# EXEMPTION IS A PROPERTY OF THE VALUE, NOT OF THE MECHANISM. The account name
# carries the exemptions `test_no_account_paths` already records - append-only
# history and dated artifacts - because rewriting those was weighed and REJECTED
# on 2026-09-07, and this guard is a second detector for the same value, not a
# second policy for it. The operator's personal address is exempt NOWHERE: the
# LEDGER 172 decision was that it leaves the tree, and an append-only file is
# still a world-readable file. Importing the sibling's rule rather than copying
# it means there is one definition to change.
EXEMPTIBLE_LABELS = frozenset({"account-in-path"})


def _fragments_for(rel: str) -> tuple:
    """The pins that apply to `rel`. One decision point, so the arms can drive it."""
    if _would_be_exempt(rel):
        return tuple(f for f in SENSITIVE_FRAGMENTS
                     if f.label not in EXEMPTIBLE_LABELS)
    return SENSITIVE_FRAGMENTS

# A fragment that names NOBODY, pinned the same way as the real ones. It is what
# proves the DETECTOR fires; the real pins cannot be planted in a tracked file
# without committing the thing this guard exists to keep out.
PROBE = pin("probe", "zqxsplitprobe")


@lru_cache(maxsize=1)
def _tracked_files() -> tuple[str, ...]:
    """Every tracked path, asked of GIT rather than of the disk."""
    out = subprocess.run(
        ["git", "ls-files", "-z"], cwd=REPO_ROOT,
        capture_output=True, text=True, check=True,
    ).stdout
    return tuple(sorted(p for p in out.split("\0") if p))


def sweep() -> tuple[int, list[str]]:
    """`(files_scanned, offenders)`. The COUNT is returned so arms can assert it."""
    scanned = 0
    offenders: list[str] = []
    for rel in _tracked_files():
        try:
            text = (REPO_ROOT / rel).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        scanned += 1
        for hit in scan_fragments(text, _fragments_for(rel)):
            offenders.append(f"{rel}: {hit}")
    return scanned, offenders


def test_the_sweep_selects_a_real_corpus():
    """Guard the guard: a sweep that scanned nothing would pass vacuously."""
    scanned, _ = sweep()
    assert scanned > 200, f"only {scanned} tracked files scanned - the corpus is wrong"


def test_no_tracked_file_carries_an_identity_fragment():
    _, offenders = sweep()
    assert not offenders, (
        f"{len(offenders)} tracked identity fragment(s):\n  "
        + "\n  ".join(offenders)
        + "\nRemove it. Describe the value instead of quoting it - the three "
        "artifacts that recorded the 2026-09-07 purge each re-published the "
        "address they were documenting. This repo is PUBLIC.")


@pytest.mark.parametrize("planted", [
    # Contiguous. The baseline: a fragment a whole-token grep would also find.
    "contact: zqxsplitprobe@example.invalid",
    # Split across adjacent lines - Lanternlight's shape.
    "the value is `zqxsplit`\n`probe` closes it",
    # Split mid-word by markdown emphasis, on ONE line.
    "the value is **zqx**split*probe* in the doc",
    # Split by a list bullet and an indent, which is how a doc actually breaks.
    "- zqx\n  - split\n  - probe\n",
    # Written backwards.
    "eborptilpsxqz",
    # Backwards AND split.
    "ebor\nptilpsxqz",
])
def test_a_split_fixture_is_caught(planted):
    """Every arm proven to FIRE. A clean sweep and an unarmed sweep look alike."""
    assert scan_fragments(planted, (PROBE,)), f"the sweep missed: {planted!r}"


@pytest.mark.parametrize("innocent", [
    "probe the split of zqx",
    "a normal sentence about splitting a probe into fragments",
    "zqx split prob",  # one character short of the pin
    "",
])
def test_an_unrelated_neighbour_survives(innocent):
    """Order matters. Normalisation deletes separators, it does not sort.

    The first cut of this arm read "zqx split probe are three unrelated words",
    which normalises to the pinned value with the spaces gone - the guard was
    right and the fixture was wrong. Kept as a warning: under normalisation,
    "unrelated words that happen to be the value in order" is not a thing.
    """
    assert not scan_fragments(innocent, (PROBE,)), f"false positive on: {innocent!r}"


@pytest.mark.parametrize("beyond_reach", [
    # Lanternlight's actual shape: the halves are separated by OTHER text, so
    # normalisation never makes them adjacent.
    "local part `zqxsplit`\nand the rest is `probe`",
    "probe\nzqxsplit",  # halves present, wrong order
])
def test_the_documented_limit_is_real_and_pinned(beyond_reach):
    """State the blind spot as an ASSERTION, so widening it cannot go unnoticed.

    This is the failure mode the whole guard exists to answer, and it is only
    answered by the CHOICE OF FRAGMENT: every pin in `SENSITIVE_FRAGMENTS` is
    distinctive on its own, so nothing has to be assembled. A pin that needed
    two halves would land exactly here. If someone widens the scanner to reach
    across unrelated text, this arm fails and the docstring gets corrected with
    it rather than silently going stale.
    """
    assert not scan_fragments(beyond_reach, (PROBE,))


def test_the_exemption_is_per_value_and_never_covers_the_address():
    """An exemption that widened to the address would undo the LEDGER 172 decision."""
    exempt = _fragments_for("docs/LEDGER.md")
    live = _fragments_for("tools/lw_paths.py")
    assert _would_be_exempt("docs/LEDGER.md") and not _would_be_exempt("tools/lw_paths.py")
    assert {f.label for f in live} == {f.label for f in SENSITIVE_FRAGMENTS}
    assert {f.label for f in exempt} == {
        f.label for f in SENSITIVE_FRAGMENTS if f.label not in EXEMPTIBLE_LABELS}
    assert "operator-surname" in {f.label for f in exempt}, (
        "the personal address became exemptible - it is exempt NOWHERE")


def test_the_probe_is_not_one_of_the_real_pins():
    """The arms above must not be proving the real fragments by accident."""
    assert PROBE not in SENSITIVE_FRAGMENTS


def test_every_real_fragment_is_pinned_and_distinctive():
    """A pin that assembles from common words would fire on prose and be deleted.

    Length is the proxy that can be asserted without naming the value: a
    fragment short enough to occur by chance in 6.6 MB of normalised text is not
    distinctive, and the rule in the docstring is that each one must stand alone.
    """
    assert SENSITIVE_FRAGMENTS, "the guard is unarmed"
    labels = [f.label for f in SENSITIVE_FRAGMENTS]
    assert len(labels) == len(set(labels)), f"duplicate labels: {labels}"
    for frag in SENSITIVE_FRAGMENTS:
        assert frag.length >= 6, f"{frag.label} is too short to stand alone"
        assert len(frag.digest) == 64, f"{frag.label} is not a sha256 pin"
        assert normalize(frag.first) == frag.first, f"{frag.label} pin is not normalised"


def test_normalize_deletes_every_separator_a_split_can_be_made_of():
    joined = "closethegap"
    for spelling in ["close the gap", "Close-The-Gap", "close\nthe\ngap",
                     "`close` **the** _gap_", "close.the.gap", "# close\n# the\n# gap",
                     "CLOSE, THE, GAP"]:
        assert normalize(spelling) == joined, f"normalisation failed on {spelling!r}"


def test_pin_takes_the_raw_value_and_pins_its_normalised_form():
    assert pin("x", "Close.The-Gap") == pin("x", "close the gap")
    assert pin("x", "closethegap").first == "c"
    assert pin("x", "closethegap").length == len("closethegap")


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
