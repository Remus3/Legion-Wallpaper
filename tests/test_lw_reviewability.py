"""Reviewability pre-check for vision-reviewer inputs (directive P1-7).

A model judging pictures is reliable about shape and absence and unreliable
about faint, small or contact-level properties. So every crop sent for a
RESIDUE judgement must be 1:1 (never downscaled), must hold its ROI fully
inside with a margin, and must clear a brightness / clipping / contrast floor.
A crop that fails is re-cut, or the item is marked "not judgeable from pixels".

Synthetic crops only; no corpus bytes.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

import lw_reviewability as R  # noqa: E402

FRAME = (2560, 1440)
ROI = (1000, 1300, 1550, 1370)          # a credit line, 550 x 70


def _mid(h=200, w=700, level=120.0, seed=0):
    rng = np.random.default_rng(seed)
    return np.clip(level + rng.normal(0, 20, size=(h, w)), 0, 255)


def test_one_to_one_crop_with_margin_is_judgeable():
    crop = R.recut(FRAME, ROI)
    rec = R.check_crop(FRAME, crop, ROI, out_size=(crop[2] - crop[0], crop[3] - crop[1]),
                       gray=_mid())
    assert rec["judgeable"] is True, rec
    assert rec["scale"] == 1.0 and rec["reasons"] == []


def test_downscaled_crop_is_rejected():
    crop = R.recut(FRAME, ROI)
    w, h = crop[2] - crop[0], crop[3] - crop[1]
    rec = R.check_crop(FRAME, crop, ROI, out_size=(w // 2, h // 2), gray=_mid())
    assert rec["judgeable"] is False
    assert "downscaled" in rec["reasons"][0]
    assert rec["action"] == "recut"


def test_roi_touching_the_crop_edge_is_rejected():
    crop = (ROI[0], ROI[1] - 40, ROI[2] + 40, ROI[3] + 40)   # left edge = ROI edge
    rec = R.check_crop(FRAME, crop, ROI, out_size=(crop[2] - crop[0], crop[3] - crop[1]),
                       gray=_mid())
    assert rec["judgeable"] is False
    assert any("edge" in r for r in rec["reasons"])
    assert rec["action"] == "recut"


def test_roi_on_the_frame_edge_is_recorded_not_recut():
    roi = (2200, 1380, 2560, 1440)                            # bottom-right corner
    crop = R.recut(FRAME, roi)
    rec = R.check_crop(FRAME, crop, roi, out_size=(crop[2] - crop[0], crop[3] - crop[1]),
                       gray=_mid())
    assert rec["roi_touches_frame_edge"] is True
    assert rec["judgeable"] is True       # nothing a re-cut could add; recorded


def test_dim_crop_is_flagged_not_judgeable_from_pixels():
    crop = R.recut(FRAME, ROI)
    rec = R.check_crop(FRAME, crop, ROI, out_size=(crop[2] - crop[0], crop[3] - crop[1]),
                       gray=_mid(level=8.0))
    assert rec["judgeable"] is False
    assert any("dim" in r for r in rec["reasons"])
    assert rec["action"] == "not_judgeable_from_pixels"


def test_clipped_crop_is_flagged():
    g = _mid()
    g[:, : g.shape[1] // 2] = 255.0
    crop = R.recut(FRAME, ROI)
    rec = R.check_crop(FRAME, crop, ROI, out_size=(crop[2] - crop[0], crop[3] - crop[1]),
                       gray=g)
    assert any("clipped" in r for r in rec["reasons"])


def test_recut_keeps_one_to_one_and_a_margin():
    crop = R.recut(FRAME, ROI)
    assert crop[0] <= ROI[0] - R.MIN_EDGE_MARGIN_PX
    assert crop[2] >= ROI[2] + R.MIN_EDGE_MARGIN_PX
    assert 0 <= crop[0] and crop[2] <= FRAME[0] and crop[3] <= FRAME[1]


def test_plan_crops_tiles_a_wide_roi_at_one_to_one_up_to_the_cap():
    wide = (100, 1300, 2400, 1360)
    plan = R.plan_crops(FRAME, wide, max_w=800)
    assert 1 < len(plan["crops"]) <= R.MAX_CROPS_PER_ITEM
    assert plan["action"] == "judge"
    for c in plan["crops"]:
        assert c[2] - c[0] <= 800 + 2 * R.MIN_EDGE_MARGIN_PX + 2 * R.PAD_PX


def test_plan_crops_over_the_cap_is_not_judgeable_from_pixels():
    huge = (0, 0, 2560, 1440)
    plan = R.plan_crops(FRAME, huge, max_w=400)
    assert plan["action"] == "not_judgeable_from_pixels"
    assert plan["crops"] == []


def test_record_is_ascii_json_serialisable():
    import json
    crop = R.recut(FRAME, ROI)
    rec = R.check_crop(FRAME, crop, ROI, out_size=(crop[2] - crop[0], crop[3] - crop[1]),
                       gray=_mid())
    json.dumps(rec).encode("ascii")


def test_reviewer_prompt_carries_the_doctrine():
    """The rules live in the reviewer prompt file, not only in code."""
    text = (Path(R.__file__).resolve().parents[1] / ".claude" / "commands"
            / "end-review.md").read_text(encoding="utf-8").lower()
    for phrase in ("picture-judging doctrine", "1:1", "not judgeable from pixels",
                   "measure before acting", "say so", "reviewability record"):
        assert phrase in text, phrase


def test_qa_crop_cells_are_never_downscaled():
    """lw_clean_qa_crops used to resize every crop to a 760px cell - a downscale
    for any crop wider than that, exactly the unreliable case."""
    import lw_clean_qa_crops as Q
    from PIL import Image
    im = Image.fromarray(np.full((1440, 2560, 3), 90, dtype=np.uint8))
    row = {"slug": "s", "reason": "not_border", "boxes": [list(ROI)],
           "overlay_score": 0.0, "n_boxes": 1, "conf_max": 0.5}
    cell, rec = Q.build_cell(im, row, sup_rel=None, boost=False)
    assert rec["scale"] == 1.0
    crop = rec["crop"]
    assert cell.width >= crop[2] - crop[0]
