"""ROADMAP R4: anime-lama vs LaMa blind A/B (tools/lw_ab_r4.py).

Pure helpers only - no torch, no cv2. Pins: the approved-_01 LaMa selector
(and the REOPEN exclusion that keeps the LEDGER 268 slugs out); deterministic,
counterbalanced side assignment; crop clamping; the blind contract (items and
votes never name an engine); votes are validated and atomic; the tally refuses
until the operator has finished and every slug carries a vote; the image route
refuses traversal and names outside the fixed set.
"""
from __future__ import annotations

import json
import random
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

import lw_ab_r4 as ab  # noqa: E402

SHA_INIT = "a" * 64
SHA_01 = "b" * 64
SHA_OTHER = "c" * 64


def _manifest(tool="lama", dst="3.Cleaning Scratch/s/s_cleanworking_01.png",
              approved=SHA_01, extra=()):
    tr = [
        {"op": "START_CLEAN", "sha256_out": SHA_INIT, "dst": "3.Cleaning Scratch/s/s_cleaninitial.png"},
        {"op": "SAVE_WORKING", "tool": tool, "dst": dst, "sha256_out": SHA_01,
         "params": {"mask_bbox": [10, 20, 30, 40], "engine": "simple-lama"}},
        {"op": "SUBMIT", "sha256_out": SHA_01},
        {"op": "APPROVE_CLEAN", "sha256_out": approved},
    ]
    tr.extend(extra)
    return {"slug": "s", "transitions": tr}


def test_approved_lama01_accepts_auto_lama_first_working():
    rec = ab.approved_lama01(_manifest())
    assert rec == {"approved_sha": SHA_01, "initial_sha": SHA_INIT,
                   "mask_bbox": [10, 20, 30, 40]}


@pytest.mark.parametrize("kw", [
    {"tool": "clean-scan"},
    {"tool": "operator-select"},
    {"tool": "iopaint"},
    {"dst": "3.Cleaning Scratch/s/s_cleanworking_02.png"},
    {"approved": SHA_OTHER},
])
def test_approved_lama01_rejects_everything_else(kw):
    assert ab.approved_lama01(_manifest(**kw)) is None


def test_approved_lama01_excludes_reopened_slugs():
    # LEDGER 268: the 14 reopened slugs carry a REOPEN transition.
    m = _manifest(extra=[{"op": "REOPEN", "sha256_out": None}])
    assert ab.approved_lama01(m) is None


def test_approved_lama01_needs_an_approval():
    m = _manifest()
    m["transitions"] = [t for t in m["transitions"] if t["op"] != "APPROVE_CLEAN"]
    assert ab.approved_lama01(m) is None


def test_select_is_deterministic_and_order_free():
    slugs = [f"slug{i}" for i in range(30)]
    a = ab.select(slugs, n=20)
    b = ab.select(list(reversed(slugs)), n=20)
    assert a == b and len(a) == 20 and len(set(a)) == 20
    assert ab.select(slugs[:5], n=20) == ab.select(slugs[:5], n=20)
    assert len(ab.select(slugs[:5], n=20)) == 5


def test_assign_sides_is_counterbalanced_and_blind_to_order():
    slugs = [f"s{i}" for i in range(20)]
    key = ab.assign_sides(slugs, rng=random.Random(7))
    assert set(key) == set(slugs)
    lefts = [key[s]["left"] for s in slugs]
    assert lefts.count("lama") == 10 and lefts.count("anime-lama") == 10
    for s in slugs:
        assert {key[s]["left"], key[s]["right"]} == {"lama", "anime-lama"}


def test_assign_sides_odd_count_differs_by_at_most_one():
    key = ab.assign_sides([f"s{i}" for i in range(13)], rng=random.Random(1))
    lefts = [v["left"] for v in key.values()]
    assert abs(lefts.count("lama") - lefts.count("anime-lama")) == 1


@pytest.mark.parametrize("bbox,pad,expect", [
    ((100, 100, 200, 150), 10, (90, 90, 210, 160)),
    ((0, 0, 50, 50), 48, (0, 0, 98, 98)),
    ((2500, 1400, 2560, 1440), 48, (2452, 1352, 2560, 1440)),
])
def test_crop_box_pads_and_clamps(bbox, pad, expect):
    assert ab.crop_box(bbox, 2560, 1440, pad) == expect


