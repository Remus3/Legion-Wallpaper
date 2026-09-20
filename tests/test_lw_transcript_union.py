"""Tests for tools/lw_transcript_union.py - the line-level transcript-store union.

Context (measured 2026-09-20, docs/TRANSCRIPT_UNION_2026-09-20.md): `~/.claude/projects`
carried TWO store keys encoding one tree, `C--Legion-Wallpaper` (canonical) and
`C--LegionWallpaper` (stray), with three session UUIDs present under BOTH. One pair was
byte-identical, one was a stray superset by a single record, and one was a contiguous
CONTINUATION TAIL (zero uuid overlap, the stray's first record parented on the canonical
copy's last uuid). A multiset union recovers all three without dropping a record.

EVERY test here injects its state via tmp_path. Nothing reads the real
`~/.claude/projects` and nothing depends on this machine - `tests/test_drift_guard_agent_config.py`
was written the same way for the same reason (a test that read machine state passed
locally and went red on CI). Written test-first per CLAUDE.md TDD.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

import lw_transcript_union as ltu  # noqa: E402


# --------------------------------------------------------------------------- helpers

def rec(uuid: str | None, **extra) -> str:
    """One transcript record as the exact bytes a .jsonl line would carry."""
    body: dict[str, object] = {"type": extra.pop("type", "assistant")}
    if uuid is not None:
        body["uuid"] = uuid
    body.update(extra)
    return json.dumps(body, separators=(",", ":")) + "\n"


def write_store(tmp_path: Path, canon: dict[str, list[str]], stray: dict[str, list[str]]) -> tuple[Path, Path]:
    """Build a two-key store under tmp_path. Values are lists of raw lines."""
    cdir = tmp_path / "projects" / "C--Canon"
    sdir = tmp_path / "projects" / "C--Stray"
    cdir.mkdir(parents=True)
    sdir.mkdir(parents=True)
    for name, lines in canon.items():
        (cdir / name).write_text("".join(lines), encoding="utf-8", newline="")
    for name, lines in stray.items():
        (sdir / name).write_text("".join(lines), encoding="utf-8", newline="")
    return cdir, sdir


def age_out(directory: Path, seconds: float = 10_000) -> None:
    """Push every mtime in `directory` outside the live-session window."""
    old = time.time() - seconds
    for p in directory.iterdir():
        os.utime(p, (old, old))


# --------------------------------------------------------------------------- union semantics

def test_superset_pair_appends_only_the_stray_only_record():
    canon = [rec("a"), rec("b"), rec("c")]
    stray = [rec("a"), rec("b"), rec("c"), rec("d")]
    out, appended = ltu.union_lines(canon, stray)
    assert out == canon + [rec("d")]
    assert appended == [rec("d")]


def test_identical_pair_is_a_no_op():
    canon = [rec("a"), rec("b")]
    out, appended = ltu.union_lines(canon, list(canon))
    assert out == canon
    assert appended == []


def test_continuation_tail_keeps_canonical_first_then_the_whole_tail():
    """The d3d7c8f7 shape: disjoint uuid sets, stray parented on canon's last record."""
    canon = [rec("c1"), rec("c2", parentUuid="c1")]
    stray = [rec("s1", parentUuid="c2"), rec("s2", parentUuid="s1")]
    out, appended = ltu.union_lines(canon, stray)
    assert out == canon + stray, "canonical order must come first, tail appended in its own order"
    assert appended == stray


def test_genuine_fork_drops_nothing_from_either_side():
    """Both sides hold records the other lacks - a union is still lossless."""
    canon = [rec("shared"), rec("conly1"), rec("conly2")]
    stray = [rec("shared"), rec("sonly1")]
    out, appended = ltu.union_lines(canon, stray)
    for line in canon + stray:
        assert line in out
    assert appended == [rec("sonly1")]
    assert out.index(rec("conly1")) < out.index(rec("sonly1"))


