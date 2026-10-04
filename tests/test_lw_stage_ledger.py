"""Stage ledger: which pipeline step touched what it should not (directive P1-1).

The ledger wraps every stage of the chain (first -> clean -> final -> last) and
records, per watched region, which stage changed it and whether that stage
ASSERTED the change. Operator-approved regions are LOCKS: a later stage that
changes a lock without asserting it blocks the end-review pass.

Hermetic: tiny synthetic PNGs in tmp_path, laid out the way lw_pipeline leaves
an 8.End Review set (every stage `_initial` plus `_lastdone`).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

import lw_pipeline  # noqa: E402
import lw_stage_ledger as L  # noqa: E402

W, H = 256, 144


def _art(seed=0):
    rng = np.random.default_rng(seed)
    return rng.integers(0, 256, size=(H, W, 3), dtype=np.uint8)


def _save(path: Path, arr):
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(arr).save(path)


def _review_set(tmp_path, frames, params=None, slug="ahri"):
    """frames: dict milestone -> array. params: stage -> SAVE_WORKING params."""
    review = tmp_path / "images" / "8.End Review" / slug
    for name, arr in frames.items():
        _save(review / f"{slug}_{name}.png", arr)
    man = {"schema": 1, "slug": slug, "transitions": []}
    for stage, p in (params or {}).items():
        man["transitions"].append({
            "op": "SAVE_WORKING", "tool": "test", "params": p,
            "dst": f"{lw_pipeline.SCRATCH_DIR[stage]}/{slug}/{slug}_{stage}working_01.png"})
    (review / "manifest.json").write_text(json.dumps(man), encoding="utf-8")
    return tmp_path / "images"


def _chain(a, clean=None, final=None, last=None):
    clean = a if clean is None else clean
    final = clean if final is None else final
    last = final if last is None else last
    return {"firstinitial": a, "cleaninitial": a, "finalinitial": clean,
            "lastinitial": final, "lastdone": last}


def _locks(tmp_path, slug, locks):
    d = tmp_path / "locks"
    d.mkdir(exist_ok=True)
    (d / f"{slug}.json").write_text(json.dumps({"locks": locks}), encoding="utf-8")
    return d


# ---------------------------------------------------------------- coverage
def test_every_pipeline_stage_has_ledger_coverage():
    """A stage added to lw_pipeline.STAGES without ledger coverage fails here."""
    assert set(L.STAGE_COVERAGE) == set(lw_pipeline.STAGES)


def test_stage_list_is_read_from_the_pipeline_not_restated():
    assert L.stages() == list(lw_pipeline.STAGES)


def test_unwatched_stage_is_reported_and_outranks_nothing_happened(tmp_path, monkeypatch):
    a = _art()
    root = _review_set(tmp_path, _chain(a))
    cov = dict(L.STAGE_COVERAGE)
    cov.pop("final")
    monkeypatch.setattr(L, "STAGE_COVERAGE", cov)
    led = L.build_ledger(root, "ahri", locks_dir=tmp_path / "locks")
    st = {s["stage"]: s for s in led["stages"]}
    assert st["final"]["status"] == "unwatched"
    assert led["summary"]["unwatched"] == ["final"]


def test_unwatched_stage_with_locks_blocks_end_review(tmp_path, monkeypatch):
    a = _art()
    root = _review_set(tmp_path, _chain(a))
    locks = _locks(tmp_path, "ahri", [{"name": "face", "box": [10, 10, 40, 40],
                                       "after_stage": "first"}])
    cov = dict(L.STAGE_COVERAGE)
    cov.pop("last")
    monkeypatch.setattr(L, "STAGE_COVERAGE", cov)
    ok, reasons = L.end_review_check(L.build_ledger(root, "ahri", locks_dir=locks))
    assert not ok and any("unwatched" in r for r in reasons)


# ---------------------------------------------------------------- outside the edit
def test_stage_editing_outside_its_declared_region_is_flagged(tmp_path):
    a = _art()
    clean = a.copy()
    clean[100:120, 100:140] = 0          # inside the declared box: asserted
    clean[5:15, 200:230] = 255           # OUTSIDE it: unexplained
    root = _review_set(tmp_path, _chain(a, clean=clean),
                       params={"clean": {"mask_bbox": [96, 96, 144, 124]}})
    led = L.build_ledger(root, "ahri", locks_dir=tmp_path / "locks")
    st = {s["stage"]: s for s in led["stages"]}
    out = next(r for r in st["clean"]["regions"] if r["region"] == "outside_edit")
    assert out["changed"] and out["asserted_by"] is None
    assert led["summary"]["unexplained"] == [{"stage": "clean", "region": "outside_edit"}]


def test_a_stage_that_stays_inside_its_box_is_clean(tmp_path):
    a = _art()
    clean = a.copy()
    clean[100:120, 100:140] = 0
    root = _review_set(tmp_path, _chain(a, clean=clean),
                       params={"clean": {"mask_bbox": [96, 96, 144, 124]}})
    led = L.build_ledger(root, "ahri", locks_dir=tmp_path / "locks")
    assert led["summary"]["unexplained"] == []


# ---------------------------------------------------------------- locks
def test_lock_changed_by_a_non_asserting_stage_blocks(tmp_path):
    a = _art()
    final = a.copy()
    final[20:30, 20:30] = 0              # the approved face moved in `final`
    root = _review_set(tmp_path, _chain(a, final=final),
                       params={"final": {"mask_bbox": [180, 100, 240, 140]}})
    locks = _locks(tmp_path, "ahri", [{"name": "face", "box": [16, 16, 48, 48],
                                       "after_stage": "clean"}])
    led = L.build_ledger(root, "ahri", locks_dir=locks)
    ok, reasons = L.end_review_check(led)
    assert not ok
    assert any("face" in r and "final" in r for r in reasons)


def test_lock_changed_by_the_stage_that_asserts_it_passes(tmp_path):
    a = _art()
    final = a.copy()
    final[20:30, 20:30] = 0
    root = _review_set(tmp_path, _chain(a, final=final),
                       params={"final": {"mask_bbox": [16, 16, 48, 48]}})
    locks = _locks(tmp_path, "ahri", [{"name": "face", "box": [16, 16, 48, 48],
                                       "after_stage": "clean"}])
    led = L.build_ledger(root, "ahri", locks_dir=locks)
    st = {s["stage"]: s for s in led["stages"]}
    face = next(r for r in st["final"]["regions"] if r["region"] == "lock:face")
    assert face["changed"] and face["asserted_by"] == "final"
    assert L.end_review_check(led)[0]


def test_lock_is_only_in_force_after_its_stage(tmp_path):
    a = _art()
    clean = a.copy()
    clean[20:30, 20:30] = 0              # clean changed it BEFORE it was approved
    root = _review_set(tmp_path, _chain(a, clean=clean),
                       params={"clean": {"mask_bbox": [180, 100, 240, 140]}})
    locks = _locks(tmp_path, "ahri", [{"name": "face", "box": [16, 16, 48, 48],
                                       "after_stage": "clean"}])
    led = L.build_ledger(root, "ahri", locks_dir=locks)
    assert L.end_review_check(led)[0]


def test_empty_lock_set_still_writes_a_note_per_stage(tmp_path):
    a = _art()
    root = _review_set(tmp_path, _chain(a))
    led = L.build_ledger(root, "ahri", locks_dir=tmp_path / "locks")
    for s in led["stages"]:
        assert any("no locks" in n for n in s["notes"]), s


def test_identity_chain_reports_nothing_changed(tmp_path):
    a = _art()
    root = _review_set(tmp_path, _chain(a))
    led = L.build_ledger(root, "ahri", locks_dir=tmp_path / "locks")
    for s in led["stages"]:
        if s["stage"] == "first":
            continue
        assert all(not r["changed"] for r in s["regions"]), s


def test_first_stage_at_source_size_compares_at_common_scale(tmp_path):
    src = np.asarray(Image.fromarray(_art()).resize((W // 2, H // 2), Image.LANCZOS))
    a = _art()
    frames = _chain(a)
    frames["firstinitial"] = src
    root = _review_set(tmp_path, frames)
    led = L.build_ledger(root, "ahri", locks_dir=tmp_path / "locks")
    st = {s["stage"]: s for s in led["stages"]}
    assert st["first"]["status"] == "watched"
    assert st["first"]["asserts"] == "whole_frame"


def test_missing_milestone_reads_absent_not_clean(tmp_path):
    a = _art()
    frames = _chain(a)
    frames.pop("finalinitial")
    root = _review_set(tmp_path, frames)
    led = L.build_ledger(root, "ahri", locks_dir=tmp_path / "locks")
    st = {s["stage"]: s for s in led["stages"]}
    assert st["clean"]["status"] == "absent"


def test_absent_stage_under_a_lock_blocks(tmp_path):
    a = _art()
    frames = _chain(a)
    frames.pop("lastinitial")
    root = _review_set(tmp_path, frames)
    locks = _locks(tmp_path, "ahri", [{"name": "face", "box": [16, 16, 48, 48],
                                       "after_stage": "first"}])
    ok, reasons = L.end_review_check(L.build_ledger(root, "ahri", locks_dir=locks))
    assert not ok


def test_write_ledger_is_atomic_json(tmp_path):
    a = _art()
    root = _review_set(tmp_path, _chain(a))
    out_dir = tmp_path / "ledger"
    path = L.write_ledger(L.build_ledger(root, "ahri", locks_dir=tmp_path / "locks"), out_dir)
    data = json.loads(Path(path).read_text(encoding="ascii"))
    assert data["slug"] == "ahri" and len(data["stages"]) == len(lw_pipeline.STAGES)


def test_unreadable_lock_file_blocks_rather_than_passing(tmp_path):
    a = _art()
    root = _review_set(tmp_path, _chain(a))
    d = tmp_path / "locks"
    d.mkdir()
    (d / "ahri.json").write_text("{not json", encoding="utf-8")
    ok, reasons = L.end_review_check(L.build_ledger(root, "ahri", locks_dir=d))
    assert not ok and any("lock" in r for r in reasons)


@pytest.mark.parametrize("box", [[0, 0, 8, 8], [248, 136, 256, 144]])
def test_lock_at_frame_corner_maps_inside_common_scale(box):
    m = L.region_mask_common((W, H), [box])
    assert m.any()


# ---------------------------------------------------------------- end review wiring
def test_finalize_refuses_when_a_lock_changed_unasserted(tmp_path):
    a = _art()
    final = a.copy()
    final[20:30, 20:30] = 0
    root = _review_set(tmp_path, _chain(a, final=final),
                       params={"final": {"mask_bbox": [180, 100, 240, 140]}})
    _locks_dir = tmp_path / "ops" / "runtime" / "locks"
    _locks_dir.mkdir(parents=True)
    (_locks_dir / "ahri.json").write_text(json.dumps({"locks": [
        {"name": "face", "box": [16, 16, 48, 48], "after_stage": "clean"}]}),
        encoding="utf-8")
    for name in lw_pipeline.STAGE_FOLDERS if hasattr(lw_pipeline, "STAGE_FOLDERS") else ():
        (root / name).mkdir(exist_ok=True)
    rc = lw_pipeline.main(["--root", str(root), "finalize", "ahri"])
    assert rc == 3
    led = json.loads((tmp_path / "ops" / "runtime" / "stage_ledger" / "ahri.json")
                     .read_text(encoding="ascii"))
    assert led["summary"]["unexplained"]
    assert not (root / "9.Image Backup" / "ahri" / "ahri_lastdone.png").exists()


def test_finalize_without_locks_writes_the_ledger_and_passes(tmp_path):
    a = _art()
    root = _review_set(tmp_path, _chain(a))
    rc = lw_pipeline.main(["--root", str(root), "finalize", "ahri"])
    assert rc == 0
    assert (tmp_path / "ops" / "runtime" / "stage_ledger" / "ahri.json").is_file()
