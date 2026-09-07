# WAKEUP_NOTES - LW hand-off ledger

---

## 2026-09-06 (late) - the 5/6 localizer number, re-measured on CUDA

Commit `5f6f119` (+ this docs sync). Suite 2519 passed / 18 skipped, ruff
clean, drift_guard 0 breaches. Ledger 151. ROADMAP's top open item is closed;
`golden-overtarget-refreeze` moves to the top and is still the operator's.

**The 5/6 holds, but say it as 5/6 frames / 10/12 WRISTS.** Positions are not
the issue: CPU and CUDA agree within 2.8 px on a 1344x768 frame, CUDA is
deterministic run-to-run, and today's CPU arm reproduces the 2026-07-11 run to
0.0000 px, so that arm is an exact control. What moves is the CONFIDENCE score
(about -0.015 on CUDA) and two of twelve wrists sit at 0.304 and 0.305 against
`min_conf=0.3`. `seed22` left and `cand_02` right fall through; their ROIs go
`missing_wrist`. `seed22` still has its RIGHT wrist on a weapon so the frame
verdict holds, but the ROI it loses is the one over the PRIMARY crossbow. The
floor is left at 0.3 on purpose - 0.25 would restore both, and that is a tuning
call the measurement was not asked to make.

**The transferable bit: a number is only as portable as its provenance.** LEDGER
19's 5/6 had to be re-measured from scratch, at real cost, only because
`summary.json` never recorded which execution provider produced it. `run()` now
stamps a `_run` block with the providers actually BOUND - read off the live
session, because ORT drops to CPU silently while still advertising CUDA in
`get_available_providers()`.

**Golden set RE-FROZEN under USM 35 (operator blessing granted mid-session).**
All 12 regenerated through the live pipeline, `pv 6d43a6d4 -> ed249af6`, regress
PASS 12/12 with `pv_changed=False`. The hand pin to USM 70 is retired - the
frozen set finally validates the recipe that ships. Every fidelity metric
improved on every case (msssim +0.0008, lpips -0.0083, halo_pct -0.0229 mean)
and lap_ratio fell -0.4220, the 2026-08-02 census reproduced on a different
sample. `1341679-banding` reads lap_ratio 0.8416 now - below the G1 floor,
correctly ungated by ADR-006 for `downscale-only`, NOT a regression.
`lw_golden candidates` + `data/golden/cases.json` shipped so the next re-freeze
is three commands rather than archaeology.

**Cross-repo: RSC's `slots.hold()` leak is real here too, and LW took the one
measurement RC was blocked on.** A lockfile leaked by a lost unlink race keeps a
LIVE pid, so both arms of `is_stale` say "not stale" and `reap()` skips it - the
valve is disarmed by the case that trips it, and `loop_controller.py:952` holds
a slot per cycle under one pid. RC proposed neutralizing the payload but would
not ship without knowing whether a write is permitted against an open reader
handle. Measured on this disk: `unlink` fails WinError 32, `write_text`
SUCCEEDS, `tmp + os.replace` fails WinError 5. So the fix is viable and must be
a NON-atomic in-place write, which collides with both repos' atomic-writes rule
and will be tidied back into brokenness unless the comment says so. Ack filed in
RSC's inbox. `slots.py` NOT touched - joint round, top ROADMAP item.

**docs-guards badge: NO for LW, structurally.** RC's ci.yml ignores every `.md`
so a docs-only commit fires nothing there; LW's carries no filter, so a
docs-only push already runs the whole suite plus the drift gate. Recorded in the
ci.yml header + CLAUDE.md Settled, with the trigger that would flip it. The
header's "~28s suite" figure was stale and is now 2521/18.

**QA of the previous hand-off, one correction.** "Settling the USM 70 -> 35
question" reads as if USM were open. It is not: `USM_DEFAULT = (1.2, 35, 3)` is
SETTLED (2026-08-02) and CLAUDE.md says so. The real entanglement is narrower
and now written into the ROADMAP item: a 4096x2305 source is not exactly
2560x1440, so `_usm_applies` is True and the over-target downscale-only branch
DOES apply an unsharp mask, which makes the flagged `lap_ratio` directly
USM-sensitive; the regress had to pin USM to 70 by hand, so the frozen set is
currently validating a recipe that has not shipped since 2026-08-02. Re-freezing
under the live default retires the pin. Still a blessing call, still untouched.

