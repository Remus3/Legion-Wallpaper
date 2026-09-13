# Refutation cost - the 126 rows re-scored under PIN v1.2, 2026-09-12

Every row from `REFUTATION_COST_ROWS_2026-09-12.md`, re-scored against
`REFUTATION_TAXONOMY_PIN_v1_2.md`. Two passes re-scored rows they did not
extract, then two further passes re-derived `prevention`, `fix_chain` and
`chain_kind` after the pin's fatal direction defect was fixed.

`chunk2-10` and `chunk2-11` carry no scores: the pin's exclusion 4 removes them
(hypotheses opened by a probe whose stated purpose was to test them, cleared as
that probe's intended output). 126 events, 124 scored.

`moved:` on a row names which field changed from the previous scoring and why.
A `fix_chain` of 0 where the record did not establish a forward link is a FLOOR,
scored down rather than guessed upward.

Summing `fix_chain` across rows OVER-COUNTS: the pin treats a chain as one event,
while this census persisted each link as its own row, so two rows can share a
remedy. Count ROWS with `fix_chain >= 1`.


---

# Part A - re-score of 51 rows (chunk1-01..21, chunk2-01..30) against REFUTATION_TAXONOMY_PIN_v1_1

Read-only. No tracked file touched. Three fields re-derived (prevention, fix_chain,
chain_kind); every other field copied through byte-for-byte from the v1 scoring.

Rules applied, stated so the recount is checkable:

- **PROXY-MEASURE** used only where the instrument was CORRECT, running it is what
  produced the false verdict, and the remedy is a SECOND instrument measuring a
  DIFFERENT quantity. An instrument that was itself holed or vacuous is NOT this
  class (chunk1-11 stays ADVERSARY on that line).
- **GATE-FIRED-IGNORED** used only where a STANDING check fired correctly and its
  output was TOLERATED (a consumption failure). A gate that fired and was ACTED on
  is not this class, so chunk1-07 and chunk2-18 do not move.
- **fix_chain is FORWARD**: how many times the remedy FOR THIS ROW'S defect was
  itself later refuted. Both v1 chunks already used the forward reading, so the
  direction pin changed one row only - the one where v1 had no VALUE to record a
  fix that created a defect.
- **INTRODUCED** where the remedy did not merely fall short but CREATED a defect
  that did not exist before it.
- **INHERITED-SHARED**: zero rows. No fix in entries 173-191 arrived byte-identical
  from a sibling's shared file (the slots.py / winmutex.py shared surface sits far
  below this window).

---

id: chunk1-01
entry: 191
prevention: GATE-ABSENT
prevention_why: nothing graded the property "every registered unattended lane checks a HALT path before it spawns", and that gate is mechanical and was written in this very entry
discovery: SELF-AUDIT
origin_time: FRESH
origin_sub: NA
correct: YES
defect_corrected: YES
fix_chain: 0
chain_kind: NA
moved: none

---

id: chunk1-02
entry: 190
prevention: GATE-ABSENT
prevention_why: check_ci had arms, but every one stubbed the gh return, so none could see a defect that lived in the ARGUMENT handed to gh; the tie-breaker sends a check that cannot see the defect without being rewritten to GATE-ABSENT
discovery: RUN
origin_time: FRESH
origin_sub: NA
correct: YES
defect_corrected: YES
fix_chain: 0
chain_kind: NA
moved: none

---

id: chunk1-03
entry: 189
prevention: GATE-ABSENT
prevention_why: nothing graded whether an arm's colour depends on machine state; the mtime guard in the same file covered the run log only and could not have seen a HALT-path read without being rewritten
discovery: RUN
origin_time: INHERITED
origin_sub: BORN-WRONG
correct: YES
defect_corrected: YES
fix_chain: 0
chain_kind: NA
moved: none

---

id: chunk1-04
entry: 188
prevention: PROXY-MEASURE
prevention_why: the tracer was accurate and answered "did bytes move" when the question was "did state change", so a guard's REPAIR was indistinguishable from damage and the remedy was a second measure (hash before and after), not a gate
discovery: SIBLING
origin_time: FRESH
origin_sub: NA
correct: YES
defect_corrected: YES
fix_chain: 0
chain_kind: NA
moved: prevention ADVERSARY -> PROXY-MEASURE. v1 forced it to ADVERSARY and its own scorer flagged the score as wrong in both directions; entry 188 states the class in the pin's exact words ("THE ROOT CAUSE IS THE INSTRUMENT'S QUESTION, NOT ITS ACCURACY"). This is the specimen CHANGE 3 was written for.

---

id: chunk1-05
entry: 187
prevention: CONTRACT
prevention_why: no mechanical check in LW's tree can see a sibling's open item; the preventing thing is a declared precondition to read the sibling's own tracker entry before repairing it
discovery: SIBLING
origin_time: INHERITED
origin_sub: DECAYED
correct: YES
defect_corrected: YES
fix_chain: 0
chain_kind: NA
moved: none

---

id: chunk1-06
entry: 187
prevention: GATE-ABSENT
prevention_why: no check ever asked WHICH arms write a live surface; the shipped remedy is mechanical (session-scoped count guard plus discovery-based arms) and the third mutant proves it binds
discovery: RUN
origin_time: INHERITED
origin_sub: BORN-WRONG
correct: YES
defect_corrected: YES
fix_chain: 0
chain_kind: NA
moved: none

---

id: chunk1-07
entry: 187
prevention: GATE-EXISTING
prevention_why: wrong time and wrong tree - CS's test_docs_citations.py pins WRITER_WRITE_SURFACE at line 2089 and did fire, but as a post-edit suite result in a foreign tree, so it detected the break instead of preventing the write
discovery: RUN
origin_time: FRESH
origin_sub: NA
correct: YES
defect_corrected: YES
fix_chain: 0
chain_kind: NA
moved: none. GATE-FIRED-IGNORED was considered and REFUSED: v1.1 defines it as a consumption failure where the output was TOLERATED, and here the RED was acted on at once (blocks moved to the foot rather than the digest re-cut). The gate that fires, is acted on, and still fails to PREVENT remains homeless in v1.1 and is reported as such. fix_chain held at 0 - "reddened twice" does not resolve between two failed placements and two failing assertions in one run, so it is scored down per the no-guess-upward rule.

---

id: chunk1-08
entry: 186
prevention: GATE-ABSENT
prevention_why: the instrument had no non-vacuity control at all, so nothing graded whether each patched route actually sees a write; planting a specimen through every route is mechanical and is exactly what shipped
discovery: SELF-AUDIT
origin_time: INHERITED
origin_sub: BORN-WRONG
correct: YES
defect_corrected: YES
fix_chain: 1
chain_kind: SAME-ARTIFACT
moved: none. Re-checked against CHANGE 2: the pathlib-plus-control remedy stood, and what entry 188 refuted is the instrument's QUESTION, a defect that predates this fix rather than one the fix created, so INTRODUCED does not apply and SAME-ARTIFACT (excluded from the ratio) holds.

---

id: chunk1-09
entry: 186
prevention: PROXY-MEASURE
prevention_why: the byte-counting tracer was correct and answered the wrong question, and RUNNING it is what manufactured the false "Lanternlight is not clean" verdict; only a second measure of a different quantity (identity or hash of the record) reaches it
discovery: SIBLING
origin_time: FRESH
origin_sub: NA
correct: NO
defect_corrected: YES
fix_chain: 0
chain_kind: NA
moved: prevention ADVERSARY -> PROXY-MEASURE, same instrument and same class as chunk1-04. Scoring it ADVERSARY implied a code reader could have caught it; nothing in the code says whether a byte delta is a repair or damage.

---

id: chunk1-10
entry: 186
prevention: GATE-ABSENT
prevention_why: when the watched-root resolution was written nothing graded whether the tracer could see its own planted writes; the control that caught it was written in the same pass and fired on its first run
discovery: RUN
origin_time: FRESH
origin_sub: NA
correct: YES
defect_corrected: YES
fix_chain: 0
chain_kind: NA
moved: none. GATE-FIRED-IGNORED refused - the control was not a STANDING check (it was written in this pass) and its output was acted on immediately.

---

id: chunk1-11
entry: 186
prevention: ADVERSARY
prevention_why: the missing thing is a lens on the instrument - a zero with no self-check is an absence of evidence dressed as evidence of absence - and no gate or brief in the tree asked that
discovery: SIBLING
origin_time: FRESH
origin_sub: NA
correct: YES
defect_corrected: YES
fix_chain: 1
chain_kind: SELF
moved: none. PROXY-MEASURE was considered and REFUSED on v1.1's own wording: that class requires the instrument to be CORRECT, and this instrument was vacuous (all three routes false on a tracer that looked healthy). ADVERSARY survives here for the right reason rather than as a forced fit.

---

id: chunk1-12
entry: 186
prevention: GATE-ABSENT
prevention_why: a positives-only control is vacuous against a promote-everything classifier, and the grader for that is mechanical - a negative specimen outside every watched root, which is what shipped
discovery: SIBLING
origin_time: FRESH
origin_sub: NA
correct: YES
defect_corrected: YES
fix_chain: 0
chain_kind: NA
moved: none

---

id: chunk1-13
entry: 186
prevention: CONTRACT
prevention_why: no mechanical check reaches a credit claim; the preventing thing is a declared precondition to compare the sibling's own fix timestamp against the outbound note's before attributing the repair
discovery: RUN
origin_time: INHERITED
origin_sub: DECAYED
correct: YES
defect_corrected: YES
fix_chain: 0
chain_kind: NA
moved: none

---

id: chunk1-14
entry: 185
prevention: CONTRACT
prevention_why: a measurement-design precondition - run a no-treatment idle control before attributing any change to the treatment - reaches it, and it has since been codified as feedback-run-an-idle-control-before-attributing
discovery: RUN
origin_time: FRESH
origin_sub: NA
correct: YES
defect_corrected: YES
fix_chain: 2
chain_kind: SELF
moved: none. PROXY-MEASURE was the closest alternative (the before/after diff was accurate and answered "did these files change" rather than "did the suite change them"), and it was REFUSED because v1.1 reserves that class for where no contract reaches it; here a declared precondition does reach it and was in fact adopted as a standing rule. Both later refutations remain SELF - the remedy failed twice at the same question (is this hermeticity measurement valid), rather than creating a new defect.

---

