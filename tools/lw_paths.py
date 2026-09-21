"""Account-free resolution of the few machine paths LW's tools need.

# arch: shared path resolution for tools/ - no account name is spelled anywhere

WHY THIS EXISTS. LW has been PUBLIC under Apache-2.0 since 2026-08-01, and until
2026-09-07 sixty-eight tracked files spelled the operator's home directory out
in full. A literal `C:\\Users\\<account>\\...` buys nothing an environment lookup
does not, and it publishes the account name plus the machine's layout. This
module is the one place the layout is written down, so the eight tool sites that
used to carry their own copy now carry an import instead.
`tests/test_no_account_paths.py` is the guard that keeps it that way.

NOT A PACKAGE. `tools/` is a flat directory of scripts run as
`python tools/<name>.py`, so siblings import each other by bare name
(`import lw_paths`) exactly as `lw_agent_mirror` imports `lw_rundash_state`.
The test suite puts `tools/` on `sys.path` for the same reason.

EVERY LOOKUP DEGRADES RATHER THAN RAISES. These run on CI runners and in
throwaway fixtures where `LOCALAPPDATA` is absent and no Legion install exists.
A resolver that raised there would turn an unrelated test red, so each function
falls back to something that works: `Path.home()` for the profile, and the
running interpreter for Python.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# The Legion install this project pins. Kept as a version-specific directory
# name rather than a glob: the point of pinning is that a second interpreter on
# the box cannot silently win, and `py` resolving to a pytest-less
# pythoncore-3.14-64 install is a measured failure (see tools/truth_gate.py).
PINNED_PYTHON_DIR = "Python314"


def user_home() -> Path:
    """The operator profile directory. USERPROFILE, then Path.home()."""
    return Path(os.environ.get("USERPROFILE") or Path.home())


def local_app_data() -> Path:
    """`%LOCALAPPDATA%`, derived from the profile when the variable is unset."""
    return Path(os.environ.get("LOCALAPPDATA") or user_home() / "AppData" / "Local")


def pinned_python() -> Path:
    """Where the pinned interpreter lives on Legion. May not exist elsewhere."""
    return (local_app_data() / "Programs" / "Python" / PINNED_PYTHON_DIR
            / "python.exe")


def system_python() -> str:
    """The interpreter to hand a subprocess. NEVER a `pythonw` build.

    The pinned install when it is present, otherwise whichever interpreter is
    running right now. Returned as `str` because every caller passes it straight
    into an argv list or an f-string.

    THE CONSOLE GUARANTEE, and why it is load-bearing (measured 2026-09-20).
    LW's hooks are invoked as `pythonw <script>`, so inside a hook
    `sys.executable` is `pythonw.exe` - the console-less build. A subprocess run
    under it has NO stdout attached, so output is DISCARDED and the child still
    exits 0:

        py      -m ruff --version  ->  rc=1  stdout=''   (no module named ruff)
        pythonw -m ruff --version  ->  rc=0  stdout=''   (ran, output binned)
        python  -m ruff --version  ->  rc=0  stdout='ruff 0.15.12'

    The middle row is the dangerous one: a caller that checks the return code
    still sees success and an empty result, which reads as "the tool found
    nothing". That is how `tools/precommit_gate.py` came to run a ruff pass that
    could never report anything. Any resolver used to spawn a tool whose OUTPUT
    is the result must therefore refuse to hand back a `pythonw`.
    """
    pinned = pinned_python()
    try:
        if pinned.exists():
            return str(pinned)
    except OSError:
        pass
    return _console_twin(sys.executable)


def _console_twin(exe: str) -> str:
    """`exe`, or its console sibling when it is a `pythonw` build.

    `pythonw.exe` and `python.exe` ship side by side in every CPython layout on
    Windows, so the swap is a basename substitution in the same directory. Falls
    back to the original when the sibling is missing, because a wrong path is
    worse than a windowless one.
    """
    p = Path(exe)
    stem = p.stem.lower()
    if not stem.startswith("pythonw"):
        return exe
    twin = p.with_name(p.name.replace("pythonw", "python", 1))
    try:
        if twin.exists():
            return str(twin)
    except OSError:
        pass
    return exe


def pictures_dir() -> Path:
    """The operator's Pictures folder - the pipeline's delivery target."""
    return user_home() / "Pictures"


def desktop_dir() -> Path:
    """The operator's Desktop - where the headless runs drop their synopsis."""
    return user_home() / "Desktop"


def claude_project_dir(slug: str) -> Path:
    """`~/.claude/projects/<slug>` - transcripts and per-project memory."""
    return user_home() / ".claude" / "projects" / slug


def expand(value: str | os.PathLike[str]) -> Path:
    """Resolve a CONFIG value that may carry `~` or `%VAR%`.

    Config files record `~/Pictures` rather than an absolute path so the tracked
    bytes name nobody. Both spellings are expanded because the JSON in this repo
    uses `~` while prose and .ps1 use `%VAR%`, and a config edited by hand is as
    likely to use one as the other.
    """
    return Path(os.path.expandvars(str(value))).expanduser()