def _seed_ab(tmp_path, slugs=("alpha", "beta")):
    root = tmp_path / "ab_r4"
    root.mkdir()
    ab.write_json_atomic(root / "items.json", {"items": [{"slug": s} for s in slugs]})
    key = {"slugs": {s: {"left": "lama" if i % 2 == 0 else "anime-lama",
                         "right": "anime-lama" if i % 2 == 0 else "lama"}
                     for i, s in enumerate(slugs)}}
    ab.write_json_atomic(root / "key.json", key)
    for s in slugs:
        (root / s).mkdir()
        (root / s / "left_tight.png").write_bytes(b"\x89PNG-left")
    return root


def test_items_view_never_names_an_engine(tmp_path):
    root = _seed_ab(tmp_path)
    view = ab.items_view(root)
    blob = json.dumps(view)
    assert "lama" not in blob
    assert [i["slug"] for i in view["items"]] == ["alpha", "beta"]
    assert view["finished"] is False and view["votes"] == {}


def test_vote_is_recorded_blind_and_atomically(tmp_path):
    root = _seed_ab(tmp_path)
    ab.record_vote(root, "alpha", "left")
    ab.record_vote(root, "alpha", "right")  # a change of mind replaces
    votes = json.loads((root / "votes.json").read_text(encoding="ascii"))
    assert votes["votes"]["alpha"]["choice"] == "right"
    assert "lama" not in json.dumps(votes)
    assert not list(root.glob("*.tmp"))


@pytest.mark.parametrize("slug,choice", [
    ("alpha", "lama"), ("alpha", ""), ("gamma", "left"), ("../x", "left"),
])
def test_vote_rejects_bad_input(tmp_path, slug, choice):
    root = _seed_ab(tmp_path)
    with pytest.raises(ab.ABError):
        ab.record_vote(root, slug, choice)


def test_finish_requires_every_slug_voted(tmp_path):
    root = _seed_ab(tmp_path)
    ab.record_vote(root, "alpha", "left")
    with pytest.raises(ab.ABError):
        ab.finish(root)
    ab.record_vote(root, "beta", "same")
    ab.finish(root)
    assert ab.items_view(root)["finished"] is True
    with pytest.raises(ab.ABError):
        ab.record_vote(root, "beta", "left")  # locked once finished


def test_tally_refuses_before_finish_and_maps_sides_after(tmp_path):
    root = _seed_ab(tmp_path)
    ab.record_vote(root, "alpha", "left")    # alpha left = lama
    ab.record_vote(root, "beta", "left")     # beta left = anime-lama
    with pytest.raises(ab.ABError):
        ab.tally(root)
    ab.finish(root)
    t = ab.tally(root)
    assert t["counts"] == {"lama": 1, "anime-lama": 1, "same": 0}
    assert t["n"] == 2
    assert {r["slug"]: r["preferred"] for r in t["per_slug"]} == {
        "alpha": "lama", "beta": "anime-lama"}


@pytest.mark.parametrize("slug,name", [
    ("alpha", "../key.json"), ("alpha", "key.json"), ("alpha", "anime_full.png"),
    ("..", "left_tight.png"), ("gamma", "left_tight.png"),
])
def test_image_path_refuses_outside_the_fixed_set(tmp_path, slug, name):
    root = _seed_ab(tmp_path)
    assert ab.image_path(root, slug, name) is None


def test_image_path_serves_a_known_crop(tmp_path):
    root = _seed_ab(tmp_path)
    p = ab.image_path(root, "alpha", "left_tight.png")
    assert p is not None and p.read_bytes() == b"\x89PNG-left"


def test_prepare_refuses_to_reshuffle_once_votes_exist(tmp_path):
    root = _seed_ab(tmp_path)
    ab.record_vote(root, "alpha", "left")
    with pytest.raises(ab.ABError):
        ab.guard_fresh(root)


def test_weights_pins_are_the_fetched_bytes():
    # official Sanster release; md5 equals IOPaint 1.6.0's ANIME_LAMA_MODEL_MD5
    assert ab.ANIME_WEIGHTS_MD5 == "29f284f36a0a510bcacf39ecf4c4d54f"
    assert len(ab.ANIME_WEIGHTS_SHA256) == 64
    assert ab.ANIME_WEIGHTS_URL.startswith("https://github.com/Sanster/models/")