def test_record_present_in_both_is_not_duplicated():
    """MUTATION-PROVED arm. Keys on `uuid`, so re-serialized bytes still dedupe."""
    canon = [rec("a", timestamp="T1"), rec("b", timestamp="T2")]
    stray = [rec("a", timestamp="T1"), rec("b", timestamp="T2"), rec("z", timestamp="T3")]
    out, _ = ltu.union_lines(canon, stray)
    assert len(out) == 3
    uuids = [json.loads(line)["uuid"] for line in out]
    assert uuids == ["a", "b", "z"]
    assert uuids.count("a") == 1 and uuids.count("b") == 1


def test_uuidless_records_dedupe_on_raw_bytes_not_collapsed_by_multiplicity():
    """The real store repeats byte-identical `custom-title` / `atis-latch` lines with no
    `uuid`. Keying them on raw bytes must keep max(canon_count, stray_count), never 1."""
    title = rec(None, type="custom-title", customTitle="LW")
    canon = [title, title, rec("a")]
    stray = [title, title, title, title, rec("a")]
    out, appended = ltu.union_lines(canon, stray)
    assert out.count(title) == 4, "stray held 4 copies; a set-based union would collapse to 1"
    assert appended == [title, title]
    assert out[:3] == canon[:3]


def test_a_record_is_never_rewritten_byte_for_byte():
    """Whitespace-odd but valid JSON must survive verbatim - we never re-serialize."""
    odd = '{ "uuid" : "a" ,  "type":"assistant" }\n'
    out, _ = ltu.union_lines([odd], [odd, rec("b")])
    assert out[0] == odd


def test_unparseable_line_is_kept_and_keyed_on_its_bytes():
    junk = "not json at all\n"
    out, appended = ltu.union_lines([junk], [junk, rec("b")])
    assert out == [junk, rec("b")]
    assert appended == [rec("b")]


def test_blank_lines_are_dropped_at_the_read_boundary(tmp_path):
    """union_lines never drops a line it was handed; blank-line filtering is read_lines'
    job, so that is where it is asserted."""
    p = tmp_path / "u.jsonl"
    p.write_text(rec("a") + "\n" + rec("b"), encoding="utf-8", newline="")
    assert ltu.read_lines(p) == [rec("a"), rec("b")]


def test_read_lines_preserves_crlf_bytes_verbatim(tmp_path):
    """Universal-newline translation would silently rewrite a CRLF record on the way
    back out. Records are copied, never re-serialized, so the bytes must survive."""
    p = tmp_path / "u.jsonl"
    raw = '{"uuid":"a","type":"assistant"}\r\n{"uuid":"b","type":"assistant"}\r\n'
    p.write_bytes(raw.encode("utf-8"))
    lines = ltu.read_lines(p)
    assert lines == ['{"uuid":"a","type":"assistant"}\r\n', '{"uuid":"b","type":"assistant"}\r\n']
    assert ltu.record_key(lines[0]) == ("u", "a")


# --------------------------------------------------------------------------- the live-session guard

def test_refuses_when_the_canonical_dir_has_a_file_modified_inside_the_window(tmp_path):
    """MUTATION-PROVED arm. This session's own transcript lives in the canonical dir."""
    cdir, sdir = write_store(tmp_path, {"u.jsonl": [rec("a")]}, {"u.jsonl": [rec("a"), rec("b")]})
    age_out(cdir)
    age_out(sdir)
    live = cdir / "3ac8447f-live-session.jsonl"
    live.write_text(rec("live"), encoding="utf-8")
    with pytest.raises(ltu.Refusal) as ei:
        ltu.assert_safe(cdir, sdir, now=time.time())
    assert "3ac8447f-live-session.jsonl" in str(ei.value)
    assert "modified" in str(ei.value).lower()


