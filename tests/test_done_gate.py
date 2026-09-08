"""The /done gate must grade the exact tree that gets pushed.

CS found this 2026-09-07 as a pre-push race. LW's form is not a race: it is the
documented ORDER of the ritual - gate, then edit ROADMAP/LEDGER/WAKEUP, then
commit and push - so every session shipped doc edits the graded run never saw.
"Fix the ordering" is a sentence in a markdown file, and a sentence asserts
nothing. These arms are the assertion.

Hermetic by construction: every arm builds its own throwaway repo and its own
bare "remote" in tmp_path. Nothing here reads the Legion checkout, the operator
profile, or any machine state - the one exception is the LAST arm, which reads
this repo's own `.claude/commands/done.md` on purpose, because the ordering of
that document IS the thing under test.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

import done_gate as DG  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[1]

pytestmark = pytest.mark.skipif(shutil.which("git") is None,
                                reason="git not on PATH")

# A check that always succeeds and touches nothing. Substituting for the real
# ruff/pytest/drift_guard trio is what keeps these arms hermetic and fast.
OK_CHECK = [[sys.executable, "-c", "pass"]]
RED_CHECK = [[sys.executable, "-c", "raise SystemExit(1)"]]


def _run(repo: Path, *args: str) -> subprocess.CompletedProcess:
    r = subprocess.run(["git", "-C", str(repo), *args],
                       capture_output=True, text=True)
    assert r.returncode == 0, f"git {args}: {r.stderr}"
    return r


def _make_repo(tmp_path: Path) -> Path:
    """A one-commit repo on `main` with identity and hooks pinned off."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _run(repo.parent, "init", "-q", str(repo))
    _run(repo, "symbolic-ref", "HEAD", "refs/heads/main")
    _run(repo, "config", "user.email", "gate@example.invalid")
    _run(repo, "config", "user.name", "gate")
    _run(repo, "config", "commit.gpgsign", "false")
    _run(repo, "config", "core.hooksPath", str(tmp_path / "no-hooks"))
    (repo / "a.txt").write_text("one\n", encoding="ascii")
    _run(repo, "add", "a.txt")
    _run(repo, "commit", "-qm", "first")
    return repo


def _make_remote(tmp_path: Path, repo: Path) -> Path:
    """A bare repo wired as `origin`, with main already pushed."""
    remote = tmp_path / "remote.git"
    _run(repo.parent, "init", "-q", "--bare", str(remote))
    _run(repo, "remote", "add", "origin", str(remote))
    _run(repo, "push", "-q", "origin", "main")
    return remote


def _commit(repo: Path, name: str, body: str = "x\n") -> str:
    (repo / name).write_text(body, encoding="ascii")
    _run(repo, "add", name)
    _run(repo, "commit", "-qm", f"add {name}")
    return DG.head_sha(repo)


# ---- bind: the tree must be clean, and clean means MORE than `git diff HEAD`


def test_bind_refuses_an_uncommitted_edit_and_clears_once_committed(tmp_path):
    """The exact LW failure: a doc edit authored after the gate would ship.

    Both halves matter. A gate that only ever fires is a gate nobody can
    satisfy, so this asserts the refusal GOES AWAY once the edit is committed -
    and that the sha it then binds is the new one, not the pre-edit one.
    """
    repo = _make_repo(tmp_path)
    receipt = tmp_path / "receipt.json"

    (repo / "ROADMAP.md").write_text("living doc edit\n", encoding="ascii")
    assert DG.bind(repo, receipt, checks=OK_CHECK) == 2
    assert not receipt.exists(), "a refused gate must not leave a receipt"

    _run(repo, "add", "ROADMAP.md")
    _run(repo, "commit", "-qm", "docs: sync living docs")
    expected = DG.head_sha(repo)

    assert DG.bind(repo, receipt, checks=OK_CHECK) == 0
    assert json.loads(receipt.read_text())["graded_sha"] == expected


