"""Ring hue metric for the DA logo veil border (pass 5, 2026-11-15).

What it measures: after a de-veil the band ON the logo's contour (the LaMa
ring and the edge the inversion touched) can carry a colour cast its two
sides do not have - pass 4 left a green deficit of 1-2 levels there on all
three purchased pairs (a magenta outline on plain background), the
operator's "hue mismatch at the veil edge". `ring_hue_step` reads it on an
OUTPUT frame and the coverage only:

  1. signed distance (ref px) to the coverage's 0.5 contour;
  2. per window (every STEP_REF ref px along the contour, radius WIN_REF):
     CIELAB a*, b* (and L*) of the flank bands FLANK_OUT and FLANK_IN, a
     plane fitted to them (the art's colour gradient), and the weighted
     median of the RING band's departure from that plane;
  3. smooth-art weight 1 / (flank residual variance + C0);
  4. per octant of the contour normal the weighted median of the windows'
     (da, db); `ring_de` = RMS over octants of sqrt(da^2 + db^2) (deltaE76
     units, chroma only); `ring_dl` the same for L* (reported).

Independence: reads the output frame and the coverage. It never calls the
pass-5 fixes (`lw_veil_pass5`), pinned by a test.

Validation and the gate's floor: docs/_archive/2026-11/VEIL_PASS5_2026-11-15.md.
"""
from __future__ import annotations

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lw_clean_overlay as OV  # noqa: E402
from lw_veil_shading import _wmedian, srgb_to_lab  # noqa: E402

RING = (-4.0, 3.0)          # ref px: the LaMa ring and the edge
FLANK_OUT = (-10.0, -5.0)   # ref px outside the ring
FLANK_IN = (4.0, 10.0)      # ref px inside the ring
WIN_REF = 14.0              # ref px radius of a window
STEP_REF = 8.0              # ref px between window centres
C0 = 1.0                    # chroma^2 floor of the smooth-art weight
MIN_PX = 20                 # pixels each band needs in a window
HUE_GATE = 2.4              # deltaE76 (chroma): veil-free floor p95 2.35 (30 frames)


def ring_hue_step(image, coverage):
    """{"ring_de", "ring_dl", "octants", "windows"} or None (no logo)."""
    cov_full = np.asarray(coverage, dtype=np.float64)
    if not (cov_full >= 0.5).any():
        return None
    fw = cov_full.shape[1]
    sc = float(OV.PAIR_REF[0]) / float(fw)
    reach = OV._ref_px(-FLANK_OUT[0] + WIN_REF + 4.0, fw)
    y0, y1, x0, x1 = OV._crop_box(cov_full > 0, reach, cov_full.shape)
    cov = cov_full[y0:y1, x0:x1]
    core = cov >= 0.5
    cap = (-FLANK_OUT[0] + 4.0) / sc
    sd = np.where(core, OV._edt_capped(~core, cap) - 0.5,
                  -(OV._edt_capped(core, cap) - 0.5)) * sc
    lab = srgb_to_lab(np.asarray(image)[y0:y1, x0:x1, :3])
    ring = (sd >= RING[0]) & (sd < RING[1])
    flank = (((sd >= FLANK_OUT[0]) & (sd < FLANK_OUT[1]))
             | ((sd >= FLANK_IN[0]) & (sd < FLANK_IN[1])))
    cy, cx = np.nonzero(core & (sd < sc))
    if not len(cy):
        return None
    gy, gx = np.gradient(np.clip(sd, -cap * sc, cap * sc))
    octant = (np.round(np.arctan2(gy, gx) / (np.pi / 4.0)).astype(int)) % 8
    step = max(int(round(STEP_REF / sc)), 1)
    cells = {}
    for yy, xx in zip(cy, cx, strict=True):
        cells.setdefault((yy // step, xx // step), (yy, xx))
    r = WIN_REF / sc
    ri = int(np.ceil(r))
    rows = []
    for yy, xx in cells.values():
        a0, a1 = max(yy - ri, 0), min(yy + ri + 1, core.shape[0])
        b0, b1 = max(xx - ri, 0), min(xx + ri + 1, core.shape[1])
        py, px = np.mgrid[a0:a1, b0:b1]
        disk = (py - yy) ** 2 + (px - xx) ** 2 <= r * r
        mr = disk & ring[a0:a1, b0:b1]
        mf = disk & flank[a0:a1, b0:b1]
        if mr.sum() < MIN_PX or mf.sum() < 2 * MIN_PX:
            continue
        dsg = np.stack([np.ones(int(mf.sum())), (py[mf] - yy) / r,
                        (px[mf] - xx) / r], axis=1)
        v = lab[a0:a1, b0:b1][mf]
        sol, *_ = np.linalg.lstsq(dsg, v, rcond=None)
        res = v - dsg @ sol
        var = float(np.mean(res[:, 1:] ** 2)) * 2.0
        dr = np.stack([np.ones(int(mr.sum())), (py[mr] - yy) / r,
                       (px[mr] - xx) / r], axis=1)
        dep = lab[a0:a1, b0:b1][mr] - dr @ sol
        ones = np.ones(len(dep))
        rows.append((int(octant[yy, xx]),
                     [_wmedian(dep[:, c], ones) for c in range(3)],
                     1.0 / (var + C0)))
    if len(rows) < 6:
        return None
    oc = np.array([t[0] for t in rows])
    st = np.array([t[1] for t in rows])
    wt = np.array([t[2] for t in rows])
    mags, dls = [], []
    for k in range(8):
        m = oc == k
        if m.sum() < 3:
            continue
        da, db = (_wmedian(st[m, c], wt[m]) for c in (1, 2))
        mags.append(da * da + db * db)
        dls.append(_wmedian(st[m, 0], wt[m]))
    if not mags:
        return None
    return {"ring_de": round(float(np.sqrt(np.mean(mags))), 3),
            "ring_dl": round(float(np.sqrt(np.mean(np.square(dls)))), 3),
            "octants": len(mags), "windows": len(rows)}


def hue_ok(result, gate=HUE_GATE):
    """Gate verdict: True when the ring's colour cast is within the floor."""
    return result is not None and float(result["ring_de"]) <= float(gate)
