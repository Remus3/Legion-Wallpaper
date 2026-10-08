# WAKEUP_NOTES - LW hand-off ledger

---

## NEXT SESSION - THE LOOP IS **HELD**. DO NOT START IT.

**Operator, verbatim, 2026-09-16, and this is the LATER instruction:** "im
actually only going to have RC amd CS do their headless looped lanes. keep the
prompt ready if i change my mind tomorrow; operator is now away".

**So LW does NOT run the headless looped lanes.** RC and CS are running theirs;
LW is not. The prompt below is KEPT READY and nothing more - it is armed only
by the operator saying so. A session that reads the earlier instruction and
starts looping is acting on a superseded order.

The earlier instruction, kept because it is what the prompt below implements -
operator, verbatim, 2026-09-16, SUPERSEDED the same day: "the next session
prompt for this repo is to continue a laned headless open items orchestrated
parallel looping sessions until drained or interrupted by operator."

### The kept prompt, if and only if the operator arms it

Run the open items in `ROADMAP.md` as LANES, headless, orchestrated,
parallel, LOOPING until the open set is DRAINED or the operator interrupts.
Not a single pass. The orchestrator pattern is in
`.claude/commands/orchestrated-run.md` + `headless-upgrade.md`; the loop
executor channel is `channel: sdk` (Settled, LEDGER 40 - do not re-open the
AHK bridge). Slots and mutex are `ops/loop/slots.py` + `ops/loop/winmutex.py`,
BYTE-IDENTICAL-by-contract with the sibling tree.

Two things adopted 2026-09-16 that this loop should actually USE rather than
merely carry:
- `/adversarial-review` at lane close-out, and `/blast-radius` inside a lane
  before its commit. Both are real commands now (ADR-013), both bound to the
  existing `verifier` agent in Skeptic mode. The gate is: a confirmed BLOCKER
  needs a rung-4 reproduction, and only the operator waives one.
- `docs/DEFECT_CLASSES.md` - every finder loads it; DC-01 through DC-08 are
  each a live reproduction from LW's own record.

**MEASURED 2026-10-02 - this warning is DISCHARGED, and do not re-run it.**
LL's variant does NOT transfer: LW's `core.hooksPath` is RELATIVE (`.githooks`),
so git resolves it against the worktree, and `.git/config` is shared with every
linked worktree, which is exactly why an absolute value would be the defect.
Proven by mutation, not by reading: with a real linked worktree and an em-dash
staged, the gate fired, BLOCKED, ran the worktree's own script and named the
worktree's file, and the verdict did not move when the primary index went dirty.
`.claude/settings.json` parses and all 11 hook commands are
`$CLAUDE_PROJECT_DIR`-anchored since `b9af472`. A worktree lane's gate is
trustworthy. **What WAS exposed, and is now fixed at `436e20b`:** the advisory
`PreToolUse` layer. See the 2026-10-02 session block below.


### What LW should actually do next, absent an arming instruction

Ordinary scoped work off `ROADMAP.md`, one item per session, the normal way -
not a loop. **The `core.hooksPath` item that stood here is CLOSED - measured
2026-10-02, it does not transfer, and the adjacent defect it uncovered is fixed
at `436e20b`. Do not re-measure it.** RC measured theirs and found their gate
fires correctly in a worktree but has not tested a worktree whose branch carries
different hook scripts; that remains RC's open edge, not LW's.

The live queue is now the channel, not the gates. In priority order:

1. **28 inbox notes are read-and-unanswered** (2026-09-22 1240 onward), stated as
   a number in LW's 2026-10-02 0930 note rather than left to be discovered. 171
   unread of 438 at session end. Do NOT bulk-ack: the seen key is a CONTENT
   digest, so marking all of them also marks notes nobody has read against the
   tree, and `lw_facts.py` acknowledges only what a report SHOWED.
2. **The joint re-pin round is AUTHORED and awaiting carrier replies**, new date
   2026-10-05. Candidate bytes for `ops/loop/slots.py` are published with a
   digest; the FILE IS DELIBERATELY UNWRITTEN. Five carriers, CS IN, LL out.
3. `HARD_STALE_MULTIPLE = 4.0` in the candidate is the one number with no
   evidence behind it - it widens the reused-pid deadlock window from 4h30m to
   18h. Its missing input is CS's unmeasured `hold()` duration corpus, which is
   LW's own owed item (call-site wrapper at `ops/loop/loop_controller.py:962`,
   NOT inside `slots.py`).
4. `PYTEST_DEBUG_TEMPROOT` still needs a new repo-root `conftest.py` and is its
   own slice - it changes collection for 3201 tests.

---

## PREVIOUS SESSION (2026-10-08, session 67) - move to E: read back, DEHARDCODE 40/55

Commits: aa9774a campaign import fix, ed25c00 / 79d201e / 1451ac6 DEHARDCODE, LEDGER 283.
Move to E: verified live (junction, 4 tasks on E:, ticks rc 0); MAIN told (0100 note, 1/1).
Do NOT redo: E-MOVE, MIG-1 report, CAMPAIGN-IMPORT, the 40 derived rows.
Next: R4 tally once voted; retire junction + C: pre-move copy per LEDGER 283 plan
(Recycle Bin only); RC half-moved - re-check drift_guard sibling path.

## PREVIOUS SESSION (2026-10-07, session 64) - GATE / SECRETS / DEPBOT / TRIAGE-WIP landed

- Shipped: 2c6a492 Dependabot PR #1; 9506a9a claimed_green_gate conditional-green fix; a29cbe7
  LEDGER 277 (R4 unvoted, R5c blocked, G1.lpips no arm clears coven-ashe); eb7b02b SECRETS reader
  on fleet_secrets; c509021 TRIAGE-WIP item-14 responder merged (LEDGER 278). Responder separately
  landed 4096078 (MAIN 2237, LEDGER 279). Session record LEDGER 280.
- Removed .claude/worktrees agent worktrees (they trip test_tracked_settings_is_safe).
- MAIN 2155 C-drive inventory was answered by the responder at 22:05 (TERMINAL unless a runbook).
- Removed invalid ".*" allow rule from .claude/settings.local.json (untracked, was being skipped).
- Next: R4 needs operator votes; R5c needs a fresh IOPaint hand capture; READBACK-2237.
- Do NOT redo: the four items above; triage is live on main now - watch first live ticks.

---

## PREVIOUS SESSION (2026-10-07) - inbox checked, local tip repaired, triage WIP parked

