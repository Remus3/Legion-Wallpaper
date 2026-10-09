"""Every subprocess spawn in tools/ and ops/ must resolve CREATE_NO_WINDOW.

Under a pythonw.exe parent a console child allocates its OWN window, so a spawn
without the flag flashes a console on the operator's desktop. `tools/
lw_window_guard.py` has checked this since the guard was written, but two ways:

  DISCOVERY - it rglobs tools/ + ops/, so no file can hide from it. Kept.
  VALUE     - `if "creationflags" in call or "CREATE_NO_WINDOW" in call`. That
              is a SUBSTRING test standing in for a value check, and it passes
              on `creationflags=0`, on a comment mentioning the word, and on
              `getattr(subprocess, "CREATE_NO_WINDW", 0)` - a typo that returns
              0, spawns fine, and flashes anyway. Silent fail-open. Replaced
              here by an AST resolver that follows the argument to a value.

Second reason this file exists at all: the guard is a SESSION-START HOOK, so it
only ever runs on the machine that would show the flash. In CI it does not run.
A check that only executes in the environment that created the state cannot
catch a regression pushed from anywhere else. Riot Commander found the same two
shapes in its own copy (RC 2026-07-27); this is LW's half.
"""
from __future__ import annotations

import ast
import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


def _load_guard():
    """Import the HOOK's own resolver rather than reimplementing it here.

    Two copies would drift, and a drifted guard-checker that agrees with
    nothing is worse than none: CI would go green on a resolver the session
    hook does not use. The hook is the shipping artifact; this file tests it.
    """
    spec = importlib.util.spec_from_file_location(
        "lw_window_guard_under_test", ROOT / "tools" / "lw_window_guard.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


guard = _load_guard()

# Kit gap B (reported to MAIN with the v4 ANSWER) is CLOSED in kit v10 (MAIN
# 0839): `_run` passes a literal `creationflags=` to Popen, bound to its own
# parameter whose default is `_NO_WINDOW`; the resolver follows that default.
# The runtime arms below still prove spawn hands the flag to `_run`.
KIT_PATH = "ops/fleet_kit/fleet_headless.py"
SCAN_DIRS = guard.SCAN_DIRS
SPAWN_FUNCS = guard.SPAWN_FUNCS
FLAG_NAME = guard.FLAG_NAME
FLAG_VALUE = guard.FLAG_VALUE
_module_consts = guard._module_consts
resolves_to_flag = guard.resolves_to_flag


# Kit v12 (MAIN 2031) ships three flagless spawn sites LW may not patch
# (FLEET-COMMON 11): fleet_gitlock's pgrep probe and its git runner, and the
# suite gate's suite runner. Reported to MAIN as a kit defect (LEDGER 290). The
# guard itself keeps NO exemption - it still prints them at session start; this
# pin only keeps the suite honest about exactly which kit sites are known. It
# is a tripwire both ways: a new flagless site anywhere fails, and so does a kit
# release that fixes one (then shrink the set).
KNOWN_KIT_SPAWN_GAPS = {
    "ops/fleet_kit/fleet_gitlock.py:157",
    "ops/fleet_kit/fleet_gitlock.py:370",
    "ops/fleet_kit/fleet_suite_gate.py:252",
}


def _spawn_sites():
    """(path, lineno, creationflags-node-or-None) for every subprocess spawn."""
    sites = []
    for d in SCAN_DIRS:
        base = ROOT / d
        if not base.is_dir():
            continue
        for py in sorted(base.rglob("*.py")):
            if "__pycache__" in py.parts:
                continue
            try:
                tree = ast.parse(py.read_text(encoding="utf-8", errors="replace"))
            except SyntaxError:  # a syntax error is py_compile's job, not ours
                continue
            module = _module_consts(tree)
            scoped = guard._scoped_consts(tree, module)
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                consts = scoped.get(id(node), module)
                f = node.func
                is_spawn = (isinstance(f, ast.Attribute) and f.attr in SPAWN_FUNCS
                            and isinstance(f.value, ast.Name)
                            and f.value.id == "subprocess")
                if not is_spawn:
                    continue
                flags = next((k.value for k in node.keywords
                              if k.arg == "creationflags"), None)
                sites.append((py.relative_to(ROOT).as_posix(),
                              node.lineno, flags, consts))
    return sites


def test_there_are_spawn_sites_to_check():
    """Guard the guard: an empty sweep must not read as a pass."""
    assert len(_spawn_sites()) >= 5


def _site_params():
    """Every site; a pinned kit-defect site is a STRICT xfail (it must keep
    failing until the kit fixes it, then the pin has to go)."""
    out = []
    for site in _spawn_sites():
        marks = ()
        if f"{site[0]}:{site[1]}" in KNOWN_KIT_SPAWN_GAPS:
            marks = pytest.mark.xfail(strict=True, reason="kit defect reported to MAIN")
        out.append(pytest.param(*site, marks=marks))
    return out


@pytest.mark.parametrize("path,lineno,flags,consts",
                         _site_params(),
                         ids=lambda v: str(v) if isinstance(v, (str, int)) else "")
def test_spawn_site_sets_create_no_window(path, lineno, flags, consts):
    assert flags is not None, (
        f"{path}:{lineno} spawns a subprocess with no creationflags - under "
        f"pythonw.exe this flashes a console window on the operator's desktop")
    assert resolves_to_flag(flags, consts), (
        f"{path}:{lineno} passes creationflags but it does not resolve to "
        f"{FLAG_NAME}. A typo'd getattr returns 0, spawns fine, and flashes "
        f"anyway - which is why the substring check could not see this.")


def test_no_kit_site_is_flagless_since_v10():
    """Kit v10 closed gap B: the kit file holds no flagless spawn site at all."""
    assert [s[1] for s in _spawn_sites() if s[0] == KIT_PATH and s[2] is None] == []


def _kit():
    spec = importlib.util.spec_from_file_location("fleet_headless_flash", ROOT / KIT_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_kit_spawn_hands_run_the_no_window_flag(tmp_path):
    kit = _kit()
    seen = {}

    def run(argv, **kw):
        seen.update(kw)
        return subprocess.CompletedProcess(argv, 0, '{"result": "ok"}', "")

    kit.spawn(tmp_path, "LW", "hi", run=run,
              url_source=lambda: "http://127.0.0.1:9", connect=lambda *a, **k: _Conn(),
              exe_source=lambda: "claude.exe")
    assert seen["creationflags"] == kit._NO_WINDOW
    if sys.platform == "win32":
        assert seen["creationflags"] == subprocess.CREATE_NO_WINDOW


def test_kit_run_forwards_the_flag_to_popen(monkeypatch):
    kit = _kit()
    seen = {}

    class _P:
        returncode = 0

        def __init__(self, argv, **kw):
            seen.update(kw)

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def communicate(self, input=None, timeout=None):
            return "", ""

    monkeypatch.setattr(kit.subprocess, "Popen", _P)
    kit._run(["x"], creationflags=0x08000000)
    assert seen["creationflags"] == 0x08000000


class _Conn:
    def close(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


# ---- teeth, proved by mutation rather than asserted -------------------------

@pytest.mark.parametrize("src,expected", [
    ('subprocess.run(["x"], creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))', True),
    ('subprocess.run(["x"], creationflags=subprocess.CREATE_NO_WINDOW)', True),
    ('subprocess.run(["x"], creationflags=0x08000000)', True),
    # the motivating silent fail-open: returns 0, spawns, flashes
    ('subprocess.run(["x"], creationflags=getattr(subprocess, "CREATE_NO_WINDW", 0))', False),
    ('subprocess.run(["x"], creationflags=0)', False),
    ('subprocess.run(["x"], creationflags=subprocess.CREATE_NEW_CONSOLE)', False),
])
def test_resolver_rejects_what_the_substring_check_accepted(src, expected):
    tree = ast.parse(src)
    call = next(n for n in ast.walk(tree) if isinstance(n, ast.Call)
                and isinstance(n.func, ast.Attribute) and n.func.attr == "run")
    flags = next(k.value for k in call.keywords if k.arg == "creationflags")
    assert resolves_to_flag(flags, {}) is expected


@pytest.mark.parametrize("src,expected", [
    ('NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)', True),
    ('NO_WINDOW = 0x08000000 if sys.platform == "win32" else 0', True),
    ('NO_WINDOW = 0 if sys.platform == "win32" else 0', False),
])
def test_resolver_follows_module_level_constants(src, expected):
    tree = ast.parse(src + '\nsubprocess.run(["x"], creationflags=NO_WINDOW)\n')
    consts = _module_consts(tree)
    call = next(n for n in ast.walk(tree) if isinstance(n, ast.Call)
                and isinstance(n.func, ast.Attribute) and n.func.attr == "run")
    flags = next(k.value for k in call.keywords if k.arg == "creationflags")
    assert resolves_to_flag(flags, consts) is expected


def test_the_session_start_guard_reports_no_spawn_site_on_this_tree():
    """The SessionStart window guard resolves every site on this tree, the kit's
    `_run` included (its parameter default since kit v10; no exemption), except
    the pinned kit-defect sites above."""
    assert set(guard.check_spawns()) == KNOWN_KIT_SPAWN_GAPS


def test_the_guard_exemption_is_the_one_kit_forwarding_site_only(tmp_path, monkeypatch):
    """A flagless **kw spawn outside the kit is flagged (the kit file too, below)."""
    d = tmp_path / "tools"
    d.mkdir()
    (d / "x.py").write_text("import subprocess\n\ndef f(**kw):\n"
                            "    subprocess.Popen(['a'], **kw)\n", encoding="ascii")
    monkeypatch.setattr(guard, "ROOT", tmp_path)
    assert guard.check_spawns() == ["tools/x.py:4"]


# ---- kit v10: the forwarding gap is closed, so the exemption is retired -----
# MAIN 0839 (LW 1258 B): `_run` now passes a literal `creationflags=` to Popen,
# bound to its own parameter whose default is `_NO_WINDOW`. The resolver follows
# a Name to the innermost enclosing def's parameter default; a parameter with no
# default (or a 0 default) shadows any module constant and fails closed.

@pytest.mark.parametrize("src,expected", [
    ("def f(cf=subprocess.CREATE_NO_WINDOW):\n"
     "    subprocess.Popen(['a'], creationflags=cf)\n", []),
    ("def f(cf=0):\n"
     "    subprocess.Popen(['a'], creationflags=cf)\n", ["tools/x.py:5"]),
    ("cf = subprocess.CREATE_NO_WINDOW\n"
     "def f(cf):\n"
     "    subprocess.Popen(['a'], creationflags=cf)\n", ["tools/x.py:6"]),
    ("def f(*, cf=0x08000000):\n"
     "    def g(cf=0):\n"
     "        subprocess.Popen(['a'], creationflags=cf)\n", ["tools/x.py:6"]),
])
def test_resolver_follows_the_enclosing_parameter_default(tmp_path, monkeypatch, src, expected):
    d = tmp_path / "tools"
    d.mkdir()
    (d / "x.py").write_text("import subprocess\n\n\n" + src, encoding="ascii")
    monkeypatch.setattr(guard, "ROOT", tmp_path)
    assert guard.check_spawns() == expected


def test_a_flagless_kwargs_spawn_in_the_kit_file_is_no_longer_exempt(tmp_path, monkeypatch):
    d = tmp_path / "ops" / "fleet_kit"
    d.mkdir(parents=True)
    (d / "fleet_headless.py").write_text("import subprocess\n\ndef f(**kw):\n"
                                         "    subprocess.Popen(['a'], **kw)\n", encoding="ascii")
    monkeypatch.setattr(guard, "ROOT", tmp_path)
    assert guard.check_spawns() == ["ops/fleet_kit/fleet_headless.py:4"]
