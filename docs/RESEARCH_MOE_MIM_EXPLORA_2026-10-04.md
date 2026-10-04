# Research: MoE, MIM and ExPLoRA alternatives for the LW pipeline (2026-10-04)

Scope: three algorithm families the operator named - Mixture-of-Experts
restoration, masked image modeling (MIM), and ExPLoRA / PEFT domain
adaptation - mapped onto the real pipeline (`docs/RESTORATION_PLAN.md`), the
settled decisions (CLAUDE.md "Settled", ADR-004, ADR-009) and the four
acknowledged gate-board rows (`docs/GATE_BOARD.md`,
`config/gate_board_ack.json`, LEDGER 244). Research only: no model was
downloaded or trained, no GPU job was run.

Method and trust levels:
- Every paper/repo row was checked by a research sub-agent against its arXiv
  abstract page and the GitHub README / LICENSE (2026-10-04). Anything not
  confirmed there is marked UNVERIFIED. VRAM and GPU-hour figures marked EST
  are estimates, not measurements.
- Two facts were measured locally in this session and are marked MEASURED:
  the CAMBI smoke test (section 3.3) and the presence of an anime LaMa in the
  operator's IOPaint install (section 5.2).
- Spot re-checked by the author: ExPLoRA venue (ICML 2025, arXiv 2406.10973)
  and the lama-manga model card (MIT, Big-LaMa fine-tuned on ~300k manga and
  anime images).
- Licences matter here in two ways: weights are never tracked (public repo,
  private use), but CODE vendored into this Apache-2.0 tree must be
  Apache-compatible. NC / research-only / GPL code stays out of the tree.

## 0. Bottom line

1. **MoE / degradation-routed all-in-one models do not fit LW today.** All 22
   candidates are trained on natural photos, mostly on the 3- or 5-task set
   (noise, rain, haze, blur, low-light). Only DA-CLIP and MoE-DiffIR cover JPEG;
   none covers banding, overlays or watermarks; none has illustration evidence.
   They also cannot satisfy ADR-009's reopen condition, because LW has no
   per-image engine labels to train or validate a router on (the 50 rejects
   were three blanket per-engine verdicts).
2. **MIM pretraining (MIT, MPI, DegAE, RAM) does not touch the broken gates.**
   It is a training recipe for generalizing restorers. The useful MIM idea is
   the DETECTOR side: mask the suspect pixels, reconstruct them from context,
   and score the stroke-aligned difference against a shifted-mask null. That
   is the best candidate found for G2.text_residue.
3. **ExPLoRA is real and cheap-ish but solves the wrong problem first.**
   Faint residue (+4 levels), output-scale banding and a 1-2 px seam are
   low-level signals that DINOv2 / MAE features are built to be invariant to;
   adaptation does not change that. Run stock-DINOv2 patch kNN (AnomalyDINO,
   training-free) first; ExPLoRA only if that fails for a demonstrable domain
   reason.
4. **The cheapest real wins are not in the three families:** CAMBI from the
   local ffmpeg's libvmaf for G1.band_delta (with a non-default parameter -
   the default reproduces band_delta's blindness, MEASURED), a contour-normal
   step measure for G2.seam, and the anime-tuned Big-LaMa that the operator's
   own IOPaint already ships.

## 1. Where the pipeline hurts (the targets)

| target | stage / gate | measured hole (LEDGER 244) | clears_when (config/gate_board_ack.json) |
|---|---|---|---|
| G2.text_residue | clean verify | OCR+MSER fires on 7/12 restored busy regions, misses a +4-level credit line on the other 5 | catches credit_line_4lv 12/12 with 0 false positives on restored regions |
| G1.band_delta | first G1 | counts 1-px steps after a LANCZOS downscale; posterize step 8 and 32 LOWER it | a banding metric PROVEN 12/12 under posterize_8 |
| G2.seam | clean verify | SSIM of the outside ring vs its blur = ring texture; a perfect fill reads < 0.92 on 9/12; live 22/41 verifies flagged | passes clean, fails seam_offset_24lv on 12/12, calibrated on real clean pairs |
| G1.lpips | first G1 | 4x down-up on coven-ashe moves LPIPS 0.037 -> 0.059 vs a 0.12 bar (lap_ratio catches it) | PROVEN 12/12 under downup_x4, fault not rescaled |
| engine choice | clean | ladder never won (ADR-009) | reopen: a measure predicting operator verdict on held-out slugs, or an engine beating `_01` where `_01` was approved |
| upscaler | first | V3 detail DAT2 primary (ADR-004) | reopen: golden A/B beats V3 on MS-SSIM/LPIPS/halo |

