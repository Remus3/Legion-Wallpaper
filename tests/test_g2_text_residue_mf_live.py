"""R2b: G2.text_residue_mf is LIVE in the cleaning verify (ROADMAP R2b).

R2 (LEDGER 267) proved the re-inpaint matched filter 12/12 on a SYNTHETIC
stroke mask. The live verify only has detection boxes, so the stroke mask is
derived from the PRE-clean image inside each detected box with the existing
glyph narrowing `lw_clean_creditline.glyph_mask` (grow=0: the residue sits on
the glyph pixels themselves, a grown mask is mostly halo and its median reads
the fill, not the residue). `_auto_inpaint` passes the value to
`verify_verdict(residue_mf=...)` and records it in verify.json metrics. With
no LaMa (or any probe error) the value is None, logged by type, never raised.

numpy-only: CI has no cv2 / torch (LEDGER 266 CI break).
"""
import contextlib
import json
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tools"))

import lw_clean_pass as cp  # noqa: E402
import lw_gate_board as B  # noqa: E402

H, W = 200, 640
BOX = (80, 120, 560, 180)


def _glyphs():
    cov = B.text_mask("WWW.DEVIANTART.COM/ARTIST", BOX[2] - BOX[0], BOX[3] - BOX[1]) > 0.5
    g = np.zeros((H, W), dtype=bool)
    g[BOX[1]:BOX[3], BOX[0]:BOX[2]] = cov
    return g


def _marked(levels=40.0, bg=100):
    rng = np.random.default_rng(1)
    img = np.clip(bg + rng.normal(0, 3, (H, W, 3)), 0, 255)
    img[_glyphs()] += levels
    return np.clip(img, 0, 255).astype(np.uint8)


def _flat_lama(image, mask):
    """Fills the hole with the mean of the unmasked pixels."""
    a = np.asarray(image.convert("RGB"), dtype=np.float64)
    m = np.asarray(mask.convert("L")) > 127
    out = a.copy()
    out[m] = a[~m].mean(axis=0)
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))


def test_boxes_mask_is_numpy_and_inclusive():
    m = cp.boxes_mask([(2, 3, 5, 4)], 8, 6)
    assert m.dtype == bool and m.shape == (6, 8)
    assert m.sum() == 4 * 2 and m[3, 2] and m[4, 5] and not m[5, 5]
    # clipped, never wraps
    assert cp.boxes_mask([(-4, -4, 100, 100)], 8, 6).all()


def test_live_stroke_mask_lands_on_the_glyphs_inside_the_box():
    img = _marked()
    s = cp.live_stroke_mask(img, [BOX])
    g = _glyphs()
    assert s.dtype == bool and s.shape == (H, W)
    assert (s & g).sum() / g.sum() > 0.9          # recall
    assert (s & g).sum() / s.sum() > 0.7          # precision (not a grown halo)
    outside = ~cp.boxes_mask([BOX], W, H)
    assert not (s & outside).any()


def test_live_stroke_mask_no_boxes_is_empty():
    assert not cp.live_stroke_mask(_marked(), []).any()


def test_live_residue_mf_reads_a_four_level_residue():
    before = _marked()
    clean = np.full((H, W, 3), 100, dtype=np.uint8)
    v, err = cp.live_residue_mf(before, clean, [BOX], _flat_lama)
    assert err is None and abs(v) < 1.0, v
    faint = clean.astype(np.float64)
    faint[_glyphs()] += 5
    v, err = cp.live_residue_mf(before, faint.astype(np.uint8), [BOX], _flat_lama)
    assert err is None and v > cp.RESIDUE_MF_MAX, v


def test_live_residue_mf_degrades_to_none_without_lama_or_on_error():
    before = _marked()
    clean = np.full((H, W, 3), 100, dtype=np.uint8)
    assert cp.live_residue_mf(before, clean, [BOX], None) == (None, "lama_unavailable")

    def boom(image, mask):
        raise RuntimeError("CUDA out of memory: secret detail")

    v, err = cp.live_residue_mf(before, clean, [BOX], boom)
    assert v is None and err == "RuntimeError"