def test_refuses_when_the_running_sessions_own_transcript_is_in_the_canonical_dir(tmp_path):
    """MUTATION-PROVED arm, and the reason this check exists at all.

    The mtime window alone is NOT sufficient: measured 2026-09-20 on Legion, the live
    session's own transcript had last been flushed 353.8s ago - Claude Code batches
    flushes, so a genuinely live session sails straight through a 120s window. The
    session id is a deterministic signal where the mtime is a racy one.
    """
    cdir, sdir = write_store(tmp_path, {"u.jsonl": [rec("a")]}, {"u.jsonl": [rec("a"), rec("b")]})
    (cdir / "live-sid.jsonl").write_text(rec("x"), encoding="utf-8", newline="")
    age_out(cdir)  # every mtime pushed far outside the window
    age_out(sdir)
    with pytest.raises(ltu.Refusal) as ei:
        ltu.assert_safe(cdir, sdir, now=time.time(), self_session_id="live-sid")
    assert "live-sid" in str(ei.value)
    assert "running session" in str(ei.value).lower()


def test_no_refusal_when_the_running_sessions_transcript_is_under_a_different_key(tmp_path):
    cdir, sdir = write_store(tmp_path, {"u.jsonl": [rec("a")]}, {"u.jsonl": [rec("a"), rec("b")]})
    age_out(cdir)
    age_out(sdir)
    ltu.assert_safe(cdir, sdir, now=time.time(), self_session_id="some-other-session")


def test_allows_when_every_file_is_older_than_the_window(tmp_path):
    cdir, sdir = write_store(tmp_path, {"u.jsonl": [rec("a")]}, {"u.jsonl": [rec("a"), rec("b")]})
    age_out(cdir)
    age_out(sdir)
    ltu.assert_safe(cdir, sdir, now=time.time())  # must not raise


def test_a_file_just_outside_the_window_is_allowed_and_just_inside_is_not(tmp_path):
    cdir, sdir = write_store(tmp_path, {"u.jsonl": [rec("a")]}, {"u.jsonl": [rec("a")]})
    age_out(cdir)
    age_out(sdir)
    target = cdir / "u.jsonl"
    now = time.time()
    os.utime(target, (now - (ltu.LIVE_WINDOW_S + 5), now - (ltu.LIVE_WINDOW_S + 5)))
    ltu.assert_safe(cdir, sdir, now=now)
    os.utime(target, (now - (ltu.LIVE_WINDOW_S - 5), now - (ltu.LIVE_WINDOW_S - 5)))
    with pytest.raises(ltu.Refusal):
        ltu.assert_safe(cdir, sdir, now=now)


def test_refuses_when_a_target_file_is_locked_for_writing(tmp_path):
    cdir, sdir = write_store(tmp_path, {"u.jsonl": [rec("a")]}, {"u.jsonl": [rec("a"), rec("b")]})
    age_out(cdir)
    age_out(sdir)

    def always_locked(path: Path) -> bool:
        return path.name == "u.jsonl"

    with pytest.raises(ltu.Refusal) as ei:
        ltu.assert_safe(cdir, sdir, now=time.time(), lock_probe=always_locked)
    assert "u.jsonl" in str(ei.value)
    assert "lock" in str(ei.value).lower() or "open for writing" in str(ei.value).lower()


def test_dry_run_still_reports_the_plan_under_a_live_session_but_warns(tmp_path, capsys):
    """A dry run writes nothing, so it cannot lose a byte - it must stay usable as a
    preview and say plainly that an apply would refuse. The apply path is NOT relaxed."""
    cdir, sdir = write_store(tmp_path, {"u.jsonl": [rec("a")]}, {"u.jsonl": [rec("a"), rec("b")]})
    (cdir / "live-sid.jsonl").write_text(rec("x"), encoding="utf-8", newline="")
    before = (cdir / "u.jsonl").read_bytes()
    code = ltu.main(["--canon-dir", str(cdir), "--stray-dir", str(sdir),
                     "--backup-dir", str(tmp_path / "bak"), "--session-id", "live-sid"])
    out = capsys.readouterr().out
    assert code == 0
    assert "WOULD REFUSE" in out
    assert "UNION u.jsonl" in out
    assert (cdir / "u.jsonl").read_bytes() == before


