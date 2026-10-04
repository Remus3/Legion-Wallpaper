"""Reviewability pre-check for crops sent to a vision reviewer (directive P1-7).

Doctrine (also in .claude/commands/end-review.md, "Picture-judging doctrine"):
a model judging pictures is reliable about SHAPE and ABSENCE and unreliable
about faint, small or contact-level properties. The zero-watermark bar is about
faint marks, so a residue judgement made from a downscaled sheet is exactly the
unreliable case. Picture size decides what a picture can answer: whole-scene
thumbnails are for layout; detail needs one region at 1:1.

Every crop sent for a residue judgement carries a reviewability record:

  scale          output px / source px - must be exactly 1.0 (never downscaled;
                 an upscale invents nothing but is not 1:1 either)
  roi margin     the ROI lies fully inside the crop with >= MIN_EDGE_MARGIN_PX
                 on every side the frame allows; an ROI on the FRAME edge is
                 recorded (`roi_touches_frame_edge`) - no re-cut can add pixels
  brightness     mean luma of the ROI pixels >= DIM_FLOOR (dim views hide marks)
  clipping       fraction of ROI pixels at 0 or 255 <= CLIP_MAX
  contrast       p95 - p5 of ROI luma >= FLAT_FLOOR (a flat view shows nothing)

action: "judge" | "recut" (scale / margin - fixable by cutting again) |
"not_judgeable_from_pixels" (dim / clipped / flat, or more crops than the cap) -
the reviewer must SAY that instead of guessing. Crops per item are capped
(MAX_CROPS_PER_ITEM): more crops = more vision calls.
"""
from __future__ import annotations

import numpy as np

MIN_EDGE_MARGIN_PX = 16
PAD_PX = 48
DIM_FLOOR = 24.0        # mean ROI luma (0..255); below = a dim view
CLIP_MAX = 0.25         # fraction of ROI pixels at 0 or 255
FLAT_FLOOR = 4.0        # p95 - p5 ROI luma; the faintest rejected residue is ~4 levels
MAX_CROPS_PER_ITEM = 4
MAX_CROP_W = 1600       # one 1:1 crop wider than this is tiled


def _clamp_box(frame, box):
    w, h = frame
    x0, y0, x1, y1 = (int(round(v)) for v in box)
    return (max(0, x0), max(0, y0), min(w, x1), min(h, y1))


def recut(frame_size, roi, pad=PAD_PX):
    """A 1:1 crop box holding `roi` with `pad` px of context, clamped to frame."""
    m = max(pad, MIN_EDGE_MARGIN_PX)
    return _clamp_box(frame_size, (roi[0] - m, roi[1] - m, roi[2] + m, roi[3] + m))


def plan_crops(frame_size, roi, max_w=MAX_CROP_W, cap=MAX_CROPS_PER_ITEM):
    """1:1 crops covering `roi`: one crop, or horizontal tiles of <= max_w when
    the ROI is wider. Over the cap -> not judgeable from pixels."""
    x0, y0, x1, y1 = (int(v) for v in roi)
    width = x1 - x0
    n = max(1, -(-width // max_w))
    if n > cap or (y1 - y0) > max_w:
        return {"crops": [], "action": "not_judgeable_from_pixels",
                "reason": f"needs {n} crops at 1:1 (cap {cap})"}
    step = -(-width // n)
    crops = [recut(frame_size, (x0 + i * step, y0, min(x1, x0 + (i + 1) * step), y1))
             for i in range(n)]
    return {"crops": crops, "action": "judge", "reason": ""}


def check_crop(frame_size, crop, roi, out_size, gray):
    """Reviewability record for one crop. `gray` is the ROI's luma (any 2D
    array of the ROI pixels at 1:1); `out_size` is what the reviewer is shown."""
    cw, ch = crop[2] - crop[0], crop[3] - crop[1]
    reasons, action = [], "judge"
    scale = round(min(out_size[0] / max(1, cw), out_size[1] / max(1, ch)), 4)
    if scale < 1.0:
        reasons.append(f"downscaled x{scale:g} - residue cannot be judged from a "
                       "shrunken crop")
        action = "recut"
    elif scale > 1.0:
        reasons.append(f"resampled x{scale:g} - not 1:1")
        action = "recut"
    fw, fh = frame_size
    on_frame_edge = roi[0] <= 0 or roi[1] <= 0 or roi[2] >= fw or roi[3] >= fh
    margins = {"left": roi[0] - crop[0], "top": roi[1] - crop[1],
               "right": crop[2] - roi[2], "bottom": crop[3] - roi[3]}
    frame_limited = {"left": roi[0] <= MIN_EDGE_MARGIN_PX, "top": roi[1] <= MIN_EDGE_MARGIN_PX,
                     "right": roi[2] >= fw - MIN_EDGE_MARGIN_PX,
                     "bottom": roi[3] >= fh - MIN_EDGE_MARGIN_PX}
    short = [k for k, v in margins.items() if v < MIN_EDGE_MARGIN_PX and not frame_limited[k]]
    if short:
        reasons.append(f"ROI at the crop edge ({', '.join(short)}) - contact with the "
                       "edge hides whether the mark continues")
        action = "recut"
    g = np.asarray(gray, dtype=np.float64)
    bright = float(g.mean()) if g.size else 0.0
    clipped = float(np.count_nonzero((g <= 0.5) | (g >= 254.5))) / max(1, g.size)
    contrast = float(np.percentile(g, 95) - np.percentile(g, 5)) if g.size else 0.0
    pixel_reasons = []
    if bright < DIM_FLOOR:
        pixel_reasons.append(f"dim: ROI mean luma {bright:.1f} < {DIM_FLOOR:g}")
    if clipped > CLIP_MAX:
        pixel_reasons.append(f"clipped: {clipped:.0%} of ROI pixels at 0/255")
    if contrast < FLAT_FLOOR:
        pixel_reasons.append(f"flat: ROI contrast {contrast:.1f} < {FLAT_FLOOR:g} levels")
    if pixel_reasons:
        reasons += pixel_reasons
        if action == "judge":
            action = "not_judgeable_from_pixels"
    return {"crop": [int(v) for v in crop], "roi": [int(v) for v in roi],
            "scale": float(scale), "margins": {k: int(v) for k, v in margins.items()},
            "roi_touches_frame_edge": bool(on_frame_edge),
            "brightness": round(bright, 2), "clipped_frac": round(clipped, 4),
            "contrast": round(contrast, 2), "reasons": reasons,
            "judgeable": action == "judge", "action": action}
