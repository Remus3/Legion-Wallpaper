# Refutation cost - the per-event rows, 2026-09-12

The raw extraction behind `REFUTATION_COST_MEASUREMENT_2026-09-12.md`. Four
read-only passes hand-opened disjoint chunks of `docs/LEDGER.md` entries 145-191;
no pass saw another's rows. **Each pass's own summary is retained below and is
NOT authoritative** - every total in the report was recounted by machine from
these rows, and three of the four passes are known to have mis-stated at least
one field definition in their own summary. Tracked so that a fleet re-score
against pinned definitions does not require re-running the census.

Known definitional splits, carried here so a re-scorer does not repeat them:
`correct` was read as "was the refutation right" by chunks 1 and 2 and as "was
the defect corrected in-window" by chunks 3 and 4; `fix_of_a_fix` was read three
ways; `inherited` was read as asked (true-when-written, since decayed) and
undercounts the wrong-when-written shape.


---

# Refutation census - chunk 1 (LEDGER.md lines 26-387, entries 191 down to 183)

Read hand-open, whole chunk, no keyword grep. 21 events recorded, 2 of them UNCLEAR.

---

id: chunk1-01
entry: 191
claim: LEDGER 189's DONE-claim that BOTH headless lanes for LW were disarmed, i.e. that LW had exactly two unattended lanes and both now had a kill switch.
refuter: the same tree catching itself while auditing the disarm - a third lane (LW-WeeklyHygiene, registered 2026-08-02) spawns claude with Edit/Write and commits+pushes with no HALT check at all.
quote: "It was missed because the disarm request was read against the two lanes that ADVERTISE a kill switch in `docs/OPERATIONS.md`"
correct: YES
bucket: b
inherited: NO
fix_of_a_fix: NO
note: the refuted claim rested on OPERATIONS.md's kill-switch roster, but that doc was never FALSE - it listed the only two switches that existed - so this is an omission at birth, not a decayed record. Contract that prevents it: enumerate unattended lanes from the SCHEDULER, never from the doc that documents switches.

---

id: chunk1-02
entry: 190
claim: truth_gate.check_ci reports the real CI state of a given sha - the function whose whole job is to separate a genuine green from queued / not-evaluated.
refuter: the operator-facing wrap ritual itself (the agent using the tool live and cross-checking against `gh run list`); ci_watchdog would have polled a permanent queued forever.
quote: "`truth_gate.check_ci('ebbd0f9b852e')` answered `{\"status\": \"queued\", \"runs\": []}` while `gh run list` showed that exact sha completed and successful"
correct: YES
bucket: live-exercise
inherited: NO
fix_of_a_fix: NO
note: only reachable by handing a REAL abbreviated sha to REAL gh - every stubbed arm returns whatever the stub says, which is exactly why the fix asserts the ARGUMENT handed to gh rather than the returned status. Secondary bucket (a): the pre-existing fixture could not contain the defect.

---

id: chunk1-03
entry: 189
claim: the LW test suite is hermetic - its colour reflects the code, not the machine.
refuter: the full suite run immediately after the two HALT files were written (self-caught, but only because an unrelated operator action changed machine state).
quote: "the next full suite went RED at four arms in `tests/test_inbox_responder.py` - not a regression, but arms that fell through to the DEFAULT `--halt`"
correct: YES
bucket: a
inherited: NO
fix_of_a_fix: NO
note: a live-surface / machine-state guard is mechanical and needs no human. The arms were green when written only because the operator's kill switch did not yet exist.

---

id: chunk1-04
entry: 188
claim: LEDGER 186's finding that Lanternlight leaks its live mail-ack state from a test - 19,700 B inbox_seen.json + 10,464 B inbox_reported.json attributed to the SessionStart hook test.
refuter: Lanternlight's own re-measurement (sibling repo), hashing the records before and after the run.
quote: "LEDGER 186's retraction of the \"Lanternlight is CLEAN\" verdict is itself retracted here"
correct: YES
bucket: c
inherited: NO
fix_of_a_fix: NO
note: root cause is the INSTRUMENT'S QUESTION - the tracer answers "did bytes move" and cannot answer "did state change", so a snapshot-and-restore GUARD is indistinguishable from damage. No static gate and no code-reading adversary finds this; it needs a second instrument asking a different question. The taxonomy has no bucket for that (see notes at end).

---

id: chunk1-05
entry: 187
claim: LW's hand-off to Clockspeed described the fix as two autouse redirects, and shipping those two would close the item.
refuter: Clockspeed's own tree - the item was already open as CS-973 with a broader written acceptance.
quote: "its acceptance asked for MORE than the two redirects LW's hand-off described - a full-suite before/after count whose arm DISCOVERS the writer rather than encoding the two already known"
correct: YES
bucket: b
inherited: YES
fix_of_a_fix: NO
note: inherited YES because the hand-off note was accurate when sent and decayed the moment CS filed CS-973 FROM it with wider acceptance. Precondition check: before repairing a sibling, read the sibling's own open item for that defect.

---

id: chunk1-06
entry: 187
claim: LW's hand-off attribution of WHICH tests wrote the 23 *.copy.sav into Clockspeed's live work/saves/ (two known writers).
refuter: a traced run inside CS - three arms, not two, and the copy happens inside a MODULE-scoped fixture so a function-scoped redirect installs and tears down after the writes.
quote: "THE HAND-OFF'S ATTRIBUTION WAS RIGHT ON THE FILES AND INCOMPLETE ON THE ARMS."
correct: YES
bucket: a
inherited: NO
fix_of_a_fix: NO
note: the prevention shipped is mechanical - a session-scoped count guard plus discovery-based arms; the third mutant proves the session guard binds alone.

---

id: chunk1-07
entry: 187
claim: LW's first edit to Clockspeed's tracked file was correct - the phase 4 blocks were placed where they read best.
refuter: Clockspeed's own guard, test_docs_citations.py, which pins WRITER_WRITE_SURFACE at line 2089 for the still-open CS-446.
quote: "The first attempt put the phase 4 blocks in the section where they read best, moving `WRITER_WRITE_SURFACE` off line 2089 and reddening `test_docs_citations.py` twice"
correct: YES
bucket: a
inherited: NO
fix_of_a_fix: NO
note: caught by a gate in a foreign tree; the durable rule stated is a contract ("do not edit a sibling's tracked file mid-file without checking its line pins first"), so this row sits on the a/b seam. Also notable: the fix was moving the blocks, NOT re-cutting the digest, which that guard's own message names as the trap.

---

id: chunk1-08
entry: 186
claim: the write-tracer's published byte figures in the 1043 and 1130 notes were complete measurements.
refuter: promoting the hack to a tested artifact (self-caught while writing arms) - builtins-only patching misses pathlib.
quote: "`builtins.open is io.open` is TRUE but `pathlib` calls `io.open` by ATTRIBUTE LOOKUP, so patching only `builtins` missed every `Path.write_text`"
correct: YES
bucket: a
inherited: NO
fix_of_a_fix: YES
note: fix_of_a_fix because the corrected instrument's own next verdict (chunk1-09) was retracted at entry 188 on the SAME instrument's deeper limit - its question, not its coverage. A non-vacuity control (planting a specimen through each patched route) is exactly the mechanical gate that catches the coverage half.

---

id: chunk1-09
entry: 186
claim: the retraction of LEDGER 185's "Lanternlight is CLEAN" verdict - i.e. the new claim that LL leaks its live mail-ack state.
refuter: nobody at the time; LW itself, with the corrected instrument, believed the reading. Refuted a day later by LL at entry 188.
quote: "the \"Lanternlight is CLEAN\" verdict is RETRACTED - re-measured, LL writes 19,700 B `inbox_seen.json` + 10,464 B `inbox_reported.json`"
correct: NO
bucket: c
inherited: NO
fix_of_a_fix: YES
note: this row is the rare one where the REFUTATION was wrong. A correct instrument produced a false verdict because the measure (bytes) was a proxy for the question (state). "You believed the reading that fit" - the reading confirmed the pattern LW had just found in three other trees.

---

id: chunk1-10
entry: 186
claim: the working tracer's watched-root resolution - a run reporting zero findings means zero live writes.
refuter: the newly added self-check control, on its very first run.
quote: "all three routes reported false on a working tracer because Windows `mkdtemp` returns the 8.3 SHORT path while `_watched` resolves to the long form"
correct: YES
bucket: a
inherited: NO
fix_of_a_fix: NO
note: textbook non-vacuity gate - "Without it that run would have printed a clean zero and been believed."

---

id: chunk1-11
entry: 186
claim: the tracer's zero-finding output was evidence that a tree was clean.
refuter: Lanternlight (sibling), on methodology, unargued and adopted.
quote: "an instrument printing a zero with no self-check reports an absence of evidence dressed as evidence of absence"
correct: YES
bucket: c
inherited: NO
fix_of_a_fix: NO
note: an adversary with a lens on the instrument, not on the code. This critique is what produced chunk1-10.

---

id: chunk1-12
entry: 186
claim: the first control design - plant a positive specimen through each patched route and report control.proved.
refuter: Lanternlight's second point, same pass.
quote: "a positives-only control still passes a classifier mutated to promote everything"
correct: YES
bucket: a
inherited: NO
fix_of_a_fix: NO
note: adopted in the same pass as chunk1-11, so chunk1-11 is not marked fix_of_a_fix. Prevention is mechanical - a NEGATIVE specimen outside every watched root.

---

id: chunk1-13
entry: 186
claim: LEDGER 185's finding that Resin Compute's suite writes 17,492 B into the operator's live day log, and by implication that LW's note drove the repair.
refuter: a re-measurement plus timestamps - RSC had already self-fixed at 10:11, ahead of LW's 10:43 note.
quote: "RSC now CLEAN, self-fixed at `7786955` (\"the suite was writing the operator's day log\") at 10:11, AHEAD of LW's 10:43 note - credit theirs"
correct: UNCLEAR
bucket: b
inherited: NO
fix_of_a_fix: NO
note: UNCERTAIN whether this is an event at all. The ledger states plainly that "LW's finding was accurate when taken", so no measurement was wrong; what was corrected is an ATTRIBUTION/credit claim plus a since-decayed state claim. Recorded rather than dropped because it is a self-correction of something this tree published.

