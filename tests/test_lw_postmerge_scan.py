"""tools/lw_postmerge_scan.py - post-merge identity scan (MAIN 0034
DEPENDABOT-MERGE-RULE section 2.2). A squash done on GitHub never runs the
local commit-msg hook, so the bad commit is on the remote before pre-push
sees it; this scan reads the default branch AFTER a merge. Every test builds a
throwaway repo under tmp_path - never live history.
"""
import os
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import lw_postmerge_scan as pm  # noqa: E402

OP = "Op Erator <op@example.invalid>"


def _git(repo, *args, env=None):
    e = dict(os.environ)
    e.update(env or {})
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True,
                          text=True, check=True, env=e).stdout.strip()


def _commit(repo, name, msg, author=OP, committer=OP):
    (repo / name).write_text(name, encoding="ascii")
    _git(repo, "add", name)
    an, ae = author.split(" <")
    cn, ce = committer.split(" <")
    env = {"GIT_AUTHOR_NAME": an, "GIT_AUTHOR_EMAIL": ae.rstrip(">"),
           "GIT_COMMITTER_NAME": cn, "GIT_COMMITTER_EMAIL": ce.rstrip(">")}
    _git(repo, "-c", "core.hooksPath=/dev/null", "commit", "-q", "-m", msg, env=env)
    return _git(repo, "rev-parse", "HEAD")


@pytest.fixture
def repo(tmp_path):
    r = tmp_path / "r"
    r.mkdir()
    _git(r, "init", "-q", "-b", "main")
    _commit(r, "a.txt", "base")
    return r


def test_clean_operator_commit_has_no_hits(repo):
    base = _git(repo, "rev-parse", "HEAD")
    _commit(repo, "b.txt", "operator bump\n\nbody line")
    assert pm.scan(repo, f"{base}..HEAD", [OP]) == []


def test_flags_synthetic_bot_squash_commit(repo):
    """The GitHub-squash shape: bot co-author trailer, GitHub web-flow committer."""
    base = _git(repo, "rev-parse", "HEAD")
    sha = _commit(repo, "b.txt",
                  "build(deps): bump x (#3)\n\nCo-authored-by: dependabot[bot] "
                  "<49699333+dependabot[bot]@users.noreply.github.com>",
                  committer="GitHub <noreply@github.com>")
    classes = {(h[0], h[1]) for h in pm.scan(repo, f"{base}..HEAD", [OP])}
    assert (sha[:7], "non-operator-committer") in classes
    assert (sha[:7], "co-authored-by") in classes


def test_flags_bot_author(repo):
    base = _git(repo, "rev-parse", "HEAD")
    sha = _commit(repo, "b.txt", "bump",
                  author="dependabot[bot] <bot@example.invalid>")
    assert (sha[:7], "non-operator-author") in {
        (h[0], h[1]) for h in pm.scan(repo, f"{base}..HEAD", [OP])}


def test_any_co_authored_by_line_is_flagged_even_human(repo):
    """The order says ANY Co-authored-by line; stricter than fleet_identity."""
    base = _git(repo, "rev-parse", "HEAD")
    _commit(repo, "b.txt", "x\n\nCo-authored-by: Some Human <h@example.invalid>")
    assert [h[1] for h in pm.scan(repo, f"{base}..HEAD", [OP])] == ["co-authored-by"]


def test_prose_mention_is_not_a_trailer(repo):
    base = _git(repo, "rev-parse", "HEAD")
    _commit(repo, "b.txt", "docs: purge the Co-Authored-By trailers from history")
    assert pm.scan(repo, f"{base}..HEAD", [OP]) == []


def test_operator_matched_by_bare_address(repo):
    base = _git(repo, "rev-parse", "HEAD")
    _commit(repo, "b.txt", "x")
    assert pm.scan(repo, f"{base}..HEAD", ["op@example.invalid"]) == []


def test_no_operator_identity_refuses(repo):
    with pytest.raises(ValueError):
        pm.scan(repo, "HEAD", [])


def test_main_exit_codes_and_state(repo, tmp_path):
    state = tmp_path / "state.json"
    _git(repo, "config", "--local", "--add", "fleet.operatorIdent", OP)
    rc = pm.main(["--repo", str(repo), "--ref", "main", "--no-fetch",
                  "--state", str(state)])
    assert rc == 0 and state.is_file()
    _commit(repo, "b.txt", "x\n\nCo-authored-by: dependabot[bot] <b@example.invalid>")
    rc = pm.main(["--repo", str(repo), "--ref", "main", "--no-fetch",
                  "--state", str(state)])
    assert rc == 1
    # a hit is NOT marked scanned: the next run still sees it until fixed
    rc = pm.main(["--repo", str(repo), "--ref", "main", "--no-fetch",
                  "--state", str(state)])
    assert rc == 1
