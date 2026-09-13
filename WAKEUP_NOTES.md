# WAKEUP_NOTES - LW hand-off ledger

---

## NEXT SESSION - three corpora scored; the open question is the `inherited` gap

**RSC's 96 rows are SCORED and filed** (LEDGER 200). Two blind passes under the
same pre-registered convention (`770684b`, unamended, third corpus). Result:
`docs/LW_SCORED_RSC_2026-09-13.md`; all 96 rows both passes in
`..._ROWS_...`; scorer output `docs/_crossscore/scored_D*.psv` + `scored_E*.psv`;
reproduce with `python docs/_crossscore/rsc.py`.

**LW on RSC's corpus, fine grain, N=96:** gate-or-contract 74.0 / 75.0,
inherited 76.0 / 78.1, fix-of-a-fix **5.2 / 7.3 (a FLOOR)**,
BORN-WRONG:DECAYED 12.00:1 / 10.33:1, `correct` 93 YES / 3 UNCLEAR / 0 NO.

**NEVER quote the fix-of-a-fix figure without the word FLOOR**, and never present
it against RSC's 18.5 as a refutation - RSC's rows record no chains, so LW scored
`fix` down wherever the text established no forward link. LW's floor sits below
RSC's own 12.5 pct ceiling. Consistent, not contradictory.

**THE REPLICATION - the strongest result LW holds.** All **24 of 24**
family-moving disagreements on RSC's corpus involve `PROXY-MEASURE` or
`ADVERSARY`, zero counterexamples - against **22 of 22**, also zero, on RC's.
Two corpora, four scorers, one convention. **The family boundary is unstable at
exactly two values and nowhere else**, and they are the two RSC proved defective
analytically (rank 4 unreachable, rank 8 not a sink).

**A PREDICTION THAT HELD.** Three of four blind scorers independently named
`GATE-EXISTING` vs `GATE-ABSENT` under v1.2's tie-breaker as the hardest call
BEFORE the comparison ran. Measured: 30 of 36 disagreements (83 pct) touch those
two values. **Third independent hit on a v1.2 defect that neither RC's nor RSC's
full adversarial audit found** - reading a clause and applying it to a row find
different defects. That is now a pattern and it is the cheapest finding available
to any tree with rows on disk.

**WITHDRAWN BY LW: the ~26 pct adjudication rate is NOT a fleet constant.** LW
had 27.4 pct on RC and RC had 26.1 pct on its own, which looked constant. **RSC's
is 37.5 pct set disagreement and family disagreement DOUBLES, 11.1 -> 25.0 pct.**
The adjudication rate is a property of the CORPUS - a tree whose defects cluster
on a contested boundary is harder to score and no contract version changes that.

**THE OPEN QUESTION - the `inherited` gap.** Convention held fixed, scorers
varied: inherited **RSC 76.0-78.1 pct against RC 46.0-54.0** (25 points), and
BORN-WRONG:DECAYED **RSC 10.33-12.00:1 against RC 2.62-3.25:1** (4x), on the
field v1.3 calls most load-bearing. **LW CANNOT attribute this to RSC's tree**:
LW scored from RSC's prose alone with no access to their ledger or git, and an
extractor writing in the past tense about prior sessions reads INHERITED more
often. Separating the tree from the extraction voice needs someone with RSC's
history. That is the next real question in this lane.

**Third corpus, same null:** no D-vs-E share gap distinguishable from zero
(p = 1.000 / 0.625 / 0.754). After RC's 0.503 / 0.388 / 0.625. The scorer does
not move the published share on any corpus measured so far.

**`correct` is a non-result for the FIFTH time** (RC 0/198, LW 1/126, RSC 64/65,
LW-on-RC 198/198, LW-on-RSC 93/96 with 0 NO). Nobody should publish it as a Q1
answer.

**Blinding, both directions.** LW's strip leaked on 49 of 198 rows; RSC's
never-scored corpus leaked on 1 of 96 (`EV-072`, "DECAYED" in prose). RSC's
structural anchor reproduces exactly (96 / 32 / 8), so their "no anchor" claim
was too strong. **Neither tree may ASSERT blinding - check it.** Always redact
taxonomy tokens from free text before scoring.

**KNOWN FLAKE, unexplained.** `tests/test_lw_usm_halo_probe.py::
test_worker_spandrel_branch_produces_both_variants` FAILED on one full-suite run
this session (1 failed / 2920 passed), then passed in isolation and passed a
second full run, on a docs-only working tree. It is NON-DETERMINISTIC, not a
regression. Nobody has found the cause. If it goes red again, that is the second
data point - capture the seed and the output before re-running.

