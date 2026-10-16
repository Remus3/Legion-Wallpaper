"""MAIN PUBREPO order 2b: merge subjects read `merge: <topic>` and carry no
agent worktree names. Pins tools/precommit_msg_check.validate()."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import precommit_msg_check as pmc  # noqa: E402


def test_merge_template_subject_passes_while_merging():
    assert pmc.validate("merge: PUBREPO codeql triage", merging=True) == (True, None)


@pytest.mark.parametrize("subject", [
    "Merge branch 'worktree-agent-a3b50d28a7b9f6792'",
    "Merge branch 'main' of github.com:x/y",
    "chore(merge): RRF-2.3b slice 2",
    "merge(tools): scoped is not the template",
    "feat: a merge commit with a normal subject",
])
def test_merge_commit_without_the_template_is_rejected(subject):
    ok, err = pmc.validate(subject, merging=True)
    assert not ok and "merge: <topic>" in err


@pytest.mark.parametrize("subject", [
    "merge: worktree-agent-a3b50d28a7b9f6792",
    "merge: agent-a3b50d28a7b9f6792 codeql slice",
    "merge: .claude/worktrees/agent-x slice",
])
def test_merge_subject_naming_an_agent_worktree_is_rejected(subject):
    ok, err = pmc.validate(subject, merging=True)
    assert not ok and "worktree" in err


def test_git_default_merge_subject_is_no_longer_skipped():
    ok, _ = pmc.validate("Merge branch 'feature'")
    assert not ok


def test_merge_type_outside_a_merge_must_still_be_the_bare_template():
    assert pmc.validate("merge: topic")[0]
    assert not pmc.validate("merge(x): topic")[0]


def test_ordinary_subjects_unchanged():
    assert pmc.validate("feat(tools): add a thing") == (True, None)
    assert pmc.validate("Revert \"feat: x\"") == (True, None)
    assert not pmc.validate("no type here")[0]


def test_main_detects_merge_head(tmp_path):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True,
                   creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    (tmp_path / ".git" / "MERGE_HEAD").write_text("0" * 40 + "\n")
    assert pmc.is_merging(tmp_path)
    (tmp_path / ".git" / "MERGE_HEAD").unlink()
    assert not pmc.is_merging(tmp_path)
