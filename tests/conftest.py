"""Suite-wide guards. Loaded before any test module imports.

YOLO_AUTOINSTALL: ultralytics monkey-patches `PIL.Image.open` globally at
import time (site-packages/ultralytics/utils/patches.py) and, on ANY exception
from it, assumes the file is HEIF and calls `check_requirements("pi-heif")`.
With ultralytics' default AUTOINSTALL=True that shells out to

    uv pip install --python <this venv> pi-heif
        --index-strategy=unsafe-best-match --break-system-packages

which resolves a DIFFERENT Pillow and replaces the one in the venv. Measured on
Legion 2026-08-11: a full-suite run under C:\\Tools\\lw-clean\\venv deleted 91
of Pillow's 103 files mid-run. Only the `.pyd` extensions survived, because the
running pytest process had them locked - which is why the wreckage looked like a
"half-deleted" install rather than an uninstall.

Two consequences, both fixed by pinning the env var off here:
  1. The suite silently MUTATED a shared toolchain venv over the network.
  2. `test_lw_wiki_swap_oneoff.py::test_verify_refuses_undecodable_bytes`
     failed only when an ultralytics-importing test ran earlier in the same
     process - the patch swallowed its deliberately-undecodable bytes and went
     looking for a codec instead of raising. That is test pollution, not a flake.

Set before any import of ultralytics so the module-level `env_bool` read sees it.

PYTEST_DEBUG_TEMPROOT: every repo on this account shared ONE tmp_path root,
`<TEMP>/pytest-of-<user>`, so a sibling's run or a temp sweep aimed at that name
could remove a dir an LW test was still using (2026-10-03: one WinError 2 inside
the child pytest of test_empty_parametrize_is_red.py, green 3 of 3 alone). LW now
gets its own root, `<TEMP>/pytest-legion-wallpaper`, named `pytest-*` so sweeps
that already spare pytest trees still recognise it. pytest reads the variable
lazily at first tmp_path use, so conftest import is early enough. setdefault, so
an explicit value (CI, a debugging run) still wins. Pinned by
tests/test_pytest_temproot_is_per_tree.py.
"""
import os
import tempfile
from pathlib import Path

os.environ.setdefault("YOLO_AUTOINSTALL", "false")

if not os.environ.get("PYTEST_DEBUG_TEMPROOT"):
    _temproot = Path(tempfile.gettempdir()) / "pytest-legion-wallpaper"
    _temproot.mkdir(exist_ok=True)          # pytest mkdirs only the child
    os.environ["PYTEST_DEBUG_TEMPROOT"] = str(_temproot)

try:                                        # PIL is absent on some lanes
    from PIL import Image as _PILImage
    _PRISTINE_IMAGE_OPEN = _PILImage.open
except Exception:                           # noqa: BLE001 - guard only
    _PILImage = None
    _PRISTINE_IMAGE_OPEN = None

import pytest


@pytest.fixture(autouse=True)
def _unpatch_pil_image_open():
    """Undo ultralytics' process-wide `PIL.Image.open` patch for every test.

    Killing the autoinstall (above) stops the venv damage but NOT the pollution:
    ultralytics still replaces `Image.open` with a wrapper that swallows the
    first exception and goes looking for a HEIF codec. Once any test imports
    ultralytics, every later test in that process inherits the wrapper - which
    is why `test_verify_refuses_undecodable_bytes` passes alone and fails in a
    full run. Restoring the pristine callable before each test makes the suite
    order-independent again.

    Captured at conftest import, i.e. before ultralytics can patch it.
    """
    if _PILImage is not None and _PRISTINE_IMAGE_OPEN is not None:
        _PILImage.open = _PRISTINE_IMAGE_OPEN
    yield


@pytest.fixture(autouse=True)
def _the_live_fleet_files_are_never_written(request, monkeypatch):
    """Redirect the fleet kit's files for EVERY test: status, budget, usage.

    Suite-wide because every headless path - responder, CI watchdog, loop
    executor, oracle, the `exec` / `spawn` CLI - now goes through MAIN's kit
    (kit v3), which writes `ops/loop/control/inbox_status.json`,
    `headless_budget.json` and `headless_usage.jsonl` under
    `lw_headless_env.FLEET_ROOT`. The widget reads the status file live and the
    budget gates real runs, so one forgotten redirect would show the operator a
    test's fake state as LW's, or spend LW's real budget. The adapter is imported
    HERE so it is always loaded, and so always redirected, before an arm runs.
    Guarded at the kit's writer, never by mtime: the armed lanes rewrite these
    files on their own schedule.
    """
    import sys
    tools = str(Path(__file__).resolve().parents[1] / "tools")
    if tools not in sys.path:
        sys.path.insert(0, tools)
    import lw_headless_env as he

    real = (Path(he.ROOT) / "ops" / "loop" / "control").resolve()
    tmp = request.getfixturevalue("tmp_path")
    monkeypatch.setattr(he, "FLEET_ROOT", tmp / "fleet_root")
    kit = he.kit
    original = kit._atomic_write
    hits: list[str] = []

    def _guarded(path, text):
        if Path(path).resolve().parent == real:
            hits.append(str(path))
            raise RuntimeError("test arm wrote a live fleet-kit file")
        return original(path, text)

    monkeypatch.setattr(kit, "_atomic_write", _guarded)
    yield
    assert hits == [], f"an arm wrote a live fleet-kit file: {hits}"


@pytest.fixture(autouse=True)
def _the_live_operator_task_log_is_never_touched(request, monkeypatch):
    """Point the operator-task engine (tools/lw_ops_tasks.py) at a per-test root.

    The engine's default store is ops/runtime/operator_tasks/, and the inbox
    responder runs `verify_pending()` on every `--once` tick. Without this, an
    arm that drives the responder's main would execute the LIVE pending checks
    and append verify events to the operator's real log. Env-var seam, read at
    call time by `lw_ops_tasks.default_root()`.
    """
    tmp = request.getfixturevalue("tmp_path")
    monkeypatch.setenv("LW_OPS_TASKS_ROOT", str(tmp / "operator_tasks"))
    yield


@pytest.fixture(autouse=True)
def _the_live_job_run_logs_are_never_written(request, monkeypatch):
    """Point tools/lw_runlog.py at a per-test root (ingest P0-4).

    The responder, CI watchdog and wallpaper tick append a run record on every
    invocation; an arm that drives their main must never append to the live
    ops/runtime/runlog/ that tools/lw_job_health.py judges.
    """
    tmp = request.getfixturevalue("tmp_path")
    monkeypatch.setenv("LW_RUNLOG_ROOT", str(tmp / "runlog"))
    yield
