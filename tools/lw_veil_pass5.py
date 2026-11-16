"""Pass-5 seam and hue fixes for the DA logo veil lane (2026-11-15).

Operator review of pass 4 (docs/_archive/2026-11/VEIL_PASS5_2026-11-15.md):
the credit line's bottom edge smudges; faint ghost lines still follow the
logo's border; where the veil edge sits on plain background the colour is not
blended out (a hue step). Measured on the purchased pairs A / B / C through
the real first-pass chain (C held out) and on the named slugs:

- the credit text box (pass 4: 0.055-0.135 logo heights under the logo,
  half-width >= 0.40) is too short and too narrow for the BIG-font credit
  lines (glyphs to 0.137, drop shadow to ~0.145, "(c)" at ~0.72 logo heights
  from the centre): LaMa then extends the cut glyph bottoms and the "(c)"
  into the box. -> `CREDIT_ROWS` / `CREDIT_HALF` for
  `lw_veil_credit.locate_credit(rows=, half=)`.
- LaMa's fill of the edge ring (and of the credit box) comes back with a
  level / colour step at its seams: a GREEN deficit of 1-2 levels on all
  three pairs (a magenta outline) that the pre-pass does not have. ->
  `membrane_fill`: out = fill + c, c harmonic inside the fill, its boundary
  value the (capped, art-edge down-weighted, boundary-smoothed) step between
  the outside pixel and the fill next to it. It adds a smooth field only.
- a thin profile (bright / dark line pair, +-5 frame px) survives along the
  contour. -> `contour_profile_fix`: per 32 px cell, quadratic art + a tent
  profile p(d) of the signed distance, smooth-art weighted, robust; across
  neighbouring cells a median keeps only what is COHERENT along the
  contour; capped at PROFILE_CAP levels; subtracted.

Held out on C (hyper-parameters chosen on A + B): edge band +-3 ref px
31.78 -> 32.06 dB, ring deltaE76 3.04 -> 2.59, the ring's a*/b* bias
+0.79 / -0.67 -> +0.05 / +0.21. Tried and rejected (truth worse): a local
halo-gain refit, an interior boundary harmonization, an octant profile
against a linear art trend, a wide (+-9 px) profile.

Pure numpy; scipy.ndimage is imported lazily (EDT, filters).
"""
from __future__ import annotations

import numpy as np

# credit line box (logo heights): rows under the logo's foot, half-width bounds
CREDIT_ROWS = (0.050, 0.160)
CREDIT_HALF = (0.78, 1.10)

# membrane seam correction
MEMBRANE_SMOOTH = 4          # px half-window along the boundary
MEMBRANE_CAP = 6.0           # levels: a larger step is art, not drift
MEMBRANE_ITERS = 400
MEMBRANE_REACH = 12.0        # frame px from the contour: the ring part of the mask

# contour profile subtraction
PROFILE_KNOTS = (-5.0, -4.0, -3.0, -2.0, -1.0, 0.0, 1.0, 2.0, 3.0, 4.0, 5.0)
PROFILE_REACH = 12.0         # frame px of the band a cell fits
PROFILE_CELL = 32            # frame px
PROFILE_LAM = 0.5            # second-difference penalty on the profile
PROFILE_CAP = 3.0            # levels
PROFILE_COH = 1.0            # levels a cell may differ from its neighbours' median
PROFILE_ITERS = 3            # IRLS rounds (Tukey)


def _ndi():
    from scipy import ndimage
    return ndimage


