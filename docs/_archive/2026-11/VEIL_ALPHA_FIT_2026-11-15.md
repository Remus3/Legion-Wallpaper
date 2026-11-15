# DA logo veil - per-frame alpha fit + batch 2 (2026-11-15)

Follows `VEIL_PAIR_RESULT_2026-11-15.md` (pair matte, a2eb6c3) and
`VEIL_BATCH_2026-11-15.md` (63-slug batch, fixed alpha 0.1511).

## Verdict

The pair matte's SHAPE stays; its AMPLITUDE (and a sub-pixel shift) is now fitted
per frame. On the three purchased pairs the fit lands within 0.004 of the
pair-measured alpha (requirement +-0.005) and held-out C does not regress. The
fit also shows that the batch-1 "residual" estimator (`pair_veil_alpha_hat`, the
step between strips 2-6 px in / 8-14 px out) is itself art-biased by up to
-0.04 on these frames, so the true per-frame veil spread is much narrower than
batch 1 read (fits 0.12-0.19, not 0.09-0.22), and the batch gate built on that
estimator now fails frames for estimator disagreement rather than visible
residue. Batch 2: 24 slugs re-run, G2 24/24 (0 px outside the mask), 9 gate pass (6
submitted to NEEDAUTH, 3 refused by ADR-009), 15 back to manual IOPaint;
the 4 batch-1 registration failures are 2 non-failures + 2 template misses,
fixed by a pair-own registration. Nothing approved. Details below.

## Method (tools/lw_clean_overlay.py, PER-FRAME AMPLITUDE note)