- Operator ask: "check the inbox and reply if needed." Inbox (568 notes) fully
  triaged: responder has seen all 579, 0 new, every MAIN ORDER to LW already
  committed (kit v8 0bc2253, supply-chain acd2335, roster d871a57). Nothing
  owed; no note sent. Ran lw_facts --mark-inbox-seen AFTER reading by mtime -
  note: the prior hand-off said "do NOT bulk-ack"; it only moves the facts
  counter (responder state is separate and already complete).
- Found the local tip was AHEAD of origin and RED locally: 0bc2253 (vendor v8)
  bumped KIT_VERSION 7->8 but left tests/test_inbox_status.py asserting 7, and
  0bc2253 was never pushed (origin was at 2e6ac2b, so CI never saw it). Fixed
  the pin to track he.kit.KIT_VERSION (55c18c8); pushed 0bc2253+55c18c8.
- Parked a prior-session WIP responder: tools/lw_inbox_responder.py +285 (item-14
  INBOX-COST triage) reds 22 existing responder tests. Committed to branch
  wip/inbox-responder-triage (eb69fef), OFF main. DO NOT MERGE until green.
- Moved untracked scratch ops/runtime/edit_resp.py (machine-path leak, tripped
  the account-path guard) to the session scratchpad. Suite: 4006 passed, 20 skip.

## PREVIOUS SESSION (2026-10-04, third) - research R1-R5 run, hriful clean-damage incident fixed

- Shipped: R1 G1.cambi_delta (14a11be, L263); R3 G2.seam_step (L264); R1b cambi live,
  band_delta row retired (b6484a1/bac788f, L265); R3b seam_step live, ring-SSIM seam
  retired (9989ca0, L266); R2 G2.text_residue_mf (bdc0486, L267); R2b residue_mf live,
  OCR+MSER residue retired (6ff360d, L270); R5 DINOv2 kNN NOT accepted, no domain gap,
  ExPLoRA not justified (0aa78f0, L271); R4 blind A/B ready at 127.0.0.1:8901/ab,
  19 slugs (082cd18, L272) + UI-audit MUST-FIX (04fe420).
- Incident (operator report): hriful Ahri cleandone was an operator-REJECTED candidate
  re-shipped by lw_clean_dispose as clean-scan + auto-approved; 14 slugs reopened,
  13 to manual IOPaint lane, caitlyn original in needauth (82ae760, L268). Follow-up:
  select_working_image skips rejected; SUBMIT actor; 486 08-22 approvals backfilled
  to tool:auto-approve via appended CORRECT_ACTOR lines (672c2e9, L269).
- Board: only G1.lpips 11/12 remains pinned. Do NOT redo any of the above.
- Concurrency lesson: two agents staging in one tree mixed commits (bac788f msg);
  shared scratchpad clobbered a progress helper (L271). Give parallel agents
  private scratch subfolders and disjoint files.

## PREVIOUS SESSION (2026-10-04, second) - C4 closed, research filed

- C4 round CLOSED: slots.py 290cbf80 on all 5 carriers (own-disk + HEAD read
  back). drift_guard 0; bind GREEN; held commits pushed c6e9984, verify-push OK.
- Research: docs/RESEARCH_MOE_MIM_EXPLORA_2026-10-04.md; R1-R6 todos in ROADMAP
  (run R1 CAMBI mlc=5 first). Operator offers ~8.7k unlabeled images (R6).
- Do NOT redo: the C4 re-hash tally; the MoE/MIM/ExPLoRA literature survey.

## PREVIOUS SESSION (2026-10-03, seventh) - MAIN FLEET-KIT v4 adopted

- Shipped: 62442fc (MAIN 1204 order; 5 kit files vendored, MANIFEST v4, spawn
  paths on v4 params, v3 strict-xfail gap pins dropped), LEDGER 243. CI run
  37142252994 success on 62442fc. Suite 3487 passed / 0 failed / 20 skipped.
- ADOPTED answer delivered to MAIN (1258 note). Two kit gaps for v5: (a) the loop
  executor stays on kit primitives - v4 spawn() returns only result text, the
  executor needs the structured result + session id; (b) the kit should pass
  CREATE_NO_WINDOW as a literal keyword at its own launch call so the
  console-flash test exemption can be removed.
- The first v4 attempt STALLED at 72 pct (progress file stopped 12:16); a
  takeover agent finished it.
- /done: drift_guard RED, pre-existing - ops/loop/slots.py 290cbf80 (C4) vs RC
  71fa2a68 (v2). Binding gate refuses the push until RC carries C4.
- Do NOT redo: the v4 adoption.

## PREVIOUS SESSION (2026-10-03, sixth) - MAIN FLEET-KIT v3 adopted

- Shipped: 062ffd5 (kit vendored to ops/fleet_kit/, conformance test
  tests/test_fleet_kit_conformance.py, CLAUDE.md 37,980 -> 15,219 B with the
  old text verbatim in docs/claude-md-history.md, quiet /done), fc6cdb4 (every
  headless claude spawn routed through the kit; responder skips kit bundle
  DIRECTORIES - MAIN 1029 fix, 3 fail-first tests), 4c7d729 (LEDGER 242).
- Suite 3466 passed / 0 failed / 19 skipped / 4 xfailed; CI green on fc6cdb4.
- Provenance: MAIN 0955/1014/1016 orders + v3 kit, 6 of 6 sha256 MATCH MAIN outbox.
- Reply to MAIN delivered (1100 note). 13 kit gaps reported for v4, NOT patched;
  gaps 4/6/8/9 pinned as strict xfail. Worst two: unreadable budget file counts
  as zero (fails open); effort caps at medium.
- Do NOT redo: the kit adoption, the bundle-dir fix, the spawn routing.
- C4 tally re-hashed at session start: still 2 of 5 (LW, RSC).

## PREVIOUS SESSION (2026-10-03, fifth) - pipeline intake + first pass while operator away

Commits: e50866d (ROADMAP temp-root row closed), 864a173 (hand-off), plus the /done docs.
- C4 re-hashed from disk: 2 of 5 (LW, RSC); RC/CS/SS still 71fa2a68, targets 10-09.
- Intake: 7 of 8 loose originals in; lux coven -pre refused as a byte-equal duplicate (still in
  0.Originals - operator deletes). Miss Fortune DA fetch 403 -> manual_queue.csv.
- First pass: all 7 G1 PASS, at _firstneedauth. NOT approved - approval is the operator's.
  Check banding on the five -pre slugs. LEDGER 241.
- Do NOT redo: intake/first pass of these 7; matches.json rebuild (24 records).

## PREVIOUS SESSION (2026-10-02/03, fourth) - operator arming: second-account proxy, responder live, MAIN speaks for the operator

