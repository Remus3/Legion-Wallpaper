"""The hand-off is gated at WRITE time, by the SAME engine as the commit hook.

WHY THIS EXISTS (ROADMAP `handoff-write-gate`): `LW-NEXT-SESSION.txt` is
TRACKED in a PUBLIC repo and is the highest-variance artifact in the tree. It
is written fresh every session, never reviewed before it is written, and quotes
freely from whatever that session happened to touch. The asymmetry, which is
Clockspeed's and is the whole reason this file exists:

    a Desktop file that is wrong costs one edit; a tracked one costs a history
    rewrite

and LW rewrote its whole history twice in the week this landed.

So the gate runs BEFORE the write, while the hand-off is still a string in
memory and the session can still fix it - not after a commit, by which point
the only remedy is a rewrite. `tools/lw_next_session.write_handoff` already
refused non-ASCII, so the refusal PATH existed; only the rule set grows.

ONE reading of the rule is the load-bearing part. The rules live in
`tools/precommit_gate.scan_handoff_text` and BOTH enforcement points call that
one function object - write time here, commit time in `_staged_violations`.
`test_the_two_enforcement_points_share_one_engine` asserts the identity rather
than the behaviour, because two implementations that agree today are exactly
the defect this consolidates (LW carries three separate declarations of the
banned-glyph rule and they agree only by inspection).

Explicitly NOT solved with a per-session exemption list. CS's reason is right:
an exemption list that grows once per session is a gate disarmed one word at a
time.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import lw_next_session as ns  # noqa: E402
import precommit_gate as pg  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent

# A hand-off that carries nothing it should not. Deliberately mentions a short
# sha and a repo-relative path, because a gate that refuses those is useless.
CLEAN = (
    "NEXT SESSION\n"
    "------------\n"
    "Task: ROADMAP handoff-write-gate - see tools/lw_next_session.py.\n"
    "Verified: ops/loop/winmutex.py 0b112a4f in LW + RC + RSC.\n"
)


def _kw(tmp_path):
    """Write into a temp root with no intent document in play."""
    return {"root": tmp_path, "intent_path": tmp_path / "no-intent.json"}


# ---------------------------------------------------------------------------
# 1. the positive control - a gate that refuses everything passes every
#    refusal test, so the clean case is asserted first
# ---------------------------------------------------------------------------
def test_a_clean_handoff_is_written(tmp_path):
    written = ns.write_handoff(CLEAN, **_kw(tmp_path))
    assert written.name == ns.DEFAULT_NAME
    assert written.read_text(encoding="utf-8") == CLEAN


def test_the_live_tracked_handoff_passes_the_gate():
    """The artifact actually in the tree must stay clean, not just be gateable."""
    live = ROOT / ns.DEFAULT_NAME
    if not live.is_file():
        pytest.skip(f"{ns.DEFAULT_NAME} is not present in the repo root")
    assert pg.scan_handoff_text(live.read_text(encoding="utf-8", errors="replace")) == []


# ---------------------------------------------------------------------------
# 2. the three rule classes the ROADMAP names, each proven in BOTH directions
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "body, rule",
    [
        ("key material: sk-liveKEYmaterial0123456789abcd\n", "secret"),
        ("token = 0123456789abcdefghij\n", "secret"),
        ("password: hunter2hunter2\n", "secret"),
        ("-----BEGIN RSA PRIVATE KEY-----\n", "secret"),
        ("logs live under C:\\Users\\SomeAccount\\AppData\\Local\n", "user-profile"),
        ("see /home/someaccount/notes.txt\n", "user-profile"),
        ("see /Users/someaccount/notes.txt\n", "user-profile"),
        ("cd %USERPROFILE%\\Desktop\n", "user-profile"),
        ("pinned at 0123456789abcdef0123456789abcdef\n", "32-hex"),
        ("blob e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855\n", "32-hex"),
    ],
)
def test_a_handoff_carrying_gated_content_is_refused(tmp_path, body, rule):
    with pytest.raises(ns.HandoffRefused) as exc:
        ns.write_handoff(CLEAN + body, **_kw(tmp_path))
    assert rule in str(exc.value)


@pytest.mark.parametrize(
    "body",
    [
        "commit 4c0eaf8 landed\n",                      # short sha
        "sha12=cd84bd20c06c ok\n",                      # 12 hex, under the floor
        "pinned 0123456789abcdef0123456789abcde\n",     # 31 hex, one under
        "the token bucket refilled\n",                  # the word, no assignment
        "images/0.Originals holds the loose files\n",   # repo-relative path
        "C:\\Legion Wallpaper\\ops\\runtime\\ - project root, not a profile\n",
    ],
)
def test_the_gate_is_not_over_broad(tmp_path, body):
    """A rule that refuses ordinary hand-off content gets exemptions bolted on,
    and an exemption list is a gate disarmed one word at a time. So the
    not-refused direction is asserted case by case, same as the refused one."""
    written = ns.write_handoff(CLEAN + body, **_kw(tmp_path))
    assert written.read_text(encoding="utf-8").endswith(body)


def test_non_ascii_is_still_refused_and_refusal_is_a_valueerror(tmp_path):
    """The pre-existing contract survives: callers catching ValueError (the
    `--write` CLI does) keep working after the rule set grew."""
    assert issubclass(ns.HandoffRefused, ValueError)
    with pytest.raises(ValueError):
        ns.write_handoff("smart \u201cquotes\u201d\n", **_kw(tmp_path))


# ---------------------------------------------------------------------------
# 3. refusal must leave the disk untouched - a partial write is worse than
#    the content it refused
# ---------------------------------------------------------------------------
def test_refusal_writes_nothing_at_all(tmp_path):
    with pytest.raises(ns.HandoffRefused):
        ns.write_handoff(CLEAN + "token = 0123456789abcdefghij\n", **_kw(tmp_path))
    assert list(tmp_path.iterdir()) == [], "refusal left something on disk"


def test_refusal_does_not_clobber_an_existing_handoff(tmp_path):
    good = ns.write_handoff(CLEAN, **_kw(tmp_path))
    with pytest.raises(ns.HandoffRefused):
        ns.write_handoff(CLEAN + "password: hunter2hunter2\n", **_kw(tmp_path))
    assert good.read_text(encoding="utf-8") == CLEAN
    assert not good.with_name(good.name + ".tmp").exists()


def test_a_finding_never_echoes_the_secret_it_found():
    """The report goes to stderr and into logs; repeating the value there just
    moves the disclosure."""
    secret = "sk-liveKEYmaterial0123456789abcd"
    findings = pg.scan_handoff_text(f"key: {secret}\n")
    assert findings, "the fixture is meant to be refused"
    assert secret not in "\n".join(findings)


# ---------------------------------------------------------------------------
# 4. one reading of the rule - the identity, not merely agreeing behaviour
# ---------------------------------------------------------------------------
def test_the_two_enforcement_points_share_one_engine():
    assert ns.scan_handoff_text is pg.scan_handoff_text


def test_the_commit_side_recognises_the_file_the_write_side_writes():
    """A rename of DEFAULT_NAME must not silently unhook the commit-time half."""
    assert pg.is_handoff_path(ns.DEFAULT_NAME)
    assert pg.is_handoff_path("LW-SOMETHING-ELSE.txt"), "the intent contract allows LW-*"
    assert not pg.is_handoff_path("docs/" + ns.DEFAULT_NAME), "repo root only"
    assert not pg.is_handoff_path("RC-NEXT-SESSION.txt"), "a sibling's hand-off is not ours"
    assert not pg.is_handoff_path("README.md")


# ---------------------------------------------------------------------------
# 5. the CLI, which is how CI and a human run the same engine over a file
# ---------------------------------------------------------------------------
def _scan_files(*paths):
    return subprocess.run(
        [sys.executable, str(ROOT / "tools" / "precommit_gate.py"), "--scan-files", *paths],
        capture_output=True, text=True, timeout=60, cwd=str(ROOT),
    )


def test_scan_files_exits_zero_on_a_clean_file(tmp_path):
    p = tmp_path / "clean.txt"
    p.write_text(CLEAN, encoding="ascii")
    out = _scan_files(str(p))
    assert out.returncode == 0, out.stderr


def test_scan_files_exits_two_on_a_dirty_file(tmp_path):
    p = tmp_path / "dirty.txt"
    p.write_text(CLEAN + "pinned 0123456789abcdef0123456789abcdef\n", encoding="ascii")
    out = _scan_files(str(p))
    assert out.returncode == 2
    assert "32-hex" in out.stderr


def test_scan_files_passes_the_live_handoff():
    live = ROOT / ns.DEFAULT_NAME
    if not live.is_file():
        pytest.skip(f"{ns.DEFAULT_NAME} is not present in the repo root")
    out = _scan_files(str(live))
    assert out.returncode == 0, out.stderr
