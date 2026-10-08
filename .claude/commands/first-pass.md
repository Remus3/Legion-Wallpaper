---
description: Stage 1 first pass - best-source selection, ONE AI upscale (IllustrationJaNai via .venv-upscale, else realesrgan-ncnn-vulkan x4plus-anime fallback), ONE Lanczos downscale to >= 2560x1440, light USM, save as _firstworking_##, run the G1 gate (FR metrics at common scale + sharpness/halo checks), then submit to _firstneedauth for operator approval. Use when images sit in 1.First Pass Scratch or the operator says "first pass".
---

> **SUBAGENT-FIRST (standing protocol, operator 2026-06-20).** Always use subagents for substantive work; do not build solo in the main thread.
> 1. **Spec first:** a Plan/design subagent emits the per-image plan (chosen source, upscaler, scale factor, USM params) BEFORE any processing; verify it vs ground truth (`tools/lw_pipeline.py status`, `ops/runtime/pipeline_state.json`, actual file dimensions) - never scaffold on assumptions.
> 2. **New session:** confirm intent + acceptance criteria with the operator (or the Gemini director), re-probe live pipeline state, THEN act.
> 3. **Act via subagents:** per-image worker subagents on disjoint slugs (sole merger) + a read-only `verifier` subagent gate before any "done" claim.
> 4. **Kit v10 (MAIN 0839):** no inline exception. The main session dispatches this whole skill to ONE sub-agent and relays only its final line; the kit hook `ops/fleet_kit/fleet_subagent_first.py` enforces it. See `CLAUDE.md` FLEET-COMMON banner.

