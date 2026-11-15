# DA logo veil - batch gate residual estimator replaced + batch 3 (2026-11-15)

Follows `VEIL_ALPHA_FIT_2026-11-15.md` (per-frame alpha fit, 8aa837f, LEDGER 372).

## Decision (taken; recorded here)

Replace the batch gate's residual-alpha estimator. Constraints: (a) the gate
must not grade the fitter with itself - a different measurement from the fit
objective; (b) validated against ground truth: on the purchased pairs A/B/C,
remove the veil with known alpha errors (0, +-0.01, +-0.02, +-0.04 off the
true value) and require the gate reading to track the true residual within
+-0.005 with no art-dependent bias. Keep the |residual| <= 0.02 threshold
unless the measured noise floor on veil-free frames says otherwise.

Decided by the order (operator via the session prompt); the estimator choice
below is taken on the validation numbers.

## Verdict

- New estimator `lw_clean_overlay.pair_residual_alpha`: a colour MATCHED
  FILTER, read on the algebraic pre-pass frame (`pair_gate_frame`).
- A/B/C, 21 known-error candidates: |err| median 0.0047, max 0.0069 (A 0.0069,
  B 0.0068, C 0.0032), slope vs truth 0.93 / 0.98 / 0.95. Old step estimator on
  the same candidates: median 0.026, max 0.044 (A -0.026, B -0.009, C -0.043
  constant offsets).
- The +-0.005 bar is MET on C and MISSED on A and B by 0.002: per-frame
  offsets A -0.006, B +0.005. Nothing tried beat 0.0064 (below). Reported as
  measured, not rounded into a pass.
- Threshold kept at 0.02 (derivation below).
- Batch 3, 22 slugs: G2 outside-mask 0 px on all 22, gate pass 17 (15
  submitted to NEEDAUTH, 2 refused by ADR-009), 5 manual. Nothing approved.
- 225f: CAUGHT (gate fail, residual -0.0397).

## The new estimator (tools/lw_clean_overlay.py, BATCH GATE RESIDUAL note)

After an inversion at `alpha_used`, the veil left in the frame is
`r * [(W - J) cov - J halo]` per channel. The halo is not inverted by the lane
(by design), so the gate first divides it out at `alpha_used`; it is not fill
residue. Then:

1. Box high-pass (PAIR_RESID_HP = 12 ref px) both the frame and that
   signature, per channel.
2. Weight each pixel by 1 / (local art energy left after the signature's local
   share + PAIR_RESID_C0 16 levels^2): smooth art counts, busy art does not.
3. Solve ONE r shared by R, G and B (weighted least squares projection).

What makes it a different instrument from the fit: the fit zeroes a
strip-mean STEP (2-6 ref px each side, smoother-half median, bisection over
alpha). The gate is a full-template projection (every edge orientation and
corner at once, the halo shape included), high-passed so locally linear
lighting drops out, colour-coupled so an art edge of another hue projects
away. It never calls `fit_pair_alpha`, `pair_veil_alpha_hat` or `_strips`.
That is pinned by `test_gate_never_calls_the_fit_or_the_old_step`.

Why it reads the PRE-PASS, not the LaMa output: LaMa repaints the 1-in / 3-out
edge ring the filter depends on. Read post-LaMa on A/B/C the same filter is
0.012 low on average (A -0.017) and its slope drops to 0.74-0.87. The fill
residual being graded lives in the interior, which LaMa never touches.
`pair_gate_frame` rebuilds the pre-pass frame from the lane's
`<slug>_iopaint_before.png` and COUNTS the candidate pixels that differ from
it outside the LaMa mask. The count must be 0 or the gate fails. It was 0 on
all 22. The LaMa ring itself is graded by G2's seam check and by the operator.

## Validation

### A/B/C known alpha errors (`images/_veil_pairs/2026-11-15/resid_gate_pairs.json`)

Truth = the same oracle as the fit doc: pooled LSQ of (candidate - registered
clean) on (W - clean) in the eroded logo interior, W 245.1. Candidates =
`remove_overlay` at oracle alpha + e, at the refined registration, e in
{-0.04, -0.02, -0.01, 0, +0.01, +0.02, +0.04}.

