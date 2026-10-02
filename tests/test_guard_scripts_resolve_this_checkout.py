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
import json
import os
import re
import subprocess
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


# ---------------------------------------------------------------------------
# tools/precommit_gate.py - WHICH TREE the PreToolUse stdin mode gates
#
# The rung above the fallbacks, and the one that was wrong. `--git-hook` mode is
# fine: git runs that hook with CWD at the worktree top, so `rev-parse
# --show-toplevel` there is the answer by construction. The PreToolUse stdin
# mode has no such guarantee - its CWD is the SESSION root, and the command it
# is handed may name a different tree entirely.
#
# Measured 2026-10-02 with a linked worktree and one em-dash staged:
#   `cd "<wt>" && git commit`, CWD=main, glyph staged in the WORKTREE
#       -> exit 0, no output. A FALSE GREEN: banned content passed because the
#          gate read the main tree's index instead.
#   `cd "<wt>" && git commit`, CWD=main, glyph staged in MAIN
#       -> exit 2 naming a file that does not exist in the worktree. A
#          WRONG-REASON RED, which is not a usable signal either.
#   `git -C "/c/Users/..."` (the MSYS path flavour)
#       -> exit 0. A THIRD false green, one layer down: `_git` runs with that
#          cwd, raises OSError, `_staged_added` swallows it and returns "", and
#          an empty diff reads as "no findings".
#
# The fixture below is hermetic - a real repo plus a real `git worktree add`
# under tmp_path - because the defect is entirely about which of two indexes
# gets read, and nothing short of two real indexes can tell the two apart.
# ---------------------------------------------------------------------------

EM_DASH = chr(0x2014)
GATE = TOOLS / "precommit_gate.py"


