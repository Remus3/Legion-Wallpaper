# DA logo veil from purchased clean originals - result (2026-11-15)

**Verdict.** The veil is ONE fixed object, identical across three artists: the
DeviantArt logo, a solid achromatic fill at **alpha ~0.14** (not 0.0578), centred
on the frame and scaled with it, plus a faint dark halo just outside its edge.
Production already carries the right amplitude (wide matte veil alpha 0.1398)
but its support covers only **44 percent** of the logo, because 32 percent of
the logo lies ABOVE `REMOVAL_BAND` (y/h 0.45) and the rest is eroded interior.
A pair-derived shape x scalar matte removes the veil on the held-out pair to
within 0.5 dB of the oracle. Recommendation: wire it in (proposed slice below).

## Inputs (step 1)

Clean files are the operator's purchased originals, read as data with PIL/numpy
only. Veiled counterparts are the ORIGINAL DA previews: the `9.Image Backup`
originals, byte-identical (same sha256) to each slug's `_firstinitial.jpg` and to
`manifest.json` `original_sha256`. Not upscaled, not cleaned.

- A pebano1 dark-cosmic-ahri dlnxav6, held IN.
  veiled `images/9.Image Backup/dark-cosmic-ahri-by-pebano1-dlnxav6-pre/dark_cosmic_ahri_by_pebano1_dlnxav6-pre.jpg`
  1192x670, sha256 62de1894255dae20912864d37e1ea397275641625457c5ff253afc47db09308d.
  clean `<console-drops>/2026-11-15/084630-bd39e3-dlnxav6-...png` 3840x2160,
  sha256 e11482b7d45b4c76fb2f2665ee8df2a150248de532ef88b9667ccb3e56eb4bb8.
- B smalltavernx mecha-ahri dia857d, held IN.
  veiled `images/9.Image Backup/mecha-ahri-by-smalltavernx-dia857d-pre/mecha_ahri_by_smalltavernx_dia857d-pre.jpg`
  1194x669, sha256 7626638086895b6e986521b49d5bc2d55ac380de3b7bf100589ff520982b06e8.
  clean `<console-drops>/2026-11-15/084633-04c0a3-dia857d-...png` 5824x3264,
  sha256 b0d137674a38d5c253732b2482f5b13fe97c42cd657ce847a11ee28f37b7532c.
- C narumicsibe yuumi dmax7wo, HELD OUT (grading only).
  veiled `images/9.Image Backup/yuumi-by-narumicsibe-dmax7wo-fullview/yuumi_by_narumicsibe_dmax7wo-fullview.jpg`
  1920x1080, sha256 3598aa9f93837bd5f8357832b5b59f879f5a8c7e8a2fd6cd13c27e5dc2ddfca2.
  clean `<console-drops>/2026-11-15/084635-38e77f-dmax7wo-...png` 2560x1440,
  sha256 7b9d1aa103a04677b66f6996faab9904fde8cfe3e5217e64be2af2763010e0e1.

## Registration and tone (step 2)

Clean resized to the preview size (INTER_AREA; scale 3.22 / 4.88 / 1.333), then
cv2 ECC affine refine on luma. The previews are plain whole-frame resizes, no
crop: ECC correlation 0.989 / 0.998 / 0.999, residual translation < 0.09 px,
residual scale <= 0.07 percent (A/B y rounding of the 670.5 / 669.2 px height).
A sub-pixel shift sweep after warping finds the optimum at (0, 0) for all three
(any 0.25 px move raises the error), so registration error is < 0.25 px.

Tone: a 3x3 colour matrix + offset fitted by least squares OUTSIDE the veil
(central box excluded, then any pixel whose smoothed luma diff exceeds 1 level,
3 iterations; 66 / 85 / 93 percent of pixels used). Residual RMS outside the veil
3.04 / 3.35 / 2.75 levels (JPEG floor). B and C are near-identity (diag
0.98-1.00, offsets < 0.6). A carries real colour drift (R 0.943, G 1.098, cross
terms up to 0.18): the purchased A file is not exactly the colour grade that was
previewed. A's colour-dependent numbers (mark colour fit) are therefore the least
trustworthy; its alpha numbers agree with B and C regardless.

## Pair-tool run (step 3)

`tools/lw_overlay_from_pair.py` (`extract` :139, `alpha_from_pair` :69,
`fit_mark_colour` :106, `ALPHA_FLOOR` 0.02 :38) run as-is on each pair:

- A: W 255.0, support 62,226 px, alpha_max 1.0, mean-in-support 0.081, bbox =
  whole frame, residual_mae 1.84.
- B: W 255.0, support 84,555 px, bbox whole frame, residual_mae 1.83.
- C (reference only): W 253.5, support 228,330 px, residual_mae 1.65.