id: chunk1-15
entry: 185
prevention: GATE-ABSENT
prevention_why: nothing graded whether the producing run completed; a pipeline that publishes an -x-truncated producer's numbers as a total is mechanically checkable at the moment the figure is cut
discovery: SELF-AUDIT
origin_time: INHERITED
origin_sub: BORN-WRONG
correct: YES
defect_corrected: YES
fix_chain: 1
chain_kind: SELF
moved: none

---

id: chunk1-16
entry: 185
prevention: GATE-ABSENT
prevention_why: no check asked whether a test's _ROOT patch actually redirects; the in-process write tracer that found it is mechanical and needs no judgment
discovery: RUN
origin_time: INHERITED
origin_sub: BORN-WRONG
correct: YES
defect_corrected: YES
fix_chain: 0
chain_kind: NA
moved: none

---

id: chunk1-17
entry: 185
prevention: GATE-ABSENT
prevention_why: same missing mechanical check as chunk1-16 - nothing graded whether a module constant bound at import can still reach a live surface under test
discovery: RUN
origin_time: FRESH
origin_sub: NA
correct: YES
defect_corrected: YES
fix_chain: 0
chain_kind: NA
moved: none

---

id: chunk1-18
entry: 184
prevention: GATE-ABSENT
prevention_why: at the moment the 13 arms were written no live-surface guard covered the run log; the autouse mtime guard that fixed it is mechanical and mutation-proven
discovery: RUN
origin_time: FRESH
origin_sub: NA
correct: YES
defect_corrected: YES
fix_chain: 1
chain_kind: SIBLING-SURFACE
moved: none. Re-checked against INTRODUCED: the mtime guard created nothing - it was correct and missed a sibling live surface (the HALT path, found at entry 189), which is SIBLING-SURFACE exactly as defined.

---

id: chunk1-19
entry: 184
prevention: CONTRACT
prevention_why: what counts as a distinguishable trace is a design judgment a machine cannot make unassisted; the preventing thing is the declared rule that an unattended lane owes a run record in the commit that arms it
discovery: SELF-AUDIT
origin_time: INHERITED
origin_sub: BORN-WRONG
correct: YES
defect_corrected: YES
fix_chain: 1
chain_kind: INTRODUCED
moved: fix_chain 0 -> 1 and chain_kind NA -> INTRODUCED. This is the one row the v1.1 changes actually move on the chain fields, and it moves because CHANGE 2 supplied a value v1 did not have, not because the direction flipped: the remedy for the observability gap (RUNLOG_PATH plus its wiring) CREATED a defect that did not exist before it - the first suite run after the log landed appended 13 records of invented cold starts, 1411 measured bytes, to the operator's live file. v1 had no way to record "the fix created a new defect" and scored the forward chain 0. Not double counting chunk1-18: that row scores its OWN remedy (the mtime guard, refuted at entry 189), a different remedy refuted a different time.

---

id: chunk1-20
entry: 183
prevention: GATE-ABSENT
prevention_why: nothing graded whether a module that spawns unattended agents carries a mid-flight stop; that is a greppable, judgment-free property and is precisely the gate written later at entry 191
discovery: SELF-AUDIT
origin_time: INHERITED
origin_sub: BORN-WRONG
correct: YES
defect_corrected: YES
fix_chain: 1
chain_kind: INTRODUCED
moved: chain_kind SAME-ARTIFACT -> INTRODUCED. The v1 scorer flagged this exact call as the single judgment moving the chunk's ratio and took the non-inflating reading only because v1 offered no third value. Under CHANGE 2 the facts resolve cleanly: the kill switch shipped at 183 gave main() a DEFAULT HALT read, and that is what made four previously-fine arms in tests/test_inbox_responder.py a function of the operator's real machine state at entry 189. The fix did not merely fall short, it created the defect. This moves the row INTO the reported ratio, where SAME-ARTIFACT had excluded it.

---

id: chunk1-21
entry: 183
prevention: ADVERSARY
prevention_why: it takes a reader with a lens to see that 60 passing arms behind classify() constrain a LIBRARY and not a bypassPermissions session that is merely TOLD the rules; no gate and no brief in the tree asked that
discovery: SELF-AUDIT
origin_time: FRESH
origin_sub: NA
correct: YES
defect_corrected: NO
fix_chain: 0
chain_kind: NA
moved: none. PROXY-MEASURE was weighed (60 green arms are a correct instrument answering the wrong question) and REFUSED: the remedy is real enforcement, not a second measure, and the finding came from a reader's lens rather than from running anything, which is the ADVERSARY signature.

---

id: chunk2-01
entry: 182
prevention: GATE-ABSENT
prevention_why: no arm ever parsed the emitted registration command - the property "the printed command parses in the shell it is printed for" was never graded, and the repair created that grader
discovery: OPERATOR
origin_time: INHERITED
origin_sub: BORN-WRONG
correct: YES
defect_corrected: YES
fix_chain: 0
chain_kind: NA
moved: none

---

id: chunk2-02
entry: 182
prevention: CONTRACT
prevention_why: no mechanical check reaches "was the box idle"; a declared precondition before the measurement would have
discovery: RUN
origin_time: FRESH
origin_sub: NA
correct: YES
defect_corrected: YES
fix_chain: 0
chain_kind: NA
moved: none

---

id: chunk2-03
entry: 181
prevention: GATE-ABSENT
prevention_why: cold-start behaviour (an absent state file is not an empty one) was never graded by any arm, and a mechanical arm for it needs no judgment
discovery: RUN
origin_time: FRESH
origin_sub: NA
correct: YES
defect_corrected: YES
fix_chain: 0
chain_kind: NA
moved: none

---

id: chunk2-04
entry: 181
prevention: GATE-EXISTING
prevention_why: vacuous - an A3 arm existed and could not fail, because two citations from the same sender were already refused by the count alone, so the rule read as tested when it was not
discovery: SELF-AUDIT
origin_time: FRESH
origin_sub: NA
correct: YES
defect_corrected: YES
fix_chain: 0
chain_kind: NA
moved: none. GATE-FIRED-IGNORED does not apply - this gate could not fire at all, which is v1's GATE-EXISTING/vacuous and stays there.

---

id: chunk2-05
entry: 181
prevention: GATE-ABSENT
prevention_why: the withdrawn-and-refiled path was never graded at all; the fix was a NEW arm, not a repaired one
discovery: SELF-AUDIT
origin_time: FRESH
origin_sub: NA
correct: YES
defect_corrected: YES
fix_chain: 0
chain_kind: NA
moved: none

---

id: chunk2-06
entry: 181
prevention: CONTRACT
prevention_why: a declared precondition that the two arms differ only in the manipulated variable would have caught it; no mechanical check reaches "did these arms see the same tree"
discovery: SELF-AUDIT
origin_time: FRESH
origin_sub: NA
correct: YES
defect_corrected: YES
fix_chain: 0
chain_kind: NA
moved: none

---

id: chunk2-07
entry: 180
prevention: CONTRACT
prevention_why: a "name the load-bearing statistic before accusing" precondition would have stopped the 179 flag pointing at a statistic nothing rested on
discovery: SELF-AUDIT
origin_time: INHERITED
origin_sub: BORN-WRONG
correct: YES
defect_corrected: YES
fix_chain: 0
chain_kind: NA
moved: none

---

id: chunk2-08
entry: 180
prevention: PROXY-MEASURE
prevention_why: the acceptance verdict is a correct instrument answering the wrong question - it counts RESIDUE, where the axis scoped_revert can lose on is art damage - and the named remedy is a SECOND instrument measuring a different quantity (a no-reference smear measure over the kept fill)
discovery: CODE-READ
origin_time: INHERITED
origin_sub: BORN-WRONG
correct: YES
defect_corrected: NO
fix_chain: 0
chain_kind: NA
moved: prevention GATE-EXISTING -> PROXY-MEASURE. The v1 scorer named this the chunk's closest PROXY specimen and scored GATE-EXISTING only because the proxy IS the gate, then asked the pin to pick one. v1.1 says rows forced into ADVERSARY or GATE-EXISTING are the likely movers, and the defining test decides it: the instrument is correct, running it produced the false verdict, and the remedy is a different quantity, not a repaired gate.

---

id: chunk2-09
entry: 180
prevention: CONTRACT
prevention_why: a precondition that any quoted performance figure names the artifact it is reproducible from; no mechanical check reaches a free-text docstring number
discovery: CODE-READ
origin_time: INHERITED
origin_sub: BORN-WRONG
correct: YES
defect_corrected: UNKNOWN
fix_chain: 0
chain_kind: NA
moved: none

---

