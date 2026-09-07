# DWPose CPU vs CUDA parity - the 5/6 localizer number re-measured

_2026-09-06. Closes the ROADMAP item `dwpose-cuda-parity` (opened LEDGER 148)._

## Question

LEDGER 19 adopted DWPose as the M1 weapon-pass localizer on **5/6
wrist-on-weapon** over the six `recall_gate` samples, against OpenPose's 1/6.
That was measured on the ONNX Runtime **CPU** execution provider. DWPose moved
onto the **CUDA** provider on 2026-09-06 (LEDGER 148, `0cce31a`). CUDA and CPU
kernels are not bit-identical, so the number had to be re-taken rather than
carried forward. Exactly one frame had been spot-checked, which is parity
evidence of one image.

The localizer CHOICE is not re-opened here (settled, LEDGER 19). Only the
provider changed.

## Method

`tools/lw_gen_localizer_eval.py dwpose` over the same six samples, from
`.venv-gen`, twice: `LW_ORT_PROVIDER=cpu` forces the old path with no
reinstall, and the default binds CUDA. A third arm compares against the
artifact of the original 2026-07-11 run, which still sits in
`images/_gen_scratch/localizer_eval/dwpose/summary.json`.

Providers were confirmed **bound**, not merely requested - ORT drops to CPU
silently when its CUDA EP fails to load while still advertising CUDA as
available, so `get_available_providers()` proves nothing:

    CPU  arm: det/pose get_providers() = ['CPUExecutionProvider']
    CUDA arm: det/pose get_providers() = ['CUDAExecutionProvider', 'CPUExecutionProvider']

Warm timing over the six samples (first image discarded; a 6-image run pays
~0.7s of one-off CUDA warmup, which is why a short cold run reads ~0.16 s):

    CPU   0.299 s/image      CUDA  0.038 s/image      (cv2 decode 0.013 of both)

This reproduces LEDGER 148's 0.29 -> 0.03.

## Result 1: the CPU arm is an exact control

Today's CPU run reproduces the 2026-07-11 run to **0.0000 px on every joint of
every frame**. Nothing in the harness, the vendored onnx helpers or the models
has drifted in eight weeks, so any CPU-vs-CUDA difference below is the provider
and nothing else.

## Result 2: positions agree, confidence scores do not

With the confidence gate off (`min_conf=0.0`), worst joint displacement per
frame, in pixels on a 1344x768 frame:

    seed22 1.019 | seed33 1.489 | seed800 1.284 | cand_01 0.039 | cand_02 2.800 | seed42 0.029

Worst case 2.8 px = 0.21 percent of frame width. CUDA is deterministic
run-to-run: two consecutive CUDA runs agree to 0.0000 px with byte-identical
scores.

The scores move by about 0.015, always slightly DOWN on CUDA:

    frame     RWrist cpu -> cuda    LWrist cpu -> cuda
    seed22      0.638 -> 0.636        0.304 -> 0.286   <- crosses the floor
    seed33      0.728 -> 0.728        0.346 -> 0.350
    seed800     0.368 -> 0.360        0.644 -> 0.626
    cand_01     0.507 -> 0.503        0.927 -> 0.926
    cand_02     0.305 -> 0.293        0.402 -> 0.406   <- crosses the floor
    seed42      0.877 -> 0.878        0.550 -> 0.553

## Result 3: two wrists fall through the `min_conf=0.3` floor

Two of the twelve wrists sit within 0.005 of the floor, and the provider shift
is three times that gap. So the difference is NOT a moved keypoint, it is a
gate decision:

    seed22  LWrist  0.304 -> 0.286  ROI L: ok -> missing_wrist
    cand_02 RWrist  0.305 -> 0.293  ROI R: ok -> missing_wrist

Wrist availability drops from **12/12 on CPU to 10/12 on CUDA**. Nothing gains
a wrist.

## Verdict

**The 5/6 headline is CONFIRMED under CUDA at the frame level, with one
asterisk that the headline hides.**

- `cand_02` was already the miss under CPU and stays a miss. Its lost RWrist
  changes no verdict.
- `seed22` was a hit and still has a wrist on a weapon: the RIGHT ROI survives
  on the second crossbow at frame-left (checked at 1:1 on both overlays). What
  it loses is the LEFT ROI, which covered the **primary** crossbow, the larger
  and more obvious weapon in the frame.

So: **5/6 frames, 10/12 wrists.** State the wrist number alongside the frame
number from here on. If the operator's original `seed22` hit was scored on the
left wrist, the honest per-frame number under CUDA is 4/6 - still above the
>= 4/6 adopt bar, and the adopt decision does not move either way.

## Root cause, and what was deliberately NOT changed

`min_conf=0.3` sits exactly where two of twelve wrists live. A confidence floor
inside the provider-noise band makes a keypoint's PRESENCE provider-dependent,
which is a property of the threshold, not of DWPose. Lowering it to 0.25 would
restore both wrists and make the two providers agree.

That is a tuning decision with a real cost on the other side (a low-confidence
wrist places a weapon ROI on the wrong pixels), the acceptance criterion here
was a measurement, and the M1 weapon pass is operator-in-the-loop. So the floor
was left at 0.3 and the evidence is written down instead. Two wrists at 0.304
and 0.305 are the whole exposure.

## What shipped

`run()` now stamps `summary.json` with a `_run` block carrying the providers
that were actually BOUND for that run, the backend, and a timestamp. LEDGER
19's number had to be re-measured from scratch precisely because its artifact
did not record the provider. Read off the live session rather than the
requested list, and never building a session, so a backend with no ORT session
stamps null and nothing allocates outside `gpu_lock()`. Three tests, injected
sessions, so the policy is asserted the same on a GPU-less CI runner.

## Do not redo

- Do not re-litigate the localizer choice (LEDGER 19: DWPose over OpenPose and
  SDPose; SDPose hard-imports mmpose and pins mmcv 2.2.0).
- Do not re-measure this on more frames expecting movement: the CPU arm is
  bit-exact against July and CUDA is deterministic run-to-run. The only
  provider-sensitive frames are those with a wrist within ~0.02 of `min_conf`.
- Artifacts, both stamped, beside the July CPU run:
  `images/_gen_scratch/localizer_eval/dwpose_cpu_2026-09-06/` and
  `.../dwpose_cuda_2026-09-06/` (gitignored, on-disk only).
