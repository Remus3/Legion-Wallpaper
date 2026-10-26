"""BLAS / OpenMP thread caps for the suite (MAIN suite-speed ORDER 2026-10-25).

Measured on Legion 2026-10-25 (psutil private bytes, one fresh process):
`import numpy` commits 500 MB and `import scipy.ndimage` 1010 MB with the
default thread pools (one OpenBLAS buffer per logical CPU, 16 here), against
18 MB and 46 MB with OPENBLAS_NUM_THREADS=1 / OMP_NUM_THREADS=1. Every xdist
worker paid that, and every worker running its own 16-thread BLAS pool beside
7 other workers only oversubscribes the CPU. tests/conftest.py pins the caps
with setdefault BEFORE any test module imports numpy, so an explicit value
(CI, a debugging run) still wins, and subprocesses a test starts inherit them.
"""
from __future__ import annotations

import os
import subprocess
import sys

import pytest

CAPS = ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS")


@pytest.mark.parametrize("name", CAPS)
def test_conftest_caps_the_thread_pools(name):
    value = os.environ.get(name)
    assert value, f"{name} is not set by tests/conftest.py"


def test_conftest_sets_the_caps_before_numpy_is_imported():
    text = open(os.path.join(os.path.dirname(__file__), "conftest.py"),
                encoding="utf-8").read()
    for name in CAPS:
        at = text.find(f'os.environ.setdefault("{name}", "1")')
        assert at != -1, name
        assert "numpy" not in text[:at], f"numpy is named before the {name} cap"


def test_a_child_python_inherits_the_caps():
    want = os.environ.get("OPENBLAS_NUM_THREADS")
    out = subprocess.run(
        [sys.executable, "-c",
         "import os; print(os.environ.get('OPENBLAS_NUM_THREADS'))"],
        capture_output=True, text=True, stdin=subprocess.DEVNULL,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    assert out.stdout.strip() == want
