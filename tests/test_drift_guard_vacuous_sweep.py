"""drift_guard: an ignore sweep over ZERO files must refuse, not report clean.

THE CLASS. `find_tracked_but_ignored` enumerates the corpus with `git ls-files`
and returns the offenders. Its guard clause is

    if ls.returncode != 0 or not ls.stdout:
        return []

and `check_tracked_but_ignored` turns an empty offender list into the note
"no tracked path is covered by an ignore rule". So a walk that enumerated
NOTHING is indistinguishable, in the report, from a walk that enumerated 450
files and found nothing wrong. That is vacuity: the acceptance condition is
satisfied by shrinking the population to zero, and the gate still reads green.

WHY IT IS REACHABLE AND NOT THEORETICAL. `ls-files` exits 0 with empty stdout in
at least three states this repo actually passes through - a fresh `git init`
before the first `git add`, a repo whose index was reset, and a worktree slice
checked out empty. In every one of them git RAN and ANSWERED; nothing in the
return path records that the answer covered no files. This is the same shape
`test_no_account_paths.test_the_sweep_selects_a_real_corpus` already guards for
on the account-path sweep, and the ignore sweep had no equivalent.

WHAT THE FIX IS NOT. The finder's contract is unchanged: it still returns [] for
a missing directory, a non-repo and a real clean repo, because eleven call sites
pin that and a non-repo genuinely has no offenders. The refusal lives in the
CHECK, which is the thing that publishes a verdict a reader acts on.

HERMETIC. Every arm builds its own throwaway repo in tmp_path. An arm that read
this machine's repo would pass only on this box.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

import drift_guard as DG  # noqa: E402

pytestmark = pytest.mark.skipif(
    shutil.which("git") is None, reason="git not on PATH")


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True, text=True, creationflags=DG.NO_WINDOW, check=False)


def _empty_repo(tmp_path: Path) -> Path:
    """A REAL git repo with an EMPTY index: `ls-files` exits 0, prints nothing."""
    repo = tmp_path / "empty"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.email", "test@example.invalid")
    _git(repo, "config", "user.name", "test")
    return repo


def _populated_repo(tmp_path: Path) -> Path:
    """A REAL git repo with tracked files and no ignore rule covering them."""
    repo = tmp_path / "full"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.email", "test@example.invalid")
    _git(repo, "config", "user.name", "test")
    (repo / ".gitignore").write_text("*.pyc\n", encoding="ascii")
    (repo / "tools").mkdir()
    (repo / "tools" / "real.py").write_text("x = 1\n", encoding="ascii")
    _git(repo, "add", "--", ".gitignore", "tools/real.py")
    _git(repo, "commit", "-q", "-m", "fixture")
    return repo


def _run_check(repo: Path) -> tuple[list[str], list[str]]:
    DG.problems.clear()
    DG.notes.clear()
    try:
        DG.check_tracked_but_ignored(repo)
        return list(DG.problems), list(DG.notes)
    finally:
        DG.problems.clear()
        DG.notes.clear()


# ---------------------------------------------------------------------------
# the counter the refusal is built on
# ---------------------------------------------------------------------------
def test_the_corpus_counter_separates_zero_from_unaskable(tmp_path):
    """Three dispositions, not two: counted N, counted ZERO, could not count.

    Collapsing the third into the second is how a missing tool installs a false
    red; collapsing the second into the first is the vacuity this file exists
    for. The counter has to be able to say all three.
    """
    assert DG.tracked_file_count(_populated_repo(tmp_path)) == 2
    assert DG.tracked_file_count(_empty_repo(tmp_path)) == 0
    assert DG.tracked_file_count(tmp_path / "does-not-exist") < 0
    plain = tmp_path / "plain"
    plain.mkdir()
    assert DG.tracked_file_count(plain) < 0, "a non-repo is UNASKABLE, not zero"


# ---------------------------------------------------------------------------
# the refusal
# ---------------------------------------------------------------------------
def test_an_empty_corpus_is_a_breach_and_never_a_clean_note(tmp_path):
    """The arm. A sweep that walked nothing must not publish a clean verdict."""
    problems, notes = _run_check(_empty_repo(tmp_path))
    assert problems, "a sweep over ZERO tracked files reported no problem at all"
    msg = problems[0]
    assert "VACUOUS" in msg, f"the breach must name the class: {msg}"
    assert not any("no tracked path is covered" in n for n in notes), (
        "the vacuous sweep still published the clean note")


def test_a_real_corpus_with_no_offenders_still_reads_clean(tmp_path):
    """Non-vacuity control: the refusal must not fire on a genuinely clean repo.

    Without this arm the fix above is satisfiable by failing always, which is
    the same defect pointed the other way.
    """
    problems, notes = _run_check(_populated_repo(tmp_path))
    assert not problems, f"false positive on a clean populated repo: {problems}"
    assert any("no tracked path is covered" in n for n in notes), (
        f"the clean note went missing: {notes}")


def test_a_non_repo_says_it_could_not_check_rather_than_clean(tmp_path):
    """git ran and there is no repository: that is UNASKABLE, not verified.

    CI on a tarball, a worktree slice, `tools/lw_model_pins.py`'s own ruling -
    absent must never read as verified. It is not a BREACH either, because a
    directory with no repo has no drift to report; it is a note that says so.
    """
    plain = tmp_path / "plain"
    plain.mkdir()
    problems, notes = _run_check(plain)
    assert not problems, f"a non-repo must be survivable, not red: {problems}"
    assert notes, "a non-repo published nothing at all"
    assert not any("no tracked path is covered" in n for n in notes), (
        "a directory with no git repo claimed a verified-clean ignore sweep")


def test_the_finder_contract_is_unchanged(tmp_path):
    """Eleven call sites pin []; the refusal lives in the CHECK, not the finder."""
    assert DG.find_tracked_but_ignored(_empty_repo(tmp_path)) == []
    assert DG.find_tracked_but_ignored(tmp_path / "nope") == []
    assert DG.find_tracked_but_ignored(_populated_repo(tmp_path)) == []
