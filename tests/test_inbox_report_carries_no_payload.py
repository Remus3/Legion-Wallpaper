"""The inbox report may carry NAMES, COUNTS and DIGESTS - never payload bytes.

LL's rule, reached LW through RSC's 0141 note: "an imperative sentence sitting
in someone else's source file must not be able to arrive in one of our sessions
wearing our own watcher's voice."

The mechanism is what makes it load-bearing rather than tidy. Everything this
watcher prints at `SessionStart` and `UserPromptSubmit` is injected into a
session's context carrying the HARNESS's authority, and it lands there before
any judgement is applied to it. A note body, a file inside a drop, a sender's
manifest and a raw exception string are all content written by another repo. So
the report may say what arrived and how much of it there is, and may not quote
any of it.

Two construction rules, both learned from other repos' measured failures:

- **The ARMING assertion comes first.** RSC's version pins this and the reason
  is that a watcher which crashed and printed nothing satisfies a bare
  no-payload assertion perfectly. Every arm below first proves the report
  actually reported.
- **Assert over WINDOWS of the payload, never one exact string.** CS measured
  the truncation hole on 2026-09-07: a mutant appending a 16-character preview
  of a payload file passed a suite whose planted sentence was 22 characters. A
  window sweep cannot be defeated by shortening the leak.

The bodies are high-entropy so that a window match is a leak and never a
coincidence of ordinary English.
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import lw_facts  # noqa: E402

NEWLINE = chr(10)
WINDOW = 12


def _secret(tag: str, n: int = 240) -> bytes:
    """A high-entropy body. Any WINDOW-length slice of it is effectively unique."""
    out = b""
    seed = tag.encode("ascii")
    while len(out) < n:
        seed = hashlib.sha256(seed).digest()
        out += seed.hex().encode("ascii")
    return out[:n]


def _windows(payload: bytes) -> list[str]:
    text = payload.decode("ascii")
    return [text[i:i + WINDOW] for i in range(len(text) - WINDOW + 1)]


@pytest.fixture
def wired(tmp_path):
    """An inbox holding a note, a drop with a file, and a sender's manifest.

    All three are payload. The manifest is included deliberately: it is shipped
    as human context and is explicitly NOT the key, which makes it the one a
    future change is most likely to start quoting.
    """
    box = tmp_path / "moon_sync_inbox"
    box.mkdir()
    (box / "2026-09-07-0000-from-XX-a-note.md").write_bytes(
        b"# heading" + NEWLINE.encode() + _secret("note"))
    drop = box / "from-XX-verbatim"
    drop.mkdir()
    (drop / "inner.py").write_bytes(_secret("inner"))
    (drop / "MANIFEST.sha256").write_bytes(_secret("manifest"))
    return box, tmp_path / "seen.json", tmp_path / "reported.json"


def _report(wired) -> str:
    box, seen, reported = wired
    return NEWLINE.join(lw_facts._inbox_lines([], inbox=box, seen_path=seen,
                                              reported_path=reported))


@pytest.mark.parametrize("tag", ["note", "inner", "manifest"])
def test_no_window_of_any_payload_reaches_the_report(wired, tag):
    block = _report(wired)
    assert "UNREAD" in block, (
        "ARMING: the report printed nothing to inspect, so a no-payload "
        f"assertion would pass vacuously. Got: {block!r}")
    leaked = [w for w in _windows(_secret(tag)) if w in block]
    assert not leaked, (
        f"the report quotes {tag} payload bytes: {leaked[:3]}")


def test_the_report_still_carries_the_metadata_it_is_FOR(wired):
    """The complement, so the property cannot be satisfied by printing nothing.

    Names and counts are not payload - they are the whole point, and a version
    of this module that suppressed them would pass every arm above.
    """
    block = _report(wired)
    assert "2026-09-07-0000-from-XX-a-note.md" in block
    assert "from-XX-verbatim" in block


def test_an_unreadable_inbox_reports_without_quoting_the_exception(tmp_path):
    """The error path is a payload path too - a raw exception can carry content.

    LW's probe is exception-proof by contract because it runs inside the
    SessionStart hook, so the interesting question is not whether it survives
    but what it PRINTS when it does.
    """
    victim = tmp_path / "moon_sync_inbox"
    victim.write_bytes(_secret("asfile"))
    lines = lw_facts._inbox_lines([], inbox=victim,
                                  seen_path=tmp_path / "seen.json",
                                  reported_path=tmp_path / "reported.json")
    block = NEWLINE.join(lines)
    assert block.strip(), "ARMING: the error path printed nothing at all"
    leaked = [w for w in _windows(_secret("asfile")) if w in block]
    assert not leaked, f"the error path quotes payload bytes: {leaked[:3]}"


def test_a_preview_mutant_would_be_CAUGHT_by_these_arms(wired):
    """Proves the arms are armed, using CS's own mutant.

    CS's finding was that an exact-string assertion is defeated by truncating
    the leak. This reproduces the leak the cheap way - by building the line a
    mutant would build - and asserts the window sweep sees it. Without this,
    a later refactor could weaken the sweep and nothing would notice.
    """
    box, _, _ = wired
    body = (box / "from-XX-verbatim" / "inner.py").read_bytes()
    mutant_line = f"  - from-XX-verbatim/ ({body.decode('ascii')[:16]})"
    leaked = [w for w in _windows(_secret("inner")) if w in mutant_line]
    assert leaked, (
        "the window sweep failed to see a 16-character preview leak - "
        "WINDOW is too large to catch a short truncation")