def test_cli_apply_exits_3_when_the_running_sessions_transcript_is_present(tmp_path, capsys):
    cdir, sdir = write_store(tmp_path, {"u.jsonl": [rec("a")]}, {"u.jsonl": [rec("a"), rec("b")]})
    (cdir / "live-sid.jsonl").write_text(rec("x"), encoding="utf-8", newline="")
    age_out(cdir)
    age_out(sdir)
    before = (cdir / "u.jsonl").read_bytes()
    code = ltu.main(["--apply", "--canon-dir", str(cdir), "--stray-dir", str(sdir),
                     "--backup-dir", str(tmp_path / "bak"), "--session-id", "live-sid"])
    assert code == 3
    assert "REFUSE" in capsys.readouterr().out
    assert (cdir / "u.jsonl").read_bytes() == before, "a refused apply must not touch a byte"


def test_cli_exits_3_on_a_refusal(tmp_path, capsys):
    cdir, sdir = write_store(tmp_path, {"u.jsonl": [rec("a")]}, {"u.jsonl": [rec("a"), rec("b")]})
    age_out(sdir)  # canonical dir keeps a fresh mtime -> refusal
    code = ltu.main(["--apply", "--canon-dir", str(cdir), "--stray-dir", str(sdir),
                     "--backup-dir", str(tmp_path / "bak")])
    assert code == 3
    assert "REFUSE" in capsys.readouterr().out


# --------------------------------------------------------------------------- planning and apply

def test_plan_classifies_union_copy_and_noop(tmp_path):
    cdir, sdir = write_store(
        tmp_path,
        {"u1.jsonl": [rec("a")], "u2.jsonl": [rec("x")]},
        {"u1.jsonl": [rec("a"), rec("b")], "u2.jsonl": [rec("x")],
         "u3.desktop-released.json": ['{"v":1}\n']},
    )
    by_name = {p.name: p for p in ltu.plan(cdir, sdir)}
    assert by_name["u1.jsonl"].action == "union"
    assert by_name["u1.jsonl"].appended == 1
    assert by_name["u2.jsonl"].action == "noop"
    assert by_name["u3.desktop-released.json"].action == "copy"


def test_dry_run_changes_nothing(tmp_path):
    cdir, sdir = write_store(tmp_path, {"u.jsonl": [rec("a")]}, {"u.jsonl": [rec("a"), rec("b")]})
    age_out(cdir)
    age_out(sdir)
    before = (cdir / "u.jsonl").read_bytes()
    bak = tmp_path / "bak"
    code = ltu.main(["--canon-dir", str(cdir), "--stray-dir", str(sdir), "--backup-dir", str(bak)])
    assert code == 0
    assert (cdir / "u.jsonl").read_bytes() == before
    assert not bak.exists()


def test_apply_unions_in_place_and_writes_the_backup_first(tmp_path):
    cdir, sdir = write_store(tmp_path, {"u.jsonl": [rec("a")]}, {"u.jsonl": [rec("a"), rec("b")]})
    age_out(cdir)
    age_out(sdir)
    before = (cdir / "u.jsonl").read_bytes()
    bak = tmp_path / "bak"
    code = ltu.main(["--apply", "--canon-dir", str(cdir), "--stray-dir", str(sdir), "--backup-dir", str(bak)])
    assert code == 0
    assert (bak / "u.canon.bak").read_bytes() == before, "backup must hold the PRE-union bytes"
    assert (cdir / "u.jsonl").read_text(encoding="utf-8") == rec("a") + rec("b")


