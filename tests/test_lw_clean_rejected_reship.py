"""Regression: an operator-REJECTED cleaning candidate re-shipped as "clean-scan".

Incident 2026-10-04 (operator report, slug spirit-blossom-ahri-mono-01-by-
hriful-dk79ceq-pre): the 2026-08-22 gate-driven disposition registered the
slug's HIGHEST `_cleanworking_NN` - an iopaint candidate the operator had
REJECTED on 2026-08-02 - as a `clean-scan` passthrough, then auto-approved it.
14 slugs in 4.Cleaning Done shipped rejected bytes this way. Three defects, one
test group each:

  1. `save-working --tool clean-scan` accepted bytes that are not the stage
     initial. A clean scan is a passthrough by definition (ADR-009 exempts it
     from the one-engine rule for exactly that reason), so any other bytes are
     an inpaint smuggled past every engine gate.
  2. `lw_clean_dispose` handed the triage row's image (the highest working)
     to the clean-scan builder instead of the slug's `_cleaninitial`.
  3. `approve --actor tool:auto-approve` recorded `actor=operator` in both the
     manifest and PIPELINE_LOG.md: the actor reached the ADR-008 rail but was
     dropped before `_complete_approve` wrote the record.

Plus the mask defect that produced the damage in the first place:

  4. `lw_clean_iopaint.resolve_preset` gave a slug with no measured region the
     namakx credit box (frame centre-bottom), which on the hriful frame sits on
     the character's skirt. The fallback is removed: no measured region, no run.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import lw_pipeline as lw  # noqa: E402

STAGE_FOLDERS = [
    "0.Originals", "1.First Pass Scratch", "2.First Pass Done",
    "3.Cleaning Scratch", "4.Cleaning Done", "5.Final Scratch",
    "6.Final Done", "7.Last Scratch", "8.End Review", "9.Image Backup",
]

HRIFUL = "spirit-blossom-ahri-mono-01-by-hriful-dk79ceq-pre"


@pytest.fixture()
def root(tmp_path: Path) -> Path:
    r = tmp_path / "images"
    for name in STAGE_FOLDERS:
        d = r / name
        d.mkdir(parents=True)
        (d / ".gitkeep").write_text("")
    return r


@pytest.fixture(autouse=True)
def _fast_gate(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(lw, "PROBE_SECONDS", 0.0)


def run(root: Path, *args: str) -> int:
    return lw.main(["--root", str(root), *args])


def _seed_cleaning(root: Path, slug: str) -> Path:
    folder = root / "3.Cleaning Scratch" / slug
    folder.mkdir(parents=True)
    man = lw.new_manifest(slug, f"{slug}.png", "0" * 64)
    (folder / "manifest.json").write_text(
        json.dumps(man, indent=2) + "\n", encoding="utf-8")
    (folder / f"{slug}_cleaninitial.png").write_bytes(b"initial")
    return folder


def _manifest(folder: Path) -> dict:
    return json.loads((folder / "manifest.json").read_text(encoding="utf-8"))


# ---------------------------------------------- 1. clean-scan is passthrough

def test_clean_scan_of_non_initial_bytes_is_refused_and_writes_nothing(
        root: Path, tmp_path: Path):
    folder = _seed_cleaning(root, "ahri")
    rejected = tmp_path / "ahri_cleanworking_03.png"
    rejected.write_bytes(b"an inpainted candidate the operator rejected")
    assert run(root, "save-working", "ahri", "--from", str(rejected),
               "--tool", "clean-scan") == 3
    assert not (folder / "ahri_cleanworking_01.png").exists()
    assert _manifest(folder)["transitions"] == []


def test_clean_scan_of_the_initial_itself_is_allowed(root: Path):
    folder = _seed_cleaning(root, "ahri")
    assert run(root, "save-working", "ahri", "--from",
               str(folder / "ahri_cleaninitial.png"),
               "--tool", "clean-scan") == 0
    assert (folder / "ahri_cleanworking_01.png").read_bytes() == b"initial"


def test_clean_scan_of_a_byte_identical_copy_is_allowed(root: Path,
                                                        tmp_path: Path):
    """Identity is by CONTENT, not path - a copy of the initial is fine."""
    _seed_cleaning(root, "ahri")
    copy = tmp_path / "copy.png"
    copy.write_bytes(b"initial")
    assert run(root, "save-working", "ahri", "--from", str(copy),
               "--tool", "clean-scan") == 0


def test_other_tools_are_not_held_to_the_passthrough_rule(root: Path,
                                                          tmp_path: Path):
    _seed_cleaning(root, "ahri")
    cand = tmp_path / "cand.png"
    cand.write_bytes(b"a real inpaint")
    assert run(root, "save-working", "ahri", "--from", str(cand),
               "--tool", "lama") == 0


def test_passthrough_rule_unit():
    lw.assert_clean_scan_passthrough("s", "clean", "clean-scan", "a" * 64,
                                     "a" * 64)
    lw.assert_clean_scan_passthrough("s", "clean", "lama", "a" * 64, "b" * 64)
    with pytest.raises(lw.PipelineError) as ei:
        lw.assert_clean_scan_passthrough("s", "clean", "clean-scan",
                                         "a" * 64, "b" * 64)
    assert ei.value.code == 3
    # no initial on disk to compare against -> fail CLOSED
    with pytest.raises(lw.PipelineError):
        lw.assert_clean_scan_passthrough("s", "clean", "clean-scan", None,
                                         "b" * 64)


# ---------------------------------------------- 2. dispose uses the initial

def test_dispose_clean_scan_registers_the_initial_not_the_triage_image(
        monkeypatch, tmp_path: Path):
    import lw_clean_dispose as disp
    scratch = tmp_path / "3.Cleaning Scratch"
    (scratch / "s1").mkdir(parents=True)
    initial = scratch / "s1" / "s1_cleaninitial.png"
    initial.write_bytes(b"initial")
    working = scratch / "s1" / "s1_cleanworking_03.png"
    working.write_bytes(b"rejected")
    monkeypatch.setattr(disp.lcp, "CLEAN_SCRATCH", str(scratch))
    rec = disp.drive("s1", "clean", str(working), dry_run=True)
    save = rec["steps"][0]["argv"]
    assert save[2] == "save-working"
    assert Path(save[save.index("--from") + 1]) == initial


# ---------------------------------------------- 3. approve records its actor

def _needauth_in_clean(root: Path, slug: str) -> Path:
    folder = _seed_cleaning(root, slug)
    assert run(root, "save-working", slug, "--from",
               str(folder / f"{slug}_cleaninitial.png"),
               "--tool", "clean-scan") == 0
    assert run(root, "submit", slug) == 0
    return folder


def test_tool_approval_is_recorded_as_the_tool_not_the_operator(root: Path):
    _needauth_in_clean(root, "ahri")
    assert run(root, "approve", "ahri", "--actor", "tool:auto-approve") == 0
    man = _manifest(root / "4.Cleaning Done" / "ahri")
    appr = [t for t in man["transitions"] if t["op"] == "APPROVE_CLEAN"]
    assert appr and appr[-1]["actor"] == "tool:auto-approve"
    log = (root.parent / "PIPELINE_LOG.md").read_text(encoding="ascii")
    line = [ln for ln in log.splitlines() if "| APPROVE_CLEAN |" in ln][-1]
    assert "actor=tool:auto-approve" in line


def test_operator_approval_still_records_operator(root: Path):
    _needauth_in_clean(root, "ahri")
    assert run(root, "approve", "ahri") == 0
    man = _manifest(root / "4.Cleaning Done" / "ahri")
    appr = [t for t in man["transitions"] if t["op"] == "APPROVE_CLEAN"]
    assert appr[-1]["actor"] == "operator"


# ---------------------------------------------- 4. no borrowed mask region

def test_hriful_preset_is_not_the_namakx_box():
    import lw_clean_iopaint as io
    region, chroma, src = io.resolve_preset(HRIFUL)
    assert region != io.NAMAKX_REGION
    x0, y0, x1, y1 = region
    # the deviantart.com/hriful credit sits bottom-LEFT (detector box
    # 0..392 x 1383..1440 on 2560x1440); the region must cover it and stay
    # clear of the character (x >= ~820 on this frame)
    assert x0 <= 1 and x1 >= 392 and y0 <= 1383 and y1 >= 1439
    assert x1 < 820
    assert src == "slug"


def test_unknown_slug_gets_no_region_at_all():
    import lw_clean_iopaint as io
    region, chroma, src = io.resolve_preset("no-such-slug-at-all")
    assert region is None
    assert src == "none"


def test_namakx_siblings_still_resolve_to_the_namakx_box():
    import lw_clean_iopaint as io
    region, _, _ = io.resolve_preset(io.NAMAKX_SLUGS[0])
    assert region == io.NAMAKX_REGION


def test_clean_slug_refuses_without_a_measured_region(tmp_path: Path):
    import lw_clean_iopaint as io
    img = tmp_path / "x.png"
    img.write_bytes(b"not read")
    res = io.clean_slug("no-such-slug-at-all", image=str(img),
                        out_dir=str(tmp_path), dry_run=True, log=lambda *a: None)
    assert res["status"] == "manual"
    assert "region" in res["reason"]
