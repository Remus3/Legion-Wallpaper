"""LOG-LEAK-2: no log writer in tools/ reaches the live logs/ under the suite.

During the 2026-10-10 07:21-07:26 full suite the LIVE logs/2026-10-10.log took
`lw_g1_gate` "cambi degraded: ffmpeg not on PATH" lines and `lw_upscale`
winmutex ACQUIRED/RELEASED lines. LOG-LEAK (LEDGER 297) had closed the same
leak for lw_headless_env.log_refusal alone, with its own env seam; every other
writer still hard-coded `<repo>/logs`.

Fix, one mechanism: env `LW_LOG_DIR` (empty = unset), canonical resolver
lw_paths.log_dir(), honoured at CALL time by every writer that defaults to the
repo logs dir, and declared in lw_race_guards.ENV_ROOTS so fleet_test_guard
points it at tmp_path for every test and every child interpreter. Modules run
in a venv child that cannot import lw_paths mirror it inline (the
lw_upscale tools_dir precedent); the parametrized arm below pins each one.
"""
from __future__ import annotations

import datetime as dt
import importlib
import os
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import lw_paths  # noqa: E402
import lw_race_guards  # noqa: E402

ENV = "LW_LOG_DIR"
LIVE = ROOT / "logs"


def _live_today() -> Path:
    return LIVE / f"{dt.datetime.now():%Y-%m-%d}.log"


def _size(p: Path) -> int:
    try:
        return p.stat().st_size
    except OSError:
        return -1


def test_the_log_dir_env_is_a_declared_runtime_root():
    assert lw_race_guards.ENV_ROOTS.get(ENV) == "logs"
    assert lw_paths.LOG_DIR_ENV == ENV


def test_the_guard_points_the_log_dir_off_the_live_tree():
    got = os.environ.get(ENV, "").strip()
    assert got, "fleet_test_guard did not set LW_LOG_DIR for this test"
    assert Path(got).resolve() != LIVE.resolve()


def test_log_dir_resolution(monkeypatch, tmp_path):
    monkeypatch.delenv(ENV, raising=False)
    assert lw_paths.log_dir() == lw_paths.repo_root() / "logs"
    assert lw_paths.log_dir(tmp_path / "d") == tmp_path / "d"
    monkeypatch.setenv(ENV, "  ")
    assert lw_paths.log_dir() == lw_paths.repo_root() / "logs", "blank = unset"
    monkeypatch.setenv(ENV, str(tmp_path / "x"))
    assert lw_paths.log_dir() == tmp_path / "x"
    assert lw_paths.log_dir(tmp_path / "d") == tmp_path / "x", "env outranks"


# (module, writer attr, call) - every daily-log writer in tools/.
_DAILY = [
    ("lw_g1_gate", "_gpu_log", lambda f: f("ll2 probe")),
    ("lw_upscale", "_gpu_log", lambda f: f("ll2 probe")),
    ("lw_clean_sdxl", "_gpu_log", lambda f: f("ll2 probe")),
    ("lw_gen_run", "_gpu_log", lambda f: f("ll2 probe")),
    ("lw_wallpaper_rotate", "_log", lambda f: f("ll2 probe")),
    ("lw_headless_env", "log_refusal", lambda f: f("ll2", "probe")),
    ("lw_gen_qa", "_log_error", lambda f: f(RuntimeError("ll2 probe"))),
    ("lw_gen_curate_weapon_crops", "_log_error", lambda f: f(RuntimeError("ll2 probe"))),
    ("lw_gen_train_weapon_lora", "_log_error", lambda f: f(RuntimeError("ll2 probe"))),
    ("lw_gen_weaponpass", "_log_error", lambda f: f(RuntimeError("ll2 probe"))),
]


