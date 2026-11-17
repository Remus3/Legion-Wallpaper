"""scipy is a CI dependency of the per-push and nightly suites (MAIN ORDER
2026-11-16-2005 item 3).

tests/test_lw_veil_pass4.py reaches tools/lw_veil_pass5.py, which imports
scipy.ndimage lazily; both suite jobs install requirements.txt only, so the
pass4 tests errored with ModuleNotFoundError (8 errors, every run since they
landed). The fix is the requirements file the jobs install from - exact,
hash-pinned, and the same version the cv lane pins - never an ad hoc pip line
in the workflow and never a skip-if-missing.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _pin(path: Path, name: str) -> str | None:
    m = re.search(rf"^{re.escape(name)}==(\S+)", path.read_text(encoding="utf-8"), re.M)
    return m.group(1) if m else None


def test_scipy_is_an_input_of_requirements_in():
    lines = [ln.strip() for ln in (ROOT / "requirements.in").read_text(encoding="utf-8").splitlines()]
    assert "scipy" in lines


def test_scipy_is_hash_pinned_in_requirements_txt():
    text = (ROOT / "requirements.txt").read_text(encoding="utf-8")
    pin = _pin(ROOT / "requirements.txt", "scipy")
    assert pin, "requirements.txt carries no scipy==<version> pin"
    block = text.split(f"scipy=={pin}", 1)[1].split("\n    # via", 1)[0]
    assert "--hash=sha256:" in block


def test_scipy_pin_matches_the_cv_lane():
    assert _pin(ROOT / "requirements.txt", "scipy") == _pin(ROOT / "requirements-cv.txt", "scipy")
    assert _pin(ROOT / "requirements.txt", "numpy") == _pin(ROOT / "requirements-cv.txt", "numpy")


def test_no_ad_hoc_scipy_install_in_the_workflow():
    ci = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    assert not re.search(r"pip install[^\n]*\bscipy\b", ci)