**Standing limit, adopted from RC verbatim:** this measures spread between READS,
not between independent intelligences, so **every rate is a LOWER bound.**

**Contract position unchanged: NO v1.4 CLAUSE SET.** Decomposition repairs are
cheap; adjudication repairs buy an undefined term. The refuted-remedy question is
answered by DECOMPOSITION (record every link so forward and links-as-events
corpora are interconvertible). `discovery` is already split three ways; do NOT
publish a `found_stance` histogram while legacy rows carry `UNRECORDED`.

**Also retracted earlier and still retracted:** "the scorer beats the contract",
the 6.9 / 10.3 share gaps, the 3.75x union ratio, the "convention is larger on
all three" over-read, and LW's 22.5-point pricing of FATAL-1 as a comparability
cost. Quote LW FINE GRAIN ONLY, never a band. LW's own corpus is 126 EXTRACTED /
124 SCORED. **DO NOT RE-SCORE LW'S OWN ROWS against any contract version.**

**Operator rules in force (2026-09-12):** never ask for reply auth or direction;
choices go to the ADJUDICATOR or THE LANE; cross-tree writes are SYNC-INBOX ONLY.
Memory `feedback-no-operator-direction-inbox-only-writes`.

## SUPERSEDED - the v1.3-out-for-attack block

**RC audited LW's pin and filed 5 FATAL / 10 MATERIAL / 4 COSMETIC (LEDGER 194).
All five fatals conceded.** LW priced them on its own corpus: FATAL-1 (the pin
never defines an EVENT, so never defines its denominator) is worth **22.5
points**; the others are 4.0, 1.6 and 0.8. Individuation alone moves LW's
fix-of-a-fix from 24.2 to 46.7 pct.

**Every LW share is a BAND now, never a point estimate:** gate-or-contract
82.3-93.3, inherited 62.9-80.0, fix-of-a-fix 24.2-46.7. Two LW figures have been
withdrawn in this exchange and both went the same way - a ratio published before
its denominator was defined. Do not quote a single number from these docs.

**DO NOT RE-SCORE A THIRD TIME** until `docs/REFUTATION_TAXONOMY_PIN_v1_3.md` has
survived a round of attack. Re-scoring against a moving contract is the
refute-fix-refute loop this lane exists to measure. That is a deliberate hold,
not an oversight.

**LL HAS reported - LW's "LL has not reported" was BORN-WRONG and is corrected.**
LL's count went to CS, RC and RSC on 2026-09-12; LW was never on the address
list. Not lost mail: their note's own line 3 names three addressees and LW is not
among them. **LL is the DISSENT at 31.1 pct program-reachable against the other
four trees' 78-93 pct**, largest bucket REAL DEFECTS IN THE DELIVERABLE. Read
their note from a sibling inbox if it still has not arrived here. LW has pinged
LL directly; the ask is one line - add LW to the roster.

Still open and unrepaired: RC's MATERIAL-1 (a gate firing on a REMEDY has nowhere
to be recorded), plus nine other MATERIAL findings. Q4 consensus is unchanged -
LW, RSC and CS all named a mutation / non-vacuity gate; LW has the rule and zero
tooling.

**Operator narrowed the lane 2026-09-12:** never ask for reply auth or direction,
choices go to the ADJUDICATOR or THE LANE, cross-tree writes are SYNC-INBOX ONLY.
Memory `feedback-no-operator-direction-inbox-only-writes`.

## SUPERSEDED - the v1.2 round

**Four counts are in and LW has re-scored (LEDGER 193).** LW 73.8 / RSC 78.5 /
RC 80.3 / CS 83.3 pct, all under different readings. LW pinned the definitions
(`docs/REFUTATION_TAXONOMY_PIN_v1_2.md`) and re-scored its own 126 rows:
**82.3 pct gate-or-contract, GATE-ABSENT beats GATE-EXISTING 2.2 to 1, inherited
62.9 pct with BORN-WRONG over DECAYED 3.11 to 1, fix-of-a-fix 24.2 pct.**

**Three things not to re-derive or re-argue.** (1) LW's published strict
fix-of-a-fix 4.8-6.3 pct is WITHDRAWN - it is 24.2 pct forward-pinned, which
closes the gap against RC's 19.1. (2) RC has RETRACTED its pre-dispatch
re-grounding gate on its own back-test; do not re-pitch it, and note LW's
born-wrong majority is a second independent reason it was never the lane. (3) The
naive corpus-hole figure of 90.2 pct is a TRAP - control for the mid-window
history rewrite first, it is 14.1 pct of substantive commits.

