r"""The commit gate's ruff pass must RUN, and a non-run must never read as clean.

MEASURED 2026-09-20, and this file exists because the pass was dead:

    py      -m ruff --version  ->  rc=1  stdout=''   no module named ruff
    pythonw -m ruff --version  ->  rc=0  stdout=''   ran, output DISCARDED
    python  -m ruff --version  ->  rc=0  stdout='ruff 0.15.12'

`tools/precommit_gate.py` invoked ruff through `py` and then did
`findings = json.loads(proc.stdout) if proc.stdout.strip() else []`, never
looking at the return code. So the ruff half of LW's pre-commit gate reported
zero findings on every commit from the day it was written. The glyph and
py_compile halves were unaffected.

`pythonw` is why a return-code check is NOT the repair. It exits 0 with empty
stdout, so `rc == 0` is satisfied by a pass that produced nothing - and LW's
hooks are invoked as `pythonw <script>`, which makes `sys.executable` the
pythonw build inside a hook. The discriminator that actually works:
`--output-format=json` ALWAYS emits at least `[]`, so EMPTY stdout is
unambiguously "did not report".

CLAUDE.md already records this same false-green family in this same file - the
gate was invoked with no args from 2026-07-03 and self-gated to a silent no-op,
"it ran on every commit and gated nothing". A breach recurring is a real
finding, so these arms INVOKE the resolver and the gate rather than grepping
their source for a reassuring substring. A source-text assertion is a claim
about text and would not have caught either instance.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import lw_paths  # noqa: E402
import precommit_gate as pg  # noqa: E402

_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def _run(argv: list[str], cwd: Path = ROOT) -> subprocess.CompletedProcess:
    return subprocess.run(argv, cwd=str(cwd), capture_output=True, text=True,
                          timeout=90, creationflags=_NO_WINDOW)


# ---- arming -----------------------------------------------------------------
# Without these the arms below can pass by finding nothing to test, which is the
# exact shape being guarded against.

def test_the_arms_below_have_something_to_run() -> None:
    assert (ROOT / "tools" / "precommit_gate.py").is_file()
    assert hasattr(pg, "_lint_python"), "the resolver under test is gone"
    target = ROOT / "tools" / "lw_paths.py"
    assert target.is_file() and target.stat().st_size > 1000


# ---- the resolver -----------------------------------------------------------

def test_the_lint_interpreter_can_actually_import_ruff() -> None:
    """The whole defect in one arm: ruff must be REACHABLE, measured.

    Not `"sys.executable" in source`. That substring was never the property that
    mattered - `py` and `pythonw` are both spelled plausibly too.
    """
    exe = pg._lint_python()
    proc = _run([exe, "-m", "ruff", "--version"])
    assert proc.returncode == 0, (
        f"{exe} cannot run ruff: rc={proc.returncode} stderr={proc.stderr!r}")
    assert proc.stdout.strip().startswith("ruff "), (
        f"{exe} -m ruff produced no version banner - stdout={proc.stdout!r}. "
        "An empty stdout at rc=0 is the pythonw signature: it ran and the "
        "output was discarded.")


def test_the_lint_interpreter_is_never_a_pythonw_build() -> None:
    exe = pg._lint_python()
    stem = os.path.splitext(os.path.basename(exe))[0].lower()
    assert not stem.startswith("pythonw"), (
        f"resolver returned the console-less build {exe}. A subprocess under it "
        "discards stdout and still exits 0, so any tool whose OUTPUT is the "
        "result silently returns nothing.")


def test_system_python_swaps_a_pythonw_path_for_its_console_twin() -> None:
    """The console guarantee, exercised on a constructed pythonw path."""
    real = Path(sys.executable)
    fake_w = real.with_name(real.name.replace("python", "pythonw", 1))
    if not fake_w.exists():  # pragma: no cover - layout without a pythonw
        pytest.skip(f"no pythonw beside {real}")
    got = lw_paths._console_twin(str(fake_w))
    assert not os.path.basename(got).lower().startswith("pythonw"), got
    assert Path(got).exists(), got


def test_the_console_twin_leaves_a_plain_python_alone() -> None:
    """The negative fixture: a matcher wide enough to fire must also be narrow."""
    assert lw_paths._console_twin(sys.executable) == sys.executable


# ---- the discriminator ------------------------------------------------------

def test_json_output_is_never_empty_so_empty_means_did_not_run() -> None:
    """The load-bearing premise of the repair, asserted against real ruff.

    If a future ruff ever emitted nothing for a clean file, the gate's
    empty-stdout test would start reading a real clean pass as a non-run. That
    would be loud (it reports a SKIP) rather than silent, but this arm is what
    tells us the premise moved.
    """
    exe = pg._lint_python()
    proc = _run([exe, "-m", "ruff", "check", "--output-format=json",
                 "tools/lw_paths.py"])
    assert proc.stdout.strip(), (
        "ruff emitted EMPTY stdout for a clean file; the gate's "
        "empty-means-did-not-run rule rests on this never happening")
    assert json.loads(proc.stdout) == [], proc.stdout[:200]


def test_a_real_violation_is_reported_as_json_so_the_pass_can_block(
        tmp_path: Path) -> None:
    """The working half still works: ruff must actually FIND a planted defect."""
    bad = tmp_path / "planted.py"
    bad.write_text("import os\n", encoding="utf-8")  # F401, unused import
    exe = pg._lint_python()
    proc = _run([exe, "-m", "ruff", "check", "--output-format=json",
                 "--isolated", "--select=F401", str(bad)])
    parsed = json.loads(proc.stdout)
    assert parsed, f"ruff found nothing in a file with an unused import: {proc}"
    assert any(f.get("code") == "F401" for f in parsed), parsed


def test_the_gate_reports_a_skip_rather_than_silence_when_ruff_cannot_run(
        tmp_path: Path) -> None:
    """A non-run must be VISIBLE. This is the arm the old code could not pass.

    Driven through a real subprocess with a real interpreter that has no ruff,
    so nothing here depends on how the gate is written internally.
    """
    probe = tmp_path / "probe.py"
    probe.write_text(
        "import subprocess, sys, json\n"
        "proc = subprocess.run([sys.executable, '-m', 'ruff_does_not_exist',\n"
        "                       'check', '--output-format=json'],\n"
        "                      capture_output=True, text=True)\n"
        "out = proc.stdout.strip()\n"
        "print(json.dumps({'rc': proc.returncode, 'empty': not out}))\n",
        encoding="utf-8")
    proc = _run([sys.executable, str(probe)])
    got = json.loads(proc.stdout)
    assert got["empty"], "a missing module must yield EMPTY stdout"
    assert got["rc"] != 0, (
        "a missing module exited 0 - then empty stdout is the ONLY signal left, "
        "which is precisely why the gate keys on stdout and not on the rc")