def test_bind_refuses_an_untracked_file(tmp_path):
    """`git diff HEAD` is empty here. The tree is still not what gets pushed.

    A new test module a session wrote but never staged is graded by the local
    run and then simply does not exist on the remote. Naming the acceptance
    check after `git diff HEAD` would have shipped this hole intact.
    """
    repo = _make_repo(tmp_path)
    receipt = tmp_path / "receipt.json"
    (repo / "test_new.py").write_text("def test_x():\n    pass\n", encoding="ascii")

    diff = subprocess.run(["git", "-C", str(repo), "diff", "HEAD", "--name-only"],
                          capture_output=True, text=True)
    assert diff.stdout.strip() == "", "premise: git diff HEAD sees nothing here"
    assert DG.bind(repo, receipt, checks=OK_CHECK) == 2


def test_bind_refuses_a_dirty_start_even_when_the_checks_tidy_up_after(tmp_path):
    """Isolates the PRE-run clean check from the post-run one.

    Contrived on purpose: this check deletes the stray file, so by the time
    the post-run assertion looks the tree is clean and HEAD has not moved, and
    a gate without the pre-run check would return 0 having graded a run made
    against content that is in no commit. Deleting the pre-run check passes
    the rest of the module - measured, mutant M1, 2026-09-07.

    The stray file surviving is the evidence: the gate refused BEFORE running
    anything, which is the only reason the tidy-up never happened.
    """
    repo = _make_repo(tmp_path)
    receipt = tmp_path / "receipt.json"
    (repo / "stray.txt").write_text("ungraded\n", encoding="ascii")
    tidy = [sys.executable, "-c",
            "from pathlib import Path; Path('stray.txt').unlink()"]

    assert DG.bind(repo, receipt, checks=[tidy]) == 2
    assert not receipt.exists()
    assert (repo / "stray.txt").exists(), "refused before the checks could run"


def test_bind_refuses_a_tree_that_moves_while_the_checks_run(tmp_path):
    """CS's race, ported. The pre-run clean check cannot see this one."""
    repo = _make_repo(tmp_path)
    receipt = tmp_path / "receipt.json"
    racer = [sys.executable, "-c",
             "from pathlib import Path; Path('late.txt').write_text('late')"]

    assert DG.bind(repo, receipt, checks=[racer]) == 2
    assert not receipt.exists()


def test_bind_separates_a_red_check_from_a_broken_ordering(tmp_path):
    """Exit 1 = gradeable tree, failing check. Exit 2 = the property is broken.

    Collapsing them would let a caller that only tests `!= 0` report the wrong
    cause, and the receipt has to carry the red so verify-push can refuse it.
    """
    repo = _make_repo(tmp_path)
    receipt = tmp_path / "receipt.json"

    assert DG.bind(repo, receipt, checks=RED_CHECK) == 1
    data = json.loads(receipt.read_text())
    assert data["passed"] is False
    assert data["graded_sha"] == DG.head_sha(repo)


def test_bind_writes_the_receipt_atomically(tmp_path):
    """No .tmp left behind - consumers may poll mid-write (CLAUDE.md rule)."""
    repo = _make_repo(tmp_path)
    receipt = tmp_path / "nested" / "receipt.json"
    assert DG.bind(repo, receipt, checks=OK_CHECK) == 0
    assert receipt.exists()
    assert list(receipt.parent.glob("*.tmp")) == []


# ---- verify-push: the remote must carry the graded sha, asked of the remote


def test_verify_push_passes_only_when_the_pushed_sha_is_the_graded_sha(tmp_path):
    repo = _make_repo(tmp_path)
    _make_remote(tmp_path, repo)
    receipt = tmp_path / "receipt.json"

    graded = _commit(repo, "b.txt")
    assert DG.bind(repo, receipt, checks=OK_CHECK) == 0
    _run(repo, "push", "-q", "origin", "main")

    assert DG.verify_push(repo, receipt, "origin", "main") == 0
    assert json.loads(receipt.read_text())["graded_sha"] == graded


def test_verify_push_refuses_a_commit_that_landed_after_the_gate(tmp_path):
    """The deterministic LW shape: gate, then author, then push."""
    repo = _make_repo(tmp_path)
    _make_remote(tmp_path, repo)
    receipt = tmp_path / "receipt.json"

    assert DG.bind(repo, receipt, checks=OK_CHECK) == 0
    _commit(repo, "LEDGER_entry.txt")          # authored AFTER the gate
    _run(repo, "push", "-q", "origin", "main")

    assert DG.verify_push(repo, receipt, "origin", "main") == 2