- new (pre-pass): A median err -0.0061 (max 0.0069), B +0.0050 (0.0068),
  C +0.0001 (0.0032); overall median |err| 0.0047, max 0.0069.
- old step estimator: A -0.0260 (max 0.0267), B -0.0091 (0.0094), C -0.0427
  (0.0436); overall median 0.026, max 0.044.
- new read after LaMa (info only, rejected as the gate input): A -0.0167,
  B -0.0071, C -0.0119; max 0.0227.

### Synthetic veil over real art (`images/_veil_pairs/2026-11-15/resid_gate_synth_art.json`)

30 real frames, none in the DA family:
- the 16 batch-1 veil-free frames, minus the 3 the search later found veiled;
- 14 random cleandone frames (seed 7).

Each frame gets a synthetic DA veil (fill + PAIR_HALO) at alpha 0.12 / 0.18.
It is removed at alpha + e, e in {-0.04, -0.02, 0, 0.02, 0.04}; truth = oracle
against the clean frame. 300 candidates.

- new: |err| median 0.0035, p95 0.0194, max 0.0265; per-frame bias p95 0.019;
  slope vs truth median 0.99 (0.90-1.16).
- old (e = 0, alpha 0.18, 30 candidates): |err| median 0.0125, p95 0.078,
  max 0.389.
- So the art-dependent bias is about 4x smaller, not gone. A few frames carry
  ~0.02 of art bias (star-guardian-caitlyn -0.025, caitlyn-love -0.020,
  t1-yone -0.019).

### Purchased slugs' 2560 cleaninitials (truth approximate, ~0.147-0.150)

- veil read on the input: 0.157 / 0.168 / 0.157.
- After removal at the fit (0.1425 / 0.1466 / 0.1447) the gate reads
  +0.004 / +0.013 / +0.008. The expected reading is about +0.003 / +0.002 /
  +0.004.
- The old estimator read 0.118 / 0.141 / 0.110 on the same inputs.

### Hermetic tests (`tests/test_lw_veil_resid_gate.py`, 55)

- Tracking on the textured fixture: 3 arts x alpha 0.10 / 0.16 / 0.22 x
  e +-0.04..0. Measured |err| median 0.0041, max 0.0061; RESID_TOL 0.0065.
- Sign under / over removal; veil-free art reads 0.
- A smooth glow behind the logo moves the old step +0.045 off the truth and
  the new one less than 0.004.
- No self-grading (monkeypatched fit / step / strips raise).
- Empty coverage gives NaN; the threshold constant.
- `pair_gate_frame` rebuild + mismatch count + shape refusal.

## Threshold derivation (kept at 0.02)

Noise floor = the new estimator on frames with NO veil (alpha_used 0, default
registration):

- 16 veil-free frames: |r| median 0.0023, p95 0.0130, max 0.0195.
- All 30 frames (cleandone included): median 0.0033, p75 0.0074, p95 0.0191,
  max 0.0248.

0.02 sits at the p95 of the new noise floor. A frame with zero residual passes
about 95 percent of the time; under the old estimator 0.02 was its p75 (batch-1
doc). A tighter bar would fail clean frames on art alone. A looser one would
pass a 0.02-0.03 imprint, which the operator rejects (zero-residue bar). The
known +-0.007 error on the purchased pairs is inside the margin. Kept 0.02.

## Alternatives measured and rejected (scratch, A/B/C unless noted)

- Windowed plane + step LSQ ("ring-contrast" with a local-background plane;
  bands 2-10 in / 4-12 out, smooth-half median): A -0.012, slope off; with a
  free halo term A -0.020.
- Grey global high-pass matched filter without the halo correction: B +0.032,
  C +0.035 (the un-inverted halo reads as fill).
- Windowed matched filter (per-window projection, median of the smooth
  windows): max 0.016-0.025, worse than the global projection.
- Larger high-pass box (24 / 32 ref px): C -0.047 / -0.084 (art leaks in).
- Ring excluded / ring-aware variants (zero weight or zero template in the
  LaMa ring): pre-pass A -0.016; post-LaMa best max 0.021.
- Tukey IRLS on top of the chosen filter: max 0.0064 vs 0.0069. Not worth the
  extra parameters.
