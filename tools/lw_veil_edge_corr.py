"""Build the pass-3 STATIC edge correction of the DA logo pair matte.

Input: purchased pairs pushed through the real first-pass chain at the lane's
resolution (veiled -> 2560 and registered clean -> 2560; pass 2 wrote them to
images/_veil_pairs/2026-11-15/pass2/truth/{A,B,C}_{veiled,clean}_up.png). Per
pair: the lane's registration, alpha fit and edge fit (no per-frame offsets),
then the TRUE residual edge offset at every contour pixel read against the
clean frame (`lw_clean_overlay.pair_true_edge_offsets`), mapped to the matte
grid. The pooled field is written to `lw_clean_overlay.PAIR_EDGE_CORR_PATH`
(gitignored, numbers only: a derivative of the third-party mark's shape).

`--loo` also prints, per pair, how well the field from the OTHER pairs
predicts its own (the field is ~85 percent static on A/B/C: leave-one-out
correlation 0.84-0.89; docs/_archive/2026-11/VEIL_PASS3_2026-11-15.md).

Usage:
  python tools/lw_veil_edge_corr.py --pair A_veiled_up.png A_clean_up.png \
      --pair B_veiled_up.png B_clean_up.png [--loo] [--out PATH]
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


def _rgb(path):
    with Image.open(path) as im:
        return np.asarray(im.convert("RGB")).astype(np.float64)


def pair_samples(veiled, clean, pm, tpl):
    """(gy, gx, v_ref) for one truth pair, plus the fit it was read against."""
    _s, dy, dx, sc = OV.best_registration(veiled, tpl)
    reg = IO.pair_registration(veiled, pm, (dy, dx), sc)
    # the lane refines the scale in pass 3; the field is learned the same way
    rs = OV.refine_pair_scale(veiled, pm, shift=reg["shift"], scale=reg["scale"],
                              centre=reg["centre"])
    reg = dict(reg, shift=rs["shift"], scale=rs["scale"],
               cov=OV.register_pair_matte(veiled.shape[:2], pm, shift=rs["shift"],
                                          scale=rs["scale"], centre=reg["centre"]))
    alpha = float(OV.fit_pair_alpha(veiled, reg["cov"], pm)["alpha"])
    geom = OV.pair_signed_distance(veiled.shape[:2], pm, shift=reg["shift"],
                                   scale=reg["scale"], centre=reg["centre"])
    theta = OV.fit_pair_edge(veiled, geom, pm, alpha)["theta"]
    got = OV.pair_true_edge_offsets(veiled, clean, geom, pm, alpha, theta)
    gy, gx = OV.pair_grid_coords(got["ys"], got["xs"], veiled.shape[:2], pm,
                                 shift=reg["shift"], scale=reg["scale"],
                                 centre=reg["centre"])
    v_ref = got["v"] * float(OV.PAIR_REF[0]) / float(veiled.shape[1]) / float(reg["scale"])
    return (gy, gx, v_ref), {"alpha": round(alpha, 4), "theta": theta,
                             "scale": rs["scale"], "n": int(len(v_ref))}


def loo_report(samples, shape):
    """Per pair: correlation and rms of its own pooled field vs the others'."""
    out = []
    for i, (gy, gx, v) in enumerate(samples):
        own = OV.build_pair_edge_corr([samples[i]], shape, fill=0)
        rest = OV.build_pair_edge_corr([s for j, s in enumerate(samples) if j != i],
                                       shape, fill=0)
        iy = np.clip(np.rint(gy).astype(int), 0, shape[0] - 1)
        ix = np.clip(np.rint(gx).astype(int), 0, shape[1] - 1)
        a, b = own[iy, ix], rest[iy, ix]
        m = (b != 0) & (a != 0)
        out.append({"pair": i, "n": int(m.sum()),
                    "corr": round(float(np.corrcoef(a[m], b[m])[0, 1]), 3) if m.sum() > 2 else None,
                    "rms_own": round(float(np.std(a[m])), 3) if m.any() else None,
                    "rms_diff": round(float(np.sqrt(np.mean((a[m] - b[m]) ** 2))), 3) if m.any() else None})
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(prog="lw_veil_edge_corr")
    ap.add_argument("--pair", nargs=2, action="append", required=True,
                    metavar=("VEILED_UP", "CLEAN_UP"))
    ap.add_argument("--out", default=OV.PAIR_EDGE_CORR_PATH)
    ap.add_argument("--sources", default="")
    ap.add_argument("--loo", action="store_true")
    args = ap.parse_args(argv)
    pm = OV.load_pair_matte()
    tpl, _matte = IO.load_overlay_pair()
    if pm is None or not tpl:
        print("no pair matte / template cached", file=sys.stderr)
        return 2
    samples, info = [], []
    for vp, cp in args.pair:
        s, meta = pair_samples(_rgb(vp), _rgb(cp), pm, tpl)
        samples.append(s)
        info.append(dict(meta, veiled=os.path.basename(vp)))
    shape = np.asarray(pm["shape"]).shape
    grid = OV.build_pair_edge_corr(samples, shape)
    OV.save_pair_edge_corr(args.out, grid, sources=args.sources or
                           ",".join(i["veiled"] for i in info),
                           n_frames=len(samples))
    rep = {"out": args.out, "pairs": info,
           "grid_p10_p50_p90": [round(float(v), 3) for v in
                                np.percentile(grid[grid != 0], (10, 50, 90))]}
    if args.loo and len(samples) > 1:
        rep["loo"] = loo_report(samples, shape)
    print(json.dumps(rep, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
