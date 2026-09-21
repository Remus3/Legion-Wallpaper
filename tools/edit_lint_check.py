"""PostToolUse hook: ruff check + em-dash / smart-quote grep on Edit|Write targets.

Reads $CLAUDE_FILE_PATHS (space-separated) and runs:
  1. python -m ruff check --fix <python files>  (auto-fix when possible)
  2. byte scan for U+2014 / U+2013 / U+201C / U+201D / U+2018 / U+2019

Hook output is shown to the model. Stay terse. Exit 0 always (advisory, non-blocking)
so the operator's flow is never stopped by hook noise; Claude reads the warning
in tool output and can self-correct on the next edit.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

# Hooks run under windowless pythonw.exe; a console-subsystem child (the `py`
# launcher + ruff) would otherwise get a fresh console allocated - an on-screen
# + taskbar flash on every edit. CREATE_NO_WINDOW suppresses it (Windows-only;
# 0 elsewhere).
_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def _lint_python() -> str:
    """A CONSOLE interpreter to run ruff under. See `lw_paths.system_python`."""
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import lw_paths  # noqa: PLC0415 - lazy on purpose; a hook must not die
        #                  at import time over an optional helper.
        return lw_paths.system_python()
    except Exception:  # noqa: BLE001 - deliberately total; see the identical
        # guard in precommit_gate._lint_python. A hook that raises is worse than
        # a hook that falls back, and the fallback is a complete answer.
        exe = sys.executable
        if os.path.basename(exe).lower().startswith("pythonw"):
            twin = os.path.join(
                os.path.dirname(exe),
                os.path.basename(exe).replace("pythonw", "python", 1))
            if os.path.exists(twin):
                return twin
        return exe

_BANNED = {
    chr(0x2014): "em-dash",
    chr(0x2013): "en-dash",
    chr(0x201C): "smart-dquote-open",
    chr(0x201D): "smart-dquote-close",
    chr(0x2018): "smart-quote-open",
    chr(0x2019): "smart-quote-close",
}

_FROZEN_SKIP = ("logs/", "docs/_archive/", ".pyc", ".git/", "__pycache__/")


def _is_skippable(p: Path) -> bool:
    s = str(p).replace("\\", "/")
    return any(skip in s for skip in _FROZEN_SKIP)


def _scan_banned(path: Path) -> list[str]:
    try:
        data = path.read_bytes()
    except OSError:
        return []
    text = data.decode("utf-8", errors="replace")
    hits: list[str] = []
    for cp, name in _BANNED.items():
        count = text.count(cp)
        if count > 0:
            hits.append(f"{name} x{count}")
    return hits


def main() -> int:
    raw = os.environ.get("CLAUDE_FILE_PATHS", "").strip()
    if not raw:
        return 0
    paths = [Path(p) for p in raw.split() if p]
    paths = [p for p in paths if p.exists() and not _is_skippable(p)]
    if not paths:
        return 0

    py_files = [str(p) for p in paths if p.suffix == ".py"]
    if py_files:
        # `py` resolved a bare pythoncore build with no ruff on this box, so this
        # autofix silently did nothing from the day it was written until
        # 2026-09-20. `pythonw` is the other trap - it runs ruff and discards the
        # output at exit 0. `system_python()` carries the console guarantee.
        # Unlike the commit gate this pass is a convenience, not a gate: a miss
        # costs an unformatted line, not a false green, so it stays quiet on
        # failure. It reports a MISSING RUFF once, because "my autofix stopped
        # working" is otherwise invisible.
        try:
            proc = subprocess.run(
                [_lint_python(), "-m", "ruff", "check", "--fix", *py_files],
                check=False,
                capture_output=True,
                text=True,
                timeout=15,
                creationflags=_NO_WINDOW,
            )
            if "No module named ruff" in (proc.stderr or ""):
                sys.stderr.write(
                    "edit_lint_check: ruff is not importable under "
                    f"{_lint_python()} - the autofix pass did nothing.\n")
        except (OSError, subprocess.SubprocessError):
            pass

    flagged: list[str] = []
    for p in paths:
        hits = _scan_banned(p)
        if hits:
            flagged.append(f"  {p}: {', '.join(hits)}")
    if flagged:
        sys.stderr.write("BANNED-GLYPH FOUND (CLAUDE.md hard rule):\n")
        sys.stderr.write("\n".join(flagged) + "\n")
        sys.stderr.write("Fix: tools/strip_em_dashes.py + tools/strip_smart_quotes.py\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
