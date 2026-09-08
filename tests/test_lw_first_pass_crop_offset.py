"""Tests for the EXACT crop-offset override in tools/lw_first_pass.py.

The sides grammar (`{slug: ["top"]}`) can only express three anchors on the
axis that needs cropping: center (both sides), hard-top and hard-bottom. That is
not enough for slug dmrl7u8-f489448f-6fc3-49f0-9fda-cec3fbc91e61 (1024x1024),
whose operator-picked 16:9 window starts at y=125 - hard-top gives y=0 and
truncates the subject, center gives y=224 and decapitates it.

The offset form generalizes the sides form rather than replacing it: for a
too-tall frame `["bottom"]` already means "top offset 0" and `["top"]` means
"top offset = remove", so an explicit `{"top": 125}` simply names a value in
between. The equality assertions below pin that generalization claim against
`anchored_crop_box` itself, so the two forms cannot drift apart.

CI constraint (same as test_lw_first_pass.py): system python 3.14 and CI 3.12
with ONLY PIL + numpy + stdlib. No torch, no pyiqa, no GPU.

Written test-first per CLAUDE.md TDD.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import lw_first_pass as fp  # noqa: E402

# The real held slug this grammar exists for.
DMRL_W, DMRL_H = 1024, 1024
DMRL_TOP = 125
DMRL_BOX = (0, 125, 1024, 701)


# ---------------------------------------------------------------------------
# offset_crop_box - geometry
# ---------------------------------------------------------------------------
def test_the_operator_picked_offset_lands_on_the_exact_window():
    """1024x1024 with top=125 is the window the operator actually chose."""
    assert fp.offset_crop_box(DMRL_W, DMRL_H, {"top": DMRL_TOP}) == DMRL_BOX


def test_a_bottom_offset_is_measured_from_the_bottom_edge():
    """remove=448, so bottom=323 is the same window as top=125."""
    assert fp.offset_crop_box(DMRL_W, DMRL_H, {"bottom": 448 - DMRL_TOP}) == DMRL_BOX


def test_the_operator_offset_is_neither_anchor():
    """The whole reason for the grammar: no sides value reaches this box."""
    assert fp.anchored_crop_box(DMRL_W, DMRL_H, ["top"]) != DMRL_BOX
    assert fp.anchored_crop_box(DMRL_W, DMRL_H, ["bottom"]) != DMRL_BOX
    assert fp.anchored_crop_box(DMRL_W, DMRL_H, ["top", "bottom"]) != DMRL_BOX


def test_top_offset_zero_is_exactly_the_hard_bottom_anchor():
    """Generalization pin: no loss off the top == all loss off the bottom."""
    assert (fp.offset_crop_box(1920, 1279, {"top": 0})
            == fp.anchored_crop_box(1920, 1279, ["bottom"]))


def test_top_offset_at_the_maximum_is_exactly_the_hard_top_anchor():
    """Generalization pin: all loss off the top == the 'top' sides anchor."""
    remove = 1280 - min(round(1920 * 9 / 16), 1280)
    assert (fp.offset_crop_box(1920, 1280, {"top": remove})
            == fp.anchored_crop_box(1920, 1280, ["top"]))


def test_bottom_offset_zero_is_exactly_the_hard_top_anchor():
    assert (fp.offset_crop_box(1920, 1280, {"bottom": 0})
            == fp.anchored_crop_box(1920, 1280, ["top"]))


def test_bottom_offset_at_the_maximum_is_exactly_the_hard_bottom_anchor():
    remove = 1279 - min(round(1920 * 9 / 16), 1279)
    assert (fp.offset_crop_box(1920, 1279, {"bottom": remove})
            == fp.anchored_crop_box(1920, 1279, ["bottom"]))


def test_a_too_wide_frame_takes_a_left_offset():
    """bamboo 1024x510: new_w=907, remove=117, so left=30 keeps 907 columns."""
    assert fp.offset_crop_box(1024, 510, {"left": 30}) == (30, 0, 937, 510)


def test_left_offset_zero_is_exactly_the_hard_right_anchor():
    assert (fp.offset_crop_box(1024, 510, {"left": 0})
            == fp.anchored_crop_box(1024, 510, ["right"]))


def test_right_offset_zero_is_exactly_the_hard_left_anchor():
    assert (fp.offset_crop_box(1024, 510, {"right": 0})
            == fp.anchored_crop_box(1024, 510, ["left"]))


def test_every_offset_box_is_exact_16x9_and_inside_the_frame():
    cases = [
        (1024, 1024, {"top": 125}),
        (1920, 1280, {"top": 77}),
        (1024, 701, {"bottom": 60}),
        (1024, 510, {"left": 30}),
        (1081, 739, {"top": 12}),
    ]
    for w, h, spec in cases:
        left, top, right, bottom = fp.offset_crop_box(w, h, spec)
        assert 0 <= left < right <= w
        assert 0 <= top < bottom <= h
        ratio = (right - left) / (bottom - top)
        assert abs(ratio - fp.TARGET_ASPECT) <= 0.01, (w, h, spec)


def test_an_already_16x9_frame_is_returned_whole():
    assert fp.offset_crop_box(2560, 1440, {"top": 5}) == (0, 0, 2560, 1440)


# ---------------------------------------------------------------------------
# offset_crop_box - rejection
# ---------------------------------------------------------------------------
def test_a_horizontal_key_on_a_too_tall_frame_raises():
    with pytest.raises(ValueError, match="tall"):
        fp.offset_crop_box(1024, 640, {"left": 10})


def test_a_vertical_key_on_a_too_wide_frame_raises():
    with pytest.raises(ValueError, match="wide"):
        fp.offset_crop_box(1024, 510, {"top": 10})


def test_an_offset_past_the_permitted_maximum_raises():
    with pytest.raises(ValueError, match="448"):
        fp.offset_crop_box(DMRL_W, DMRL_H, {"top": 449})


def test_a_negative_offset_raises():
    with pytest.raises(ValueError):
        fp.offset_crop_box(DMRL_W, DMRL_H, {"top": -1})


def test_two_keys_raise():
    with pytest.raises(ValueError):
        fp.offset_crop_box(DMRL_W, DMRL_H, {"top": 10, "bottom": 10})


def test_no_key_raises():
    with pytest.raises(ValueError):
        fp.offset_crop_box(DMRL_W, DMRL_H, {})


def test_an_unknown_key_raises():
    with pytest.raises(ValueError):
        fp.offset_crop_box(DMRL_W, DMRL_H, {"topp": 10})


def test_a_bool_offset_raises():
    """bool is an int subclass; {"top": true} must not read as 1."""
    with pytest.raises(ValueError):
        fp.offset_crop_box(DMRL_W, DMRL_H, {"top": True})


def test_a_non_integer_offset_raises():
    with pytest.raises(ValueError):
        fp.offset_crop_box(DMRL_W, DMRL_H, {"top": 125.5})


# ---------------------------------------------------------------------------
# the dispatcher - callers must not branch
# ---------------------------------------------------------------------------
def test_the_dispatcher_routes_a_list_to_the_sides_form():
    assert (fp.resolve_crop_box(1920, 1280, ["top"])
            == fp.anchored_crop_box(1920, 1280, ["top"]))


def test_the_dispatcher_routes_a_tuple_to_the_sides_form():
    assert (fp.resolve_crop_box(1920, 1280, ("top",))
            == fp.anchored_crop_box(1920, 1280, ("top",)))


def test_the_dispatcher_routes_a_dict_to_the_offset_form():
    assert (fp.resolve_crop_box(DMRL_W, DMRL_H, {"top": DMRL_TOP})
            == fp.offset_crop_box(DMRL_W, DMRL_H, {"top": DMRL_TOP}))


def test_the_dispatcher_rejects_a_type_it_cannot_route():
    with pytest.raises(ValueError):
        fp.resolve_crop_box(DMRL_W, DMRL_H, "top")


# ---------------------------------------------------------------------------
# parse_crop_overrides - both grammars in one file
# ---------------------------------------------------------------------------
def test_parse_reads_both_grammars_from_one_file(tmp_path):
    p = tmp_path / "ov.json"
    p.write_text(
        '{"akali-x": "left,top,right", "vayne-y": ["bottom"], '
        '"dmrl7u8-x": {"top": 125}}',
        encoding="utf-8")
    got = fp.parse_crop_overrides(str(p))
    assert got == {"akali-x": ["left", "top", "right"],
                   "vayne-y": ["bottom"],
                   "dmrl7u8-x": {"top": 125}}


def test_parse_rejects_a_two_key_offset(tmp_path):
    p = tmp_path / "ov.json"
    p.write_text('{"a": {"top": 1, "bottom": 2}}', encoding="utf-8")
    with pytest.raises(ValueError):
        fp.parse_crop_overrides(str(p))


def test_parse_rejects_an_unknown_offset_key(tmp_path):
    p = tmp_path / "ov.json"
    p.write_text('{"a": {"middle": 1}}', encoding="utf-8")
    with pytest.raises(ValueError):
        fp.parse_crop_overrides(str(p))


def test_parse_rejects_a_negative_offset(tmp_path):
    p = tmp_path / "ov.json"
    p.write_text('{"a": {"top": -5}}', encoding="utf-8")
    with pytest.raises(ValueError):
        fp.parse_crop_overrides(str(p))


def test_parse_rejects_a_non_integer_offset(tmp_path):
    p = tmp_path / "ov.json"
    p.write_text('{"a": {"top": 12.5}}', encoding="utf-8")
    with pytest.raises(ValueError):
        fp.parse_crop_overrides(str(p))


def test_parse_rejects_a_bool_offset(tmp_path):
    """JSON true decodes to a python bool, which is an int subclass."""
    p = tmp_path / "ov.json"
    p.write_text('{"a": {"top": true}}', encoding="utf-8")
    with pytest.raises(ValueError):
        fp.parse_crop_overrides(str(p))


def test_parse_rejects_an_empty_offset_object(tmp_path):
    p = tmp_path / "ov.json"
    p.write_text('{"a": {}}', encoding="utf-8")
    with pytest.raises(ValueError):
        fp.parse_crop_overrides(str(p))


# ---------------------------------------------------------------------------
# condition_source - the offset flows end to end, and records faithfully
# ---------------------------------------------------------------------------
def _write_img(path, w, h):
    from PIL import Image
    Image.new("RGB", (w, h), (90, 120, 200)).save(path, format="PNG")
    return str(path)


def test_condition_source_honours_an_offset_override(tmp_path):
    src = _write_img(tmp_path / "src.png", DMRL_W, DMRL_H)
    out, plan = fp.condition_source(src, tmp_path, crop_sides={"top": DMRL_TOP})

    assert out is not None and out != src
    assert plan["cropped"] is True
    assert plan["aspect_class"] == "crop_override"
    assert plan["crop_box"] == DMRL_BOX
    assert plan["area_loss"] == pytest.approx(448 / 1024, abs=1e-6)

    from PIL import Image
    with Image.open(out) as im:
        assert im.size == (1024, 576)


def test_condition_source_records_the_offset_dict_not_its_keys(tmp_path):
    """list() on a dict yields KEYS; the plan must carry the instruction."""
    src = _write_img(tmp_path / "src.png", DMRL_W, DMRL_H)
    _out, plan = fp.condition_source(src, tmp_path,
                                     crop_sides={"top": DMRL_TOP})
    assert plan["crop_sides"] == {"top": DMRL_TOP}


def test_the_recorded_instruction_is_json_safe(tmp_path):
    """The plan value is written into the manifest, so it must serialize."""
    import json
    src = _write_img(tmp_path / "src.png", DMRL_W, DMRL_H)
    _out, plan = fp.condition_source(src, tmp_path,
                                     crop_sides={"top": DMRL_TOP})
    assert json.loads(json.dumps(plan["crop_sides"])) == {"top": DMRL_TOP}