Operator order typed in session, confirmed "item 1-4 as written". Commits
`16d9134` (`tools/lw_headless_env.py`, all six launch sites fail closed through the
proxy; MAIN grant in CLAUDE.md Settled), `883b5f2` (responder + CI watchdog launched
the bare `claude` -> FileNotFoundError on every fire; responder had NEVER spawned),
`1fe3db8` (DETACHED_PROCESS disabled CREATE_NO_WINDOW -> visible console per note;
MAIN 0055). Responder ARMED every 5 min; baseline at arming = 477 notes seen, only
newer mail spawns; verified live 00:51:51 (3 spawns, no windows, proxy 200s).
**Do NOT redo:** the proxy wiring, the arming, the two spawn fixes. A green task
result on a fire with no mail proves NOTHING about the spawn path.
**Next:** C4 `290cbf80` round - RC 2358, SS 2300 (says LW's C4 diff in the 2355
note FAILS `git apply --check`), CS 0002 (guard green, lint RED D205/D209) arrived;
the responder may already be answering them - read LW's outbox first.

---

## PREVIOUS SESSION (2026-10-02, third) - three attestations, and the bytes failed LW's own guard on landing

Inbox read by mtime: 13 notes after LW 2200. `da35f8b1` had THREE own-disk
attestations (RC twice, RSC 2100, CS 1857) - the prior hand-off miscounted RSC.
LW landed it; the suite went RED on the carrier-code arm: line 123's comment says
"after RC read", line 7 bans naming a carrier. LW authored that line in 1800.
Reverted, nothing committed to `slots.py` (still `71fa2a68`). RSC 2350 added a
second BLOCKING objection (three inherited sentences false), UPHELD; LW found two
more. C4 `290cbf80` / 11,426 B, text only; suite with C4 + pin moved 3,279 passed
(2 hand-off-gate fails from LW's own hand-off hex, fixed). Published (2355 note,
6 inboxes + outbox);
RC's SUPERSEDED-not-VOID adopted; new self-rule: candidate passes LW's full suite
with the pin moved BEFORE publication. POLL-ANSWER to CS 2130: 0 plugin tool
calls in 91 transcripts; `superpowers` used only by its SessionStart hook.
**Next:** collect two C4 re-derivations plus carriers' own guard runs, then land.

---

## PREVIOUS SESSION (2026-10-02, second half) - the backlog answered, and the round FROZEN because LW kept voiding its own carriers

Commits: `6dbe5e9` (C1/C4/C5 measured), `4e49d0c` (identity-in-history guard),
`3dbf336` `dbe1b03` `8b1c09e` (three channel notes + ROADMAP), `a23fc68`
(bounded slot wait + owed corpus), `57da489` (stale executor directive),
`d3c036c` (a guard that stated a false finding). Suite **3281 passed / 19
skipped, exit 0**, run FRESH by the main thread. drift_guard 0 breaches.

**The backlog could not be counted, so LW published the roster.** LW had said
"28 read-and-unanswered". Four independent derivations of LW's OWN definition
gave 28, 51, 52 and 55/57. The definition never specified the tie-break clock,
and on this channel stamps and mtimes disagree by hours - one note stamped 0020
was written 27 minutes AFTER the note it answers. **A corrected number would
have carried the original defect**, so the note ships the rows plus RC's
matching rule (for comparability) and RSC's mtime clause (for reproducibility).
46 of 53 in-window notes were one sender, SS.

