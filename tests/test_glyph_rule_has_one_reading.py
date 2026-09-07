"""One CLAUDE.md hard rule, one banned set - asserted, not assumed.

WHY THIS EXISTS
---------------
Resin Compute found the shape and Riot Commander confirmed it on its own tree
(cross-repo notes, 2026-09-06): a hard rule enforced by more than one mechanism
drifts, because each mechanism carries its own idea of what the rule says. RC's
version was a narrow test guard beside a catch-all commit gate. RC's fix was to
have CI call the gate engine so there is one reading.

LW's shape is different and needs a different fix, measured here rather than
copied: LW already sweeps tracked content TWICE in CI - `tools/strip_em_dashes.py
--check` plus the pytest hygiene guards - so LW has no unenforced-on-a-fresh-clone
hole and a third sweep would only re-check what already ran (the same reasoning
that keeps a docs-guards workflow out of this repo). What LW had instead was
DIVERGENCE, measured 2026-09-06:

    tools/precommit_gate.py            6 glyphs  (the COMMIT gate)
    tools/strip_em_dashes.py           6 glyphs  (the CI drift gate)
    tests/test_smart_quote_hygiene.py  8 glyphs  (adds U+2026 and NBSP)

So an ellipsis or a non-breaking space in staged content passed the commit hook
and then reddened CI for the same commit - two rules disagreeing about one
CLAUDE.md line. All three were converged on the STRICTEST reading (8), and this
file is what stops them drifting apart again. Widening the gate surfaced a
second defect in the fixer: its byte prefilter covered only U+2013 to U+2026,
so an NBSP-only file was skipped by the fast path.

The sets are compared as CODEPOINTS because the three modules spell them
differently on purpose (chars, ints, named constants) and all three stay 7-bit
ASCII by building them with chr().
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import precommit_gate  # noqa: E402
import strip_em_dashes  # noqa: E402


def _hygiene_module():
    """Load the sibling test module by path - it is not an importable package."""
    spec = importlib.util.spec_from_file_location(
        "_lw_hygiene_guard", ROOT / "tests" / "test_smart_quote_hygiene.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _gate_set() -> set[int]:
    return {ord(ch) for ch in precommit_gate._BANNED}


def _drift_set() -> set[int]:
    return {ord(ch) for ch in strip_em_dashes.REPL}


def _hygiene_set() -> set[int]:
    return set(_hygiene_module()._BANNED)


def test_the_commit_gate_and_the_ci_drift_gate_agree():
    assert _gate_set() == _drift_set(), (
        "the commit gate and the CI drift gate ban different glyph sets: "
        f"gate-only={sorted(hex(c) for c in _gate_set() - _drift_set())} "
        f"drift-only={sorted(hex(c) for c in _drift_set() - _gate_set())}")


def test_the_commit_gate_and_the_hygiene_guard_agree():
    """THE measured divergence: the hygiene guard banned U+2026 and the gate did
    not, so an ellipsis committed clean and failed CI on the same commit."""
    assert _gate_set() == _hygiene_set(), (
        "the commit gate and tests/test_smart_quote_hygiene.py ban different "
        f"glyph sets: gate-only={sorted(hex(c) for c in _gate_set() - _hygiene_set())} "
        f"guard-only={sorted(hex(c) for c in _hygiene_set() - _gate_set())}")


def test_every_glyph_CLAUDE_md_names_is_in_the_set():
    """The rule text is the floor, not the ceiling: en/em dash, both smart quote
    pairs, and the ellipsis that started this."""
    named = {0x00A0, 0x2013, 0x2014, 0x2018, 0x2019, 0x201C, 0x201D, 0x2026}
    missing = sorted(hex(c) for c in named - _gate_set())
    assert not missing, f"CLAUDE.md names {missing} but the gate does not ban them"


def test_the_drift_gate_replacement_for_every_banned_glyph_is_ascii():
    """A fixer that swaps one non-ASCII glyph for another is not a fixer."""
    bad = {hex(ord(k)): v for k, v in strip_em_dashes.REPL.items()
           if not v.isascii()}
    assert not bad, f"non-ASCII replacement(s): {bad}"


def test_the_byte_prefilter_still_covers_every_banned_glyph():
    """strip_em_dashes skips a file whose bytes match none of its prefilters.

    Every banned codepoint has to encode with one of them or the fixer walks
    straight past it. NBSP is exactly that case: it encodes C2 A0 and the
    prefilter was a single E2 80 prefix, so a file whose only offender was an
    NBSP was skipped by the fast path without a word.
    """
    missed = [hex(ord(ch)) for ch in strip_em_dashes.REPL
              if not any(pre in ch.encode("utf-8")
                         for pre in strip_em_dashes._PREFILTER)]
    assert not missed, (
        f"{missed} match none of {strip_em_dashes._PREFILTER!r}, so "
        "strip_em_dashes will skip files that contain only those")
