"""Every worktree parent directory must carry an ignore rule.

THE GAP, found 2026-09-19 during the machine stray-work sweep. This repo has
two worktree parent directories, `.claude/worktrees/` and `worktrees/` at the
root. Only the first had a rule:

    $ git check-ignore -v .claude/worktrees
    .gitignore:20:.claude/worktrees/   .claude/worktrees
    $ git check-ignore -v worktrees
    (nothing, exit 1)

Both were empty at the time, so `git status` was silent and nothing looked
wrong. That silence is the trap: git does not track empty directories, so an
unignored empty directory is indistinguishable from an ignored one until the
moment something lands in it. The first worktree checked out into `worktrees/`
would have appeared as untracked content - a whole second copy of the tree,
including anything gitignored-but-present in it - in a repository that is
PUBLIC under Apache-2.0. "Nothing shows up in git status" is not evidence of an
ignore rule; it is evidence the directory is empty.

Same failure class as the repo's git-hook guard: presence is not proof. A rule
is verified by asking git, never by reading a directory listing.

HERMETIC: builds a throwaway git repo in tmp_path, copies in THIS repo's
tracked .gitignore, and asks git about paths that do not exist. `git
check-ignore` answers from the rules alone, so no file is created and nothing
on this machine is read beyond the tracked .gitignore itself - which is
byte-identical in CI.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
GITIGNORE = REPO / ".gitignore"

# Every directory this repo checks worktrees out into. A new one added without
# a rule fails here rather than at the first `git add -A` after a lane opens.
WORKTREE_ROOTS = (".claude/worktrees", "worktrees")


def _tmp_repo(tmp_path: Path) -> Path:
    git = shutil.which("git")
    if git is None:
        pytest.skip("git not on PATH")
    root = tmp_path / "repo"
    root.mkdir()
    subprocess.run([git, "init", "-q"], cwd=root, check=True,
                   capture_output=True)
    shutil.copyfile(GITIGNORE, root / ".gitignore")
    return root


def _ignored(root: Path, rel: str) -> tuple[bool, str]:
    """(is_ignored, the PATTERN that did it) for a path that need not exist.

    Parses the pattern column rather than trusting the exit code. Measured on
    this repo 2026-09-19, git answers `check-ignore -v --no-index worktrees/`
    with exit 0 and this line:

        .gitignore:194:<TAB>worktrees/

    which reads like a match and is not one: `-v` prints
    `source:line:pattern<TAB>path`, so the pattern there is EMPTY and line 194
    of .gitignore is BLANK. Only the trailing-slash form does it. A test that
    checked the exit code, or grepped the whole line for the directory name,
    would have gone green against a repo with no rule at all - the pathname
    column supplies the very string it was looking for.
    """
    res = subprocess.run(
        ["git", "check-ignore", "-v", "--no-index", rel.rstrip("/")],
        cwd=root, capture_output=True, text=True,
    )
    # NOTE for the caller: a directory-only rule (`foo/`) matches a path only
    # when git can see it IS a directory, so the caller materialises the path
    # in the throwaway repo first. Asking about a non-existent `foo` against
    # the rule `foo/` answers "not ignored" and is a false RED.
    line = res.stdout.strip()
    if res.returncode != 0 or not line or "\t" not in line:
        return False, line
    lhs = line.split("\t", 1)[0]
    pattern = lhs.split(":", 2)[2] if lhs.count(":") >= 2 else ""
    return bool(pattern), pattern


@pytest.mark.parametrize("root_dir", WORKTREE_ROOTS)
def test_worktree_root_is_ignored(tmp_path, root_dir):
    repo = _tmp_repo(tmp_path)
    (repo / root_dir).mkdir(parents=True, exist_ok=True)
    ok, pattern = _ignored(repo, root_dir)
    assert ok, (
        f"{root_dir} matches no .gitignore rule. It is invisible today only "
        "because it is empty; the first checkout into it lands as untracked "
        "content in a PUBLIC repository."
    )
    assert "worktrees" in pattern, (
        f"{root_dir} is ignored, but by an unrelated rule ({pattern!r}). The "
        "rule must name it, or a later edit to that other rule silently "
        "un-ignores a whole worktree."
    )


@pytest.mark.parametrize("root_dir", WORKTREE_ROOTS)
def test_a_file_inside_a_worktree_root_is_ignored(tmp_path, root_dir):
    """The directory rule must cover what actually appears: files, deep.

    A rule can match the directory and still let a nested path through if it
    was written without a trailing slash or with the wrong anchor, so the
    payload case is asserted separately from the directory case.
    """
    repo = _tmp_repo(tmp_path)
    rel = f"{root_dir}/lane-x/tools/lw_pipeline.py"
    (repo / rel).parent.mkdir(parents=True, exist_ok=True)
    (repo / rel).write_text("x\n", encoding="ascii")
    ok, _ = _ignored(repo, rel)
    assert ok, f"a file inside {root_dir}/ is not ignored"


def test_the_rule_is_anchored_and_does_not_swallow_a_nested_worktrees_dir():
    """Narrow first. `worktrees/` unanchored would match at EVERY depth.

    This repo has already been bitten by an unanchored rule: `_archive/`, meant
    for the root quarantine directory, silently swallowed `docs/_archive/`,
    which holds the authoritative sha-rewrite maps. The root worktree rule is
    anchored with a leading slash so a hypothetical `docs/worktrees/` page
    directory stays addable.
    """
    text = GITIGNORE.read_text(encoding="utf-8")
    lines = [ln.strip() for ln in text.splitlines()]
    assert "/worktrees/" in lines, "the root worktree rule must be anchored"
    assert "worktrees/" not in lines, (
        "an UNANCHORED `worktrees/` matches at every depth - use `/worktrees/`"
    )


def test_gitignore_is_ascii():
    """Repo-wide hard rule; this file is edited by hand often enough to check."""
    raw = GITIGNORE.read_bytes()
    bad = [(i, hex(b)) for i, b in enumerate(raw) if b > 127]
    assert bad == [], f"non-ASCII bytes in .gitignore: {bad[:5]}"


def test_no_other_worktree_root_lacks_a_rule(tmp_path):
    """Guard the guard: if a new worktree parent appears on disk, name it here.

    WORKTREE_ROOTS is a hand-maintained list, so it decays silently. This arm
    fails when the working copy holds a `*worktrees*` directory at the root or
    under .claude/ that the list does not cover. It reads the working copy on
    purpose and is skipped when run outside it.
    """
    if not (REPO / ".git").exists():
        pytest.skip("not run from the working copy")
    found = set()
    for parent in (REPO, REPO / ".claude"):
        if not parent.is_dir():
            continue
        for p in parent.iterdir():
            if p.is_dir() and "worktree" in p.name.lower():
                found.add(p.relative_to(REPO).as_posix())
    missing = found - set(WORKTREE_ROOTS)
    assert not missing, (
        f"worktree parent directories with no entry in WORKTREE_ROOTS: "
        f"{sorted(missing)} - add the rule AND the list entry"
    )
