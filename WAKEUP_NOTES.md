# WAKEUP_NOTES - LW hand-off ledger

---

## NEXT SESSION - the parked pipeline queue

**The responder lane AND the false-RED repair are both DONE and closed.** Do not
re-file the positions, do not re-measure the false-RED count (it is 0; re-run
`python tools/lw_false_red_probe.py` only after touching an external-binary call
site, and only on an otherwise IDLE box - a contended run reported 2 phantom
failures and cost a re-run).

**The work: the parked pipeline queue**, kept verbatim in
`docs/NEXT_SESSION_PARKED_2026-09-10.md` - 108 `needauth`, 7
`aspect_crop_heavy`, 3 `lap_ratio`, plus the scoped_revert art-damage measure
and the `dists` gating decision. RE-PROBE its counts before acting;
`0.Originals` has moved twice already.

**Still open and NOT to be guessed at:** the one unreproduced slot
over-admission (peak 8 at width 7, 50 clean re-runs, cause UNKNOWN, ROADMAP has
it). `ops/loop/slots.py` is byte-identical by contract with RC.

**Still waiting on the operator:** registering `LW-InboxResponder`. The printed
command was BROKEN on the first attempt (cmd escaping run in PowerShell) and is
fixed - `python tools/lw_inbox_responder.py --print-register-command` now emits
a PowerShell form and a cmd form, and the PowerShell one is parse-checked by an
arm. Registering is D5; it stays the operator's act.

**Acceptance, unchanged:** `python -m pytest tests/ -q` green, ruff clean,
`python tools/drift_guard.py` exit 0, `python tools/done_gate.py bind` exit 0,
then push the bound sha. The suite still runs one more item than it collects -
PRE-EXISTING.

---

## 2026-09-10 - the 43 false-RED sites repaired, 43 -> 0 (LEDGER 182)

- **Repaired the same day they were measured.** `tests/gitdep.py` answers one
  factual question and each site decides what it means there: module-level
  `pytestmark` where all 21 arms build a repository, a fixture-level skip where
  only 9 of 35 do, a per-arm decorator for the remaining 13. NOT a sweep, NOT a
  matcher - widening one matcher over 43 sites relocates a conflation.
- **Graded behaviourally, both directions.**
  `tests/test_git_absence_is_a_skip.py` runs a representative node per repaired
  file with git stripped AND with git present: SKIP then RUN. Reading skip
  conditions is the blindness RC reported against its own guard.
- **Without git: 0 failed / 0 errors / 2794 passed / 101 skipped** (was 15 / 28
  / 2783 / 57). With git: exit 0, 2877 passed / 18 skipped. 5 mutants, 5 killed.
- **The same measurement error, twice.** The first post-repair probe said 2
  remaining - both timing arms, neither git-related - because a mutation harness
  was hammering the box. Uncontended: 0.
- **The registration line was broken in the operator's hands** - cmd's `\"`
  escape run in PowerShell. Fixed by removing the quoting question entirely
  (`Register-ScheduledTask` takes execute and arguments separately), with an arm
  that PARSES the emitted PowerShell and never runs it.

---

## 2026-09-10 - the responder lane: positions filed, responder built and NOT armed, 43 false-RED sites measured (LEDGER 181)

- **Standby lifted, positions filed.** One note, byte-identical by construction
  (sha256 `f627670e967f1603...`, 13627 bytes), into all four sibling inboxes
  plus LW's own record. RSC located at `C:\Resin Compute` - it is NOT under
  `C:\ReSin*`. No code written into any sibling tree.
- **The conftest claim, refuted on a SECOND tree.** RSC's "already latent in the
  conftest all five of us share" was retracted after RC refuted it; LW measured
  its own rather than taking either side. No root `conftest.py` exists;
  `tests/conftest.py` is 56 lines, has ZERO external-binary calls and encodes no
  skip/fail policy - it is the YOLO_AUTOINSTALL + PIL guard and nothing else.
  Q3 stands anyway: LW's evidence is `tools/lw_model_pins.py`, production code.
- **Responder built to the REPAIRED list, not the proposed one.** CS and RSC had
  both refuted parts of RC's A1-A4 before LW wrote a line, so A3 needs two
  INDEPENDENT corroborating carriers, A4 never moves a pin alone, A2 is bounded
  and reports counts not a verdict, and A5 exists at all. Gate is three-valued:
  AUTO / DRAFT / UNAVAILABLE, `checked` separating REFUSED from COULD-NOT-CHECK.
- **Caught by running it:** the first dry run against the real inbox reported
  139 new notes and would have spawned 139 headless sessions. Cold start now
  baselines and spawns nothing; `MAX_SPAWNS_PER_CYCLE = 3` bounds a burst.
