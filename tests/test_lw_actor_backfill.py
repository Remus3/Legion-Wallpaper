"""Backfill of the 2026-08-22 mislabelled approvals (LEDGER 269).

The append-only PIPELINE_LOG is never rewritten: one CORRECT_ACTOR line is
appended per corrected slug. Manifests get the true actor plus a
`corrected_from` record. A second run is a no-op.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import lw_actor_backfill as bf  # noqa: E402


def _t(ts, op, actor="operator", sha="ab" * 32):
    return {"ts": ts, "op": op, "actor": actor, "tool": None,
            "sha256_in": sha, "sha256_out": sha}


def _make(root: Path, slug: str, transitions, crlf=True) -> Path:
    d = root / "images" / "4.Cleaning Done" / slug
    d.mkdir(parents=True)
    text = json.dumps({"slug": slug, "transitions": transitions}, indent=2) + "\n"
    if crlf:
        text = text.replace("\n", "\r\n")
    (d / "manifest.json").write_bytes(text.encode("utf-8"))
    return d / "manifest.json"


def _load(p: Path) -> dict:
    return json.loads(p.read_bytes())


def test_dispose_batch_is_corrected_and_others_are_left(tmp_path):
    m1 = _make(tmp_path, "a", [
        _t("2026-08-17T06:00:00Z", "SUBMIT"),
        _t("2026-08-17T06:00:01Z", "APPROVE_FIRST"),
        _t("2026-08-22T12:04:03Z", "SUBMIT"),
        _t("2026-08-22T12:04:04Z", "APPROVE_CLEAN"),
    ])
    m2 = _make(tmp_path, "b", [
        _t("2026-08-22T19:08:19Z", "SUBMIT"),
        _t("2026-08-22T19:08:19Z", "APPROVE_CLEAN"),
    ])
    m3 = _make(tmp_path, "c", [_t("2026-09-01T14:13:00Z", "APPROVE_CLEAN")])
    log = tmp_path / "PIPELINE_LOG.md"
    log.write_bytes(b"# header\n\nold line\n")

    rows = bf.run(tmp_path / "images", log, apply=True, now="2026-10-04T00:00:00Z")
    assert sorted(r["slug"] for r in rows) == ["a", "b"]

    a = _load(m1)["transitions"]
    assert [t["actor"] for t in a] == [
        "operator", "operator", "tool:lw_clean_dispose", "tool:auto-approve"]
    assert a[3]["corrected_from"]["actor"] == "operator"
    assert a[3]["corrected_from"]["ref"] == bf.REF
    assert "corrected_from" not in a[1]
    b = _load(m2)["transitions"]
    # 19:08 batch: approve flag recorded in docs; the submit driver was not.
    assert [t["actor"] for t in b] == ["unattributed", "tool:auto-approve"]
    assert _load(m3)["transitions"][0]["actor"] == "operator"
    assert b"\r\n" in m1.read_bytes()  # line endings preserved

    lines = log.read_text(encoding="ascii").splitlines()
    assert lines[:3] == ["# header", "", "old line"]  # history untouched
    new = lines[3:]
    assert len(new) == 2
    for ln in new:
        f = ln.split(" | ")
        assert len(f) == 8
        assert f[2] == "CORRECT_ACTOR"
        assert f[4] == "actor=tool:lw_actor_backfill"
        assert f[5] == "sha12=" + "ab" * 6
    assert "APPROVE_CLEAN@2026-08-22T12:04:04Z operator->tool:auto-approve" in new[0]


def test_second_run_is_a_noop(tmp_path):
    _make(tmp_path, "a", [_t("2026-08-22T12:04:04Z", "APPROVE_CLEAN")])
    log = tmp_path / "PIPELINE_LOG.md"
    log.write_bytes(b"x\n")
    assert len(bf.run(tmp_path / "images", log, apply=True)) == 1
    before = log.read_bytes()
    assert bf.run(tmp_path / "images", log, apply=True) == []
    assert log.read_bytes() == before


def test_dry_run_writes_nothing(tmp_path):
    m = _make(tmp_path, "a", [_t("2026-08-22T12:04:04Z", "APPROVE_CLEAN")])
    log = tmp_path / "PIPELINE_LOG.md"
    log.write_bytes(b"x\n")
    before = m.read_bytes()
    assert len(bf.run(tmp_path / "images", log, apply=False)) == 1
    assert m.read_bytes() == before
    assert log.read_bytes() == b"x\n"
