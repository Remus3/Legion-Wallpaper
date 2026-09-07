"""Guard for the repo-root hand-off target: tools/lw_next_session.py.

WHY THIS EXISTS (BACKLOG next-session-handoff-enforcement): the write target
must never be taken on trust - it is read from an on-disk intent document, and
ANY non-conforming value falls back to the LW default rather than being
honoured. A cross-repo write must be a deliberate act, never a fallback.

The hand-off lives in the REPO ROOT (moved 2026-09-06, operator-directed via
RC's cross-repo note): the Desktop is untracked and unreviewable, so nothing
could notice a hand-off going stale and no diff showed what the last session
handed over. The Desktop keeps a SHORTCUT to the repo file, so operator access
is unchanged. The `LW-` prefix stays on the filename even though it is now
redundant in-repo: the Desktop shortcuts are still a shared surface, and the
prefix is what stops a doctored intent document naming an arbitrary target.

The rejection set is the point - absolute paths, drive letters, `..` segments,
path separators, empty/blank, non-string, and any filename not prefixed `LW-`.
A stale or doctored intent document must not be able to aim an LW session at
`RC-NEXT-SESSION.txt`.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import lw_next_session as ns  # noqa: E402


# ---------------------------------------------------------------------------
# 1. the default
# ---------------------------------------------------------------------------
def test_the_default_filename_is_the_lw_namespaced_one():
    assert ns.DEFAULT_NAME == "LW-NEXT-SESSION.txt"
    assert ns.DEFAULT_NAME.startswith(ns.REQUIRED_PREFIX)


def test_no_intent_document_resolves_to_the_default(tmp_path):
    name, reason = ns.choose_filename_from_intent(tmp_path / "missing.json")
    assert name == ns.DEFAULT_NAME
    assert "no intent document" in reason


def test_target_lands_in_the_given_repo_root(tmp_path):
    target = ns.resolve_target(root=tmp_path, intent_path=tmp_path / "none.json")
    assert target == tmp_path / ns.DEFAULT_NAME


def test_the_real_target_is_the_repo_root_not_the_desktop():
    """The 2026-09-06 move. A Desktop target is untracked and unreviewable."""
    target = ns.resolve_target(intent_path=Path("no-such-intent.json"))
    assert target == ns.ROOT / ns.DEFAULT_NAME
    assert target.parent == ns.ROOT
    assert "Desktop" not in target.parts


def test_the_repo_root_target_is_trackable_by_git():
    """A hand-off in an ignored path is exactly as invisible as the Desktop one."""
    import subprocess
    target = ns.resolve_target(intent_path=Path("no-such-intent.json"))
    res = subprocess.run(["git", "check-ignore", "-q", target.name],
                         cwd=ns.ROOT, capture_output=True)
    assert res.returncode == 1, f"{target.name} is gitignored, so it would never be tracked"


# ---------------------------------------------------------------------------
# 2. the accepted case
# ---------------------------------------------------------------------------
def test_a_conforming_lw_prefixed_name_is_honoured():
    name, reason = ns.choose_filename("LW-NEXT-SESSION-batch21.txt")
    assert name == "LW-NEXT-SESSION-batch21.txt"
    assert reason == ""


def test_a_conforming_name_is_read_out_of_the_intent_document(tmp_path):
    doc = tmp_path / "intent.json"
    doc.write_text(json.dumps({"filename": "LW-HANDOFF.txt"}), encoding="utf-8")
    name, reason = ns.choose_filename_from_intent(doc)
    assert name == "LW-HANDOFF.txt"
    assert reason == ""


# ---------------------------------------------------------------------------
# 3. the rejection set - every one falls back to the default
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("value", [
    "RC-NEXT-SESSION.txt",                  # a SIBLING's hand-off - the whole point
    "RM-NEXT-SESSION.txt",
    "NEXT-SESSION.txt",                     # unprefixed
    "lw-next-session.txt",                  # prefix is case-sensitive
    "C:/Users/example/Desktop/LW-X.txt",   # absolute + drive letter
    "C:\\Users\\example\\Desktop\\LW-X.txt",
    "/etc/passwd",
    "../LW-NEXT-SESSION.txt",               # escape upward
    "..\\LW-NEXT-SESSION.txt",
    "sub/LW-NEXT-SESSION.txt",              # any separator at all
    "sub\\LW-NEXT-SESSION.txt",
    "LW-../escape.txt",                     # prefix present but still escapes
    "",                                     # empty
    "   ",                                  # blank
    "LW-",                                  # prefix and nothing else
    ".",
    "..",
])
def test_non_conforming_values_fall_back_to_the_default(value):
    name, reason = ns.choose_filename(value)
    assert name == ns.DEFAULT_NAME, f"{value!r} was honoured but must not be"
    assert reason, "a rejection must explain itself"


@pytest.mark.parametrize("value", [None, 42, 3.5, True, ["LW-x.txt"], {"a": 1}])
def test_non_string_values_fall_back_to_the_default(value):
    name, reason = ns.choose_filename(value)
    assert name == ns.DEFAULT_NAME
    assert reason


def test_a_sibling_repo_cannot_be_targeted_via_the_intent_document(tmp_path):
    """The headline attack: a stale/doctored document aimed at RC's hand-off."""
    doc = tmp_path / "intent.json"
    doc.write_text(json.dumps({"filename": "RC-NEXT-SESSION.txt"}), encoding="utf-8")
    name, reason = ns.choose_filename_from_intent(doc)
    assert name == ns.DEFAULT_NAME
    assert "LW-" in reason
    target = ns.resolve_target(root=tmp_path, intent_path=doc)
    assert target.name == ns.DEFAULT_NAME


