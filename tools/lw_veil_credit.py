"""Pass-4 credit line lane for the DA logo veil ("(c) ARTIST.DEVIANTART.COM").

Measured on the purchased pairs through the real first-pass chain
(docs/_archive/2026-11/VEIL_PASS4_2026-11-15.md): the credit line is the
same object as the logo - a semi-transparent WHITE fill (alpha ~0.14-0.15,
read 0.140 / 0.143 / 0.152 on C / B / A) with a dark rim (outline / drop
shadow, black alpha up to ~0.3-0.6 next to the glyph) - in one text row at a
FIXED place under the logo (0.06-0.13 logo heights below its foot on all
three pairs) and CENTRED on the logo's column. Only its text (the artist's
name), and so its length, varies.

Until pass 3 the credit line rode on the collection matte's seed plus a bright
completion, and LaMa filled whatever that covered: the first and last glyphs
("(c)", "M") fell outside it on most slugs, and on bright art the completion
missed whole words (seraphine-by-pebano1: "DEVIANTART.COM" untouched).

This lane: `locate_credit` takes the text row from the registered logo and
the text's half-width from the lane's OWN detection inside that row - its
farthest column from the centre on either side, plus a margin - applied to
BOTH sides (the text is centred, so the side the detection under-reaches is
covered by the other's reach); `credit_box_mask` hands the whole text box to
LaMa, so no glyph, outline or anti-aliased edge is left outside the mask.

Tried and rejected on the pairs (recorded in the doc): a per-glyph analytic
de-blend (LaMa's fill as the background, glyph cores inverted
J = (I - a W) / (1 - a), art between glyphs kept, edges clamped to the veil
band). It scores best by PSNR on the text pixels but leaves the dark
OUTLINE visible on every pair - the rim's black alpha varies along each
glyph and a physical clamp holds it - which fails the zero-residue bar.
Restricting LaMa's fill to a glyph support read from it leaves fragments
where the fill's background guess is wrong (over hair, over lips).
"""
from __future__ import annotations

import numpy as np

CREDIT_ROWS = (0.055, 0.135)   # logo heights below the logo's foot
CREDIT_MARGIN = 0.12           # logo heights added past the seed's reach
CREDIT_HALF = (0.40, 1.10)     # logo heights: the box half-width's bounds


def _luma(a):
    a = np.asarray(a, dtype=np.float64)
    return a.mean(axis=2) if a.ndim == 3 else a


def _dilate(m, r):
    m = np.asarray(m, dtype=bool)
    if r <= 0:
        return m
    out = m.copy()
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            if dy * dy + dx * dx <= r * r:
                out |= np.roll(np.roll(m, dy, axis=0), dx, axis=1)
    return out


def _erode(m, r):
    return ~_dilate(~np.asarray(m, dtype=bool), r)


def logo_box(coverage):
    """(y0, y1, x0, x1) of the registered logo (coverage >= 0.5), or None."""
    ys, xs = np.nonzero(np.asarray(coverage) >= 0.5)
    if not len(ys):
        return None
    return int(ys.min()), int(ys.max()) + 1, int(xs.min()), int(xs.max()) + 1


def credit_rows(coverage):
    """(r0, r1, cx, lh): the text row and the logo's centre column / height."""
    lb = logo_box(coverage)
    if lb is None:
        return None
    ly0, ly1, lx0, lx1 = lb
    lh = float(ly1 - ly0)
    return (int(round(ly1 + CREDIT_ROWS[0] * lh)),
            int(round(ly1 + CREDIT_ROWS[1] * lh)), 0.5 * (lx0 + lx1), lh)


def search_box(shape, coverage):
    """Full-frame bool: the widest box the text can occupy (for the ROI)."""
    m = np.zeros(tuple(shape[:2]), dtype=bool)
    cr = credit_rows(coverage)
    if cr is None:
        return m
    r0, r1, cx, lh = cr
    hw = CREDIT_HALF[1] * lh
    m[max(r0, 0):r1, max(int(cx - hw), 0):int(cx + hw) + 1] = True
    return m


def locate_credit(seed, coverage):
    """{"rows", "cols", "text_h", "half_w", "seed_px"} or None.

    The text row is fixed by the logo (CREDIT_ROWS). The text is CENTRED on
    the logo's column (A, B and C alike) and only its length varies, so its
    half-width is read from `seed` (the lane's own mark detection: collection
    seed + completion) inside the text row - the farthest detected column
    from the centre, on EITHER side, plus CREDIT_MARGIN - and applied to both
    sides: the first and last glyphs the detection misses on one side are
    covered by the other side's reach. None when nothing was detected there.
    """
    cr = credit_rows(coverage)
    if cr is None:
        return None
    r0, r1, cx, lh = cr
    sd = np.asarray(seed, dtype=bool)
    h, w = sd.shape
    if r0 < 0 or r1 > h:
        return None
    x0 = max(int(cx - CREDIT_HALF[1] * lh), 0)
    x1 = min(int(cx + CREDIT_HALF[1] * lh) + 1, w)
    ys, xs = np.nonzero(sd[r0:r1, x0:x1])
    if len(xs) < 20:
        return None
    reach = float(np.max(np.abs(xs + x0 - cx)))
    hw = float(np.clip(reach + CREDIT_MARGIN * lh, CREDIT_HALF[0] * lh,
                       CREDIT_HALF[1] * lh))
    return {"rows": (r0, r1), "cols": (max(int(cx - hw), 0),
                                       min(int(cx + hw) + 1, w)),
            "text_h": r1 - r0, "half_w": round(hw / lh, 3),
            "seed_px": int(len(xs))}


def credit_box_mask(shape, loc, margin=2):
    """Full-frame bool: the text box (rows +- margin) LaMa fills."""
    m = np.zeros(tuple(shape[:2]), dtype=bool)
    if loc is None:
        return m
    (r0, r1), (c0, c1) = loc["rows"], loc["cols"]
    m[max(r0 - margin, 0):r1 + margin, c0:c1] = True
    return m
