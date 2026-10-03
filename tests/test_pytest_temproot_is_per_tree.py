"""LW's tmp_path must not live in the machine-wide shared pytest root.

Every repo on this account wrote its tmp_path dirs into the ONE directory
`<TEMP>/pytest-of-<user>`, so a sibling tree's run, or any temp sweep that
targets that name, could remove a directory an LW test was still using. The
measured symptom (2026-10-03, responder A2 on fe71425): one
`FileNotFoundError [WinError 2]` on a temp path inside the child pytest of
tests/test_empty_parametrize_is_red.py, green 3 of 3 when re-run alone.
SS already relocates its root per tree; tests/conftest.py now does the same
for LW via PYTEST_DEBUG_TEMPROOT, which pytest reads lazily at first tmp_path
use, so setting it at conftest import is early enough.
"""
import os
import tempfile
from pathlib import Path

SHARED_TEMP = Path(tempfile.gettempdir()).resolve()


def test_temproot_env_is_set_and_is_not_the_shared_temp_dir():
    root = os.environ.get("PYTEST_DEBUG_TEMPROOT")
    assert root, "tests/conftest.py did not set PYTEST_DEBUG_TEMPROOT"
    assert Path(root).resolve() != SHARED_TEMP, (
        "PYTEST_DEBUG_TEMPROOT points at the shared temp dir, which is the "
        "default it was meant to move away from")


def test_tmp_path_lives_under_the_per_tree_root(tmp_path):
    root = Path(os.environ["PYTEST_DEBUG_TEMPROOT"]).resolve()
    assert tmp_path.resolve().is_relative_to(root), (
        f"tmp_path {tmp_path} is outside the per-tree root {root}")