1. `refine_pair_shift`: sub-pixel registration of the coverage near the given
   registration - maximize sum(grad I . grad coverage) over the edge band (art
   gradients clipped at their 90th percentile), integer shifts (exact; a
   bilinear-shifted gradient blurs and biases the peak to whole pixels), then a
   parabola per axis. Needed: C's logo sits (+0.5, +2.0) px off the consensus
   matte at 1920 (measured from C's own alpha map); a narrow step read through
   that offset is ~0.03 low. Recovered: A (0.48, 0.10), B (-0.23, 0.01),
   C (0.60, 1.07).
2. `fit_pair_alpha`: the alpha whose inversion leaves zero step across the logo
   edge. Model = fill over the coverage PLUS the dark halo outside the edge
   (`PAIR_HALO`, black-layer alpha per unit fill alpha by ref-px distance,
   measured on pairs B and C: 0.35 at 2 px, 0.18 at 5, 0.10 at 10, 0 by 30).
   Local means 2-6 ref px inside vs 2-6 outside, 15 ref px windows along the
   edge, median over the smoother half of the windows (roughness fixed once at
   the matte's prior alpha), bisection inside `PAIR_FIT_BOUNDS` (0.03, 0.30); a
   clamped fit is flagged (`at_bound` low / high; no usable edge -> prior,
   `no_edge`). numpy + PIL only (an exact capped EDT, no scipy).
3. `overlay_prepass(pair_fit=True)` (default) records `alpha_fit`, `at_bound`,
   `fit_windows`, `shift_fit`, `scale_fit`, `reg_source`, `reg_score` in
   `info["pair"]`; `pair_fit=False` is the a2eb6c3 path byte for byte (pinned).
   The inversion uses the fitted registration; the LaMa edge ring stays on the
   template registration it was swept on (see C below).
4. Pair-own registration (`search_pair_registration` +
   `lw_clean_iopaint.pair_registration`): scale about the FRAME centre
   (0.88-1.33) x shift up to 3 percent of the width, coarse at 1/4, refined;
   it replaces the template registration only when it scores 1.25x better.
   Presence read only at a searched registration also needs a fit off the
   lower bound. See the registration section.

Rejected on the way (all measured on A/B/C, scratch only): wide strips / local
plane fits (C off by up to -0.08), gradient-domain IRLS (C -0.07: edge-profile
and sub-pixel mismatch), per-window linearized estimates + mode (off by
0.02-0.09), no-halo model (biases B +0.02 to +0.04).

## Validation on the purchased pairs (`images/_veil_pairs/2026-11-15/alpha_fit_pairs.json`)

The cited pair alphas 0.1435 / 0.1396 / 0.1406 are LSQ fits with W = 255; the
matte uses W = 245.1, which trades against alpha (a (W - J) is what is seen).
Both units are reported. Oracle = pooled LSQ of (veiled - registered clean)
against (W - clean) in the eroded logo interior.

- A dlnxav6 (preview 1192x670): fit 0.1505; oracle (W 245.1) 0.1466 -> +0.0039;
  W 255 equivalent 0.1441 vs cited 0.1435 -> +0.0006.
- B dia857d (1194x669): fit 0.1497; oracle 0.1502 -> -0.0005; W255-eq 0.1403 vs
  0.1396 -> +0.0007.
- C dmax7wo held out (1920x1080): fit 0.1455; oracle 0.1491 -> -0.0035; W255-eq
  0.1363 vs 0.1406 -> -0.0043.
- Same frames, old step estimator: 0.125 / 0.142 / 0.106. Fit without the shift
  refinement: 0.146 / 0.152 / 0.136 (C fails without it).
- On the purchased slugs' UPSCALED 2560 cleaninitials (the frames the lane
  actually cleans): fit 0.1425 / 0.1466 / 0.1447 (truth ~0.147-0.150, all
  -0.004); step estimator 0.118 / 0.141 / 0.110 (-0.03 / -0.01 / -0.04).
- Synthetic (tests/test_lw_veil_alpha_fit.py fixture, 108 frames = 12 seeds x 3
  brightness x alpha 0.08/0.15/0.22, hard-edged blobs across the edge): |err|
  median 0.002-0.003, p95 0.007-0.008, max 0.010 at 960 and 1280 px.

## Held-out C does not regress vs a2eb6c3 (`eval_alphafit_C_lane.json`)

Same grader as `eval_pairwire.json` (reproduces its fixed-alpha numbers
exactly). logo / edge / near / far PSNR dB, edge_hp, residual alpha vs clean:

- fixed pre-pass (a2eb6c3): 34.65 / 29.37 / 35.63 / 39.24, 5.09, -0.0023
- FITTED pre-pass: **35.19 / 30.46 / 35.64 / 39.24, 4.84, +0.0041**
- fixed full lane (a2eb6c3): 34.38 / 28.89 / 34.58 / 39.26, 5.74
- fitted full lane, ring moved with the refined shift: 33.69 / 27.78 / 34.98 /
  39.25, 6.45 - REJECTED (LaMa on the moved 1/3 ring costs 0.7 / 1.1 dB)
- fitted full lane, ring on the template registration (SHIPPED): 34.34 / 28.86
  / 34.57 / 39.26, 5.77 - within 0.05 dB of a2eb6c3 on every region.

The pre-pass (what the fit controls) improves on every region; the lane after
LaMa is unchanged within 0.05 dB. |residual| 0.0041 vs 0.0023, both far under
the 0.01 bar.

## Batch 2 (step 3)

Targets (`images/_veil_pairs/2026-11-15/batch2/targets.json`): the 22 manual-queue
slugs that registered, plus the 2 ADR-009-blocked gate-pass slugs with
|resid| > 0.01 (not in NEEDAUTH). The 11 gate-pass slugs with |resid| > 0.01
that sit in NEEDAUTH were NOT touched - the cleaning-pass skill has no clean
re-submit (only operator approve / reject): 245f, 261f, 269f, 276f, 278f,
bayonetta-by-stellastria-dm7iiug-pre, caitlyn-by-pebano1-dm9fw9z-fullview,
fierce-enforcer-of-piltover-by-vexxsoul-dm5crlf-pre,
inkshadow-kai-sa-by-pebano1-dm7m9lz-fullview,
seraphine-stage-of-brilliance-by-vexxsoul-dm5uzf1-pre,
syndra-league-of-legends-by-smalltavernx-dlsfcue-pre. If the operator rejects
one, the re-run is `clean_slug --overlay` (pair_fit is the default).

Same lane and gate as batch 1: `clean_slug(overlay=True)` (now fitting), G2 vs
the original input with mask = pair coverage (template AND fitted registration)
OR the LaMa mask; batch gate = G2 pass AND registration ok AND fit not at a
bound AND |resid| <= 0.02; resid = `pair_veil_alpha_hat` on the candidate at
the template registration (batch-1 estimator, unchanged). Pass -> save-working
--tool iopaint + submit (dry-run first); ADR-009 exit 3 recorded, never
--allow-ladder; fail -> annotate --tool qa route manual_iopaint (key
`veil_alpha_batch2_2026_11_15`). The run used the code before Method step 4
(own registration) was added; a prepass re-run with the final code
(`batch2/consistency_prepass.json`) keeps the template registration and the
same alpha_fit on all 24.

Counts:

- re-run 24; G2 pass 24, outside_max_abs 0 on all
- batch gate pass 9: submitted to NEEDAUTH 6 (224f, 262f, 272-cleanup, 287f,
  anime-poster-of-soraka-from-league-of-legends-by-givemenine-dg8j,
  miss-fortune-by-stellastria-dmcdsno-fullview); ADR-009 refused 3
  (aatrox-the-darkin-blade-in-flames-by-vexxsoul-dm6j4xi-pre - newly gate-pass,
  a prior engine on the slug - plus prestige-coven-xayah and viego-the-king,
  as in batch 1)
- manual IOPaint 15, every one on residual only (no bound, no registration)
- fitted alpha over the 24: min 0.1208 (224f), median 0.1538, max 0.1870
  (225f); none at a bound. The batch-1 step read 0.104-0.223 on the same frames.
- queue totals after both batches: NEEDAUTH 33 + 6 = 39; ADR-009 refused 5
  (aatrox, prestige-coven, viego-the-king, aidraw, syndra-coven); manual 15 + the
  4 registration slugs = 19.

Why 15 still fail: their residual is the batch-1 estimator's read, and it
disagrees with the fit by about (step - fit): 239f reads 0.104 vs fit 0.141 ->
resid -0.043; 225f 0.223 vs 0.187 -> +0.045. On the purchased frames (above) the
estimator is the one that is off (-0.01 to -0.04), so a large share of these
failures is the gate's measuring stick, not residue. Not all: at 2x, 225f with
the fit keeps a faint outline of the logo's upper edge (much fainter than the
fixed-alpha candidate, which keeps a visible fill); 239f fitted shows no dark
imprint at 2x. Proposal (not done; the order fixed the gate): gate on an
edge-band visual-residue measure, after an operator pass over these crops.