def test_verify_push_refuses_a_local_commit_the_remote_never_got(tmp_path):
    """Isolates the HEAD==graded check from the remote==graded one.

    Bind and push sha A, then commit B locally and stop. The remote still
    carries exactly the graded sha, so the remote comparison is happy; only
    the HEAD comparison can see that the session ended holding work its own
    gate never graded. Without this arm, deleting that comparison passes the
    whole module - measured, mutant M4, 2026-09-07.
    """
    repo = _make_repo(tmp_path)
    receipt = tmp_path / "receipt.json"
    _make_remote(tmp_path, repo)

    graded = DG.head_sha(repo)
    assert DG.bind(repo, receipt, checks=OK_CHECK) == 0
    _run(repo, "push", "-q", "origin", "main")
    _commit(repo, "after.txt")                 # local only, never pushed

    assert DG.remote_head_sha(repo, "origin", "main") == graded
    assert DG.verify_push(repo, receipt, "origin", "main") == 2


def test_verify_push_refuses_when_the_push_never_landed(tmp_path):
    repo = _make_repo(tmp_path)
    _make_remote(tmp_path, repo)
    receipt = tmp_path / "receipt.json"

    _commit(repo, "c.txt")
    assert DG.bind(repo, receipt, checks=OK_CHECK) == 0
    # no push at all
    assert DG.verify_push(repo, receipt, "origin", "main") == 2


def test_verify_push_asks_the_remote_not_the_stale_local_cache(tmp_path):
    """`git rev-parse origin/main` would agree with a push that never landed.

    The remote-tracking ref is a local cache. Rewinding the bare repo behind
    its back leaves the cache pointing at a sha the server does not have - the
    exact state a rejected or half-finished push leaves - and the gate must
    read the server.
    """
    repo = _make_repo(tmp_path)
    remote = _make_remote(tmp_path, repo)
    receipt = tmp_path / "receipt.json"

    base = DG.head_sha(repo)
    graded = _commit(repo, "d.txt")
    assert DG.bind(repo, receipt, checks=OK_CHECK) == 0
    _run(repo, "push", "-q", "origin", "main")

    _run(remote, "update-ref", "refs/heads/main", base)      # server rewinds

    cached = subprocess.run(["git", "-C", str(repo), "rev-parse", "origin/main"],
                            capture_output=True, text=True).stdout.strip()
    assert cached == graded, "premise: the local cache still says graded"
    assert DG.remote_head_sha(repo, "origin", "main") == base
    assert DG.verify_push(repo, receipt, "origin", "main") == 2


def test_verify_push_refuses_a_missing_or_red_receipt(tmp_path):
    repo = _make_repo(tmp_path)
    _make_remote(tmp_path, repo)
    receipt = tmp_path / "receipt.json"

    assert DG.verify_push(repo, receipt, "origin", "main") == 2

    assert DG.bind(repo, receipt, checks=RED_CHECK) == 1
    _run(repo, "push", "-q", "origin", "main")
    assert DG.verify_push(repo, receipt, "origin", "main") == 2


# ---- the ritual document itself: ordering is the fix, so pin the ordering


def _done_doc() -> str:
    p = REPO_ROOT / ".claude" / "commands" / "done.md"
    assert p.is_file(), f"{p} is missing"
    return p.read_text(encoding="utf-8")


def test_done_ritual_wires_the_binding_gate():
    text = _done_doc()
    assert "tools/done_gate.py bind" in text
    assert "tools/done_gate.py verify-push" in text


def test_done_ritual_binds_after_every_authored_edit_and_before_the_push():
    """The ordering property, asserted on the document that carries it.

    A future edit that moves the living-doc sync back below the gate, or the
    push back above it, turns this red. That is the entire point: the old
    ordering was readable, deliberate and wrong, and nothing could tell.
    """
    text = _done_doc()
    bind_at = text.index("tools/done_gate.py bind")
    verify_at = text.index("tools/done_gate.py verify-push")
    push_at = text.index("git -C \"C:/Legion Wallpaper\" push origin")
    docs_at = text.index("### 4b. Living-doc sync")
    handoff_at = text.index("tools/lw_next_session.py --write")

    assert docs_at < bind_at, "living-doc sync must be graded, so it comes first"
    assert handoff_at < bind_at, "the hand-off file must be graded too"
    assert bind_at < push_at, "the gate binds BEFORE the push"
    assert push_at < verify_at, "verify-push reads the remote AFTER the push"