**NEXT: LL has not reported.** Check `moon_sync_inbox/` before touching the row.
Q4 consensus is emerging around a mutation / non-vacuity gate - LW, RSC and CS
named it independently, CS's per-arm kill proof with an observability control is
the most developed, RSC already owns a runner. LW has the RULE and ZERO tooling
(`ls tools/ | grep -i mutat` is empty). If the fleet builds it, exchange the
described MECHANISM and never byte-pinned source.

**Operator narrowed the lane 2026-09-12:** never ask for reply auth or direction,
choices go to the ADJUDICATOR or THE LANE, cross-tree writes are SYNC-INBOX ONLY.
Memory `feedback-no-operator-direction-inbox-only-writes`.

## SUPERSEDED - the first-round count (kept for the method, not the ratios)

**Do not build anything on the tooling tier yet.** ROADMAP carries the row; the
ask is fleet consensus first. LW's count is filed (LEDGER 192,
`docs/REFUTATION_COST_MEASUREMENT_2026-09-12.md`): 126 events over ledger
entries 145-191, (a)+(b) 73.8 pct, Q4 = a non-vacuity gate. RC answered at 80.3
pct. RSC and CS and LL had not answered as of 2026-09-12 1905. **Next session:
check `moon_sync_inbox/` for their counts before touching this row.** LW's
standing ask is to pin the definitions of `fix_of_a_fix`, `correct` and a
prevention-versus-discovery split and have each tree re-score its OWN rows; four
counts are not comparable until then, and RC's 19.1 pct sits between LW's two
readings of the same field.

**Two things not to re-derive.** (1) The three history-rewrite maps DO NOT CHAIN
- CLAUDE.md is corrected with the measurement inline. Resolve a cited sha in the
09-07 map FIRST. (2) **LW has NO dead-citation finding.** A claim that six cited
test files were fabricated was retracted by its own author within the hour: they
are foreign paths, to-dos and sentences asserting absence. Do not re-run a bare
path-existence sweep over the docs and file the result - the instrument cannot
tell a dead citation from a correctly-cited foreign file, and a re-grounding gate
built without a claim-reading step will manufacture that false positive at scale.

**Where the raw rows live:** `docs/REFUTATION_COST_ROWS_2026-09-12.md`, tracked,
1666 lines, all 126 per-event rows with each pass's own (non-authoritative)
summary retained. A fleet re-score against pinned definitions can run off that
file without re-opening the ledger.

---

## NEXT SESSION - the parked pipeline queue

**LW's finding against Lanternlight is RETRACTED (LEDGER 188).** LL re-measured:
both records byte-identical, the bytes were their RESTORE, the hook's real
writes were in a subprocess the tracer cannot see. Do not re-measure LL's inbox
records and do not re-file that finding. The cross-repo audit is CLOSED on every
sibling. The lesson is now a mechanism, not a memory: the tracer's report
carries a `bytes_not_state` limit key, and an arm plants a snapshot-restore
guard to assert the record is byte-identical WHILE the tracer names the
restoring test. Before filing anything that tracer reports, hash the path before
and after.

**`truth_gate.check_ci` was reading a completed green as `queued` for any
ABBREVIATED sha (LEDGER 190, fixed at `db75ca0`).** Found by following LW's own
wrap ritual: `done_gate bind` prints 12 chars, `gh run list --commit` matches 40.
Any sha is resolved now. If a CI poll ever sits on `queued` forever again, check
what was ASKED before believing the answer.

**ALL THREE HEADLESS LANES ARE DISARMED as of this wrap (operator direction;
LEDGER 189 + 191 - the weekly-hygiene lane had NO switch at all and one was
added, arms in tests/test_headless_lane_kill_switches.py).** The kill switches
are on disk: `ops\runtime\inbox_responder\HALT`, `ops\runtime\ci_watchdog\HALT`
and `ops\runtime\weekly_hygiene\HALT`. The scheduled tasks are still registered
and still Ready - the HALT files are what stop them, checked before any work is
done, and all three were PROVED halted by running them. RE-ARM is deleting the
three files, and it is the OPERATOR'S call, not a next session's housekeeping.
Do not delete them to "fix" a task that looks idle.


**The Clockspeed call is CLOSED and CS is fixed and pushed** (CS `10a7e52`,
LEDGER 187). Do not re-measure it, do not re-file it, and do not re-open the
cross-repo audit - RSC self-fixed at `7786955`, RC has its own tracer, LL was
told about its inbox ack state, and LW itself was fixed at `ec9c8d6` /
`f319583`. The operator's answer was FIX CS DIRECTLY and that authority was for
that repair; it is NOT a standing licence to edit sibling trees. Ask again next
time.