---

id: chunk1-14
entry: 185
claim: the cross-tree hermeticity measurement method - hash the live files, run the suite, diff - and the first three conclusions drawn from it.
refuter: a 300-second IDLE control with no suite running, which showed all four candidate files changing anyway (daemons and concurrent Claude sessions).
quote: "the obvious probe - hash the live files, run the suite, diff - is INVALID on this box"
correct: YES
bucket: c
inherited: NO
fix_of_a_fix: YES
note: two of the first three conclusions were withdrawn on that evidence. fix_of_a_fix YES - the replacement in-process pytest plugin was itself refuted at entry 186 (builtins-only, missing pathlib) and again at 188 (bytes not state). Since codified as the memory feedback-run-an-idle-control-before-attributing, which would make a future instance bucket b.

---

id: chunk1-15
entry: 185
claim: the RC byte figures LW published in its first outbound note.
refuter: LW itself, on noticing the producing run used -x and stopped early.
quote: "the first RC pass used `-x` and was a lower bound"
correct: YES
bucket: a
inherited: NO
fix_of_a_fix: YES
note: a pipeline that reports a truncated producer's numbers as a total - mechanically preventable. The corrected figures were AGAIN declared a lower bound at entry 186 for a second, unrelated reason (pathlib), hence fix_of_a_fix.

---

id: chunk1-16
entry: 185
claim: that LW's own suite was hermetic and that LEDGER 162's report-then-ack split was safe - arms patched _ROOT and were assumed redirected.
refuter: LW's own in-process write tracer (later probe).
quote: "`lw_facts._INBOX/_SEEN/_REPORTED` bind at IMPORT, so an arm patching `_ROOT` kept the live paths and `main()` wrote the real `ops/runtime/sync_inbox_reported.json`"
correct: YES
bucket: a
inherited: NO
fix_of_a_fix: NO
note: consequence was that a suite run marked live mail as SHOWN - LEDGER 162's defect re-entered through the suite. Fixed at the root with path accessors deriving from _ROOT at USE.

---

id: chunk1-17
entry: 185
claim: same hermeticity claim, second instance - lw_monitor did not touch live surfaces under test.
refuter: the same in-process tracer.
quote: "`lw_monitor.main()` hard-called `setup_logging(MONITOR_LOG)`, now `--monitor-log`"
correct: YES
bucket: a
inherited: NO
fix_of_a_fix: NO
note: recorded separately from chunk1-16 because it is a distinct module and a distinct fix, though found in the same probe. Generalisation stated in the entry: a module constant computed from a repo root AT IMPORT cannot be redirected by patching the root afterwards - one shape, every tree.

---

id: chunk1-18
entry: 184
claim: the newly shipped inbox-responder run log was done - 13 arms written RED-first and all 13 green.
refuter: the first full suite run after the feature landed, which appended fabricated history to the operator's LIVE file.
quote: "the first suite run after the log landed appended 13 records of INVENTED cold starts to the operator's live file (1411 bytes, measured, then removed as fabricated history)"
correct: YES
bucket: a
inherited: NO
fix_of_a_fix: YES
note: the fix was an autouse mtime guard on BOTH responder test files, mutation-proven and the file restored byte-exact. Marked fix_of_a_fix because entry 189 found four arms in the SAME file still reading machine state - "Same defect class as the run-log leak this very file already carries a fixture for", i.e. the guard did not generalise to the sibling live surface.

---

id: chunk1-19
entry: 184
claim: LEDGER 183's DONE-claim that LW-InboxResponder was armed and VERIFIED - liveness demonstrable.
refuter: an end-to-end audit of the lane on an operator question.
quote: "the task runs detached with `stdout` at DEVNULL, so a DRAFT refusal, a deferred remainder and a halted cycle all left the same trace as a responder that never fired"
correct: YES
bucket: b
inherited: NO
fix_of_a_fix: NO
note: three of four legs were already sound, so this is an INCOMPLETE prior claim rather than a wrong one. Same contract shape as chunk1-01: an unattended lane owes a kill switch AND a run record in the commit that arms it.

---

id: chunk1-20
entry: 183
claim: the responder as designed and left ready-to-register by LEDGER 181/182 was safe to arm.
refuter: the tree itself at the moment of arming, on operator direction.
quote: "Arming something that spawns unattended agents with no mid-flight stop is the gap"
correct: YES
bucket: b
inherited: NO
fix_of_a_fix: YES
note: fix_of_a_fix because the fix shipped here - the HALT check plus five arms - had its TEST half refuted at entry 189, where arms covering that very switch were found reading the operator's real kill switch. The runtime half of the fix held.

---

id: chunk1-21
entry: 183
claim: the implicit claim that classify()'s 60 arms constrain what the spawned headless session may do.
refuter: the same agent, stating it to the operator at the arming rather than burying it.
quote: "the allowlist is enforced as INSTRUCTIONS in the spawned session's prompt, not mechanically"
correct: UNCLEAR
bucket: c
inherited: NO
fix_of_a_fix: NO
note: UNCERTAIN whether this is a refutation or a disclosure. Nothing in the window shows a prior entry asserting mechanical enforcement; it is recorded because the entry frames it as something that would otherwise have been believed, and because it names the trial's actual risk surface.

---

## EXCLUSIONS

RECITALS (refutation happened outside this window, merely re-told) - 5:
 1. 183 - "the footgun LEDGER 181 caught in dry run made real and harmless" (caught outside the window).
 2. 183 - the empty-file ruling "lifted deliberately from `ci_watchdog.halted` including the rule it learned first" (learned outside the window).
 3. 191 - the same empty-file ruling retold a third time.
 4. 189 - "the same one as `feedback-hermetic-tests-machine-state`" (the CI incident behind that memory is outside the window).
 5. 185 - "LEDGER 162's defect" itself (the re-entry through the suite IS recorded, as chunk1-16; the original is not).

EXTERNAL-ORIGIN (sibling defects this tree never rested on) - 7:
 1. 188 - LL's restore used `Path.write_bytes`, non-atomic; filed there as OPS-82.
 2. 188 - LL filed LW's two walker probes as accumulating; measured, zero remain. LL's error about LW's tree, never adopted here.
 3. 187 - CS's `tests/test_edit_lint_check.py` writes its CS-841 bait under `work/`; filed not fixed.
 4. 185 - RC's live-surface guard that fires in a full-suite run but passes file-alone.
 5. 185 - RC's 181,285 B supervisor log plus 7 replaced live JSON state files.
 6. 185 - RSC's 17,492 B day-log leak (state claim; the credit correction IS recorded as chunk1-13).
 7. 185/186/187 - CS's 23 `*.copy.sav` (the DEFECT is CS's; LW's own hand-off errors about it are chunk1-05/06).

ORDINARY RED-FIRST TDD AND MUTATION PROOFS (a test written to fail first is not a refutation) - 8:
 1. 190 - two arms RED on the old code.
 2. 185 - 4 arms RED-first.
 3. 184 - 13 arms written and run before implementation, 13/13 failed then passed.
 4. 191 - deleting the check reddens 3 of 6, restored byte-exact.
 5. 188 - deleting the `io.open` patch reddens the new arm.
 6. 187 - three mutants, three killed.
 7. 186 - deleting the `io.open` patch flips control.proved; a second arm forces one route to break.
 8. 183 - two mutants killed on the kill-switch arms.

## SUMMARY (recount by hand from the rows; provided as required)

total events: 21 (chunk1-13 and chunk1-21 carry correct: UNCLEAR)
bucket totals: a = 10 (03, 06, 07, 08, 10, 12, 15, 16, 17, 18); b = 5 (01, 05, 13, 19, 20); c = 5 (04, 09, 11, 14, 21); live-exercise = 1 (02)
fix_of_a_fix YES: 6 (08, 09, 14, 15, 18, 20)
inherited YES: 1 (05)
excluded: recitals 5, external-origin 7, ordinary RED-first/mutation 8 - 20 total

## WHAT IS WRONG WITH THE TAXONOMY (challenged as instructed)

1. The buckets classify PREVENTION but the rows record DETECTION, and they disagree constantly. chunk1-02 was detected only by running the real thing, yet is preventable by a contract ("assert the argument handed to the external tool, not the stubbed return"). chunk1-07 was detected by a gate in a foreign tree but prevented by a contract. Forcing one letter loses the more useful fact, which is the PAIR (found-by, prevented-by).

2. A whole class here fits no bucket: WRONG-INSTRUMENT-QUESTION. chunk1-04 and chunk1-09 are not (c) "an adversary with a lens" - no amount of code reading finds them, because the instrument was CORRECT and its question was wrong (bytes moved vs state changed; a restore looks exactly like damage). They are not live-exercise either, since running it is what produced the false verdict. They need a SECOND instrument measuring a different quantity. That deserves its own bucket - call it (d) proxy-measure.

3. "inherited" as defined (true when written, since decayed) barely fires - 1 of 21. Almost every refuted claim in this window was INCOMPLETE AT BIRTH rather than decayed: a roster that never listed the third lane, an attribution that named two of three arms, a control that only ever planted positives. If the axis is meant to separate rot from omission, it currently reads NO for both and only the rot is named. Add the omission value or the axis will read as "durable records are fine" when the real pattern is "records are born partial".

4. fix_of_a_fix conflates two things: the fix being WRONG (chunk1-09, the retraction retracted) and the fix being TOO NARROW for a sibling surface (chunk1-18, the mtime guard that did not cover HALT). In this window the second dominates 5 to 1, and it is the actionable one - it says "sweep siblings", not "you were wrong".

