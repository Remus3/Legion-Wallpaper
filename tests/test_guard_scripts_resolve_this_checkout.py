"""A guard or launcher must resolve the checkout it is RUNNING IN.

The sibling sweep for `tests/test_hook_commands_are_env_anchored.py`. Anchoring
the hook COMMANDS to `$CLAUDE_PROJECT_DIR` moves the right script in a clone or
a linked worktree; it does nothing about a script that, once running, reads its
paths from a literal baked into its own source. That is the same false GREEN one
layer down, and the root-cause rule in CLAUDE.md is explicit that a fix in a
family of similar cases gets a grep for the siblings and a test per sibling.

WHAT THE 2026-09-20 SWEEP FOUND, and the verdicts it reached. A literal
`C:\\Legion Wallpaper` is tracked in many places and MOST of them are correct:
prose in CLAUDE.md and the docs (which have to write the path down to document
it), test fixtures that deliberately simulate this machine, `.claude/commands/*`
instructions where the orchestrator means the MAIN tree on purpose (a merge
fired from a worktree lands on the wrong branch), one-off dated analysis
scripts, and the scheduled tasks - a task registered on this box is legitimately
absolute, and rewriting it would break the registration for no gain. The
`tools/lw_clean_*` / `lw_first_pass` / `lw_pipeline` roots point at the
GITIGNORED image corpus and runtime state, which genuinely lives at one place on
one machine; moving those would change where images are read from, which is a
data decision and not this defect.

The genuine cases are the ones below: code whose whole job is to gate or launch
THIS checkout.

  tools/text_first_guard.py  A PreToolUse hook. Its escape hatch is the file
      `ops/runtime/allow_visual.flag`, and the path was a bare literal with no
      fallback at all. So in any second checkout the hook consults the ORIGINAL
      tree's flag: a guard reading another tree's override is the precise shape
      of a gate that reports on something other than what is being edited, and
      an override dropped in the tree you are actually working in does nothing.

  tools/precommit_gate.py  Already resolves the root properly - from the
      command's `-C`, then `git rev-parse --show-toplevel` in the hook's CWD -
      and the literal is a documented LAST resort reached only when there is no
      git at all. Not the defect, and deliberately left in place. What it gains
      here is one rung: `CLAUDE_PROJECT_DIR`, which the harness now exports into
      every hook process (measured on CLI 2.1.251), tried BEFORE the literal, so
      the final fallback names the right tree instead of one particular tree.

  ops/loop/launch_loop.ps1 and tools/gemini_audit.ps1  Launchers that pinned
      their repo root. Their two siblings, `tools/headless_run.ps1` and
      `tools/weekly_hygiene_run.ps1`, already derive it with
      `Split-Path -Parent $PSScriptRoot` - which is what makes these two the odd
      ones out rather than a matter of taste. `.githooks/` got the same thing
      right from the start with `git rev-parse --show-toplevel`.

`$CLAUDE_PROJECT_DIR` is NOT used in any of these: it is a hooks-layer feature
the harness substitutes into a hook command, so a `.ps1` launched from a
scheduled task would receive the literal characters. The scripts resolve from
their own location instead, and only `precommit_gate.py` - which runs as a hook
and therefore really does have the variable - reads it.
"""
from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS = REPO_ROOT / "tools"
sys.path.insert(0, str(TOOLS))

# A drive-absolute or UNC value assigned to a root-ish PowerShell variable, or
# used as its parameter default. Structural rather than a match on this repo's
# name, which would go green the moment the folder were renamed.
_PS_PINNED_ROOT = re.compile(
    r"\$(?:root|repoRoot)\s*=\s*\"(?:[A-Za-z]:[\\/]|\\\\)", re.IGNORECASE)

# The launchers, and the two siblings that already did it right - kept in the
# same list so the arm reads as one rule rather than two exceptions.
LAUNCHERS = [
    "ops/loop/launch_loop.ps1",
    "tools/gemini_audit.ps1",
    "tools/headless_run.ps1",
    "tools/weekly_hygiene_run.ps1",
]