---

## 2026-09-06 (evening) - driver bump, DWPose onto the GPU, and two silent guards

Commits `1ef672e`, `81de837`, `a019586`, `0cce31a`, `6f07bd5`, `5715cf0`,
`1998e2b`, `ce8b4ad`, `3a8a296`, `024d0a8`. All pushed, CI green on
`024d0a8`. Suite 2516 passed, 18 skipped, ruff clean, drift_guard 0
breaches. Ledger 146-150.

CI went RED once on `3a8a296` and the local suite did not catch it: the new
DLL-path test asserted Windows-only behaviour, and `os.pathsep` is `:` on the
runner. Fixed in `024d0a8` by INJECTING the platform decision rather than
skipping on POSIX - a skip there would have been the same green-by-skip hole
closed one commit earlier.

**The `.git` directory was destroyed during the folder move and rebuilt.** The
tree arrived complete with no `.git`; `.git` carries the Windows HIDDEN
attribute and the other dot-entries do not, so a copy that skipped hidden items
took everything except the repository. Recovered from origin with `init` +
`fetch` + `reset --mixed`: zero differences against `origin/main`, nothing
tracked lost. Reflog and stashes are gone; `core.hooksPath` had to be
reinstalled because it lived in the destroyed config. See
memory `reference-git-dir-is-hidden`.

**DWPose now runs on the GPU, and that has a cost worth remembering.** Three
things had to be true, and only the first was the one reported: the CPU-only
`onnxruntime` wheel, a hardcoded `["CPUExecutionProvider"]` in
`lw_gen_localizer_eval.py`, and the DLL search path. On the last one,
`os.add_dll_directory` does NOT work and neither does ctypes-preloading cuDNN -
PATH does. ORT fails to load its CUDA provider and falls back to CPU SILENTLY
while still listing CUDA as available, so "CUDAExecutionProvider in
get_available_providers()" proves nothing. Install the CUDA-12 build with
`--no-deps` from the ORT index; the PyPI default is CUDA 13 and will not load
beside torch cu128. 0.29s -> 0.03s per image. `LW_ORT_PROVIDER=cpu` forces the
old path.

The cost: DWPose was exempt from the machine-wide GPU mutex *because* it ran on
CPU. It now takes `GPU_MUTEX` and serializes against the upscaler and SDXL
across both repos. `test_gpu_mutex_wiring` caught this immediately.

**Golden regress, 12 cases, answering the driver question (610.62 -> 616.56):
no measurable drift.** 11 of 12 pass within epsilon. The single flag is on the
ONLY case that never touches the GPU - its 4096x2305 source takes the G0
over-target downscale-only branch, and its baseline predates that branch by 64
minutes (froze `37741ea`, gate landed `6cffc3d`). Stale baseline, not a
regression. **Re-freezing it is a blessing call and is left to the operator.**

The unit tests in `tests/test_lw_golden.py` do NOT exercise the GPU - they test
the freeze/regress tool against tmp_path. Running them before and after a
driver change proves nothing; `data/golden/golden_set.json` is the real
baseline. `lw_golden` also hardcoded the USM recipe into `pipeline_version`
while `USM_DEFAULT` moved on 2026-08-02, so the hash reported "unchanged"
through a real pipeline change. Now pinned to the definition site, and `pv`
correctly reads `ed249af6` against the manifest's `6d43a6d4`.

**Two guards were silently blind, one on each side.** LW's rename disarmed RC's
cross-repo guards for ~3 hours (RC held the old `LW_ROOT`; their suite went
28/0 to 25/3 and stayed green). LW had the identical structure aimed at
`C:\Riot Commander`. `drift_guard.resolve_sibling_root()` now returns
present/renamed/absent - a rename is a breach, genuine absence still skips. The
transferable rule: a guard whose target can move must tell moved from missing,
and the renaming party sweeps the sibling's constants in the rename commit.

