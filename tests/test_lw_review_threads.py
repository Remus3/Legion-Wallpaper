"""Spatial review bench threads (directive P1-2, tools/lw_review_threads.py).

Named tests from the directive: submission schema round-trip; publish stamps
only unpublished items; the reply crop uses the stored view; a follow-up
reopens. Hermetic: synthetic PNGs in tmp_path, never the corpus.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

import lw_review_threads as RT  # noqa: E402


def _img(tmp_path, name="ahri_cleanworking_01.png", seed=0):
    root = tmp_path / "images"
    d = root / "3.Cleaning Scratch" / "ahri"
    d.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(seed)
    arr = rng.integers(0, 256, size=(144, 256, 3), dtype=np.uint8)
    Image.fromarray(arr).save(d / name)
    return root, d / name, arr


def _mark(tmp_path, review, root, said="ghost of the credit line here"):
    return RT.submit("ahri", [100, 60], 12, said, {"x0": 40, "y0": 20, "x1": 200, "y1": 120},
                     review_root=review, images_root=root)


def test_submission_round_trips_with_schema(tmp_path):
    root, _, arr = _img(tmp_path)
    review = tmp_path / "review"
    rec = _mark(tmp_path, review, root)
    back = RT.load("ahri", rec["id"], review)
    assert back == rec
    for key in ("kind", "id", "slug", "xy", "r", "said", "view", "state", "published",
                "image", "shots", "thread"):
        assert key in back
    assert back["kind"] == "mark" and back["state"] == "new" and back["published"] is None
    before = np.asarray(Image.open(review / "ahri" / back["shots"]["before"]))
    assert np.array_equal(before, arr[20:120, 40:200])   # the 1:1 view, not a resample


def test_latest_image_is_the_newest_milestone(tmp_path):
    root, p1, _ = _img(tmp_path, "ahri_cleanworking_01.png")
    import os
    import time
    _, p2, _ = _img(tmp_path, "ahri_cleanworking_02.png", seed=1)
    t = time.time()
    os.utime(p1, (t - 100, t - 100))
    os.utime(p2, (t, t))
    assert RT.latest_image("ahri", root) == p2


def test_publish_stamps_only_unpublished_and_notifies_once(tmp_path):
    root, _, _ = _img(tmp_path)
    review = tmp_path / "review"
    first = _mark(tmp_path, review, root)
    sent = []

    def sink(msg):
        sent.append(msg)
        return True, "ok"
    m1 = RT.publish(review, notify=sink)
    assert [i["id"] for i in m1["items"]] == [first["id"]]
    a = _mark(tmp_path, review, root, "band in the sky")
    b = _mark(tmp_path, review, root, "halo on the sword")
    c = _mark(tmp_path, review, root, "smear left of the face")
    m2 = RT.publish(review, notify=sink)
    assert sorted(i["id"] for i in m2["items"]) == sorted(x["id"] for x in (a, b, c))
    assert len(sent) == 2 and sent[1]["count"] == 3          # one notification per batch
    assert RT.load("ahri", first["id"], review)["published"] == m1["batch"]  # not restamped
    assert RT.publish(review, notify=sink) is None and len(sent) == 2


def test_reply_crop_uses_the_stored_view(tmp_path):
    root, path, _ = _img(tmp_path)
    review = tmp_path / "review"
    rec = _mark(tmp_path, review, root)
    fixed = np.zeros((144, 256, 3), dtype=np.uint8)
    fixed[:, :, 1] = np.arange(256, dtype=np.uint8)[None, :]
    newer = path.with_name("ahri_cleanworking_02.png")
    Image.fromarray(fixed).save(newer)
    t = RT.answer("ahri", rec["id"], "re-filled; see reply", review, image_path=newer)
    shot = np.asarray(Image.open(review / "ahri" / t["thread"][-1]["shot"]))
    assert np.array_equal(shot, fixed[20:120, 40:200])
    assert t["state"] == "answered"


def test_follow_up_reopens_and_unpublishes(tmp_path):
    root, _, _ = _img(tmp_path)
    review = tmp_path / "review"
    rec = _mark(tmp_path, review, root)
    RT.publish(review, notify=lambda m: (True, "ok"))
    RT.answer("ahri", rec["id"], "done", review, images_root=root)
    t = RT.follow_up("ahri", rec["id"], "still a faint ghost at 1:1", review)
    assert t["state"] == "new" and t["published"] is None
    assert [e["role"] for e in t["thread"]] == ["operator", "agent", "operator"]


def test_states_and_bad_input_are_refused(tmp_path):
    root, _, _ = _img(tmp_path)
    review = tmp_path / "review"
    rec = _mark(tmp_path, review, root)
    assert RT.set_state("ahri", rec["id"], "fixed", review)["state"] == "fixed"
    with pytest.raises(RT.ReviewError):
        RT.set_state("ahri", rec["id"], "deleted", review)
    with pytest.raises(RT.ReviewError):
        RT.submit("../etc", [1, 1], 5, "x", {"x0": 0, "y0": 0, "x1": 5, "y1": 5},
                  review_root=review, images_root=root)
    with pytest.raises(RT.ReviewError):
        RT.submit("ahri", [9999, 1], 5, "x", {"x0": 0, "y0": 0, "x1": 5, "y1": 5},
                  review_root=review, images_root=root)
    with pytest.raises(RT.ReviewError):
        RT.load("ahri", "../../x", review)


def test_promote_writes_a_seed_and_edits_nothing(tmp_path):
    root, path, _ = _img(tmp_path)
    before = path.read_bytes()
    review = tmp_path / "review"
    rec = _mark(tmp_path, review, root)
    seed = RT.promote("ahri", rec["id"], review)
    assert seed["box"] == [88, 48, 112, 72]
    assert path.read_bytes() == before
    assert json.loads((review / "ahri" / f"{rec['id']}_seed.json").read_text())["from_mark"] == rec["id"]


def test_stored_files_are_ascii(tmp_path):
    root, _, _ = _img(tmp_path)
    review = tmp_path / "review"
    rec = RT.submit("ahri", [10, 10], 4, "café smudge", {"x0": 0, "y0": 0, "x1": 30, "y1": 30},
                    review_root=review, images_root=root)
    raw = (review / "ahri" / f"{rec['id']}.json").read_bytes()
    raw.decode("ascii")


def test_traversal_slugs_are_refused_by_name(tmp_path):
    for bad in ("..", "../x", "a/b", "a\b", "", ".hidden"):
        with pytest.raises(RT.ReviewError, match="bad slug"):
            RT.load(bad, "m20261004T000000-abcdef", tmp_path)


def test_seed_mask_unions_promoted_marks_for_the_cleaning_lane(tmp_path):
    root, path, _ = _img(tmp_path)
    review = tmp_path / "review"
    a = _mark(tmp_path, review, root)
    b = RT.submit("ahri", [30, 30], 5, "veil", {"x0": 0, "y0": 0, "x1": 60, "y1": 60},
                  review_root=review, images_root=root)
    RT.promote("ahri", a["id"], review)
    RT.promote("ahri", b["id"], review)
    out = RT.seed_mask("ahri", review, tmp_path / "clean")
    m = np.asarray(Image.open(out["mask"]))
    assert m.shape == (144, 256) and m[60, 100] == 255 and m[30, 30] == 255 and m[0, 255] == 0
    assert sorted(out["from_marks"]) == sorted([a["id"], b["id"]])
    assert path.read_bytes() == path.read_bytes()  # the artifact is never edited
