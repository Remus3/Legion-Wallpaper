"""Brand assets: the original LW icon, banner and social preview (operator order 2026-11-17).

THE RULE. The repo's icon, README banner and GitHub social-preview card are
ORIGINAL, self-authored and generated from ONE geometry in
`tools/lw_brand_assets.py`: an abstract 16:9 frame whose left part is the
blocky low-resolution scene and whose right part is the same scene restored,
split by a scan bar, with a gate check badge. No third-party artwork, logo or
character. The committed SVGs are byte-identical to the generator output, so a
hand edit that drifts from the source fails here.
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

import lw_brand_assets as ba

import pytest

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "docs" / "assets"


@pytest.mark.parametrize("name,make", [("lw-icon.svg", ba.icon_svg),
                                       ("lw-banner.svg", ba.banner_svg)])
def test_committed_svg_matches_the_generator(name, make):
    got = (ASSETS / name).read_bytes()
    assert got == make().encode("ascii"), (
        f"{name} drifted from tools/lw_brand_assets.py; run "
        "`python tools/lw_brand_assets.py --write`")


@pytest.mark.parametrize("make", [ba.icon_svg, ba.banner_svg])
def test_svg_is_ascii_lf_and_well_formed(make):
    text = make()
    text.encode("ascii")
    assert "\r" not in text
    root = ET.fromstring(text)
    assert root.tag.endswith("svg")
    assert root.get("viewBox")


@pytest.mark.parametrize("make", [ba.icon_svg, ba.banner_svg])
def test_svg_is_self_contained_and_original(make):
    text = make().lower()
    for banned in ("<image", "xlink:href=\"http", "href=\"http", "<script",
                   "league", "riot", "legends"):
        assert banned not in text, banned


def test_icon_has_the_four_design_parts():
    root = ET.fromstring(ba.icon_svg())
    ids = {el.get("id") for el in root.iter() if el.get("id")}
    assert {"frame", "lowres", "restored", "scanbar", "gate"} <= ids


def test_lowres_half_samples_the_same_scene_as_the_restored_half():
    """The pixel cells are the scene sampled at each cell centre - a cell over
    the sun reads the sun colour, a cell over the sky reads a sky colour."""
    sun_u, sun_v = ba.SUN[0], ba.SUN[1]
    assert ba.scene_color(sun_u, sun_v) == ba.SUN_COLOR
    assert ba.scene_color(0.5, 0.02) != ba.SUN_COLOR
    assert ba.scene_color(0.5, 0.99) == ba.FRONT_HILL


def test_social_preview_png_is_the_github_size():
    from PIL import Image
    p = ASSETS / "lw-social-preview.png"
    with Image.open(p) as im:
        assert im.size == (1280, 640)
        assert im.mode in ("RGB", "RGBA")
    assert p.stat().st_size < 1_000_000


def test_render_social_preview_writes_a_1280x640_png(tmp_path):
    from PIL import Image
    out = tmp_path / "card.png"
    ba.render_social_png(out)
    with Image.open(out) as im:
        assert im.size == (1280, 640)


def test_readme_leads_with_the_banner():
    head = (ROOT / "README.md").read_text(encoding="utf-8").splitlines()[:6]
    assert any("docs/assets/lw-banner.svg" in line for line in head)


def test_check_mode_reports_drift(tmp_path, monkeypatch):
    monkeypatch.setattr(ba, "ASSETS", tmp_path)
    assert ba.main(["--check"]) == 1
    assert ba.main(["--write"]) == 0
    assert ba.main(["--check"]) == 0
