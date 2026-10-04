"""Isolated verification copy of live state (ingest P2-6).

Arms: refusal when source and target are the same (or the source sits inside
the target); a count or content mismatch fails the proof; only a MARKED verify
copy is ever cleared; the dashboards' --runtime-root moves their reads onto the
copy.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

import lw_verify_snapshot as vs  # noqa: E402

from tools import lw_monitor, lw_rundash  # noqa: E402


def _live(tmp_path) -> Path:
    src = tmp_path / "runtime"
    src.mkdir()
    (src / "pipeline_state.json").write_text('{"images": {}}', encoding="utf-8")
    (src / "job_health.json").write_text('{"jobs": []}', encoding="utf-8")
    (src / "notes.txt").write_text("not copied", encoding="utf-8")
    return src


def test_a_snapshot_is_proven_and_leaves_the_source_alone(tmp_path):
    src = _live(tmp_path)
    before = {p.name: p.read_bytes() for p in src.iterdir()}
    res = vs.snapshot(src, tmp_path / "verify")
    assert res["proven"] and res["files"] == 2
    assert {p.name: p.read_bytes() for p in src.iterdir() if p.is_file()} == before
    assert not (tmp_path / "verify" / "notes.txt").exists()


def test_same_source_and_target_is_refused(tmp_path):
    src = _live(tmp_path)
    with pytest.raises(vs.SnapshotRefused, match="same"):
        vs.snapshot(src, src)
    with pytest.raises(vs.SnapshotRefused, match="inside"):
        vs.snapshot(src, tmp_path)


def test_a_count_mismatch_fails_the_proof(tmp_path):
    src = _live(tmp_path)
    tgt = tmp_path / "verify"
    vs.snapshot(src, tgt)
    (tgt / "extra.json").write_text("{}", encoding="utf-8")
    assert any("count" in p for p in vs.prove(vs._files(src), tgt))


def test_a_content_mismatch_fails_the_proof(tmp_path):
    src = _live(tmp_path)
    tgt = tmp_path / "verify"
    vs.snapshot(src, tgt)
    (tgt / "job_health.json").write_text('{"jobs": [1]}', encoding="utf-8")
    assert any("content" in p for p in vs.prove(vs._files(src), tgt))


def test_an_unmarked_target_with_files_is_never_cleared(tmp_path):
    src = _live(tmp_path)
    tgt = tmp_path / "someone-elses"
    tgt.mkdir()
    (tgt / "precious.json").write_text("{}", encoding="utf-8")
    with pytest.raises(vs.SnapshotRefused, match="marker"):
        vs.snapshot(src, tgt)
    assert (tgt / "precious.json").exists()


def test_a_marked_copy_is_refreshed(tmp_path):
    src = _live(tmp_path)
    tgt = tmp_path / "verify"
    vs.snapshot(src, tgt)
    (src / "job_health.json").unlink()
    res = vs.snapshot(src, tgt)
    assert res["proven"] and not (tgt / "job_health.json").exists()


def test_cli_exit_codes(tmp_path):
    src = _live(tmp_path)
    assert vs.main(["--source", str(src), "--target", str(tmp_path / "v")]) == 0
    assert vs.main(["--source", str(src), "--target", str(src)]) == 2


def test_rundash_runtime_root_moves_every_runtime_read(tmp_path):
    args = argparse.Namespace(control_dir=None, manifest=None, session_dir=None,
                              runtime_root=str(tmp_path))
    kw = lw_rundash.server_kwargs(args)
    for key in ("manifest_path", "mirror_path", "pipeline_state_path", "job_health_path"):
        assert Path(kw[key]).parent == tmp_path, key
    live = lw_rundash.server_kwargs(argparse.Namespace(
        control_dir=None, manifest=None, session_dir=None, runtime_root=None))
    assert live["manifest_path"] == lw_rundash.MANIFEST_PATH


def test_monitor_runtime_root_moves_the_state_read(tmp_path):
    a = argparse.Namespace(state_file=None, runtime_root=str(tmp_path))
    assert lw_monitor.resolve_state_path(a) == tmp_path / "pipeline_state.json"
    b = argparse.Namespace(state_file=str(tmp_path / "x.json"), runtime_root=str(tmp_path))
    assert lw_monitor.resolve_state_path(b) == tmp_path / "x.json"
    c = argparse.Namespace(state_file=None, runtime_root=None)
    assert lw_monitor.resolve_state_path(c) == lw_monitor.STATE_PATH
