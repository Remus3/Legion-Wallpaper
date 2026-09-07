"""The bare interpreter names in `.claude/settings.json` must actually RESOLVE.

WHY, and it is a warning taken from another tree rather than a defect found in
this one. On 2026-09-07 LW replaced the operator's hard-coded home path in all
eleven hook commands with the bare name `pythonw` (LEDGER 166). Lanternlight,
doing the same cleanup the same night, sent the failure mode with it:

    A parameterised path that does not RESOLVE is worse than a hardcoded one.
    [...] Two of the obvious candidate names on this machine resolve to
    Microsoft Store stubs rather than to a real interpreter.

That is the whole argument for this file. A hook naming an absent or stubbed
interpreter does not fail loudly - it reports NOTHING, which is
indistinguishable from a clean run and is the same silence class that let LW's
own gate self-gate to a no-op for three weeks in 2026-07. The Store stubs are
the specific trap: `%LOCALAPPDATA%\\Microsoft\\WindowsApps\\python.exe` exists,
is on PATH ahead of a real install for some accounts, and opens the Store
instead of running anything.

WHAT THIS ASSERTS. Not that a name is on PATH - `shutil.which` returning a path
is exactly what a stub also does. It asserts the resolved binary RUNS and
reports a version, which a stub cannot, and that it is not the WindowsApps
shim. The names are read out of the tracked settings file rather than retyped,
so this cannot drift into testing a name the hooks no longer use.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SETTINGS = REPO_ROOT / ".claude" / "settings.json"

# Windows only. On the Linux runner there is no settings.json semantics to test
# and no Store stub to fall into.
pytestmark = pytest.mark.skipif(
    sys.platform != "win32", reason="hook interpreter resolution is Windows-only")


def _hook_commands() -> list[str]:
    data = json.loads(SETTINGS.read_text(encoding="utf-8"))
    return [h["command"]
            for event in data.get("hooks", {}).values()
            for group in event
            for h in group.get("hooks", [])]


def _interpreter_names() -> set[str]:
    """The FIRST token of every hook command, which is the interpreter."""
    names = set()
    for cmd in _hook_commands():
        first = cmd.split()[0].strip('"')
        # An absolute path is its own proof and is not a PATH lookup.
        if "/" not in first and "\\" not in first:
            names.add(first)
    return names


def test_the_settings_file_actually_declares_hooks():
    """Guard the guard: no commands would make every assertion below vacuous."""
    cmds = _hook_commands()
    assert len(cmds) >= 10, f"only {len(cmds)} hook commands found in {SETTINGS}"


def test_every_hook_command_names_a_bare_interpreter():
    """The account-path fix is what put bare names here; keep it that way."""
    names = _interpreter_names()
    assert names, (
        "no hook command starts with a bare interpreter name - if these went "
        "back to absolute paths, check they do not carry an account name "
        "(tests/test_no_account_paths.py)")
    assert names <= {"python", "pythonw"}, f"unexpected interpreter(s): {names}"


@pytest.mark.parametrize("name", sorted(_interpreter_names()))
def test_the_interpreter_is_on_path(name):
    resolved = shutil.which(name)
    assert resolved, (
        f"`{name}` does not resolve on PATH, so every hook invoking it reports "
        "NOTHING - silence indistinguishable from a clean run")


@pytest.mark.parametrize("name", sorted(_interpreter_names()))
def test_the_interpreter_is_not_a_microsoft_store_stub(name):
    """A stub is on PATH and opens the Store. `which` alone cannot tell."""
    resolved = Path(shutil.which(name) or "")
    assert "WindowsApps" not in resolved.parts, (
        f"`{name}` resolves to the Microsoft Store stub at {resolved}, which "
        "launches the Store instead of running the script")


@pytest.mark.parametrize("name", sorted(_interpreter_names()))
def test_the_interpreter_actually_runs(name):
    """The assertion a stub cannot pass: it must EXECUTE and report a version.

    `pythonw` has no console, so the version is written to a file rather than
    read off stdout - reading stdout would test the console, not the binary.
    """
    proc = subprocess.run(
        [name, "-c", "import sys; sys.stdout.write(sys.version.split()[0])"],
        capture_output=True, text=True, timeout=60,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    assert proc.returncode == 0, (
        f"`{name}` resolved but did not run: rc={proc.returncode} "
        f"stderr={proc.stderr[:200]}")
    version = proc.stdout.strip()
    assert version.startswith("3."), (
        f"`{name}` ran but reported no usable version: {version!r}")
