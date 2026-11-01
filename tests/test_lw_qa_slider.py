"""LW-QA-SLIDER (MAIN W44 UI/UX round): before/after slider for the QA queue.

One queued (NEEDAUTH) item, its stage input (`_<stage>initial`, the N-1
milestone) against the submitted candidate (`_<stage>needauth`, stage N) in
one box at the candidate's dimensions, and the newest gate audit beside it.
The page is read-only: it writes one html file and touches no pipeline state.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT))

from tools import lw_qa_slider as qs  # noqa: E402

SLUG = "demo-slug"


def _state(root: Path, images: dict) -> Path:
    path = root / "pipeline_state.json"
    path.write_text(json.dumps({"schema": 1, "images": images}), encoding="utf-8")
    return path


def _item(root: Path, stage_folder="1.First Pass Scratch", stage="first",
          gate_audit=None, with_after=True) -> Path:
    folder = root / "images" / stage_folder / SLUG
    folder.mkdir(parents=True)
    (folder / f"{SLUG}_{stage}initial.jpg").write_bytes(b"before")
    if with_after:
        (folder / f"{SLUG}_{stage}needauth.png").write_bytes(b"after")
    transitions = [{"op": "SAVE_WORKING", "audit": {"global_filter": {}}}]
    if gate_audit is not None:
        transitions.append({"op": "ANNOTATE", "audit": gate_audit})
    transitions.append({"op": "SUBMIT", "audit": None})
    (folder / "manifest.json").write_text(
        json.dumps({"slug": SLUG, "transitions": transitions}), encoding="utf-8")
    return folder


G1 = {"gate": "G1", "verdict": "PASS",
      "metrics": {"msssim": 0.9988, "lpips": 0.0085, "halo_pct": 0.0183},
      "fr_all": {"common_scale": [3840, 2160]}}


def test_queue_lists_only_needauth_items_sorted(tmp_path):
    state = {"images": {
        "b": {"substate": "NEEDAUTH", "stage_folder": "x"},
        "a": {"substate": "NEEDAUTH", "stage_folder": "x"},
        "c": {"substate": None, "stage_folder": "x"},
    }}
    assert qs.queue(state) == ["a", "b"]


def test_pair_is_stage_initial_against_stage_needauth(tmp_path):
    folder = _item(tmp_path, stage_folder="3.Cleaning Scratch", stage="clean")
    stage, before, after = qs.pair(folder, SLUG)
    assert stage == "clean"
    assert before.name == f"{SLUG}_cleaninitial.jpg"
    assert after.name == f"{SLUG}_cleanneedauth.png"


def test_pair_without_a_candidate_is_none(tmp_path):
    folder = _item(tmp_path, with_after=False)
    assert qs.pair(folder, SLUG) is None


def test_gate_metrics_takes_the_newest_gate_audit(tmp_path):
    older = {"gate": "G1", "verdict": "FAIL", "metrics": {"lpips": 0.5}}
    man = {"transitions": [{"op": "ANNOTATE", "audit": older},
                           {"op": "ANNOTATE", "audit": G1},
                           {"op": "SUBMIT", "audit": None}]}
    assert qs.gate_metrics(man) is G1
    assert qs.gate_metrics({"transitions": []}) is None


def test_page_shows_both_stages_slider_and_metrics(tmp_path):
    folder = _item(tmp_path, gate_audit=G1)
    out = tmp_path / "out" / "slider.html"
    state = _state(tmp_path, {SLUG: {"substate": "NEEDAUTH",
                                     "stage_folder": "1.First Pass Scratch"}})
    rc = qs.main(["--state", str(state), "--images", str(tmp_path / "images"),
                  "--out", str(out)])
    assert rc == 0
    page = out.read_text(encoding="ascii")
    assert (folder / f"{SLUG}_firstinitial.jpg").resolve().as_uri() in page
    assert (folder / f"{SLUG}_firstneedauth.png").resolve().as_uri() in page
    assert 'type="range"' in page
    assert "G1" in page and "PASS" in page and "0.0085" in page
    assert "3840x2160" in page


def test_page_names_a_missing_gate_audit_instead_of_hiding_it(tmp_path):
    _item(tmp_path, gate_audit=None)
    out = tmp_path / "slider.html"
    state = _state(tmp_path, {SLUG: {"substate": "NEEDAUTH",
                                     "stage_folder": "1.First Pass Scratch"}})
    assert qs.main(["--state", str(state), "--images", str(tmp_path / "images"),
                    "--out", str(out)]) == 0
    assert "no gate audit recorded" in out.read_text(encoding="ascii")


def test_empty_queue_writes_nothing_and_exits_1(tmp_path):
    out = tmp_path / "slider.html"
    state = _state(tmp_path, {})
    assert qs.main(["--state", str(state), "--images", str(tmp_path / "images"),
                    "--out", str(out)]) == 1
    assert not out.exists()


def test_page_is_ascii_and_escapes_the_slug(tmp_path):
    page = qs.build_page("a<b", "first", tmp_path / "x.jpg", tmp_path / "y.png", G1)
    assert "a&lt;b" in page and "a<b" not in page
    page.encode("ascii")
