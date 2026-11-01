"""Every wall-clock bound a test can FAIL on goes through fleet_test_guard.budget().

MAIN 2026-11-01-1223 item 6 (FLEET-9). budget() scales a bound by the live suite-gate
load factor, so a bound written as a bare number is a load-dependent flake: it passes
alone and goes red when the box is shared. 5c39ef3 wrapped the three bare elapsed
comparisons; the same bound also hides in `assert ev.wait(timeout=10)`, in a polling
`deadline = time.time() + 5` and in a tries-times-sleep loop.

What this scanner does not judge, on purpose: a `timeout=` on subprocess.run / join /
proc.wait is a hang guard, its expiry is not the claim under test, and pytest's own
per-test timeout sits above all of them. A bound a test expects to EXPIRE
(winmutex.hold(timeout=0.2)) must stay small and is not scaled.
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

TESTS = Path(__file__).resolve().parent
CLOCKS = {"time", "monotonic", "perf_counter"}
ELAPSED_NAMES = {"elapsed", "took", "dt", "wall", "duration"}


def _is_number(node: ast.AST) -> bool:
    return isinstance(node, ast.Constant) and isinstance(node.value, (int, float))


def _is_clock(node: ast.AST) -> bool:
    return (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
            and node.func.attr in CLOCKS
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id in {"time", "_time"})


def _is_elapsed(node: ast.AST) -> bool:
    if isinstance(node, ast.Name):
        return node.id in ELAPSED_NAMES
    return isinstance(node, ast.BinOp) and isinstance(node.op, ast.Sub) and _is_clock(node.left)


def bare_bounds(source: str) -> list[int]:
    """Line numbers of the bare wall-clock bounds a test can fail on."""
    hits = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Assert):
            for sub in ast.walk(node.test):
                if isinstance(sub, ast.Compare) and len(sub.ops) == 1 and isinstance(
                        sub.ops[0], (ast.Lt, ast.LtE, ast.Gt, ast.GtE)):
                    pair = (sub.left, sub.comparators[0])
                    if (_is_elapsed(pair[0]) and _is_number(pair[1])) or (
                            _is_elapsed(pair[1]) and _is_number(pair[0])):
                        hits.append(node.lineno)
                if (isinstance(sub, ast.Call) and isinstance(sub.func, ast.Attribute)
                        and sub.func.attr == "wait"
                        and any(k.arg == "timeout" and _is_number(k.value)
                                for k in sub.keywords)):
                    hits.append(node.lineno)
        if (isinstance(node, ast.Assign) and isinstance(node.value, ast.BinOp)
                and isinstance(node.value.op, ast.Add)
                and _is_clock(node.value.left) and _is_number(node.value.right)):
            hits.append(node.lineno)
    return sorted(set(hits))


@pytest.mark.parametrize("bad", [
    "assert elapsed < 3.0",
    "assert time.monotonic() - t0 < 30",
    "assert 30 > time.perf_counter() - t0",
    "assert ev.wait(timeout=10)",
    "deadline = time.time() + 5",
    "deadline = time.monotonic() + 30.0",
])
def test_the_scanner_catches_a_bare_bound(bad):
    assert bare_bounds(bad) == [1]


@pytest.mark.parametrize("good", [
    "assert elapsed < fleet_test_guard.budget(3.0)",
    "assert time.monotonic() - t0 < fleet_test_guard.budget(30)",
    "assert ev.wait(timeout=fleet_test_guard.budget(10))",
    "deadline = time.time() + fleet_test_guard.budget(5)",
    "assert rec['elapsed_s'] == 540.0",
    "old = time.time() - 9000",
    "proc.wait(timeout=30)",
    "os.utime(path, (time.time() + 10_000, time.time() + 10_000))",
])
def test_the_scanner_passes_a_budgeted_bound_and_a_non_bound(good):
    assert bare_bounds(good) == []


def test_no_test_file_carries_a_bare_wall_clock_bound():
    files = sorted(TESTS.rglob("test_*.py"))
    assert len(files) > 100, "the sweep must select a real corpus"
    found = {}
    for path in files:
        hits = bare_bounds(path.read_text(encoding="utf-8"))
        if hits:
            found[path.name] = hits
    assert not found, f"wrap these in fleet_test_guard.budget(): {found}"