Fault amplitudes are fixed by the board (calibrated on operator captures; not
rescaled per subject). Every experiment below is judged by that board.

## 2. Family 1 - Mixture-of-Experts and routed all-in-one restoration

### 2.1 Candidates

| name | what it is | paper / code | licence | weights | training domain | fit on 12 GB (EST) |
|---|---|---|---|---|---|---|
| MoCE-IR (CVPR 2025) | MoE whose experts differ in compute and receptive field; cheap experts favoured, unneeded ones skipped | arxiv.org/abs/2411.18466, github.com/eduardzamfir/MoCE-IR | CC BY-NC-SA 4.0 | yes (S, base) | photos; 3-task, 5-task, CDD11 | yes, 256-512 tiles |
| MoE-DiffIR (ECCV 2024) | MoE prompts extracting codec-specific priors from Stable Diffusion | arxiv.org/abs/2407.10833, github.com/renyulin-f/MoE-DiffIR | no licence file | yes | photos; 21 compression degradations, 7 codecs incl. JPEG/WebP | ~6-10 GB tiled; slow; generative |
| DA-CLIP (ICLR 2024) | CLIP + controller giving a degradation embedding (a degradation classifier) driving an IR-SDE restorer | arxiv.org/abs/2310.01018, github.com/Algolzw/daclip-uir | MIT | yes (HF) | photos; 10 types incl. JPEG; README warns about real-world shift | classifier ViT-B/32 cheap; restorer slow |
| PromptIR (NeurIPS 2023) | learned degradation prompts on a Restormer backbone | arxiv.org/abs/2306.13090, github.com/va1shn9v/PromptIR | MIT | yes | photos; noise/rain/haze | yes, tiled |
| InstructIR (ECCV 2024) | restoration steered by a text instruction | arxiv.org/abs/2401.16468, github.com/mv-lab/InstructIR | MIT | yes (HF) | photos; 5 tasks, no JPEG | yes |
| AutoDIR (2023) | CLIP quality step picks the dominant degradation, latent diffusion restores it | arxiv.org/abs/2310.10123, github.com/jiangyitong/AutoDIR | no licence file | yes | photos; no JPEG | SD-class, slow |
| AdaIR (ICLR 2025) | frequency mining/modulation all-in-one | github.com/c-yn/AdaIR (arXiv UNVERIFIED) | MIT | yes | photos; 5 tasks | yes |
| DFPIR (CVPR 2025) | degradation-guided channel shuffle + attention masking | arxiv.org/abs/2505.12630, github.com/TxpHome/DFPIR | no licence file | yes | photos | yes |
| Perceive-IR (TIP 2025) | three-tier CLIP quality prompts | arxiv.org/abs/2408.15994, github.com/House-yuyu/Perceive-IR | Apache-2.0 | Baidu only | photos | yes |
| AnyIR (TMLR 2026) | spatial-frequency degradation adaptation, ~82% fewer params than baseline | arxiv.org/abs/2504.14249, github.com/Amazingren/AnyIR | no licence file | link UNVERIFIED | photos | yes |
| DiffUIR (CVPR 2024) | conditional diffusion mapping all degradations to one shared distribution | arxiv.org/abs/2403.11157, github.com/iSEE-Laboratory/DiffUIR | MIT | yes (0.89M-36M) | photos; blur/low-light/rain/snow/haze | yes |
| RAM / RAM++ (ECCV 2024 / 2025) | MIM pretrain then fine-tune; RAM++ adds DINOv2 regularization | arxiv.org/abs/2409.19403, arxiv.org/abs/2509.12039, github.com/Dragonisss/RAM | Pi-Lab 1.0, non-commercial | yes | photos; JPEG coverage UNVERIFIED | yes |
| UniRes (ICCV 2025) | combines specialist diffusion models during sampling | arxiv.org/abs/2506.05599 | no code | no | UNVERIFIED | - |
| SeemoRe (ICML 2024) | lightweight SR from a mixture of low-rank experts | arxiv.org/abs/2402.03412, github.com/eduardzamfir/seemoredetails | CC BY-NC-SA 4.0 | yes | bicubic photo SR | yes; below DAT2 class |
| MoR (AAAI 2026) | each LoRA rank of a diffusion SR model is an expert, CLIP degradation score sets active count | arxiv.org/abs/2511.16024 | no code | no | photos | - |
| AgenticIR (ICLR 2025) | LLM+VLM perceive/schedule/execute/reflect over a restorer toolbox | arxiv.org/abs/2410.17809, github.com/Kaiwen-Zhu/AgenticIR | no licence file | needs DepictQA | photos | heavy |
| 4KAgent (2025) | AgenticIR extended to 4K | arxiv.org/abs/2507.07105, github.com/taco-group/4KAgent | Apache-2.0 | yes + VLM/API keys | photos + AI-generated 4K sets (only non-photo evidence found) | "low GPU" mode < 24 GB |
| JarvisIR (CVPR 2025) | VLM picks expert tools (driving / weather) | arxiv.org/abs/2504.04158, github.com/LYL1015/JarvisIR | MIT | yes | photos; no JPEG tool | heavy |
| MAIR (IJCV 2026) | splits degradations into scene/imaging/compression and reverses compression first | arxiv.org/abs/2503.09403 | code "will be made available" | no | photos | - |