As shipped the tool is JPEG-noise dominated: it solves alpha per pixel with no
pooling, and `fit_mark_colour` scores every "touched" pixel (> 1 level), which
on a JPEG preview is every pixel. Its bbox and support are meaningless here. The
model is right; it needs local pooling. A Gaussian-weighted (sigma 2 px) local
least-squares of `obs - orig = alpha (W - orig)` over channels gives a clean
matte: the logo and the credit line stand out on a flat zero field (99th
percentile alpha 0.142 / 0.143 / 0.141; median ~0.000).

## The matte (step 4)

Logo = largest component of smoothed alpha > 0.07, holes filled.

- Position, frame-normalized bbox (x0, y0, x1, y1): A 0.4446 0.3418 0.5554 0.6597;
  B 0.4447 0.3408 0.5553 0.6577; C 0.4453 0.3417 0.5563 0.6593. Centroid
  (0.499-0.501, 0.498-0.500). Area 2.24 / 2.21 / 2.22 percent of frame.
  The logo is centred and scales with the frame; agreement is ~1 px.
- Interior alpha (eroded logo, per-pixel LSQ): median 0.1435 / 0.1396 / 0.1406;
  smoothed mean 0.140 / 0.141 / 0.139.
- Mark colour, per-channel fit of (alpha, W) inside the interior: B (0.151,
  245), (0.148, 246), (0.149, 248); C (0.144, 252), (0.142, 252), (0.147, 249).
  Achromatic, W ~246-252. A gives W 254-293 per channel: ill-conditioned (dark
  art, colour drift above), not a different mark.
- A vs B on a common 1920x1080 normalized grid: matte correlation **0.978** in
  the logo window (0.938 with the artist-specific credit line included), logo
  IoU 0.973, mean |dAlpha| in the logo 0.005; best extra shift 1 px. A vs C 0.936
  / IoU 0.967; B vs C 0.949 / IoU 0.972.
- Versus the pooled estimate: **0.0578 +- 0.0046** (`docs/_archive/2026-09/POOLED_VEIL_RESULT_2026-09-05.md`:97)
  was low by ~2.4x. The ring-step method measured a half-shadowed, partly
  out-of-band boundary (see halo below), not the fill. Production's wide-matte
  veil alpha 0.1398 (`ops/runtime/clean/overlay_matte_wide.npz`) is correct.

**Single scalar vs per-pixel.** The fill is constant: interior per-pixel std
0.041 / 0.055 / 0.031 equals the noise std measured on veil-free art (0.030 /
0.041 / 0.031); smoothed std 0.009-0.010; no dependence on the underlying luma
(quintile medians within 0.137-0.146, no trend). The 4x4 block medians span
0.120-0.150 only because edge blocks contain the ramp. Verdict: single scalar
alpha over the FILL is right (`estimate_veil` docstring, `tools/lw_clean_overlay.py`:699-707,
is vindicated). What is NOT scalar is the boundary: a ~1-2 px antialiased edge
and a dark halo outside it.

**Halo.** Fitting `obs - orig = aw (255 - orig) - ak orig` per signed-distance
bin (in 1920-grid px) gives a black-layer alpha just outside the logo: at -3 /
-5 / -9 / -14 / -24 px, B 0.052 / 0.044 / 0.019 / 0.008 / 0.004, C 0.067 / 0.030
/ 0.018 / 0.009 / 0.004 (A similar but with a noisy floor ~0.02). This is the
"dark outline" LEDGER 29/94 saw; it is a soft shadow, consistent across artists.

**Credit line.** Falls out separately below the logo (A bbox y 0.681-0.700, B
0.689-, C 0.689-0.695), alpha p90 ~0.16 with its own dark rim. It is
artist-specific text, so it is never part of a shared model (consistent with the
pooled-result finding); it stays on the LaMa stroke path.

## Grading (step 5)

Reference = registered, tone-matched clean. Regions: logo (own logo mask +3 px),
edge band, ring (out to 3 percent of width, credit excluded), credit box,
outside. Residual alpha = smoothed alpha re-estimated from (output, reference)
inside the logo; 0 is a perfect removal. Old = the production algebraic
pre-pass as wired (`overlay_prepass`, `tools/lw_clean_iopaint.py`:764: wide
template `best_registration`, then `OV.remove_overlay`, `tools/lw_clean_overlay.py`:771,
with the wide matte); its LaMa stroke stage is not run, so the credit line and
outline residue it would hand to LaMa are scored as-is for every path. New =
shape x scalar matte from the OTHER pairs (logo mask consensus on the
normalized grid, blurred sigma 1 px, times the median interior alpha 0.144),
`J = (I - a W) / (1 - a)`, W from B's fit (246.3; 250 where B is held out).

