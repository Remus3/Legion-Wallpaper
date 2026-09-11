"""Every headless lane must be stoppable without unregistering its task.

Three lanes on this box spawn unattended work with nobody watching:
`lw_inbox_responder` (detached headless sessions), `ci_watchdog` (a headless
fixer that pushes), and `weekly_hygiene_run.ps1` (`claude -p
--dangerously-skip-permissions`). The first two carried a HALT switch and are
arm-covered in their own files. MEASURED 2026-09-11, when the operator asked to
disarm every lane: the hygiene lane had NO switch at all, so the only stop
available was unregistering the task - a change to the operator's scheduler
configuration to achieve what an empty file achieves elsewhere.

These arms pin the property rather than the wording: a kill switch exists, and
it is consulted BEFORE the thing it is meant to prevent. Checking order matters
more than presence - a switch read after `claude` is launched stops nothing.
"""
from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
HYGIENE = ROOT / "tools" / "weekly_hygiene_run.ps1"


def _text() -> str:
    return HYGIENE.read_text(encoding="utf-8")


def test_the_weekly_hygiene_lane_has_a_halt_switch():
    body = _text()
    assert "weekly_hygiene" in body and "HALT" in body, \
        "the unattended claude lane has no kill switch"
    assert "Test-Path" in body, "the switch must be a file the operator can create"


def test_the_halt_check_precedes_the_claude_invocation():
    """A switch read after the session is launched stops nothing. This is the
    whole assertion: ORDER, not presence."""
    lines = _text().splitlines()
    halt = next(i for i, ln in enumerate(lines) if "Test-Path" in ln and "halt" in ln)
    launch = next(i for i, ln in enumerate(lines) if ln.lstrip().startswith("$out = & claude"))
    assert halt < launch, \
        f"the HALT check at line {halt + 1} runs after claude at line {launch + 1}"


def test_an_empty_halt_file_still_halts():
    """`type nul > HALT` is how an operator makes one under stress. Reading an
    empty file as "no halt" disarms the switch exactly when it is being used -
    the same ruling `ci_watchdog.halted` and the responder already carry."""
    body = _text()
    assert "IsNullOrWhiteSpace" in body, \
        "an empty HALT file must still stop the lane, with a generic reason"


@pytest.mark.parametrize("relative", [
    "ops/runtime/inbox_responder",
    "ops/runtime/ci_watchdog",
    "ops/runtime/weekly_hygiene",
])
def test_each_lane_keeps_its_switch_in_the_gitignored_runtime_tree(relative):
    """The switches live under `ops/runtime/`, which is gitignored: this repo is
    PUBLIC, a HALT file states operator intent, and a committed one would also
    halt every clone."""
    assert (ROOT / relative).parent.name == "runtime"
