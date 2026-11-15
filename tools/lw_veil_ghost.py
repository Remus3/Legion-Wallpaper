"""Edge-ghost metric for the DA logo veil border (pass 2, 2026-11-15).

What it measures: after a de-veil, the logo's OUTLINE can survive as a faint
line - bright where the inversion under-removed the edge, dark where it
over-removed or left the halo, a bright/dark pair where the matte sits a
fraction of a pixel off. `edge_ghost` reads it on a candidate frame:

  1. signed distance (ref px) to the coverage's 0.5 contour, and the edge
     normal's octant;
  2. luma high-pass (box, HP_REF ref px half-width);
  3. smooth-art weight 1 / (art energy + C0), the art energy read OFF the
     +-4 ref px band so a ghost does not down-weight itself;
  4. per octant (one carrying at least OCT_MIN of the edge) and per side bin
     (outer -5..-2.5, out -2.5..0, in 0..1.5, inner 1.5..3.5 ref px), the
     WEIGHTED MEDIAN of the high-pass - a coherent outline survives the
     median, a crossing art line does not;
  5. `line_rms` = RMS over those cells (levels): the gated number.

`halo` (low-pass offset 4-12 ref px outside vs a 16-30 ref px annulus) is
reported for information only: on 30 veil-free frames its |value| reaches
p95 4.3 levels on art alone, so it cannot gate.

Validation (docs/_archive/2026-11/VEIL_PASS2_2026-11-15.md): purchased pairs
A/B/C upscaled through the real first-pass chain give a ground-truth clean
frame at 2560; candidates with injected edge errors (shift 0-3 px, offset
+-2 px, halo 0-100 percent left, blur 0-3 px) rank by `line_rms` as they rank
by the true band RMS error (Spearman 0.92 / 0.98 / 0.95 over all 23
candidates per pair, 1.0 within most families). Noise floor on 30 veil-free
frames at the default registration: median 0.19, p95 2.0, max 6.4 (strong
ink lines along the logo's edge directions) -> GHOST_LINE_GATE 2.0.

Independence: this reads the OUTPUT frame's high-pass along the contour. The
pass-2 fix (`lw_clean_overlay.fit_pair_edge`) fits a planar-art window model
to the INPUT frame. This module never calls the fit (pinned by a test).
"""
from __future__ import annotations

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lw_clean_overlay as OV  # noqa: E402
from lw_clean_pass import _box_mean  # noqa: E402

HP_REF = 3.0           # ref px half-width of the high-pass box
ART_REF = 12.0         # ref px half-width of the art-energy window
C0 = 4.0               # art-energy floor (levels^2) of the smooth-art weight
REACH_REF = 40.0       # ref px around the logo that is read
OCT_MIN = 0.06         # an octant must carry this share of the edge pixels
BINS = (("outer", -5.0, -2.5), ("out", -2.5, 0.0), ("in", 0.0, 1.5),
        ("inner", 1.5, 3.5))
GHOST_LINE_GATE = 2.0  # levels; veil-free floor p95 (see the module doc)


def _masked_mean(a, m, k):
    m = m.astype(np.float64)
    return _box_mean(a * m, k) / np.maximum(_box_mean(m, k), 1e-6)


def _wmedian(v, w):
    order = np.argsort(v)
    cw = np.cumsum(w[order])
    return float(v[order][np.searchsorted(cw, cw[-1] / 2.0)])


def edge_ghost(image, coverage):
    """{"line_rms", "line_mean", "line", "halo"} for one frame, or None.

    `coverage` is the pair matte where the inversion put it (registered, full
    frame). None when it has no logo (nothing to read).
    """
    cov_full = np.asarray(coverage, dtype=np.float64)
    if not (cov_full >= 0.5).any():
        return None
    g_full = np.asarray(image, dtype=np.float64)
    g_full = g_full.mean(axis=2) if g_full.ndim == 3 else g_full
    fw = cov_full.shape[1]

    def rp(n):
        return OV._ref_px(n, fw)
    y0, y1, x0, x1 = OV._crop_box(cov_full > 0, rp(REACH_REF), cov_full.shape)
    cov = cov_full[y0:y1, x0:x1]
    g = g_full[y0:y1, x0:x1]
    core = cov >= 0.5
    sc = float(OV.PAIR_REF[0]) / float(fw)
    cap = REACH_REF / sc + 2.0
    sd = np.where(core, OV._edt_capped(~core, cap) - 0.5,
                  -(OV._edt_capped(core, cap) - 0.5)) * sc
    gy, gx = np.gradient(_box_mean(cov, 2 * rp(2) + 1))
    has = np.hypot(gy, gx) > 1e-4
    octant = np.round((np.degrees(np.arctan2(gy, gx)) % 360.0) / 45.0).astype(int) % 8
    hp = g - _box_mean(g, 2 * rp(HP_REF) + 1)
    band = (sd > -4.0) & (sd < 4.0)
    art = _masked_mean(hp * hp, ~band, 2 * rp(ART_REF) + 1)
    wgt = 1.0 / (art + C0)
    cells = {}
    ntot = int(has.sum())
    for o in range(8):
        so = has & (octant == o)
        if so.sum() < OCT_MIN * ntot:
            continue
        for name, lo, hi in BINS:
            m = so & (sd >= lo) & (sd < hi)
            if m.sum() < 15:
                continue
            cells[f"{o}{name}"] = round(_wmedian(hp[m], wgt[m]), 3)
    vals = np.asarray(list(cells.values()), dtype=np.float64)
    lp = _box_mean(g, 2 * rp(1.5) + 1)
    bg = _masked_mean(g, (sd < -16.0) & (sd >= -30.0), 2 * rp(16) + 1)
    hm = (sd >= -12.0) & (sd < -4.0)
    halo = _wmedian((lp - bg)[hm], wgt[hm]) if hm.any() else 0.0
    return {"line_rms": round(float(np.sqrt(np.mean(vals ** 2))) if vals.size else 0.0, 3),
            "line_mean": round(float(np.mean(vals)) if vals.size else 0.0, 3),
            "line": cells, "halo": round(float(halo), 3)}


def ghost_ok(result, gate=GHOST_LINE_GATE):
    """Gate verdict: True when the line ghost is within the veil-free floor."""
    return result is not None and float(result["line_rms"]) <= float(gate)