Held-out C, model from A+B (logo PSNR / SSIM, ring PSNR, outside PSNR, residual alpha):

- input, no removal: 21.53 / 0.888, ring 37.01, outside 39.24, residual 0.127
- OLD production pre-pass: 25.24 / 0.909, ring 32.37, outside 38.83, residual 0.051
- NEW per-pixel mean matte: 34.21 / 0.940, ring 36.58, residual 0.009
- NEW shape x scalar: **35.22 / 0.949**, ring 36.91, outside 39.24, residual **0.002**
- oracle (C's own matte): 35.75 / 0.951, ring 37.01, residual 0.010
- NEW shape x scalar + halo profile: 34.20 / 0.938, ring **37.82**, residual 0.005

Leave-one-out (logo PSNR, residual alpha): A from B's matte, old 21.42 / 0.049
vs new 30.23 / 0.003 (oracle 30.42); B from A's matte, old 23.26 / 0.048 vs new
33.89 / 0.001 (oracle 34.09). Old damages the ring on every pair (C 37.0 ->
32.4, A 31.5 -> 28.8, B 35.8 -> 31.4) - the feathered over-correction of an
out-of-place support - and lowers outside PSNR slightly; new leaves ring and
outside at the input's value (pixels outside the matte are byte-identical).

Why the old path leaves ~40 percent of the veil: on the native geometry its
veil support covers 44 / 44 / 45 percent of the logo (A / B / C), 32-33 percent
of the logo rows sit above `REMOVAL_BAND` y/h 0.45 and are never touched, and
the edge matte adds only mean alpha 0.011 inside the logo. Registration chose
shift (0,0) or (1,-1), scale 1.0, so it is not a registration miss.

Visual check (2x zoom of new on C): the fill is gone; a faint 1 px outline
ghost remains along the logo boundary (the halo + edge ramp at preview
resolution). That fails the zero-watermark bar on its own, so the edge still
needs the LaMa outline mask (or the halo term). A blind sub-pixel shift search
(min high-pass energy in the edge band) was tried and REJECTED: it moved C by
1.5 px and lost 1.4 dB.

## Synthetic loop (step 6)

The A+B model (fill + halo, W 250) was composited onto three non-veiled
2560x1440 `4.Cleaning Done` frames (10f, 114f, 11f; overlay_score 0.055 /
0.051 / 0.045, below the 0.071 clean ceiling) and JPEG-re-encoded at q88.
Logo PSNR input / old / new: 10f 18.52 / 20.42 / 23.38; 114f 18.24 / 19.72 /
22.09; 11f 18.01 / 20.38 / 25.87. Ring PSNR: old drops it 5 dB, new raises it
~1 dB. Residual alpha: old 0.041-0.052, new -0.006 to -0.016. The loop works
and ranks paths as the real pairs do; it is circular for the new model (same
matte synthesizes and removes), so it grades the old path and plumbing, not the
new matte. Absolute logo PSNR is capped by the q88 re-encode.

## Recommendation and proposed next slice

Wire the pair matte into production. Not done here (no production code changed).

1. New artifact `data/reference/da_veil_pair_matte.npz`: logo shape on a
   frame-normalized grid (consensus of A and B), fill alpha 0.142, W 248,
   halo profile ak(signed distance / frame width). Built by a script that
   regenerates it from the two pairs; image bytes stay untracked.
2. `remove_overlay` gains a frame-normalized veil path: resize the shape to the
   full frame (not to `REMOVAL_BAND`), registration by frame geometry plus the
   existing template shift, apply `J = (I - aw W) / (1 - aw - ak)`.
3. Keep the LaMa outline mask for the credit line and the residual 1 px edge.
4. Fix `lw_overlay_from_pair.extract` for JPEG pairs: local pooled LSQ (sigma
   2 px) and score `fit_mark_colour` only inside a support, not on every pixel
   touched by JPEG noise.
5. Gate: a test that grades the remover on held-out C (residual alpha < 0.01,
   ring PSNR not below input) using the untracked pair when present, and on
   the synthetic loop in CI.
6. Note: the 2560x1440 firstdones the lane cleans are crops/upscales of these
   previews; a firstdone whose crop is not centred moves the logo off frame
   centre, so registration must stay (template shift), not assume centre.

## Outputs

Untracked (images/ is gitignored, `.gitignore`:58): `images/_veil_pairs/2026-11-15/`
- registered cleans, alpha maps and visualizations, logo/credit masks, all
removal outputs, side-by-side crops, and `register.json`, `analyze.json`,
`eval.json`, `eval_v1_rescored.json`, `eval_v2.json`, `eval_synth.json`,
`edge_profile*.json`, `model_AB.npz`.
