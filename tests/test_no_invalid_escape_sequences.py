"""No authored .py may carry an invalid escape sequence.

Python emits a SyntaxWarning for a backslash pair it does not recognise, such
as the `C:\\Legion Wallpaper` written into a non-raw docstring or the
`"Global\\SOME-NAME"` written into a non-raw literal. Today it is a warning.
In a future Python it is a SyntaxError, so a file that merely warns now is a
file that stops importing later - and on this repo, where every path is a
Windows path with backslashes, the shape is easy to author by accident.

Two of these were live when this guard was written (2026-10-02):
`tests/test_drift_guard_sibling_root.py:4` ("\\L", inside a docstring quoting
two sibling repo roots) and `tests/test_p5_probe.py:156` ("\\S", inside a
mutex-name literal). Both were found as collateral - a sibling project's agent
noticed them in passing while fixing something else - which is the signal that
nothing was watching for them. Both were repaired by making the string raw,
and the VALUE was proven unchanged before the edit rather than after: for a
sequence Python does not recognise it already keeps the backslash, so
`"Global\\SOME"` and `r"Global\\SOME"` are the same string, and the repair
cannot move behaviour.

Fixing those two was fixing the instances. This fixes the class.

The sweep compiles rather than greps. A regex over source would have to model
raw prefixes, f-strings, concatenation, triple quotes and comments; `compile()`
is the same parser that will one day reject these, so it cannot disagree with
the thing being guarded against.
"""

import warnings
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parent.parent

# Authored trees only. A finding under a vendored tree is an upstream report,
# not a defect here, and .venv* is not ours at all.
_SCAN_DIRS = ("tests", "tools", "ops")
_SKIP_PARTS = ("dwpose_onnx",)


def _authored_py():
    for name in _SCAN_DIRS:
        d = _ROOT / name
        if not d.is_dir():
            continue
        for f in sorted(d.rglob("*.py")):
            if any(part in f.parts for part in _SKIP_PARTS):
                continue
            yield f


def _syntax_warnings(path: Path):
    """Compile one file and return its SyntaxWarnings as (lineno, message)."""
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        try:
            compile(path.read_bytes(), str(path), "exec")
        except SyntaxError as exc:  # pragma: no cover - a broken file is its own red
            pytest.fail(f"{path} does not compile: {exc}")
        return [
            (w.lineno, str(w.message))
            for w in caught
            if issubclass(w.category, SyntaxWarning)
        ]


def test_the_sweep_actually_finds_files():
    """Guard the guard: an empty scan would pass every arm below vacuously.

    This is the arm that catches a renamed directory or a glob that stopped
    matching. Without it, deleting `tests/` would turn this module green.
    """
    found = list(_authored_py())
    assert len(found) > 100, (
        f"expected the authored tree to hold well over 100 .py files, found "
        f"{len(found)} - the sweep is looking in the wrong place"
    )


def test_no_authored_python_carries_an_invalid_escape():
    offenders = []
    for f in _authored_py():
        for lineno, message in _syntax_warnings(f):
            if "invalid escape sequence" in message:
                offenders.append(f"{f.relative_to(_ROOT)}:{lineno} {message}")
    assert not offenders, (
        "invalid escape sequence(s) - make the string raw, which keeps the "
        "value byte-identical for any sequence Python does not recognise:\n  "
        + "\n  ".join(offenders)
    )


def test_a_crafted_invalid_escape_is_detected(tmp_path):
    """The detector must fire on a known-bad file, or the arm above is a no-op.

    Mutation-proving the sweep by editing a real tracked file would leave the
    tree dirty mid-run, so the positive control is a file written here. It
    carries the exact shape that was live in this repo.
    """
    bad = tmp_path / "crafted_bad.py"
    bad.write_text('other = "Global' + chr(92) + 'SOME-OTHER-NAME"\n', encoding="utf-8")
    found = [m for _, m in _syntax_warnings(bad) if "invalid escape sequence" in m]
    assert found, "the detector did not fire on a file known to carry the defect"


def test_the_raw_repair_is_detected_as_clean(tmp_path):
    """And the negative control: the repair this guard recommends must pass.

    A detector that flags the fix as well as the defect would make the advice
    in the failure message wrong.
    """
    good = tmp_path / "crafted_good.py"
    good.write_text('other = r"Global' + chr(92) + 'SOME-OTHER-NAME"\n', encoding="utf-8")
    found = [m for _, m in _syntax_warnings(good) if "invalid escape sequence" in m]
    assert not found, f"the recommended repair was flagged: {found}"


def test_the_raw_repair_preserves_the_value():
    """Why the repair is safe, asserted rather than claimed in a comment.

    For a sequence Python does not recognise the backslash survives, so making
    the literal raw cannot change what the program compares against. This is
    the fact that made the two live repairs mechanical instead of risky.
    """
    bs = chr(92)
    src_plain = 'v = "Global' + bs + 'SOME-OTHER-NAME"'
    src_raw = 'v = r"Global' + bs + 'SOME-OTHER-NAME"'
    ns_plain: dict = {}
    ns_raw: dict = {}
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", SyntaxWarning)
        exec(compile(src_plain, "<plain>", "exec"), ns_plain)
    exec(compile(src_raw, "<raw>", "exec"), ns_raw)
    assert ns_plain["v"] == ns_raw["v"] == "Global" + bs + "SOME-OTHER-NAME"