def signed_distance(cov, pad=24, up=4):
    """(sd, box): signed distance in frame px (+ inside) to the coverage's 0.5
    contour, sub-pixel via an EDT on a 4x bilinear upsample, over the logo's
    box grown by `pad`. None when the coverage is empty."""
    from PIL import Image
    ndi = _ndi()
    cov = np.asarray(cov, dtype=np.float32)
    ys, xs = np.nonzero(cov >= 0.5)
    if not len(ys):
        return None, None
    y0, y1 = max(int(ys.min()) - pad, 0), min(int(ys.max()) + pad + 1, cov.shape[0])
    x0, x1 = max(int(xs.min()) - pad, 0), min(int(xs.max()) + pad + 1, cov.shape[1])
    c = cov[y0:y1, x0:x1]
    h, w = c.shape
    cu = np.asarray(Image.fromarray(c).resize((w * up, h * up), Image.BILINEAR))
    ins = cu >= 0.5
    d = ndi.distance_transform_edt(ins) - ndi.distance_transform_edt(~ins)
    sd = d[up // 2::up, up // 2::up][:h, :w] / float(up)
    return sd, (y0, y1, x0, x1)


def membrane_fill(img, region, smooth=MEMBRANE_SMOOTH, cap=MEMBRANE_CAP,
                  iters=MEMBRANE_ITERS):
    """(out float, corr): the fill in `region` shifted by a harmonic field so
    it meets the pixels around it without a step. Pixels outside `region` are
    returned unchanged."""
    ndi = _ndi()
    img = np.asarray(img, dtype=np.float64)
    R = np.asarray(region, dtype=bool)
    corr_full = np.zeros(img.shape)
    if not R.any():
        return img.copy(), corr_full
    ys, xs = np.nonzero(R)
    pad = 2 * smooth + 2
    y0, y1 = max(ys.min() - pad, 0), min(ys.max() + pad + 1, R.shape[0])
    x0, x1 = max(xs.min() - pad, 0), min(xs.max() + pad + 1, R.shape[1])
    r = R[y0:y1, x0:x1]
    sub_img = img[y0:y1, x0:x1]
    bnd = ndi.binary_dilation(r, ndi.generate_binary_structure(2, 1)) & ~r
    _d, (iy, ix) = ndi.distance_transform_edt(~r, return_indices=True)
    diff = np.zeros(sub_img.shape)
    diff[bnd] = sub_img[bnd] - sub_img[iy[bnd], ix[bnd]]
    diff = np.clip(diff, -cap, cap)
    lum = sub_img.mean(axis=-1)
    g2 = ndi.uniform_filter(np.gradient(lum, axis=0) ** 2
                            + np.gradient(lum, axis=1) ** 2, 3)
    wb = bnd / (g2 + 4.0)                      # an art edge carries little weight
    k = 2 * smooth + 1
    wsum = ndi.uniform_filter(wb, k)
    dsm = np.stack([ndi.uniform_filter(diff[..., c] * wb, k)
                    for c in range(sub_img.shape[-1])], -1)
    dsm /= np.maximum(wsum, 1e-9)[..., None]
    c = np.zeros(sub_img.shape)
    c[bnd] = dsm[bnd]
    _d, (by, bx) = ndi.distance_transform_edt(~bnd, return_indices=True)
    c[r] = c[by[r], bx[r]]
    for _ in range(iters):
        nb = (np.roll(c, 1, 0) + np.roll(c, -1, 0)
              + np.roll(c, 1, 1) + np.roll(c, -1, 1)) / 4.0
        c = np.where(r[..., None], nb, c)
    out = img.copy()
    out[y0:y1, x0:x1][r] += c[r]
    corr_full[y0:y1, x0:x1][r] = c[r]
    return out, corr_full


def _tents(d, knots):
    kn = np.asarray(knots, dtype=np.float64)
    B = np.zeros((len(d), len(kn)))
    for k, t in enumerate(kn):
        lo = kn[k - 1] if k > 0 else t - 1.0
        hi = kn[k + 1] if k < len(kn) - 1 else t + 1.0
        left = (d >= lo) & (d <= t)
        right = (d > t) & (d <= hi)
        B[left, k] = (d[left] - lo) / (t - lo)
        B[right, k] = (hi - d[right]) / (hi - t)
    return B


def _fit_cells(img, sd, cell, lam, iters, knots):
    ndi = _ndi()
    h, w = sd.shape
    band = np.abs(sd) < PROFILE_REACH
    K = len(knots)
    D2 = np.zeros((K - 2, K))
    for i in range(K - 2):
        D2[i, i:i + 3] = (1.0, -2.0, 1.0)
    lum = img.mean(axis=-1)
    hp = lum - ndi.uniform_filter(lum, 7)
    en = ndi.uniform_filter(hp * hp, 15)
    pen = np.zeros((6 + K, 6 + K))
    pen[6:, 6:] = lam * D2.T @ D2 + 1e-3 * np.eye(K)
    cells = {}
    for cy in range(0, h, cell):
        for cx in range(0, w, cell):
            sl = (slice(max(cy - cell // 2, 0), min(cy + cell + cell // 2, h)),
                  slice(max(cx - cell // 2, 0), min(cx + cell + cell // 2, w)))
            m = band[sl]
            if m.sum() < 150:
                continue
            d = sd[sl][m]
            if (d < -4).sum() < 30 or (d > 4).sum() < 30:
                continue
            yy, xx = np.nonzero(m)
            Y = (yy - yy.mean()) / cell
            X = (xx - xx.mean()) / cell
            A = np.concatenate([np.stack([np.ones_like(Y), Y, X, Y * Y, X * X, X * Y], 1),
                                _tents(d, knots)], 1)
            wa = 1.0 / (en[sl][m] + 4.0)
            prof = []
            for c in range(img.shape[-1]):
                v = img[sl][..., c][m]
                wr = np.ones_like(v)
                for _ in range(iters):
                    wt = wa * wr
                    atw = A.T * wt
                    sol = np.linalg.solve(atw @ A + pen * wt.mean(), atw @ v)
                    res = v - A @ sol
                    s = 1.4826 * np.median(np.abs(res)) + 0.5
                    u = res / (4.685 * s)
                    wr = np.where(np.abs(u) < 1.0, (1.0 - u * u) ** 2, 0.0)
                prof.append(sol[6:])
            cells[(cy // cell, cx // cell)] = np.array(prof)
    return cells


def contour_profile_fix(img, cov, allowed, cell=PROFILE_CELL, cap=PROFILE_CAP,
                        coh=PROFILE_COH, lam=PROFILE_LAM, iters=PROFILE_ITERS,
                        knots=PROFILE_KNOTS):
    """(uint8 out, info): subtract the contour-coherent profile of the signed
    distance from `img` on `allowed` pixels; every other pixel is returned
    byte for byte."""
    src = np.asarray(img)
    base = np.clip(np.rint(src), 0, 255).astype(np.uint8)
    sd, box = signed_distance(cov)
    if sd is None:
        return base, {"cells": 0}
    y0, y1, x0, x1 = box
    crop = base[y0:y1, x0:x1].astype(np.float64)
    cells = _fit_cells(crop, sd, cell, lam, iters, knots)
    if not cells:
        return base, {"cells": 0}
    h, w = sd.shape
    ny, nx = h // cell + 2, w // cell + 2
    nch, K = crop.shape[-1], len(knots)
    G = np.zeros((ny, nx, nch, K))
    M = np.zeros((ny, nx))
    for (i, j), p in cells.items():
        G[i, j] = np.clip(p, -cap, cap)
        M[i, j] = 1.0
    G2 = G.copy()
    for (i, j) in cells:
        nb = [G[a, b] for a in range(max(i - 1, 0), min(i + 2, ny))
              for b in range(max(j - 1, 0), min(j + 2, nx)) if M[a, b]]
        if len(nb) >= 3:
            med = np.median(np.array(nb), 0)
            G2[i, j] = np.where(np.abs(G[i, j] - med) <= coh, G[i, j], med)
    G = G2
    yy, xx = np.nonzero(np.abs(sd) < PROFILE_REACH)
    fy, fx = (yy - cell / 2.0) / cell, (xx - cell / 2.0) / cell
    iy = np.clip(np.floor(fy).astype(int), 0, ny - 2)
    ix = np.clip(np.floor(fx).astype(int), 0, nx - 2)
    ty, tx = np.clip(fy - iy, 0, 1), np.clip(fx - ix, 0, 1)
    B = _tents(sd[yy, xx], knots)
    corr = np.zeros((len(yy), nch))
    wsum = np.zeros(len(yy))
    for di, dj, wt in ((0, 0, (1 - ty) * (1 - tx)), (1, 0, ty * (1 - tx)),
                       (0, 1, (1 - ty) * tx), (1, 1, ty * tx)):
        ww = wt * M[iy + di, ix + dj]
        corr += ww[:, None] * np.einsum("nk,nck->nc", B, G[iy + di, ix + dj])
        wsum += ww
    corr /= np.maximum(wsum, 1e-9)[:, None]
    al = np.asarray(allowed, dtype=bool)[y0:y1, x0:x1][yy, xx]
    out = base.copy()
    sub = out[y0:y1, x0:x1]
    vals = crop[yy[al], xx[al]] - corr[al]
    sub[yy[al], xx[al]] = np.clip(np.rint(vals), 0, 255).astype(np.uint8)
    return out, {"cells": len(cells),
                 "corr_p99": round(float(np.percentile(np.abs(corr[al]), 99)), 3)
                 if al.any() else 0.0}


def seam_fix(frame, lama_mask, cov, allowed, credit_box=None):
    """The pass-5 post-LaMa step on a full uint8 frame (H, W, C).

    1. membrane on the ring part of the LaMa mask (within MEMBRANE_REACH of
       the contour); 2. membrane on the credit box's part of the mask, as its
       own region; 3. the contour profile subtraction on `allowed`.
    Only pixels of `lama_mask` (1, 2) and of `allowed` (3) can change.
    Returns (uint8 frame, info)."""
    arr = np.asarray(frame)
    lm = np.asarray(lama_mask, dtype=bool)
    sd, box = signed_distance(cov)
    info = {"membrane_px": 0}
    cur = arr.astype(np.float64)
    if sd is not None:
        near = np.zeros(lm.shape, dtype=bool)
        y0, y1, x0, x1 = box
        near[y0:y1, x0:x1] = np.abs(sd) < MEMBRANE_REACH
        ring = lm & near
        if credit_box is not None:
            ring &= ~np.asarray(credit_box, dtype=bool)
        cur, _c = membrane_fill(cur, ring)
        info["membrane_px"] = int(ring.sum())
    if credit_box is not None:
        cb = lm & np.asarray(credit_box, dtype=bool)
        cur, _c = membrane_fill(cur, cb)
        info["membrane_credit_px"] = int(cb.sum())
        info["membrane_px"] += int(cb.sum())
    cur = np.clip(np.rint(cur), 0, 255).astype(np.uint8)
    out, pinfo = contour_profile_fix(cur, cov, allowed)
    info["profile"] = pinfo
    return out, info