- Clipping note: A is dark art (edge median 50); at e = +0.04, 31 percent of
  its coverage clips to 0. That is where A's slope (0.93) comes from.

## Batch 3

Targets (`images/_veil_pairs/2026-11-15/batch3/targets.json`), 22 slugs, all
CLEAN_SCRATCH EDITING, none in NEEDAUTH (checked; 0 skipped):

- the 15 batch-2 manual slugs;
- the 4 batch-1 registration failures (110-cleanup, 122, bamboo-gal,
  fantasy-design);
- the 3 found by the search (281-cleanup, 258-cleanup, fury-tempest-sona).

Lane unchanged: `clean_slug(overlay=True)` with pair fit and own registration,
dry run first (22/22 ok).

- G2: candidate vs the ORIGINAL input; mask = pair coverage at template AND
  fitted registration, OR the LaMa mask.
- Gate: G2 pass AND pair used AND fit not at a bound AND pre-pass mismatch 0
  AND |pair_residual_alpha| <= 0.02.
- Pass: save-working --tool iopaint + submit, dry run first. ADR-009 exit 3 is
  recorded; never --allow-ladder.
- Fail: annotate --tool qa, route manual_iopaint (key
  `veil_resid_gate_batch3_2026_11_15`).

Counts:

- re-run 22; G2 pass 21 (281-cleanup: no_op, change_ssim 0.937 > 0.90 - a weak
  0.088 veil); outside_max_abs 0 on all 22; pre-pass mismatch 0 on all 22
- gate pass 17
  - submitted to NEEDAUTH 15: 107-cleanup, 221-cleanup, 239f, 244f, 259f,
    268f, 270f, 273f, 277f, ahri-league-of-legends-by-khanzaaiart-dmbzcmq-pre,
    xayah-by-pebano1-dm44iab-fullview, 110-cleanup, 122,
    bamboo-gal-seraphine-by-mrphantomknight-dm1rp4q-fullview, 258-cleanup
  - refused by ADR-009 2 (prior engine): the-ruined-king-viego-by-vexxsoul-dm6j4mu-pre,
    fury-tempest-sona-by-ryoairtist-dm7ziam-pre
- manual IOPaint 5: 225f (-0.0397), fantasy-design-by-aivio-dkdq5p7-pre
  (-0.0255), 285f (-0.0250), ashe-by-stellastria-dlzcque-fullview (-0.0232),
  281-cleanup (-0.0326 + G2 no_op)
- the old estimator on the same 22 candidates: |old| <= 0.02 on 3 only
  (122 +0.0173, bamboo-gal +0.0033, fury-tempest-sona -0.0134), none of the
  15 batch-2 manual slugs
- queue totals after batch 3: NEEDAUTH 39 + 15 = 54; ADR-009 refused
  5 + 2 = 7; manual IOPaint 5 (was 19: the 15 + the 4 registration slugs;
  the 3 found by the search were in no queue)

Residuals on the 22 skew negative (median -0.011). The new gate reads the
purchased 2560 frames +0.004..+0.013 after the fit, so this is not a known
negative bias of the instrument. It reads like the fit removing slightly too
much on this art (or art bias, p95 0.019). Watch for it at operator review:
a dark imprint, not a bright logo.

### 225f

- The 2x crop (`batch3/225f_logo_before_after_2x.png`) after the fit at 0.187
  still shows a faint light outline along the upper-left box's top and left
  edges.
- The new gate FAILS it at -0.0397: it reads the veil on the input at 0.153
  against the fit's 0.187, i.e. over-removal.
- The old gate also failed it, but at +0.045 (under-removal).
- Caught: yes. The sign of the reading says the fit is too strong on this
  frame. The visible defect is an edge outline, which the operator should
  judge in IOPaint.

Per slug (veil in = new estimator on the input; resid = new on the pre-pass;
old = batch-1 step on the candidate; post = new on the LaMa output, info only):

