"""RRF-2.10 (MAIN REPO-REVIEW 2.10): one session-scoped tracked corpus.

The hygiene guards each ran their own `git ls-files -z` and re-read the
tracked tree from disk (655 files, 9.66 MB, measured by MAIN 2026-10-08).
`tests/tracked_corpus.py` asks git ONCE per test process and reads each file
ONCE; `tracked_corpus` (tests/conftest.py, scope=session) hands the same
object to any test that wants it as a fixture.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

import tracked_corpus as tc

ROOT = Path(__file__).resolve().parents[1]

# The tree-wide guards that used to enumerate the corpus themselves.
CONSUMERS = (
    "test_ascii_only_authored.py",
    "test_live_docs_cite_lines_that_exist.py",
    "test_no_account_paths.py",
    "test_no_account_uuid.py",
    "test_no_hardcoded_c_paths.py",
    "test_no_identity_enters_history.py",
    "test_no_secret_literals.py",
    "test_no_split_identity.py",
)
_OWN_LS_FILES = re.compile(r"""["']ls-files["']\s*,\s*["']-z["']""")


def test_the_fixture_is_session_scoped_and_is_the_shared_module(request, tracked_corpus):
    assert tracked_corpus is tc
    fixturedef = request._fixturemanager.getfixturedefs("tracked_corpus", request.node)[-1]
    assert fixturedef.scope == "session"


def test_git_is_asked_once_and_the_corpus_is_real(tracked_corpus):
    first, second = tracked_corpus.tracked_files(), tracked_corpus.tracked_files()
    assert first is second
    assert len(first) > 100
    assert "tests/test_tracked_corpus.py" in first or "tests/conftest.py" in first


def test_each_file_is_read_once():
    a = tc.read_bytes("tests/conftest.py")
    assert tc.read_bytes("tests/conftest.py") is a
    assert a == (ROOT / "tests/conftest.py").read_bytes()


def test_read_text_matches_path_read_text_newline_translation(tmp_path, monkeypatch):
    monkeypatch.setattr(tc, "REPO", tmp_path)
    tc.read_bytes.cache_clear()
    try:
        (tmp_path / "crlf.txt").write_bytes(b"a\r\nb\rc\n")
        assert tc.read_text("crlf.txt") == (tmp_path / "crlf.txt").read_text(encoding="utf-8")
        (tmp_path / "bad.txt").write_bytes(b"\xff")
        with pytest.raises(UnicodeDecodeError):
            tc.read_text("bad.txt")
        assert tc.read_text("bad.txt", errors="replace") == "\ufffd"
    finally:
        tc.read_bytes.cache_clear()


@pytest.mark.parametrize("name", CONSUMERS)
def test_no_hygiene_guard_runs_its_own_ls_files(name):
    src = (ROOT / "tests" / name).read_text(encoding="utf-8")
    assert not _OWN_LS_FILES.search(src), f"{name} still enumerates the tree itself"
    assert "tracked_corpus" in src
