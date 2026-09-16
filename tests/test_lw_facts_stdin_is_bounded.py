"""The stdin payload read must be BOUNDED in bytes AND in seconds.

This is the riskiest edit in LW's moon-sync adoption slice, and the risk is
asymmetric in a way that hides it. `lw_facts.py --inbox-only` is wired as the
UserPromptSubmit hook, so it runs on EVERY operator message. The session id it
needs lives in a JSON payload the harness writes to stdin - but a hook that
blocks on that read does not fail loudly, it times out silently, and the only
visible symptom is that cross-repo mail stops being announced. That is the
exact failure mode the watcher exists to prevent, re-introduced by the code
added to make the watcher better.

BOTH bounds are load-bearing and neither is sufficient alone:

  * a byte cap with no clock cap still parks forever on a parent that writes
    fewer bytes than the cap and never closes the pipe - which is what a
    `read(n)` on a live pipe does, and what the harness looks like whenever it
    supplies no payload;
  * a clock cap with no byte cap still buffers an unbounded write into memory
    before the clock is ever consulted.

The timing arm below is the one that matters, so it is written to fail on the
unbounded implementation rather than to describe the bounded one: it opens a
real pipe, writes NOTHING, never closes the write end, and asserts the call
returns anyway. On an unbounded `read()` that arm hangs until pytest is killed.

The validation arms cover the second half: a session id is a machine-supplied
token that lands in a tab-separated log line and in a JSON record, so anything
that is not an anchored, charset-bounded, length-bounded token is treated as NO
session id - which fails OPEN (print, suppress nothing), never closed.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import lw_facts as F  # noqa: E402


class _FakeStdin:
    """A stdin whose `.buffer` is a real OS pipe read end."""

    def __init__(self, fd: int) -> None:
        self.buffer = os.fdopen(fd, "rb", buffering=0)
        self.closed = False

    def isatty(self) -> bool:
        return False


@pytest.fixture
def pipe_stdin(monkeypatch):
    """Replace sys.stdin with a real pipe. Returns the WRITE fd, still open."""
    made: list[tuple[int, _FakeStdin]] = []

    def _make() -> int:
        r, w = os.pipe()
        fake = _FakeStdin(r)
        monkeypatch.setattr(sys, "stdin", fake)
        made.append((w, fake))
        return w

    yield _make
    for w, fake in made:
        try:
            os.close(w)
        except OSError:
            pass
        try:
            fake.buffer.close()
        except OSError:
            pass


def test_a_writer_that_never_closes_does_not_hang_the_hook(pipe_stdin):
    """The whole point. No bytes, no EOF, and the call must still return.

    On an unbounded read this does not fail - it HANGS, which is precisely why
    the defect is worth a test rather than a code comment.
    """
    pipe_stdin()
    t0 = time.monotonic()
    out = F._read_stdin_bounded(cap_bytes=1024, cap_s=0.2)
    elapsed = time.monotonic() - t0
    assert out == b"", out
    assert elapsed < 3.0, f"the bounded read took {elapsed:.2f}s - it is not bounded"


def test_a_partial_write_with_no_close_still_returns(pipe_stdin):
    """The realistic shape of the hang: the parent writes the payload and then
    keeps the pipe open. `read(cap)` waits for the remaining cap-n bytes that
    are never coming."""
    w = pipe_stdin()
    os.write(w, json.dumps({"session_id": "abcd1234efgh"}).encode("utf-8"))
    t0 = time.monotonic()
    out = F._read_stdin_bounded(cap_bytes=64 * 1024, cap_s=0.3)
    elapsed = time.monotonic() - t0
    assert elapsed < 3.0, f"the bounded read took {elapsed:.2f}s"
    # Whatever it managed to read must not be MORE than what was written.
    assert len(out) <= 64 * 1024


def test_a_closed_writer_yields_the_whole_payload(pipe_stdin):
    """Guard the guard: the bounds must not have broken the happy path."""
    w = pipe_stdin()
    payload = json.dumps({"session_id": "abcd1234efgh", "cwd": "x"}).encode("utf-8")
    os.write(w, payload)
    os.close(w)
    out = F._read_stdin_bounded(cap_bytes=64 * 1024, cap_s=2.0)
    assert out == payload, out
    assert F._session_id_from(out) == "abcd1234efgh"


def test_the_byte_cap_is_honoured(pipe_stdin):
    """The second bound, measured independently of the clock."""
    w = pipe_stdin()
    os.write(w, b"x" * 4096)
    os.close(w)
    out = F._read_stdin_bounded(cap_bytes=100, cap_s=2.0)
    assert len(out) == 100, len(out)


def test_a_tty_stdin_is_not_read_at_all():
    """A manual `python tools/lw_facts.py` at a console must never block."""

    class _Tty:
        buffer = object()
        closed = False

        def isatty(self) -> bool:
            return True

    saved = sys.stdin
    sys.stdin = _Tty()
    try:
        assert F._read_stdin_bounded(cap_bytes=10, cap_s=5.0) == b""
    finally:
        sys.stdin = saved


@pytest.mark.parametrize("payload", [
    b"",
    b"not json at all",
    b"[1, 2, 3]",
    b'"a bare string"',
    json.dumps({}).encode("utf-8"),
    json.dumps({"session_id": None}).encode("utf-8"),
    json.dumps({"session_id": ""}).encode("utf-8"),
    json.dumps({"session_id": "short"}).encode("utf-8"),
    json.dumps({"session_id": "has a space in it"}).encode("utf-8"),
    json.dumps({"session_id": "tab\there"}).encode("utf-8"),
    json.dumps({"session_id": "newline\nhere"}).encode("utf-8"),
    json.dumps({"session_id": "x" * 200}).encode("utf-8"),
])
def test_an_unusable_payload_reads_as_no_session_id(payload):
    """Every one of these fails OPEN - no id means print and suppress nothing."""
    assert F._session_id_from(payload) is None


@pytest.mark.parametrize("sid", [
    "f716e8e1-616e-4acb-a3c5-0ce1475eb1db",
    "abcd1234",
    "A_b-C_9" * 3,
])
def test_a_well_formed_session_id_is_accepted(sid):
    assert F._session_id_from(
        json.dumps({"session_id": sid}).encode("utf-8")) == sid


def test_a_forged_field_cannot_break_a_log_line(tmp_path):
    """A tab or a newline in any logged field would forge a second record.

    The id is already rejected upstream, but the log scrubber is the backstop
    and it is asserted directly rather than assumed from that rejection.
    """
    log = tmp_path / "invocations.log"
    F._log_invocation("mode\twith\ttabs", "sid\nwith\nnewlines",
                      note="note\r\nline two", log_path=log)
    text = log.read_text(encoding="utf-8")
    assert text.count("\n") == 1, repr(text)
    assert text.count("\t") == 3, repr(text)


def test_the_invocation_log_is_written_at_all(tmp_path):
    """LW had no invocation log; "did the hook fire" was unanswerable."""
    log = tmp_path / "invocations.log"
    F._log_invocation("inbox-only", "abcd1234efgh", note="printed=True", log_path=log)
    F._log_invocation("session-start", None, note="anomalies=0", log_path=log)
    rows = [ln.split("\t") for ln in
            log.read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 2, rows
    assert [r[1] for r in rows] == ["inbox-only", "session-start"]
    assert rows[0][2] == "abcd1234efgh"
    assert rows[1][2] == "-", "a missing session id must log as '-', not as empty"


def test_the_invocation_log_never_raises_on_an_unwritable_path(tmp_path):
    """Best effort by contract: the log must never be why a hook fails."""
    blocker = tmp_path / "blocker"
    blocker.write_text("not a directory\n", encoding="utf-8")
    F._log_invocation("inbox-only", "abcd1234efgh",
                      log_path=blocker / "nested" / "invocations.log")