def _run_auto_inpaint(tmp_path, monkeypatch, residue, reinpaint_fails=False):
    before = _marked()
    src = tmp_path / "in.png"
    Image.fromarray(before).save(src)
    glyphs = _glyphs()

    def fake_inpaint(base, mask, lam):
        a = np.asarray(base).astype(np.float64)
        m = np.asarray(mask) > 127
        out = a.copy()
        out[m] = 100.0
        if a.shape[:2] == (H, W):   # the clean itself leaves `residue` on the strokes
            out[glyphs & m] += residue
        elif reinpaint_fails:
            raise RuntimeError("CUDA out of memory: raw detail")
        return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))

    def np_render_mask(bxs, ww, hh, dilate_px=cp.DILATE_PX):
        m = np.zeros((int(hh), int(ww)), dtype=np.uint8)
        for x0, y0, x1, y1 in bxs:
            m[max(0, y0 - dilate_px):y1 + dilate_px + 1,
              max(0, x0 - dilate_px):x1 + dilate_px + 1] = 255
        return m

    monkeypatch.setattr(cp, "render_mask", np_render_mask)
    monkeypatch.setattr(cp, "inpaint_lama", fake_inpaint)
    monkeypatch.setattr(cp, "gpu_lock", lambda dev: contextlib.nullcontext())
    models = {"device": "cpu", "reader": object(), "lama": object()}
    rec = {"slug": "s", "mask_area_pct": 1.0, "conf": 0.9}
    out_dir = tmp_path / "out"
    res = cp._auto_inpaint("s", str(src), [BOX], W, H, str(out_dir), 1, models,
                           ["en"], rec)
    disk = json.loads((out_dir / "s_verify.json").read_text(encoding="utf-8"))
    return res, disk


def test_live_verify_flags_a_faint_residue_and_records_it(tmp_path, monkeypatch):
    res, disk = _run_auto_inpaint(tmp_path, monkeypatch, residue=6)
    v = res["verify"]
    assert v["verdict"] == "pass"
    assert "residue_mf" in v["flags"]
    assert v["metrics"]["residue_mf"] > cp.RESIDUE_MF_MAX
    assert v["metrics"]["residue_mf_error"] is None
    assert "residue_mf" in disk["verify"]["flags"]
    assert disk["verify"]["metrics"]["residue_mf"] == v["metrics"]["residue_mf"]


def test_live_verify_clean_fill_is_not_flagged(tmp_path, monkeypatch):
    res, _ = _run_auto_inpaint(tmp_path, monkeypatch, residue=0)
    v = res["verify"]
    assert v["verdict"] == "pass" and "residue_mf" not in v["flags"]
    assert abs(v["metrics"]["residue_mf"]) <= cp.RESIDUE_MF_MAX


def test_live_verify_reinpaint_error_records_none_and_does_not_flag(tmp_path, monkeypatch, capsys):
    res, disk = _run_auto_inpaint(tmp_path, monkeypatch, residue=6, reinpaint_fails=True)
    v = res["verify"]
    assert v["verdict"] == "pass" and "residue_mf" not in v["flags"]
    assert v["metrics"]["residue_mf"] is None
    assert v["metrics"]["residue_mf_error"] == "RuntimeError"
    out = capsys.readouterr().out
    assert "residue_mf" in out and "raw detail" not in out


# ---- retirement of the OCR+MSER arm (R2b, after the live census) ----------
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")


def test_ocr_mser_residue_no_longer_fails_or_flags():
    r = cp.verify_verdict(0.999, 0.4, 0.7, True, 0.95)
    assert r["verdict"] == "pass" and r["reasons"] == []
    r = cp.verify_verdict(0.999, 0.4, 0.7, None, 0.95)
    assert "residue_probe_error" not in r["flags"]


def test_unknown_residue_mf_is_flagged_never_clean():
    r = cp.verify_verdict(0.999, 0.4, 0.7, None, 0.95, residue_mf=None,
                          residue_mf_error="RuntimeError")
    assert r["verdict"] == "pass" and "residue_mf_error" in r["flags"]
    assert "residue_mf_error" not in cp.verify_verdict(0.999, 0.4, 0.7, None, 0.95,
                                                       residue_mf=0.1)["flags"]


def test_live_verify_does_not_run_the_ocr_mser_probe(tmp_path, monkeypatch):
    def boom(*a, **k):
        raise AssertionError("retired OCR+MSER probe was called")
    monkeypatch.setattr(cp, "probe_residue", boom)
    res, disk = _run_auto_inpaint(tmp_path, monkeypatch, residue=0)
    assert res["verify"]["verdict"] == "pass"
    assert "residue" not in res["verify"]["metrics"]


def test_live_verify_reinpaint_error_flags_unknown(tmp_path, monkeypatch):
    res, _ = _run_auto_inpaint(tmp_path, monkeypatch, residue=6, reinpaint_fails=True)
    assert "residue_mf_error" in res["verify"]["flags"]


def test_board_and_ack_have_no_ocr_mser_residue_row():
    names = {r.name for r in B.lw_board().rows}
    assert "G2.text_residue" not in names and "G2.text_residue_mf" in names
    assert "G2.text_residue" not in B.FAULT_EVIDENCE
    assert "G2.text_residue" not in B.FAULT_NAME
    with open(os.path.join(ROOT, "config", "gate_board_ack.json"), encoding="utf-8") as f:
        ack = json.load(f)
    assert "G2.text_residue" not in {e["row"] for e in ack["entries"]}