- **18 mutants, 18 killed, byte-exact restore.** Two honest misses recorded
  rather than quietly fixed: the A3-independence mutant SURVIVED the first pass
  (the existing arm was already refused by the count, so the rule read as tested
  when it was not), and `record_seen`'s prune-to-live survived until a
  withdrawn-and-refiled arm was added.
- **43 false-RED sites**, measured with RC's own reproduction. Mirror direction
  measured too: skips 18 -> 57, so 39 arms already degrade correctly.
- **One RED nobody can reproduce, recorded not buried.** A full-suite run
  inside `done_gate bind` failed the slots ceiling arm with peak 8 at width 7.
  25 isolated runs and 25 under 12-way CPU load were clean, as were three other
  full-suite runs. Cause UNKNOWN. The arm's message was wrong for the
  over-admission case and is now split in two. `ops/loop/slots.py` is
  byte-identical by contract with RC - see ROADMAP.
- Suite 2870 passed / 18 skipped, ruff clean, drift_guard 0 breaches.

---

## 2026-09-08 - PVR closed, two guards shipped, and two contamination probes (LEDGER 177-180)

- **PVR (177):** premise CORRECTED - the enabling `PUT` was a verified no-op
  because the operator had already flipped it by hand. Verified two ways: REST
  reads `{"enabled":true}` AND an unauthenticated `curl -L` of the advisories
  form returns 200, which is the half that proves an outside reporter can
  actually land on it.
- **Model pins (178):** `lw_upscale.py:449` RECORDED `model_sha256` and nothing
  asserted it. Now `config/model_pins.json` + `tools/lw_model_pins.py`, asserted
  at the top of `upscale_spandrel()` ABOVE the torch import so a drifted weight
  refuses before taking the GPU mutex. Four states - ABSENT never reads as
  verified. The run-scoped hatch deliberately does NOT silence the session gate.
- **Ignored-tracked (178):** proven live, `git add -A` on a new file in
  `docs/_archive/` exited 0 and added nothing. Root cause was an unanchored
  `_archive/`; fixed rather than exempted, and anchoring un-hid 5 invisible
  files which now stay out explicitly because the repo is public.
- **MS-SSIM (179):** I called the arm decoration on 719 audits of silence and
  r=-0.872 redundancy. Measuring inverted it - it is the ONLY arm catching a
  geometric error (16px shift: msssim 0.8598 FAIL, lpips 0.1206, dists 0.0704).
  Behaviour pinned, floor untouched. Found `dists` has no rule at all.
- **scoped_revert (180):** the cited "held is 0 in all 28" IS contaminated but
  was never load-bearing; `still_reads` 13 -> 2 replicates across two conditions
  off the stopping rule. The real hole is that both cited measures count
  residue, where scoped cannot lose by construction, and 95 percent of the
  changed area has no art-damage measure at all.
- Suite 2813 passed / 18 skipped, ruff clean, drift_guard 0 breaches.

---

## 2026-09-08 - split-value blindness probed; the leak was found first (LEDGER 174)

- **Premise corrected before any code.** The hand-off named two guards. Only
  `tests/test_no_account_paths.py` exists - there is NO operator-email guard in
  `tests/`, `tools/` or `.githooks/`, and `drift_guard` / `done_gate` /
  `precommit_gate` contain no email check. LEDGER 172 left one backstop,
  `git config user.email`, which is the commit IDENTITY field, not file content.
- **The leak, found by grepping instead of assuming:** the operator's personal
  address was tracked CONTIGUOUSLY in 5 places across 3 files - WAKEUP_NOTES.md,
  LEDGER item 172, and the 2026-09-07 sha-rewrite map. All three were written to
  RECORD the purge. Lanternlight's finding in its plainest form, and it did not
  even need a split to survive. Scrubbed; `git grep` returns nothing.