# ---------------------------------------------------------------------------
# 4. a malformed intent document is not an error path, it is the default path
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("body", ["{ not json", "[]", '"a string"', "null", "{}",
                                  '{"other_key": "LW-x.txt"}'])
def test_a_malformed_intent_document_falls_back_rather_than_raising(tmp_path, body):
    doc = tmp_path / "intent.json"
    doc.write_text(body, encoding="utf-8")
    name, reason = ns.choose_filename_from_intent(doc)
    assert name == ns.DEFAULT_NAME
    assert reason


# ---------------------------------------------------------------------------
# 5. the write itself
# ---------------------------------------------------------------------------
def test_write_is_atomic_and_leaves_no_temp_file(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    written = ns.write_handoff("NEXT SESSION\nbody\n", root=root,
                               intent_path=tmp_path / "none.json")
    assert written.read_text(encoding="utf-8") == "NEXT SESSION\nbody\n"
    assert list(root.iterdir()) == [written]


def test_write_creates_the_target_directory_if_absent(tmp_path):
    written = ns.write_handoff("x\n", root=tmp_path / "absent",
                               intent_path=tmp_path / "none.json")
    assert written.is_file()


def test_write_overwrites_rather_than_appends(tmp_path):
    kw = {"root": tmp_path, "intent_path": tmp_path / "none.json"}
    ns.write_handoff("first\n", **kw)
    second = ns.write_handoff("second\n", **kw)
    assert second.read_text(encoding="utf-8") == "second\n"


def test_write_refuses_a_sibling_target_end_to_end(tmp_path):
    doc = tmp_path / "intent.json"
    doc.write_text(json.dumps({"filename": "RC-NEXT-SESSION.txt"}), encoding="utf-8")
    written = ns.write_handoff("body\n", root=tmp_path, intent_path=doc)
    assert written.name == ns.DEFAULT_NAME
    assert not (tmp_path / "RC-NEXT-SESSION.txt").exists()


def test_written_content_is_ascii_only_by_contract(tmp_path):
    """The repo is 7-bit ASCII; the hand-off is authored text like any other."""
    with pytest.raises(ValueError):
        ns.write_handoff("smart \u201cquotes\u201d\n", root=tmp_path,
                         intent_path=tmp_path / "none.json")


# ---------------------------------------------------------------------------
# 6. the ritual doc must not drift back to the Desktop
# ---------------------------------------------------------------------------
def test_the_done_ritual_writes_the_handoff_from_its_ALWAYS_section():
    """Writing the hand-off is unconditional; only consuming an intent is gated."""
    doc = (ns.ROOT / ".claude" / "commands" / "done.md").read_text(encoding="utf-8")
    assert "python tools/lw_next_session.py --write -" in doc
    head, _, tail = doc.partition("### 10b.")
    assert tail, "done.md has no section 10b"
    assert "(ALWAYS)" in tail.splitlines()[0], "10b must be marked ALWAYS"
    assert "Desktop hand-off" not in tail, "10b still calls the target a Desktop file"