id: chunk2-10
entry: 179
prevention: NA
prevention_why: EXCLUDED, not scored (pin exclusion 4, unchanged under CHANGE 6 - H1 was opened BY the selection-contamination probe whose stated purpose was to test it, and the clearing is that probe's intended output)
discovery: NA
origin_time: NA
origin_sub: NA
correct: NA
defect_corrected: NA
fix_chain: 0
chain_kind: NA
moved: none. CHANGE 6 narrows exclusion 4 to probe-opened hypotheses only, which is exactly this row, so the exclusion survives the narrowing.

---

id: chunk2-11
entry: 179
prevention: NA
prevention_why: EXCLUDED, not scored (pin exclusion 4, same probe, second accusation - H2 was retired on the probe's own evidence and no durable record was wrong)
discovery: NA
origin_time: NA
origin_sub: NA
correct: NA
defect_corrected: NA
fix_chain: 0
chain_kind: NA
moved: none. Re-checked against CHANGE 6: this was not an adopted approach later abandoned, it was a hypothesis the probe existed to test, so it stays excluded.

---

id: chunk2-12
entry: 179
prevention: PROXY-MEASURE
prevention_why: the audit sweep was correct (719 audits, msssim never bound) and answered "has this arm ever fired" when the question was "is it reachable and unique"; running it is what produced the decoration verdict, and only a second instrument - the degradation table over a real frame - reversed it
discovery: RUN
origin_time: FRESH
origin_sub: NA
correct: YES
defect_corrected: YES
fix_chain: 0
chain_kind: NA
moved: prevention ADVERSARY -> PROXY-MEASURE. The v1 scorer put it in ADVERSARY under protest, noting the truth was "a contract drove it" (the repo's own arm-nobody-has-seen-fail rule). v1.1 still has no value for a contract that CAUSES a defect, but PROXY-MEASURE is now the closest correct fit on the mechanism, and ADVERSARY read as the opposite of the truth. The contract-caused fact is reported as still unrecordable rather than dropped.

---

id: chunk2-13
entry: 179
prevention: GATE-ABSENT
prevention_why: no check ever asserted that a computed-and-stored metric has a consuming rule; dists has no entry in DEFAULT_G1_THRESHOLDS and never did
discovery: CODE-READ
origin_time: INHERITED
origin_sub: BORN-WRONG
correct: YES
defect_corrected: NO
fix_chain: 0
chain_kind: NA
moved: none

---

id: chunk2-14
entry: 179
prevention: CONTRACT
prevention_why: a precondition that a tuned constant declares its evaluation set (in-sample grid winner as against held-out) at the point it is written
discovery: CODE-READ
origin_time: INHERITED
origin_sub: BORN-WRONG
correct: UNCLEAR
defect_corrected: NO
fix_chain: 0
chain_kind: NA
moved: none

---

id: chunk2-15
entry: 178
prevention: GATE-ABSENT
prevention_why: recording is not asserting - nothing graded the recorded model_sha256, so the property was never checked, and the fix created the first check (config/model_pins.json plus assert_pinned)
discovery: CODE-READ
origin_time: INHERITED
origin_sub: BORN-WRONG
correct: YES
defect_corrected: YES
fix_chain: 0
chain_kind: NA
moved: none

---

id: chunk2-16
entry: 178
prevention: GATE-ABSENT
prevention_why: no prior guard existed for the tracked-but-ignored trap; drift_guard.check_tracked_but_ignored was written by this fix
discovery: RUN
origin_time: INHERITED
origin_sub: DECAYED
correct: YES
defect_corrected: YES
fix_chain: 1
chain_kind: INTRODUCED
moved: chain_kind SELF -> INTRODUCED. The first remedy was the build agent's EXEMPTION, and entry 178 names what it left behind in its own words - "a standing hole" retired to an empty tuple. That is not an incomplete fix, it is a fix that created a new defect (a permanent blind spot in the guard), which is precisely the case CHANGE 2 says v1 was forcing into SELF. fix_chain stays 1 and the row stays inside the ratio, so this move changes the kind and not the count.

---

id: chunk2-17
entry: 178
prevention: CONTRACT
prevention_why: the repo's own declared root-cause-first rule would have refused an exemption that tolerates the bug; no mechanical check can tell a legitimate exemption from a hole
discovery: CODE-READ
origin_time: FRESH
origin_sub: NA
correct: YES
defect_corrected: YES
fix_chain: 0
chain_kind: NA
moved: none. This row IS the chain link scored at chunk2-16; under the forward pin it scores its own remedy only, which stood, so 0.

---

id: chunk2-18
entry: 178
prevention: CONTRACT
prevention_why: the repo's declared "grep and cite file:line for every method and field a probe will use" rule reaches both bugs (r.message did not exist), and the suite is what FOUND them rather than a check that failed to fire
discovery: RUN
origin_time: FRESH
origin_sub: NA
correct: YES
defect_corrected: YES
fix_chain: 0
chain_kind: NA
moved: none. GATE-FIRED-IGNORED was considered and REFUSED: the gate fired and its output was acted on in the same slice, so there is no consumption failure to count.

---

id: chunk2-19
entry: 178
prevention: CONTRACT
prevention_why: the standing verification rule to re-measure rather than carry a number forward; no mechanical check reaches a number pasted into a hand-off
discovery: RUN
origin_time: INHERITED
origin_sub: DECAYED
correct: YES
defect_corrected: YES
fix_chain: 0
chain_kind: NA
moved: none

---

id: chunk2-20
entry: 178
prevention: GATE-ABSENT
prevention_why: nothing compares pytest's collected count against its run count, and a mechanical arm doing so needs no judgment
discovery: RUN
origin_time: FRESH
origin_sub: NA
correct: UNCLEAR
defect_corrected: NO
fix_chain: 0
chain_kind: NA
moved: none. GATE-FIRED-IGNORED was weighed - the off-by-one was observed and left alone - and REFUSED because no standing CHECK fired; the numbers were an incidental output nobody had wired to a verdict, which is the absence case.

---

id: chunk2-21
entry: 177
prevention: CONTRACT
prevention_why: the standing rule to re-probe external state before asserting it; no gate in this tree can see a GitHub repo setting
discovery: RUN
origin_time: INHERITED
origin_sub: DECAYED
correct: YES
defect_corrected: YES
fix_chain: 0
chain_kind: NA
moved: none

---

id: chunk2-22
entry: 175
prevention: GATE-FIRED-IGNORED
prevention_why: the done_gate check fired correctly and named the failing test, and the caller's tail -6 destroyed that output before any reader could act on it - a consumption failure, not a missing or vacuous gate
discovery: RUN
origin_time: FRESH
origin_sub: NA
correct: YES
defect_corrected: YES
fix_chain: 0
chain_kind: NA
moved: prevention GATE-EXISTING -> GATE-FIRED-IGNORED. The v1 scorer named this row as the pin's own unhandled class in exactly those terms ("THE GATE THAT FIRED AND NOBODY COULD ACT") and said absorbing it into GATE-EXISTING loses that the failure was in the CONSUMER. CHANGE 3 supplies the value and this is the specimen it fits.

---

id: chunk2-23
entry: 174
prevention: CONTRACT
prevention_why: a precondition that a hand-off cite file:line for every artifact it names would have made the missing guard visible when the brief was written
discovery: CODE-READ
origin_time: INHERITED
origin_sub: BORN-WRONG
correct: YES
defect_corrected: YES
fix_chain: 0
chain_kind: NA
moved: none

---

id: chunk2-24
entry: 174
prevention: GATE-ABSENT
prevention_why: nothing was looking - git grep over tests/, tools/ and .githooks/ found no email guard anywhere, and drift_guard / done_gate / precommit_gate contained no email check at all
discovery: CODE-READ
origin_time: INHERITED
origin_sub: DECAYED
correct: YES
defect_corrected: YES
fix_chain: 0
chain_kind: NA
moved: none. Explicitly re-checked under CHANGE 1: this row is itself the refutation of LEDGER 172's purge, which is the BACKWARD reading v1.1 forbids. Its own remedy (the split scanner plus the sha-pinned values) was not refuted, so it stays 0 forward and the chain is counted once, at its root outside this row set.

---

id: chunk2-25
entry: 174
prevention: GATE-ABSENT
prevention_why: the tie-breaker - test_no_account_paths.py existed but parses the account segment out of a CONTIGUOUS regex match and could not have seen a split value without being rewritten; the fix was a new tool, not a repaired arm
discovery: RUN
origin_time: INHERITED
origin_sub: BORN-WRONG
correct: YES
defect_corrected: YES
fix_chain: 1
chain_kind: SELF
moved: none. INTRODUCED was checked and does not apply - the split scanner created nothing; it fell short at the same defect (a value assembled across a separator), which is SELF.

---

id: chunk2-26
entry: 174
prevention: ADVERSARY
prevention_why: two halves separated by unrelated text never become adjacent under normalisation; no gate and no contract reaches it, the answer is the CHOICE OF FRAGMENT and that needs a reader with a lens
discovery: SIBLING
origin_time: FRESH
origin_sub: NA
correct: YES
defect_corrected: NO
fix_chain: 0
chain_kind: NA
moved: none. PROXY-MEASURE refused: the scanner's question was right and its COVERAGE was short, which is not the correct-instrument-wrong-question class.

---

id: chunk2-27
entry: 174
prevention: CONTRACT
prevention_why: a declared "fixtures carry fake values, never the real secret" rule reaches it; no mechanical check can distinguish an intentional fixture from a leak without being told which values are forbidden
discovery: RUN
origin_time: INHERITED
origin_sub: BORN-WRONG
correct: YES
defect_corrected: YES
fix_chain: 0
chain_kind: NA
moved: none

---

id: chunk2-28
entry: 173
prevention: CONTRACT
prevention_why: a precondition to count against the consuming code's own definition (lw_recover's regex) before reporting a count, rather than after being challenged
discovery: SELF-AUDIT
origin_time: FRESH
origin_sub: NA
correct: YES
defect_corrected: YES
fix_chain: 1
chain_kind: SELF
moved: none. INTRODUCED was weighed (the recount to 10 was wrong where 9 had been right) and REFUSED: the remedy got the SAME question wrong a second time rather than creating a defect elsewhere, and it was corrected back inside the session.

---

id: chunk2-29
entry: 173
prevention: GATE-ABSENT
prevention_why: no arm graded the crop-instruction round trip into the manifest, so list(crop_sides) yielding dict KEYS was never checkable
discovery: CODE-READ
origin_time: FRESH
origin_sub: NA
correct: YES
defect_corrected: YES
fix_chain: 0
chain_kind: NA
moved: none

---

id: chunk2-30
entry: 173
prevention: GATE-EXISTING
prevention_why: wrong scope - the near-dup measure the pipeline already has is perceptual (phash/dhash, which put these two 26/27 apart), and the duplicate verdict was reached on a shared DeviantArt deviation id, which a multi-image upload shares by design
discovery: RUN
origin_time: FRESH
origin_sub: NA
correct: YES
defect_corrected: YES
fix_chain: 0
chain_kind: NA
moved: none

---

## Counts for this 51-row set (machine-recountable from the blocks above)

rows in: 51. rows out: 51. excluded rows carried through unscored: 2 (chunk2-10,
chunk2-11). scored events: 49.

**prevention moved on 5 rows:** chunk1-04 (ADVERSARY -> PROXY-MEASURE), chunk1-09
(ADVERSARY -> PROXY-MEASURE), chunk2-08 (GATE-EXISTING -> PROXY-MEASURE), chunk2-12
(ADVERSARY -> PROXY-MEASURE), chunk2-22 (GATE-EXISTING -> GATE-FIRED-IGNORED).

prevention distribution over the 49 scored rows:
- GATE-ABSENT 22: chunk1-01, 02, 03, 06, 08, 10, 12, 15, 16, 17, 18, 20; chunk2-01,
  03, 05, 13, 15, 16, 20, 24, 25, 29
- CONTRACT 16: chunk1-05, 13, 14, 19; chunk2-02, 06, 07, 09, 14, 17, 18, 19, 21,
  23, 27, 28
- PROXY-MEASURE 4: chunk1-04, 09; chunk2-08, 12
- GATE-EXISTING 3: chunk1-07; chunk2-04, 30
- ADVERSARY 3: chunk1-11, 21; chunk2-26
- GATE-FIRED-IGNORED 1: chunk2-22

**fix_chain moved on 1 row:** chunk1-19 (0 -> 1). Both v1 chunks had already read the
integer forward, so CHANGE 1 confirmed the existing direction rather than reversing
it; the single move comes from CHANGE 2 supplying INTRODUCED, a value v1 lacked, for
a remedy that created a defect.

fix_chain distribution: 0 on 39 scored rows; 1 on 9 (chunk1-08, 11, 15, 18, 19, 20;
chunk2-16, 25, 28); 2 on 1 (chunk1-14).

**chain_kind moved on 3 rows:** chunk1-19 (NA -> INTRODUCED), chunk1-20
(SAME-ARTIFACT -> INTRODUCED), chunk2-16 (SELF -> INTRODUCED).

chain_kind distribution: NA 39; SELF 5 (chunk1-11, 14, 15; chunk2-25, 28);
INTRODUCED 3 (chunk1-19, 20; chunk2-16); SIBLING-SURFACE 1 (chunk1-18);
SAME-ARTIFACT 1 (chunk1-08); INHERITED-SHARED 0.

**Fix-of-a-fix over these 51 rows, old against new.**
- Rows with fix_chain >= 1: OLD 9, NEW 10 (chunk1-19 added).
- Rows counted in the pin's ratio (SELF + INTRODUCED + SIBLING-SURFACE +
  INHERITED-SHARED; SAME-ARTIFACT excluded): OLD 7 of 49 = 14.3 pct, NEW 9 of 49 =
  18.4 pct. Two of the three added rows are chain_kind moves into the ratio
  (chunk1-20 out of the excluded SAME-ARTIFACT bucket, chunk1-19 newly chained);
  chunk2-16's move is inside the ratio and changes the kind only.

## Limits of this pass, per the pin's reporting requirement

1. Different agents scored these rows than extracted them, so the
   producer-grades-own-work defect does not apply to this re-score.
2. The per-event rows were PERSISTED, so this re-score cost one read pass and not a
   fresh extraction.
3. The count remains a FLOOR - the corpus is authored by the party being measured.
4. Still unrecordable in v1.1, found again here: (a) a CONTRACT that CAUSED the
   defect (chunk2-12, scored PROXY-MEASURE on mechanism, which loses the causal
   fact); (b) the gate that FIRED, was ACTED on, and still did not PREVENT
   (chunk1-07) - GATE-FIRED-IGNORED requires the output to be tolerated, so this
   case is still homed in GATE-EXISTING against that field's own wording.

---

# Part B re-score against REFUTATION_TAXONOMY_PIN_v1_1 - 2026-09-12

READ-ONLY pass. No tracked file was edited. Rows in: 75 (chunk3-01..47, chunk4-01..28).
Rows out: 75. None added, dropped, merged or renumbered.

## Declared conventions for the three re-derived fields

- `fix_chain` is the PINNED FORWARD integer: how many times the REMEDY SHIPPED FOR
  THIS EVENT was itself subsequently refuted. An event is NOT scored >= 1 because it
  is somebody's second attempt. Counting rule applied, stated so a merger can check
  it: a link is counted only where a later recorded row's refuted CLAIM names this
  event's own remedy (same slice allowed only when the claim explicitly names the
  fix shipped in that slice). Deeper links belonging to a successor remedy are left
  on the successor's row rather than carried up the lineage, so the ancestor is not
  inflated. Evidence for forward links was taken from the whole census file
  (chunks 1 and 2 carry entries 191-173, which is FORWARD of every row scored here).
