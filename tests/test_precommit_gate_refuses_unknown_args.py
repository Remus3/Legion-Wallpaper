"""The gate must REFUSE an argument it does not understand, not fall through.

Provenance, because this repair came from outside: LL measured it on
2026-09-08 and re-measured it 2026-09-16 - a one-character slip in a hook line
(`--lintstaged` for `lint-staged`) made their gate exit 0 printing nothing,
because the unrecognised token fell through to the stdin path, found no JSON,
and returned 0. A clean repository also exits 0, so the two were
indistinguishable by the only thing a git hook reads. LW reproduced the
identical shape on itself the same day: a deliberate should-FAIL probe passed
`--staged`, a flag this script does not have, and got a silent green from the
probe written to catch exactly that class (DC-01).

LL's repair is narrower and stronger than "prove it through a real commit":
REFUSE EVERY ARGUMENT YOU DO NOT UNDERSTAND. The fall-through is what turns a
typo into a silent pass. CS, measured independently, already refuses at this
entry point. LW was the tree still carrying it.

The refusal code is deliberately NOT 2. CS's caution, repeated by RSC and worth
pinning here: exit 2 is not self-evidencing - a module's syntax error and a tool
deliberately refusing both exit 2. This gate already returns 2 for BLOCKED, so
a refusal that also returned 2 would be unreadable by the thing that matters,
which is a human or an agent reading the hook's output.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
GATE = REPO / "tools" / "precommit_gate.py"
REFUSE_CODE = 3

# Every mode the script really has, taken from its own dispatch.
KNOWN_MODES = ("--git-hook", "--scan-files", "--message-file")


def _run(args: list[str], stdin: str = "") -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(GATE), *args],
        input=stdin, capture_output=True, text=True, cwd=str(REPO), timeout=120)


@pytest.mark.parametrize("bogus", [
    "--staged",        # the exact token LW's own probe used
    "--lintstaged",    # LL's one-character slip, adapted
    "--git-hooks",     # a plausible fat-finger of a REAL mode
    "--check",
    "-q",
])
def test_an_unknown_argument_is_refused_loudly(bogus: str) -> None:
    r = _run([bogus])
    assert r.returncode == REFUSE_CODE, (
        f"{bogus!r} returned {r.returncode}, expected {REFUSE_CODE}. An "
        "argument the gate does not understand must REFUSE, never fall "
        "through to a path that finds nothing to do and reports success.")
    combined = r.stdout + r.stderr
    assert bogus in combined, (
        f"the refusal does not name the offending argument {bogus!r}: "
        f"{combined!r}")
    assert "refus" in combined.lower(), (
        "the refusal must SAY it is refusing, so a reader cannot mistake it "
        f"for a measured pass: {combined!r}")


def test_the_refusal_names_the_modes_that_do_exist() -> None:
    r = _run(["--staged"])
    combined = r.stdout + r.stderr
    for mode in KNOWN_MODES:
        assert mode in combined, (
            f"the refusal does not name the real mode {mode} - a reader who "
            f"typo'd a flag needs the list: {combined!r}")


def test_no_arguments_still_reads_stdin_and_passes_a_non_commit() -> None:
    """The PreToolUse hook invokes this with NO arguments; that must keep working.

    A repair that refused the empty argv would break the hook it protects -
    which is the mutation this arm exists to forbid.
    """
    r = _run([], stdin='{"tool_input": {"command": "git status"}}')
    assert r.returncode == 0, (
        f"bare invocation with a non-commit payload must pass: {r.returncode} "
        f"{r.stdout!r} {r.stderr!r}")


@pytest.mark.parametrize("mode", KNOWN_MODES)
def test_every_real_mode_is_still_accepted(mode: str) -> None:
    """Guard the guard: a refusal that swallowed the real modes would be worse."""
    args = [mode]
    if mode == "--message-file":
        args.append(str(REPO / "does-not-exist.txt"))
    r = _run(args, stdin="")
    assert r.returncode != REFUSE_CODE, (
        f"{mode} is a real mode and must not be refused: {r.stdout!r} "
        f"{r.stderr!r}")


def test_scan_files_trailing_paths_are_not_mistaken_for_flags() -> None:
    """`--scan-files a.py b.py` passes paths after the mode; they are its business."""
    r = _run(["--scan-files", "README.md"])
    assert r.returncode != REFUSE_CODE, (
        f"paths after --scan-files must not trip the refusal: {r.stdout!r} "
        f"{r.stderr!r}")