Per slug (veil step in = batch-1 estimator on the input):

| slug | veil step in | alpha_fit | shift_fit | resid after | G2 | gate | route |
|---|---|---|---|---|---|---|---|
| 107-cleanup | 0.1957 | 0.1598 | +1.03,+1.68 | +0.0450 | pass (out 0) | fail | manual_iopaint |
| 221-cleanup | 0.1742 | 0.1599 | +0.42,+0.02 | +0.0215 | pass (out 0) | fail | manual_iopaint |
| 224f | 0.1238 | 0.1208 | +0.46,-0.96 | +0.0041 | pass (out 0) | pass | submitted |
| 225f | 0.2233 | 0.1870 | -0.43,+0.08 | +0.0453 | pass (out 0) | fail | manual_iopaint |
| 239f | 0.1036 | 0.1407 | -0.50,+0.42 | -0.0426 | pass (out 0) | fail | manual_iopaint |
| 244f | 0.1263 | 0.1464 | -0.26,+0.08 | -0.0233 | pass (out 0) | fail | manual_iopaint |
| 259f | 0.1244 | 0.1517 | -0.30,+0.03 | -0.0316 | pass (out 0) | fail | manual_iopaint |
| 262f | 0.1712 | 0.1577 | -0.39,-0.09 | +0.0165 | pass (out 0) | pass | submitted |
| 268f | 0.1959 | 0.1602 | -0.09,+1.65 | +0.0433 | pass (out 0) | fail | manual_iopaint |
| 270f | 0.1779 | 0.1586 | +0.72,+1.34 | +0.0234 | pass (out 0) | fail | manual_iopaint |
| 272-cleanup | 0.1270 | 0.1426 | +0.26,+1.79 | -0.0171 | pass (out 0) | pass | submitted |
| 273f | 0.1707 | 0.1514 | -0.23,+0.01 | +0.0245 | pass (out 0) | fail | manual_iopaint |
| 277f | 0.1801 | 0.1555 | +0.41,+1.89 | +0.0291 | pass (out 0) | fail | manual_iopaint |
| 285f | 0.2016 | 0.1646 | -0.29,+0.07 | +0.0440 | pass (out 0) | fail | manual_iopaint |
| 287f | 0.1690 | 0.1693 | -0.58,+0.20 | +0.0005 | pass (out 0) | pass | submitted |
| aatrox-the-darkin-blade-in-flames-by-vexxsoul-dm6j4xi-pre | 0.1717 | 0.1665 | -1.29,+0.06 | +0.0117 | pass (out 0) | pass | ladder_blocked |
| ahri-league-of-legends-by-khanzaaiart-dmbzcmq-pre | 0.1043 | 0.1394 | -0.12,-0.18 | -0.0407 | pass (out 0) | fail | manual_iopaint |
| anime-poster-of-soraka-from-league-of-legends-by-givemenine-dg8j | 0.1722 | 0.1604 | -0.50,+1.81 | +0.0145 | pass (out 0) | pass | submitted |
| ashe-by-stellastria-dlzcque-fullview | 0.1895 | 0.1616 | +0.67,+0.99 | +0.0354 | pass (out 0) | fail | manual_iopaint |
| miss-fortune-by-stellastria-dmcdsno-fullview | 0.1268 | 0.1424 | +0.82,+1.07 | -0.0179 | pass (out 0) | pass | submitted |
| the-ruined-king-viego-by-vexxsoul-dm6j4mu-pre | 0.1853 | 0.1405 | -1.70,+0.33 | +0.0528 | pass (out 0) | fail | manual_iopaint |
| xayah-by-pebano1-dm44iab-fullview | 0.1079 | 0.1295 | +0.20,+1.92 | -0.0242 | pass (out 0) | fail | manual_iopaint |
| prestige-coven-xayah-by-pebano1-dmc27t0-pre | 0.1411 | 0.1512 | +0.31,+1.81 | -0.0101 | pass (out 0) | pass | ladder_blocked |
| viego-the-king-by-slimshadywallpaper-dhawigh-pre | 0.1629 | 0.1520 | -0.31,+0.01 | +0.0130 | pass (out 0) | pass | ladder_blocked |

