"""ruff.toml's `exclude` must bind for a path named EXPLICITLY, not just for a
path ruff discovered by walking a directory.

The defect this pins, measured on ruff 0.15.12, 2026-09-20:

    python -m ruff check tools/dwpose_onnx/onnxdet.py
      -> exit 1, two B905 findings at :66 and :120

`tools/dwpose_onnx` is in ruff.toml's top-level `exclude`, and
`python -m ruff check .` is clean, so the config reads as if that tree is not
linted. It was. ruff defaults `force-exclude` to FALSE, which makes `exclude`
apply to directory WALKING only: a path handed to ruff on the command line
bypasses it. tools/precommit_gate.py hands ruff the staged paths explicitly
(`py -m ruff check --output-format=json <staged paths>`, cwd=repo root), so the
gate was in exactly the configuration where `exclude` does nothing.

Only the gate's net-new filter (a finding must land inside a staged hunk range)
was masking it, which means the failure mode was not "noisy" but "dormant": a
re-vendor of tools/dwpose_onnx touching line 66 or 120 would have been BLOCKED
by a rule this repo's own config declares excluded, and the commit message would
have been arguing with the config.

Two arms below, and the live one is ARMED on purpose. Asserting "ruff reports
nothing for the vendored file" is worth nothing by itself - a file with no
findings satisfies it just as well as a file that is properly excluded. So the
arm first proves, from `--no-force-exclude`, that the file really does carry
findings, and only then asserts that the project config suppresses them.
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "ruff.toml"
VENDORED = "tools/dwpose_onnx/onnxdet.py"

HAVE_RUFF = importlib.util.find_spec("ruff") is not None


def _cfg() -> dict:
    return tomllib.loads(CONFIG.read_text(encoding="utf-8"))


def test_force_exclude_is_set_and_is_top_level():
    """A key ruff only reads at top level is INERT under [lint] while still
    looking configured - the same trap that left `exclude` itself dead for
    months (measured on ruff 0.15.12)."""
    cfg = _cfg()
    assert cfg.get("force-exclude") is True, (
        "ruff.toml has no top-level `force-exclude = true`, so `exclude` is "
        "ignored for any path named explicitly on the command line - which is "
        "how tools/precommit_gate.py invokes ruff."
    )
    lint = cfg.get("lint", {})
    # The two keys fail DIFFERENTLY when misplaced, re-measured on ruff 0.15.12
    # rather than assumed, because the obvious guess is wrong for one of them.
    assert "force-exclude" not in lint, (
        "`force-exclude` is under [lint], which is not merely inert: it is an "
        "unknown field there and ruff refuses the whole config with exit 2 and "
        "empty stdout. tools/precommit_gate.py catches that and continues with "
        "`findings = []`, so the gate's ruff pass is off entirely and silently."
    )
    assert "exclude" not in lint, (
        "`exclude` is under [lint], where ruff ACCEPTS it and it means "
        "something else - exit 1 and the vendored file linted anyway. That one "
        "really is silently inert, which is how it went unnoticed for months."
    )
    assert "tools/dwpose_onnx" in cfg.get("exclude", []), (
        "the vendored dwpose_onnx tree left the exclude list; force-exclude "
        "now has nothing to enforce for it."
    )


@pytest.mark.skipif(not HAVE_RUFF, reason="ruff is not installed in this interpreter")
def test_the_vendored_tree_is_excluded_even_when_named_explicitly():
    def run(*extra: str) -> tuple[int, list]:
        proc = subprocess.run(
            [sys.executable, "-m", "ruff", "check", "--output-format=json",
             *extra, VENDORED],
            cwd=ROOT, capture_output=True, text=True, timeout=120)
        # No swallowing of a non-run here either: an exit code outside (0, 1)
        # means ruff never linted anything, and "no findings" would then be an
        # artefact of the failure rather than evidence of an exclusion.
        assert proc.returncode in (0, 1), (
            f"ruff exited {proc.returncode} with args {extra}: "
            f"{proc.stderr.strip()[:400]}"
        )
        findings = json.loads(proc.stdout) if proc.stdout.strip() else []
        return proc.returncode, findings

    # ARMING clause. Without this, "0 findings" below is satisfied by a clean
    # file, by a missing file, or by a ruff that never ran, and the arm asserts
    # nothing at all.
    assert (ROOT / VENDORED).is_file(), f"{VENDORED} is gone - re-point this arm"
    _, unforced = run("--no-force-exclude")
    assert unforced, (
        f"{VENDORED} produced no findings even with exclusions disabled, so "
        f"this arm cannot tell an excluded file from a clean one. Pick a "
        f"vendored file that ruff still objects to, or the pin is vacuous."
    )

    code, findings = run()
    assert (code, findings) == (0, []), (
        f"ruff reported {len(findings)} finding(s) for {VENDORED} although "
        f"ruff.toml excludes that tree: {[(f.get('code')) for f in findings]}. "
        f"force-exclude is off or no longer top-level, and tools/precommit_gate"
        f".py will block a re-vendor over a rule the config says is excluded."
    )


@pytest.mark.skipif(not HAVE_RUFF, reason="ruff is not installed in this interpreter")
def test_no_finding_over_the_tracked_file_list_comes_from_an_excluded_tree():
    """The gate's real shape: every staged path named explicitly, from the repo
    root so the project config is found."""
    tracked = subprocess.run(["git", "ls-files", "*.py"], cwd=ROOT,
                             capture_output=True, text=True, timeout=120)
    pyfiles = [p for p in tracked.stdout.split("\n") if p.strip()]
    assert len(pyfiles) > 100, f"only {len(pyfiles)} tracked .py files - git call failed?"
    proc = subprocess.run(
        [sys.executable, "-m", "ruff", "check", "--output-format=json", *pyfiles],
        cwd=ROOT, capture_output=True, text=True, timeout=300)
    # ARMING clause, and it caught a real vacuity in this very arm: a ruff that
    # REFUSES the config exits 2 with empty stdout, which parses to zero
    # findings and satisfies the assertion below for the wrong reason. 0 and 1
    # are ruff's clean / findings-present codes; anything else did not run.
    assert proc.returncode in (0, 1), (
        f"ruff exited {proc.returncode} instead of running: "
        f"{proc.stderr.strip()[:400]}"
    )
    findings = json.loads(proc.stdout) if proc.stdout.strip() else []
    excluded = sorted({
        (f.get("filename") or "").replace("\\", "/")
        for f in findings
        if "tools/dwpose_onnx/" in (f.get("filename") or "").replace("\\", "/")
    })
    assert not excluded, (
        f"ruff reported findings inside the excluded vendored tree: {excluded}. "
        f"The exclude list is decoration while force-exclude is off."
    )


def test_the_gate_does_not_disable_force_exclude_on_the_command_line():
    """`--no-force-exclude` on the gate's argv would undo the config fix
    without touching ruff.toml, so nothing above would notice."""
    src = (ROOT / "tools" / "precommit_gate.py").read_text(encoding="utf-8")
    assert "no-force-exclude" not in src, (
        "tools/precommit_gate.py passes --no-force-exclude, which overrides "
        "ruff.toml and re-lints the vendored tree."
    )
    assert '"ruff", "check"' in src.replace("'", '"'), (
        "the gate no longer invokes `ruff check` in the shape this arm "
        "reasons about - re-read tools/precommit_gate.py and re-point it."
    )
