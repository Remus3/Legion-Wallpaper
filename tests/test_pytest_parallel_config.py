"""RRF-2.1: the suite runs under pytest-xdist, with a serial set kept out of it.

The full suite is ~4.5k node ids and ~255 s serial (measured 2026-10-08). It
runs in parallel as `-n auto --dist loadfile`: loadfile keeps every test of a
file on one worker, so module-level state and fixtures behave as they do
serially. Files that share MACHINE state across files (named mutexes, the loop
lane files, a bound port) or that time themselves carry `pytest.mark.serial`
and run in a second `-n0` pass. `tools/lw_suite.py` is the one place that pairs
the two passes; CI spells them out step by step.

Every arm here reads the real tracked files - a guard that reads a copy proves
nothing about what CI and the done gate actually run.
"""
from __future__ import annotations

import configparser
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

SERIAL_FILES = (
    "test_loop_concurrency.py",
    "test_gpu_mutex_wiring.py",
    "test_loop_lanes.py",
    "test_lw_httpd.py",
)
PLUGINS = ("pytest-xdist", "pytest-timeout")


def _ini() -> configparser.SectionProxy:
    cp = configparser.ConfigParser(interpolation=None)
    cp.read(ROOT / "pytest.ini", encoding="utf-8")
    return cp["pytest"]


def test_both_plugins_are_inputs_and_hash_pinned_in_both_lock_files():
    for stem in ("requirements", "requirements-cv"):
        names = [ln.strip().lower() for ln in
                 (ROOT / f"{stem}.in").read_text(encoding="utf-8").splitlines()
                 if ln.strip() and not ln.startswith("#")]
        lock = (ROOT / f"{stem}.txt").read_text(encoding="utf-8")
        for pkg in PLUGINS:
            assert pkg in names, f"{pkg} missing from {stem}.in"
            m = re.search(rf"^{re.escape(pkg)}==\S+ \\\n((?:\s+--hash=sha256:[0-9a-f]{{64}}.*\n)+)",
                          lock, re.M)
            assert m, f"{pkg} is not ==-pinned with --hash lines in {stem}.txt"


def test_ini_carries_timeout_durations_and_strict_markers():
    ini = _ini()
    assert ini.get("timeout", "").strip() == "120"
    addopts = ini.get("addopts", "").split()
    assert "--durations=25" in addopts
    assert "--strict-markers" in addopts
    # xdist is opted into by the suite runners, never by addopts: a bare
    # `pytest tests/` (truth_gate, the false-red probe, a developer) stays a
    # complete serial run that cannot skip the serial set.
    assert not any(a == "-n" or a.startswith("-n") or a.startswith("--numprocesses")
                   for a in addopts), addopts


def test_markers_are_registered():
    names = {ln.split(":", 1)[0].strip() for ln in _ini().get("markers", "").splitlines()
             if ln.strip()}
    assert {"serial", "slow", "subprocess", "git"} <= names, names


def test_serial_set_carries_the_mark():
    for name in SERIAL_FILES:
        text = (ROOT / "tests" / name).read_text(encoding="utf-8")
        assert re.search(r"^pytestmark\s*=\s*(\[[^\]]*)?pytest\.mark\.serial\b", text, re.M), name


def test_suite_runner_pairs_the_parallel_and_serial_passes():
    import lw_suite
    passes = lw_suite.passes(["-q"])
    assert len(passes) == 2
    par, ser = (" ".join(p) for p in passes)
    # -n 8, not -n auto (MAIN suite-speed ORDER 2026-10-25): auto = 16 workers
    # on the Legion box, and the suite gate runs 2 suites machine-wide, so one
    # auto suite oversubscribes the CPU and doubles its own peak commit. CI's
    # small runners keep -n auto (test_ci_suite_jobs_run_both_passes).
    assert "pytest tests/ -n 8 --dist loadfile -m not serial -q" in par
    assert "pytest tests/ -n0 -m serial -q" in ser


def test_suite_runner_is_red_when_either_pass_is_red_or_the_serial_set_is_empty():
    import lw_suite
    assert lw_suite.combine([0, 0]) == 0
    assert lw_suite.combine([1, 0]) == 1
    assert lw_suite.combine([0, 1]) == 1
    # exit 5 = no tests collected: an emptied serial set must not read green.
    assert lw_suite.combine([0, 5]) == 5


def test_done_gate_runs_the_two_pass_suite_through_the_suite_gate():
    import done_gate
    suites = [c for c in done_gate.default_checks(env={})
              if any(str(a).replace("\\", "/").endswith("tools/lw_suite.py") for a in c)]
    assert len(suites) == 1
    assert any(str(a).replace("\\", "/").endswith("fleet_suite_gate.py") for a in suites[0])
    assert not any(c[1:3] == ["-m", "pytest"] for c in done_gate.DEFAULT_CHECKS)


def test_ci_suite_jobs_run_both_passes():
    text = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    par = 'LW_REQUIRE_HOOK_GATE=1 pytest tests/ -n auto --dist loadfile -m "not serial"'
    ser = "LW_REQUIRE_HOOK_GATE=1 pytest tests/ -n0 -m serial"
    assert text.count(par) == 2, "check + nightly-full-suite each run the xdist pass"
    assert text.count(ser) == 2, "check + nightly-full-suite each run the -n0 serial pass"


def test_suite_runner_children_inherit_the_report_streams(monkeypatch):
    """With all std handles None, CREATE_NO_WINDOW gives the child a hidden
    console and the pytest report is lost (measured 2026-10-12); an explicit
    stdin makes the child inherit this process's stdout/stderr."""
    import subprocess

    import lw_suite
    seen = []

    class _R:
        returncode = 0

    def fake_run(cmd, **kw):
        seen.append(kw)
        return _R()

    monkeypatch.setattr(lw_suite.subprocess, "run", fake_run)
    assert lw_suite.main(["-q"]) == 0
    assert len(seen) == 2
    assert all(kw.get("stdin") is subprocess.DEVNULL for kw in seen)
    assert all("stdout" not in kw and "capture_output" not in kw for kw in seen)