## Registration failures (step 4)

Diagnosis (`batch2/regfail_diag.json`, `batch2/consistency_prepass.json`):

- 110-cleanup, 122: NOT registration failures. The frames are 1.12x zooms; the
  template's (24, -1) at 1.12 about the REMOVAL_BAND centre is the same place
  as 1.12 about the frame centre + (0, 2) (0.15 h centre offset x 0.12 = 26
  px). Batch 1's rule (scale != 1 AND resid >= 0.01) fired on AMPLITUDE. With
  the fit: alpha 0.158 / 0.164, prepass resid +0.020 / +0.014.
- bamboo-gal-seraphine-by-mrphantomknight-dm1rp4q-fullview: source preview
  1024x510 (2.0:1, not 16:9). The logo sits near frame centre (+1.1, +4.1 px);
  the COLLECTION template was dragged to dx +30 by art (score 141 there vs 362
  at the logo). Fixed: pair-own registration, alpha 0.154, prepass resid
  +0.004.
- fantasy-design-by-aivio-dkdq5p7-pre: the frame is a 1.2x centre zoom; the
  template's scale grid is about the REMOVAL_BAND centre and answered (43, -10)
  at 1.0 (score 118 vs 374). Fixed: pair-own registration 1.2 + (0.9, 2.2),
  alpha 0.151, prepass resid -0.019. Its batch-1 "over-removal" (-0.075) was
  this misregistration, not a weak veil.
- Root cause: the pair borrowed the collection template's registration. Fix +
  tests: Method step 4; `test_search_finds_a_zoomed_frame`,
  `test_prepass_overrides_a_template_that_missed_a_zoomed_frame`,
  `test_prepass_overrides_a_dragged_template`,
  `test_prepass_keeps_a_good_template`.
- The 4 were NOT re-run through the lane (outside the order's re-run set); with
  the final code they are ready for `clean_slug --overlay`.

Missed family members found by the search: 3 of batch 1's 19 "veil-free"
frames carry the DA logo and credit line at a zoom the template never tried
(eyeballed, `batch2/search_presence_check.png`): 281-cleanup (1.16x, fit
0.088), 258-cleanup (0.88x, fit 0.174), fury-tempest-sona-by-ryoairtist-dm7ziam-pre
(1.2x, fit 0.167). One false hit, caitlyn-love-confession-lol-skin-splash-art-4k-wallpaper-uhdpape
(no logo; fit at the lower bound 0.03) - hence the lower-bound presence rule,
pinned by `test_search_only_presence_needs_a_fit_above_the_lower_bound`. The 3
were not run.

## Review aids (step 5, gitignored)

- `images/_veil_pairs/2026-11-15/batch2/<slug>_logo_before_after_2x.png`:
  input | batch-1 fixed 0.1511 | batch-2 fitted, logo window + credit line, 2x
  nearest (24 slugs).
- `images/_veil_pairs/2026-11-15/batch2/contact_sheet_01.png` to `_03.png`
  (8 per sheet, labelled fit / bound / shift / veil step / resid / gate / route).
- C grading outputs `batch2/C_grade/`; data `targets.json`, `dry.json`,
  `exec.json`, `regfail_diag.json`, `consistency_prepass.json`,
  `../alpha_fit_pairs.json`, `../eval_alphafit_C_lane.json`; batch-1
  candidates kept for the triptychs in `batch2/_prev/`.

## Operator

Nothing approved. NEEDAUTH +6 (listed above); the 15 manual slugs keep their
batch-2 candidates in `ops/runtime/clean/<slug>/` for a look before IOPaint.
