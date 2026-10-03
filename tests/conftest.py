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
