"""The pipeline diagram is generated from the code, and checked against it.

Context (ROADMAP archify item, 2026-09-16): the operator queued `tt-a1i/archify`
to render LW's structure as a checked diagram instead of prose. The JOB is real;
archify is the wrong instrument for it here (see the ROADMAP entry and
`docs/PIPELINE_DIAGRAM.md` for the scope answer). What the job actually needs is
a diagram that CANNOT disagree with the code, and that is what these arms buy.

Two arms, and the second is the one that matters:

1. The tracked `docs/PIPELINE_DIAGRAM.md` is byte-identical to a fresh
   generation. Rename a folder in `lw_pipeline.py` and the doc goes stale
   loudly instead of silently.
2. Every folder-CHANGING transition verb that `lw_pipeline.py` actually logs
   appears as an edge in the diagram, or sits on the explicit in-place
   allowlist. Add a new transition and forget the diagram, and this goes red.
   Without this arm the generator could drift from the code it claims to
   describe while arm 1 stayed green, because arm 1 only compares the doc to
   the GENERATOR.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))

import lw_diagram  # noqa: E402

DOC = REPO / "docs" / "PIPELINE_DIAGRAM.md"
PIPELINE_SRC = REPO / "tools" / "lw_pipeline.py"


def test_tracked_diagram_matches_a_fresh_generation() -> None:
    assert DOC.is_file(), "docs/PIPELINE_DIAGRAM.md is not on disk"
    fresh = lw_diagram.render_document().encode("utf-8")
    assert DOC.read_bytes() == fresh, (
        "docs/PIPELINE_DIAGRAM.md is stale - regenerate it with "
        "`python tools/lw_diagram.py --write`"
    )


def test_generated_doc_is_seven_bit_ascii_lf() -> None:
    raw = DOC.read_bytes()
    assert not [b for b in raw if b > 127], "diagram carries non-ASCII bytes"
    assert b"\r" not in raw, "diagram carries CR; *.md is pinned eol=lf"


def test_every_logged_transition_verb_is_accounted_for() -> None:
    """The anti-drift arm: a new transition in the code must reach the diagram."""
    src = PIPELINE_SRC.read_text(encoding="utf-8")
    # Every ctx.log call site names its op as a literal or via a dict lookup.
    literal = set(re.findall(r'ctx\.log\(\s*slug,\s*"([A-Z_]+)"', src))
    via_dict = set(re.findall(r"ctx\.log\(\s*slug,\s*(?:op_name or )?([A-Z_]+)\[", src))
    for table in via_dict:
        literal |= set(getattr(lw_diagram.lw_pipeline, table).values())

    drawn = {op for op, _src, _dst in lw_diagram.build_edges()}
    unaccounted = literal - drawn - lw_diagram.IN_PLACE_OPS
    assert not unaccounted, (
        f"lw_pipeline.py logs transition verb(s) {sorted(unaccounted)} that the "
        "diagram neither draws nor lists as in-place. Draw the edge in "
        "tools/lw_diagram.py, or add the verb to IN_PLACE_OPS with its reason."
    )


def test_in_place_allowlist_is_not_a_dumping_ground() -> None:
    """Every allowlisted verb must actually be logged by the code."""
    src = PIPELINE_SRC.read_text(encoding="utf-8")
    stale = {op for op in lw_diagram.IN_PLACE_OPS if f'"{op}"' not in src}
    assert not stale, (
        f"IN_PLACE_OPS lists verb(s) {sorted(stale)} that lw_pipeline.py no "
        "longer logs - drop them rather than letting the allowlist grow stale"
    )


def test_edges_only_reference_declared_states() -> None:
    states = set(lw_diagram.build_states())
    for op, src, dst in lw_diagram.build_edges():
        assert src in states, f"{op} leaves undeclared state {src}"
        assert dst in states, f"{op} enters undeclared state {dst}"


def test_check_mode_agrees_with_the_tracked_file() -> None:
    assert lw_diagram.main(["--check"]) == 0
