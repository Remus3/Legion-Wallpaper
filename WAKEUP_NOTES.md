# WAKEUP_NOTES - LW hand-off ledger

---

## NEXT SESSION - the parked pipeline queue

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
