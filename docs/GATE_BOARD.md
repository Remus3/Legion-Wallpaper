# Fault-proven gate board (P0-3, 2026-10-04)

`tools/lw_gate_board.py`. Every gate row must have been SEEN RED: it passes on
a clean subject and fails on a planted copy carrying a synthetic defect. Rows
judge through the LIVE gate code (`lw_g1_gate.verdict`, `lw_first_pass.
gate_metrics`, `lw_clean_pass.verify_verdict`, `lw_upscale._finish`) and read
thresholds at evaluation time, so a mutant that deletes or loosens a threshold
flips its row to BROKEN (pinned in `tests/test_lw_gate_board.py`).

States: PROVEN (clean PASS, planted FAIL), BROKEN (the fault does not move the
row past its bar, or the fault aliased the subject), UNPROVEN (no fault),
UNKNOWN (the measurement raised or returned nothing, or the clean subject
already fails), NA (the live gate does not apply - lap_ratio on a downscale-
only frame, ADR-006), VALIDATION (operator-only rows; never measured, never
count toward done).

## Running it

    python tools/lw_gate_board.py prove --golden --env all     # ~4 min, GPU for metrics + OCR
    python tools/lw_gate_board.py check                        # exit 1 unless all PROVEN

`--env all` runs the `metrics` rows (MS-SSIM, LPIPS) under `.venv-metrics`, the
`clean` row (OCR + MSER residue) under the lw-clean venv, and the numpy rows on
system python, then merges to `ops/runtime/gate_proofs.json` (gitignored). It
writes `ops/loop/control/progress/gate-board-prove.json` as it goes. No image
bytes are tracked: faults are numpy edits of in-memory copies of the
gitignored golden set.

`drift_guard` (`check_gate_proofs`) breaches on any registered row that is not
PROVEN, on a stale table (registry digest changed), and on an absent table
wherever the golden set is on disk; on CI (no golden set) absence is a note.

## Proof table, golden set (12 frames), run 2026-10-04

| row | state | proven | fault (amplitude) |
|---|---|---|---|
| G0.aspect | PROVEN | 12/12 | letterbox to 16:10 |
| G1.lap_ratio | PROVEN | 11/11 (+1 NA) | down-up x2 bicubic |
| G1.halo_pct | PROVEN | 12/12 | USM r2 p150 t0 |
| G1.cambi_delta | PROVEN | 12/12 | posterize step 8 (added 2026-10-04, LEDGER 263) |
| G1.msssim | PROVEN | 12/12 | 16 px shift |
| G1.lpips | BROKEN | 11/12 | down-up x4 |
| G2.outside_identity | PROVEN | 12/12 | one 32x32 block +16 levels outside the mask |
| G2.no_op | PROVEN | 12/12 | fill returned the input |
| G2.seam_step | PROVEN | 12/12 | fill offset +24 levels (added 2026-10-04, LEDGER 264) |
| G2.text_residue | BROKEN | 0/12 | credit line at +4 luma levels |
| G2.text_residue_mf | PROVEN | 12/12 | credit line at +4 luma levels (added 2026-10-04, LEDGER 267) |
| V.reads_like_original | VALIDATION | - | operator only |
| V.zero_watermark_eye | VALIDATION | - | operator only |

**P0-3 acceptance ("every gate PROVEN") is NOT MET.** Two rows are
acknowledged (below), which is a record of a measured hole, not a pass.

## What the board found

1. **G2 outside identity was blind to a localized change - FIXED.** The arm was
   two frame MEANS (ssim >= 0.995, mad <= 1 level). One 32x32 block moved +16
   levels outside the mask read ssim 0.9999 / mad 0.0045 on every golden frame:
   BROKEN 0/12. The LaMa composite is byte-identical outside its binary mask by
   construction, so a strict arm `outside_max_abs <= OUTSIDE_MAX_ABS (0)` was
   added to `verify_verdict`; the row now reads PROVEN 12/12.
2. **The live residue probe failed OPEN - FIXED.** `except Exception: residue =
   False` turned a crashed probe into "no residue". `probe_residue` now returns
   (None, ExcType); verify flags `residue_probe_error` and records the type.
3. **G1.band_delta cannot see output-scale banding.** It counts isolated 1-px
   steps after a LANCZOS downscale to source scale, which smears every step into
   a ramp; posterizing the output at step 8 (and 32) LOWERS it. REPLACEMENT
   PROVEN (R1, LEDGER 263): G1.cambi_delta = CAMBI (libvmaf, max_log_contrast=5)
   of the output at 2560x1440 minus CAMBI of the source resized to that size;
   clean -0.51..1.21, posterize_8 3.00..14.17, flag > 2.0, PROVEN 12/12; 0/131
   live needauth frames flag. LIVE since R1b (LEDGER 265):
   `lw_first_pass.compute_cambi_delta` feeds `assemble_metrics`, None (not
   gated, logged) without ffmpeg. The G1.band_delta row and its ack entry are
   RETIRED; band_delta is recorded under the annotate payload's `info_metrics`
   only, and stays a verdict rule solely for `lw_clean_fr` (same-scale audit).
4. **G1.lpips misses a 4x detail loss on a soft low-res source** (coven-ashe,
   0.037 -> 0.059 vs a 0.12 bar). lap_ratio catches it there (1.514 -> 0.198).
