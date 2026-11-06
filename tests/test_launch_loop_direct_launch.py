"""PY-ON-PATH, launcher side: launch_loop.ps1 never ShellExecutes python.

Start-Process without -NoNewWindow goes through ShellExecute, which applies
Python Manager's App Paths entry for python.exe and PREPENDS its WindowsApps
package dir to the child's PATH - so every descendant's bare `python` resolved
to a pythoncore install without pytest (2026-11-05). The launcher starts the
interpreter directly (System.Diagnostics.Process, UseShellExecute false,
CreateNoWindow true): no App Paths, no console window.

Static arms on the script text; the PowerShell 5.1 parse arm runs only where
powershell.exe exists (Windows), guarded before the call.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "ops" / "loop" / "launch_loop.ps1"


def _code_lines() -> list[str]:
    return [ln for ln in SCRIPT.read_text(encoding="ascii").splitlines()
            if not ln.lstrip().startswith("#")]


def test_python_is_never_started_through_start_process():
    hits = [ln for ln in _code_lines() if re.search(r"Start-Process\s+\$py\b", ln)]
    assert not hits, hits


def test_the_direct_launch_disables_shell_execute_and_the_console():
    text = "\n".join(_code_lines())
    assert re.search(r"\.UseShellExecute\s*=\s*\$false", text)
    assert re.search(r"\.CreateNoWindow\s*=\s*\$true", text)
    calls = re.findall(r"Start-Direct\s+\$py\b", text)
    assert len(calls) == 2, calls


def test_the_script_is_ascii_and_lf():
    raw = SCRIPT.read_bytes()
    assert raw.isascii() and b"\r" not in raw


def test_the_script_parses_under_windows_powershell_5_1():
    if os.name != "nt":
        return
    exe = shutil.which("powershell.exe")
    if not exe:
        return
    cmd = ("$e=$null; [void][System.Management.Automation.Language.Parser]::ParseFile("
           f"'{SCRIPT}', [ref]$null, [ref]$e); if ($e.Count) {{ $e | ForEach-Object "
           "{ $_.Message }; exit 1 }")
    r = subprocess.run([exe, "-NoProfile", "-NonInteractive", "-Command", cmd],
                       capture_output=True, text=True, timeout=60,
                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    assert r.returncode == 0, r.stdout + r.stderr
