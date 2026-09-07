"""The ARCHITECTURE.md port restatement must match the registry it restates.

Ported in shape from Riot Commander's tests/test_readme_port_map.py, delivered
verbatim to moon_sync_inbox/from-RC-verbatim/ on 2026-09-07. RC measured its own
README missing `:8861` - a port that was in the registry, bound by a live
scheduled task, and holding its own credential. Nothing noticed, because nothing
compared the two.

LW's restatement lives in `docs/ARCHITECTURE.md` rather than the README, and it
was unguarded the same way: `tools/lw_ports.py` produces the truth
(`ALLOCATIONS`, pinned per entry against its own definition site), the doc
restates it for a reader, and a restatement with no guard is a claim that
decays.

It matters more than an ordinary doc nit because of the cross-project doctrine
written into `tools/lw_ports.py` itself: a band is verified against the OWNING
project's registry IN SOURCE, never against a live scan - a sibling checking for
a collision reads this doc. RSC put its engine inside a neighbour's block in
exactly that way on 2026-09-06 and nothing failed, because nothing was listening.

Both directions are asserted. A port the registry knows and the doc omits is
RC's defect; a port the doc names and the registry does not is its mirror - a
service that was moved or retired with the doc left behind, which is the shape
that sends a sibling looking at the wrong band.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import lw_ports  # noqa: E402

DOC = ROOT / "docs" / "ARCHITECTURE.md"

# Four-digit literals only. The block bounds themselves (8900-8919) are written
# as a RANGE in the doc and are checked separately, not as allocations.
_PORT = re.compile(r"\b(\d{4})\b")


def _doc_text() -> str:
    return DOC.read_text(encoding="utf-8", errors="replace")


def _ports_cited_in_the_doc() -> set[int]:
    low, high = lw_ports.LW_BLOCK
    text = _doc_text()
    # Drop the block statements ("8900-8919") before scanning: they name the
    # range, not an allocation, and would otherwise read as two live ports.
    text = re.sub(rf"\b{low}\s*-\s*{high}\b", " ", text)
    return {int(m) for m in _PORT.findall(text) if low <= int(m) <= high}


def test_the_doc_names_every_registered_allocation():
    """RC's defect: a registered, live port missing from the map a reader uses."""
    cited = _ports_cited_in_the_doc()
    missing = {name: port for name, port in lw_ports.ALLOCATIONS.items()
               if port not in cited}
    assert not missing, (
        f"docs/ARCHITECTURE.md does not name {missing}, which tools/lw_ports.py "
        "registers. The doc is what a sibling project reads to check a band, so "
        "an incomplete map is a cross-project hazard, not a doc nit.")


def test_the_doc_names_no_port_the_registry_does_not():
    """The mirror: a doc left behind when a service moved or was retired."""
    known = set(lw_ports.ALLOCATIONS.values())
    stray = sorted(_ports_cited_in_the_doc() - known)
    assert not stray, (
        f"docs/ARCHITECTURE.md cites {stray} inside LW's block, but "
        "tools/lw_ports.py registers no such allocation. Either register it "
        "(and pin it against its definition site) or remove it from the doc.")


def test_the_doc_states_the_reserved_block():
    low, high = lw_ports.LW_BLOCK
    assert re.search(rf"\b{low}\s*-\s*{high}\b", _doc_text()), (
        f"docs/ARCHITECTURE.md no longer states LW's reserved block {low}-{high}. "
        "The block is the part a sibling project needs most.")
