"""Build the pass-4 STATIC ALPHA FIELD of the DA logo pair matte.

Input: purchased pairs pushed through the real first-pass chain at the lane's
resolution (pass 2 wrote them to
images/_veil_pairs/2026-11-15/pass2/truth/{A,B,C}_{veiled,clean}_up.png).
Per pair: the lane's pass-3 registration (template + pair search, fine
scale), alpha fit and static edge correction, then the TRUE fill alpha per
matte-grid cell read against the clean frame
(`lw_clean_overlay.pair_true_alpha_sums`), after a 3x3 + offset colour match
of the clean frame to the veiled one OUTSIDE the logo (pair A's purchased
file is a slightly different grade). The pooled field
(`build_pair_alpha_field`) is written to
`lw_clean_overlay.PAIR_ALPHA_FIELD_PATH` (gitignored, numbers only).

Build it from A + B only so C stays held out
(docs/_archive/2026-11/VEIL_PASS4_2026-11-15.md).

Usage:
  python tools/lw_veil_alpha_field.py --pair A_veiled_up.png A_clean_up.png \
      --pair B_veiled_up.png B_clean_up.png [--out PATH]
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lw_clean_iopaint as IO  # noqa: E402
import lw_clean_overlay as OV  # noqa: E402

INTERIOR_REF = 4.0     # ref px inside the edge: past the edge ramp
EXCLUDE_REF = 60.0     # ref px around the logo kept out of the colour match


def _rgb(path):
    with Image.open(path) as im:
        return np.asarray(im.convert("RGB")).astype(np.float64)


def colour_match(clean, veiled, exclude, iters=3):
    """`clean` mapped onto `veiled`'s grade: 3x3 + offset, least squares
    outside `exclude`, the worst 15 percent dropped per round."""
    m = ~np.asarray(exclude, dtype=bool)
    x = np.concatenate([clean[m], np.ones((int(m.sum()), 1))], 1)
    y = veiled[m]
    keep = np.ones(len(x), dtype=bool)
    sol = None
    for _ in range(int(iters)):
        sol, *_r = np.linalg.lstsq(x[keep][::7], y[keep][::7], rcond=None)
        r = np.abs(x @ sol - y).max(1)
        keep = r < max(float(np.percentile(r, 85)), 3.0)
    flat = np.concatenate([clean.reshape(-1, 3),
                           np.ones((clean.shape[0] * clean.shape[1], 1))], 1)
    return (flat @ sol).reshape(clean.shape), sol


def pair_sums(veiled, clean, pm, tpl, corr):
    """(num, den, alpha_fit) for one truth pair, plus its registration."""
    _s, dy, dx, sc = OV.best_registration(veiled, tpl)
    reg = IO.pair_registration(veiled, pm, (dy, dx), sc)
    rs = OV.refine_pair_scale(veiled, pm, shift=reg["shift"], scale=reg["scale"],
                              centre=reg["centre"])
    shift, scale, centre = rs["shift"], rs["scale"], reg["centre"]
    cov = OV.register_pair_matte(veiled.shape[:2], pm, shift=shift, scale=scale,
                                 centre=centre)
    alpha = float(OV.fit_pair_alpha(veiled, cov, pm)["alpha"])
    geom = OV.pair_signed_distance(veiled.shape[:2], pm, shift=shift,
                                   scale=scale, centre=centre, edge_corr=corr)
    h, w = veiled.shape[:2]
    sd = np.full((h, w), -1e9)
    y0, y1, x0, x1 = geom["box"]
    sd[y0:y1, x0:x1] = geom["sd"] * float(OV.PAIR_REF[0]) / float(w)
    excl = sd > -EXCLUDE_REF
    ys, xs = np.nonzero(sd > 0)
    # the credit line sits below the logo: keep it out of the colour match
    excl[ys.max(): min(ys.max() + int(0.06 * h), h),
         max(xs.min() - 50, 0): xs.max() + 50] = True
    matched, _sol = colour_match(clean, veiled, excl)
    num, den = OV.pair_true_alpha_sums(veiled, matched, sd > INTERIOR_REF,
                                       veiled.shape[:2], pm, shift=shift,
                                       scale=scale, centre=centre)
    return (num, den, alpha), {"alpha": round(alpha, 5), "scale": scale,
                               "shift": [float(shift[0]), float(shift[1])]}


def main(argv=None):
    ap = argparse.ArgumentParser(prog="lw_veil_alpha_field")
    ap.add_argument("--pair", nargs=2, action="append", required=True,
                    metavar=("VEILED_UP", "CLEAN_UP"))
    ap.add_argument("--out", default=OV.PAIR_ALPHA_FIELD_PATH)
    ap.add_argument("--corr", default=OV.PAIR_EDGE_CORR_PATH,
                    help="static edge correction the lane uses (pass 3)")
    args = ap.parse_args(argv)
    pm = OV.load_pair_matte()
    tpl, _matte = IO.load_overlay_pair()
    corr = OV.load_pair_edge_corr(args.corr)
    if pm is None or not tpl or corr is None:
        print("no pair matte / template / edge correction cached", file=sys.stderr)
        return 2
    frames, info = [], []
    for vp, cp in args.pair:
        f, meta = pair_sums(_rgb(vp), _rgb(cp), pm, tpl, corr["grid"])
        frames.append(f)
        info.append(dict(meta, veiled=os.path.basename(vp)))
    logo = np.asarray(pm["shape"], dtype=np.float64) > 0.5
    grid, binfo = OV.build_pair_alpha_field(frames, logo)
    OV.save_pair_alpha_field(args.out, grid,
                             sources=",".join(i["veiled"] for i in info),
                             n_frames=len(frames), kappa=binfo["kappa_mean"])
    print(json.dumps({"out": args.out, "pairs": info, **binfo}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