5. No bucket covers the most common shape in entries 185-188 at all: a finding PUBLISHED to another tree and then corrected. The cost there is not a bad commit, it is a sibling acting on a wrong report. A "published-before-confirmed" axis would carry more than the a/b/c split does.

---

# Refutation census - chunk 2 (LEDGER.md lines 388-886, entries 182 down to 173)

Read at full text, every sentence. No keyword grep used.

---

id: chunk2-01
entry: 182
claim: The schtasks registration command shipped in LEDGER 181 was a usable deliverable for the operator.
refuter: The operator, by running it (it failed in PowerShell)
quote: "The `schtasks` line LEDGER 181 shipped used cmd.exe's `\"` escape and the operator ran it in PowerShell, which strips the backslashes"
correct: YES
bucket: a
inherited: NO
fix_of_a_fix: NO
note: the printed command was never parsed by any arm; the repair adds a parse-only arm, which is a mechanical grader.

id: chunk2-02
entry: 182
claim: After the 43-site repair, 2 failures remained (post-repair probe result).
refuter: Same agent, re-running uncontended
quote: "The first post-repair probe reported 2 remaining failures - both timing-sensitive concurrency arms, neither git-related - because it ran while a mutation harness was hammering the same box."
correct: YES
bucket: b
inherited: NO
fix_of_a_fix: NO
note: precondition (idle box) not declared before the measurement.

id: chunk2-03
entry: 181
claim: The inbox responder as built was safe to run against the real inbox (default deny, D1-D8 verbatim).
refuter: Running it once in dry-run
quote: "The first `--once --dry-run` against the real inbox reported **139 new notes** and would have launched a headless session per historical note."
correct: YES
bucket: live-exercise
inherited: NO
fix_of_a_fix: NO

id: chunk2-04
entry: 181
claim: The A3 two-independent-carriers rule was tested.
refuter: Its own mutation pass (mutant survived)
quote: "the A3 independence mutant SURVIVED the first pass - two citations from the same sender were already refused by the count alone"
correct: YES
bucket: a
inherited: NO
fix_of_a_fix: NO

id: chunk2-05
entry: 181
claim: record_seen prune-to-live behaviour was covered by the suite.
refuter: Its own mutation pass (mutant survived)
quote: "`record_seen`'s prune-to-live survived until an arm for a withdrawn-and-refiled note was added"
correct: YES
bucket: a
inherited: NO
fix_of_a_fix: NO

id: chunk2-06
entry: 181
claim: The first false-RED probe run produced a valid with-git / without-git comparison.
refuter: Self-check of the probe's own arms
quote: "The first probe attempt was DISCARDED as a measurement error - its two arms saw different trees."
correct: YES
bucket: b
inherited: NO
fix_of_a_fix: NO

