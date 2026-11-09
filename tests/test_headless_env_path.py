"""PY-ON-PATH: a headless child's PATH resolves bare `python` to THIS interpreter.

ROOT CAUSE (2026-11-05): Python Manager registers App Paths python.exe /
pythonw.exe / py.exe (HKCU and HKLM) whose Path value is the
`...\\WindowsApps\\PythonSoftwareFoundation.PythonManager_*` package dir. Any
ShellExecute launch of a python.exe PREPENDS that dir to the child's PATH, so a
bare `python` in every descendant resolved to a pythoncore install without
pytest. The kit's child_env copies os.environ as-is, so LW sanitizes PATH in
its adapter: every entry containing `\\WindowsApps\\PythonSoftwareFoundation.`
(case-insensitive) is dropped, and dirname(sys.executable) plus its Scripts
dir (Windows) are put first, deduplicated.

Hermetic: every arm injects the env and the interpreter path.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import lw_headless_env as he  # noqa: E402

_URL = "http://127.0.0.1:4999/tc-acct/fake-id"
SEP = os.pathsep
PYDIR = os.path.join(os.sep, "fake", "Python314")
EXE = os.path.join(PYDIR, "python.exe")
SCRIPTS = os.path.join(PYDIR, "Scripts")
# No drive colon off Windows: there os.pathsep is ":" and "C:\\..." splits into a
# stray "C" entry (CI nightly red 2026-11-06..08, run 42491770307).
PSF = (("C:" if os.name == "nt" else "")
       + "\\Program Files\\WindowsApps\\PythonSoftwareFoundation.PythonManager_26.0.0_x64__"
       "3847v3x7pw1km")
PSF_LOWER = PSF.lower()
OTHER = os.path.join(os.sep, "usr", "tools")


def _entries(value: str) -> list[str]:
    return [e for e in value.split(SEP) if e]


def _head():
    return [PYDIR, SCRIPTS] if os.name == "nt" else [PYDIR]


def test_psf_entries_are_dropped_and_this_interpreter_goes_first():
    env = {"PATH": SEP.join([PSF, OTHER, PSF_LOWER])}
    out = he.sane_path(env, exe=EXE)
    assert _entries(out["PATH"]) == [*_head(), OTHER]
    assert env["PATH"] == SEP.join([PSF, OTHER, PSF_LOWER]), "input must be copied"


def test_existing_interpreter_dirs_are_deduplicated_not_repeated():
    env = {"PATH": SEP.join([OTHER, PYDIR, "", OTHER])}
    assert _entries(he.sane_path(env, exe=EXE)["PATH"]) == [*_head(), OTHER]


def test_a_mixed_case_path_key_is_sanitized_in_place_on_windows():
    if os.name != "nt":
        return
    out = he.sane_path({"Path": SEP.join([PSF, OTHER])}, exe=EXE)
    assert [k for k in out if k.upper() == "PATH"] == ["Path"]
    assert _entries(out["Path"]) == [*_head(), OTHER]


def test_an_env_without_path_gets_the_interpreter_dirs():
    assert _entries(he.sane_path({}, exe=EXE)["PATH"]) == _head()


def _up(*_a, **_k):
    class _C:
        def close(self):
            pass
    return _C()


def test_child_env_hands_the_child_a_sanitized_path():
    base = {"PATH": SEP.join([PSF, OTHER])}
    env = he.child_env(base, url_source=lambda: _URL, connect=_up)
    entries = _entries(env["PATH"])
    assert not [e for e in entries if "pythonsoftwarefoundation." in e.lower()]
    assert entries[0] == os.path.dirname(sys.executable)
    assert entries[-1] == OTHER
    assert base["PATH"] == SEP.join([PSF, OTHER])


def test_spawn_hands_the_child_a_sanitized_path(monkeypatch):
    monkeypatch.setenv("PATH", SEP.join([PSF, OTHER]))
    seen = {}

    def run(argv, **kw):
        seen["kw"] = kw

        class _R:
            returncode = 0
            stdout = json.dumps({"result": "done", "usage": {"input_tokens": 5}})
            stderr = ""
        return _R()

    line = he.spawn("hello", note="2026-11-05-from-RC-ACK-x.md", kind="inbox",
                    url_source=lambda: _URL, connect=_up, run=run,
                    exe_source=lambda: "claude.exe")
    assert line["result"] == "done"
    entries = _entries(seen["kw"]["env"]["PATH"])
    assert not [e for e in entries if "pythonsoftwarefoundation." in e.lower()]
    assert entries[0] == os.path.dirname(sys.executable)
    assert os.environ["PATH"] == SEP.join([PSF, OTHER]), "os.environ is never mutated"