def test_backup_exists_before_the_replace_even_if_the_replace_fails(tmp_path, monkeypatch):
    cdir, sdir = write_store(tmp_path, {"u.jsonl": [rec("a")]}, {"u.jsonl": [rec("a"), rec("b")]})
    age_out(cdir)
    age_out(sdir)
    bak = tmp_path / "bak"
    real_replace = os.replace

    def boom(src, dst):
        if str(dst).endswith("u.jsonl"):
            raise OSError("simulated replace failure")
        return real_replace(src, dst)

    monkeypatch.setattr(ltu.os, "replace", boom)
    with pytest.raises(OSError):
        ltu.apply_plan(ltu.plan(cdir, sdir), bak)
    assert (bak / "u.canon.bak").read_bytes() == rec("a").encode("utf-8")


def test_apply_leaves_the_stray_directory_completely_untouched(tmp_path):
    cdir, sdir = write_store(
        tmp_path,
        {"u.jsonl": [rec("a")]},
        {"u.jsonl": [rec("a"), rec("b")], "s.desktop-released.json": ['{"v":1}\n']},
    )
    age_out(cdir)
    age_out(sdir)
    snapshot = {p.name: p.read_bytes() for p in sdir.iterdir()}
    ltu.main(["--apply", "--canon-dir", str(cdir), "--stray-dir", str(sdir), "--backup-dir", str(tmp_path / "bak")])
    assert {p.name: p.read_bytes() for p in sdir.iterdir()} == snapshot
    assert sdir.is_dir()


def test_sidecar_with_no_counterpart_is_copied_into_the_canonical_key(tmp_path):
    cdir, sdir = write_store(tmp_path, {}, {"d3.desktop-released.json": ['{"v":1,"reason":"delete"}\n']})
    age_out(sdir)
    ltu.main(["--apply", "--canon-dir", str(cdir), "--stray-dir", str(sdir), "--backup-dir", str(tmp_path / "bak")])
    assert (cdir / "d3.desktop-released.json").read_text(encoding="utf-8") == '{"v":1,"reason":"delete"}\n'


def test_apply_is_idempotent(tmp_path):
    cdir, sdir = write_store(tmp_path, {"u.jsonl": [rec("a")]}, {"u.jsonl": [rec("a"), rec("b")]})
    age_out(cdir)
    age_out(sdir)
    bak = tmp_path / "bak"
    ltu.main(["--apply", "--canon-dir", str(cdir), "--stray-dir", str(sdir), "--backup-dir", str(bak)])
    first = (cdir / "u.jsonl").read_bytes()
    age_out(cdir)
    ltu.main(["--apply", "--canon-dir", str(cdir), "--stray-dir", str(sdir), "--backup-dir", str(bak)])
    assert (cdir / "u.jsonl").read_bytes() == first


def test_apply_writes_the_verification_block_and_asserts_no_canonical_line_was_lost(tmp_path, capsys):
    cdir, sdir = write_store(tmp_path, {"u.jsonl": [rec("a"), rec("c")]}, {"u.jsonl": [rec("a"), rec("b")]})
    age_out(cdir)
    age_out(sdir)
    ltu.main(["--apply", "--canon-dir", str(cdir), "--stray-dir", str(sdir), "--backup-dir", str(tmp_path / "bak")])
    out = capsys.readouterr().out
    assert "VERIFICATION" in out
    assert "lines 2 -> 3" in out
    assert "all pre-union canonical lines present: yes" in out
    assert rec("c") in (cdir / "u.jsonl").read_text(encoding="utf-8")


def test_verify_preserved_detects_a_dropped_canonical_line():
    """Guards the verification block itself - it must be able to FAIL."""
    assert ltu.verify_preserved([rec("a"), rec("b")], [rec("a"), rec("b")]) is True
    assert ltu.verify_preserved([rec("a"), rec("b")], [rec("a")]) is False
    assert ltu.verify_preserved([rec("a"), rec("a")], [rec("a")]) is False
