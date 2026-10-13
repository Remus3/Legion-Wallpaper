#!/usr/bin/env python3
"""lw_suite: the whole LW test suite as its two passes (RRF-2.1).

# arch: one entry for the parallel + serial suite passes

    python tools/lw_suite.py [extra pytest args, e.g. -q]

Pass 1 runs everything not marked `serial` under pytest-xdist with
`-n auto --dist loadfile`. Pass 2 runs the `serial` set with `-n0`. Both passes
always run, so a red first pass still reports the serial set. The exit code is
the first non-zero pass code; an empty serial pass (pytest exit 5, "no tests
collected") is red, because an emptied serial set is a guard that vanished.

Run it through the kit's suite gate like any whole suite:
    python ops/fleet_kit/fleet_suite_gate.py run --owner <id> -- python tools/lw_suite.py -q
CI spells the same two commands out per step (.github/workflows/ci.yml);
tests/test_pytest_parallel_config.py keeps the three in step.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# CREATE_NO_WINDOW: 0 on non-Windows so the module imports in CI.
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)

PARALLEL = ["tests/", "-n", "auto", "--dist", "loadfile", "-m", "not serial"]
SERIAL = ["tests/", "-n0", "-m", "serial"]


def passes(extra: list[str]) -> list[list[str]]:
    """The two pytest argv lists, extra args appended to each."""
    base = [sys.executable, "-m", "pytest"]
    return [base + PARALLEL + list(extra), base + SERIAL + list(extra)]


def combine(codes: list[int]) -> int:
    """First non-zero exit code, else 0 (exit 5 on the serial pass is red)."""
    for code in codes:
        if code != 0:
            return code
    return 0


def main(argv: list[str] | None = None) -> int:
    extra = list(sys.argv[1:] if argv is None else argv)
    codes = []
    for cmd in passes(extra):
        print("lw_suite: " + " ".join(cmd[1:]), flush=True)
        # stdin=DEVNULL is load-bearing on Windows: with every std handle left
        # None, CREATE_NO_WINDOW hands the child a fresh hidden console and its
        # whole report vanishes (measured 2026-10-12). Any explicit handle sets
        # STARTF_USESTDHANDLES, so stdout/stderr inherit this process's own.
        codes.append(subprocess.run(cmd, cwd=ROOT, stdin=subprocess.DEVNULL,
                                    creationflags=NO_WINDOW).returncode)
    rc = combine(codes)
    print(f"lw_suite: parallel rc={codes[0]} serial rc={codes[1]} -> {rc}", flush=True)
    return rc


if __name__ == "__main__":
    sys.exit(main())
