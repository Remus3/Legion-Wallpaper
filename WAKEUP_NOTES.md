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