Contract references: `docs/research/PIPELINE_STATE_MACHINE.md` (stage semantics 2.8, T3/T4), `docs/research/UPSCALE_TOOLCHAIN.md` (model ladder + install), `docs/research/AUDIT_GATES.md` (G1 gate, section 5.1). Stage doctrine: NEVER double-resample (the old pipeline's softness bug) - exactly ONE AI upscale then exactly ONE Lanczos downscale.

### 0. Preflight (mandatory, before touching any image)

1. Run: `python tools/lw_pipeline.py status`
   - If `tools/lw_pipeline.py` is missing or errors, STOP and report (single-writer rule).
2. Read the tail (last ~20 lines) of `PIPELINE_LOG.md` at the project root - look for prior REJECT lines on the target slugs (rejection notes are the retry hints).
3. Identify targets: slugs in `images\1.First Pass Scratch\` in EDITING substate (a `_firstinitial` present, no `_firstneedauth`).
4. Tooling readiness - each item is an INSTALL TARGET from the `docs/RESTORATION_PLAN.md` install checklist, not an assumption. Check availability HERE and pick the path; never fail mid-image:
   - **Primary upscaler:** `.venv-upscale\Scripts\python.exe` exists AND `import torch; torch.cuda.is_available()` is True AND an IllustrationJaNai model file is present (spandrel-loadable .pth/.safetensors). Missing -> report the exact install steps (venv + torch cu128 + spandrel + model download per RESTORATION_PLAN.md) and fall back.
   - **Fallback upscaler:** `C:\Tools\realesrgan\realesrgan-ncnn-vulkan.exe` with the `realesrgan-x4plus-anime` model (Vulkan; no CUDA/torch dependency). Missing too -> STOP cleanly before any transition and report both install targets.
   - **Metrics (G1):** the metrics venv (pyiqa: MS-SSIM/LPIPS/DISTS) per RESTORATION_PLAN.md. Missing -> run the OpenCV-only subset of G1 (sharpness/halo/banding) and flag the image for operator review instead of auto-passing FR metrics.

### 1. Best-source selection (per slug)

- Compare the `_firstinitial` file against any recovered source from `/intake` provenance (manifest `source_url` + fetched files). Pick the highest-true-resolution, least-compressed source; prefer a recovered clean original over a watermarked rip (recover, do not inpaint, when a clean official source exists).
- If a better source replaces the initial, route it through lw_pipeline (never hand-rename): re-intake or `save-working --from`, recording provenance.
- G0 source gate: resolution >= half the 2560x1440 target (else the upscale factor is too aggressive - flag), decodes clean, sane aspect ratio, not a `-pre` preview file.

### 2. Process: ONE upscale, ONE downscale, light USM

1. AI upscale with the chosen tool (integer factor, typically 4x). Record tool + params.
2. ONE Lanczos downscale to the target: >= 2560x1440, preserving aspect (exact 2560x1440 conformance is the final stage's job; never upscale again after this point).
3. Light unsharp mask with CAPPED amount/radius (the cap is the prevention; the G1 halo detector is the audit).
4. Register the result: `... lw_pipeline.py save-working <slug> --from <path> --tool <name> --params <json>` -> `<slug>_firstworking_##.png`. All milestones after `_firstinitial` are PNG.

Any helper script authored here that spawns subprocesses MUST pass `creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)` (Legion focus-steal rule).

### 3. G1 gate (deterministic, free - per AUDIT_GATES.md 1.4 + 3.1-3.3)

Compute at COMMON SCALE: downscale the output to the source resolution with Lanczos; NEVER upscale the reference (that manufactures a blurry reference and approves soft output).

- Alignment asserts first: integer scale factor, identical aspect, no crop/pad/offset. An unexplained SSIM cliff is an alignment bug before it is a quality bug.
- MS-SSIM >= 0.92 pass; 0.85-0.92 flag; < 0.85 hard fail. LPIPS <= 0.20 pass; 0.20-0.30 flag; > 0.30 hard fail. DISTS advisory (log; LPIPS-bad + DISTS-fine = re-synthesized texture -> flag).
- Laplacian-variance ratio output/source >= 1.0 (ratio < 0.9 = the double-resample softness bug - hard fail); median edge width logged; halo detector (overshoot/undershoot > 8/255 on > 5% of strong edges = flag).
- Banding delta <= 0 (processing must not add band edges).
- Thresholds are calibration seeds (AUDIT_GATES.md 6.4) - log every metric to the manifest regardless of verdict.

Hard fail -> do NOT submit; save the evidence, adjust (different model/params) and loop back to section 2, or queue for the operator with the metric report.

### 4. Submit for authorization

- Gate pass (or flag-with-report): `... lw_pipeline.py submit <slug>` -> `_firstneedauth.png`.
- Operator decides via `... lw_pipeline.py approve <slug>` (-> `_firstdone` + move to `images\2.First Pass Done\`) or `... lw_pipeline.py reject <slug> --note "<reason>"` (-> next `_firstworking_##`). This command never self-approves.

### 5. Log/state update + banner

1. Confirm `PIPELINE_LOG.md` gained SAVE_WORKING/SUBMIT lines per image and `ops/runtime/pipeline_state.json` is fresh (re-run `... lw_pipeline.py scan` if in doubt).
2. Print the closing banner (one ASCII line):

```
LW FIRST PASS | processed=<n> submitted=<k> gate-fail=<f> flagged=<g> | upscaler=<janai|realesrgan> | awaiting-auth=<q> | next: approve/reject via lw_pipeline
```

## Failure catalogue

Every rule above traces to a real failure. Each row cites the LEDGER item that recorded it; `drift_guard` checks this table exists and that every cited item is real (`tools/lw_failure_catalogue.py`). Add a row when a new failure teaches a rule.

| Symptom | Cause | How it was caught | Fix | LEDGER |
|---|---|---|---|---|
| The better upscaler hard-failed G1 on 8 of 10 images. | A band_delta greater-than-0 rule failed on about 0.004 of noise. | IJN vs fallback A/B with identical gate code. | band_delta demoted to an advisory flag above 0.05. | LEDGER 3 |
| Downscale-only outputs passed or failed G1 at random. | The lap_ratio floor swung 0.75 to 1.20 on near-identical clean downscales. | A non-mutating probe on three 4K sources. | ADR-006 drops only the lap floor for downscale-only. | LEDGER 11 |
| 63 of 230 manifests were missing DISTS. | At 8K common scale DISTS ran out of memory on both the GPU and system RAM. | A live probe plus a blast-radius count of failed manifests. | MAX_COMMON_PIXELS cap in lw_g1_gate, plus empty_cache between metrics. | LEDGER 32 |
| The backfill produced garbage DISTS of 0.75 on fullview slugs. | PIL crop() zero-pads a box larger than the image. | Cross-checked against the recorded MS-SSIM of 0.99. | Redone through production condition_source with an asserted src_dims. | LEDGER 32 |
| An at-target source showed halo_pct 0.0711. | A no-op resize still applied USM, which manufactured the halo. | The G1 halo flag during the refs-46 escalation. | _usm_applies() skips USM only when the input already equals the target size. | LEDGER 46 |
| The pixel-identity test passed against the bug. | A saturated 0/255 step edge is a fixed point of UnsharpMask. | It was the one required test that never went red. | Fixture re-cut on a mid-tone edge, with the reason in the docstring. | LEDGER 46 |
| Alpha was flattened with no trace in the audit. | first_pass discarded RGBA and P+tRNS alpha silently. | Four investigation cycles over the refs-46 sources. | Audit now records source_mode and alpha_flattened. | LEDGER 56 |
| A slug died with a SyntaxError, not a quality failure. | An apostrophe in a filename closed a hand-built r'...' literal. | The batch lost kai-sa during /first-pass. | _pylit() via json.dumps at both call sites and in run_fr_metrics. | LEDGER 143 |
| A crop offset override would have been silently lost. | list(crop_sides) on a dict records only its keys. | Found while adding the --crop-overrides offset grammar under TDD. | The recording call site was fixed in the same commit. | LEDGER 173 |
| Posterized (banded) output does not raise band_delta. | The metric counts isolated 1-px steps after a LANCZOS downscale that smears every step. | The fault-proven gate board: posterize step 8 and 32 lower it, BROKEN 0/12. | Retired from the first pass: G1.cambi_delta (CAMBI mlc=5 at output scale, flag > 2.0, None without ffmpeg) is the banding arm; band_delta is recorded under info_metrics only. | LEDGER 244, 265 |