| slug | alpha_fit | reg | veil in | resid | old | post | G2 | gate | route |
|---|---|---|---|---|---|---|---|---|---|
| 107-cleanup | 0.1598 | template | 0.1713 | +0.0033 | +0.0450 | -0.0236 | pass | pass | submitted |
| 221-cleanup | 0.1599 | template | 0.1866 | +0.0157 | +0.0215 | -0.0019 | pass | pass | submitted |
| 225f | 0.1870 | template | 0.1530 | -0.0397 | +0.0453 | -0.0851 | pass | fail | manual_iopaint |
| 239f | 0.1407 | template | 0.1423 | -0.0071 | -0.0426 | -0.0116 | pass | pass | submitted |
| 244f | 0.1464 | template | 0.1515 | -0.0003 | -0.0233 | -0.0181 | pass | pass | submitted |
| 259f | 0.1517 | template | 0.1622 | +0.0014 | -0.0316 | -0.0190 | pass | pass | submitted |
| 268f | 0.1602 | template | 0.1546 | -0.0132 | +0.0433 | -0.0392 | pass | pass | submitted |
| 270f | 0.1586 | template | 0.1520 | -0.0191 | +0.0234 | -0.0340 | pass | pass | submitted |
| 273f | 0.1514 | template | 0.1466 | -0.0111 | +0.0245 | -0.0288 | pass | pass | submitted |
| 277f | 0.1555 | template | 0.1538 | -0.0114 | +0.0291 | -0.0164 | pass | pass | submitted |
| 285f | 0.1646 | template | 0.1453 | -0.0250 | +0.0440 | -0.0418 | pass | fail | manual_iopaint |
| ahri-league-of-legends-by-khanzaaiart-dmbzcmq-pre | 0.1394 | template | 0.1393 | -0.0025 | -0.0407 | -0.0542 | pass | pass | submitted |
| ashe-by-stellastria-dlzcque-fullview | 0.1616 | template | 0.1459 | -0.0232 | +0.0354 | -0.0332 | pass | fail | manual_iopaint |
| the-ruined-king-viego-by-vexxsoul-dm6j4mu-pre | 0.1405 | template | 0.1299 | -0.0168 | +0.0528 | -0.0430 | pass | pass | ladder_blocked |
| xayah-by-pebano1-dm44iab-fullview | 0.1295 | template | 0.1390 | +0.0023 | -0.0242 | -0.0097 | pass | pass | submitted |
| 110-cleanup | 0.1578 | template | 0.1617 | -0.0030 | +0.0320 | -0.0050 | pass | pass | submitted |
| 122 | 0.1636 | template | 0.1742 | +0.0010 | +0.0173 | -0.0085 | pass | pass | submitted |
| bamboo-gal-seraphine-by-mrphantomknight-dm1rp4q-fullview | 0.1543 | search | 0.1472 | -0.0144 | +0.0033 | -0.0315 | pass | pass | submitted |
| fantasy-design-by-aivio-dkdq5p7-pre | 0.1512 | search | 0.1305 | -0.0255 | +0.0527 | -0.0367 | pass | fail | manual_iopaint |
| 281-cleanup | 0.0876 | search | 0.0569 | -0.0326 | -0.0580 | -0.0217 | FAIL no_op | fail | manual_iopaint |
| 258-cleanup | 0.1737 | search | 0.1652 | -0.0179 | -0.0302 | -0.0331 | pass | pass | submitted |
| fury-tempest-sona-by-ryoairtist-dm7ziam-pre | 0.1668 | search | 0.1712 | -0.0042 | -0.0134 | -0.0176 | pass | pass | ladder_blocked |

## Review aids (gitignored)

- `images/_veil_pairs/2026-11-15/batch3/<slug>_logo_before_after_2x.png`:
  before | after, logo window + credit line, 2x nearest (22).
- `images/_veil_pairs/2026-11-15/batch3/contact_sheet_01.png` to `_03.png`
  (8 per sheet, labelled fit / bound / registration / resid new and old /
  gate / route).
- Data: `batch3/targets.json`, `dry.json`, `exec.json`;
  `../resid_gate_pairs.json`, `../resid_gate_synth_art.json`.

## Operator

Nothing approved. NEEDAUTH +15 (listed above). The 5 manual slugs keep their
batch-3 candidates in `ops/runtime/clean/<slug>/` for a look before IOPaint.