- `chain_kind` characterises the link: SELF (remedy incomplete for the SAME defect),
  INTRODUCED (remedy CREATED a new defect), SIBLING-SURFACE (remedy correct, missed
  a surface sharing the root cause), INHERITED-SHARED (remedy arrived byte-identical
  from a sibling's shared file), SAME-ARTIFACT (a later DIFFERENT defect in the same
  artifact), NA (fix_chain 0).
- `prevention` re-derived against the six-value list. Vacuity stays GATE-EXISTING.
  GATE-FIRED-IGNORED is used only where a standing check DID fire correctly and its
  output was TOLERATED. PROXY-MEASURE is used only where the instrument was correct,
  no code-reading adversary reaches it, and RUNNING it is what made the false verdict.

---

id: chunk3-01
entry: 172
prevention: GATE-ABSENT
prevention_why: nothing ever graded the address across commit METADATA, only across worktree content
discovery: SELF-AUDIT
origin_time: FRESH
origin_sub: NA
correct: YES
defect_corrected: YES
fix_chain: 2
chain_kind: INTRODUCED
moved: fix_chain 1 -> 2 and chain_kind SELF -> INTRODUCED. Forward: the remedy (filter-repo rewrite + force-push) was refuted twice - by chunk3-02 at 172 (GitHub-side unreachable objects still answer 200) and by chunk2-24 at 174 (the address tracked CONTIGUOUS in five places, every site an artifact written to RECORD the purge, i.e. created by the fix).

id: chunk3-02
entry: 172
prevention: CONTRACT
prevention_why: CLAUDE.md already recorded that a force-push does not purge GitHub-side unreachable objects
discovery: RUN
origin_time: FRESH
origin_sub: NA
correct: YES
defect_corrected: NO
fix_chain: 0
chain_kind: NA
moved: fix_chain 1 -> 0, chain_kind SELF -> NA. The old 1 was the backward reading. Forward: no remedy was ever shipped for this event (delete-and-recreate or a Support request was never done), so there is no remedy that could be refuted.

id: chunk3-03
entry: 171
prevention: CONTRACT
prevention_why: the inbound note asserted a mechanism without declaring it repo-specific; a brief requiring an inbound claim to name its scope stops the adoption
discovery: CODE-READ
origin_time: INHERITED
origin_sub: BORN-WRONG
correct: YES
defect_corrected: YES
fix_chain: 2
chain_kind: SELF
moved: fix_chain 0 -> 2 and chain_kind NA -> SELF. Forward: the remedy was LW's own push verification (done_gate, cb19250), and it was refuted twice - chunk3-07 at 171 ("the six-arm mutation result proved the done_gate arms bind" - two mutants survived) and chunk2-22 at 175 (done_gate's RED discarded the child's failing-test name).

id: chunk3-04
entry: 171
prevention: GATE-EXISTING
prevention_why: wrong time - the suite existed and ran, but /done ran it BEFORE the living-doc edits, so it graded a tree that was never pushed
discovery: CODE-READ
origin_time: INHERITED
origin_sub: BORN-WRONG
correct: YES
defect_corrected: YES
fix_chain: 2
chain_kind: SELF
moved: fix_chain 0 -> 2 and chain_kind NA -> SELF. Same remedy as chunk3-03 (the reordered ritual plus done_gate), refuted at 171 by the surviving mutants and at 175 by the gate's unusable RED report.

id: chunk3-05
entry: 171
prevention: ADVERSARY
prevention_why: needs a reader who knows `git diff HEAD` is blind to untracked files; no gate or template reaches a defect written INTO the acceptance line
discovery: CODE-READ
origin_time: INHERITED
origin_sub: BORN-WRONG
correct: YES
defect_corrected: YES
fix_chain: 0
chain_kind: NA
moved: none. Forward reading confirms 0 - the implementer's replacement cleanliness check is named nowhere later as refuted.

id: chunk3-06
entry: 171
prevention: ADVERSARY
prevention_why: needs a reader who knows a remote-tracking ref is a local cache that a failed push leaves stale
discovery: CODE-READ
origin_time: INHERITED
origin_sub: BORN-WRONG
correct: YES
defect_corrected: YES
fix_chain: 0
chain_kind: NA
moved: none. Forward reading confirms 0 - the replacement sha read is never refuted in the record.

id: chunk3-07
entry: 171
prevention: CONTRACT
prevention_why: the mutation ritual is a declared precondition an agent follows, not a tree-resident gate, and it is what caught the two survivors
discovery: RUN
origin_time: FRESH
origin_sub: NA
correct: YES
defect_corrected: YES
fix_chain: 0
chain_kind: NA
moved: fix_chain 1 -> 0, chain_kind SELF -> NA. The old 1 was backward (this event refutes a prior proof). Forward: the added arms that killed the two survivors are never themselves refuted later.

id: chunk3-08
entry: 171
prevention: GATE-ABSENT
prevention_why: no mechanical check graded that a cited "section N" still resolves in the target document
discovery: SELF-AUDIT
origin_time: INHERITED
origin_sub: DECAYED
correct: YES
defect_corrected: YES
fix_chain: 0
chain_kind: NA
moved: fix_chain 1 -> 0, chain_kind SAME-ARTIFACT -> NA. Backward before; forward, the repin of the hand-off guard is never refuted later in the record.

id: chunk3-09
entry: 170
prevention: GATE-ABSENT
prevention_why: the concurrency-ceiling property was never graded on either side of the shared file; the seven arms that now grade it had to be written
discovery: CODE-READ
origin_time: INHERITED
origin_sub: BORN-WRONG
correct: YES
defect_corrected: YES
fix_chain: 0
chain_kind: NA
moved: none. Forward: amendment B plus its arms, jointly accepted by RC, is not refuted anywhere later in the window.

id: chunk3-10
entry: 170
prevention: GATE-EXISTING
prevention_why: wrong scope - `drift_guard.check_claude_path_keys` grades the property, but the "fixed machine-wide" claim was recorded without running it over every checkout
discovery: RUN
origin_time: INHERITED
origin_sub: BORN-WRONG
correct: YES
defect_corrected: NO
fix_chain: 0
chain_kind: NA
moved: fix_chain 1 -> 0, chain_kind SIBLING-SURFACE -> NA. The old 1 pointed BACKWARD at the 2026-09-05 fix. Forward: LW surfaced and did not edit, so no remedy exists here to be refuted.

