"""An emptied parametrize pin must be RED, and this proves it live.

LW found this class and broadcast it: pytest's DEFAULT for a parametrize with
zero cases is to emit one SKIPPED placeholder, so a pin that empties takes its
arms with it and the run still exits 0. Measured on this tree before the repair,
and recorded in tests/test_loop_concurrency.py: `SHARED_SHA256 = {}` - a single
dict literal - reduced the four-arm cross-repo parity guard to "1 passed, 3
skipped", exit 0, green.

`empty_parameter_set_mark = fail_at_collect` in pytest.ini closes it. This file
is the BEHAVIOURAL half of that fix, and the behavioural half is the one that
matters: sibling SS reported that an arm which merely reads the value back out
of the ini is the weaker half - it proves a string is present in a file, not
that pytest is acting on it. A typo in the section header, a second ini file
winning the rootdir race, or a future `-c` override would all leave that arm
green. So the arms below run a REAL pytest subprocess against a crafted
zero-case parametrize and observe the collection outcome.

Hermetic by construction:
  - the fixture file and every ini are written into tmp_path, never the repo;
  - nothing is read from the repo except pytest.ini itself, which IS the
    artifact under test, resolved relative to __file__ rather than from an
    absolute path (CLAUDE.md: no account paths in tracked files);
  - the subprocess gets an explicit `-c`, so no rootdir discovery and no
    inherited addopts can decide the outcome;
  - `-p no:cacheprovider` keeps it from writing a cache anywhere.

The negative control is the point of the pair. An arm that only watches the
real ini go red cannot tell "the setting is in effect" from "the fixture is
broken and errors for some other reason". The control runs the SAME fixture
under an ini WITHOUT the line and requires it to go green-with-a-skip, which is
the old defective behaviour reproduced on demand.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
REAL_INI = REPO_ROOT / "pytest.ini"

SETTING = "empty_parameter_set_mark"
WANT = "fail_at_collect"

# No-console-flash rule (CLAUDE.md): every subprocess passes
# creationflags=NO_WINDOW. CREATE_NO_WINDOW exists only on Windows, so the
# os.name check happens HERE, at module import, BEFORE any call site - not
# inside the call, where a Linux CI run would raise AttributeError.
NO_WINDOW = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0

# A parametrize over an empty collection. Written as a literal `[]` rather than
# an emptied pin because the defect is about the ZERO-CASE collection, and a
# literal cannot be accidentally non-empty on some machine.
FIXTURE = """
import pytest


@pytest.mark.parametrize("case", [])
def test_arm_over_an_emptied_pin(case):
    raise AssertionError("must never run - there are no cases")


def test_a_second_test_so_the_file_is_not_empty():
    assert True
"""

# The same empty pin, but saying AT THE CALL SITE that it is allowed to be
# empty. MEASURED, because the spelling that reads most naturally does not
# exist: `empty_parameter_set_mark` is an INI-ONLY option (_pytest/mark/
# structures.py names it EMPTY_PARAMETERSET_OPTION), and passing it as a
# parametrize kwarg raises `TypeError: Metafunc.parametrize() got an unexpected
# keyword argument`. This arm is why that was found at all - the read-back half
# of this fix would have shipped the wrong instruction in pytest.ini's comment.
#
# The working opt-out keeps the set non-empty with one SKIPPED sentinel case.
FIXTURE_WITH_OPT_OUT = """
import pytest

ALLOWED_TO_BE_EMPTY = []

# DELIBERATELY empty, recorded here with a reason rather than relying on a
# global default, so a reviewer sees the decision in the diff.
_SENTINEL = [pytest.param(
    None, marks=pytest.mark.skip(reason="ALLOWED_TO_BE_EMPTY is empty on purpose"))]


@pytest.mark.parametrize("case", ALLOWED_TO_BE_EMPTY or _SENTINEL)
def test_arm_that_is_allowed_to_have_no_cases(case):
    raise AssertionError("must never run - there are no cases")
"""

# The kwarg spelling that does NOT work, pinned so the file records the
# measurement rather than leaving a future reader to rediscover it.
FIXTURE_WITH_BOGUS_KWARG = """
import pytest


@pytest.mark.parametrize("case", [],
                         empty_parameter_set_mark=pytest.mark.skip(reason="nope"))
def test_arm(case):
    raise AssertionError("must never run")