5. **G2.seam measures ring texture, not a seam.** A perfect fill reads < 0.92 on
   9/12 frames; live, 22 of 41 recorded verifies carry the flag. Treat the live
   seam flag as noise until it is rebuilt. REPLACEMENT PROVEN (R3, LEDGER
   264): G2.seam_step = |median over 16 px contour cells of median(inner
   1-3 px band) - median(outer 1-3 px band)|; golden clean max 2.36 vs
   offset min 21.64, 26 real LaMa clean pairs max 2.06, bar 6.0 levels,
   PROVEN 12/12; live 1/37 over the bar. LIVE since R3b (LEDGER 266):
   `_auto_inpaint` computes `seam_step(out, mask)` and passes it to
   `verify_verdict`, which flags `seam_step`; the ring-SSIM `seam` flag, the
   G2.seam row and its ack entry are RETIRED. `seam_ssim` stays in
   verify.json metrics as an info field only (lw_clean_retry_probe computes
   its own ring SSIM). Re-scored live: 1/37 flag (spirit-blossom-ahri-mono-01,
   6.28 - operator review) vs 22/37 under the retired arm.
6. **G2.text_residue fires on clean busy art and misses faint residue.** 7/12
   restored regions read as residue; on the other 5 the +4-level mark does not
   move it. Consistent with LEDGER 121. REPLACEMENT PROVEN (R2 / E-MIM-1,
   LEDGER 267): G2.text_residue_mf = signed median over the old mark's
   stroke pixels of luma(cleaned) - luma(LaMa re-inpaint of the strokes
   dilated 3 px); golden clean |.| max 2.00 vs +4 lv min 4.00, 26 real LaMa
   clean pairs max 1.94 (0 FP; +4 lv copies min 3.89, 26/26 caught), bar
   3.0 levels, PROVEN 12/12. Not yet computed in live verify (R2b: needs a
   stroke mask from the pre-clean detection), so G2.text_residue stays
   pinned until that wiring retires it.
7. **Measurement-basis split, recorded:** `lw_golden._real_compute_metrics`
   feeds PIL "L" (uint8) gray to banding_delta, the live first pass feeds float
   luma from RGB; the same frame scores +0.0074 vs -0.0767. The board measures
   the LIVE basis (`lw_first_pass.compute_numpy_metrics`).

## Fault calibration and evidence

| row | amplitude | evidence |
|---|---|---|
| G2.text_residue | +4 luma levels toward white inside the glyphs | the faintest residue the operator's eye REJECTED in the hand-clean captures (`ops/runtime/clean/handedits/`): 105-cleanup step 70 median 3.77 levels (n=733, corr 0.86 with the remaining residue, 84 percent of pixels moving toward final) and its final step 4.5 levels (n=2813). As alpha that is ~0.018-0.026 for a white mark, ~0.06-0.075 for a dark one; the DA centre veil (alpha 0.09-0.13, CLEAN_VEIL_AMPLITUDE_2026-08-12) is ~5x stronger. 107-cleanup's 3.2-level steps were texture regeneration (corr 0.18-0.36), not residue, and were not used. |
| G2.text_residue_mf | +4 luma levels (same fault) | same calibration as G2.text_residue; clean max 2.00 (golden) / 1.94 (26 real pairs) vs +4 lv min 3.89 |
| G2.seam_step | +24 levels | twice the operator's median per-step edit delta (11.8, CLEAN_HANDEDIT_ANALYSIS); clean max 2.36 (golden) / 2.06 (26 real pairs) vs offset min 14.35 |
| G2.outside_identity | 32x32 block, +16 levels | a localized composite bug, far below what the mean arms can see |
| G1.lap_ratio | down-up x2 | the historic double-resample softness bug (AUDIT_GATES 3.1) |
| G1.halo_pct | USM r2 p150 t0 | a second USM at the `_clamp_usm` ceiling; the fallback upscaler measured 0.049-0.145 (QA Session 2) |
| G1.cambi_delta | posterize step 8 | same fault; clean max 1.21 vs banded min 3.00 on the golden set |
| G1.msssim | 16 px shift | measured 2026-09-08 (tests/test_g1_msssim_arm_binds.py) |
| G1.lpips | down-up x4 | blur r8 measured lpips 0.157 (same file) |
| G0.aspect | 16:10 letterbox | the commonest non-16:9 wallpaper drop |

Faults are NOT rescaled per subject to make a gate pass (adjudicated): a fault
tuned until the metric fires proves nothing about faint residue.

## Acknowledged rows (config/gate_board_ack.json)

Adjudicated 2026-10-04, option (b): breach by default; a tracked entry naming
the row, its pinned measured state (state, n_proven, failing subjects), a
LEDGER item that exists and a checkable `clears_when` downgrades exactly that
row to a note. A re-run that is WORSE breaches; a row that becomes PROVEN asks
for its entry to be removed. Entries are added only through a recorded
adjudication; removing one is always allowed. Current entries: G1.lpips,
G2.text_residue (LEDGER 244); G1.band_delta removed with its row in R1b
(LEDGER 265); G2.seam removed with its row in R3b (LEDGER 266).

## Operator validation rows

Two rows no script can measure stay with the operator and never count toward
done: "reads like the original art" and "no ghost, band or faint residue
visible at 1:1".

## Stage ledger tolerance (P1-1, `tools/lw_stage_ledger.py`)

The stage ledger compares each stage's input and output at a fixed common
scale: BOX resampling by an integer factor (2560x1440 -> 640x360), so a
common-scale pixel whose 4x4 block lies wholly outside an edit is exactly equal
across an identity pair. Calibrated 2026-10-04 with `lw_stage_ledger.py
calibrate` on the 26 real clean pairs whose working came from the LaMa
composite (byte-identical outside its binary mask): outside the declared box
dilated by 19 px (DILATE_PX 15 + 4), max |luma diff| at common scale = 0.0 on
26 of 26. `CHANGE_TOL = 0.5` therefore counts any whole-level change.
