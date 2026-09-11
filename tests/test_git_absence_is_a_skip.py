"""A missing git must produce a SKIP, and its presence must produce a RUN.

BOTH DIRECTIONS, BEHAVIOURALLY. RC's audit of its own tree found a 2116-line
guard that is structurally blind to this exact defect, because it audits skip
CONDITIONS and an ungated `subprocess.run([...], check=True)` has no skip to
inspect. So this file does not read any condition. It RUNS the arms twice - once
with git stripped off PATH, once with git present - and grades the outcomes:

    git absent   every representative node SKIPS, nothing fails, nothing errors
    git present  every representative node RUNS   (the mirror; a marker that
                 always skips satisfies the first arm perfectly and grades
                 nothing at all)

The representative set is one node per repaired file, chosen to cover both
observed failure modes: a plain FAILED (the tracked-corpus sweeps call git
inside the test) and an ERROR (`test_git_hooks_gate` and `test_loop_executor`
call git inside a fixture, so collection succeeds and setup explodes).

Measured 2026-09-10 before the repair: 43 items went RED with git off PATH,
none of them a defect in the thing under test.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

# One node per repaired file. Not the whole 43: this arm exists to prove the
# DISPOSITION is right, and running 43 nodes twice buys nothing the 10 do not.
REPRESENTATIVE = (
    "tests/test_git_hooks_gate.py::test_check_detects_missing_hook_file",
    "tests/test_loop_executor.py::test_gate_reason_is_none_in_this_repo",
    "tests/test_loop_executor.py::test_worktree_gate_is_inert_when_hookspath_is_unset",
    "tests/test_lw_facts_inbox.py::test_the_record_lives_in_gitignored_runtime_state",
    "tests/test_lw_next_session_guard.py::test_the_repo_root_target_is_trackable_by_git",
    "tests/test_mojibake_hygiene.py::test_no_mojibake_signature_in_authored_source",
    "tests/test_smart_quote_hygiene.py::test_no_smart_quotes_in_authored_source",
    "tests/test_no_account_paths.py::test_no_tracked_file_carries_an_account_path",
    "tests/test_no_secret_literals.py::test_no_tracked_file_carries_a_secret_literal",
    "tests/test_no_split_identity.py::test_no_tracked_file_carries_an_identity_fragment",
    "tests/test_tracked_settings_is_safe.py::test_every_declared_hook_script_exists",
)

NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def _path_without_git(env: dict[str, str]) -> str:
    kept = []
    for entry in env.get("PATH", "").split(os.pathsep):
        if not entry.strip():
            continue
        d = Path(entry)
        try:
            has_git = (d / "git.exe").exists() or (d / "git").is_file()
        except OSError:
            has_git = False
        if not has_git:
            kept.append(entry)
    return os.pathsep.join(kept)


def _run_nodes(env: dict[str, str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "pytest", *REPRESENTATIVE, "-q", "-rs",
         "-p", "no:cacheprovider"],
        cwd=str(ROOT), env=env, capture_output=True, text=True,
        errors="replace", creationflags=NO_WINDOW,
    )


@pytest.fixture(scope="module")
def stripped_env() -> dict[str, str]:
    """An environment where git genuinely cannot be resolved.

    ASSERTED, not assumed. A stripper that quietly left git reachable would make
    the whole file pass while measuring nothing - the false-GREEN failure mode
    of a false-RED arm.
    """
    env = dict(os.environ)
    env["PATH"] = _path_without_git(env)
    probe = subprocess.run(
        [sys.executable, "-c", "import shutil;print(shutil.which('git') or '')"],
        env=env, capture_output=True, text=True, creationflags=NO_WINDOW,
    )
    if probe.stdout.strip():
        pytest.fail(f"the stripped environment still resolves git: {probe.stdout!r}")
    return env


def test_every_representative_node_skips_when_git_is_absent(stripped_env):
    proc = _run_nodes(stripped_env)
    tail = proc.stdout.strip().splitlines()[-1] if proc.stdout.strip() else ""
    assert " failed" not in tail and " error" not in tail, (
        "a missing git must be a SKIP with a reason that is true, never a RED a "
        f"reader cannot act on. pytest said: {tail}\n{proc.stdout[-3000:]}")
    assert f"{len(REPRESENTATIVE)} skipped" in tail, (
        f"expected all {len(REPRESENTATIVE)} nodes to skip, got: {tail}")


def test_the_skip_reason_names_git_rather_than_being_generic(stripped_env):
    """RSC's ceiling: no mechanism can grade the truth of English, but a reason
    that does not even name the missing tool cannot be acted on either."""
    proc = _run_nodes(stripped_env)
    reasons = [ln for ln in proc.stdout.splitlines() if "SKIPPED" in ln]
    assert reasons, proc.stdout[-2000:]
    assert all("git" in ln.lower() for ln in reasons), reasons


@pytest.mark.skipif(shutil.which("git") is None,
                    reason="git is not installed here, so the mirror direction - "
                           "that these arms still RUN when git is present - cannot "
                           "be observed on this machine")
def test_the_same_nodes_actually_run_when_git_is_present():
    """THE MIRROR. A marker that always skips passes the arm above perfectly."""
    proc = _run_nodes(dict(os.environ))
    tail = proc.stdout.strip().splitlines()[-1] if proc.stdout.strip() else ""
    assert f"{len(REPRESENTATIVE)} passed" in tail, (
        "with git present these arms must RUN, not skip - a guard against a "
        f"false skip leaves the capability itself ungraded. pytest said: {tail}")
