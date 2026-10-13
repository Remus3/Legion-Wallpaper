# Golden set re-frozen under USM 35 - the operator's blessing call, enacted

_2026-09-06. Closes the ROADMAP item `golden-overtarget-refreeze` (opened
LEDGER 149)._

## What was wrong

The 12-case golden baseline froze on 2026-07-05 under `USM_DEFAULT` percent
**70**. The default moved to **35** on 2026-08-02 (settled, do not re-litigate),
and `lw_golden` restated the recipe as a literal so `pipeline_version` reported
"unchanged" straight through the change until `5715cf0` pinned it to the
definition site. Two consequences, both live until tonight:

1. The 2026-09-06 driver regress had to **pin USM back to 70 by hand** or every
   case would have read as driver drift. The frozen set was validating a
   sharpening recipe that had not shipped in five weeks.
2. `1341679-banding` flagged on `lap_ratio` because its 4096x2305 source takes
   the G0 over-target downscale-only branch, which landed 64 minutes AFTER its
   baseline was frozen. Its baseline came from the AI-4x path it no longer
   takes.

Note the two were entangled, not adjacent: 4096x2305 is not exactly 2560x1440,
so `_usm_applies` is True and the downscale-only branch **does** run an unsharp
mask (`usm_applied=True`, confirmed in the regenerate log). The flagged
`lap_ratio` was USM-sensitive.

## What was done

All 12 cases regenerated through the LIVE pipeline (IJN V3 detail DAT2,
USM 35, current branch logic), re-frozen, and self-checked:

    candidates  12 -> 11 spandrel (~35s each) + 1 downscale-only (0.67s)
    freeze      12 cases, pv 6d43a6d4c2d4 -> ed249af6c004
    regress     PASS 12/12, pv_changed=False

`pv_changed=False` is the point: the manifest now hashes to the live pipeline,
so the hand pin is retired and the next regress measures the recipe that ships.

## What moved, and in which direction

Baseline metrics, old (USM 70) -> new (USM 35), all 12 cases:

    msssim     mean +0.0008   worst +0.0019   improves on every case
    lpips      mean -0.0083   worst -0.0213   improves on every case
    halo_pct   mean -0.0229   worst -0.0317   improves on every case
    lap_ratio  mean -0.4220   worst -0.6729   falls on every case

This reproduces the 2026-08-02 census independently and on a different sample:
weakening the mask improves every fidelity measure and costs sharpening. The
old baseline was USM-70-shaped, which is why 11 of 12 could only pass with the
hand pin.

`1341679-banding` now reads `lap_ratio` **0.8416**, below the G1 floor of 1.0.
That is expected and not a gate failure: ADR-006 drops `lap_ratio` from the
gated set for backend `downscale-only` (`lw_first_pass.py:339`), because a
Lanczos downscale of an over-target source is softer than the source at common
scale by construction. Do not read that number as a regression.

## What shipped with it

- `lw_golden candidates` - the verb that regenerates every frozen input through
  the live pipeline. This step was an ad-hoc script both times it was needed and
  did not survive the session that wrote it, which is why the 2026-09-06 regress
  could not be reproduced and this re-freeze had to rebuild it. Each row reports
  the branch taken and whether the USM actually ran.
- `data/golden/cases.json` - the tracked blessed-set definition (slug, input,
  baseline basename, defect axes; no image bytes, per the privacy boundary).
  A re-freeze is now three commands, written down in `docs/research/GOLDEN_SET.md`.
- `data/golden/candidates/` gitignored, same boundary as `inputs/` and
  `baseline/`.

The pre-re-freeze baselines and manifest were copied out of the tree before
`freeze` overwrote them; the manifest's previous revision is in git regardless.