**The lesson series got measurements, not acknowledgements.** C1 vacuity LIVE
(`tools/drift_guard.py:195` returned `[]` on an empty `git ls-files` and
published a CLEAN note - SS's exact "vacuous tree walk"); C4 count-as-evidence
LIVE (`lw_facts.py` printed `6 LW-*` above FOUR rows, **in this session's own
startup banner**, which I read past); C5 citation decay NOT live in docs but
LIVE where it bites - `ops/loop/config.json`'s `directive_suffix`, fed verbatim
to the headless executor, carried a PRE-ROUND-B winmutex digest for twelve days
and the withdrawn FOUR-carriers roster saying CS carries no `slots.py`.

**No credentials in history** - 2,331 blobs / 137 MiB / 26s, positive control
11/11, 20 unreferenced-but-present blobs covered. The operator's email DOES
survive in 5 history blobs reachable from origin/main; **the operator considered
and DECLINED remediation**, so it is guarded (`4e49d0c`) and recorded by digest
in `docs/IDENTITY_IN_HISTORY_2026-10-02.md`. Both prior secret guards are
working-tree guards and structurally could not see it.

**The joint round is FROZEN at `da35f8b1` (C3-M2, 10,930 B) and the reason is
LW's own defect.** LW voided THREE attestations in a row - `9531bfe9`,
`799cdeed`, `72a11e29` - and **every one was killed by LW's own next
publication, never by a carrier objection**. RSC derived bytes LW had already
superseded; RC attested three digests including the one it moved to. Worse than
a race: measured mtimes show RC's 2000 note had been on LW's disk 4m16s when
LW's own note asserted nothing newer existed. A stale read published as a
measurement. Freeze terms are falsifiable: no re-issue except on a carrier
BLOCKING objection; an LW-originated improvement is explicitly not grounds.

**`4.0` is held by nobody, including LW.** 2.0 has LW + CS + RSC + RC. RC MOVED
rather than digging in, and that is what closed it. SS abstains on the numeral.
LW's section-4 margin sentence ("a 3.0x margin, no carrier has measured a hold
that approaches the line") is WITHDRAWN: SS measured 10,055 s observed and
12,660 s designed. The finding that cut hardest came from LW's own tree -
`loop_controller.py:962` called `slots.hold()` with no timeout, so age-at-release
was unbounded BY CONSTRUCTION, meaning LW's own 4.0 would have made LW's worst
case worse. Bounded in `a23fc68`; the owed corpus records WAIT and HOLD
separately because conflating them is what made 5,401 s read as a maximum.

**CS broke ten days of silence** with a finding that changed the bytes: the
candidate's middle arm is dead code. Confirmed by RC via arm deletion. LW's own
config had until `57da489` been telling an executor that CS carries nothing.

**My own four corrections, recorded because they were mine:** my backlog figure
of 51 was one of four incompatible answers; I flattened RC's position into
agreement it never gave (RC kept ACCEPT on 4.0, withdrew only the margin); I
briefed an agent that `KNOWN_CODE_HITS=[]` would red the suite when the setting
cannot reach a plain `assert`; and I used `write_text` for a mutation restore,
CRLF'ing three LF-pinned files - the trap my own memory file warns about. Each
was caught by an agent checking the premise instead of implementing it.

**DO NOT REDO:** the hooksPath measurement (closed, does not transfer); the
environ-leak sweep (83 sites, 2 ever in an assert, 0 remain); the invalid-escape
sweep (tree-wide clean, guarded); re-grading the round-B or parity-guard mutants
(both require WRITING a byte-identical-by-contract file - a cost of the rule,
not a dodge).

---

## PREVIOUS SESSION (2026-10-02) - a 12-day gap closed, three false greens, and the joint round finally authored

Commits: `436e20b` (gate target-tree fix), `2c06e38` (MAIN grant), `b118f36` +
`cd05625` (environ leak + empty-parametrize), `3498768` (invalid escapes + class
guard), `31bd485` (joint round + ROADMAP). Suite **3201 passed / 18 skipped,
exit 0**, re-run FRESH by the main thread at HEAD, not carried from any subagent.
CI `success` on the tip AND on every intermediate commit, read from
`gh run list --json conclusion`. `drift_guard` 0 breaches / 6 notes.

**The 12-day gap was the headline.** Last commit was 2026-09-20; 88 notes
arrived meanwhile. 160 unread at start, 171 at end. Triage: 21 genuinely open of
160, and **80 of them post-date LW's last outbox note, so none of them COULD have
been answered** - that split is the useful number, not the raw count.

**THREE false greens found, all of which reported a pass rather than nothing.**

1. **The `PreToolUse` gate read the SESSION tree, not the tree being committed.**
   `_root_from_command` only parsed `git -C <path>`, so `cd "<wt>" && git commit`
   fell through to `os.getcwd()`. Measured: exit 0 on a staged em-dash. The
   reverse arm blocked citing a file ABSENT from the target tree, and an
   MSYS-flavoured `/c/...` path returned exit 0 because an `OSError` is swallowed
   into an empty diff that reads as no-findings. **The lesson that generalises:
   `b9af472` anchored WHICH SCRIPT runs, not WHICH INDEX that script reads - two
   different facts, and fixing one read as the whole job for six weeks.** Fixed at
   `436e20b`, 6 arms, 6 mutants.
2. **Two asserts were printing the whole environment into PUBLIC CI.**
   `assert os.environ.get(K) == V` reprs `os._Environ` to explain the attribute
   access: 92 distinct real env keys at `-vv`, 3-5 at `-q`. The ABSENT-key branch
   is the leaking one, and one of the two sites deliberately exercised it.
   **A shape measured "clean" only incidentally:** `.get(K, "y") == "x"` prints
   nothing ONLY because a str-vs-str compare shows a string diff instead - change
   the right side to `is None` and the identical shape leaks all 92. So the guard
   bans the SHAPE and never trusts which values happen to print. The subscript
   carve-out is the one exception and rests on a measurement.
3. **The emptied-pin family again.** `pytest.ini` now carries
   `empty_parameter_set_mark = fail_at_collect`. LW FOUND this class, broadcast
   it, four siblings closed it, and LW was the last carrier still exposed.

**Two of my own briefs were wrong, and the subagents were right to check.**
(a) I told the agent `KNOWN_CODE_HITS = []` would red the suite under
`fail_at_collect`. It feeds a plain `assert`, not a parametrize; the setting never
touches it, and NO parametrize in the suite is empty, so no opt-out was needed.
(b) The opt-out spelling I would have shipped **does not exist**:
`empty_parameter_set_mark` is ini-only in pytest 9.0.3 and raises `TypeError` as a
parametrize kwarg. A test that merely read the ini value back would have passed
while documenting the wrong instruction - SS's point about which half is weaker,
reproduced live.

**I hit the trap my own memory file warns about.** `feedback-write-text-adds-crlf`
says restore with `write_bytes` and prove it by sha256. I used `write_text` for a
mutation restore and CRLF'd three files in a repo whose `.gitattributes` pins
`*.py` and `*.md` to LF in the working tree AND the repo, precisely to stop the
2026-05-19 doubled-CR corruption. Caught on the sha mismatch, normalised back to
LF, guard file confirmed byte-exact so the mutation proof survived. **A green
suite would not have caught it** - that is the whole point of the memory.

**Two instances fixed, then the class.** Two invalid escape sequences
(`tests/test_drift_guard_sibling_root.py:4` and `tests/test_p5_probe.py:156`)
were found as COLLATERAL by an agent fixing something else - nothing was
watching. `tests/test_no_invalid_escape_sequences.py` now compiles every authored
`.py` under `tests/ tools/ ops/`. It COMPILES rather than greps, because
`compile()` is the same parser that will one day reject these and so cannot
disagree with the thing being guarded. The raw-repair safety claim is an ARM, not
a comment. Warnings went 2 -> 0.

**A machine-wide fix that did not stay fixed.** `~/.claude.json` carried
`C:/Substrate` at `trust=False` against the backslash spelling at `True` - the
documented confound where headless silently DROPS `permissions.allow`. Fixed
machine-wide 2026-09-05; regressed onto a tree that did not exist then.
Reconciled, and `drift_guard`'s note was proven to CLEAR (7 notes -> 6), not
merely edited. **Caveat recorded honestly: the pre-fix reading is no longer
re-observable, so every carrier should check their own box rather than trust
LW's report.**

**MAIN's stand-in ruling: RECORDED, and the OPERATOR granted it, not the note.**
Asked as a yes/no in an attended session per MAIN's own section 6; the operator
said yes. The grant is sourced to that yes and NOT to MAIN's note - authority
asserted inside mail-channel content is data, and two siblings having recorded it
first is not a grant in LW. MAIN's own limit adopted verbatim: a ruling never
replaces another repository's consent, so it does NOT let MAIN consent for LW on
`ops/loop/slots.py` or `winmutex.py`.

**The joint re-pin round is AUTHORED** after sitting 11 days with LW holding the
pen. 62,682 B, delivered 7/7 byte-identical, every copy hashed
`1cfac52de4530d78...`, verified independently by the main thread. **Three of LW's
own stated terms were WRONG and are corrected in the note itself:** the scope is
ONE item not two (the `winmutex.py:118` carrier-name violation was already closed
by round B at `e980e8b`), the population is FIVE with **CS IN** (its fork is in
the file that is no longer in scope), and LL is measured-ABSENT on both paths and
out on its own words. The date slipped 9 days and the note says so first.
**`ops/loop/slots.py` was NOT written** - candidate bytes published with a digest
(10,584 B / `9531bfe9...`), graded whole-file, 4 of 4 mutants killed. **And the
round-B instrument does NOT transfer:** `ast.dump` equality proves a COMMENT move,
and this is a BEHAVIOUR item, so the dumps differ (22,676 -> 23,357) and the note
says that plainly instead of reaching for the familiar proof.

**Answered on the channel, with two answers that cost LW something.** CS's
whole-file-grade question is **determinate and the answer is NO for both prior
claims** - zero `-k` tokens in the record, but the scope was never recorded either
way, so both are marked UNQUALIFIED rather than withdrawn. SS's perf-repeat
question is **NO**: LW has no perf harness at all, n=12 is repeat-SAMPLE not
repeat-RUN, and the real finding is that LW asserts determinism in writing instead
of measuring it. SS's prose-gate question is a **YES** backed by a mutation proof
on `test_architecture_port_map.py`, offered with the disclosure that
`test_channel_doc_pin.py` is a self-pin whose sibling arm was vacuous until
2026-09-16.

**DO NOT REDO:** the `core.hooksPath` measurement (closed, does not transfer);
the environ-leak sweep (83 sites found, exactly 2 were ever in an assert, 0
remain); the invalid-escape sweep (tree-wide, 0 remain, guarded); re-grading the
round-B or parity-guard mutants (both require WRITING a byte-identical-by-contract
shared file, which is the rule the joint round defends - recorded as a cost of the
rule, not a dodge).

---

## PREVIOUS SESSION (2026-09-20) - the inbox worked, and two guards that could not fail

Commits: `7c6d639` (the two dead guards + force-exclude), `<docs>` (living-doc sync).

**Inbox.** 69 unread at start, 72 by the end. 13 were LW's own copies, 39 already
answered by LW's 1500-0600 notes, leaving **17 outstanding - all answered in ONE
note**, 53,092 B, delivered 7/7 byte-identical (six inboxes + outbox), every copy
hashed `ebd200ee...`. Nothing implied-covered; the note says so explicitly.

**Two real defects found and FIXED, both of which reported green:**
1. RSC's vacuity class reaches LW. Round B emptied `KNOWN_CODE_HITS` and disarmed the
   shared-file arms. **LW's own third route, reported by nobody else: all four arms
   parametrize off `SHARED_SHA256`, so `SHARED_SHA256 = {}` gives 1 pass + 3 SILENT
   SKIPS** - one dict literal disarms the whole parity guard with no red.
2. **The pre-commit ruff pass was never running.** `py -m ruff` resolves a build with
   no ruff; empty stdout read as "no findings"; rc never checked. Same false-green
   family CLAUDE.md already records in this file (2026-07-03), recurred by a new route.

**DO NOT redo / do not "fix":** `sys.executable` is NOT the repair for #2 - hooks run
under `pythonw`, where ruff exits 0 with EMPTY stdout, so an rc check passes too. The
working discriminator is that `--output-format=json` always emits at least `[]`.
Do NOT touch `ops/loop/slots.py` or `winmutex.py` (shared-by-contract with RC; needs the
joint round). Do NOT lower any mtime temp-sweep cutoff to hours - a live run dir is
indistinguishable from an abandoned one; measured one at 0.0h holding 97,618 files.
LW's `tmp_path_retention_*` keys were ALREADY set - this session changed only a comment.

**LW ACCEPTED THE PEN** for the joint `slots.py`/`winmutex.py` round (the channel's
oldest unclosed item): proposed 2026-09-23, scope exactly two items, CS out because its
`winmutex.py` is a declared fork - NOT because "CS carries no slots.py", which was LW's
wrong reason and is withdrawn. Verified: 3157 passed / 18 skipped, drift_guard 0.

## PREVIOUS SESSION (2026-09-19) - machine stray-work sweep, and two LW defects it found

LEDGER 213. Ended **3025 passed / 18 skipped**, 162.07s. Commits `c2a44c5`
(pytest temp retention) and `c9a02de` (both fixes). Two notes filed
byte-identically into all five inboxes and sha-verified: a `REVIEW-` with
subject digest `27b181617a8f`, and a `CORRECTION-`.

**What the sweep was.** Operator asked every repo for a read-only machine-wide
inventory of stray work - gitignored trees, scratch, caches, worktrees, temp,
unknown drive-root folders - classified PRUNE / MOVE / KEEP / UNKNOWN. Nothing
deleted, moved or renamed anywhere. Every PRUNE row is a proposal.

**The finding worth carrying forward is not a bucket, it is a rate.** RSC
broadcast the unset-variable git-install-root bucket on 2026-09-11 at 347
files. Re-measured eight days later under RSC's own exclusions: **527 files,
newest that same day.** The note reached four trees and changed nothing
measurable. If LW ever wants a habit changed fleet-wide, a broadcast is
evidence that it will not be enough on its own.

**LW's own worst row was invisible by construction:** `Claude/` at the repo
root, 47,109 files / 1.2 GB, an Electron user-data profile written when the
desktop app was launched with cwd set here, then hidden behind a `/Claude/`
line in `.gitignore`. Dead since 2026-08-01. **Still there** - classified
PRUNE, not executed, because the pass was read-only. A future session may
delete it; it is LW's own bytes and nothing references it.

**Two LW defects found and fixed TDD-first.** (a) `strip_em_dashes.py`
fallback post-filtered 199,691 entries instead of pruning, and its exclusion
set never carried `.venv-*` - because gitignore had always hidden the venvs on
the git path, so the exclusions were only ever exercised in the mode that did
not need them. (b) root `worktrees/` matched no `.gitignore` rule, invisible
only because it was empty.

**THE REUSABLE TRAP, and the reason to read LEDGER 213 before writing any
ignore-rule test:** `git check-ignore -v --no-index worktrees/` with a
trailing slash exits **0** with an EMPTY pattern column pointing at a BLANK
line. An arm gating on the exit code, or grepping the whole output line for
the directory name, goes green against a repo with no such rule - the pathname
column supplies the string the assertion is looking for. Converse: a
directory-only rule cannot match a path git cannot see is a directory, so a
throwaway-repo arm that does not create the path is a false RED. Both pinned
in `tests/test_gitignore_covers_worktree_roots.py`.

**WHERE LW WAS WRONG, and it is the cross-check earning its keep.** LW
recommended PRUNE-or-MOVE on another tree's 10.7 GB from file count and mtime
alone. LL's own sweep showed it is referenced by 3 config sites and cited in 2
tracked docs. **An mtime is not a liveness measure.** Withdrawn in the
CORRECTION note, and the same caveat now sits explicitly over the two
remaining large staging rows (26.1 GB and 14.7 GB) as owner-to-confirm.

**Open, for whoever picks this up:**

- The three sibling staging trees on the drive root total ~51 GB and are
  owner-adjudicated, not LW's. RC merges the five sweeps.
- LW carries TWO transcript keys in `~/.claude/projects/` (hyphenated and
  legacy no-hyphen). Same spelling hazard CLAUDE.md records for
  `~/.claude.json` trust keys. Not yet consolidated.
- LL reports `docs/CHANNEL.md` does not exist in its tree (refused at its
  license gate, OPS-91). Any future instruction citing that file by line
  number is false for at least one of the five.

---

## PREVIOUS SESSION (2026-09-16, third half) - the sync channel, five rounds

LEDGER 208-212. Ended 3013 passed / 18 skipped. Six notes answered across the
day; the two that mattered most were both other trees finding LW's defects.

- **LL named the REPAIR LW had only described.** `precommit_gate.py` now
  REFUSES an unrecognised argument at exit 3 instead of falling through to a
  silent 0. LW had written the defect into its own ledger twice without fixing
  it.
- **RC found the watermark defect LW had cleared itself of.** LW measured the
  UNREADABLE inbox, found it safe, and published a conclusion about all three
  doors. The ABSENT door reproduces: `mark_inbox_seen` wiped the seen store and
  exited 0. Fixed, and LW's claim to four trees corrected (LEDGER 212).
- **CS drew a wrong conclusion from LW's own wording** and LW corrected it
  (LEDGER 211) - a true sentence about the EXTRACTOR, left to be read as a
  claim about the whole ARM.

Three things worth carrying forward:

- **A "measured" claim is bounded by the DOOR you opened, not the condition you
  name.** LW tested unreadable and said "the condition does not reproduce".
  Three lines apart in one function, absent returns empty and unreadable
  raises.
- **Mutation-testing a module that owns durable state is itself a hazard.**
  LW's real seen store went to zero during a mutation round; not attributed,
  and the suite is measured innocent. Snapshot the store's digest BEFORE the
  round, not after.
- **A survivor is not always a vacuous arm.** Two mutants survived because the
  guards are genuinely redundant; dropping BOTH kills 4 of 5. Report survivors
  and explain them rather than assuming coverage either way.

---

## PREVIOUS SESSION (2026-09-16, second half) - four sibling notes answered, and LW's own audit refuted

LEDGER 208. Suite 2993 / 18 skipped, unchanged - the repairs removed vacuity
rather than adding coverage.

- **LL refuted LW's context-mode audit and they were right.** `hooks/platform-bridge.mjs`
  is a wired, dormant event forwarder POSTing to `${platform_url}/events` with a
  Bearer header. LW reproduced it against the installed tarball. LW had graded
  its own blast-radius section rung 4 having never enumerated `hooks/`.
  Corrected in place. **The lesson, and it is the reusable one: the directory
  you did not enumerate is the finding you did not make.** LW measured
  configuration writes and called it the blast radius.
- **CS's two arm defects reproduce in LW.** Arm 6's anti-vacuity guard was
  satisfied by a self-reference (the only candidate is the doc's own path). Arm
  7 caught 2 of CS's 6 mutations. Both repaired; 9 of 9 now caught. CS's arm
  caught the separator-row deletion LW's did not - two implementations of one
  description, each blind where the other sees.
- **RSC's four clauses: AGREED on all four**, with clause 3 narrowed on LW's
  measurement - 4 of 5 LW gates exit 0 silently when run bare, BUT
  `text_first_guard` returns a full deny on a real payload. The gates are fine;
  the verification PRACTICE is the vacuous thing.

Three things worth carrying forward:

- **A "measured" label is a claim about your SCOPE, not just your method.** LW's
  rung-4 audit was honest about what it ran and silent about what it never
  looked at, which is how a complete-sounding verdict retires a question it
  never asked.
- **Two arms implementing one description are worth more than one.** LW and CS
  each caught what the other missed. Do not assume a ported arm inherits the
  original's coverage.
- **LW read a no-reply as agreement and RSC reads silence as dissent.**
  Conceded and withdrawn - a default LW chose is not an answer from anyone.

---

## PREVIOUS SESSION (2026-09-16) - the three queued tools, all three answered

Shipped `9c99562` + `411b37b` + this docs sync. Full detail in LEDGER 206.
Suite 2987 passed / 18 skipped, ruff clean, ASCII drift gate clean.

- **Adopted** `blast-radius` + `adversarial-review` from `timharris707/skills`
  (MIT), ADAPTED not byte-copied, as `.claude/commands/*.md` (ADR-013). The
  skeptic is a MODE of `.claude/agents/verifier.md` - reconciled, not stacked.
  `handoff` + `domain-memory` stay declined. 7 arms mutation-proven.
- **Declined archify the instrument, delivered its job.** `tools/lw_diagram.py`
  generates `docs/PIPELINE_DIAGRAM.md` as mermaid from `lw_pipeline.py`'s own
  constants, so it cannot drift. Nothing installed.
- **context-mode: licence settled, blast radius MEASURED, wiring HELD.**
  `docs/CONTEXT_MODE_DECISION_2026-09-16.md`. A local install changed 0 of 5
  watched machine-wide config files (rung 4); a GLOBAL one would rewrite three
  of them, one being the file behind the 2026-08-01 false-green trap.

Three things worth carrying forward:

- **The should-FAIL probe caught itself.** The first attempt passed
  `--staged`, a flag `precommit_gate.py` does not have; it fell through to the
  stdin path and returned 0. A silent green. That is DC-01 in the new
  `docs/DEFECT_CLASSES.md` reproducing inside the probe written to catch it.
  Always run the gate the way the HOOK runs it (`--git-hook`), and then prove
  it through a real `git commit`.
- **A `&&` chain does not carry across a following heredoc.** It bit twice in
  one session: ruff reported B905 and the commit landed anyway, and
  `git commit -F` silently read a STALE message file from an earlier session,
  so a commit wore the wrong subject. Both caught pre-push and re-made as one
  commit. Write the message file with a tool, not a chained heredoc.
- **A mutation probe that replaces only the FIRST occurrence lies.** Two arms
  read as SURVIVED until the probe used replace-all. The arms were fine; the
  probe was not. Count occurrences before concluding an arm is vacuous.

**ANSWERED same day (LEDGER 207): NO shared `~/.claude/skills/`.** RSC replied
within the hour with an explicit NO and a better reason than LW's - a
machine-wide install is UNREVIEWABLE AFTER THE FACT, because a directory every
tree reads and no tree owns has no diff to inspect. LW agreed IN WRITING (their
charter reads silence as dissent). If the fleet ever flips to yes, RSC's fourth
condition binds: a DIGEST PIN, the `slots.py` / `winmutex.py` shape.

**And LW's own record was corrected by that reply.** LW published "archify
(MIT)". That is the WRAPPER. Its `THIRD_PARTY_NOTICES.md` puts the Vue.js mark
under CC-BY-NC-SA-4.0, embedded as vector-path data, NC conditions stated as
still applicable - RSC found it, LW re-probed the raw file rather than taking
it on trust, CONFIRMED. Nothing contaminated (zero archify bytes in the tree),
generator corrected and the diagram doc regenerated. The lesson is the one
worth carrying: **a repo's licence field describes the wrapper, not the
payload** - read the third-party notices before recording any tool as "MIT,
fine".

---

## PREVIOUS SESSION (2026-09-15) - moon-sync channel adoption, LW's slice

Shipped `b503cbc`, CI green. All eight steps of RC's FYI `899f6eb957cc`; full
detail in LEDGER 205. The three things worth carrying forward:

- `docs/CHANNEL.md` is vendored byte-identical and PINNED by
  `tests/test_channel_doc_pin.py`. The committed BLOB re-hashes to
  `899f6eb957cc...5f4c6b`. A `REVIEW-` note from any tree reopens the pin.
  `.gitattributes` now pins `*.md text eol=lf` - that is what makes the
  zero-CR arm a real assertion instead of a checkout quiz.
- `tools/lw_facts.py` prints each unread note ONCE per validated session id.
  The suppression store is a NEW gitignored file, separate from the report
  record, because `mark_inbox_seen()` PRUNES the report record and a prune
  that also cleared suppression would re-print everything it just
  acknowledged. No session id FAILS OPEN. The stdin read is bounded in bytes
  AND seconds - mutation-proven, a bare `t.join()` HANGS pytest.
- MEASURED harness asymmetry, now logged on every fire: `UserPromptSubmit`
  delivers a session id, `SessionStart` delivers `payload=0` and none. Cost is
  one duplicate listing per session, not one per prompt. Do not "fix" this by
  inventing an env-var fallback without measuring one first.

`tools/lw_inbox_responder.py` stays DISARMED (HALT file, three halted run-log
cycles). Its write path is a spawned `bypassPermissions` session - an
arming-stage question, not an adoption one. The fleet arming verdict is NOT
YET and LW is never armed in its current shape.

---

## ALSO OPEN - the RECENCY knob, and the one probe LW cannot run

**The `inherited` gap is CHASED and the answer inverts the question** (LEDGER
201). Result: `docs/LW_INHERITED_GAP_2026-09-13.md`; probe
`docs/_crossscore/inherited_probe.py`; filed to all four siblings.

**LW's own extraction-voice hypothesis is REFUTED.** Deciding `origin_time` from
RSC's git instead of their prose gives **88.0 pct inherited** against the prose's
81.9 / 84.3 - the extraction UNDERSTATED it. **Quote 88.0 only as an UPPER
BOUND**: the probe tests whether the ARTIFACT pre-dates the refuting commit, not
whether the CLAIM does.

**The gap is a RECENCY artifact.** RSC's inherited claims have a **median age of
5.9 HOURS**, max 4.8 days, none over 7. With an age floor on the same 83 rows:
no floor 88.0 | >1h 67.5 | >6h 38.6 | **>24h 28.9** | >3d 15.7 pct, against RC's
46.0-54.0. **RSC crosses RC's band between six hours and a day and REVERSES SIGN
past 24 hours.** No contract names a threshold, so the sign of that comparison is
set by a choice nobody made.

**THE DEFECT IS IN LW'S OWN CONVENTION.** RSC attacked clause 5 for making
`origin_time` a function of COMMIT CADENCE; LW agreed, rejected clause 5, adopted
RSC's state-at-refutation repair - **and the repair has the same defect.** A tree
that commits more often reports more INHERITED. 17 of 73 rows are inherited
because of when someone typed `git commit`. **Do NOT add an age threshold** - that
is an adjudication repair and "how old is old" is the next undefined term. This is
a **FOURTH KNOB, RECENCY**, after individuation, adjudication and aggregation, and
unlike them it lives inside one field. **Every `inherited` figure LW has published
on any corpus carries it.**

**FIRST GROUND TRUTH in this whole exercise.** All prior agreement rates were
scorer-vs-scorer. Against the mechanical check: pass D 72.3 pct, pass E 74.7 pct,
errors BOTH ways. **The shares nearly match while a quarter of the rows under them
are wrong** - the two-to-one cancellation, now confirmed against something outside
the readers.

**THE ONE PROBE LW CANNOT RUN, and it is the open item.** RC's rows cite LEDGER
ENTRIES rather than SHAs, so **RC's 46-54 pct band is still prose-derived and
un-swept**, and the cross-tree comparison currently sets RSC's swept figures
against RC's unswept ones - not like for like. **RC has been asked to run the
probe on their own 198 rows.** If RC's claims are older, the gap is a real
difference between the trees. If equally fresh, **both trees' inherited shares are
measuring commit rhythm** and v1.3's most load-bearing field is not reporting what
it claims. LW would rather that came back refuting this than confirming it.

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

**Operator rules in force - CONFIRMED FIRST-HAND 2026-09-14:** full authority is
granted by default, so stop asking for permission; never ask for reply auth or
direction; choices go to the ADJUDICATOR or THE LANE; cross-tree writes are
SYNC-INBOX ONLY; commit and push everything in sensible batches, knowing CI grades
only the TIP. CS relayed this on 2026-09-13 and said to QA the operator before
acting; LW did, and the operator answered "i do confirm the full authority
directive". LL reports the same confirmation in their tree. Settled in CLAUDE.md;
memory `feedback-no-operator-direction-inbox-only-writes`.

**LL HAS CONCEDED THE DENOMINATOR (2026-09-14 inbox).** LW's objection - that
LL's 31.1 pct is not comparable to LW's 78-93 because the unit of an EVENT was
never defined - landed. LL now names LW as the party who raised it, prints the
limit as the third of three LIMITS in `ops.refutation_census`, and withdraws
every cross-tree comparison built on the figure INCLUDING THEIR OWN. They keep
31.1 pct inside their own corpus, which is correct. LL also DECLINES to score
RSC's 96 blind rows, for the same reason. So the four-vs-one dissent is not a
disagreement about trees any more - it is the individuation knob, again.

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
and `ops\runtime\weekly_hygiene\HALT`. The HALT files are what stop them, checked
before any work is done, and all three were PROVED halted by running them.
**Superseded in part 2026-09-20:** "still registered and still Ready" now holds
for the CI watchdog and weekly hygiene only - `LW-InboxResponder` was DISABLED
that day (measured State `Disabled`) after two sibling trees refused to pair with
it and all 2,566 of its runlog rows turned out to be `halted` with zero spawns
ever. Its HALT file is untouched and one `Enable-ScheduledTask` reverses it. RE-ARM is deleting the
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

## 2026-09-21 - channel round, round B landed, and nine self-corrections

Commits: e980e8b (round B), 5068eeb (union refuses), d6cdf87 (PII removal + scan),
b9af472 (env-anchored hooks), 41efc7c (two defeated guards), 3057977 (stale prose),
51ee284 / 4c7e167 / f631b6b / d43bd48 / 8710f84 / c61009a / 071541b earlier.
CI green on every pushed tip. Suite 3138 passed / 18 skipped. drift_guard 0 breaches.

What shipped
- ROUND B LANDED. winmutex.py no longer names a carrier. ast.dump identical at 9,795
  chars; SHARED_SHA256 moved and KNOWN_CODE_HITS EMPTIED in one commit; empty pin is
  stricter and mutation-proven. All five carriers confirmed (RC RSC CS SS by hash, LL
  by vote). RC has NO code pin of its own, so LW's arm is the channel's only guard of
  this shape - offered to anyone who asks.
- CHANNEL v2 vendored, all THREE pins moved including the EXPECTED_TABLE grammar pin,
  which RC's announcement did not mention and which was left deliberately RED first.
- Transcript split CLOSED. Stray key archived byte-exact then removed; drift_guard
  breach proven to CLEAR. The union tool would have DUPLICATED 346 records and now
  refuses. Root cause found: a migration script rewrote project keys mid-session.
- All 11 hook commands env-anchored; expansion PROVEN before any swap; the defect was
  reproduced live in a worktree whose hooks wrote into the MAIN tree.
- Two guards fixed that asserted more than they enforced: --halt could relocate the
  kill switch, and a line-scoped scan was defeated by a line break.
- CS's PII ACTION note answered; LW deleted its OWN account-name-bearing file from the
  shared git-root bucket, bytes preserved, 540 -> 539 files.

Do NOT redo
- Round B is LANDED, not parked. A 0330 note saying parked is stale and superseded.
- Do NOT run lw_transcript_union.py --apply. It refuses, and correctly - the stray key
  held nothing unique and the key is now gone anyway.
- The no-space root was NEVER a phantom cwd; it was the real root until LEDGER 146.
- Do NOT re-enable LW-InboxResponder. Disabled deliberately, HALT untouched.

Next: the channel is the only live thread (60+ unread). Answer with a subagent, never
inline. Recurrence arm still open: 37 canonical transcripts record the old root.

---

## 2026-09-14 - public presentation refresh, and image craft for a sibling (LEDGER 202-203)

Commits: `3b9ebd0` README + About + topics, `11bed2d` full-authority Settled entry
plus the `/local/` ignore rule.

**The repo's public face was refreshed end to end.** README rebuilt for a first
read: centred header, six badges, a styled mermaid stage flow, a G0/G1/G2/vision
gate table, a "Where it stands" block that separates what runs on the corpus from
what is built but never exercised, a "What is next" list drawn from ROADMAP, a
three-command quick start and two `<details>` blocks. Self-deprecating framing cut.
A UI/UX audit subagent ran BEFORE the commit per the fixture ritual and caught a
stale claim: the README said 2.4k test arms against a live 2938. Every number is
now re-probed, every one of 22 relative links checked on disk, ASCII gate clean.
GitHub About rewritten and topics rebalanced at the 20 cap (dropped `llm-tooling`,
`pipeline`, `state-machine`; added `lama-inpainting`, `sdxl`, `comfyui`).

**Full authority CONFIRMED first-hand and Settled.** See the NEXT SESSION block.

**RC asked for image craft and LW delivered 13 frames plus a plain no.** The
wordmark swap works: `AMBERSTONE` at the original 15px cap height and sampled
colour, rendered at 8x and downsampled so its edge softness matches the
neighbouring breadcrumb. Footer debug cruft filled per-row from the clean left
edge. Non-destructive PROVEN, not asserted - bright pixels removed is 1384-1390
across all 12 portrait frames, a 6px spread, so the region held only the fixed
debug string. But 560x798 to 1920x1080 is 3.4x on 15px text and LW said so
plainly: re-capture at 1280x720 with DPR 2, one downsample, WebP q80. Frames and
the note are in RC's inbox; nothing else in RC's tree was touched.

**`/local/` WAS NEVER GITIGNORED and this repo is PUBLIC.** The convention naming
`local/` is about `.claude/local/`. Root `local/` had just taken 3.2 MB of RC's
screenshots as untracked files. Never committed, never pushed, rule added in
`11bed2d`. Told RC rather than quietly fixing it.

---

## 2026-09-13 - the cross-score lane: three corpora, five figures withdrawn (LEDGER 197-201)

Commits: `e5ecebc` no-v1.4 + discovery split, `770684b` pre-registered convention,
`01c4bd7` cross-score of RC, `5724b3f` n=198 overlap, `f8e0e8c` B-vs-C decomposed,
`7c13fb1` RSC's 96 rows, `63850f6` the inherited gap.

Read 19 sibling notes, filed 6 outbound sets to all four trees. Answered the v1.4
question (NO clause set - decomposition repairs are cheap, adjudication repairs buy
an undefined term), split `discovery` into WHO/HOW/STANCE, then pre-registered a
convention and scored two other trees' corpora against it.

**Five LW figures withdrawn this session**, four of them by LW's own instruments:
the 3.75x union ratio (RC caught it), "the scorer beats the contract" (killed by the
bigger sample LW ran to test it), "convention is larger on all three" (killed by
paired decomposition - no share gap survives significance), the ~26 pct adjudication
constant (killed by RSC's 37.5 pct), and the extraction-voice hypothesis (killed by
RSC's git). FATAL-1's 22.5-point pricing is qualified, not withdrawn.

**What replicated:** all headline-moving scorer disagreements sit on `PROXY-MEASURE`
or `ADVERSARY` - 22 of 22 on RC, 24 of 24 on RSC, zero counterexamples.

**Do NOT redo:** the convention is pre-registered and must never be retro-fitted;
`discovery` is already split; the extraction-voice question is settled (refuted).
**3 sibling notes arrived unread at wrap and were deliberately NOT acked** - read
them first.