def _git_cmd(args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    """git with the ambient config that could break a fixture turned off."""
    return subprocess.run(
        ["git", "-c", "commit.gpgsign=false", "-c", "core.hooksPath=", *args],
        cwd=str(cwd), capture_output=True, text=True, timeout=120)


@pytest.fixture
def two_trees(tmp_path):
    """A real repo at tmp_path/main plus a real linked worktree at tmp_path/wt.

    Two separate indexes is the whole point: the gate's defect is reading the
    wrong one, and a single-tree fixture cannot observe that.
    """
    main = tmp_path / "main"
    wt = tmp_path / "wt"
    main.mkdir()
    _git_cmd(["init", "-b", "main"], main)
    _git_cmd(["config", "user.email", "fixture@example.invalid"], main)
    _git_cmd(["config", "user.name", "Fixture"], main)
    (main / "seed.txt").write_text("seed\n", encoding="utf-8")
    _git_cmd(["add", "-A"], main)
    _git_cmd(["commit", "-m", "seed", "--no-verify"], main)
    added = _git_cmd(["worktree", "add", str(wt), "-b", "side"], main)
    assert wt.is_dir(), f"the fixture worktree was not created: {added.stderr}"
    return main, wt


def _stage_glyph(tree: Path, name: str) -> None:
    (tree / name).write_text(f"a {EM_DASH} b\n", encoding="utf-8")
    assert _git_cmd(["add", name], tree).returncode == 0


def _hook_call(command: str, cwd: Path) -> subprocess.CompletedProcess:
    """Invoke the gate exactly as the PreToolUse hook does: no argv, JSON stdin.

    `cwd` is the knob under test - it stands in for the session root, which the
    harness does NOT guarantee is the tree the commit is about.
    """
    payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": command}})
    return subprocess.run(
        [sys.executable, str(GATE)], input=payload,
        capture_output=True, text=True, cwd=str(cwd), timeout=180)


def _said(proc: subprocess.CompletedProcess) -> str:
    return proc.stdout + proc.stderr


def test_a_cd_chained_commit_gates_the_tree_it_cds_INTO(two_trees):
    """arm A - the false green. Glyph in the worktree, main clean, cd into wt."""
    main, wt = two_trees
    _stage_glyph(wt, "bad_in_worktree.txt")
    r = _hook_call(f'cd "{wt}" && git commit -m "probe"', cwd=main)
    assert r.returncode != 0, (
        "the gate PASSED a staged em-dash. The commit runs in the worktree and "
        "the glyph is staged there; the gate read the session CWD's index "
        f"instead, found it clean, and reported success: {_said(r)!r}")
    assert "bad_in_worktree.txt" in _said(r), (
        "the gate blocked, but did not name the worktree file that is actually "
        f"staged - so it blocked for some other reason: {_said(r)!r}")


def test_a_cd_chained_commit_does_not_gate_the_tree_it_cd_AWAY_from(two_trees):
    """arm B - the wrong-reason red. Glyph in MAIN, worktree clean, cd into wt."""
    main, wt = two_trees
    _stage_glyph(main, "bad_in_main.txt")
    r = _hook_call(f'cd "{wt}" && git commit -m "probe"', cwd=main)
    assert "bad_in_main.txt" not in _said(r), (
        "the gate blocked the worktree's commit over a file staged in a "
        "DIFFERENT tree. Naming a path that does not exist where the commit "
        f"runs is not a usable signal: {_said(r)!r}")
    assert r.returncode == 0, (
        "the worktree's index is clean, so this commit must pass: "
        f"{r.returncode} {_said(r)!r}")


def test_a_dash_C_commit_still_gates_the_tree_it_names(two_trees):
    """arm C - the regression guard. This shape already worked; keep it working."""
    main, wt = two_trees
    _stage_glyph(wt, "bad_in_worktree.txt")
    r = _hook_call(f'git -C "{wt}" commit -m "probe"', cwd=main)
    assert r.returncode != 0, (
        f"`git -C <wt> commit` stopped gating the tree it names: {_said(r)!r}")
    assert "bad_in_worktree.txt" in _said(r), _said(r)


@pytest.mark.skipif(
    os.name != "nt",
    reason="the MSYS `/c/...` path flavour only exists alongside a drive letter")
def test_an_MSYS_flavoured_path_gates_identically_to_the_windows_one(two_trees):
    """arm D - `/c/Users/...` is what Git Bash hands over; it must resolve.

    The os.name check is on the DECORATOR, not inside the body: on POSIX there
    is no second flavour of the same path to disagree about, so the arm has
    nothing to assert rather than something to skip past mid-call.
    """
    main, wt = two_trees
    _stage_glyph(wt, "bad_in_worktree.txt")
    drive, rest = os.path.splitdrive(str(wt))
    msys = "/" + drive[0].lower() + rest.replace("\\", "/")
    r = _hook_call(f'git -C "{msys}" commit -m "probe"', cwd=main)
    assert r.returncode != 0, (
        f"the MSYS path {msys} resolved to nothing and the gate reported a "
        "pass. An unreachable cwd makes `git diff --cached` raise OSError, "
        "which `_staged_added` swallows into an empty diff - and an empty diff "
        f"reads as no findings: {_said(r)!r}")
    assert "bad_in_worktree.txt" in _said(r), _said(r)


def test_a_plain_commit_in_the_cwd_still_works_both_ways(two_trees):
    """arm E - the do-not-break-the-common-case arm, both polarities.

    A bare `git commit` names no tree at all, so the CWD IS the target by
    construction and resolving it there is not a guess. This is overwhelmingly
    the shape that actually runs, and a gate that started refusing it would be
    a worse defect than the one being fixed here.
    """
    main, _wt = two_trees
    clean = _hook_call('git commit -m "x"', cwd=main)
    assert clean.returncode == 0, (
        "an ordinary commit with a clean index must pass, and must not be "
        f"refused for an undeterminable tree: {clean.returncode} {_said(clean)!r}")
    _stage_glyph(main, "bad_in_main.txt")
    dirty = _hook_call('git commit -m "x"', cwd=main)
    assert dirty.returncode != 0, (
        f"an ordinary commit with a staged em-dash must block: {_said(dirty)!r}")
    assert "bad_in_main.txt" in _said(dirty), _said(dirty)


def test_an_unresolvable_target_tree_refuses_instead_of_gating_the_cwd(two_trees):
    """arm F - the refusal itself.

    Fail-open was a pass and fail-closed named a foreign file. Neither is
    readable, so the gate says what it could not determine instead.
    """
    main, _wt = two_trees
    _stage_glyph(main, "bad_in_main.txt")
    r = _hook_call('cd "$SOME_UNEXPANDED_VAR" && git commit -m "x"', cwd=main)
    assert r.returncode != 0, (
        "a commit whose target tree cannot be identified must not pass: "
        f"{_said(r)!r}")
    assert "bad_in_main.txt" not in _said(r), (
        f"the refusal fell back to gating the session CWD's index: {_said(r)!r}")
    assert "target tree" in _said(r).lower(), (
        f"the refusal does not say what it could not determine: {_said(r)!r}")


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
