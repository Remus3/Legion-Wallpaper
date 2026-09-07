# WAKEUP_NOTES - LW hand-off ledger

---

## 2026-09-06 (night) - the `claude` contributor purged, and the hand-off moved in-repo

- **GitHub listed `claude` as a second Contributor; the cause was NOT
  authorship.** All 483 commits were already authored AND committed by
  Moonbeam. It was 84 `Co-Authored-By: Claude` trailers on commits dated
  2026-07-03 to 2026-07-26 - every one predating the commit-msg strip hook.
- **Fixed by rewriting all 483 commits** (`git filter-repo --message-callback`)
  and force-pushing. HEAD tree byte-identical either side (`1c558e45`), so no
  file content moved - only shas. `aa99af3` -> `16bc443`. The contributors API
  now returns `Remus3` alone, 483. Suite 2521 passed / 18 skipped, CI green.
- **Every sha in the repo changed.** All 255 shas cited in tracked Markdown are
  mapped in `docs/_archive/2026-09-06-sha-rewrite-map.md`, chained to the
  2026-08-01 map - walk the older map first, then this one. LEDGER 154.
- **Do NOT redo:** no further trailer sweep. `.githooks/commit-msg` already
  strips it, re-verified active this session via `install_git_hooks.py --check`.
- **RC's 22:05 inbox note was actioned in-session, not deferred.**
  `LW-NEXT-SESSION.txt` moved off the Desktop into the REPO ROOT and is tracked;
  the Desktop keeps a `.lnk` to it. LW did NOT have RC's write/consume bug -
  there is no `--consume` mode here, so there was nothing to split. LEDGER 155.
- **Answered RC's watcher question honestly: LW has NO inbox watcher**, measured
  by grep, not assumed. Reply is in RC's inbox. The proposal (SessionStart hook
  surfaces unread items against a watermark file, no daemon) is opened as
  ROADMAP `sync-inbox-visible-at-session-start` - build it next, do not invent a
  fourth background daemon for it.
- **Then the cross-repo round took over the session, all of it actioned rather
  than deferred.** RC corrected LW's inbox-watcher design before any code was
  written (seen-FILENAME set, never an mtime watermark - a watermark loses a
  note on a `/clear` right after session start, and loses it SILENTLY on
  mtime-preserving delivery and clock skew). ROADMAP row carries the corrected
  shape.
- **Mutex names ROTATED and the disclosure prose SCRUBBED (LEDGER 156,
  ADR-012, `1de8d4e`) - operator-approved, not taken unilaterally.** RSC was
  holding a public flip believing it would be first to publish the shared loop
  files; LW verified live that it already publishes them (raw URL HTTP 200) and
  unblocked RSC. Done with every loop STOPPED because this re-pin moves the name
  VALUES. The rotation exposed a REAL defect: `p5_probe.py` matched the mutex by
  the substring "GEMINI", so opaque names made condition 4 report GREEN on no
  evidence - now bound to the value, with two tests pinning it.
- **The `hold()` release-path leak is FIXED, authored by LW (LEDGER 157,
  `374c79e`).** LW was the unanswered party and is the other acquirer.
  CONFIRMED on LW's tree: `loop_controller.py:916` runs every cycle under one
  pid, so a leaked lane was unreapable for the whole run. MEASURED what RC would
  not ship on: unlink fails under an open reader (WinError 32), in-place rewrite
  SUCCEEDS, `tmp + os.replace` FAILS (WinError 5). So release() retries then
  NEUTRALISES (pid 0, ts 0) and `hold()` stops logging a release that did not
  happen.
- **Both rounds converged the same night - VERIFIED by hashing all three trees,
  not by their say-so.** `winmutex.py` `0b112a4f` is in LW, RC and RSC, so the
  rotation window is CLOSED and the loop-start block is LIFTED. `slots.py`
  `629c3d51` is in LW and RC; RSC is still on `1c4f8af4`, which is non-blocking
  because RSC vendors that file and never acquires. drift_guard reads 0
  breaches. Whether RC and RSC updated their own pinned digest CONSTANTS is
  theirs to confirm - LW verified the file bytes.
- **Next:** the 123f hand-clean (veil stage) in Photoshop - still untouched,
  unchanged from the last three hand-offs.

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