id: chunk2-07
entry: 180
claim: (LEDGER 179's own flag) the "held is 0 in all 28" statistic was the contaminated evidence carrying the scoped_revert case.
refuter: This tree's own held-out measurement, correcting its own earlier flag
quote: "FINDING 1, correcting my own flag: `held` IS the verdict's own output and cannot be evidence, but it was never the load-bearing number."
correct: YES
bucket: c
inherited: NO
fix_of_a_fix: NO
note: UNCERTAIN between (b) and (c) - a "name the load-bearing statistic before accusing" precondition would have caught it, but identifying it needed a lens.

id: chunk2-08
entry: 180
claim: The residue measures (held, still_reads) validate scoped_revert.
refuter: Reading the acceptance code itself (lw_clean_spot.py:330-332) during the held-out pass
quote: "both cited measures count RESIDUE, and on residue scoped cannot lose BY CONSTRUCTION - the band is a subset of the blob and the verdict must still pass"
correct: YES
bucket: a
inherited: NO
fix_of_a_fix: NO
note: textbook bucket (a) - a grader that cannot fail on the axis that matters (art damage is unmeasured; 95.0 percent of the changed area is vouched for only by the stopping rule).

id: chunk2-09
entry: 180
claim: The run_spot_heal docstring's 28.13 -> 1.80 percent improvement figure.
refuter: Attempt to reproduce it from the lane plans on disk
quote: "`handed_back_px` postdates most lanes and exists only in `run_shipdefault` (1.91 percent), so the docstring's 28.13 -> 1.80 percent is NOT reproducible from disk"
correct: YES
bucket: b
inherited: YES
fix_of_a_fix: NO

id: chunk2-10
entry: 179
claim: (probe hypothesis H1, held by this tree on opening) the G1 thresholds are fitted to the winning upscaler's own output.
refuter: Evidence in lw_g1_gate.py:164-167 and lw_golden.py
quote: "CLEARED (H1): the G1 thresholds are NOT fitted to the winning upscaler's own output"
correct: YES
bucket: c
inherited: NO
fix_of_a_fix: NO
note: UNCERTAIN whether a self-opened hypothesis counts as a claim; included because the tree held the premise long enough to open the item on it.

id: chunk2-11
entry: 179
claim: (probe hypothesis H2) the USM census's "17 gated slugs" means 17 slugs that PASSED, so the USM_DEFAULT conclusion is outcome-conditioned.
refuter: Re-reading the census definition and the actual verdict split
quote: "CLEARED (H2): \"17 gated slugs\" in the USM census means \"has a G1 verdict\", not \"passed\" (10 PASS / 7 FLAG / 0 FAIL)"
correct: YES
bucket: b
inherited: NO
fix_of_a_fix: NO

id: chunk2-12
entry: 179
claim: The G1 MS-SSIM arm is decoration - never bound in 719 audits and redundant with lpips at r = -0.872.
refuter: The same agent, by measuring the arm against deliberately degraded frames
quote: "I called it decoration; MEASURING IT REVERSED THAT."
correct: YES
bucket: c
inherited: NO
fix_of_a_fix: NO
note: the repo's own inherited rule ("an arm nobody has seen fail asserts nothing") produced the WRONG verdict here; only a reachability-plus-uniqueness lens reversed it.

id: chunk2-13
entry: 179
claim: dists is a live part of the G1 gate ladder (ADR-007 moved the pixel budget specifically to recover it).
refuter: Sweep of _METRIC_RULES / DEFAULT_G1_THRESHOLDS
quote: "`dists` has no rule at all (`_METRIC_RULES:705-711`, no entry in DEFAULT_G1_THRESHOLDS), so it is computed and stored on every audit and consumed by nothing"
correct: YES
bucket: a
inherited: NO
fix_of_a_fix: NO

id: chunk2-14
entry: 179
claim: lw_clean_creditline.py:104-113 constants represent achieved performance.
refuter: The same probe, flagging them as in-sample grid winners
quote: "Also unverified: `lw_clean_creditline.py:104-113` constants are in-sample grid winners quoted as achieved performance."
correct: UNCLEAR
bucket: c
inherited: NO
fix_of_a_fix: NO
note: explicitly left unverified in-window.

id: chunk2-15
entry: 178
claim: Upscale provenance is captured - every audit records model_sha256.
refuter: This session's audit of what actually asserts the recorded value
quote: "has always RECORDED `model_sha256` into every upscale audit and NOTHING asserted it, so a re-fetched, swapped or truncated weight would drift the frozen golden"
correct: YES
bucket: a
inherited: NO
fix_of_a_fix: NO

id: chunk2-16
entry: 178
claim: The .gitignore _archive/ rule ignores only the root audit-cleanup quarantine; tracked docs-archive files stay addable.
refuter: A live probe writing a new file into docs/_archive and running git add
quote: "Proven live, not theorised - `echo x > docs/_archive/_probe.md; git add -A` exited 0 and added nothing."
correct: YES
bucket: a
inherited: YES
fix_of_a_fix: YES
note: found by running, but the defect class is mechanically gate-able and is now gated by drift_guard.check_tracked_but_ignored; the first fix (an exemption) was itself refuted - see chunk2-17.

id: chunk2-17
entry: 178
claim: (build agent's fix) exempting the affected path is an acceptable way to make the tracked-but-ignored check pass.
refuter: The merging agent's root-cause pass
quote: "The exemption the build agent added to tolerate the bug is RETIRED to an empty tuple rather than left as a standing hole."
correct: YES
bucket: b
inherited: NO
fix_of_a_fix: NO

id: chunk2-18
entry: 178
claim: The new drift_guard wiring was correct as written.
refuter: Its own tests, which found two real bugs in it
quote: "My own drift_guard wiring caught two real bugs in itself under test (`r.message` did not exist, and the absent-note matched a \"verified\" substring)."
correct: YES
bucket: a
inherited: NO
fix_of_a_fix: NO

id: chunk2-19
entry: 178
claim: The suite baseline at HEAD was 2752 passed / 18 skipped (number carried in the hand-off).
refuter: Re-measuring HEAD instead of inheriting the number
quote: "over a re-measured HEAD baseline of **2754 passed / 18 skipped** - the 2752 in the hand-off was stale"
correct: YES
bucket: b
inherited: YES
fix_of_a_fix: NO

id: chunk2-20
entry: 178
claim: Collected count and run count of the suite agree (the basis for every +N delta claim in this window).
refuter: Measuring both with and without the new files
quote: "the suite runs one more item than it collects (2772 run vs 2771 collected at HEAD without these files) - measured both with and without, unexplained, left alone"
correct: UNCLEAR
bucket: c
inherited: NO
fix_of_a_fix: NO
note: UNCERTAIN whether this is a refutation event or only a recorded anomaly; included because a later entry (181) leans on the off-by-one to reconcile its counts.

id: chunk2-21
entry: 177
claim: (LEDGER 176 FUTURE note) GitHub private vulnerability reporting is DISABLED and one PUT will close it.
refuter: The BEFORE probe in the same shell, plus operator confirmation in session
quote: "the BEFORE probe in the same shell already answered `{\"enabled\":true}`, so the `PUT` was a verified no-op (`rc=0`, idempotent) and NOT the thing that flipped it"
correct: YES
bucket: b
inherited: YES
fix_of_a_fix: NO
note: cleanest inherited case in the chunk - the record was true when written and the operator flipped the state by hand between sessions.

id: chunk2-22
entry: 175
claim: done_gate bind reported a real RED (pytest tests/ -q -> 1) on commit ae9b277.
refuter: Three full green suite runs either side of it, paid for at about 4.5 minutes
quote: "The failing test's name was printed by the child and thrown away by the caller's `tail -6`, so two extra full-suite runs (~4.5 minutes) bought nothing"
correct: YES
bucket: a
inherited: NO
fix_of_a_fix: NO
note: literal bucket-(a) shape - a pipeline that discards the producer's evidence. The root cause of the RED itself stays UNKNOWN and is recorded as unknown.

id: chunk2-23
entry: 174
claim: (hand-off brief) there are two whole-token guards to probe for split blindness.
refuter: git grep over tests/, tools/ and .githooks/ before any code was written
quote: "The hand-off named two guards to probe. Only ONE exists"
correct: YES
bucket: b
inherited: NO
fix_of_a_fix: NO

id: chunk2-24
entry: 174
claim: (LEDGER 172) the operator's personal email was purged from the tree.
refuter: git grep for the surname, run as part of the probe
quote: "`git grep` for the surname found the operator's personal address CONTIGUOUS and tracked in FIVE places across THREE files"
correct: YES
bucket: a
inherited: YES
fix_of_a_fix: NO
note: every re-leak site was an artifact written to RECORD the purge.

id: chunk2-25
entry: 174
claim: tests/test_no_account_paths.py guards the tree against account-path leakage.
refuter: Three planted split fixtures proving the misses
quote: "`tests/test_no_account_paths.py` parses the account segment out of a contiguous regex match, so a break AT the separator ends the match"
correct: YES
bucket: a
inherited: NO
fix_of_a_fix: YES
note: the fix (tools/split_scan.py) was itself shown incomplete in-window - see chunk2-26.

id: chunk2-26
entry: 174
claim: The new normalized split scanner closes split-value blindness.
refuter: The Lanternlight 26-character case, asserted as a standing arm rather than glossed
quote: "Two halves separated by UNRELATED text (Lanternlight's 26 characters) never become adjacent under normalisation."
correct: YES
bucket: c
inherited: NO
fix_of_a_fix: NO

id: chunk2-27
entry: 174
claim: The account guard's planted fixtures are safe test data.
refuter: The new sweep firing on the live tree (10 hits over 9 files, 444 scanned)
quote: "The account guard's own planted fixtures were de-identified to a fake account (`mdunning`), so the guard's fixtures are no longer the last tracked copy of the real one."
correct: YES
bucket: a
inherited: NO
fix_of_a_fix: NO

id: chunk2-28
entry: 173
claim: 9 Tier-1 DeviantArt candidates in the batch.
refuter: Re-measurement against lw_recover's own regex, then a second re-measurement
quote: "a first count of 9 Tier-1 candidates was re-measured as 10 against `lw_recover`'s own regex, then corrected BACK to 9 when the tenth proved to be the pre-existing scratch slug"
correct: YES
bucket: b
inherited: NO
fix_of_a_fix: YES
note: the correction to 10 was itself refuted back to 9 inside the same session - a candidate set that moved mid-verdict.

id: chunk2-29
entry: 173
claim: Crop instructions are recorded faithfully into the manifest.
refuter: The implementation pass for the new offset grammar
quote: "`list(crop_sides)` on a dict yields its KEYS, so an offset instruction would have reached the manifest as `[\"top\"]` with the offset silently lost"
correct: YES
bucket: a
inherited: NO
fix_of_a_fix: NO

id: chunk2-30
entry: 173
claim: Two slugs sharing a DeviantArt deviation id are duplicates (near-dup gate verdict).
refuter: phash/dhash measurement, plus the operator approving and shipping both crops
quote: "the two `dmrl7u8-*` slugs share deviation 1376595440 but are phash 26 / dhash 27 apart - a multi-image upload, NOT duplicates"
correct: YES
bucket: a
inherited: NO
fix_of_a_fix: NO

---

## EXCLUSIONS

RECITALS (the refutation happened outside this window and is merely re-told here) - 5:
1. 182 re-telling LEDGER 181's discarded first probe ("the error LEDGER 181 already recorded in its other form").
2. 182 citing RC's structural-blindness finding against RC's own 2116-line guard.
3. 182 citing RSC's charter ruling on widening a matcher after the second defeat.
4. 181 applying CS's and RSC's earlier refutations of RC's responder shape (A3 / A4 / A2 / A5) before the first line of code.
5. 180 re-telling the LEDGER 179 flag against LEDGER 2354's "held is 0 in all 28" (the flag itself is an in-window 179 event; 180's own correction of it is chunk2-07).

EXTERNAL-ORIGIN, never adopted by this tree - 1:
1. 181: RSC's 21:55 claim that the three-disposition ruling is "already latent in the conftest all five of us share", retracted at 22:45 after RC refuted it. LW measured its own tree instead of taking either side and never adopted the premise. BORDERLINE - LW's own measurement (no root conftest, tests/conftest.py 56 lines, zero external-binary invocations) did independently kill it, so a stricter reading would count this as an event.

ORDINARY RED-FIRST TDD FAILURES - 3:
1. 175: both new arms failing on AttributeError: failure_log before implementation.
2. 174: the new test file erroring on ModuleNotFoundError: split_scan before tools/split_scan.py existed.
3. 173: 35 new tests RED-first with failure output captured before implementation.

## SUMMARY

total events: 30
bucket a: 14
bucket b: 9
bucket c: 6
bucket live-exercise: 1
fix_of_a_fix YES: 3 (chunk2-16, chunk2-25, chunk2-28)
inherited YES: 5 (chunk2-09, chunk2-16, chunk2-19, chunk2-21, chunk2-24)
excluded recitals: 5
excluded external-origin: 1
excluded ordinary RED-first TDD: 3

---

# Refutation-event census - CHUNK 3

Source: C:\Legion Wallpaper\docs\LEDGER.md lines 887-1583
Entries actually covered: 172, 171, 170, 169, 168, 167, 166, 165, 164, 163, 162, 161, 160.
BOUNDARY NOTE: the brief said "172 down to 159". Line 1583 is the blank line that
ENDS entry 160; entry 159 begins at line 1584 and is OUTSIDE the chunk. It was read
only far enough to confirm the boundary and is NOT censused here.

---

id: chunk3-01
entry: 172
claim: Scrubbing the operator's personal email from the two tracked doc files (commit 219fdb7) removes the exposure.
refuter: The tree's own pre-action premise probe (git log --all --format='%ae|%ce' over all 526 commits).
quote: the doc scrub alone would have left nearly all of the exposure in place
correct: YES
bucket: a
inherited: NO
fix_of_a_fix: YES

id: chunk3-02
entry: 172
claim: The filter-repo rewrite plus force-push removes the address from the published history.
refuter: A live GitHub API probe run AFTER the force-push.
quote: a force-push does NOT purge GitHub-side unreachable objects - `GET /commits/219fdb70...` still answered 200 after the push
correct: NO
bucket: live-exercise
inherited: NO
fix_of_a_fix: YES

id: chunk3-03
entry: 171
claim: LW carries the pre-push RACE that CS reported (its hook graded one sha, the remote ended at another).
refuter: LW's own probe of .githooks/ before writing any code.
quote: There is none - `.githooks/` holds `commit-msg` and `pre-commit` only
correct: YES
bucket: b
inherited: NO
fix_of_a_fix: NO
note: CS's finding still applied, in a WORSE form. Bucket (b) because the inbound note asserted a mechanism without declaring it repo-specific.

id: chunk3-04
entry: 171
claim: The /done ritual gates what gets pushed.
refuter: The same agent, reading the written order of .claude/commands/done.md.
quote: so every session shipped living-doc edits no run had ever graded. It fired on `e62543b` that evening; CI catching nothing was luck, not a defence.
correct: YES
bucket: a
inherited: NO
fix_of_a_fix: NO

id: chunk3-05
entry: 171
claim: The accepted acceptance line's cleanliness check, `git diff HEAD` empty, is sufficient.
refuter: The implementer, departing deliberately from the brief.
quote: because `git diff HEAD` is blind to an UNTRACKED authored file
correct: YES
bucket: b
inherited: NO
fix_of_a_fix: NO

id: chunk3-06
entry: 171
claim: The pushed sha can be read with `git rev-parse origin/main`.
refuter: The implementer, second deliberate departure from the brief.
quote: the remote-tracking ref is a local cache that a failed push leaves stale, so the cache-reading version agrees with itself about a push that never landed
correct: YES
bucket: b
inherited: NO
fix_of_a_fix: NO

id: chunk3-07
entry: 171
claim: The six-arm mutation result proved the done_gate arms bind.
refuter: The mutation pass itself - two mutants survived.
quote: the first six-arm result LOOKED like proof and was not
correct: YES
bucket: a
inherited: NO
fix_of_a_fix: YES

id: chunk3-08
entry: 171
claim: test_lw_next_session_guard.py pins the hand-off write by naming "section 10b".
refuter: This session's own renumbering of done.md.
quote: pinned the hand-off write to "section 10b"; that section is now 6
correct: YES
bucket: a
inherited: YES
fix_of_a_fix: YES

id: chunk3-09
entry: 170
claim: The concurrency-ceiling property of the shared ops/loop/slots.py is assured (asserted in RC's design prose).
refuter: LW's amendment B, which RC then accepted.
quote: a property asserted in RC's prose and in nobody's test is asserted nowhere
correct: YES
bucket: a
inherited: NO
fix_of_a_fix: NO

id: chunk3-10
entry: 170
claim: The disagreeing-trust-key defect in ~/.claude.json was fixed machine-wide on 2026-09-05.
refuter: A later probe of the Resin Compute checkout, carried outbound as a finding.
quote: the Resin Compute checkout has two path spellings in `~/.claude.json` with DISAGREEING trust [False, True] - surfaced, not edited
correct: NO
bucket: a
inherited: YES
fix_of_a_fix: YES
note: UNCERTAIN. The ledger entry does not itself frame this as refuting CLAUDE.md's "Fixed machine-wide 2026-09-05" line; that contradiction is inferred from the durable record.

id: chunk3-11
entry: 169
claim: The 11 surviving sibling-name hits in RC's public history are all inside the two byte-pinned shared modules.
refuter: LW's independent anonymous-mirror audit, over every object split by type.
quote: Trap (c) turned on its author: a check over the paths you already knew to worry about returns true and useless.
correct: YES
bucket: a
inherited: NO
fix_of_a_fix: NO
note: UNCERTAIN adoption. The scope sentence is RC's, but LW's operator made a decision (declining the offered further rewrite of LW's name) in its context, so it was accepted far enough to act on.

id: chunk3-12
entry: 169
claim: 653 blob hits for "Red Moon" in RC's public history (LW's own first pass, nearly sent).
refuter: The same agent, on inspecting the printed sample lines.
quote: Anchoring to `red[ _-]?moon` took 653 to 3, a 218x inflation.
correct: YES
bucket: a
inherited: NO
fix_of_a_fix: NO

id: chunk3-13
entry: 169
claim: The 2026-09-06 purge of the Claude co-author trailers closed that exposure (and .githooks/commit-msg is the standing backstop).
refuter: LW's audit of commits dated AFTER the public flip.
quote: A history rewrite has no opinion about the commits you make after it.
correct: NO
bucket: a
inherited: YES
fix_of_a_fix: YES
note: Measured in RC's tree, but explicitly generalised ("Same operator behind all five repos, so this one is not only RC's").

id: chunk3-14
entry: 169
claim: A sentence already sitting in RC's tree: "LW is not writing into their inboxes".
refuter: LW's own 18:17 delivery of three byte-identical copies into the sibling trees.
quote: That reversed a sentence already sitting in RC's tree ("LW is not writing into their inboxes")
correct: YES
bucket: b
inherited: YES
fix_of_a_fix: NO
note: Corrected by a fresh 18:20 note rather than an in-place edit - "a claim that travelled needs a correction that travels the same distance".

id: chunk3-15
entry: 168
claim: The inbox watcher reports what the operator has not seen.
refuter: RC's property list (a withdrawal must be reportable).
quote: The report was `entries - seen`, so a note pulled by its sender had no line it could fail to print.
correct: YES
bucket: c
inherited: NO
fix_of_a_fix: YES

id: chunk3-16
entry: 168
claim: The withdrawal fix shipped in this same slice is complete, and its docstring says the ack prunes the report record.
refuter: Running it - not a test.
quote: the ack pruned `seen` only, so a withdrawal re-derived itself forever and could never be cleared
correct: YES
bucket: live-exercise
inherited: NO
fix_of_a_fix: YES
note: "a false rationale authored in the same slice that reported on false rationales". The correction had to be broadcast to four repos already carrying the wrong version.

id: chunk3-17
entry: 168
claim: The tracked-settings guard asserts every declared hook script exists.
refuter: RC's leftover-worktree finding, measured against LW's 10 root-walking guards.
quote: the tenth asked whether every declared hook script EXISTS from `ROOT.rglob`, so a stale worktree answers for a script deleted from the real tree
correct: YES
bucket: a
inherited: NO
fix_of_a_fix: YES
note: The refuted guard is entry 161's, shipped inside this same window.

id: chunk3-18
entry: 168
claim: The receiver-side payload digest (shipped in 165) binds.
refuter: Mutation testing, adopting CS's technique.
quote: PAYLOAD leg green against a size key AND an mtime key - the second a mutant CS had not named
correct: YES
bucket: a
inherited: NO
fix_of_a_fix: YES

id: chunk3-19
entry: 168
claim: The payload walker digests the files in a drop directory.
refuter: CS's four walker findings, reproduced on this box.
quote: a one-file drop reported 32 files because `is_symlink()` is False for a junction
correct: YES
bucket: c
inherited: NO
fix_of_a_fix: YES

id: chunk3-20
entry: 168
claim: The walker classifies every entry it encounters.
refuter: CS's walker findings, reproduced here.
quote: `if is_dir / elif is_file` had no `else`, so an unclassifiable entry fell off the loop.
correct: YES
bucket: a
inherited: NO
fix_of_a_fix: YES

id: chunk3-21
entry: 168
claim: The inbox tests are hermetic.
refuter: The first code that READ the report record (i.e. running the new withdrawal report).
quote: the first code to READ it announced 24 withdrawn notes, 18 of them fixtures
correct: YES
bucket: a
inherited: YES
fix_of_a_fix: YES
note: Entry 162 had already fixed two tests of exactly this class by injecting the path; the shared helper kept the defect.

id: chunk3-22
entry: 168
claim: The recovery pass that cleaned the polluted live record removed only fixture entries.
refuter: The same agent, checking what the cleanup deleted.
quote: Recovery over-purged a genuine entry (`slots.py.proposed-3repo`) and it was restored
correct: YES
bucket: a
inherited: NO
fix_of_a_fix: YES

id: chunk3-23
entry: 168
claim: The junction arm added in this slice is green.
refuter: CI (the Linux `check` job).
quote: The junction arm passed `creationflags` unconditionally - Windows-only, `ValueError` on Linux
correct: YES
bucket: a
inherited: NO
fix_of_a_fix: YES
note: "Mirror image of the trap already recorded in `test_tracked_settings_is_safe.py`" - the same trap entry 161 had already documented in this window.

id: chunk3-24
entry: 167
claim: The comment at tools/lw_facts.py:56-61 correctly explains why the name key was acceptable.
refuter: CS, asking a direct checkable question about LW's tree.
quote: its central claim is inverted exactly as CS argued: an edit CHANGES the content, so a content key SURFACES it and the name key is what hides it
correct: YES
bucket: c
inherited: NO
fix_of_a_fix: NO

id: chunk3-25
entry: 167
claim: That same comment describes the key the module actually uses.
refuter: LW's own read, a defect CS could not have seen.
quote: it was STALE, describing a name key this module stopped using in `271a4f7` earlier the same night
correct: YES
bucket: a
inherited: YES
fix_of_a_fix: YES
note: Deleted rather than reworded, on the argument that a reworded rationale keeps the authority of the original.

id: chunk3-26
entry: 167
claim: LL's two-half property test (report twice -> identical unread set; seen record byte-unchanged and mtime unmoved) proves the property.
refuter: LW, implementing it.
quote: an empty report passes both of LL's halves while proving nothing
correct: YES
bucket: a
inherited: NO
fix_of_a_fix: NO

id: chunk3-27
entry: 167
claim: Making bare `pythonw` load-bearing in all eleven hook commands (LEDGER 166) was verified.
refuter: LL's interpreter warning, arriving about 90 minutes later.
quote: A parameterised path that does not RESOLVE is worse than a hardcoded one
correct: YES
bucket: b
inherited: NO
fix_of_a_fix: YES
note: UNCERTAIN. The new arms passed (5 passed), so no live defect was demonstrated; what was refuted is the sufficiency of a one-time manual check with no standing gate. Also records that `shutil.which` returning a path is what a stub does too.

id: chunk3-28
entry: 167
claim: LW's outgoing cross-repo notes carry a usable timestamp.
refuter: The same agent, stamping the reply with real wall clock per the ritual.
quote: LW's two earlier notes tonight carry the old +375 min skew
correct: NO
bucket: a
inherited: NO
fix_of_a_fix: NO
note: Called out in the outgoing note; the two skewed notes were not restamped.

id: chunk3-29
entry: 166
claim: 32 tracked files carry the operator home path (the ROADMAP row, written earlier in this same window).
refuter: This session's re-measurement before any edit.
quote: the ROADMAP row claimed 32 tracked files, which was a single-separator measurement.
correct: YES
bucket: a
inherited: NO
fix_of_a_fix: YES
note: Real corpus 68, including five files the original sweep never saw at all (a tracked evidence artifact, a captured stdout fixture, two test placeholders, and an 8.3 short-name `ADMINI~1` path).

id: chunk3-30
entry: 166
claim: The scripted sweep removed every account path from the tree.
refuter: The new guard, on the first full-suite run.
quote: A first full-suite run failed on ONE hit - the guard catching this session's own CLAUDE.md wording
correct: YES
bucket: a
inherited: NO
fix_of_a_fix: YES

id: chunk3-31
entry: 165
claim: The inbox watcher surfaces notes the operator has not read (keying on filename).
refuter: RC's request to MEASURE rather than answer from a docstring; LW's fixture-inbox probe.
quote: a note corrected IN PLACE moved nothing the watcher could see, and this channel has already sent notes under a CORRECTION heading
correct: YES
bucket: c
inherited: NO
fix_of_a_fix: NO

id: chunk3-32
entry: 165
claim: A payload directory can be keyed on the MANIFEST.sha256 the sender ships (LW's own cut from two hours earlier).
refuter: RC measured the trap; CS named the principle.
quote: a check whose evidence is supplied by the thing being checked is not a check
correct: YES
bucket: a
inherited: NO
fix_of_a_fix: YES

id: chunk3-33
entry: 165
claim: A SessionStart hook is sufficient to surface incoming mail.
refuter: LW's probe against RC's five properties.
quote: so mail landing mid-session was invisible until the next start - the COMMON case here
correct: YES
bucket: c
inherited: NO
fix_of_a_fix: NO

id: chunk3-34
entry: 165
claim: The tracked .claude/settings.json hook wiring is checked (entry 161's guard asserts it).
refuter: The same probe, looking at what the config actually declares.
quote: `.claude/settings.json` declared `UserPromptSubmit` with an EMPTY hooks array: declared and wired to nothing.
correct: YES
bucket: a
inherited: NO
fix_of_a_fix: YES
note: "an empty array passed every check LW had" - the guard shipped in 161, inside this same window.

id: chunk3-35
entry: 165
claim: The ported secret guard (entry 164) is correct.
refuter: CI, on a docs-only commit describing the guard.
quote: the secret guard read a doc's markdown as part of the value, so a docs-only commit DESCRIBING the guard turned CI red
correct: YES
bucket: live-exercise
inherited: NO
fix_of_a_fix: YES

id: chunk3-36
entry: 164
claim: tools/lw_facts.py reports unread cross-repo mail.
refuter: RC found it on its own tree first and asked everyone to check what theirs globs; LW then measured.
quote: `tools/lw_facts.py` globbed top-level `*.md`, so a payload DIRECTORY was invisible.
correct: YES
bucket: a
inherited: NO
fix_of_a_fix: YES
note: LW had `from-RSC-verbatim/` (7 files) and a top-level `slots.py.proposed-3repo` unreported.

id: chunk3-37
entry: 164
claim: RSC's tests/test_no_secret_literals.py, ported verbatim, is clean on LW's tree.
refuter: Running it over `git ls-files`.
quote: Two false positives fixed rather than exempted away
correct: YES
bucket: live-exercise
inherited: NO
fix_of_a_fix: YES
note: The detector did not recognise `$env:GEMINI_API_KEY = $key` (a bare `$name` is a variable, never a literal), and flagged a fixture planting a fake `sk-` literal.

id: chunk3-38
entry: 164
claim: CS's recorded upstream digest f1b4b011 for the shared winmutex.py is current, so RC's delivery at 0b112a4f means drift.
refuter: LW's diagnosis - the cause was LW's own change.
quote: Nothing drifted: commit `1de8d4e` (2026-09-06, ADR-012) rotated the mutex names to opaque strings
correct: YES
bucket: b
inherited: YES
fix_of_a_fix: NO
note: Also told CS the rotation may dissolve part of ADR-0017's rationale - a second durable record decayed by the same change.

id: chunk3-39
entry: 164
claim: LW's public repo is clean of operator-identifying paths (RC's pre-public audit on LW passed all checks).
refuter: CS's finding about RC's payload, applied inward by LW.
quote: But LW carries the same class independently: 32 TRACKED files, in a public repo.
correct: YES
bucket: c
inherited: NO
fix_of_a_fix: NO
note: inherited flagged UNCERTAIN - whether the 2026-08-01 pre-public clearance was TRUE WHEN WRITTEN is not measured in this window.

id: chunk3-40
entry: 163
claim: The no-em-dash / ASCII glyph rule is enforced by the commit gate.
refuter: RSC's finding, measured live here across all three implementations.
quote: an ellipsis or a non-breaking space in staged content COMMITTED clean and reddened CI on the same commit
correct: YES
bucket: a
inherited: NO
fix_of_a_fix: NO
note: Three re-implementations of one rule disagreed: precommit_gate 6 glyphs, strip_em_dashes 6, test_smart_quote_hygiene 8.

id: chunk3-41
entry: 163
claim: Widening all three glyph sets to the strictest reading fixes the rule.
refuter: The widening itself, which surfaced a second defect underneath.
quote: `strip_em_dashes` prefiltered on UTF-8 `E2 80`, which NBSP does not carry (`C2 A0`), so an NBSP-only file was skipped by the fast path silently
correct: YES
bucket: a
inherited: NO
fix_of_a_fix: YES

id: chunk3-42
entry: 162
claim: The seen-set watcher replaced the mtime-watermark defect, and the handed-forward ritual fix ("ack at session start, not at wrap") closes what remains.
refuter: This project measuring itself, twice.
quote: Six notes on 2026-09-05, five more on 2026-09-06 - marked read having been shown to nobody.
correct: YES
bucket: a
inherited: NO
fix_of_a_fix: YES
note: "That is the mtime-watermark defect the watcher was built to replace, wearing the ACK as a costume instead of the report".

id: chunk3-43
entry: 162
claim: Two existing inbox tests were hermetic.
refuter: Those tests turning red once reported_path existed.
quote: they called `mark_inbox_seen` with a tmp seen file but let `reported_path` default to the real machine record
correct: YES
bucket: a
inherited: YES
fix_of_a_fix: NO

id: chunk3-44
entry: 162
claim: Entry 161's guard docstring - a tracked bypass key "arrives silently with a checkout".
refuter: The same tree, a severity correction; the operator's report about how Claude Code gates permissions.
quote: the claim that a tracked bypass key "arrives silently with a checkout" was overstated
correct: YES
bucket: c
inherited: NO
fix_of_a_fix: YES
note: The ruling itself was left unchanged - only the rationale was corrected.

id: chunk3-45
entry: 161
claim: The public Apache-2.0 repo tracks only repo configuration in .claude/settings.json.
refuter: A measurement of the tracked file on this tree.
quote: the TRACKED `.claude/settings.json` carried `bypassPermissions`, `dangerouslySkipPermissions`, `defaultMode: bypassPermissions`
correct: YES
bucket: c
inherited: NO
fix_of_a_fix: NO
note: inherited flagged UNCERTAIN for the same reason as chunk3-39 - whether these keys were present at the 2026-08-01 public flip is not measured here.

id: chunk3-46
entry: 160
claim: LW's four existing real-commit tests in tests/test_git_hooks_gate.py prove the git hooks refuse.
refuter: Porting RC's real probe and comparing the fixtures.
quote: it was the FIXTURE that was thin
correct: YES
bucket: a
inherited: NO
fix_of_a_fix: NO
note: The old fixture lacked GIT_CONFIG_GLOBAL/SYSTEM isolation, a pinned PYTHON, gpgsign=false, an executable index mode, and used `commit -m` (which tests the shell, not the gate).

id: chunk3-47
entry: 160
claim: The hook-gate probe running green in CI means the gate is armed.
refuter: The porting slice, reasoning about environment skips.
quote: turning the probe's environment skips into FAILURES so an unconfigured clone goes RED instead of green-by-skipping
correct: YES
bucket: a
inherited: NO
fix_of_a_fix: NO
note: UNCERTAIN - the named victim of this failure mode is RC's five hooks at mode 100644; LW's own green-by-skipping is implied, not measured.

---

## EXCLUDED

RECITALS (refutation happened outside this window, merely re-told) - 6:
 1. 170: RSC's own finding that three of its gates were implemented, unit-tested and never consulted by the code that runs.
 2. 163: "LW's earlier 'you are still on the old slots.py' was a nine-minute-stale read and RSC was right" - the round RSC refuted closes here, but the refutation predates the window.
 3. 160: RC's 100644 index-mode regression that made five RC hooks inert on every Linux clone; Lanternlight measured the same 2026-09-06.
 4. 168: RSC measuring a heredoc eating a NUL and reporting SURVIVED on mutations that never applied (RSC's harness, adopted here as a guard).
 5. 169: LL's 1744 measurement that 14 of its 19 outgoing notes leave no trace in its own repo.
 6. 164: CS finding the operator account path in RC's pulled 48-file payload (19 of 48, not the 3 CS first reported) - a correction entirely between RC and CS.

EXTERNAL-ORIGIN, never adopted by this tree - 3:
 1. 164: RC proposing the `(N files)` count key and refuting it within the hour. LW never shipped it.
 2. 169: `refs/tags/backup-pre-scrub-20260621` "reads like a preserved pre-scrub line" but is clean - a candidate finding nobody had asserted.
 3. 168: trailing-dot/space filenames NOT reproducible on this box and explicitly NOT claimed.

ORDINARY RED-FIRST TDD - 5:
 1. 166: test_no_account_paths.py failing on 111 hits with all 15 detector arms passing.
 2. 164: "7 tests RED first, including both defects by name."
 3. 163: test_glyph_rule_has_one_reading.py written RED first (0x2026, then 0xa0).
 4. 162: 8 tests written RED first in tests/test_lw_facts_inbox.py.
 5. 165/171: the RED-first mentions attached to the watcher and done_gate arms.

NOT A REFUTATION (bookkeeping / caveats / gaps, listed so the omission is visible) - 6:
 - 172: CLAUDE.md Settled line updated TWICE -> THREE.
 - 170: the SCOPE caveat that today's slots.py has no reservation, so only one of RC's four proposed properties holds - a self-limiting statement, not a refutation.
 - 163: LW's ARCHITECTURE.md port map "unguarded in exactly RC's way" - a missing guard with no measured drift.
 - 163: RC's stop-claim suite 63 arms vs LW's 48, queued rather than guessed at - a gap.
 - 168/172: FUTURE / not-yet-measured items (LW's refs/pull count, the reserved-lock reap arm).
 - 161: `drift_guard.scan_settings` "had been flagging the wildcard allow and empty deny" - see TAXONOMY note 3.

---

## SUMMARY (to be discarded and recounted)

Total events: 47
Bucket totals: a = 29, b = 6, c = 8, live-exercise = 4
fix_of_a_fix YES: 27
inherited YES: 8
Excluded: recitals 6, external-origin-never-adopted 3, ordinary RED-first TDD 5, not-a-refutation 6

---

## TAXONOMY NOTES (what I think is wrong with the scheme)

1. Bucket (a) is a sink. 29 of 47 land there because "preventable by a gate" is
   true of almost anything in hindsight - you can always name a gate that would
   have caught it. The bucket only discriminates if it means "a gate THAT EXISTED
   and failed" versus "a gate nobody had thought to build". Those two are
   different failure modes and this chunk contains many of each. Suggested split:
   (a1) an EXISTING grader that could not see the defect (chunk3-17, 23, 34, 46);
   (a2) a property that was simply never graded (chunk3-04, 09, 40).

2. (c) IRREDUCIBLE and live-exercise overlap badly. chunk3-16 was found by running
   the thing, but only because RC had first supplied the lens (the withdrawal
   property). Discovery METHOD and discovery PRECONDITION are two axes being
   collapsed into one field. I split them by asking "what was scarce here" - the
   lens or the execution - but several calls were coin flips.

3. There is no bucket for the dominant class in this chunk: A GATE THAT FIRED AND
   NOBODY ACTED. Entry 161 says `drift_guard.scan_settings` "had been flagging the
   wildcard allow and empty deny" - the instrument was right, standing, and its
   output was tolerated until an unrelated audit forced the issue. That is neither
   preventable-by-a-gate nor irreducible; it is a CONSUMPTION failure. I excluded
   it rather than force it, but it is a real and repeating shape.

4. `inherited` as defined (TRUE WHEN WRITTEN and since decayed) undercounts. The
   much commoner shape here is a durable record that was WRONG WHEN WRITTEN and
   inherited anyway because it was credited or confident (chunk3-24: "an attributed
   rationale reads as already-reviewed"; chunk3-16: a false docstring authored in
   the same slice that reported on false rationales). Both are inherited-record
   failures; only one gets a YES. I answered the field as literally specified, so
   the YES count of 8 understates durable-record damage by roughly 3x.

5. `fix_of_a_fix` is nearly always YES in a window like this (27 of 47) because
   the whole window is one long repair cascade on a single subsystem (the inbox
   watcher: entries 159->162->164->165->167->168). The field does not distinguish
   "second defect in the same artifact" from "the fix itself created the defect".
   chunk3-16 and chunk3-22 are the latter and are much more interesting than the
   rest; the flag hides that.

6. `correct: YES|NO|UNCLEAR` is ambiguous between "the finding was correct" and
   "the defect was corrected". I read it as the latter throughout.

7. One event resists the whole scheme: chunk3-14 (LW's own delivery falsified a
   sentence already sitting in another repo's tree). Nothing was defective; a true
   record was made false by a correct action elsewhere. The scheme has no place
   for "correct action invalidates a remote durable record", and cross-repo work
   generates these continuously.

---

# Refutation census - chunk 4

Window: docs/LEDGER.md lines 1584-2119. Entries present in full: **159 down to 145**
(the brief said 158-145; entry 159 begins exactly at line 1584 and is complete inside
the window, so it is censused here. Flag on merge - 159 may also fall in chunk 3.)

Read method: whole chunk read at full text in two passes, no keyword grep.

Convention used for `correct`: YES = the refuted thing was actually corrected,
retracted or narrowed inside this window. NO = acknowledged and left open.

De-duplication ruling (stated because it moves the count): the `slots.hold()`
release leak is narrated TWICE in this window - discovered and verified on LW's own
disk in entry 153, shipped as a fix in entry 157. It is counted ONCE, at 153, and
entry 157 is logged under recitals.

---

id: chunk4-01
entry: 159
claim: The inbox-unread design LW itself proposed one entry earlier (155) used an mtime watermark in sync_inbox_seen.json; at implementation time the watermark was shown to lose mail silently and was replaced by a set of seen FILENAMES.
refuter: the same agent catching itself while writing the implementation and its tests
quote: "a watermark advances on WRITE, so a session cleared before anyone read the output moves past a note nobody saw"
correct: YES
bucket: c
inherited: NO
fix_of_a_fix: YES

id: chunk4-02
entry: 158
claim: Moving LW-NEXT-SESSION.txt into the tracked repo (shipped DONE in 155) was incomplete - it turned the highest-variance artifact in the tree into a public one with no write-time gate.
refuter: Clockspeed's asymmetry finding, relayed by RC
quote: "a Desktop file that is wrong costs one edit, a tracked one costs a history rewrite, and LW rewrote its whole history twice this week"
correct: YES
bucket: b
inherited: NO
fix_of_a_fix: YES

id: chunk4-03
entry: 158
claim: The banned-glyph rule is one enforced rule; found instead to exist as three independent declarations with nothing binding them together.
refuter: this session, while writing the identity-of-function-object test
quote: "it carries THREE declarations of the banned-glyph rule (`strip_em_dashes`, `precommit_gate`, `edit_lint_check`) which agree today with nothing making them agree tomorrow"
correct: NO
bucket: a
inherited: NO
fix_of_a_fix: NO

id: chunk4-04
entry: 156
claim: The public repo carried nothing sensitive; in fact both Global mutex names, the vendor, the single-metered-account fact and a description of a failover defect had been anonymously world-readable for five weeks.
refuter: a live anonymous fetch of the raw tracked file, run by this tree
quote: "`raw.githubusercontent.com/.../ops/loop/winmutex.py` returns HTTP 200 anonymously"
correct: YES
bucket: c
inherited: NO
fix_of_a_fix: NO

id: chunk4-05
entry: 156
claim: The winmutex.py header described the live acquirer set; it named an acquirer RC had since retired.
refuter: RC (sibling repo), folded into the same round on accuracy grounds
quote: "the header asserted an acquirer RC had retired"
correct: YES
bucket: b
inherited: YES
fix_of_a_fix: NO

id: chunk4-06
entry: 156
claim: Condition 4 of the P5 acceptance run was GREEN; the probe identified the adjudicator mutex by the substring GEMINI, so after the rotation it matched nothing and passed on zero evidence.
refuter: the name rotation itself, acting as an unintended mutation test
quote: "condition 4 of the P5 acceptance run reports GREEN on no evidence. A vacuous pass, in the one judge written to close vacuous passes."
correct: YES
bucket: a
inherited: YES
fix_of_a_fix: YES

id: chunk4-07
entry: 155
claim: The session hand-off belonged on the Desktop (the standing /done ritual); shown unreviewable, so a stale hand-off could never be noticed.
refuter: the operator, via RC's cross-repo note
quote: "the Desktop is untracked, unversioned and unreviewable, so nothing can notice a hand-off going stale"
correct: YES
bucket: b
inherited: NO
fix_of_a_fix: NO

id: chunk4-08
entry: 154
claim: Banning the co-author trailer at the commit hook had settled the problem; GitHub still showed claude as a contributor because 84 pre-hook commits kept the trailer in history.
refuter: a live probe of the GitHub contributors surface
quote: "the second contributor came purely from `Co-Authored-By: Claude ... <noreply@anthropic.com>` trailers on 84 commits"
correct: YES
bucket: b
inherited: NO
fix_of_a_fix: YES

id: chunk4-09
entry: 153
claim: slots.reap() is the fail-open valve for leaked lane locks; verified on LW's own disk that a leaked lockfile keeps a live pid, so reap skips it and the valve is disarmed by exactly the case that trips it. (Fix shipped in 157.)
refuter: RSC's leak addendum, verified line by line against LW's own ops/loop/slots.py
quote: "a lockfile leaked by a lost ERROR_SHARING_VIOLATION race keeps a LIVE pid, `reap()` skips it, and the fail-open valve is disarmed by exactly the case that trips it"
correct: YES
bucket: a
inherited: NO
fix_of_a_fix: NO

id: chunk4-10
entry: 153
claim: The repo-wide hard rule atomic-writes-only applies here; measurement showed tmp + os.replace is the one write that FAILS against an open reader handle, so the only viable neutralisation is a non-atomic in-place write.
refuter: LW's own live measurement on the Windows box
quote: "So proposal 3 is viable AND must be a direct in-place write that CANNOT be atomic - which collides with both repos' atomic-writes-only house rule"
correct: YES
bucket: live-exercise
inherited: YES
fix_of_a_fix: NO

id: chunk4-11
entry: 153
claim: The ci.yml header's "~28s whole suite" figure described the suite; it was a bring-up number long overtaken.
refuter: the same agent, while editing that header to record the badge answer
quote: The stale "~28s whole suite" figure in that header, from bring-up, is corrected to 2521/18.
correct: YES
bucket: a
inherited: YES
fix_of_a_fix: NO

id: chunk4-12
entry: 152
claim: The over-target downscale-only case and the USM question were separate concerns; found entangled because 4096x2305 is not exactly 2560x1440, so _usm_applies is True and that branch DOES sharpen. UNCERTAIN - the prior belief is implied by "entangled, not adjacent" rather than stated outright.
refuter: the same agent, premise-checking before regenerating the golden set
quote: "the over-target case and the USM question are entangled, not adjacent"
correct: YES
bucket: c
inherited: NO
fix_of_a_fix: NO

id: chunk4-13
entry: 151
claim: LEDGER 19's adopted 5/6 wrist-on-weapon number was portable across execution providers; re-measurement restated it as 5/6 frames / 10/12 wrists, two wrists falling through min_conf on CUDA, because the original artifact never recorded its provider.
refuter: a later probe - this session's dual-provider re-measurement
quote: "LEDGER 19's number had to be re-measured from scratch precisely because its artifact did not record the provider"
correct: YES
bucket: b
inherited: YES
fix_of_a_fix: NO

id: chunk4-14
entry: 150
claim: LW's cross-repo byte guards compare the shared loop files; they take a skip-when-absent branch, so a renamed sibling makes them compare nothing and stay green.
refuter: RC's incident report (Amberstone e752e4edc), then confirmed structurally on LW's own tree
quote: "LW carried the identical structure aimed at `C:\Riot Commander` (`tests/test_loop_concurrency.py`, `tools/drift_guard.py:194`)."
correct: YES
bucket: a
inherited: YES
fix_of_a_fix: NO

id: chunk4-15
entry: 150
claim: The root re-spelling in 146 shipped DONE with a 177-spelling sweep over 60 files; it silently disarmed RC's guards for about 3 hours because the sweep never reached the sibling's constants.
refuter: RC (sibling repo)
quote: "LW's root rename silently disarmed RC's cross-repo guards for ~3 hours"
correct: YES
bucket: b
inherited: NO
fix_of_a_fix: NO

id: chunk4-16
entry: 149
claim: Running tests/test_lw_golden.py before and after the NVIDIA driver bump would protect the golden baseline; the test never touches the GPU, so the plan proved nothing.
refuter: the same agent, premise-correcting mid-item (logged as "Premise CORRECTED twice")
quote: "`tests/test_lw_golden.py` does NOT exercise the GPU - it tests the freeze/regress tool against tmp_path in 0.06s, so running it before and after a driver change proves nothing"
correct: YES
bucket: a
inherited: NO
fix_of_a_fix: NO

id: chunk4-17
entry: 149
claim: pipeline_version tracked the shipping recipe; _pinned_from_config hardcoded USM 70 while lw_upscale.USM_DEFAULT moved to 35 five weeks earlier, so the hash read unchanged straight through a real sharpening change.
refuter: the same agent, second of the two corrected premises
quote: "a version hash blind to the version moving, the same failure mode as a restated port literal"
correct: YES
bucket: a
inherited: YES
fix_of_a_fix: NO

id: chunk4-18
entry: 149
claim: The 1341679-banding golden flag was driver drift; the baseline predates the G0 over-target downscale-only branch by 64 minutes, so it was a stale baseline.
refuter: the same agent, tracing the baseline freeze timestamp against the branch's landing commit
quote: "Stale baseline, not a regression, not the driver."
correct: YES
bucket: a
inherited: YES
fix_of_a_fix: NO

id: chunk4-19
entry: 148
claim: The incoming premise was that .venv-gen carried a CPU-only onnxruntime and a wheel swap would move DWPose to the GPU; only the first of three required conditions had been reported, and a hardcoded CPUExecutionProvider list meant the new package changed nothing.
refuter: the same agent, attempting the change (logged as "Premise VERIFIED and then found INCOMPLETE")
quote: "swapping the wheel alone would NOT have moved a single node. Three things had to be true and only the first was reported."
correct: YES
bucket: b
inherited: NO
fix_of_a_fix: NO

id: chunk4-20
entry: 148
claim: get_available_providers() listing CUDA proves the GPU provider is bound; measured that ORT fails the CUDA provider silently and keeps listing it, so the standard check would have shown healthy while every node ran on the CPU.
refuter: live measurement on the box - os.add_dll_directory alone and a ctypes preload both left the session on CPU
quote: "ORT fails to load its CUDA provider and falls back SILENTLY - no exception, and `get_available_providers()` still lists CUDA"
correct: YES
bucket: live-exercise
inherited: NO
fix_of_a_fix: NO

id: chunk4-21
entry: 148
claim: DWPose's exemption from the machine-wide GPU mutex was justified by a code comment citing LEDGER 19 as settling onnx-CPU; LEDGER 19 settled the localizer CHOICE only, and the CPU provider was an accident of the installed wheel.
refuter: tests/test_gpu_mutex_wiring firing on the provider change, then a re-read of the cited ledger entry
quote: "LEDGER 19 settled the LOCALIZER CHOICE, not the execution provider, and the CPU provider was an accident of the installed wheel"
correct: YES
bucket: a
inherited: NO
fix_of_a_fix: NO

id: chunk4-22
entry: 148
claim: The 38s first GPU run implied a break-even of about 146 images; it was one-time sm_120 PTX JIT that the driver caches, so break-even is about 3. UNCERTAIN - the ~146 figure is presented as what the cold measurement WOULD have yielded, not as one this tree published.
refuter: repeated runs on the same box, the driver's JIT cache showing up on the next processes
quote: "break-even is ~3 images, not the ~146 the cold number implied"
correct: YES
bucket: live-exercise
inherited: NO
fix_of_a_fix: NO

id: chunk4-23
entry: 147
claim: The root move in 146 completed; the tree arrived with all 46 entries but no .git, because the copy skipped Windows HIDDEN items and dropped exactly the repository.
refuter: the next session's own inspection of the moved tree
quote: "the tree arrived complete (46 entries) with NO `.git`, and the three `C:\` helper files were gone too"
correct: YES
bucket: a
inherited: NO
fix_of_a_fix: NO

id: chunk4-24
entry: 147
claim: The init + remote add + fetch + reset recovery restored the repository; core.hooksPath lived in the destroyed config and was NOT restored, leaving the authoritative gate dead.
refuter: tools/install_git_hooks.py --check
quote: "`core.hooksPath` had to be reinstalled separately - it lived in the destroyed config and is not restored by the above"
correct: YES
bucket: a
inherited: NO
fix_of_a_fix: YES

id: chunk4-25
entry: 146
claim: A session-0 scheduled task retrying once a second would win a gap and rename the live root; 180 seconds of retries never won one, because Windows refuses to rename a live process's cwd.
refuter: live exercise - the retry loop itself
quote: "proven by 180s of 1-second retries from a session-0 scheduled task never winning a gap"
correct: YES
bucket: live-exercise
inherited: NO
fix_of_a_fix: NO

id: chunk4-26
entry: 146
claim: ops/loop/slots.py named Red Moon as a participant; Red Moon had been re-spelled to Resin Compute, so the shared file's docstring was stale.
refuter: RM (sibling repo) via the inbox round, verified against this tree before editing
quote: "`ops/loop/slots.py` now names Resin Compute where it named Red Moon"
correct: YES
bucket: b
inherited: YES
fix_of_a_fix: NO

id: chunk4-27
entry: 145
claim: The framing accepted into the session was MIT vs Apache-2.0 under a goal of preventing download-alter-commercialize; the premise is void because both are permissive and the governing axis is permissive vs copyleft.
refuter: this tree's own research, refusing the operator's framing
quote: "The premise is void: MIT and Apache-2.0 are BOTH permissive and both grant exactly that."
correct: YES
bucket: c
inherited: NO
fix_of_a_fix: NO

id: chunk4-28
entry: 145
claim: Green CI covered the suite; test_worker_spandrel_branch_produces_both_variants fails locally with a CUDA OOM and CI is green only because no runner has a GPU.
refuter: the local suite run, against the green CI signal
quote: "This session touched one PNG and zero Python, and CI is green because no runner has CUDA."
correct: NO
bucket: a
inherited: NO
fix_of_a_fix: NO

---

## Summary (to be discarded and recounted)

Total events: 28

By bucket (by id, authoritative):
- a (preventable by a gate): 03, 06, 09, 11, 14, 16, 17, 18, 21, 23, 24, 28 = 12
- b (preventable by a contract): 02, 05, 07, 08, 13, 15, 19, 26 = 8
- c (irreducible): 01, 04, 12, 27 = 4
- live-exercise: 10, 20, 22, 25 = 4

fix_of_a_fix YES: 01, 02, 06, 08, 24 = 5
inherited YES: 05, 06, 10, 11, 13, 14, 17, 18, 26 = 9
correct NO: 03, 28 = 2
UNCERTAIN-flagged: 12, 22 = 2

Excluded:
- RECITALS (refutation happened outside this window, or is the same in-window event
  re-told): 4 - entry 157's full re-telling of the slots leak, counted once at 153;
  entry 154's 2026-07-26 "84 of the last 200 commits" measurement; entry 152's
  reproduction of the 2026-08-02 USM census; entry 145's mention of the ADR-010/011
  reversal pair.
- EXTERNAL-ORIGIN claims never adopted by this tree: 7 - RSC's premise that its own
  flip would be the first publication (156); RC's stale-file write/consume diagnosis,
  checked and found not to apply to LW (155); RC's docs-guards badge plus
  md_guard_selector.py proposal, rejected as structurally moot (153b); RC's own
  28-passed-to-25/3 suite incident, which is RC's defect not LW's (150); and three
  external license beliefs examined and rejected in 145 (CC BY-SA as the loose option,
  the GPL ingest bridge, license-driven GitHub visibility).
- ORDINARY RED-first TDD failures: 11 entries' worth - 159 (17 RED), 158 (18 of 27
  RED), 157 (4 RED), 156 (2 pinning tests), 155 (9 failing), 152 (2 RED), 151 (3 RED),
  150 (5 RED), 149 (RED-first), 148 (RED-first on both helpers), 146 (RED-first on the
  ports contract).

## Where the taxonomy is wrong

1. The four buckets are not one axis. (a) and (b) name a PREVENTION mechanism;
   live-exercise names a DISCOVERY channel. Ids 10, 20 and 25 are all of them at once:
   only findable by running the thing, AND trivially gateable once known. Forcing one
   label destroys information. Split into two fields - prevention (gate / contract /
   adversary) and discovery (code-read / run / sibling / operator / CI).

2. A whole bucket is missing: STALE DURABLE RECORD. Nine of 28 events are a constant,
   a cited number, a docstring, a baseline or a comment that was TRUE when written and
   rotted (05, 06, 10, 11, 13, 14, 17, 18, 26). I was forced to file most of them under
   (a), which reads as "someone forgot a test" and hides the real mechanism: nothing in
   the system dates its own facts. The `inherited` axis captures it, but then the
   bucket field actively misleads.

3. VACUOUS GREEN deserves its own name. Ids 06, 14, 16 and 28 are four independent
   instances in 15 ledger entries of a check that passed while measuring nothing - a
   substring matcher after a rename, a skip-when-absent guard, a GPU-less test used as
   a GPU control, a GPU-less CI runner. Filing them under (a) alongside ordinary
   missing coverage understates how specific and how repeated the pattern is.

4. `correct` is ambiguous as written - readable as "the refutation was correct" or "the
   defect was corrected". I used the second and said so. Pin it in the brief, or chunks
   scored under different readings will not merge.

5. `fix_of_a_fix` is too coarse for a tree with byte-identical cross-repo files. It
   cannot distinguish "fix of my own earlier fix" (01, 24) from "fix of a fix I
   inherited byte-identical from a sibling" (09), and only the second forces a joint
   round and a re-pin.

6. The window boundary interacts badly with the ledger's newest-first ordering. A
   defect introduced at 146 is refuted at 147 and 150; a design proposed at 155 is
   refuted at 159. Counting by entry puts the refuter before the claim. Any merge
   across chunks must de-duplicate by DEFECT, not by entry.