Governor round is complete across all three trees, verified from this disk:
`slots.py` `1c4f8af4...`, `winmutex.py` `f1b4b011...`, byte-equal in LW, RC and
RSC. RSC is not a full participant yet - no `SHARED_SHA256`, no
`max_concurrent_lanes`, nothing calling `slots.hold()` - so the bucket is 3 wide
with two real acquirers. Do not lower it to 2.

**Open, deliberately not done:** LEDGER 19's 5/6 wrist-on-weapon was measured on
the CPU provider. One frame gave identical keypoints on both - parity evidence
of exactly one image. Worth a proper pass over the recall_gate samples before
trusting any DWPose number measured before today.

---

## 2026-09-06 - root renamed to "C:\Legion Wallpaper", RM replaced by RSC

Commits 1ef672e (inbox) and 81de837 (rename), both pushed. Suite green: ruff
clean, 2501 passed, 19 skipped.

**Two spellings, both deliberate - do not "fix" either.** The local root is
`C:\Legion Wallpaper` WITH A SPACE. The GitHub repo is `Remus3/Legion-Wallpaper`
with a HYPHEN, because a repo name cannot hold a space. The agent project slug
`C--Legion-Wallpaper` is unchanged, since the slug hyphenates the space anyway.
Rule of thumb: a filesystem path is anchored on `C:`; a bare `Legion-Wallpaper`
token is the repo name. Any NEW hardcoded path needs QUOTING - an unquoted
`-File C:\Legion Wallpaper\tools\x.ps1` is read as `-File C:\Legion` plus a
stray positional, and fails silently.

**drift_guard WILL report a slots.py divergence between LW and RC. That is
correct and expected - do NOT revert it.** Red Moon is archived read-only and
its working copy deleted; Resin Compute took the vacated third slot in the
concurrency governor. LW authored the new bytes (docstring only, line 5,
`MAX_CONCURRENT_SLOTS` still 3) and re-pinned from its own disk:

    1c4f8af43ff349709c11bf3fe622e922b24cb720771c49a522b13a4d5e58c492
    previous 5297f2d041030398a9ba240aad527b2b01a86d6e7f57a196719af8f0a91cb0a6

RC copies those bytes verbatim next; RSC lands its vendored copy LAST, being
the only participant with no pin to break. The flip cannot be atomic. Replies
explaining the sequencing are in RC's and RSC's `moon_sync_inbox`.

Also landed: `RSC: 8790-8809` recorded in `tools/lw_ports.py` FORBIDDEN (the
seventh block). LW binds nothing in that band - checked against source, the
registry and all three task definitions. `RM: 8770-8789` stays declared even
though Red Moon is gone, because Amberstone's `core/ports.py` still declares
`RM_BLOCK = range(8770, 8790)`.

If the folder move has not run yet: close Claude Code and run
`C:\finish-legion-rename.cmd`. It is idempotent and also repairs the three
agreeing `~/.claude.json` trust spellings, the three `LW-*` scheduled tasks
(quoting `-File` for the space), the agent memory directory, and checks that
all four venvs still resolve.

