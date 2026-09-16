"""Contract for the adopted review protocol (ADR-013).

LW adopted two skills from `timharris707/skills` (MIT) on 2026-09-16:
`blast-radius` (the implementer's own pre-merge discipline) and
`adversarial-review` (the reviewer's isolated-finders + skeptic gate).
They were ADAPTED, not byte-copied, for three measured reasons recorded in
ADR-013: upstream cross-links four skills LW deliberately did not take, the
upstream text is not 7-bit ASCII, and a verbatim drop would stand a second
protocol beside the SUBAGENT-FIRST block that 20 command docs already carry.

This test is the non-vacuity gate on that adaptation. It exists because a
process document nobody checks decays into prose: the five ladder rungs must
stay spelled the SAME WAY in every place that grades a claim, or the shared
grading language - which is the entire mechanism - silently forks.
"""
from __future__ import annotations

from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
BLAST = REPO / ".claude" / "commands" / "blast-radius.md"
ADVERSARIAL = REPO / ".claude" / "commands" / "adversarial-review.md"
VERIFIER = REPO / ".claude" / "agents" / "verifier.md"
ADR = REPO / "docs" / "adr" / "ADR-013-review-protocol-evidence-ladder.md"

# The shared grading language. Every surface that grades a claim spells the
# rungs THIS way; a second spelling is a fork, which is what this pins.
RUNGS = ("Asserted", "Cited", "Traced", "Run", "Reproduced")

GRADING_SURFACES = (BLAST, ADVERSARIAL, VERIFIER)
ADOPTED = (BLAST, ADVERSARIAL)


def _read(path: Path) -> str:
    return path.read_bytes().decode("utf-8")


@pytest.mark.parametrize("path", ADOPTED + (ADR,), ids=lambda p: p.name)
def test_adopted_files_exist(path: Path) -> None:
    assert path.is_file(), f"adopted file missing from disk: {path}"


@pytest.mark.parametrize("path", ADOPTED + (ADR,), ids=lambda p: p.name)
def test_adopted_files_are_seven_bit_ascii_lf(path: Path) -> None:
    raw = path.read_bytes()
    offenders = sorted({b for b in raw if b > 127})
    assert not offenders, (
        f"{path.name} carries non-ASCII bytes {offenders}; upstream text is not "
        "7-bit ASCII and this tree is (CLAUDE.md hard rule)"
    )
    assert b"\r" not in raw, f"{path.name} carries CR; *.md is pinned eol=lf"


@pytest.mark.parametrize("path", GRADING_SURFACES, ids=lambda p: p.name)
def test_every_grading_surface_spells_the_same_five_rungs(path: Path) -> None:
    text = _read(path)
    missing = [r for r in RUNGS if f"**{r}.**" not in text]
    assert not missing, (
        f"{path.name} is missing ladder rung(s) {missing}; all five rungs are "
        "spelled **Rung.** on every surface that grades a claim"
    )


@pytest.mark.parametrize("path", ADOPTED, ids=lambda p: p.name)
def test_adopted_docs_carry_the_subagent_first_block(path: Path) -> None:
    assert "SUBAGENT-FIRST" in _read(path), (
        f"{path.name} does not carry the SUBAGENT-FIRST block that every other "
        ".claude/commands doc carries - that is stacking, not reconciling"
    )


@pytest.mark.parametrize("path", ADOPTED, ids=lambda p: p.name)
def test_adopted_docs_carry_mit_attribution(path: Path) -> None:
    text = _read(path)
    assert "## Attribution" in text, f"{path.name} has no Attribution section"
    assert "timharris707/skills" in text, (
        f"{path.name} does not name the upstream it was adapted from"
    )
    assert "MIT" in text, f"{path.name} does not state the upstream licence"


@pytest.mark.parametrize("path", ADOPTED, ids=lambda p: p.name)
def test_no_dangling_links_to_skills_lw_did_not_adopt(path: Path) -> None:
    """Upstream cross-links skills LW deliberately declined.

    `handoff` and `domain-memory` would fragment WAKEUP_NOTES.md /
    docs/LEDGER.md / docs/adr/ (the documented two-disagreeing-records failure
    mode); `plainspoken`, `orchestrate` and the `team-workflow` pack were out
    of scope. A relative link to any of them resolves to nothing on disk.
    """
    text = _read(path)
    assert "/SKILL.md" not in text, (
        f"{path.name} links to an upstream SKILL.md path that does not exist here"
    )
    assert "](../" not in text, (
        f"{path.name} carries an upstream relative skill link; LW's commands are "
        "flat under .claude/commands/"
    )


def test_blocker_rank_requires_a_run_rung_repro() -> None:
    """The gate's honesty rule: nothing blocks a merge on a hunch."""
    text = _read(ADVERSARIAL)
    assert "BLOCKER" in text
    assert "rung 4" in text, (
        "adversarial-review must state that BLOCKER rank requires a rung-4 "
        "(Run) reproduction - without it the gate blocks on plausibility"
    )


def test_verifier_gained_skeptic_mode_rather_than_a_second_agent() -> None:
    """Reconcile, do not stack: the skeptic is a MODE of the existing verifier."""
    text = _read(VERIFIER)
    assert "Skeptic mode" in text, (
        ".claude/agents/verifier.md must carry the skeptic mode; adding a "
        "separate skeptic agent would stand a second protocol beside it"
    )
    assert "dismissed bucket" in text.lower(), (
        "skeptic mode must record its kills in the dismissed bucket"
    )


def test_adr_records_the_two_declined_skills_by_name() -> None:
    """So nobody re-opens them without reading why they were declined."""
    text = _read(ADR)
    for declined in ("handoff", "domain-memory"):
        assert declined in text, f"ADR-013 does not record declining {declined}"