Not found as named: "AMIR" resolves only to a MICCAI 2024 medical
all-in-one paper (irrelevant); "MoA-IR" not found (nearest: M2Restore,
arxiv.org/abs/2506.07814, code UNVERIFIED).

### 2.2 Mapping to LW

- **Stage:** clean (engine choice) and the first-stage JPEG pre-pass. Nothing
  here touches watermarks, overlays or banding.
- **Against ADR-009:** the policy is not "one engine forever", it is "no
  automatic chain on REJECT"; the ADR names the reopen condition (a measure
  that predicts the operator's verdict on held-out slugs, not seam and not
  anything that rises with edit area). An MoE router is exactly such a
  measure, so it would have to be validated on held-out OPERATOR verdicts.
  LW has none at the right grain: the 50 rejects are three blanket
  per-engine verdicts with identical notes. A router cannot be trained or
  validated on that; it would learn the engine, not the image.
- **The one usable piece:** DA-CLIP's degradation embedding (MIT, ViT-B/32,
  cheap) as a triage FEATURE - e.g. "JPEG-heavy source, run the FBCNN pre-pass
  / route to V3 denoise" vs "clean digital art, V3 detail". That is routing at
  the first stage, not a cleaning ladder, so ADR-009 does not bind it; ADR-004
  does if it ever swaps the primary upscaler.
- **Design note worth keeping:** MAIR's ordering (compression first) already
  matches RESTORATION_PLAN 2.3's ORDERING NOTE (FBCNN before upscale).

### 2.3 Experiment (low priority)