**The one durable lesson, and it cost a red run:** do not edit a sibling's
tracked file MID-FILE without checking its line pins first. CS pins source line
numbers from `docs/item_notes/` and an insertion above line 2089 in
`tests/save/test_phase4_gate.py` reddened `test_docs_citations.py` twice. The
repair is to APPEND AT THE FOOT, never to re-cut the digest - that guard's own
message names re-cutting as the trap. CS's own `tests/conftest.py` records the
same rule for the same reason.


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

**LW-InboxResponder is ARMED as of 2026-09-11** (operator direction; LEDGER
183). Registered, Ready, forced run `LastTaskResult` 0, baselined at 142 notes /
0 spawned. It fires every 5 minutes and spawns a DETACHED HEADLESS session on a
note that is new by content digest. Do NOT re-register and do NOT re-baseline -
re-baselining swallows every note that arrived since. Stop it mid-flight with
`type nul > "ops\runtime\inbox_responder\HALT"` (an empty file counts; it is
checked before the inbox is read), release with `del`. Known and deliberate: the
allowlist is enforced as prompt INSTRUCTIONS to a `bypassPermissions` session,
not mechanically. That is RC's adopted shape and it is the trial's real risk
surface - if the trial goes wrong, that is where to look first.

**Acceptance, unchanged:** `python -m pytest tests/ -q` green, ruff clean,
`python tools/drift_guard.py` exit 0, `python tools/done_gate.py bind` exit 0,
then push the bound sha. The suite still runs one more item than it collects -
PRE-EXISTING.

---

## 2026-09-11 - the inbox responder's run log, and the hermeticity bug it exposed in four trees (LEDGER 184-185)

Started from "is the sync inbox lane properly set up". It was: report, ack,
outbound fan-out and the armed responder all probed live and working. The one
gap was observability, and closing it uncovered a bug class in four repos.

Shipped: ec9c8d6 run log (`ops/runtime/inbox_responder/runs.jsonl`, non-idle
cycles only, append not tmp-replace), f319583 two further LW live-write fixes,
ebbb6f3 LEDGER 185, 7a5f92b `tools/lw_write_tracer.py` promoted to a tracked
tested artifact, 7ca9396 the planted control.

**METHOD, and it is the durable lesson.** A snapshot diff around a suite run is
INVALID on this box - a 300s idle control with NO suite running showed all four
candidate files changing anyway (daemons, other sessions). Two of the first
three conclusions were withdrawn on that evidence. Use
`tools/lw_write_tracer.py`: process-local, patches `builtins.open`, `io.open`,
`os.replace`, `os.rename`, counts BYTES, plants a control every run.

**`io.open` is a SEPARATE binding from `builtins.open`.** Patching only
`builtins` misses every `Path.write_text`. That hole made every figure published
before 7a5f92b a lower bound and produced one wrong CLEAN verdict.

Do NOT redo: the LW fixes are shipped and the suite traces clean (control
proved, all buckets empty, 2912 passed). Do not re-measure LW. Do not re-run the
snapshot-diff approach. RSC fixed itself (7786955); RC is on it with its own
tracer; LL was told its suite writes its own inbox ack state.

Open: CS has 23 `*.copy.sav` written into live `work/saves/` and nobody on it -
the operator was asked whether LW should fix CS and RSC directly and had not
answered at wrap. Nothing in any sibling tree has been edited by LW.

---

## 2026-09-11 - LW-InboxResponder armed, and the kill switch that required (LEDGER 183)

- **Armed on operator direction.** PT5M indefinite, Limited, pythonw so nothing
  flashes. Verified by reading the scheduler back, not by assuming the register
  call meant it: State Ready, Interval PT5M, Enabled True, forced run result 0.
- **Baselined under supervision:** 142 notes, 0 spawned. The cold-start footgun
  caught in dry run on 2026-09-10, made real and harmless.
- **New kill switch** `ops\runtime\inbox_responder\HALT`, checked FIRST so it
  beats the baseline write too. An EMPTY file still halts - lifted from
  `ci_watchdog.halted`, which learned that one first. 5 arms including the
  mirror, 2 mutants killed, live halt-then-release smoke test on the real path.
- **Said out loud rather than buried:** the allowlist is prompt INSTRUCTIONS to a
  `bypassPermissions` session, not a mechanical gate. RC's shape, adopted.

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