"""

INI_WITHOUT_SETTING = "[pytest]\n"
INI_WITH_SETTING = f"[pytest]\n{SETTING} = {WANT}\n"


def _run(ini: Path, fixture: Path) -> subprocess.CompletedProcess[str]:
    """Collect `fixture` under `ini` in a real pytest subprocess."""
    return subprocess.run(
        [sys.executable, "-m", "pytest", "-c", str(ini), str(fixture),
         "--collect-only", "-q", "-p", "no:cacheprovider"],
        capture_output=True, text=True, check=False, cwd=str(fixture.parent),
        creationflags=NO_WINDOW,
    )


def _write(tmp_path: Path, ini_text: str, fixture_text: str) -> tuple[Path, Path]:
    ini = tmp_path / "probe.ini"
    fixture = tmp_path / "test_probe_fixture.py"
    ini.write_text(ini_text, encoding="ascii")
    fixture.write_text(fixture_text, encoding="ascii")
    return ini, fixture


def test_the_real_ini_makes_a_zero_case_parametrize_fail_at_collect(tmp_path):
    """The load-bearing arm: LW's OWN pytest.ini, live, on a crafted fixture."""
    _ini, fixture = _write(tmp_path, "", FIXTURE)
    proc = _run(REAL_INI, fixture)
    combined = proc.stdout + proc.stderr
    assert proc.returncode != 0, (
        "a zero-case parametrize collected CLEANLY under the repo's own "
        f"pytest.ini, so an emptied pin still exits 0:\n{combined[-2000:]}")
    assert "error" in combined.lower(), (
        f"expected a collection error, got:\n{combined[-2000:]}")
    assert "skipped" not in combined.lower(), (
        "the zero-case arm was SKIPPED rather than errored - that is the "
        f"defective default, so the setting is not in effect:\n{combined[-2000:]}")


def test_without_the_setting_the_same_fixture_goes_green_with_a_skip(tmp_path):
    """Negative control. Proves the red above comes from the SETTING.

    This is the defect reproduced on demand: same fixture, ini missing one
    line, and pytest reports a skip and exits 0.
    """
    ini, fixture = _write(tmp_path, INI_WITHOUT_SETTING, FIXTURE)
    proc = _run(ini, fixture)
    combined = proc.stdout + proc.stderr
    assert proc.returncode == 0, (
        "the control did not reproduce the old behaviour, so the arm above is "
        f"not isolating the setting:\n{combined[-2000:]}")
    assert "error" not in combined.lower(), (
        f"the control errored for some unrelated reason:\n{combined[-2000:]}")


def test_a_minimal_ini_carrying_only_the_setting_is_enough(tmp_path):
    """Isolates the setting from everything else in the repo's ini.

    If the real-ini arm ever reds for an unrelated reason, this one says
    whether the setting itself still behaves.
    """
    ini, fixture = _write(tmp_path, INI_WITH_SETTING, FIXTURE)
    proc = _run(ini, fixture)
    assert proc.returncode != 0, proc.stdout + proc.stderr


def test_the_call_site_opt_out_still_collects_green(tmp_path):
    """The escape hatch works, so a deliberately-empty pin has a way to say so.

    Without this, the only way past a collection error would be to re-grow a
    pin that is meant to be empty - which is exactly what
    tests/test_loop_concurrency.py forbids for KNOWN_CODE_HITS.
    """
    _ini, fixture = _write(tmp_path, "", FIXTURE_WITH_OPT_OUT)
    proc = _run(REAL_INI, fixture)
    combined = proc.stdout + proc.stderr
    assert proc.returncode == 0, (
        "the skipped-sentinel opt-out still failed collection, so a "
        f"deliberately-empty pin has no way to say so:\n{combined[-2000:]}")


def test_the_kwarg_spelling_of_the_opt_out_does_not_exist(tmp_path):
    """Pins the measurement that corrected pytest.ini's own comment.

    `empty_parameter_set_mark` is ini-only. If a future pytest makes it a valid
    parametrize kwarg, this arm reds and the guidance in pytest.ini and in the
    comment above FIXTURE_WITH_OPT_OUT should be widened to offer it - rather
    than that guidance silently going stale.
    """
    _ini, fixture = _write(tmp_path, "", FIXTURE_WITH_BOGUS_KWARG)
    proc = _run(REAL_INI, fixture)
    combined = proc.stdout + proc.stderr
    assert proc.returncode != 0 and "unexpected keyword argument" in combined, (
        "empty_parameter_set_mark now appears to work as a parametrize kwarg - "
        f"update the opt-out guidance in pytest.ini:\n{combined[-2000:]}")


def test_the_ini_declares_the_setting(tmp_path):
    """The WEAKER half, kept only as a fast canary.

    On its own this proves a string is in a file. It is here because it names
    the setting and the file in the failure text, which turns a confusing
    subprocess error above into a one-line diagnosis. It is NOT the proof.
    """
    text = REAL_INI.read_text(encoding="ascii")
    lines = [ln.strip() for ln in text.splitlines()
             if ln.strip().startswith(SETTING)]
    assert lines == [f"{SETTING} = {WANT}"], (
        f"expected exactly one `{SETTING} = {WANT}` line in {REAL_INI.name}, "
        f"found {lines}")


def test_the_subprocess_flag_is_guarded_for_non_windows():
    """CREATE_NO_WINDOW exists only on Windows; CI runs Linux."""
    if os.name == "nt":
        assert NO_WINDOW == subprocess.CREATE_NO_WINDOW
        assert NO_WINDOW != 0
    else:
        assert NO_WINDOW == 0