id: chunk3-11
entry: 169
prevention: GATE-EXISTING
prevention_why: wrong scope - the audit scan ran over the paths already known to be at risk, so it returned true and useless
discovery: SELF-AUDIT
origin_time: INHERITED
origin_sub: BORN-WRONG
correct: YES
defect_corrected: UNKNOWN
fix_chain: 0
chain_kind: NA
moved: fix_chain 1 -> 0, chain_kind SIBLING-SURFACE -> NA. Backward before (RC's earlier rewrite missed surfaces). Forward: the remedy is RC's wider audit plus the operator's decline, and nothing later refutes it.

id: chunk3-12
entry: 169
prevention: CONTRACT
prevention_why: the anchor-your-match / print-a-sample-beside-every-count rule was already recorded and was not applied to the first pass
discovery: SELF-AUDIT
origin_time: FRESH
origin_sub: NA
correct: YES
defect_corrected: YES
fix_chain: 0
chain_kind: NA
moved: none. Forward reading confirms 0 - the anchored re-count (3 hits) is never refuted later.

id: chunk3-13
entry: 169
prevention: GATE-EXISTING
prevention_why: wrong scope - `.githooks/commit-msg` grades exactly this but is per-repo, and the post-flip commits landed in a tree where it was not in force
discovery: SELF-AUDIT
origin_time: INHERITED
origin_sub: DECAYED
correct: YES
defect_corrected: NO
fix_chain: 0
chain_kind: NA
moved: fix_chain 1 -> 0, chain_kind SIBLING-SURFACE -> NA. Backward before. Forward: measured and reported in RC's tree with no correction recorded here, so there is no remedy to refute.

id: chunk3-14
entry: 169
prevention: CONTRACT
prevention_why: only a declared precondition (a claim that travelled needs a correction that travels the same distance) reaches this; no gate can
discovery: SELF-AUDIT
origin_time: INHERITED
origin_sub: DECAYED
correct: YES
defect_corrected: YES
fix_chain: 0
chain_kind: NA
moved: none. Forward: the 18:20 correction note is never itself refuted.

id: chunk3-15
entry: 168
prevention: ADVERSARY
prevention_why: the withdrawal property had to be NAMED before any arm could grade it, and RC supplied the lens; `entries - seen` cannot fail on a note that is gone
discovery: SIBLING
origin_time: INHERITED
origin_sub: BORN-WRONG
correct: YES
defect_corrected: YES
fix_chain: 1
chain_kind: INTRODUCED
moved: chain_kind SAME-ARTIFACT -> INTRODUCED (fix_chain stays 1 but for the opposite reason). Forward: the withdrawal fix shipped for THIS event was refuted in the same slice by chunk3-16, which names it explicitly, and the failure is a defect the fix CREATED - a withdrawal that re-derived itself forever and could never be cleared, plus a docstring asserting the opposite.

id: chunk3-16
entry: 168
prevention: GATE-ABSENT
prevention_why: the property "a reported withdrawal can be CLEARED" was never graded; an arm proving a thing APPEARS is not the arm proving it can GO AWAY
discovery: RUN
origin_time: FRESH
origin_sub: NA
correct: YES
defect_corrected: YES
fix_chain: 0
chain_kind: NA
moved: fix_chain 1 -> 0, chain_kind SELF -> NA. The old 1 was backward (this row IS the refutation of the same-slice fix, now carried forward on chunk3-15). The ack-prune correction broadcast to four repos is not itself refuted later.

id: chunk3-17
entry: 168
prevention: GATE-EXISTING
prevention_why: vacuous - the guard asserted every declared hook script EXISTS via `ROOT.rglob`, and a stale worktree only ADDS files
discovery: SIBLING
origin_time: INHERITED
origin_sub: BORN-WRONG
correct: YES
defect_corrected: YES
fix_chain: 0
chain_kind: NA
moved: fix_chain 1 -> 0, chain_kind SELF -> NA. Backward before (it refuted entry 161's guard, a link now carried forward on chunk3-45). Forward: sourcing basenames from `git ls-files` is never refuted later.

id: chunk3-18
entry: 168
prevention: CONTRACT
prevention_why: the mutation ritual is the only thing that grades whether an arm binds, and it is what exposed the size-key and mtime-key mutants
discovery: RUN
origin_time: INHERITED
origin_sub: BORN-WRONG
correct: YES
defect_corrected: YES
fix_chain: 0
chain_kind: NA
moved: fix_chain 1 -> 0, chain_kind SELF -> NA. Backward before (it refuted the 165 digest, now carried forward on chunk3-32). The hardened digest is not refuted later.

id: chunk3-19
entry: 168
prevention: ADVERSARY
prevention_why: the scarce thing is knowing `is_symlink()` is False for a Windows junction; at authoring time no gate or contract reached it
discovery: SIBLING
origin_time: INHERITED
origin_sub: BORN-WRONG
correct: YES
defect_corrected: YES
fix_chain: 1
chain_kind: INTRODUCED
moved: chain_kind SELF -> INTRODUCED (fix_chain stays 1, forward this time). The junction fix shipped for this event was refuted by chunk3-23, whose claim names it verbatim ("the junction arm added in this slice is green"), and the arm CREATED a new defect - unconditional `creationflags`, a Linux ValueError.

id: chunk3-20
entry: 168
prevention: GATE-ABSENT
prevention_why: an arm for an unclassifiable entry was never written; `if is_dir / elif is_file` with no `else` needs only a fixture
discovery: SIBLING
origin_time: INHERITED
origin_sub: BORN-WRONG
correct: YES
defect_corrected: YES
fix_chain: 0
chain_kind: NA
moved: fix_chain 1 -> 0, chain_kind SELF -> NA. Backward before. Forward: the added `else` branch is never refuted later.

id: chunk3-21
entry: 168
prevention: GATE-ABSENT
prevention_why: hermeticity was never mechanically graded; a check that no test writes under ops/runtime is writable with no human judgment
discovery: RUN
origin_time: INHERITED
origin_sub: BORN-WRONG
correct: YES
defect_corrected: YES
fix_chain: 1
chain_kind: SELF
moved: chain_kind SIBLING-SURFACE -> SELF (fix_chain stays 1, now forward). The hermeticity remedy shipped here was refuted at entry 185 by chunk1-16 - `lw_facts._INBOX/_SEEN/_REPORTED` bind at IMPORT, so an arm patching `_ROOT` kept the live paths and the same defect re-entered through the suite.

id: chunk3-22
entry: 168
prevention: CONTRACT
prevention_why: the anchor-your-match rule was already recorded in this tree and was not applied to a DESTRUCTIVE cleanup script
discovery: SELF-AUDIT
origin_time: FRESH
origin_sub: NA
correct: YES
defect_corrected: YES
fix_chain: 0
chain_kind: NA
moved: fix_chain 1 -> 0, chain_kind SELF -> NA. The old 1 was backward (this row IS the over-purge of a recovery pass). Forward: the restore of `slots.py.proposed-3repo` is never refuted later.

id: chunk3-23
entry: 168
prevention: CONTRACT
prevention_why: the mirror-image trap was ALREADY recorded in tests/test_tracked_settings_is_safe.py (guard on os.name BEFORE the Windows-only call)
discovery: CI
origin_time: FRESH
origin_sub: NA
correct: YES
defect_corrected: YES
fix_chain: 0
chain_kind: NA
moved: fix_chain 1 -> 0, chain_kind SAME-ARTIFACT -> NA. Backward before (the link is now carried forward on chunk3-19). The os.name guard added here is not refuted later.

id: chunk3-24
entry: 167
prevention: ADVERSARY
prevention_why: an inverted rationale paragraph is prose; no gate and no template grades whether an argument is backwards, and it read as reviewed because it was CREDITED
discovery: SIBLING
origin_time: INHERITED
origin_sub: BORN-WRONG
correct: YES
defect_corrected: YES
fix_chain: 0
chain_kind: NA
moved: none. Forward: deleting the comment outright is never refuted later.

id: chunk3-25
entry: 167
prevention: CONTRACT
prevention_why: a declared precondition (change the key, then update or DELETE the rationale beside it) reaches this; no check grades whether a comment still describes its code
discovery: CODE-READ
origin_time: INHERITED
origin_sub: DECAYED
correct: YES
defect_corrected: YES
fix_chain: 0
chain_kind: NA
moved: fix_chain 1 -> 0, chain_kind SELF -> NA. Backward before (the stale comment was created by the 271a4f7 key change, a link now carried forward on chunk3-31). The deletion is never refuted later.

id: chunk3-26
entry: 167
prevention: CONTRACT
prevention_why: LW's standing arm-must-be-able-to-go-red rule reaches this; an empty report passes both of LL's halves
discovery: CODE-READ
origin_time: INHERITED
origin_sub: BORN-WRONG
correct: YES
defect_corrected: YES
fix_chain: 0
chain_kind: NA
moved: none. Forward: LW's non-vacuous implementation of the property is never refuted later.

id: chunk3-27
entry: 167
prevention: GATE-ABSENT
prevention_why: no standing check graded that the hook interpreter RESOLVES and EXECUTES; a one-time manual check leaves no arm behind
discovery: SIBLING
origin_time: INHERITED
origin_sub: BORN-WRONG
correct: YES
defect_corrected: YES
fix_chain: 0
chain_kind: NA
moved: none. Forward reading confirms 0 - the five arms added here are never refuted later.

id: chunk3-28
entry: 167
prevention: GATE-ABSENT
prevention_why: nothing graded an outgoing note's stamp against real wall clock; the check is mechanical and was never written
discovery: SELF-AUDIT
origin_time: INHERITED
origin_sub: BORN-WRONG
correct: YES
defect_corrected: NO
fix_chain: 0
chain_kind: NA
moved: none. The census's uncertainty was about a BACKWARD prior skew fix; under the forward reading that is irrelevant, and no remedy for this event (the two skewed notes were never restamped) exists to be refuted.

id: chunk3-29
entry: 166
prevention: GATE-ABSENT
prevention_why: the account-path property was never graded mechanically; a detector parsing the account SEGMENT over both separators is writable with no judgment
discovery: SELF-AUDIT
origin_time: INHERITED
origin_sub: BORN-WRONG
correct: YES
defect_corrected: YES
fix_chain: 1
chain_kind: SELF
moved: fix_chain 0 -> 1 and chain_kind NA -> SELF. Forward: the remedy (the re-measured 68-file corpus plus tests/test_no_account_paths.py) was refuted at entry 174 by chunk2-25 - the detector parses the account segment out of a CONTIGUOUS match, so three planted split fixtures walk straight through it; incomplete for the same defect.

id: chunk3-30
entry: 166
prevention: GATE-EXISTING
prevention_why: not a miss - the guard DID fire on the first full-suite run and the hit was ACTED ON, which the pin still has no value for
discovery: RUN
origin_time: FRESH
origin_sub: NA
correct: YES
defect_corrected: YES
fix_chain: 2
chain_kind: INTRODUCED
moved: fix_chain 1 -> 2 and chain_kind SELF -> INTRODUCED. Forward: the sweep-plus-guard remedy was refuted twice at entry 174 - chunk2-25 (split-value blindness) and chunk2-27, where the guard's OWN planted fixtures turned out to be the last tracked copy of the real account, a defect the fix created. Prevention held at GATE-EXISTING: this is a fired-and-ACTED-ON gate, which is not GATE-FIRED-IGNORED (that value requires the output to be tolerated).

id: chunk3-31
entry: 165
prevention: ADVERSARY
prevention_why: the blindness of a name key to an IN-PLACE correction had to be named before it could be graded, and RC supplied the lens
discovery: SIBLING
origin_time: INHERITED
origin_sub: BORN-WRONG
correct: YES
defect_corrected: YES
fix_chain: 1
chain_kind: INTRODUCED
moved: chain_kind SELF -> INTRODUCED (fix_chain stays 1, now forward). The remedy was the content key landed in `271a4f7`; it was refuted at entry 167 by chunk3-25, and the defect - a rationale left describing a key the module no longer used - was CREATED by that fix.

id: chunk3-32
entry: 165
prevention: ADVERSARY
prevention_why: "a check whose evidence is supplied by the thing being checked is not a check" is the lens CS had to NAME; no gate or contract carried it beforehand
discovery: SIBLING
origin_time: INHERITED
origin_sub: BORN-WRONG
correct: YES
defect_corrected: YES
fix_chain: 1
chain_kind: SELF
moved: none in value, but the basis is now forward: the receiver-side digest shipped as the remedy here is refuted at entry 168 by chunk3-18, which names it ("the receiver-side payload digest, shipped in 165"), and it was incomplete for the same defect - the PAYLOAD leg stayed green against a size key and an mtime key.

id: chunk3-33
entry: 165
prevention: ADVERSARY
prevention_why: "SessionStart fires ONCE" is a lifecycle property nobody had stated; RC's five-property list is what turned it into something gradable
discovery: SIBLING
origin_time: INHERITED
origin_sub: BORN-WRONG
correct: YES
defect_corrected: YES
fix_chain: 0
chain_kind: NA
moved: fix_chain 1 -> 0, chain_kind SELF -> NA. The old 1 pointed BACKWARD at entry 159's watcher. Forward: the mid-session delivery fix is not named as refuted in any later row.

id: chunk3-34
entry: 165
prevention: GATE-EXISTING
prevention_why: vacuous - entry 161's guard asserted the hook wiring is PRESENT, and an EMPTY hooks array satisfies presence
discovery: CODE-READ
origin_time: INHERITED
origin_sub: BORN-WRONG
correct: YES
defect_corrected: YES
fix_chain: 0
chain_kind: NA
moved: fix_chain 1 -> 0, chain_kind SELF -> NA. Backward before (it refuted entry 161's guard, a link now carried forward on chunk3-45). The non-empty assertion added here is never refuted later.

id: chunk3-35
entry: 165
prevention: GATE-ABSENT
prevention_why: nothing exercised the ported detector against PROSE describing itself; that arm is mechanically writable and did not exist
discovery: CI
origin_time: INHERITED
origin_sub: BORN-WRONG
correct: YES
defect_corrected: YES
fix_chain: 0
chain_kind: NA
moved: fix_chain 1 -> 0, chain_kind SIBLING-SURFACE -> NA. Backward before (it was the third surface of entry 164's fix, a link now carried forward on chunk3-37). The markdown-parsing fix is never refuted later.

id: chunk3-36
entry: 164
prevention: GATE-ABSENT
prevention_why: no arm graded that the inbox glob reaches a SUBDIRECTORY; a fixture with a payload directory needs no lens
discovery: SIBLING
origin_time: INHERITED
origin_sub: BORN-WRONG
correct: YES
defect_corrected: YES
fix_chain: 0
chain_kind: NA
moved: fix_chain 1 -> 0, chain_kind SELF -> NA. The old 1 pointed BACKWARD at entry 159's watcher (carried forward now on chunk4-01). No later row names the recursive-glob fix as refuted.

id: chunk3-37
entry: 164
prevention: ADVERSARY
prevention_why: needs a reader who knows a bare `$name` in PowerShell is a variable and never a literal; a detector's false-positive profile on a NEW corpus is not gateable by the sending tree
discovery: RUN
origin_time: INHERITED
origin_sub: BORN-WRONG
correct: YES
defect_corrected: YES
fix_chain: 1
chain_kind: SIBLING-SURFACE
moved: fix_chain 0 -> 1 and chain_kind NA -> SIBLING-SURFACE. Forward: the remedy (fixing two false positives in the ported secret guard rather than exempting them) was refuted at entry 165 by chunk3-35, which names "the ported secret guard (entry 164)" and is a third surface of the same root cause - the guard reading a doc's markdown as part of the value.

id: chunk3-38
entry: 164
prevention: CONTRACT
prevention_why: a declared precondition (a digest pin records the commit it was taken at, and a rotation notifies the holders of the pin) reaches this
discovery: CODE-READ
origin_time: INHERITED
origin_sub: DECAYED
correct: YES
defect_corrected: UNKNOWN
fix_chain: 0
chain_kind: NA
moved: none. Forward: LW's diagnosis and its advice to re-pin at 0b112a4f are never refuted; whether CS re-pinned is outside the window, which is a defect_corrected question, not a fix_chain one.

id: chunk3-39
entry: 164
prevention: GATE-ABSENT
prevention_why: RC's pre-public audit graded credentials, gists, scraped content and pack size and never graded account paths at all
discovery: SIBLING
origin_time: INHERITED
origin_sub: BORN-WRONG
correct: YES
defect_corrected: YES
fix_chain: 1
chain_kind: SELF
moved: fix_chain 0 -> 1 and chain_kind NA -> SELF. Forward: the remedy scoped here (the account-path remediation, recorded as a 32-file corpus) was refuted at entry 166 by chunk3-29 - the real corpus is 68, including five files the sweep never saw - so the first remedy was incomplete for the same defect. The deeper 174 links belong to the 166 guard and are left on chunk3-29/30 rather than carried up.

id: chunk3-40
entry: 163
prevention: GATE-EXISTING
prevention_why: wrong scope - the commit gate fired on 6 glyphs while CI graded 8, so an ellipsis or an NBSP COMMITTED clean and reddened CI on the same commit
discovery: SIBLING
origin_time: INHERITED
origin_sub: BORN-WRONG
correct: YES
defect_corrected: YES
fix_chain: 1
chain_kind: SELF
moved: fix_chain 0 -> 1 and chain_kind NA -> SELF. Forward: the remedy (widening all three glyph sets to the strictest reading) was refuted in the same slice by chunk3-41, whose claim names it verbatim, and it was incomplete for the same defect - `strip_em_dashes` prefiltered on `E2 80`, which NBSP does not carry.

id: chunk3-41
entry: 163
prevention: GATE-ABSENT
prevention_why: no arm graded that the fast-path PREFILTER still covers the whole glyph set; the check is mechanical and was written only after the widening exposed it
discovery: RUN
origin_time: FRESH
origin_sub: NA
correct: YES
defect_corrected: YES
fix_chain: 0
chain_kind: NA
moved: fix_chain 1 -> 0, chain_kind SELF -> NA. Backward before (this row IS the refutation of the widening, now carried forward on chunk3-40). The prefilter fix is never refuted later.

id: chunk3-42
entry: 162
prevention: GATE-ABSENT
prevention_why: nothing graded that the ack marks only what the REPORT SHOWED; the eight arms that now grade it had to be written
discovery: SELF-AUDIT
origin_time: INHERITED
origin_sub: BORN-WRONG
correct: YES
defect_corrected: YES
fix_chain: 1
chain_kind: SELF
moved: fix_chain 2 -> 1 (chain_kind unchanged). The old 2 counted two PRIOR remedies, which is the backward reading. Forward there is exactly one link: the report-then-ack split shipped here was refuted at entry 185 by chunk1-16, where a suite run marked live mail as SHOWN and "LEDGER 162's defect re-entered through the suite".

id: chunk3-43
entry: 162
prevention: GATE-ABSENT
prevention_why: hermeticity was never mechanically graded; the two tests defaulted `reported_path` to the real machine record
discovery: RUN
origin_time: INHERITED
origin_sub: BORN-WRONG
correct: YES
defect_corrected: YES
fix_chain: 1
chain_kind: SIBLING-SURFACE
moved: fix_chain 0 -> 1 and chain_kind NA -> SIBLING-SURFACE. Forward: the remedy (injecting the path into those two tests) was refuted at entry 168 by chunk3-21, which states it directly - "entry 162 had already fixed two tests of exactly this class by injecting the path; the shared helper kept the defect".

id: chunk3-44
entry: 162
prevention: CONTRACT
prevention_why: CLAUDE.md already recorded the measured half (an untrusted workspace makes headless DISCARD permissions.allow), so checking it before asserting stops the overstatement
discovery: OPERATOR
origin_time: INHERITED
origin_sub: BORN-WRONG
correct: YES
defect_corrected: YES
fix_chain: 0
chain_kind: NA
moved: fix_chain 1 -> 0, chain_kind SAME-ARTIFACT -> NA. Backward before (a later defect in entry 161's artifact, a link now carried forward on chunk3-45's neighbourhood). The corrected rationale is never itself refuted.

id: chunk3-45
entry: 161
prevention: GATE-FIRED-IGNORED
prevention_why: `drift_guard.scan_settings` HAD BEEN flagging the wildcard allow and the empty deny, correctly, and the flag stood unacted-on until an unrelated audit forced it
discovery: SELF-AUDIT
origin_time: INHERITED
origin_sub: BORN-WRONG
correct: YES
defect_corrected: YES
fix_chain: 2
chain_kind: SELF
moved: prevention GATE-EXISTING -> GATE-FIRED-IGNORED (v1.1 CHANGE 3 finally supplies the value this row was forced out of - v1's own closing section names this exact specimen). fix_chain 0 -> 2 and chain_kind NA -> SELF: the remedy (removing the keys plus the tracked-settings guard) was refuted twice - at entry 165 by chunk3-34, where an EMPTY hooks array passed every check LW had, and at entry 168 by chunk3-17, where the tenth guard's `ROOT.rglob` existence test is satisfied by a stale worktree; both name entry 161's guard explicitly.

id: chunk3-46
entry: 160
prevention: GATE-EXISTING
prevention_why: vacuous - four real-commit tests existed and were green, but the FIXTURE was thin, so they could pass while measuring the wrong repo
discovery: SIBLING
origin_time: INHERITED
origin_sub: BORN-WRONG
correct: YES
defect_corrected: YES
fix_chain: 0
chain_kind: NA
moved: none. Forward candidate considered and REFUSED: chunk3-47 sits in the same porting slice, but its claim does not name the new fixture as the thing refuted, so the link is not established by the record and is not scored upward.

id: chunk3-47
entry: 160
prevention: GATE-EXISTING
prevention_why: vacuous - the probe ran in CI and its environment SKIPS made a green meaningless
discovery: CODE-READ
origin_time: INHERITED
origin_sub: BORN-WRONG
correct: YES
defect_corrected: YES
fix_chain: 0
chain_kind: NA
moved: none. Forward: arming LW_REQUIRE_HOOK_GATE=1 in all three jobs is never refuted later in the record.

id: chunk4-01
entry: 159
prevention: ADVERSARY
prevention_why: no gate and no contract reaches the write-time-versus-read-time semantics of a watermark; it needs a reader who asks what advances the marker
discovery: SELF-AUDIT
origin_time: INHERITED
origin_sub: BORN-WRONG
correct: YES
defect_corrected: YES
fix_chain: 5
chain_kind: SELF
moved: fix_chain 1 -> 5 (chain_kind unchanged). This is the largest single effect of the forward pin. The remedy for this event is the seen-FILENAMES watcher shipped at 159, and five later rows name that watcher as the refuted claim: chunk3-42 at 162 (the ack marking notes shown to nobody - "the mtime-watermark defect wearing the ACK as a costume"), chunk3-36 at 164 (top-level glob, a payload DIRECTORY invisible), chunk3-31 at 165 (name key blind to an in-place correction), chunk3-33 at 165 (SessionStart only, so mid-session mail invisible) and chunk3-15 at 168 (a withdrawal has no line it can fail to print). Every one is the same defect the watcher was built to close - mail the operator has not seen going unsurfaced - so SELF, not SAME-ARTIFACT.

id: chunk4-02
entry: 158
prevention: CONTRACT
prevention_why: a declared precondition - promoting an artifact to tracked in a public repo requires a write-time content gate - would have caught it
discovery: SIBLING
origin_time: INHERITED
origin_sub: BORN-WRONG
correct: YES
defect_corrected: YES
fix_chain: 1
chain_kind: SAME-ARTIFACT
moved: chain_kind SELF -> SAME-ARTIFACT (fix_chain stays 1, now forward). The old SELF was the backward note that the 155 fix INTRODUCED the exposure; under v1.1 that INTRODUCED reading belongs on chunk4-07, not here. Forward: the write-time gate shipped here is refuted at entry 171 by chunk3-08, where `test_lw_next_session_guard.py` pins the hand-off write by naming "section 10b" and that section is now 6 - a later, DIFFERENT defect in the same guard, so it is excluded from the reported ratio.

id: chunk4-03
entry: 158
prevention: GATE-ABSENT
prevention_why: nothing graded agreement between the three banned-glyph declarations; a set-equality assertion is mechanical and needs no judgment
discovery: CODE-READ
origin_time: FRESH
origin_sub: NA
correct: YES
defect_corrected: NO
fix_chain: 0
chain_kind: NA
moved: none. Forward: no remedy shipped (the divergence was recorded as a known gap and left open), so nothing exists to be refuted; the 163 incident refutes the COMMIT GATE, not a fix for this event.

id: chunk4-04
entry: 156
prevention: CONTRACT
prevention_why: a declared disclosure review at the moment a file becomes tracked in a public repo reaches it; the mutex-name literals were mechanically checkable
discovery: RUN
origin_time: FRESH
origin_sub: NA
correct: YES
defect_corrected: YES
fix_chain: 0
chain_kind: NA
moved: none. Forward link considered and REFUSED: the ADR-012 name rotation that remedied this later decayed CS's digest pin (chunk3-38 at 164) and exposed a vacuous judge (chunk4-06), but the rotation itself was never shown WRONG, and a fix that invalidates a sibling's pin is not the fix being refuted.

id: chunk4-05
entry: 156
prevention: CONTRACT
prevention_why: a shared file's header asserting a live acquirer set must be re-grounded when either side changes; no mechanical check reaches a cross-repo fact
discovery: SIBLING
origin_time: INHERITED
origin_sub: DECAYED
correct: YES
defect_corrected: YES
fix_chain: 0
chain_kind: NA
moved: none. Forward: the corrected header is never refuted later.

id: chunk4-06
entry: 156
prevention: GATE-EXISTING
prevention_why: vacuous - the condition-4 judge ran and reported GREEN while its substring matcher matched zero mutexes after the rotation
discovery: RUN
origin_time: INHERITED
origin_sub: DECAYED
correct: YES
defect_corrected: YES
fix_chain: 0
chain_kind: NA
moved: fix_chain 1 -> 0, chain_kind SELF -> NA. The old 1 was explicitly backward ("the refuted artifact was the one judge written to close vacuous passes"). Forward: the judge's non-empty assertion is never itself refuted. Prevention held at GATE-EXISTING per the pin's vacuity ruling.

id: chunk4-07
entry: 155
prevention: CONTRACT
prevention_why: a declared precondition that a durable hand-off lives where it can be diffed and reviewed; the standing /done ritual said the opposite
discovery: OPERATOR
origin_time: INHERITED
origin_sub: BORN-WRONG
correct: YES
defect_corrected: YES
fix_chain: 1
chain_kind: INTRODUCED
moved: fix_chain 0 -> 1 and chain_kind NA -> INTRODUCED. Forward: the remedy (moving LW-NEXT-SESSION.txt into the tracked repo, shipped DONE at 155) was refuted at entry 158 by chunk4-02, and it did not merely fall short - it CREATED a new defect, turning the highest-variance artifact in the tree into a public one with no write-time gate. Only this first link is scored here; the 171 link belongs to the 158 gate and is left on chunk4-02.

id: chunk4-08
entry: 154
prevention: CONTRACT
prevention_why: CLAUDE.md's Data Fixes rule already said a pollution fix is not done until the corrupted rows are backfilled, and nobody purged the 84
discovery: RUN
origin_time: FRESH
origin_sub: NA
correct: YES
defect_corrected: YES
fix_chain: 1
chain_kind: SIBLING-SURFACE
moved: chain_kind SELF -> SIBLING-SURFACE (fix_chain stays 1, now forward). The remedy was the 2026-09-06 history purge of the 84 trailers; it is refuted at entry 169 by chunk3-13 - "a history rewrite has no opinion about the commits you make after it" - on a surface the purge never reached, the post-flip commits in a tree where the commit-msg backstop was not in force.

id: chunk4-09
entry: 153
prevention: GATE-ABSENT
prevention_why: no test asserted that a lockfile carrying a LIVE pid but no owner is reaped; the property is mechanically checkable and was never graded
discovery: SIBLING
origin_time: FRESH
origin_sub: NA
correct: YES
defect_corrected: YES
fix_chain: 0
chain_kind: NA
moved: none in value. Recorded for the merger: this is the row v1.1's INHERITED-SHARED was added for, but under the FORWARD pin that value cannot be used here - the fix shipped at 157 into the byte-identical shared `slots.py` is never subsequently refuted in this window (the reserved-lock reap arm is filed as a FUTURE item, not a refutation), so fix_chain is 0 and chain_kind must be NA.

id: chunk4-10
entry: 153
prevention: ADVERSARY
prevention_why: no gate and no contract reaches Windows unlink-against-an-open-handle semantics, and the house rule was itself the thing that was wrong
discovery: RUN
origin_time: INHERITED
origin_sub: BORN-WRONG
correct: YES
defect_corrected: YES
fix_chain: 0
chain_kind: NA
moved: none.

id: chunk4-11
entry: 153
prevention: GATE-ABSENT
prevention_why: nothing checked a documented performance figure against a measured one, and nothing dates its own facts
discovery: SELF-AUDIT
origin_time: INHERITED
origin_sub: DECAYED
correct: YES
defect_corrected: YES
fix_chain: 0
chain_kind: NA
moved: none. Forward: the corrected 2521/18 figure in the ci.yml header is never refuted later; entry 178's stale 2752 baseline is a different artifact and a different remedy.

id: chunk4-12
entry: 152
prevention: ADVERSARY
prevention_why: the code behaved as written; what was defective was the agent's model of it, and only a reader tracing `_usm_applies` against the over-target branch reaches that
discovery: CODE-READ
origin_time: FRESH
origin_sub: NA
correct: YES
defect_corrected: YES
fix_chain: 0
chain_kind: NA
moved: none.

id: chunk4-13
entry: 151
prevention: CONTRACT
prevention_why: a declared precondition that a measurement artifact records its execution environment; LEDGER 19's artifact never recorded its provider
discovery: RUN
origin_time: INHERITED
origin_sub: DECAYED
correct: YES
defect_corrected: YES
fix_chain: 0
chain_kind: NA
moved: none. PROXY-MEASURE was considered and refused: the second measurement uses the SAME instrument on a different provider, not a different quantity, so this is an unrecorded-environment failure and CONTRACT holds.

id: chunk4-14
entry: 150
prevention: GATE-EXISTING
prevention_why: vacuous - both cross-repo byte guards ran and stayed green while their skip-when-absent branch compared ZERO files after the sibling was renamed
discovery: SIBLING
origin_time: INHERITED
origin_sub: DECAYED
correct: YES
defect_corrected: YES
fix_chain: 0
chain_kind: NA
moved: none.

id: chunk4-15
entry: 150
prevention: CONTRACT
prevention_why: the renaming party must sweep the SIBLING's constants in the rename commit - a statable precondition neither side had
discovery: SIBLING
origin_time: INHERITED
origin_sub: BORN-WRONG
correct: YES
defect_corrected: YES
fix_chain: 0
chain_kind: NA
moved: none. Forward: `resolve_sibling_root` is never refuted later; that the sweep rule stayed FUTURE guidance is a coverage gap, not a refuted remedy.

id: chunk4-16
entry: 149
prevention: GATE-EXISTING
prevention_why: vacuous - tests/test_lw_golden.py exercises the freeze/regress tool against tmp_path in 0.06s and never touches the GPU, so it would have passed identically either side of the driver bump
discovery: CODE-READ
origin_time: FRESH
origin_sub: NA
correct: YES
defect_corrected: YES
fix_chain: 0
chain_kind: NA
moved: none. PROXY-MEASURE was considered and refused: a CODE READ is what caught it, and the pin requires that no code-reading adversary reaches a PROXY-MEASURE row.

id: chunk4-17
entry: 149
prevention: GATE-EXISTING
prevention_why: wrong scope and vacuous in effect - `_pinned_from_config` hardcoded {1.2, 70, 3} instead of reading live `lw_upscale.USM_DEFAULT`, so the version hash could not move
discovery: CODE-READ
origin_time: INHERITED
origin_sub: DECAYED
correct: YES
defect_corrected: YES
fix_chain: 0
chain_kind: NA
moved: none. PROXY-MEASURE refused for the same reason as chunk4-16, and because the instrument was not correct - it hashed the wrong input.

id: chunk4-18
entry: 149
prevention: GATE-ABSENT
prevention_why: nothing dated the golden baseline against the code path it baselines; comparing a freeze timestamp to a landing commit is mechanical and was never graded
discovery: CODE-READ
origin_time: INHERITED
origin_sub: DECAYED
correct: YES
defect_corrected: NO
fix_chain: 0
chain_kind: NA
moved: none. Forward: the re-freeze was deliberately left to the operator, so no remedy exists to be refuted.

id: chunk4-19
entry: 148
prevention: CONTRACT
prevention_why: a brief must enumerate every condition required for the effect it claims; only the first of three was reported
discovery: CODE-READ
origin_time: INHERITED
origin_sub: BORN-WRONG
correct: YES
defect_corrected: YES
fix_chain: 0
chain_kind: NA
moved: none.

id: chunk4-20
entry: 148
prevention: PROXY-MEASURE
prevention_why: `get_available_providers()` is a CORRECT instrument answering the WRONG question - ORT falls back to CPU silently and keeps listing CUDA, so running the standard check is what manufactured the false green
discovery: RUN
origin_time: FRESH
origin_sub: NA
correct: YES
defect_corrected: YES
fix_chain: 0
chain_kind: NA
moved: prevention ADVERSARY -> PROXY-MEASURE. The v1 pass scored ADVERSARY under protest and flagged this row as the pin's own un-handled class; v1.1 CHANGE 3 supplies the value, and this row meets every clause - no gate reaches it, no code-reading adversary reaches it, and a second instrument measuring a different quantity is what was needed. fix_chain confirmed 0 forward.

id: chunk4-21
entry: 148
prevention: CONTRACT
prevention_why: re-read a cited source before resting on it, which is LW's own Verification rule; no check grades whether a citation supports the claim it is used for
discovery: RUN
origin_time: INHERITED
origin_sub: BORN-WRONG
correct: YES
defect_corrected: YES
fix_chain: 0
chain_kind: NA
moved: none. GATE-FIRED-IGNORED was considered and refused: `tests/test_gpu_mutex_wiring` did fire, but its output was ACTED ON - it is what found the defect - and the new value requires the output to have been tolerated.

id: chunk4-22
entry: 148
prevention: CONTRACT
prevention_why: never quote a per-item break-even off a single COLD run - a statable methodology precondition; the 38s carried one-time sm_120 PTX JIT
discovery: RUN
origin_time: FRESH
origin_sub: NA
correct: YES
defect_corrected: YES
fix_chain: 0
chain_kind: NA
moved: none. Note for the merger: v1.1 CHANGE 6 narrows exclusion 4 and this row stays IN either way - it is a measurement that would have driven a real decision, not a probe clearing its own stated hypothesis.

id: chunk4-23
entry: 147
prevention: GATE-ABSENT
prevention_why: no post-move check existed - asserting that `.git` is present and `git status` answers is mechanical, and the Windows HIDDEN attribute made the failure silent
discovery: SELF-AUDIT
origin_time: INHERITED
origin_sub: BORN-WRONG
correct: YES
defect_corrected: YES
fix_chain: 1
chain_kind: SELF
moved: fix_chain 0 -> 1 and chain_kind NA -> SELF. Forward: the remedy (init + remote add + fetch + reset) was refuted by chunk4-24 in the same entry - `core.hooksPath` lived in the destroyed config and was not restored, so the recovery was incomplete for the same defect and the authoritative gate stayed dead.

id: chunk4-24
entry: 147
prevention: GATE-EXISTING
prevention_why: wrong time - `tools/install_git_hooks.py --check` already existed and is wired into drift_guard, but nothing ran it as PART of the recovery
discovery: RUN
origin_time: FRESH
origin_sub: NA
correct: YES
defect_corrected: YES
fix_chain: 0
chain_kind: NA
moved: fix_chain 1 -> 0, chain_kind SELF -> NA. The old 1 was the backward reading and is now carried forward on chunk4-23. Reinstalling `core.hooksPath` is never itself refuted later.

id: chunk4-25
entry: 146
prevention: ADVERSARY
prevention_why: no gate and no contract reaches the fact that Windows refuses to rename a live process's cwd; only a reader with that lens, or the run itself, gets there
discovery: RUN
origin_time: FRESH
origin_sub: NA
correct: YES
defect_corrected: YES
fix_chain: 1
chain_kind: INTRODUCED
moved: fix_chain 0 -> 1 and chain_kind NA -> INTRODUCED. Forward: the abandoned rename approach's remedy was the copy-based move actually performed, and that remedy was refuted at entry 147 by chunk4-23 - the copy skipped Windows HIDDEN items and dropped exactly the repository, a new defect the remedy CREATED. Scored on the record's own causal statement rather than inferred. Also note under v1.1 CHANGE 6: this row is a PLANNED APPROACH that was adopted and attempted for 180s, so the narrowed exclusion 4 no longer even arguably touches it.

id: chunk4-26
entry: 146
prevention: CONTRACT
prevention_why: a shared file naming its participants must be re-grounded on any participant rename; the 146 sweep covered LW's own root spelling and no rule covered a sibling's
discovery: SIBLING
origin_time: INHERITED
origin_sub: DECAYED
correct: YES
defect_corrected: YES
fix_chain: 0
chain_kind: NA
moved: none. The 150 sibling-constant incident refutes the ROOT RENAME sweep, not this docstring correction, so no forward link is scored here.

id: chunk4-27
entry: 145
prevention: ADVERSARY
prevention_why: no gate and no contract reaches a void premise handed in by the operator; it takes a reader willing to refuse the framing and name the real axis
discovery: SELF-AUDIT
origin_time: INHERITED
origin_sub: BORN-WRONG
correct: YES
defect_corrected: YES
fix_chain: 0
chain_kind: NA
moved: none on the three re-derived fields. Flagged only: v1.1 CHANGE 4 adds RESEARCH, which is this row's true `discovery` value, but `discovery` is a copy-through field in this pass and is left at SELF-AUDIT for the merger to fix.

id: chunk4-28
entry: 145
prevention: GATE-EXISTING
prevention_why: vacuous - CI ran and reported green while `test_worker_spandrel_branch_produces_both_variants` cannot execute on any runner, so the green asserts nothing about that arm
discovery: RUN
origin_time: FRESH
origin_sub: NA
correct: YES
defect_corrected: NO
fix_chain: 0
chain_kind: NA
moved: none. GATE-FIRED-IGNORED was considered (the LOCAL run does go red and the result is filed unowned) and refused per the brief's ruling that vacuity is GATE-EXISTING; the refuted claim is the CI green, which is the vacuous half.

---

## Counts (hand-derived from the rows above; recount by machine)

Rows out: 75 (chunk3 47, chunk4 28).

prevention MOVED: 2 of 75 - chunk3-45 (GATE-EXISTING -> GATE-FIRED-IGNORED),
chunk4-20 (ADVERSARY -> PROXY-MEASURE). Both are exactly the two specimens v1 named
in its own closing section as classes it could not score.
 - GATE-EXISTING 16, GATE-ABSENT 20, CONTRACT 23, ADVERSARY 14,
   GATE-FIRED-IGNORED 1, PROXY-MEASURE 1 (machine-counted from this file).

fix_chain MOVED: 36 of 75 (chunk3 30, chunk4 6).
 - chunk3: 01, 02, 03, 04, 07, 08, 10, 11, 13, 16, 17, 18, 20, 22, 23, 25, 29, 30,
   33, 34, 35, 36, 37, 39, 40, 41, 42, 43, 44, 45.
 - chunk4: 01, 06, 07, 23, 24, 25.

chain_kind MOVED: 40 of 75 (chunk3 33, chunk4 7).
 - chunk3: 01, 02, 03, 04, 07, 08, 10, 11, 13, 15, 16, 17, 18, 19, 20, 21, 22, 23,
   25, 29, 30, 31, 33, 34, 35, 36, 37, 39, 40, 41, 43, 44, 45.
 - chunk4: 02, 06, 07, 08, 23, 24, 25.
 - values: NA 53, SELF 11, INTRODUCED 7, SIBLING-SURFACE 3, SAME-ARTIFACT 1,
   INHERITED-SHARED 0 (machine-counted from this file).

FIX-OF-A-FIX COUNT (rows with fix_chain >= 1):
 - OLD, as scored under v1: 32 of 75 (chunk3 27, chunk4 5).
 - NEW, forward: 22 of 75 (chunk3 16, chunk4 6).
 - chunk3 forward >= 1: 01(2), 03(2), 04(2), 15, 19, 21, 29, 30(2), 31, 32, 37, 39,
   40, 42, 43, 45(2).
 - chunk4 forward >= 1: 01(5), 02, 07, 08, 23, 25.
 - Membership overlap between the old and new sets is 8 rows only (chunk3-15, 19, 21,
   30, 31, 32, 42, chunk4-01), so the direction change is not a re-labelling of the
   same population - it is very nearly a different one, which is the disjointness
   v1.1 CHANGE 1 was written to stop.
 - Under the pin's ratio rule (SELF + INTRODUCED + SIBLING-SURFACE + INHERITED-SHARED,
   SAME-ARTIFACT excluded) the counted set is 21 of 75; chunk4-02 is the one
   SAME-ARTIFACT exclusion.

## Limits this pass must report alongside its numbers

1. EXTRACTOR vs BUCKETER: satisfied. These 75 rows were extracted by two other
   passes; this pass scored rows it did not extract and did not author the events.
2. PERSISTENCE: satisfied. The per-event rows are tracked in
   `docs/REFUTATION_COST_ROWS_2026-09-12.md`, so this re-score cost one read pass,
   not a fresh extraction.
3. FLOOR: every count here is a floor. Forward links can only be seen where a later
   entry names the remedy; a remedy quietly refuted outside the ledger, or in a
   sibling tree's records, is invisible to this pass. Where the record did not
   establish a forward link, the row was scored 0 rather than guessed upward - that
   rule was applied explicitly on chunk3-46, chunk4-04, chunk4-09, chunk4-26.
4. DOUBLE COUNTING, declared: the pin says a chain is ONE event, but the census
   persisted each link as its own row and this pass may not merge rows. Where two
   rows were closed by the SAME remedy (chunk3-03/04 on done_gate, chunk3-29/30 on
   the account-path sweep) both carry that remedy's forward links, so a merger
   summing fix_chain across rows will over-count; counting ROWS with fix_chain >= 1
   does not.
