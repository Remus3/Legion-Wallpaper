"""R3b: G2.seam_step is LIVE in the cleaning verify; the ring-SSIM seam flag is
RETIRED (ROADMAP R3b, LEDGER 266).

R3 (LEDGER 264) proved the contour-normal step 12/12 with 0/26 real FP and
left the live verify unchanged. Here `_auto_inpaint` computes
`seam_step(out, mask)` and passes it to `verify_verdict`, which no longer
flags on `seam_ssim` (ring TEXTURE: 22/37 live verifies flagged a clean fill).
seam_ssim stays in the verify.json metrics as an info field only.
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

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")


def test_ring_ssim_no_longer_flags():
    r = cp.verify_verdict(0.999, 0.4, 0.7, False, 0.10)
    assert r["verdict"] == "pass"
    assert "seam" not in r["flags"]


def _run_auto_inpaint(tmp_path, monkeypatch, offset):
    rng = np.random.default_rng(3)
    h, w = 160, 256
    arr = rng.integers(40, 216, size=(h, w, 3)).astype(np.uint8)
    src = tmp_path / "in.png"
    Image.fromarray(arr).save(src)
    boxes = [(80, 60, 170, 100)]

    def fake_inpaint(base, mask, lama):
        b = np.asarray(base).astype(np.int16)
        m = np.asarray(mask) > 127
        out = b.copy()
        # a "fill" that changes the inside (shuffled) and offsets it
        inside = out[m]
        out[m] = np.clip(inside[::-1] + offset, 0, 255)
        return Image.fromarray(out.astype(np.uint8))

    def np_render_mask(bxs, ww, hh, dilate_px=cp.DILATE_PX):
        # cv2-free stand-in (CI has no cv2): box union grown by a square
        m = np.zeros((int(hh), int(ww)), dtype=np.uint8)
        for x0, y0, x1, y1 in bxs:
            m[max(0, y0 - dilate_px):y1 + dilate_px + 1,
              max(0, x0 - dilate_px):x1 + dilate_px + 1] = 255
        return m

    monkeypatch.setattr(cp, "render_mask", np_render_mask)
    monkeypatch.setattr(cp, "inpaint_lama", fake_inpaint)
    monkeypatch.setattr(cp, "probe_residue", lambda *a, **k: (False, None))
    monkeypatch.setattr(cp, "gpu_lock", lambda dev: contextlib.nullcontext())
    models = {"device": "cpu", "lama": object(), "reader": object()}
    rec = {"slug": "s", "mask_area_pct": 1.0, "conf": 0.9}
    out_dir = tmp_path / "out"
    res = cp._auto_inpaint("s", str(src), boxes, w, h, str(out_dir), 1, models,
                           ["en"], rec)
    on_disk = json.loads((out_dir / "s_verify.json").read_text(encoding="utf-8"))
    return res, on_disk


def test_live_verify_flags_an_offset_fill(tmp_path, monkeypatch):
    res, disk = _run_auto_inpaint(tmp_path, monkeypatch, 24)
    v = res["verify"]
    assert v["verdict"] == "pass"
    assert "seam_step" in v["flags"]
    assert v["metrics"]["seam_step"] > cp.SEAM_STEP_MAX
    assert "seam_step" in disk["verify"]["flags"]


def test_live_verify_clean_fill_no_seam_flags_and_ssim_kept_as_info(tmp_path, monkeypatch):
    res, _ = _run_auto_inpaint(tmp_path, monkeypatch, 0)
    v = res["verify"]
    assert v["verdict"] == "pass"
    assert "seam_step" not in v["flags"] and "seam" not in v["flags"]
    assert v["metrics"]["seam_step"] <= cp.SEAM_STEP_MAX
    # info field kept for census continuity, never a flag
    assert "seam_ssim" in v["metrics"]


def test_board_has_no_ring_ssim_seam_row():
    names = {r.name for r in B.lw_board(envs=("base",)).rows}
    assert "G2.seam" not in names
    assert "G2.seam_step" in names
    assert "G2.seam" not in B.FAULT_EVIDENCE and "G2.seam" not in B.FAULT_NAME


def test_ack_has_no_g2_seam_entry():
    with open(os.path.join(ROOT, "config", "gate_board_ack.json"), encoding="utf-8") as f:
        ack = json.load(f)
    assert "G2.seam" not in {e["row"] for e in ack["entries"]}
