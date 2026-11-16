"""Low-frequency shading metric for the DA logo veil interior (pass 4).

What it measures: after a de-veil, the logo's INTERIOR can differ from its
surroundings at low frequency - a "patch" brighter or darker, washed out or
over-saturated, than the art around it, and differently so at the top and
the foot when the veil's alpha varies across the logo. `boundary_step`
reads that on a candidate frame alone:

  1. signed distance (ref px) to the coverage's 0.5 contour;
  2. windows along the contour (every STEP_REF ref px); in each, the pixels
     of an INSIDE band (IN_BAND ref px: past the edge ramp and the LaMa
     ring) and an OUTSIDE band (OUT_BAND: past the dark halo) within
     WIN_REF ref px of the window centre;
  3. per CIELAB channel a least-squares plane (art gradient) plus a step
     term for "inside" - the step is the low-frequency difference the plane
     cannot explain;
  4. smooth-art weight 1 / (residual variance + C0): busy art says little;
  5. the logo is split into THIRDS by height; per third the weighted median
     step (dL, da, db); `step_de_rms` = RMS over the thirds of the step's
     Euclidean length (deltaE76 units) - the gated number - and `spread_L`
     = max - min of dL over the thirds (top-to-foot shading).

Validation (docs/_archive/2026-11/VEIL_PASS4_2026-11-15.md): candidates with
injected alpha errors (scale 0.85-1.15, a top-to-foot gradient of either
sign) on the purchased pairs at 2560 rank by `step_de_rms` as they rank by
the true low-frequency deltaE against the clean frame.

Independence: reads the OUTPUT frame and the coverage only. It never calls
the alpha fit or the alpha field (pinned by a test).
"""
from __future__ import annotations

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lw_clean_overlay as OV  # noqa: E402

IN_BAND = (3.0, 12.0)       # ref px inside the contour: past the LaMa ring
OUT_BAND = (-12.0, -4.0)    # ref px outside: past the LaMa ring
WIN_REF = 16.0              # ref px radius of a window
STEP_REF = 8.0              # ref px between window centres along the contour
C0 = 4.0                    # deltaE^2 floor of the smooth-art weight
MIN_PX = 40                 # pixels each band needs in a window
SHADING_GATE = 3.2          # deltaE76: veil-free floor p95 (30 frames; see the doc)


def srgb_to_lab(rgb):
    """CIELAB (D65) of an sRGB uint8 / float array in 0..255."""
    v = np.clip(np.asarray(rgb, dtype=np.float64), 0.0, 255.0) / 255.0
    lin = np.where(v <= 0.04045, v / 12.92, ((v + 0.055) / 1.055) ** 2.4)
    m = np.array([[0.4124564, 0.3575761, 0.1804375],
                  [0.2126729, 0.7151522, 0.0721750],
                  [0.0193339, 0.1191920, 0.9503041]])
    xyz = lin @ m.T / np.array([0.95047, 1.0, 1.08883])
    f = np.where(xyz > 216.0 / 24389.0, np.cbrt(xyz),
                 (24389.0 / 27.0 * xyz + 16.0) / 116.0)
    return np.stack([116.0 * f[..., 1] - 16.0,
                     500.0 * (f[..., 0] - f[..., 1]),
                     200.0 * (f[..., 1] - f[..., 2])], axis=-1)


def _wmedian(v, w):
    order = np.argsort(v)
    cw = np.cumsum(w[order])
    return float(v[order][np.searchsorted(cw, cw[-1] / 2.0)])


def boundary_step(image, coverage):
    """{"step_de_rms", "spread_L", "thirds": [[dL, da, db], ...], "windows"}
    for one frame, or None when the coverage has no logo."""
    cov_full = np.asarray(coverage, dtype=np.float64)
    if not (cov_full >= 0.5).any():
        return None
    fw = cov_full.shape[1]
    sc = float(OV.PAIR_REF[0]) / float(fw)
    reach = OV._ref_px(-OUT_BAND[0] + WIN_REF + 4.0, fw)
    y0, y1, x0, x1 = OV._crop_box(cov_full > 0, reach, cov_full.shape)
    cov = cov_full[y0:y1, x0:x1]
    core = cov >= 0.5
    cap = (-OUT_BAND[0] + 4.0) / sc
    sd = np.where(core, OV._edt_capped(~core, cap) - 0.5,
                  -(OV._edt_capped(core, cap) - 0.5)) * sc
    lab = srgb_to_lab(np.asarray(image)[y0:y1, x0:x1, :3])
    ins = (sd >= IN_BAND[0]) & (sd < IN_BAND[1])
    outs = (sd >= OUT_BAND[0]) & (sd < OUT_BAND[1])
    # the contour: logo pixels next to a non-logo pixel (sd = 0.5 frame px)
    cy, cx = np.nonzero(core & (sd < sc))
    if not len(cy):
        return None
    step = max(int(round(STEP_REF / sc)), 1)
    # one contour pixel per step x step cell
    cells = {}
    for yy, xx in zip(cy, cx, strict=True):
        cells.setdefault((yy // step, xx // step), (yy, xx))
    r = WIN_REF / sc
    ri = int(np.ceil(r))
    ly0, ly1 = np.nonzero(core)[0].min(), np.nonzero(core)[0].max()
    lh = max(ly1 - ly0, 1)
    rows = []
    for yy, xx in cells.values():
        a0, a1 = max(yy - ri, 0), min(yy + ri + 1, core.shape[0])
        b0, b1 = max(xx - ri, 0), min(xx + ri + 1, core.shape[1])
        py, px = np.mgrid[a0:a1, b0:b1]
        disk = (py - yy) ** 2 + (px - xx) ** 2 <= r * r
        mi = disk & ins[a0:a1, b0:b1]
        mo = disk & outs[a0:a1, b0:b1]
        if mi.sum() < MIN_PX or mo.sum() < MIN_PX:
            continue
        m = mi | mo
        dsg = np.stack([np.ones(int(m.sum())), (py[m] - yy) / r, (px[m] - xx) / r,
                        mi[m].astype(np.float64)], axis=1)
        v = lab[a0:a1, b0:b1][m]
        sol, *_ = np.linalg.lstsq(dsg, v, rcond=None)
        res = v - dsg @ sol
        var = float(np.mean(res * res)) * 3.0
        rows.append((yy, sol[3], 1.0 / (var + C0)))
    if len(rows) < 6:
        return None
    ys = np.array([t[0] for t in rows], dtype=np.float64)
    st = np.array([t[1] for t in rows])
    wt = np.array([t[2] for t in rows])
    thirds = []
    for k in range(3):
        lo = ly0 + k * lh / 3.0
        hi = ly0 + (k + 1) * lh / 3.0 + (1 if k == 2 else 0)
        m = (ys >= lo) & (ys < hi)
        if m.sum() < 2:
            thirds.append(None)
            continue
        thirds.append([round(_wmedian(st[m, c], wt[m]), 3) for c in range(3)])
    got = [t for t in thirds if t is not None]
    mag = [float(np.sqrt(sum(c * c for c in t))) for t in got]
    dl = [t[0] for t in got]
    return {"step_de_rms": round(float(np.sqrt(np.mean(np.square(mag)))), 3),
            "spread_L": round(float(max(dl) - min(dl)), 3),
            "thirds": thirds, "windows": len(rows)}


def shading_ok(result, gate=SHADING_GATE):
    """Gate verdict: True when the interior step is within the floor."""
    return result is not None and float(result["step_de_rms"]) <= float(gate)
