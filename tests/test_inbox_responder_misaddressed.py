"""SS-MAIL: a note addressed to another tree is never LW's mail.

MEASURED 2026-11-05: SS's responder copies every note it writes to every
participant regardless of addressee, so LW's inbox holds e.g.
`2026-11-03-1324-from-SS-FIX-to-MAIN-KIT-checklist-caps-...-ONE-ANSWER.md`.
The kit's classify() escalates a FIX to WORK on the class alone, so LW spent a
full headless run on a note that names MAIN as its only addressee.

THE RULE (parent side, before any spawn): the addressee is the run of fleet
codes right after `-from-<SNDR>-[<CLASS-WORDS>-]to-`, anchored there so a
prose `...-owed-to-LL-...` in a slug never counts. The note is SKIPPED when
that run names neither LW nor ALL, and is not just the sender's own code (a
`-from-SS-CORRECTION-to-SS-1700-` corrects SS's own earlier note; it is
broadcast). No addressee at all keeps the note.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import lw_inbox_responder as responder  # noqa: E402

fleet_inbox = responder.fleet_inbox


def _note(tmp_path: Path, name: str) -> Path:
    p = tmp_path / name
    p.write_text("# From SS - a note\n\nbody\n", encoding="ascii", newline="\n")
    return p


SKIPPED = [
    # The live case: verbatim filename from LW's inbox.
    ("2026-11-03-1324-from-SS-FIX-to-MAIN-KIT-checklist-caps-cut-silently-13a-"
     "departure-board-displaced-row-ONE-ANSWER.md", "MAIN"),
    ("2026-10-24-1525-from-SS-FIX-to-MAIN-KIT-fleet_test_guard-IGNORE-misses-ONE-ANSWER.md",
     "MAIN"),
    ("2026-10-03-0915-from-MAIN-ORDER-to-RC-lane-widget-addendum.md", "RC"),
    ("2026-10-18-1230-from-SS-OPERATOR-REQUEST-to-MAIN-hold-SS-tree-writes.md", "MAIN"),
    ("2026-09-21-1330-from-SS-to-MAIN-ACTION-DONE-ruling-recorded.md", "MAIN"),
    ("2026-11-05-0100-from-MAIN-ORDER-to-RC-EW-two-trees-not-lw.md", "RC"),
]

KEPT = [
    "2026-10-25-1935-from-MAIN-FIX-to-LW-gh-review-pillow-13-82-alerts-ONE-ANSWER.md",
    "2026-10-19-0034-from-MAIN-ORDER-to-LW-RC-EW-DEPENDABOT-MERGE-RULE-ONE-ANSWER.md",
    "2026-10-09-0930-from-MAIN-ORDER-to-ALL-SIX-FLEET-KIT-v14-kit14-defects-ONE-ANSWER.md",
    "2026-10-26-0315-from-MAIN-ORDER-to-ALL-SEVEN-FLEET-KIT-v24-cumulative-ONE-ANSWER.md",
    "2026-11-05-0200-from-MAIN-ORDER-to-ALL-FLEET-KIT-v29-ONE-ANSWER.md",
    "2026-11-05-0300-from-MAIN-ORDER-FLEET-KIT-v29-no-addressee-ONE-ANSWER.md",
    "2026-11-05-0400-from-RC-REVIEW-inventory-to-share-and-CI-time-measurements.md",
    # Prose `to-<CODE>` inside a slug is not an addressee.
    "2026-09-20-1502-from-SS-no-objection-to-CS-joining-a-reserved-floor.md",
    "2026-09-07-1013-from-CS-ACTION-whole-channel-read-a-retraction-owed-to-LL-and-more.md",
    # A sender correcting its own earlier note is broadcast.
    "2026-09-21-1800-from-SS-CORRECTION-to-SS-1700-an-ordered-script.md",
]


@pytest.mark.parametrize(("name", "dest"), SKIPPED)
def test_a_note_addressed_to_another_tree_is_skipped(tmp_path, name, dest):
    d, why = responder.decide(_note(tmp_path, name))
    assert d.action == fleet_inbox.SKIP
    assert d.reason == "misaddressed"
    assert why and why.startswith("misaddressed:") and dest in why


@pytest.mark.parametrize("name", KEPT)
def test_a_note_for_lw_all_or_no_one_in_particular_is_kept(tmp_path, name):
    d, why = responder.decide(_note(tmp_path, name))
    assert d.action != fleet_inbox.SKIP, (name, d, why)
    assert why is None


@pytest.mark.parametrize(("name", "codes"), [
    ("x-from-SS-FIX-to-MAIN-KIT-y.md", ("MAIN",)),
    ("x-from-MAIN-ORDER-to-LW-RC-EW-DEPENDABOT-y.md", ("LW", "RC", "EW")),
    ("x-from-MAIN-ORDER-to-ALL-SEVEN-y.md", ("ALL",)),
    ("x-from-MAIN-ORDER-to-ALL-SIX-y.md", ("ALL",)),
    ("x-from-SS-no-objection-to-CS-joining.md", ()),
    ("x-from-MAIN-ORDER-FLEET-KIT-v29.md", ()),
])
def test_addressees_are_parsed_from_the_anchored_slot_only(name, codes):
    assert responder.addressees(name) == codes


def test_own_skip_reasons_win_over_misaddressed(tmp_path):
    # LW's own note to MAIN stays a SELF skip, not a misaddressed one.
    d, why = responder.decide(_note(tmp_path, "2026-11-05-from-LW-ANSWER-to-MAIN-x.md"))
    assert d.action == fleet_inbox.SKIP and why == responder.SELF_WHY