- **The probe on the guard that does exist:** a break AT the separator ends the
  contiguous match, so `C:\Users\` + newline + account, the same break made by a
  markdown code span, and the path written backwards are all MISSED. Now a
  standing arm in that file, not a claim.
- **Shipped:** `tools/split_scan.py` + `tests/test_no_split_identity.py`. Values
  pinned by sha256 and never spelled out; scan runs over a normalised
  (`[a-z0-9]` only) view AND its reverse; only windows starting with the pinned
  first character get hashed, which keeps 6.6 MB at ~1.3s. Exemption is a
  property of the VALUE: the account name imports `_would_be_exempt` from the
  sibling, the address is exempt nowhere and an arm asserts it cannot become so.
- **Proof it binds AND clears:** the sweep fired on the live tree (10 hits / 9
  files / 444 scanned) before the fix; each scrubbed file's pre-edit HEAD blob
  reports its fragment and its worktree copy reports none. Suite 2750/18
  (baseline 2728/18), ruff clean.
- **Do NOT redo:** no history rewrite for this. The address re-entered AFTER the
  2026-09-07 rewrite, the ruling is fix-forward, and a force-push does not purge
  GitHub-side objects anyway. Do not pin the mail domain: it names millions of
  people, would fire on prose, and a guard that fires on prose gets deleted.
- **Also shipped (LEDGER 175):** `done_gate bind` reported `pytest -> 1` on the
  very commit above, and the suite was green on three full runs either side. The
  failing test's name went to my own `tail -6`, so two extra full-suite runs
  bought nothing. The one RED did NOT reproduce and its cause is recorded as
  UNKNOWN. The gate now captures each check, echoes 40 lines of a failure and
  keeps the full output in `ops/runtime/done_gate_failure.log`; a GREEN run
  deletes a stale one. Cost, named in the docstring: a passing check no longer
  streams live. **Do not pipe the gate through `tail`.**
- **Also shipped (LEDGER 176, `eacb64e`):** the GitHub community checklist is
  complete - `CODE_OF_CONDUCT.md`, `CONTRIBUTING.md`, `SECURITY.md`,
  `.github/ISSUE_TEMPLATE/` (defect + doc-error, blank issues off) and
  `.github/pull_request_template.md`, all written for what this repo IS rather
  than from a template. README gains the publication-guards row; topics now 20
  (added `agentic-ai`). **CLOSED 2026-09-08 (LEDGER 177):** private
  vulnerability reporting is ENABLED - the operator flipped it by hand, and a
  live re-probe reads `{"enabled":true}` with the anonymous advisory form at
  HTTP 200, so the SECURITY.md and issue-template links resolve.
- **Answered for CS (their 2026-09-08 1859 correction note):** LW's SessionStart
  wiring IS in the TRACKED `.claude/settings.json`, but `moon_sync_inbox/` is
  gitignored (.gitignore:180), so a clone gets the watcher and no channel. LW
  does NOT have their silent-failure half: measured in-process, an absent inbox
  reports `- moon_sync_inbox: absent at <path> - no cross-repo mail channel`
  with no anomaly and no non-zero exit. Separately, every LW hook command
  hard-codes the absolute project path, so a clone elsewhere runs none of them.

---

## 2026-09-08 - 0.Originals ingest, then first pass on the batch (LEDGER 173)

- **Intake:** 122 loose files in `0.Originals` -> **117 intaken**, 5 refused by
  the near-dup perceptual gate and LEFT in place (`--allow-near-dup` is an
  operator override; not taken). 117 INTAKE + 117 ANNOTATE log lines all `ok`,
  `lw_pipeline verify` ok on 713 images, verifier subagent PASS on all 7 claims.
- **Recovery:** Tier 0 (pHash vs 292 reference_pictures) found NOTHING for this
  batch - 0 accepts, 1 borderline 14/14 review, and a self-match control proved
  the hash path live, so it is a real null. Tier 1 decoded 9/9 DeviantArt
  tokens, 4 oEmbed-confirmed alive. The other 108 are QUEUED for Tier 2 in
  `ops/runtime/tier2_queue_2026-09-07.txt` - SauceNAO free tier is ~4/30s and
  ~100/day, so it is an overnight batch, NEVER a loop.
- **Shipped code (d327642):** `--crop-overrides` gained a second grammar, a
  one-key `{side: pixels}` offset. The sides grammar could only say three
  anchors per axis and the operator picked a frame between them. It also fixed
  a latent bug: `list(crop_sides)` on a dict yields its KEYS, so an offset
  would have been recorded in the manifest as `["top"]` with the offset lost.
  35 new tests, RED-first evidence captured. Suite 2728/18 (was 2693/18).
- **First pass:** 111 processed, **108 submitted** to `_firstneedauth`, all
  exactly 2560x1440, upscaler V3detail DAT2 via spandrel at 4x (ADR-004).
- **Do NOT redo:** the two `dmrl7u8-*` slugs are NOT duplicates. They share one
  deviation (1376595440) but are phash 26 / dhash 27 apart - a multi-image
  upload. Both crops are operator-approved and already shipped.
- **Open, needs the operator:** 108 await approve/reject (never self-approved);
  7 slugs HELD `aspect_crop_heavy` need a framing call (3 pintrest lose 68-71%
  of area to reach 16:9); 3 slugs failed G1 on `lap_ratio` 0.91-0.93 vs floor
  1.0 - soft SOURCES, not the double-resample bug, and they kept their working.