E-MoE-1: DA-CLIP degradation-embedding triage. Score the 302-image corpus
once (CPU/GPU minutes), hand-label 40 sources jpeg-heavy / clean (operator
or vision 2AFC), report AUROC of the JPEG logit. Acceptance: AUROC >= 0.9 on
held-out labels; only then wire it as a manifest FLAG (never a gate, never a
second engine). Cost ~0.5 day. Expected gain: small (it automates a choice
already made by source format and FBCNN's own QF estimate).

Reopen evidence for ADR-009 from this family: a router whose choice beats
`_01` on slugs where `_01` was approved, judged by the operator blind, with
edit area held equal. None of the surveyed work supplies that.

## 3. Family 2 - Masked image modeling (MIM)

### 3.1 MIM pretraining for restoration / SR (low relevance)

| name | what it is | paper / code | licence | weights | LW relevance |
|---|---|---|---|---|---|
| Masked Image Training, denoising (CVPR 2023) | masks input pixels and attention features so denoising generalizes to unseen noise | arxiv.org/abs/2303.13132, github.com/haoyuc/MaskedDenoising | not stated | one sigma=15 model | training recipe only |
| MPI, zero-shot denoiser (NeurIPS 2024) | masked pretraining, then iterative fill of a noisy image, no fine-tune | arxiv.org/abs/2401.14966, github.com/krennic999/MPI | not stated | yes | a ready masked-context reconstructor, photo-trained |
| DegAE (CVPR 2023) | degradation autoencoder pretraining | CVF open access; github.com/lyh-18/DegAE_DegradationAutoencoder | not stated | yes | none |
| HAT same-task pretraining (CVPR 2023) | large-data same-task pretraining for SR | arxiv.org/abs/2205.04437, github.com/XPixelGroup/HAT | Apache-2.0 | yes incl. Real_HAT_GAN | possible upscaler A/B arm, photo-trained |
| RAM / RAM++ | see 2.1 | - | non-commercial | yes | none for gates |

A "MaskSR / MIT-SR" image-SR paper by that name was NOT found (MaskSR is a
speech paper); UNVERIFIED.

### 3.2 MIM / MAE-prior inpainting

| name | paper / code | licence | weights | note |
|---|---|---|---|---|
| MAT, Mask-Aware Transformer (CVPR 2022) | arxiv.org/abs/2203.15270, github.com/fenglinglwb/MAT | research use only | Places/CelebA-HQ/FFHQ at 512 | photo/face trained; 512 multiples |
| MAE-FAR (ECCV 2022) | arxiv.org/abs/2208.01837, github.com/ewrfcas/MAE-FAR | CC BY-NC 4.0 | FFHQ/Places2 | MAE features as inpaint prior |
| ZITS++ (TPAMI 2023) | arxiv.org/abs/2210.05950, github.com/ewrfcas/ZITS-PlusPlus | Apache-2.0 | 256/512 | line/edge structure prior; relevant to line continuity at a seam |

None is anime-trained; for LW's mask contract the anime Big-LaMa (5.2) is the
better inpaint arm. MIM inpainters matter here mainly as RECONSTRUCTORS for a
detector.

### 3.3 MIM / reconstruction as a DETECTOR - the broken rows

Prior art (concept): MAEDAY (arxiv.org/abs/2211.14307; code "coming soon", no
weights), RIAD (Pattern Recognition 2021; unofficial code only), InTra
(arxiv.org/abs/2104.13897, code UNVERIFIED), EAR (arxiv.org/abs/2310.04010,
DINO-attention-chosen masks, no code), DRAEM (arxiv.org/abs/2108.07610,
github.com/VitjanZ/DRAEM, MIT: reconstruction + segmenter trained on
synthetic anomalies). Warning paper: UniAD (arxiv.org/abs/2206.03687) - a
reconstructor that SEES the anomaly rebuilds it (identity shortcut).
Non-reconstruction baselines: PatchCore (arxiv.org/abs/2106.08265,
Apache-2.0), SimpleNet (CVPR 2023, MIT), AnomalyDINO
(arxiv.org/abs/2405.14529, github.com/dammsi/AnomalyDINO, Apache-2.0,
training-free DINOv2 patch kNN).

No paper was found that detects faint watermark residue by inpaint-and-
compare. The design below is LW's own synthesis of RIAD/MAEDAY with a
matched filter.

**G2.text_residue - "re-inpaint and matched-filter" (E-MIM-1).**
1. Take the glyph/stroke mask the cleaning pass already has for the mark
   (detection boxes + OCR strokes); dilate 2-3 px so the reconstructor never
   sees residue pixels (avoids UniAD's identity shortcut by construction).
2. Re-inpaint those strokes on the CLEANED output with LaMa (same engine, same
   venv) -> B, a residue-free estimate of the background.
3. R = output - B (luma). Score S = mean(R over stroke pixels) / sigma_null,
   where sigma_null comes from the same statistic with the stroke mask moved
   to 50-100 random offsets inside the restored region (same LaMa call per
   offset, batched).
4. A real residue is a same-sign offset coherent along the strokes; averaging
   over N stroke pixels lifts +4 levels by about sqrt(N) against a per-pixel
   LaMa error that is random with respect to the moved masks. The shifted-mask
   null is the false-fire control the OCR+MSER arm lacks (the 7/12 busy-art
   frames).
- Risks: LaMa's per-pixel error on busy art is far above 4 levels (only the
  aggregated, null-calibrated score can work); a tight mask leaks residue back
  through context (dilate); the stroke mask must come from the PRE-clean
  detection (available) - this is a verify-time check, not a blind detector.
- Fallback / companion (DRAEM-style, E-MIM-1b): synthesize faint text
  overlays (alpha 1-5 percent, the board's +4-level calibration) on clean
  corpus tiles in memory and train a small segmenter; cheap on 12 GB, no image
  bytes tracked (fixtures generated at run time from the gitignored corpus).
- Acceptance = the row's clears_when: credit_line_4lv caught 12/12 AND 0
  false positives on the 12 clean restored regions; plus no new fire on the
  operator-approved `_cleandone` set. Cost ~1-2 days, GPU minutes per prove.

**G1.band_delta - CAMBI (E-BAND-1).** CAMBI (Netflix, contrast-aware
multiscale banding index, arxiv.org/abs/2102.00079) ships in libvmaf
(BSD-2-Clause-Patent), no-reference, CPU, runs on the 2560x1440 output with
no downscale (the exact failure of band_delta). MEASURED 2026-10-04 on the
local ffmpeg 8.1.1 (gyan full build, libvmaf with cambi available) on a
synthetic 2560x1440 luma ramp (16 -> 240):

| subject | cambi (default, max_log_contrast=2) | cambi max_log_contrast=5 |
|---|---|---|
| clean 8-bit ramp | 10.34 | 16.81 |
| same ramp posterized step 8 | 0.00 | 44.43 |

So DEFAULT CAMBI reproduces band_delta's blindness on the board's own fault:
an 8-level step exceeds its contrast window and is read as an edge, not a
band. With max_log_contrast=5 (the maximum) the posterized ramp scores 2.6x
the clean one. Synthetic only - real art has edges that a widened window may
also count. Experiment: add a `G1.cambi` candidate row computed via
`ffmpeg -lavfi libvmaf=feature='name=cambi\:max_log_contrast=5'` (escaping
matters; the unquoted form errors), on output only and as a delta vs the
upscaled-input when available; calibrate the bar on the 12 golden frames.
Acceptance = clears_when (posterize_8 PROVEN 12/12, clean passes 12/12) and
no new FLAG on the 17 current needauth items that the operator then approves.
Cost ~0.5 day, CPU only. Alternates: BBAND (arxiv.org/abs/2002.11891,
github.com/google/bband-adaband, Apache-2.0, MATLAB only, archived - needs a
port), DBI deep banding index (ICASSP 2021, TF2, code licence not seen),
deepDeband (arxiv.org/abs/2110.08569, MIT) as a remover not a gate. FFmpeg
deband/gradfun are removers; blurdetect is not a banding metric.

RESULT 2026-10-04 (R1, LEDGER 263): ACCEPTED. On the 12 golden outputs at
2560x1440, clean vs posterize_8: output-only mlc=5 ranks banded above clean
12/12, but one absolute bar separates only 11/12 (dfz5w2g banded 3.00 below
other frames' clean up to 4.90); default mlc=2 ranks 7/12 (bar 3/12). The
delta vs the source (Lanczos-resized to the output size) separates 12/12:
clean -0.51..1.21, banded 3.00..14.17. Shipped as `lw_g1_gate.cambi_delta`
+ live-table flag bar 2.0 + board row G1.cambi_delta: PROVEN 12/12. Live
census on the 131 current `_firstneedauth` frames: 0 flagged (max 1.74,
median 0.00). Not yet computed in the live first pass (ROADMAP R1b); the
band_delta arm stays pinned until that wiring retires it.

**G2.seam - contour-normal step (E-SEAM-1).** Nothing in the literature is a
ready seam metric (re-inpainting self-consistency, arxiv.org/abs/2405.16263,
no code; "seam gradient" scores seen only in search snippets, UNVERIFIED).
Design (LW's own): sample short normals along the mask contour; per normal,
step = |median(inner 2-4 px band) - median(outer 2-4 px band)| / local MAD;
score = robust mean of the signed step; null = the same statistic on the
contour shifted 8 px outward (texture-only). A +24-level fill offset is a
large coherent signed step; ring texture is not. Calibrate on the 26 real
clean pairs already used by the stage ledger (LaMa composite, byte-identical
outside the mask). Acceptance = clears_when (clean passes, seam_offset_24lv
fails 12/12) AND the live flag rate on the 41 recorded verifies falls from
22/41 to a rate the operator's verdicts support. Cost ~0.5 day, numpy only.
ZITS++ line maps are an optional add-on for line-continuity seams.

RESULT 2026-10-04 (R3, LEDGER 264): ACCEPTED. Measured on the 12 golden G2
subjects (Coons fill, clean vs seam_offset_24lv), the 26 real LaMa clean
pairs (`4.Cleaning Done` cleandone + the saved `_mask.png`, else the exact
changed-pixel set; same pair filter as `lw_stage_ledger.calibrate`) and those
26 pairs offset +24, plus the 37 recorded live verifies whose mask and
candidate are on disk (41 recorded). Eight variants (signed / abs median,
mean, MAD-normalized, minus the 8 px-shifted null) all separated 12/12 with
0/26 real FP; the simplest won the widest gap: score = |median over 16 px
contour cells of median(inner 1-3 px band) - median(outer 1-3 px band)| in
luma levels. Golden clean 0.01..2.36, seam_offset_24lv 21.64..24.83; real
clean 0.00..2.06 (0/26 over the bar), real offset copies 14.35..; flag bar
SEAM_STEP_MAX = 6.0 (about the geometric middle of 2.36 and 14.35). The null
added no separation and was dropped. Live: 1/37 flagged
(spirit-blossom-ahri-mono-01 6.28, unreviewed) vs 22/37 under ring SSIM.
Shipped as `lw_clean_pass.seam_step` + `verify_verdict(seam_step=...)` flag +
board row G2.seam_step. LIVE since R3b (LEDGER 266): `_auto_inpaint` passes
seam_step to verify_verdict; the ring-SSIM seam flag and G2.seam row are retired.

## 4. Family 3 - ExPLoRA and PEFT domain adaptation

### 4.1 ExPLoRA

- Khanna, Irgau, Lobell, Ermon, "ExPLoRA: Parameter-Efficient Extended
  Pre-training to Adapt Vision Transformers under Domain Shifts", ICML 2025,
  arxiv.org/abs/2406.10973, github.com/samar-khanna/ExPLoRA (Apache-2.0;
  merged ViT-B/L DINOv2 and ViT-L MAE checkpoints on HF for satellite data).
- Method: from a natural-image DINOv2 or MAE ViT, fully unfreeze 1-2 blocks,
  LoRA (rank 32-64) on Q/V elsewhere, unfreeze norms, continue the SAME
  self-supervised objective on unlabeled target-domain images; then linear
  probe or LoRA fine-tune for the task. ~5-10 percent of weights trained.
- Reported: fMoW-RGB linear probe 77.48 vs 69.00 stock DINOv2; also
  Sentinel, RESISC-45, Camelyon17, GlobalWheat. Hardware one RTX 6000 Ada
  48 GB or 4x A4000; 200k iterations at effective batch 1024. Absolute
  GPU-hours not stated (UNVERIFIED). All target sets are >= tens of thousands
  of images; nothing near LW's ~809.
- LW fit (EST): ViT-B/14, rank 32, one unfrozen block, bf16 + torch SDPA (no
  Triton), batch 32-64 with accumulation, random multi-crops from the 517
  cleaned + 292 reference images: ~10-20k iterations, ~2-6 GPU-h on the 5070
  (ViT-L ~3x). Risk: ~100x less data than any paper setting; the DINO
  objective may collapse/overfit - the MAE objective is safer at this scale.

### 4.2 Related PEFT and anime-domain work

| name | what it is | paper / code | licence | weights | compute |
|---|---|---|---|---|---|
| AdaptIR (NeurIPS 2024) | MoE adapter on frozen IPT/EDT, 0.6 percent params | arxiv.org/abs/2312.08881, github.com/csguoh/AdaptIR | Apache-2.0 | base models only | ~8 h on a 3090 |
| LoRA-IR | CLIP-routed mixture of low-rank experts, all-in-one | arxiv.org/abs/2410.15385, github.com/shallowdream204/LoRA-IR | Apache-2.0 | yes (HF) | not stated |
| AdaptSR (2025) | LoRA moves bicubic SR models (SwinIR, DRCT...) to real degradations; ~matches full fine-tune | arxiv.org/abs/2503.07748 | repo 404, UNVERIFIED | UNVERIFIED | ~4 h on a 4090 (SwinIR) |
| SRTTA (NeurIPS 2023) | per-image test-time adaptation by re-degrading the input | arxiv.org/abs/2310.19011, github.com/DengZeshuai/SRTTA | MIT | EDSR | per-image time UNVERIFIED |
| Rein (CVPR 2024) | PEFT adapter on DINOv2 for domain-generalized segmentation | arxiv.org/abs/2312.04265, github.com/w1oves/Rein | UNVERIFIED | yes | - |
| APISR (CVPR 2024) | anime SR with a compression-predicting degradation model; 2x/4x incl. DAT-Small | arxiv.org/abs/2403.01598, github.com/Kiteretsu77/APISR | GPL-3.0 (academic disclaimer) | yes | trains on one 3090/4090 |
| traiNNer-redux | the-database's training framework (IllustrationJaNai's ecosystem) | github.com/the-database/traiNNer-redux | Apache-2.0 | - | DAT2 fine-tune documented (strict_load_g, lr 1e-4); native LoRA UNVERIFIED |
| WD EVA02-Large tagger v3 | Danbooru-trained anime feature extractor (semantic) | huggingface.co/SmilingWolf/wd-eva02-large-tagger-v3 | Apache-2.0 | yes | - |
| DINOv3 | newer self-supervised ViT | github.com/facebookresearch/dinov3 | custom DINOv3 licence (not Apache) | yes | - |

No public DINOv2 checkpoint adapted to anime was found (UNVERIFIED that none
exists). No illustration distortion-IQA model was found ("AnimeIQA",
"ArtIQA" not found); the nearest are aesthetics sets (APDDv2,
arxiv.org/abs/2411.08545).

### 4.3 What adaptation could buy LW, honestly

- **Detectors (residue/seam/band):** an adapted backbone tightens the
  "normal illustration patch" manifold for patch-kNN anomaly maps. But
  DINOv2 patches are 14 px at ~518 px input and largely invariant to
  few-level offsets by design; a +4-level, ~2 percent alpha credit line is
  very unlikely to move a patch feature (judgement, not measured). The
  low-level gates are better served by section 3.3's explicit statistics.
- **LPIPS replacement (G1.lpips):** what fixes a photo-trained perceptual
  metric is CALIBRATION of a linear head on 2AFC judgments (operator
  approve/reject history, existing vision 2AFC), on any backbone - minutes of
  compute. ExPLoRA alone does not produce a metric. Note: G1.lpips is already
  covered on its failing subject by lap_ratio (ack entry), so this is low
  priority.
- **The SR model itself:** fine-tuning V3 DAT2 (traiNNer-redux, full fine-tune
  at batch 4-6, lq 48-64, bf16; EST 5-15 GPU-h) is feasible on 12 GB. TRAP:
  the 517 approved images are V3 output downscaled to 2560x1440 - using them
  as HR targets is self-distillation and teaches V3 to reproduce itself. Valid
  HR = native high-res originals / reference images at or above output scale,
  degraded with a corpus-matched chain (JPEG/WebP, DeviantArt preview
  resampling; copy APISR's IDEA, not its GPL code). A fine-tune inherits
  IllustrationJaNai's licence (V1 DAT2 CC-BY-NC-SA-4.0; V3 UNVERIFIED, likely
  the same) - fine for private use, weights never tracked.

### 4.4 Experiment

E-PEFT-1 (gated two-step):
1. AnomalyDINO zero-shot, stock DINOv2 ViT-B, memory bank = patches from the
   approved `_cleandone` set, query = the 12 golden restored regions clean vs
   with credit_line_4lv planted (in memory). Metric: patch AUROC and the
   board's clears_when. Cost ~0.5 day, GPU minutes.
2. Only if (1) fails AND a domain diagnosis says the gap is the backbone
   (e.g. clean busy-art patches sit far from the bank while planted ones do
   not separate), run ExPLoRA-MAE ViT-B on multi-crops (EST 2-6 GPU-h,
   background, progress file) and repeat (1).
Acceptance: AUROC >= 0.95 and clears_when met. Expected outcome: (1) likely
fails on +4 levels (judgement); the value is closing the ExPLoRA question
with a measured negative rather than a guess.

## 5. Other strong alternatives (brief)

### 5.1 Upscale (stage first; ADR-004 binds)

- **No IllustrationJaNai newer than V3** (MangaJaNai releases page: 3.0.0,
  2024-11-26, V3 detail + V3 denoise; still a pre-release). No 2025-2026
  illustration model shown to beat it was found (UNVERIFIED that none exists).
- **APISR DAT-Small 4x** (anime-native, feed-forward, GPL code - run it
  out-of-tree, never vendor) is the one reasonable A/B arm.
- HAT Real_HAT_GAN (Apache-2.0), DRCT (MIT): photo-trained, A/B arms only.
- MambaIR/MambaIRv2: needs mamba_ssm/causal_conv1d CUDA kernels; avoid on
  Windows sm_120.
- Diffusion-prior SR: only **PiSA-SR** (github.com/csslc/PiSA-SR, CVPR 2025,
  Apache-2.0, built-in tiling, explicit pixel-vs-semantic fidelity dials) is
  even a candidate, and only as an opt-in rescue for very low-res sources.
  Avoid SUPIR, HYPIR (non-commercial, photo priors), StableSR (README: >= 18 GB
  tiled), DreamClear, DiT4SR (VRAM / 2 GPUs), LucidFlux, FLUX.1-Fill (12B,
  non-commercial, photo prior). OSEDiff, SeeSR, InvSR, DiffBIR fit but
  hallucinate texture on cel shading.
- **Thera** (arxiv.org/abs/2311.17643, TMLR 2025): arbitrary-scale SR with
  analytic anti-aliasing - conceptually a principled replacement for the
  4x-then-Lanczos step; code appears JAX/Linux (UNVERIFIED). Watch only.
- ADR-004 reopen evidence: `tools/lw_golden.py regress` A/B on the golden set
  beats V3 on MS-SSIM and halo AND on LPIPS plus lap_ratio (LPIPS alone is
  BROKEN on coven-ashe), with the operator's blind 2AFC agreeing.

### 5.2 Inpainting (stage clean; ADR-009 binds)

- **anime-manga Big-LaMa** - Big-LaMa fine-tuned on ~300k manga/anime images
  (HF mayocream/lama-manga, MIT, ~989 MB safetensors; original
  `anime-manga-big-lama.pt` from the IOPaint author's models release).
  MEASURED: the operator's installed IOPaint 1.6.0 already ships it as model
  `anime-lama` (`iopaint/model/lama.py:68`, class `AnimeLaMa`, URL + md5
  pinned at lines 22-27). Same architecture and mask contract as LW's LaMa,
  so G2.outside_identity (byte-identical composite) is unaffected.
- MI-GAN (github.com/Picsart-AI-Research/MI-GAN, MIT, ONNX): tiny, ~LaMa
  quality or below. MAT: research-only. BrushNet/PowerPaint/FLUX-Fill:
  generative, high hallucination.
- Visible-watermark SOTA: SLBR (ACM MM 2021, 256 px CLWD, no licence),
  SplitNet (no licence); no 2024-2026 visible-watermark remover with usable
  weights found. The detect -> mask -> LaMa design stands.

### 5.3 JPEG

- FBCNN (current, Apache-2.0) stays. JDEC (github.com/WooKyoungHan/JDEC,
  CVPR 2024, BSD-3-Clause) decodes from the DCT coefficients, so it only
  applies to untouched original .jpg files; tested on 24 GB (12 GB fit
  UNVERIFIED). IllustrationJaNai V2 DeJPEG variants exist in MangaJaNai
  2.0.0 - an in-family illustration de-JPEG option.

## 6. Settled decisions - what would reopen each

| settled item | this research's verdict | evidence that would reopen it |
|---|---|---|
| ADR-004 V3 detail DAT2 primary | stands; no newer illustration model found | golden A/B beating V3 on MS-SSIM, halo, LPIPS + lap_ratio, operator blind 2AFC agreeing (APISR or a corpus fine-tune are the only plausible challengers) |
| ADR-009 one engine per submission | stands; MoE routers cannot be validated on LW's per-engine labels | a router/measure predicting operator verdict on held-out slugs with edit area held equal, or an engine beating `_01` where `_01` was approved. An anime-lama SWAP is an engine choice, not a ladder - it is tested as a replacement, never chained |
| overlay_score detection-only (LEDGER 101-103) | the E-MIM-1 score is likewise a residue DETECTION verify flag, not a removal-quality gate that could reward bigger repaints | a legibility measure validated as a ship gate |
| ADR-008 vision reviewer flags only | untouched | - |
| USM_DEFAULT (1.2, 35, 3) | untouched; CAMBI is NR on banding, not halo | a fidelity-plus-halo census |
| ADR-007 G1 FR budget 3840x2160 | CAMBI runs at output scale, NR - no FR budget impact | - |
| repo public, no image bytes | all experiments plant faults in memory on the gitignored golden set; only numbers land in tracked files | - |

## 7. Ranked shortlist - top 5 experiments

| rank | experiment | gate / stage | cost | expected gain |
|---|---|---|---|---|
| 1 | E-BAND-1: CAMBI with max_log_contrast=5 at 2560x1440 as the banding row | G1.band_delta | ~0.5 day, CPU, tool already on disk | DONE 2026-10-04 (LEDGER 263): delta vs source separates 12/12; G1.cambi_delta PROVEN 12/12; live wiring = R1b |
| 2 | E-MIM-1: re-inpaint + stroke-aligned matched filter with shifted-mask null (+ DRAEM-style synthetic segmenter if needed) | G2.text_residue | ~1-2 days, GPU minutes per prove | HIGH if it works - the only row tied to the zero-watermark bar; medium probability |
| 3 | E-SEAM-1: contour-normal signed step vs 8 px-shifted null, calibrated on the 26 real clean pairs | G2.seam | ~0.5 day, numpy | DONE 2026-10-04 (LEDGER 264): golden 12/12, 0/26 real FP at 6.0 levels; G2.seam_step row; live wiring = R3b |
| 4 | E-LAMA-1: anime-lama (already in the operator's IOPaint) vs current LaMa, golden cleaning A/B on slugs where `_01` was approved; operator blind 2AFC; outside identity must stay exact | clean engine (ADR-009 swap, not ladder) | ~0.5 day + operator review; ~1 GB weights, GPU minutes | MEDIUM - domain-matched fill for the busy-art regions that drive the manual IOPaint lane |
| 5 | E-PEFT-1: stock-DINOv2 AnomalyDINO zero-shot residue map; ExPLoRA-MAE ViT-B only if the miss is diagnosed as domain gap | G2.text_residue (second signal) | ~0.5 day; +2-6 GPU-h EST if step 2 runs | LOW - expected to miss +4 levels; buys a measured close of the ExPLoRA question |

Not shortlisted: MoE / all-in-one restorers (photo-trained, no LW labels to
route on); MIM pretraining recipes (no gate impact); diffusion SR (fidelity
risk; PiSA-SR held as a low-res rescue idea only); a DAT2 corpus fine-tune
(feasible, ~5-15 GPU-h EST, but blocked on assembling native-HR targets -
revisit after rank 1-3 make the gates trustworthy enough to judge it).

Order matters: ranks 1-3 repair the instrument; a model swap (rank 4, or any
ADR-004 challenger) is only judgeable once the board's broken rows are PROVEN.
