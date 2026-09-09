"""drift_guard: a TRACKED path that the ignore rules would nonetheless IGNORE.

THE TRAP. This .gitignore is deny-by-default with re-includes (images/**,
tools/models/*, ops/loop/control/* and more). When a rule covers a directory
that already holds TRACKED files, git keeps the tracked ones - the index wins
over .gitignore for a path already in it - but every NEW sibling created there
is silently un-addable. Measured live on this repo 2026-09-08:

    $ echo x > docs/_archive/_probe.md
    $ git add -A
    $ git status --porcelain
    (nothing)                       <- exit 0, no output, file never lands

`git add -A` does not warn. Only naming the path explicitly earns a hint, and
nothing in the repo's normal add-commit flow does that. The directory looks
tracked because six files in it ARE tracked, so nothing on the surface says the
seventh will vanish. That is the same "presence is not proof" failure class the
repo already guards for git hooks, and it had no check.

The live cause here is one unanchored rule: `.gitignore:26` reads `_archive/`,
written for the ROOT audit-cleanup quarantine, but an unanchored pattern matches
at every depth, so it also swallows `docs/_archive/` - which CLAUDE.md cites as
the authoritative sha-rewrite maps.

HERMETIC. Every test builds a throwaway git repo in tmp_path with its own
.gitignore and its own force-added files, and runs the check against THAT. A
test that read this machine's real repo state would pass only on this box and
break in CI on Linux - the failure this repo's verification discipline exists
to catch (see the note in test_drift_guard_agent_config.py).
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

import drift_guard as DG  # noqa: E402

pytestmark = pytest.mark.skipif(
    shutil.which("git") is None, reason="git not on PATH")


# ---------------------------------------------------------------------------
# hermetic fixture repo
# ---------------------------------------------------------------------------
def _git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True, text=True, creationflags=DG.NO_WINDOW, check=False)


def make_repo(tmp_path: Path, gitignore: str, files: dict[str, str]) -> Path:
    """A throwaway repo where `files` are TRACKED regardless of `gitignore`.

    `git add -f` is the whole point of the fixture: it reproduces the only way
    these paths can exist, which is someone forcing them in once (or the rule
    arriving later) and the index quietly keeping them afterwards.
    """
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.email", "test@example.invalid")
    _git(repo, "config", "user.name", "test")
    (repo / ".gitignore").write_text(gitignore, encoding="ascii")
    for rel, body in files.items():
        p = repo / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(body, encoding="ascii")
        _git(repo, "add", "-f", "--", rel)
    _git(repo, "add", "--", ".gitignore")
    _git(repo, "commit", "-q", "-m", "fixture")
    return repo


# ---------------------------------------------------------------------------
# the finder
# ---------------------------------------------------------------------------
def test_finds_a_tracked_path_an_ignore_rule_covers(tmp_path):
    """The arm itself: tracked, yet the rules say ignore."""
    repo = make_repo(
        tmp_path,
        "_archive/\n",
        {"docs/_archive/map.md": "m\n", "tools/real.py": "x = 1\n"},
    )
    assert DG.find_tracked_but_ignored(repo) == ["docs/_archive/map.md"]


def test_a_repo_with_no_such_path_reports_nothing(tmp_path):
    """MUTATION GUARD (inversion). If the condition were flipped to report the
    tracked paths that are NOT ignored, this repo would yield two hits instead
    of zero and this test goes red. Paired with the test above - which goes red
    if the check is stubbed to a no-op - the arm cannot be disarmed silently in
    either direction.
    """
    repo = make_repo(
        tmp_path,
        "*.log\n",
        {"docs/notes.md": "n\n", "tools/real.py": "x = 1\n"},
    )
    assert DG.find_tracked_but_ignored(repo) == []


def test_an_ignored_but_UNtracked_path_is_not_reported(tmp_path):
    """Ignoring an untracked file is what .gitignore is FOR. Only the
    tracked-and-ignored overlap is the trap; flagging the rest is noise that
    would bury it.
    """
    repo = make_repo(tmp_path, "build/\n", {"tools/real.py": "x = 1\n"})
    (repo / "build").mkdir()
    (repo / "build" / "out.o").write_text("o\n", encoding="ascii")
    assert DG.find_tracked_but_ignored(repo) == []


def test_a_reincluded_path_is_not_reported(tmp_path):
    """`images/**` + `!images/**/.gitkeep` is exactly LW's shape: the re-include
    means .gitkeep is NOT ignored, so it must not be reported.
    """
    repo = make_repo(
        tmp_path,
        "images/**\n!images/**/\n!images/**/.gitkeep\n",
        {"images/0.Originals/.gitkeep": ""},
    )
    assert DG.find_tracked_but_ignored(repo) == []


def test_a_path_with_a_space_survives_the_batched_call(tmp_path):
    """The batch is fed over stdin; a naive newline/space split loses this one.
    LW's own root has a space in it, so this is not hypothetical.
    """
    repo = make_repo(tmp_path, "_archive/\n", {"docs/_archive/a b c.md": "m\n"})
    assert DG.find_tracked_but_ignored(repo) == ["docs/_archive/a b c.md"]


def test_the_finder_makes_one_batched_call_not_one_per_file(tmp_path, monkeypatch):
    """drift_guard runs at every session start against 450+ tracked files.
    Per-file spawning would make it unusable, so the batching is a contract.
    """
    repo = make_repo(
        tmp_path, "_archive/\n",
        {f"docs/_archive/f{i}.md": "m\n" for i in range(12)},
    )
    calls: list[list] = []
    real = subprocess.run

    def counting(cmd, *a, **kw):
        calls.append(cmd)
        return real(cmd, *a, **kw)

    monkeypatch.setattr(DG.subprocess, "run", counting)
    hits = DG.find_tracked_but_ignored(repo)
    assert len(hits) == 12
    assert len(calls) <= 2, f"expected <=2 subprocess calls, got {len(calls)}"


# ---------------------------------------------------------------------------
# APPEARS IS NOT GOES-AWAY
# ---------------------------------------------------------------------------
def test_the_report_CLEARS_when_the_gitignore_rule_is_anchored(tmp_path):
    """Prove the finding can be RESOLVED, not merely raised.

    The live fix for LW is one character: anchor `_archive/` as `/_archive/` so
    it covers the ROOT quarantine dir it was written for and stops swallowing
    docs/_archive/. A report the operator cannot clear is a defect, so this
    walks the actual before/after rather than asserting only that it fires.
    """
    repo = make_repo(
        tmp_path, "_archive/\n",
        {"docs/_archive/map.md": "m\n", "tools/real.py": "x = 1\n"},
    )
    assert DG.find_tracked_but_ignored(repo) == ["docs/_archive/map.md"], "before"

    (repo / ".gitignore").write_text("/_archive/\n", encoding="ascii")
    assert DG.find_tracked_but_ignored(repo) == [], "after the one-character fix"

    # and the anchored rule still does its original job on the root dir.
    (repo / "_archive").mkdir()
    (repo / "_archive" / "quarantined.md").write_text("q\n", encoding="ascii")
    _git(repo, "add", "-A")
    r = _git(repo, "status", "--porcelain")
    assert "_archive/quarantined.md" not in r.stdout


def test_the_breach_clears_from_the_report_too(tmp_path):
    """Same proof one level up, through the reporting layer that /done reads.

    Deliberately NOT under an exempt prefix, so this walks the BREACH out of
    the report - the severity that actually blocks a /done.
    """
    repo = make_repo(tmp_path, "quarantine/\n",
                     {"docs/quarantine/map.md": "m\n"})
    DG.problems.clear()
    DG.notes.clear()
    DG.check_tracked_but_ignored(repo)
    assert len(DG.problems) == 1

    (repo / ".gitignore").write_text("/quarantine/\n", encoding="ascii")
    DG.problems.clear()
    DG.notes.clear()
    DG.check_tracked_but_ignored(repo)
    assert DG.problems == []
    assert DG.notes, "a clean result still reports, so a silent skip is visible"


# ---------------------------------------------------------------------------
# severity + exemptions
# ---------------------------------------------------------------------------
def test_an_unexpected_path_is_a_BREACH(tmp_path):
    repo = make_repo(tmp_path, "logs/\n", {"logs/keep.md": "k\n"})
    DG.problems.clear()
    DG.notes.clear()
    DG.check_tracked_but_ignored(repo)
    assert len(DG.problems) == 1
    assert "logs/keep.md" in DG.problems[0]


def test_an_exempt_prefix_is_a_NOTE_not_a_breach(tmp_path, monkeypatch):
    """Exemptions are explicit prefixes, each commented in drift_guard with why.

    A deliberately tracked path must not wedge /done, but it must NOT go quiet
    either: the sibling-file trap is live in exactly those directories, so the
    exemption downgrades the severity and keeps the message.
    """
    monkeypatch.setattr(DG, "IGNORED_TRACKED_EXEMPT", ("docs/_archive/",))
    repo = make_repo(tmp_path, "_archive/\n", {"docs/_archive/map.md": "m\n"})
    DG.problems.clear()
    DG.notes.clear()
    DG.check_tracked_but_ignored(repo)
    assert DG.problems == []
    assert any("docs/_archive" in n for n in DG.notes)


def test_an_exemption_does_not_suppress_its_non_exempt_neighbours(tmp_path,
                                                                  monkeypatch):
    """Not a blanket suppression: a rogue path still breaches alongside it."""
    monkeypatch.setattr(DG, "IGNORED_TRACKED_EXEMPT", ("docs/_archive/",))
    repo = make_repo(
        tmp_path, "_archive/\nlogs/\n",
        {"docs/_archive/map.md": "m\n", "logs/keep.md": "k\n"},
    )
    DG.problems.clear()
    DG.notes.clear()
    DG.check_tracked_but_ignored(repo)
    assert len(DG.problems) == 1
    assert "logs/keep.md" in DG.problems[0]
    assert "docs/_archive/map.md" not in DG.problems[0]


def test_every_exemption_is_a_directory_prefix(tmp_path):
    """A bare-filename or empty exemption would silently widen into a blanket
    suppression the next time someone appended to the tuple.
    """
    for entry in DG.IGNORED_TRACKED_EXEMPT:
        assert entry and entry.endswith("/"), f"{entry!r} is not a dir prefix"
        assert not entry.startswith("/") and "\\" not in entry


# ---------------------------------------------------------------------------
# the message has to be actionable
# ---------------------------------------------------------------------------
def test_the_message_names_the_paths_and_says_what_to_do(tmp_path):
    repo = make_repo(tmp_path, "logs/\n", {"logs/keep.md": "k\n"})
    DG.problems.clear()
    DG.notes.clear()
    DG.check_tracked_but_ignored(repo)
    msg = DG.problems[0]
    assert "logs/keep.md" in msg, "must name the offending path"
    assert ".gitignore" in msg, "must point at where the fix goes"
    assert "add" in msg.lower(), "must say what actually breaks"


def test_the_printed_sample_is_capped(tmp_path):
    """Same shape as the existing checks - name a sample, count the rest,
    never dump 400 paths into a session-start report.
    """
    repo = make_repo(
        tmp_path, "logs/\n",
        {f"logs/f{i:02d}.md": "k\n" for i in range(30)},
    )
    DG.problems.clear()
    DG.notes.clear()
    DG.check_tracked_but_ignored(repo)
    msg = DG.problems[0]
    assert "30" in msg, "must report the true total"
    assert msg.count("logs/f") <= 8, "must not dump every path"


# ---------------------------------------------------------------------------
# wiring + environment
# ---------------------------------------------------------------------------
def test_a_missing_or_non_repo_directory_is_survivable(tmp_path):
    """CI, a worktree slice, a tarball checkout: no repo is not a crash."""
    assert DG.find_tracked_but_ignored(tmp_path / "nope") == []
    plain = tmp_path / "plain"
    plain.mkdir()
    assert DG.find_tracked_but_ignored(plain) == []


def test_main_calls_the_check():
    """An arm nobody calls asserts nothing - the gate has to be wired in."""
    src = (Path(__file__).resolve().parents[1]
           / "tools" / "drift_guard.py").read_text(encoding="ascii")
    body = src.split("def main()", 1)[1]
    assert "check_tracked_but_ignored()" in body


def test_the_subprocess_flag_is_guarded_for_non_windows():
    """No-console-flash rule (CLAUDE.md): every subprocess passes
    creationflags=NO_WINDOW. CREATE_NO_WINDOW exists ONLY on Windows, so the
    os.name check comes BEFORE the value assertion - this suite is authored on
    Windows and runs on Linux in CI.
    """
    if os.name == "nt":
        assert DG.NO_WINDOW == subprocess.CREATE_NO_WINDOW
        assert DG.NO_WINDOW != 0
    else:
        assert DG.NO_WINDOW == 0


def test_this_test_file_is_pure_ascii():
    """Repo hard rule: 7-bit ASCII, no em/en-dashes, no smart quotes."""
    raw = Path(__file__).resolve().read_bytes()
    assert max(raw) < 128, "non-ASCII byte in this file"