@pytest.mark.parametrize("mod_name,attr,call", _DAILY, ids=[m for m, _, _ in _DAILY])
def test_every_daily_log_writer_honours_the_env(mod_name, attr, call, monkeypatch, tmp_path):
    try:
        mod = importlib.import_module(mod_name)
    except ImportError as exc:  # a venv-only dependency on a lean runner
        pytest.skip(f"{mod_name} not importable here: {exc}")
    target = tmp_path / "redirected"
    monkeypatch.setenv(ENV, str(target))
    live = _live_today()
    before = _size(live)
    call(getattr(mod, attr))
    files = list(target.glob("*.log"))
    assert files, f"{mod_name}.{attr} ignored LW_LOG_DIR"
    assert "ll2" in files[0].read_text(encoding="utf-8")
    assert _size(live) == before, f"{mod_name}.{attr} wrote the live daily log"


def test_the_g1_cambi_degraded_path_leaves_the_live_log_alone(monkeypatch):
    g1 = importlib.import_module("lw_g1_gate")
    np = pytest.importorskip("numpy")
    monkeypatch.setattr(g1, "_ffmpeg_exe", lambda: None)
    live = _live_today()
    before = _size(live)
    assert g1.cambi_score(np.zeros((8, 8, 3), dtype=np.uint8)) is None
    assert _size(live) == before
    redirected = Path(os.environ[ENV])
    assert "cambi degraded" in "".join(
        p.read_text(encoding="utf-8") for p in redirected.glob("*.log"))


def test_the_upscale_mutex_path_leaves_the_live_log_alone(monkeypatch):
    up = pytest.importorskip("lw_upscale")
    import contextlib
    import types

    # A stand-in winmutex with the real hold(log=) contract: never touches the
    # live machine-wide GPU mutex, so a running GPU job cannot stall the suite.
    @contextlib.contextmanager
    def hold(name, *, timeout=None, log=None):
        log(f"winmutex: ACQUIRED {name}")
        yield None
        log(f"winmutex: RELEASED {name}")

    fake = types.SimpleNamespace(GPU_MUTEX="GPU", MutexTimeout=TimeoutError, hold=hold)
    monkeypatch.setattr(up, "_winmutex", lambda: fake)
    live = _live_today()
    before = _size(live)
    seen = []
    with up.gpu_lock("cuda", log=seen.append):
        pass
    assert seen, "gpu_lock emitted no winmutex line"
    assert _size(live) == before
    redirected = Path(os.environ[ENV])
    assert "winmutex" in "".join(
        p.read_text(encoding="utf-8") for p in redirected.glob("*.log"))


# A repo-logs path literal: `/ "logs"`, `"logs\..."` (.ps1) or join(..., "logs").
_LOGS_LITERAL = re.compile(r"""/\s*["']logs["']|["']logs\\|join\([^)\n]*["']logs["']""")


def test_no_writer_in_tools_spells_the_logs_dir_without_the_env_seam():
    """Static backstop for the next writer: a tools/ file that builds a path
    into the repo logs/ dir must also honour LW_LOG_DIR (or call
    lw_paths.log_dir), else the suite can write the operator's live log."""
    offenders = []
    for p in sorted(TOOLS.glob("*.py")) + sorted(TOOLS.glob("*.ps1")):
        text = p.read_text(encoding="utf-8", errors="replace")
        if _LOGS_LITERAL.search(text) and ENV not in text and "lw_paths.log_dir" not in text:
            offenders.append(p.name)
    assert offenders == []


@pytest.mark.parametrize("mod_name,const,leaf", [
    ("lw_monitor", "MONITOR_LOG", "lw_monitor.log"),
    ("lw_rundash", "RUNDASH_LOG", "lw_rundash.log"),
])
def test_daemon_default_log_files_honour_the_env(mod_name, const, leaf, monkeypatch, tmp_path):
    mod = importlib.import_module(mod_name)
    monkeypatch.setenv(ENV, str(tmp_path))
    assert mod.default_log_file() == tmp_path / leaf
    monkeypatch.delenv(ENV)
    assert mod.default_log_file() == getattr(mod, const)