def _load(name: str):
    """Import a `tools/` script by bare name, the way its siblings do."""
    spec = importlib.util.spec_from_file_location(name, TOOLS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# ---------------------------------------------------------------------------
# tools/text_first_guard.py - the escape-hatch flag
# ---------------------------------------------------------------------------

def test_the_visual_flag_resolves_under_the_repo_that_holds_the_script(monkeypatch):
    """No env at all: the flag must still land in THIS checkout, not a literal."""
    monkeypatch.delenv("CLAUDE_PROJECT_DIR", raising=False)
    guard = _load("text_first_guard")
    flag = guard.flag_path()
    assert flag == REPO_ROOT / "ops" / "runtime" / "allow_visual.flag", (
        f"the escape hatch resolved to {flag}, which is not this checkout - a "
        "hook reading another tree's override grants a bypass nobody asked for "
        "here, and ignores the one dropped in the tree being edited")


def test_the_visual_flag_follows_CLAUDE_PROJECT_DIR_when_the_harness_sets_it(
        monkeypatch, tmp_path):
    """The harness exports it into every hook process; honour it when present."""
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
    guard = _load("text_first_guard")
    assert guard.flag_path() == tmp_path / "ops" / "runtime" / "allow_visual.flag"


def test_the_visual_flag_path_carries_no_literal_drive_letter():
    text = (TOOLS / "text_first_guard.py").read_text(encoding="utf-8")
    offenders = [ln.strip() for ln in text.splitlines()
                 if "allow_visual.flag" in ln and re.search(r"[A-Za-z]:\\\\?Legion", ln)]
    assert not offenders, f"the flag path is still pinned to one tree: {offenders}"


# ---------------------------------------------------------------------------
# tools/precommit_gate.py - the last rung of the fallback chain
# ---------------------------------------------------------------------------

def test_the_gate_falls_back_to_CLAUDE_PROJECT_DIR_before_the_literal(monkeypatch, tmp_path):
    """The literal stays as the FINAL rung; this only inserts a better one above it."""
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
    gate = _load("precommit_gate")
    assert gate.fallback_root() == str(tmp_path)


def test_the_gate_still_has_a_last_resort_when_nothing_is_set(monkeypatch):
    """Removing the literal would be a regression: it is the no-git-at-all arm."""
    monkeypatch.delenv("CLAUDE_PROJECT_DIR", raising=False)
    gate = _load("precommit_gate")
    assert gate.fallback_root(), "the gate lost its final fallback entirely"


# ---------------------------------------------------------------------------
# The PowerShell launchers
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("rel", LAUNCHERS)
def test_a_launcher_does_not_pin_its_repo_root(rel):
    """One rule, four files. Two of them already passed before this fix landed."""
    text = (REPO_ROOT / rel).read_text(encoding="utf-8")
    pinned = [ln.strip() for ln in text.splitlines() if _PS_PINNED_ROOT.search(ln)]
    assert not pinned, (
        f"{rel} pins its repo root: {pinned}. Derive it from $PSScriptRoot, as "
        "tools/headless_run.ps1 and tools/weekly_hygiene_run.ps1 already do - "
        "$CLAUDE_PROJECT_DIR is a hooks-layer substitution and would arrive "
        "here as literal characters.")


@pytest.mark.parametrize("rel", LAUNCHERS)
def test_a_launcher_derives_its_root_from_its_own_location(rel):
    text = (REPO_ROOT / rel).read_text(encoding="utf-8")
    assert "$PSScriptRoot" in text, f"{rel} never references $PSScriptRoot"


@pytest.mark.parametrize("planted", [
    '$root = "C:\\Legion Wallpaper"',
    '  [string]$RepoRoot = "C:\\Legion Wallpaper",',
    '$root = "D:/Some Clone"',
    '$root = "\\\\server\\share\\tree"',
])
def test_the_pinned_root_detector_fires(planted):
    """An arm nobody has seen fail asserts nothing."""
    assert _PS_PINNED_ROOT.search(planted), f"detector missed: {planted}"


@pytest.mark.parametrize("innocent", [
    '$root = Split-Path -Parent $PSScriptRoot',
    '$repo = Split-Path -Parent $PSScriptRoot',
    '$ctl = "$root\\ops\\loop\\control"',
    '$ahk = "C:\\Program Files\\AutoHotkey\\v2\\AutoHotkey64.exe"',
])
def test_the_pinned_root_detector_has_no_false_positives(innocent):
    assert not _PS_PINNED_ROOT.search(innocent), f"false positive: {innocent}"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