> Newest-first. Keep only the last 2-3 sessions here at FULL fidelity; archive
> older sessions verbatim to `docs/history_notes.md` (append a pointer line to
> this banner when you prune). Per-item completion records live in
> `docs/LEDGER.md`; open work lives in `ROADMAP.md` + `BACKLOG.md`.
> Archived to `docs/history_notes.md`: the two 2026-07-03 sessions (genesis +
> product-defined, pruned 2026-07-04), 2026-07-04 QA Session 1 (pruned
> 2026-07-05), 2026-07-04 QA Session 2 (pruned 2026-07-07), and the 2026-07-07
> first-pass-queue session + the lw-gen generator-sidecar/deep-research session (both pruned 2026-07-11), and the 2026-07-11 QA-floor calibration + recipe-v2 session (pruned 2026-07-11), and the 2026-07-11 GOLDEN DEFINITION session (pruned 2026-07-12), and the 2026-07-11 M0-foundations + M1-slices-1-2 session (pruned 2026-07-12), and the 2026-07-11 localizer-decision session (pruned 2026-07-12), and the 2026-07-12 M1-weapon-CLIP-gate session (pruned 2026-07-16), and the 2026-07-16 W4-M3 weapon-parked session (pruned 2026-07-16), and the 2026-07-16 Stage-2 cleaning-pipeline session (pruned 2026-07-18), and the 2026-07-27 loop-cycle-11 alpha-audit session (pruned 2026-07-29), and the 2026-08-01 three-repo-N=3 / hook-rule-correction session (pruned 2026-08-01), and the 2026-08-01 (evening) Stage-2-drain / L1 / dashboard-spine session (pruned 2026-08-01), and the 2026-08-01 (night) dashboard-spec-completion session (pruned 2026-08-01), and the 2026-08-01 (earlier) P3/P4/P5 + wiki-swap session and the 2026-08-01 (late) MCP-list/P1 session (both pruned 2026-08-02), and the 2026-08-02 all-five-recommendations/USM-flip/watchdog session (pruned 2026-08-09), and the 2026-08-10/11 intake/retry-degrades session + the 2026-08-11 detector-precision/recall session + the 2026-08-11 (evening) centre-overlay-inpaint session (all three pruned 2026-08-12), and the 2026-08-12 faint-mark REMOVAL lane session (pruned 2026-08-12), and the 2026-08-12 (later) overlay-registration-SCALE session (pruned 2026-08-12), and the 2026-08-12 QA-lane precision-census session (pruned 2026-08-12), and the 2026-08-12 veil-ring session (pruned 2026-08-13), and the 2026-08-12 clean-retry-degrades/one-engine session + the 2026-08-12 bare-pytest-wrong-tree session (both pruned 2026-08-16), and the 2026-08-23 queue-run/revert-lever session (pruned 2026-08-29), and the 2026-08-29 chord-coverage session (pruned 2026-08-29) - keep the last 3.

---

## 2026-09-06 - the license question, answered by refusing its premise

One commit (`511f1d8`) plus a docs sync, all pushed. Suite **2501 passed / 18
skipped / 1 pre-existing GPU failure**, ruff clean, `drift_guard` 0 breaches,
CI green.

- **No license change shipped, and that IS the result. Do not re-open it -
  CLAUDE.md Settled + LEDGER 145 carry the full reasoning.** The operator asked
  MIT vs Apache-2 wanting to block "downloaded + altered + commercialized".
  Both are permissive and both allow exactly that, so the premise was void; the
  governing axis is permissive vs copyleft and neither candidate was on it.
  MIT, GPL-3.0, AGPL-3.0, MPL-2.0, BUSL-1.1, PolyForm NC and the whole CC
  family were each weighed and each lost to the incumbent Apache-2.0.
- **The GPL-3.0 probe was the sharp one and it still came back empty.**
  CC BY-SA 4.0 -> GPLv3 is a real one-way bridge, but LW has nothing to carry
  over it: `data/reference/wiki/` is `render/` + `splash/` IMAGE bytes
  (gitignored, zero tracked) and BY-SA covers wiki TEXT, while the art is Riot
  IP regardless; ComfyUI (GPL-3.0) is a headless SUBPROCESS, which is mere
  aggregation and already fine under Apache-2. Copyleft binds on distribution
  of a combined work only - never subprocess, private use, or optional deps.
- **Visibility is metadata, not license.** All four levers set and verified
  live: description, homepage -> `docs/adr`, 19 topics, and a 1280x640
  social-preview card (`docs/assets/social-preview.png`, self-authored with
  PIL, no corpus bytes). Social preview had to be uploaded by hand - GitHub has
  no REST endpoint for it - and it is CONFIRMED landed because the page serves
  `og:image` from the `repository-images` custom CDN, not the
  `opengraph.githubassets.com` fallback. One topic slot is free.
- **Do NOT redo:** the licensing exploration, the metadata levers, or the
  social preview. All shipped and verified this session.
- **Pre-existing, not mine:** `test_worker_spandrel_branch_produces_both_variants`
  OOMs on an IDLE GPU (11105/12227 MiB free, no compute process), reproduced
  twice. CI never sees it - no CUDA runner. Now tracked as ROADMAP
  `usm-halo-probe-cuda-oom`.
- **Next:** the 123f hand-clean (veil stage) in Photoshop - unchanged from the
  last hand-off, this session never touched it.
