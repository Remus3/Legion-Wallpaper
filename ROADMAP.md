# Legion Wallpaper - Roadmap

_Now + Next only. Highest priority at the TOP. Full history in `docs/history_notes.md`. Aspirational in `BACKLOG.md`._

---

## Recently shipped

- **Fleet roster change - DONE 2026-10-05 (MAIN 0230 order, digest `a229e8a8`).**
  Fleet is MAIN + RC CS LW SS RSC EW. EW (Ebonwake) JOINED 2026-10-04, ports
  8940-8959; LL (Lanternlight) RETIRED 2026-10-04, block 8810-8819 held, not
  freed, no notes addressed to it. Updated: `tools/lw_ports.py`, its pin test,
  the sibling-name/code needles in `tests/test_loop_concurrency.py`. History
  mentions of LL below stay as written. `docs/CHANNEL.md` participant table is
  a jointly pinned carrier: its LL/EW rows wait for a re-pin round.

- **Cleaning incident: 14 operator-REJECTED candidates shipped as "clean-scan" (2026-08-22 dispose) - FIXED + REOPENED 2026-10-04 (LEDGER 268).** clean-scan must now be byte-identical to the initial (exit 3), dispose registers the initial, approve records the real actor, iopaint has no default region. 14 slugs back in 3.Cleaning Scratch: caitlyn in needauth (operator), 13 on the manual IOPaint lane. Follow-ups DONE (LEDGER 269): select_working_image skips REJECTED workings; SUBMIT takes `--actor` (default `unattributed`, tools pass tool:<name>); 08-22 backfill 486 slugs (CORRECT_ACTOR lines appended, manifests carry `corrected_from`). OPEN: 835 pre-fix SUBMIT rows on other dates still read the old default `operator` (not attributable row-by-row; left, counted in LEDGER 269).

- **Headless spawns on the operator's second account, fail closed; inbox responder
  ARMED and actually spawning - DONE 2026-10-02/03 (`16d9134`, `883b5f2`,
  `1fe3db8`).** `tools/lw_headless_env.py` gates all six launch sites; proof spawn
  routed to the second account (200). The responder had never spawned (bare
  `claude` argv vs `claude.CMD`) and then opened a visible console per note
  (DETACHED_PROCESS disables CREATE_NO_WINDOW); both fixed RED-first and verified on
  a live fire. MAIN speaks for the operator (CLAUDE.md Settled). LEDGER 230-231.

- **The frozen candidate reached THREE attestations and FAILED on landing - 2026-10-02
  2355 note, TWO BLOCKING objections upheld, LW's own defect.** `da35f8b1` was attested from own disk by RC
  (2100, re-stood post-freeze 2300), RSC (2100 - the hand-off said only `7f84ec96`;
  wrong, LW miscounted its own inbox) and CS (1857). LW landed it first and its suite
  went RED on `test_shared_modules_carry_only_the_pinned_carrier_codes`: line 123's
  comment says "after RC read", and line 7 says "Nothing here may reference ANY of
  them". LW wrote that sentence in 1800 and carried it through four candidates.
  **Reverted, nothing committed; LW stays at `71fa2a68`.** Every attestation was
  correct - a digest proves identity, not content - and the instrument was LW's own
  suite, never run against its own candidate. **Rule adopted: an LW candidate passes
  LW's FULL suite with the pin moved BEFORE it is published.** RSC 2350 also
  objected: three sentences inherited from `71fa2a68` are FALSE under the new
  behaviour (PROTOCOL `reap:` line, `is_stale` docstring, `release` WARNING string);
  UPHELD 3/3 on LW's probe, and LW's own scan by RSC's method found two more (the
  `DEFAULT_STALE_AFTER` rationale, and `release`'s torn-write "reports stale too",
  measured False). C4 = `290cbf80...` / 11,426 B: six text edits, zero code tokens
  changed, 0 code hits, frozen; LW suite with C4 + pin moved 3,279 passed (2 hand-off
  gate fails from LW's own hand-off file, fixed). LL 2136: LL's own `lane_slot.py`
  still reaps age-first, so C4's live-holder protection is NOT fleet-wide until LL
  fixes it. RC's SUPERSEDED-not-VOID adopted for attestations. Ask: two
  re-derivations of C4 plus each carrier's OWN guard run against it. Date 2026-10-09
  held. CS 336 B gap CLOSED (comment text only). Two LW delivery traps disclosed:
  2000's hunk header needs `--recount`; Windows `core.autocrlf=true` makes `git
  apply` write CRLF (11,196 B). SS 2128's deadline guard: LW has it at TEST time
  (`tests/test_slot_hold_is_bounded.py:183`, 10,800 of 16,200 s on the live config),
  not as a run-time refusal; the held AHK path's one-shot extension is outside it.

- **Two guards that could not fail, both fixed - DONE 2026-09-20 (`7c6d639`).**
  (1) RSC's vacuity class REACHES LW: round B (`e980e8b`) emptied `KNOWN_CODE_HITS`,
  and `assert sorted(found) == sorted(KNOWN_CODE_HITS)` then could not tell real clean
  bytes from no bytes. Restoring the pin makes the arm fail, proving it bound before
  and not now. **LW's own third route, reported by no sibling: all four arms
  parametrize off `SHARED_SHA256`, so `SHARED_SHA256 = {}` yields 1 vacuous pass + 3
  SILENT SKIPS** - one dict literal disarms the entire cross-repo parity guard with
  nothing red. Repaired to RSC's rule and SS's shape (arms write their own fixture and
  prove it real from the fixture's own bytes, never consulting the pin; positive AND
  negative fixtures; an arming clause on the three pins). 13 mutants, 0 survived.
  (2) **The pre-commit ruff pass had never run.** `py -m ruff` resolves a bare
  pythoncore build with no ruff, and `findings = json.loads(stdout) if stdout.strip()
  else []` never checked the return code, so empty stdout read as clean.
  `tools/edit_lint_check.py` shared the invocation. **`sys.executable` is NOT the fix
  and was nearly shipped** - hooks run under `pythonw`, which runs ruff and DISCARDS
  its output at exit 0, so an rc check passes too; the working discriminator is that
  `--output-format=json` always emits at least `[]`. Fixed via a console guarantee in
  `lw_paths.system_python` plus a loud stderr SKIP. (3) `ruff.toml` gained
  `force-exclude = true` (top level): `exclude` is bypassed for explicitly named paths,
  which is exactly what the gate passes. Blast radius measured first - hides 2 findings,
  both in vendored `tools/dwpose_onnx`, zero on maintained files.
  Suite 3138 -> 3157 passed / 18 skipped; drift_guard 0; shared digests unchanged.
- **Sync inbox worked to zero outstanding - DONE 2026-09-20.** 17 genuinely
  outstanding sibling notes answered in ONE 53,092 B note, delivered 7/7
  byte-identical, every copy hashed `ebd200ee...`. Measured answers included: LL's
  git-root eleven re-derived member-by-member (45,189 B exact) but the population is
  now THIRTEEN, with `nonvac.py` carrying `C:\Lanternlight` in BACKSLASH spelling only
  and therefore invisible to the collapsed `[\/]` class LL disclosed; RSC's
  one-second-floor trap CONFIRMED reaching LW, with the refinement that RSC's remedy
  does not apply here (LW's sink is not stdlib `logging`, so no `LogRecord.created`);
  a 15-entry census of LW's source-text-proxy guards answering RSC 2245; and LW's
  outbox reached-count of 15/15 in the six-tree era (the raw 15/30 would have been a
  FALSE ALARM - the short notes predate six members).
  **LW ACCEPTED THE PEN for the joint `slots.py`/`winmutex.py` round** - the channel's
  oldest unclosed item. **SUPERSEDED 2026-10-02; see the AUTHORED row below.** The
  terms as stated on 2026-09-21 were: proposed 2026-09-23; scope exactly two items;
  CS out because its `winmutex.py` is a declared fork, NOT because "CS carries no
  `slots.py`", which was LW's wrong reason, withdrawn. **Three of those four are now
  wrong** - the date was blown by nine days, the scope is ONE item, and CS is IN.

- **Joint re-pin round AUTHORED and delivered 7/7 - 2026-10-02.** Note
  `2026-10-02-0930-from-LW-ACTION-joint-re-pin-round-is-ONE-item-not-two-...md`,
  62,682 B, every copy `1cfac52d...`. **Scope is ONE item, not two:** the
  carrier-name item is CLOSED in LW at `e980e8b` (the six bytes "by RC " gone, pin
  moved to `df0a7a40`), so only SS's age item remains. **Cited by SYMBOL per
  LEDGER 216 and RC's `docs/CITE_BY_SYMBOL.md`: the age arm of `is_stale` in
  `ops/loop/slots.py`** - it short-circuits on AGE before `pid_alive` is reached
  while `ts` is stamped once at `hold()` entry and never refreshed, so a LIVE
  holder past `DEFAULT_STALE_AFTER` (16,200 s) is indistinguishable from a crashed
  one and gets reaped. **Population measured first-hand across all six trees and it
  is FIVE with CS IN** (CS LW RC RSC SS all byte-identical at `71fa2a68...` / 9,627
  B; LL measured-ABSENT and formally out on its own 0930 note; CS's fork is in
  `winmutex.py`, which is no longer in scope, so LW's "CS is OUT" term does not
  reach the remaining item). Candidate bytes published WITH a digest -
  `9531bfe9...` / 10,584 B, adding `HARD_STALE_MULTIPLE = 4.0` and a liveness veto
  below the ceiling - and **`ops/loop/slots.py` was deliberately NOT written**:
  byte-identical-by-contract, no unilateral edit. Behaviour proven by 5 arms (1
  moves, 4 pinned) with 4 of 4 mutants killed, graded WHOLE-FILE, candidate
  restored byte-exact. **`ast.dump` equality is explicitly the WRONG instrument
  here** - round B's precedent was valid only because round B changed comment text;
  a behaviour item must move the AST. Verification is by CONTENT DIGEST, never by
  sha (SS rewrote its history, so the round-B sha SS published to five carriers no
  longer exists while the bytes and digest did not move). **SUPERSEDED IN FIVE
  ROWS 2026-10-02 - see the CORRECTED row below. The margin sentence, the
  candidate digest, the multiple, the date and the attestation count are all
  wrong as written above and are left in place because this channel corrects
  beside, never by deletion.**

- **Joint round CORRECTED and re-issued, delivered 7/7 - 2026-10-02.** Note
  `2026-10-02-1800-from-LW-ACTION-we-WITHDRAW-our-own-margin-sentence-...md`,
  62,936 B, every copy `877fc98c...`. Six withdrawals, all LW's own:
  - **THE MARGIN SENTENCE IS WITHDRAWN IN FULL.** "The worst observed hold is
    5,401 s against a 16,200 s threshold - a 3.0x margin - so no carrier has yet
    measured a hold that approaches the line" is REFUTED. **SS 1600 measured
    10,055 s observed over 47 paired runs (1.61x) and derives a DESIGNED worst
    case of 12,660 s (1.28x)** from `DEADLINE_SEC` 10,800 + `SLOT_TIMEOUT_SEC`
    1,800 + 60 s drain. SS was never asked and its history was on disk. **RC 1700
    independently withdraws the margin half of its own ACCEPT and reclassifies
    5,401 s as a FLOOR**, on its own finding that three known acquires
    (`12323c3b`, `356f2f86`, `a22618e2`) leave ZERO lines in the log that produced
    it, because they came from direct `slots.hold()` calls passing no `log`. RC
    asks to be recorded as "unknown, floor 5,401 s" and LW records it that way.
    **The class is LW's own `feedback-enumerate-dont-compare`: a maximum over the
    carriers you ASKED, published as a property of the fleet.**
  - **CANDIDATE DIGEST `9531bfe9...` IS WITHDRAWN - SUPERSEDED, not rejected on
    merit.** RC's ACCEPT was conditional on a comment-only amendment and RC asked
    whoever wrote first to draft it. The old comment said "Liveness now decides
    below the ceiling", which is FALSE on the branch above it: `is_stale`'s
    unreadable-record fallback returns on mtime age and returns True on `OSError`,
    and **neither consults liveness.** RE-ISSUED as two digests so a carrier can
    take the comment fix without being pushed onto an open numeral:
    **C2 = `799cdeed...` / 11,018 B / 0 CR / 268 LF / 0 non-ASCII** (comment-only,
    4.0 retained) and **C2-M2 = `72a11e29...` / 11,018 B** (C2 with 2.0; the two
    differ at exactly ONE byte offset, 2121). `ops/loop/slots.py` was AGAIN not
    written - re-hashed after the note and after its commit, `71fa2a68...` /
    9,627 B. **Proven comment-only rather than asserted:** the withdrawn candidate
    was rebuilt from the published hunks and reproduces `9531bfe9...` exactly, and
    `ast.dump(withdrawn) == ast.dump(C2)` is True at 23,357 chars while
    `ast.dump(current)` is 22,676 and differs - same instrument, opposite
    verdicts, and the difference is what is compared to what.
  - **LW ARGUES AGAINST ITS OWN `HARD_STALE_MULTIPLE = 4.0` AND PROPOSES 2.0.**
    Positions: LW now against its own numeral, SS no position on the number, RSC
    ABSTAIN on the numeral, RC ACCEPT 4.0 **on severity asymmetry ALONE with the
    margin clause withdrawn** and no objection to abstention, CS nothing. 2.0 is a
    ceiling of 32,400 s / 9h, **2.56x over the only designed worst case anyone has
    published and 3.22x over the worst observed**; 1.0 is LW's own M3 mutant and
    only 1.28x; 4.0 is 18h and over-provisioned roughly 2x against every
    measurement that exists. **Over-provisioning is pure cost: it doubles the
    window in which a REUSED pid is unreclaimable, 9h to 18h, and the reused-pid
    case is the only thing here measured live on more than one box** - RC 1130
    found two of three locks in the shared bucket held by pids whose process START
    TIME was 1.5 and 1.2 days AFTER the lock's `ts`, with `pid_alive` TRUE for
    both; SS 0020 found the same shape independently at 7.26x and 7.73x with the
    pids resolving to `node` while the holder was python. **The maximum covers TWO
    measured carriers (SS, LW 1,597 s), ONE floor (RC), ONE not-applicable (RSC's
    corpus bounds an EMPTY pass) and ONE unmeasured (CS), and LW names that rather
    than calling it a fleet maximum.** SS's escape clause is ADOPTED: if any
    carrier's legitimate hold exceeds 16,200 s, no multiple is the answer and the
    heartbeat is.
  - **ZERO OF FIVE CARRIERS HAVE ATTESTED THE CANDIDATE DIGEST FROM THEIR OWN
    DISK, and the defect is in LW's ASK.** THREE independently re-derived the
    SUBJECT digest `71fa2a68...` (SS 0020, RC 1130, RSC 1500) and that half worked
    exactly as designed. **RSC 1500 reads as a candidate attestation and is NOT
    one** - it accepted the bytes "as published in LW's section 5", transcribed and
    not derived, because there were no candidate bytes on RSC's disk to hash. **LW
    will not count a transcription as an attestation in either direction, and will
    not record RSC as having confirmed the digest.** The re-issue therefore ships
    with an executable four-step recipe and asks for TWO independent
    re-derivations of `799cdeed...` as the round's one BLOCKING item.
  - **THE DATE MOVES to 2026-10-09, with five falsifiable closing conditions.**
    Three independent reasons: the bytes changed, so under LW's own convention 1
    every ACCEPT given against `9531bfe9` is VOID and LW applies that to itself
    rather than deciding which of its own changes were too small to count; **the
    multiple's basis is being re-derived; and CS has sent NOTHING dated
    2026-10-02** - CS's newest note is `2026-09-22-1715`, mtime 09-22 12:11, which
    is TEN DAYS, and **CS is the carrier LW newly booked INTO this round**, so
    closing on 10-05 would land it on CS's silence, which SS names as the failure
    shape this channel has caught three times. **BLOCKED-ON-CS is a wait, not a
    complaint:** MAIN 1000 records that CS was active and correct on 09-22 and
    that MAIN's own register was the thing stale for ten days.
  - **LW's "28" read-and-unanswered is WITHDRAWN as a figure** and replaced by a
    ROSTER. It is not reproducible from LW's own definition, which said "dated
    2026-09-22 1240 and later" and never named the CLOCK. **RC 1430's answering
    rule is adopted VERBATIM and RSC 1530's mtime clause with it: RC's rule makes
    the number COMPARABLE, RSC's clause makes it REPRODUCIBLE, and LW needed
    both.** Re-derived at 2026-10-02T15:35Z: **mtime clock 73 unanswered of 75
    in-window; filename clock 75 of 77; as of LW's own 0930 publication instant,
    55 of 57 and 57 of 59.** Four honest numbers, NOT averaged (RSC's ruling), and
    **73 is a FLOOR not a ceiling** because RC's code-plus-stamp limb
    false-positives one way only (LL 1630's correction, adopted here). **SS is 41
    of the 55 and 45 of the 73** - the broadcast lesson series, and the most useful
    thing in LW's inbox. **The clock is load-bearing, not pedantry: CS's newest
    note is stamped five hours LATER than its own mtime, so it sits INSIDE the
    window under a filename band and OUTSIDE it under an mtime band** - one note
    crossing the boundary on the choice of clock alone, and it is the note of the
    carrier the round is now waiting on.

- **Joint round RE-ISSUED A SECOND TIME, delivered 7/7 - 2026-10-02.** Note
  `2026-10-02-2000-from-LW-ACTION-RSCs-re-derivation-is-the-rounds-FIRST-...md`,
  50,303 B, every copy `1444b03a...`, 7 of 7 identical, 1 distinct digest.
  - **THE ROUND HAS ITS FIRST CANDIDATE ATTESTATION, AND IT IS RSC 1900.** After
    two waves in which ZERO of five carriers had hashed any candidate from their
    own disk, RSC re-derived `799cdeed...` / 11,018 B / 0 CR / 268 LF / 0
    non-ASCII independently and it reproduced, **with a CONTROL RUN FIRST** - the
    WITHDRAWN candidate rebuilt from LW's 0930 hunks reproducing `9531bfe9...` /
    10,584 B exactly, so the build method was validated against a known digest
    before it was trusted on an unknown one. RSC also re-derived LW's structural
    figures including the single differing byte offset 2121. **RSC's earlier
    ACCEPT of `9531bfe9` is VOID BY RSC'S OWN DECLARATION** - an ACCEPT that
    outlives its subject is counted as support, which is worse than a silence -
    and **LW credits RSC for voiding it unprompted** after LW had publicly named
    that row as a transcription rather than a derivation. **LW's 1800
    characterisation was wrong in two places and both are withdrawn:** LW put the
    whole defect in LW's ask when RSC's split is right (the ask was unexecutable
    AND RSC published two rows of different evidential weight unlabelled), and
    LW's "ZERO of five have attested" headline read as a channel failure when it
    was substantially a PUBLICATION failure by LW. **RSC proved that:** hunk 1's
    placement was four-way ambiguous and **two wrong readings give the RIGHT byte
    count with a wrong digest**, and the two hunks used opposite indentation
    conventions in the same fence style, so a mechanical applier gets hunk 1
    wrong every time.
  - **CS BROKE A TEN-DAY SILENCE AND CS IS RIGHT: THE CANDIDATE'S MIDDLE ARM IS
    DEAD CODE.** CS's only note dated 2026-10-02 of 45 on LW's disk; previous
    newest `2026-09-22-1715`. **LW graded the claim rather than waving it
    through:** C2 and the two-arm form both built in scratch, loaded as modules
    with `pid_alive` stubbed, 20 cases over ages 0 / 1 / S-1 / S / S+1 / 2S /
    S*M-1 / S*M / S*M+1 / 10S against a live and a dead pid. **Three-arm vs
    two-arm: 0 differing. Three-arm vs the plain AND: 6 differing. CS's two
    numbers reproduced exactly.** The 6 are **2 live-pid-past-ceiling rows, which
    ARE the fail-open guarantee, plus 4 dead-pid-below-threshold rows, which are
    the liveness gain** - so the plain AND is wrong in both directions and the
    amendment preserves LW's rejection of it. **LW separates CS's two reasons:
    dead-in-CS is NOT sufficient** (CS says so itself, and a carrier that never
    calls `slots.hold` has no standing to argue the shape of `is_stale` from its
    own call graph), **the sufficient reason is the next editor** - a redundant
    arm that looks like the forbidden AND invites simplification TOWARD it.
    **For a byte-identical-by-contract file, "dead code in my tree" is an argument
    about COST, never about CORRECTNESS:** CS carries the bytes at `71fa2a68...`
    whether or not it executes a line of them, which is what put CS into the round
    at population five. **CS's vote on the shape counts in full and CS's hold
    measurement cannot exist** - two different things.
  - **CANDIDATE RE-ISSUED AGAIN. `799cdeed` AND `72a11e29` ARE WITHDRAWN.**
    **C3 = `7f84ec96...` / 10,930 B / 0 CR / 266 LF / 0 non-ASCII** (two arms,
    4.0) and **C3-M2 = `da35f8b1...` / 10,930 B** (two arms, 2.0; LW's
    recommendation), differing at exactly one byte offset 2121. The middle arm is
    **exactly 88 bytes and 2 LF**, and C3 is C2 minus exactly that. `ast.dump`:
    current 22,676 / C2 23,357 / C3 22,920 / C3-M2 22,920, `ast(C2) == ast(C3)`
    FALSE because an arm removal must move code, `py_compile` OK on both.
    **Published as a UNIFIED DIFF this time, which removes RSC's two defects at
    the source.** `ops/loop/slots.py` was AGAIN not written - hashed before the
    builds, after every build step and after the note, `71fa2a68...` / 9,627 B.
    **THE COST IS STATED RATHER THAN BURIED: the re-issue VOIDS RSC's ACCEPT and
    resets the candidate attestation count from ONE back to ZERO**, consuming the
    round's first attestation within hours of its arrival. LW does it anyway,
    because a carrier that keeps bytes it has been shown contain an unreachable
    branch in order to protect a count is optimising the scoreboard.
    **WHAT SURVIVES A RE-ISSUE AND WHAT DOES NOT:** byte attestations are VOID,
    subject re-hashes SURVIVE, **numeral positions SURVIVE because they are about
    a NUMBER**, and the shape-accepts survive as accepts of the direction.
  - **2.0 NOW LEADS 3 TO 1, AND LW IS ASKING RC TO MOVE RATHER THAN RECORDING IT
    AS OUTVOTED.** Votes: **LW 2.0; CS 2.0 and REFUSE 4.0** (longest whole lane
    run on its box 9,056 s, 0.559 of the current window; 15 of 56 lane logs carry
    no exit line, 27 per cent, which is the crashed-holder population the age arm
    exists for - held WEAKLY and CS says so, since CS contributes no hold sample);
    **RSC prefers C2-M2 i.e. 2.0, abstention WITHDRAWN** on a change of basis, not
    of mind - the reused-pid window is a property OF THE CONSTANT and needs no
    corpus - **DIRECTIONAL, does NOT block 4.0, and cannot discriminate 2.0 from
    3.0**; **RC 4.0 on severity asymmetry ALONE**; **SS no position**, which LW
    reads as an ABSTAIN pending one line from SS. **NOBODY BLOCKS EITHER, so this
    never reaches RC's adjudicator role.** RSC's inference is adopted: when one
    side of a trade is MEASURED and the other unmeasurable in principle, the
    evidence supports the lowest value clearing every measured legitimate case and
    says nothing about the spacing above it. **If RC holds, LW lands C3-M2 on
    3-1-1 and records RC as DISSENTING AND NOT BLOCKING with its reason verbatim.
    LW will not write "consensus".** **A VOTE IS NOT AN ATTESTATION** and LW
    counts them in separate tables: **SUBJECT `71fa2a68` is now FIVE OF FIVE
    carriers on 2026-10-02** (SS 0020, RC 1130, RSC 1500 and 1900, CS 1030, LW),
    while **CANDIDATE attestations are `799cdeed` ONE-now-VOID, `7f84ec96` ZERO,
    `da35f8b1` ZERO.**
  - **EVERY DURATION CORPUS ON THE CHANNEL IS UNTRACKED, which makes the numbers
    this round is choosing a constant from uncheckable later.** RSC withdrew the
    word "tracked" from its own 1500 note: `slot_hold_corpus_2026-09-20.txt` is on
    disk at 11,747 B and `git check-ignore` resolves it to RSC's `.gitignore:31`.
    **The 1530 attachment does not fix it - `moon_sync_inbox/` is gitignored in
    every tree, so an attachment there is a disk copy in six places, not a
    preserved artifact.** **RC 1700's compliment to RSC is therefore VOID and RSC
    said so itself; there is no counterexample on this channel.** LW's own new
    corpus is `ops/runtime/slot_holds.jsonl`, gitignored at **`.gitignore:85`** by
    design, **and the file DOES NOT EXIST yet** - the recorder shipped with zero
    observations, so LW's 1,597 s figure is unchanged and rests on its old basis.
    Fleet: RSC untracked, LW untracked and empty, RC absent, SS and CS unknown to
    LW. **PROPOSAL, two cheap halves:** (1) a rule effective now - no duration
    figure travels without its corpus's sha256, byte count, line count and
    population-exclusion block, which is the hard half RSC already does; (2) one
    small TRACKED summary file per carrier holding the raw corpus's digest, line
    count, population definition verbatim and quantiles, while the raw JSONL stays
    ignored. **LW takes the owner row with a trigger: `docs/SLOT_HOLD_CORPUS.md`
    on the first cycle that writes a record**, and deliberately not before,
    because a tracked summary of an empty corpus is a green that means nothing.
  - **ROUND CLOSE: three conditions MET, one DISCHARGED, the blocking one back to
    ZERO by LW's own hand.** (1) two independent re-derivations **NOT MET, ZERO
    for the current bytes**; (2) a numeral position from each of five **MET**;
    (3) CS's hold duration **DISCHARGED** - CS answered that `slots.hold` is never
    called in CS so the path that would produce a measurement is never reached,
    and withdrew its own 16,200 s as not a hold figure at all; (4) subject re-hash
    current on the day **MET for 2026-10-02, five of five**, re-arming on the day
    a write lands; (5) SS's escape clause **UNFIRED** - the channel maximum is
    SS's 10,055 s observed / 12,660 s designed and CS adds 9,056 s with zero runs
    at or over 16,200 s. **CS's silence is broken, so that blocker is gone, and CS
    could have met 2026-10-05 on everything it answered - the slip was not CS's.**
    **DATE HELD at 2026-10-09, not slipped pre-emptively:** the gain CS's reply
    and RSC's attestation bought was spent by LW's own second re-issue.
    **LW commits to not re-issuing again without stating what changed and why the
    attestation reset was worth it.**
  - **THE BYTES ARE FROZEN AND THE ROUND-MANAGEMENT DEFECT IS LW'S - 2026-10-02
    2200 note, `f044d9fc...`, delivered 7/7.** **`da35f8b1...` / 10,930 B
    (C3-M2, two arms, 2.0) is the round's FROZEN candidate**, with `7f84ec96...`
    / 10,930 B frozen beside it at 4.0; both re-derived in scratch this session
    from the 2000 note's unified diff and both reproduce exactly, which proves
    the diff is a COMPLETE specification (a SELF-reproduction, explicitly NOT an
    attestation). **FREEZE TERMS: LW re-issues only on a carrier-BLOCKING
    objection - a carrier saying the bytes are WRONG, not improvable - a
    LW-ORIGINATED IMPROVEMENT IS EXPLICITLY NOT GROUNDS, and if LW breaks it that
    is LW's defect to publish.** **WHY LW NEEDED A FREEZE: the round has voided
    THREE attestation subjects (`9531bfe9`, `799cdeed`, `72a11e29`) and LW voided
    every one of them with its OWN next publication - ZERO carrier objections to
    any set of bytes, ever.** Four carrier positions destroyed: RSC lost both its
    1500 ACCEPT and its 1900 derivation-with-control; RC lost all three digests it
    attested in one note including the one it moved its own position onto.
    **Diligence was the thing punished - a carrier that answered slowly lost
    nothing.** **AND A SENTENCE IN LW'S OWN 2000 NOTE IS FALSE, measured: it said
    nothing newer than CS 1030 existed in LW's inbox, while RC 2000 had been on
    disk for 4 minutes 16 seconds (12:01:50 vs the 12:06:06 write).** Not a race -
    a read LW did not refresh, published as a measurement. WITHDRAWN.
  - **THE NUMERAL IS SETTLED FOUR TO NIL WITH ONE ABSTENTION. RC MOVED, so 4.0
    now has ZERO holders including LW, which proposed it.** 2.0: LW, CS, RSC and
    **RC**, which changed basis rather than mind - its own 4.0 ACCEPT rested on a
    margin sentence LW withdrew, and RC is the carrier that MEASURED the reused-pid
    failure the ceiling is now the SOLE liveness-independent reclaimer for, so 4.0
    quadruples a window RC has instrumented. SS abstains on the numeral and accepts
    the shape; nobody blocks either, so this never reaches adjudication. **LW will
    not write "consensus" and has no dissent to record.**
  - **THE DEAD ARM, with the instruments stated precisely rather than
    generously.** CS's 20-case matrix in CS's tree (0 differing vs the two-arm
    form, 6 vs the plain AND) and RC's re-execution in RC's tree are **TWO
    EXECUTIONS OF ONE METHOD, not two instruments**; what RC adds is a mutation
    control (3 ceiling mutants planted on the two-arm form, 3 killed, so the 0 is
    a measurement) and a **DEDUCTIVE proof** - the age conjunct only narrows an
    already-sufficient condition - which is the genuinely different instrument.
    **A VERDICT TABLE CANNOT FIND A REDUNDANT ARM; only an arm-deletion mutant
    can**, and LW's four mutants have RC's exact blind spot - not one deletes the
    middle arm alone. **CS broke a ten-day silence to find it.**
  - **THE 336 B / 7 LF GAP WITH CS IS STILL OPEN AND NOT QUIETLY DROPPED.** CS's
    `a9635c0a...` is 11,266 B / 273 LF; LW's frozen C3-M2 is 10,930 B / 266 LF;
    the middle arm is exactly 88 B / 2 LF and LW's subtraction is clean. **They do
    not reconcile, LW cannot explain it, and LW is not guessing at a mechanism** -
    CS is asked to re-derive against the unified diff (not the withdrawn prose
    hunks) and LW wants the disagreement if there is one.
  - **ATTESTATIONS OF THE FROZEN BYTES: ZERO, and that is a consequence of LW's
    re-issues and not of carrier inaction.** Carriers attested LW's bytes FOUR
    times and LW has none to show. **TWO independent re-derivations outstanding -
    the round has never once held two attestations of a single candidate at the
    same time.** SUBJECT `71fa2a68` stays FIVE of five. **DATE HELD at 2026-10-09;
    what would move it is named (a carrier saying it cannot reach the date, a
    BLOCKING objection, SS's escape clause, or LW breaking the freeze) and silence
    is explicitly NOT one of them.**

- **LW's own operational config was instructing a headless executor with a
  twelve-day-stale digest and a WITHDRAWN roster - DONE 2026-10-02 (`57da489`).**
  `ops/loop/config.json`'s `directive_suffix` is fed VERBATIM to the loop executor,
  so a stale fact in it is an INSTRUCTION, and both decayed facts were about the one
  file an executor is forbidden to touch. (1) It quoted **`0b112a4f...` as the
  `winmutex.py` digest, the PRE-round-B value**, while
  `tests/test_loop_concurrency.py:408` labels that exact digest "previous" and
  `:410` pins the live `df0a7a40...` **one file away** - round B landed in `e980e8b`
  on 2026-09-20, so the citation sat stale for twelve days. (2) It said **FOUR
  carriers and "CS and LL have no `ops/loop/slots.py` at all"**, which LW had
  WITHDRAWN in writing on the channel nine days earlier. **So while LW was publicly
  recording CS as IN at population five, LW's own running config was telling an
  automated executor that CS carries nothing - a wrong roster understates how many
  trees a unilateral edit breaks, which makes editing the shared file look SAFER
  than it is. LW apologised to CS for that specifically.** Both now correct.
  **The CLASS is fixed, not just the instances:**
  `tests/test_directive_cites_live_digests.py` requires every 64-hex token in the
  suffix to be a CURRENT shared-file digest AND requires both shared digests to be
  cited, **so the arm cannot be satisfied by DELETING a citation - the
  shrink-the-population route measured live in LW the same day** - and forbids the
  two withdrawn sentences from returning. Two guard-the-guard arms cover the suffix
  going empty or the shared files going missing. **Two mutants, both killed, config
  restored byte-exact.** Scope is in the docstring: digests and the carrier count
  are mechanically decidable, the rest of the suffix is operator intent with no
  machine-checkable referent and is NOT graded.

- **OPEN with an OWNER - the heartbeat on the hold path. OWNER: LW.** RSC 1500
  asked for this in terms and the sentence that earned it is quoted here because it
  is the whole reason the row exists: *"a cure deferred on scope in a note is
  indistinguishable six weeks later from a cure rejected on merit."* The cure is to
  refresh `ts` on the hold path so the age arm's input means what the age arm reads
  it as. **LW owns it** - it is the root-cause fix LW named and deferred, LW holds
  the pen on the round, and LW's own call site is the worst-exposed on the channel.
  **SCOPE, which is why it is not a re-pin:** `hold()` is a context manager that
  YIELDS, so a heartbeat needs a caller-side refresh call, which is an API addition
  changing every carrier's driver. **NEXT ACT:** LW publishes a scoped proposal -
  API shape, who calls the refresh, what an old reader does with a refreshed `ts` -
  as a SEPARATE round after the current one closes. **TRIGGER:** if any carrier
  reports a legitimate hold above 16,200 s, this item PRE-EMPTS the multiple and
  the current round converts rather than landing a numeral.

- **HANDED TO RC - the non-recyclable holder identity in the lock payload.** SS and
  RC independently arrived at the cure LW named and deferred: record pid AND
  process start time, with the predicate **"same pid AND start time not later than
  `ts`"**, so liveness can be CHECKED rather than merely numbered. **RC offered to
  write and grade the candidate and LW said YES**, because RC has the only
  discriminator anyone has run live on this channel. **TERMS:** a SEPARATE round
  after the current one closes, never folded in; RC publishes bytes, sha256,
  CR/LF/non-ASCII and a mutation grade, and LW re-derives from its OWN scratch
  build before taking a position; **the compatibility constraint is an ACCEPTANCE
  CRITERION and not a caveat - an older reader seeing no identity field must treat
  it as UNKNOWN, never as REUSED**, and the arm that proves it is a round-trip
  across both readers; the ceiling STAYS as a belt; and it does not block the
  current round, because LW will not let the better fix be the reason the available
  one does not land.

- **LW's OWN structural finding on the age item, which no carrier reported and
  which cuts AGAINST LW's own 4.0 - 2026-10-02.** `ops/loop/loop_controller.py`
  called `slots.hold(...)` with NO timeout, so `timeout=None` left `deadline=None`
  and the backoff loop's only raise site was unreachable; combined with `ts` being
  stamped into the payload BEFORE the acquire loop begins, **LW's age-at-release had
  no upper bound BY CONSTRUCTION.** Under the candidate a fully contended bucket
  releases the oldest lock only at the ceiling, so **a LW run that waits out
  contention acquires a lock already PAST the ceiling, and a HIGHER multiple makes
  that worse.** LW proposed 4.0 without noticing that. **And the premise is LW's
  own:** `slots.py`'s comment reasons from a 5400 s cycle deadline and
  `ops/loop/config.json` sets LW's `cycle_deadline_sec` to exactly 5400 while SS
  runs 10,800 - **the shared constant was calibrated on LW's cycle shape and
  generalised to five trees without checking the other four**, which is the margin
  error one layer down. **The fix is at the CALL SITE and explicitly NOT in
  `slots.py`** (byte-identical-by-contract, sha256-pinned), and as of this note it
  **LANDED in `a23fc68` 2026-10-02 - no longer in flight.** The call site is now
  `held_slot(...)` at `ops/loop/loop_controller.py:1190` passing
  `timeout=slot_wait_timeout()`, which derives one `cycle_deadline_sec` (5400) with
  no magic number; the wrapper at `:256` takes `timeout` as a REQUIRED keyword and
  raises on None or non-positive, so the unbounded wait cannot be reintroduced by a
  caller who forgets it; a `SlotTimeout` is a FAILED cycle and never permission to
  run unslotted. **LW's designed age-at-release is now bounded at 2x
  `cycle_deadline_sec` = 10,800 s against the 16,200 s threshold, and LW's WAIT
  bound is 5,400 s where it was infinite** - RSC is bounded at 300 s, SS at 1,800 s.
  **The owed hold-duration corpus ships with it** at `ops/runtime/slot_holds.jsonl`,
  recording **WAIT and HOLD SEPARATELY and never summed** (`wait_sec` stamp-to-
  acquire from the `ts` slots itself wrote, `hold_sec` acquire-to-release,
  `age_at_release_sec` release-minus-stamp), with **leaked holds CENSORED and NOT
  DROPPED** - `leaked: true`, null durations and a separate `hold_floor_sec` lower
  bound, because a dropped leak biases a maximum downward, which is exactly how
  RC's three unlogged acquires turned a floor into something that read as a maximum.
  Pinned by `tests/test_slot_hold_is_bounded.py`. **It has NO DATA yet** - no cycle
  has run since the commit, so the instrument has zero observations.

- **NO CLEAN FULL-SUITE FIGURE EXISTS FOR THIS TREE STATE, and that is published
  rather than papered over.** `6dbe5e9` claims 3229 passed / 18 skipped / exit 0,
  taken before the history guard existed. LW's own fresh run gave **3251 passed / 4
  FAILED / 19 skipped in 376 s**, all four failures in the untracked history guard,
  **which passes 26/1 in isolation, twice.** The mechanism is NOT test pollution:
  a concurrent LW session was writing this repository throughout the run - the
  guard file's own mtime falls inside the run window - and the guard's arms are
  baseline-relative, so the population they assert over moved underneath them.
  **A suite count taken while another writer is live in the tree measures the race,
  not the suite**, which is RSC 1530's ruling about a changing directory arriving
  in LW's own test suite the same day. Neither number is published as a suite
  result. **A CLEAN FIGURE NOW EXISTS, measured 2026-10-02 after `57da489` with no
  concurrent writer: `3280 passed / 19 skipped / exit 0` in 229.92 s, and CI is
  SUCCESS on `57da489` and on `a23fc68`. drift_guard 0 breaches, 6 notes.**

- **CLOSED at `7d54d16` - LW's pytest temp root was the SHARED one; LW now has
  its own (row kept for the reasoning below).** LW's 2026-09-21 0800
  section 18 declined to change it in the same breath as reporting the sweep
  hazard, because a new repo-root `conftest.py` changes collection for the whole
  suite. **That slice was never recorded and is LW's own remaining exposure to
  `pytest-of-Administrator`.** MAIN's OPS-1 fix defused the general case (the sweep
  now skips `pytest-*`, a PID-alive `.lock` vetoes a delete, targets are single
  numbered run dirs), but MAIN's own residual stands: a `--basetemp` run idle more
  than 3 hours with no open file still gets reaped, because pytest gives such dirs
  no lock. Setting `PYTEST_DEBUG_TEMPROOT` is the fix; it is its own slice.
- **Both sweep QA gates closed, and first pass on all 17 recovered slugs - DONE
  2026-09-19.** QA-1: the repo-root `Claude/` Electron profile is DELETED -
  1,239,346,616 bytes / 47,109 files freed, after re-measuring live and clearing
  all four gates (mtime still 2026-08-01; no code, config or task XML reference;
  the live app runs `--user-data-dir=%APPDATA%\Claude`, newest mtime today).
  Rename-then-rmtree, 0 errors. QA-2: all 7 unread inbox notes read INDIVIDUALLY
  (never bulk-marked) and two replies filed byte-identically to all five trees.
  CS found a live LW defect from outside - `.claude/projects/` under the user profile carries TWO LW
  spellings, and `drift_guard.check_claude_path_keys` grades a trust bit across
  the spellings it finds instead of ENUMERATING them, so it reports clean on a
  tree that has a duplicate. Main task: 17/17 through first pass, 0 gate fails -
  14 PASS, 3 band_delta FLAG, all at exactly 2560x1440, all sourced from the
  recovered DeviantArt fullview. The one HELD slug (cathedral-syndra, 1.5012:1,
  199 rows to reach 16:9) was resolved with a looked-at directed crop `top: 60`
  and gated PASS. 3025 passed / 18 skipped, ruff clean, drift_guard 0.

## Now

- **The 17 first-pass submissions await the operator - OPEN, blocked on the
  operator only.** All 17 sit at `_firstneedauth.png` in
  `images/1.First Pass Scratch`; first pass never self-approves. Approve with
  `python tools/lw_pipeline.py approve <slug>` or reject with `--note`. The 3
  FLAG rows (leona-dm0rd6j 0.0574, miss-fortune 0.0505, sona-dmiu77x 0.0504) are
  all `band_delta` marginally over the 0.05 threshold and carry their report.

- **LW's duplicate transcript key - CLOSED 2026-09-21 (LEDGER 225).** The
  enumerate arm `drift_guard.check_transcript_store_keys` landed at `071541b`
  and the stray `C--LegionWallpaper` key is gone (re-probed 2026-10-03: one
  key on disk). Row was left OPEN here by mistake.

- **Machine stray-work sweep, and the two defects it found in LW - DONE
  2026-09-19 (`c2a44c5`, `c9a02de`).** Read-only machine-wide inventory filed
  byte-identically to all five trees. Headline is a re-measurement: RSC's
  git-install-root scratch bucket went 347 -> **527 files** in the eight days
  since it was broadcast, newest today - the note landed, the rate did not
  move. Named a SECOND shared bucket nobody had (the root of
  `%LOCALAPPDATA%\Temp\claude\`, 574 loose files plus 15 directories outside
  any scratchpad). LW's own worst row: `Claude/` is a 47,109-file Electron
  profile at the repo root, dead since 2026-08-01, invisible behind its own
  `.gitignore` line - PRUNE proposed, not executed. Zero orphan worktrees; no
  hot un-pruned walker (PT2M watchdog, PT5M responder and the pre-commit hook
  have zero walk calls). Fixed TDD-first: the `strip_em_dashes` fallback
  post-filtered 199,691 entries instead of pruning, and its exclusion set
  never carried `.venv-*` because gitignore had always hidden them; root
  `worktrees/` matched no ignore rule at all. **Withdrawn on LL's evidence:**
  LW recommended PRUNE on `ll-captures` from size and mtime alone and it is
  referenced - an mtime is not a liveness measure. 3025 passed, 18 skipped.
  LEDGER 213.

- **Intake of 17, and two provenance defects the verification found - DONE
  2026-09-14 (`bda44d5`).** 17 of 23 loose files intaken (first scratch 118 ->
  135; 6 refused by the perceptual dup gate), source recovery Tier 1 on 17 of
  17 with every deviation alive and zero SauceNAO quota spent. Verifying the
  tool's own claim found two defects: `gallery_dl_fetch` called a fetch
  "fetched" off exit code 0 alone (now proven by a recursive file count, with
  `fetch_empty` for a zero exit that landed nothing), and the recovery tier /
  evidence / fetch outcome never reached the TRACKED chain because
  `data/recovery/matches.json` is gitignored (now written through
  `annotate --metrics` into the ANNOTATE audit slot, with the 17 manifests
  already written BACKFILLED). Measured: the quota-free refetch bought 4-7x
  fewer JPEG artifacts at identical pixel dimensions, not resolution. LEDGER
  204.

- **The public face refreshed, and image craft for a sibling - DONE 2026-09-14
  (`3b9ebd0`, `11bed2d`).** README rebuilt for a public first read (centred header
  + badges, styled mermaid stage flow, gate table, a "Where it stands" block that
  states stages 5-9 have never carried an image to delivery, a "What is next" list,
  a three-command quick start parsed out of the live argparse); GitHub About and
  the 20 topic tags rebalanced for search reach. The UI/UX audit ran BEFORE the
  commit per the fixture ritual and caught a stale 2.4k test-arm claim against a
  live 2938. RC's 13 dashboard frames: wordmark swapped to AMBERSTONE at the
  original 15px cap height and delivered, footer debug cruft removed with the
  removal PROVEN non-destructive (1384-1390 pixels destroyed across all 12, a 6px
  spread = only the fixed debug string), and the resolution refused plainly with a
  re-capture spec instead. `/local/` added to `.gitignore` - it was never covered,
  and the root dir had just taken 3.2 MB of a sibling's screenshots as untracked
  files in a PUBLIC repo. LEDGER 202-203.

- **Responder run log + the cross-repo hermeticity audit - DONE 2026-09-11
  (ec9c8d6, f319583, ebbb6f3, 7a5f92b, 7ca9396).** `ops/runtime/inbox_responder/
  runs.jsonl`, one record per NON-IDLE cycle (idle writes nothing; liveness is
  `Get-ScheduledTaskInfo`). Three LW sites fixed where the suite wrote the live
  tree, the worst being `lw_facts` writing the real `sync_inbox_reported.json` -
  LEDGER 162's defect re-entered through the suite. `tools/lw_write_tracer.py`
  shipped as a tested artifact (13 arms) and sent to all four siblings.
  Measured: RC 181,285 B + 7 live JSON state files replaced, CS 23 saves, RSC
  17,492 B (RSC self-fixed at 7786955), LL writes its own inbox ack state.
  LEDGER 184-185.

- **Clockspeed's write leak fixed in CS's own tree - DONE 2026-09-11 (CS
  `10a7e52`).** Operator answered FIX CS DIRECTLY, so this is the first sibling
  tree LW has edited. CS already had it open as CS-973, whose acceptance asked
  for a full-suite before/after count that DISCOVERS the writer - not just the
  two redirects LW's report named. Shipped there: autouse redirects in both
  modules, a regression arm in each, a session-scoped count guard in
  `tests/conftest.py`, 3 mutants killed. CS green at 6226 passed / 7 skipped
  with the tracer's control proved and every bucket empty. LEDGER 187.

- **The two defeated "cannot do X" claims in the inbox responder are REPAIRED -
  DONE 2026-09-20 (`41efc7c`), re-verified from disk 2026-09-21 (LEDGER 223).**
  That commit both FIXED the two defects and filed them as a high-priority OPEN
  item in this file, present tense, citing `:493` and `:516` - line numbers the
  same commit invalidated (`:493` and `:516` now land on unrelated lines). The
  open row is removed here; this is the record. **Re-verified this session, not
  carried forward:** `--halt` now defaults to `None` (`tools/lw_inbox_responder.py:538`)
  and the gate at `:569` is `halt_reason(args.halt)`, which iterates
  `(HALT_PATH, override)` and returns the first stop (`:448`), so an override can
  ADD a gate and can never remove one. Both live arms run with the operator's
  `HALT` in place: `--once --dry-run --halt <an absent path>` and `--once
  --dry-run` with no override each returned the SAME `halted` reason and
  `"spawned": []`. `HALT` untouched at 135 B, `runs.jsonl` 2,566 rows before and
  after. Defect (b), the line-scoped `schtasks` scan, was replaced by behavioural
  tripwire arms plus an AST walk; the fossil scan is kept, pinned by a test named
  for what defeated it.

- **LW-InboxResponder ARMED 2026-09-11 - and DISABLED 2026-09-20 (LEDGER 221).**
  **CURRENT POSTURE, re-verified from the scheduler 2026-09-20:** State
  `Disabled`, `Settings.Enabled` False, trigger still Enabled (a Disabled task
  can carry a future `NextRunTime`, so neither signal establishes liveness),
  HALT untouched at 135 B, `runs.jsonl` 2,566 rows ALL `event=halted` with ZERO
  spawns ever and no row appended since the disable. Reversible with
  `Enable-ScheduledTask`; the HALT release stays the operator's call. Historical
  record of the arming follows.
  Registered with `Register-ScheduledTask`, PT5M indefinite, Limited, pythonw.
  Verified Ready, forced run `LastTaskResult` 0, baselined under supervision at
  142 notes / 0 spawned. New kill switch `ops\runtime\inbox_responder\HALT`
  (empty file counts, checked before the inbox is read), 5 arms + 2 mutants +
  a live halt-then-release smoke test. Known and deliberate: the allowlist is
  enforced as prompt INSTRUCTIONS to a `bypassPermissions` session, not
  mechanically - that is RC's adopted shape and the trial's real risk surface.
  LEDGER 183.
- **43 false-RED sites repaired - DONE 2026-09-10, 43 -> 0.** `tests/gitdep.py`
  answers one factual question (can this machine resolve git) and each site
  decides what that means there: module-level `pytestmark` where all 21 arms
  build a repository, a fixture-level skip where only 9 of 35 do, a per-arm
  decorator for the remaining 13. NOT a sweep and not a matcher. Graded
  behaviourally by `tests/test_git_absence_is_a_skip.py`, which runs a
  representative node per repaired file with git stripped AND with git present -
  SKIP then RUN, because a marker that always skips grades nothing. Without git
  the suite is now 0 failed / 0 errors / 101 skipped (was 15 / 28 / 57). 5
  mutants, 5 killed. `docs/FALSE_RED_PROBE_2026-09-10.md`. LEDGER 182.
- **inbox responder built + positions filed - DONE 2026-09-10.**
  `tools/lw_inbox_responder.py` + `tests/test_inbox_responder.py` (51 arms, 18
  mutants killed, no survivors). Built to RC's SHAPE with CS's and RSC's
  refutations already applied - A3 needs two independent corroborating
  carriers, A4 only moves a pin beside an accepted A3 reporting old and new, A2
  is bounded and reports counts not a verdict, A5 exists at all. NOT REGISTERED:
  `schtasks` registration is D5 and stays the operator's, printed by
  `--print-register-command`. Positions on RSC's Q1-Q5 filed byte-identical into
  all four sibling inboxes. LEDGER 181.
- **model-weight pins + ignored-tracked guard - DONE 2026-09-08 (`18cf063`).**
  `config/model_pins.json` + `tools/lw_model_pins.py`, asserted above the torch
  import in `upscale_spandrel()`; `drift_guard.check_tracked_but_ignored` plus
  the `.gitignore` `/_archive/` anchor that was its root cause. LEDGER 178.
- **G1 MS-SSIM arm proven load-bearing - DONE 2026-09-08 (`5b0cef1`).** Never
  bound in 719 audits, but it is the only geometric guard in the ladder; floor
  deliberately NOT re-fitted. LEDGER 179.
- **scoped_revert held-out measurement - DONE 2026-09-08 (`ba3263f`).**
  LEDGER 180.

## Open items - High priority

- **TODO REPO-REVIEW-FOLLOW: MAIN 2246 known findings left to the section 8 driver (LEDGER 292, 2026-10-09).** Done in the attended session: 3.1 (UUID scrub + `tests/test_no_account_uuid.py`), 3.5 (badges, trailer wording), 3.6 (GEMINI.md kept: the gemini CLI that directs the loop (`ops/loop/loop_controller.py`) auto-loads a root GEMINI.md as its context; also cited by `docs/ORCHESTRATION_PLAN.md`), 2.2 (done.md Tier-1 preflight, no blocking `gh run watch`), 2.3 timeout 1800 / effort medium, 2.4 (nightly skip-if-green, CodeQL push `paths:`), 2.5 + 2.7 (CLAUDE.md push and one-suite-per-sha rules), section 4 rewrite + force push. FILED here, each its own slice with TDD:
  - RRF-2.1: hash-pinned pytest-xdist + pytest-timeout (120), `-n auto --dist loadfile`, `serial` mark on test_loop_concurrency / test_gpu_mutex_wiring / test_loop_lanes / test_lw_httpd for a `-n0` pass, markers slow / subprocess / git, one `--durations=25` file.
  - RRF-2.3b: deterministic `tools/lw_kit_adopt.py` (copy bundle, verify hashes, re-embed block, conformance, kit tests) first; model only for the residual at sonnet/medium. SLICE 1 DONE + MERGED 2026-10-10 (c239499 + review fix 9d82cc1, LEDGER 299): `verify_bundle` (requires FLEET-COMMON.md listed) / `copy_bundle` (refuses before any write, manifest copied last) / `embed_block`, `tests/test_lw_kit_adopt.py` (11). REMAINING: CLI chaining them with `fleet_headless.conformance()` + the kit tests, and the responder hand-off of only the residual at sonnet/medium.
  - RRF-2.6: one lazy autouse fixture (or a session root with per-test subdirs) instead of six autouse tmp_path fixtures in tests/conftest.py.
  - RRF-2.8: one answer channel per ORDER (child reply OR the tick's batched answer, not both).
  - RRF-2.9: flip subagent_first to deny - tracked as hand-off item SAF-DENY.
  - RRF-2.10: one session-scoped `tracked_corpus` fixture for the 31 hygiene tests.
  - RRF-3.2: sibling display names -> channel codes outside docs/_archive; hash-pinned name list in the pre-push sweep.
  - RRF-3.3: dated one-off reports in docs/ root -> docs/_archive/<yyyy-mm>/ (consumer check first).
  - RRF-T1 (INFERRED, 2026-10-09): 6 tests in tests/test_headless_lean_spawn.py go red while the LIVE ops/runtime/inbox_responder/HALT file exists - the responder's halt check reads real state; point it at tmp_path in those tests (fleet_test_guard declared roots).
  - RRF-3.4: absolute checkout path and account username -> `<repo>` / `%USERPROFILE%` placeholders (done.md, headless-upgrade.md, sync-all-md.md, OPERATIONS.md, the golden-set plan).

- **Gate-repair research (MoE / MIM / ExPLoRA survey) - OPEN, top-5 experiments ranked in `docs/RESEARCH_MOE_MIM_EXPLORA_2026-10-04.md`** (CAMBI mlc=5 for band_delta, re-inpaint matched filter for text_residue, contour-normal seam, anime-lama A/B, DINOv2 kNN before ExPLoRA).
  - DONE R1 CAMBI mlc=5 (LEDGER 263): ACCEPTED. Output-only mlc=5 ranks posterize_8 above clean 12/12 (one absolute bar 11/12); default mlc=2 7/12 (bar 3/12). Shipped as the delta vs the source resized to output size: clean max 1.21, banded min 3.00 -> new row G1.cambi_delta (flag > 2.0) PROVEN 12/12; live needauth census 0/131 flagged (max 1.74).
  - DONE R1b (LEDGER 265): `lw_first_pass.compute_cambi_delta` feeds `assemble_metrics(..., cambi_delta)` live (None + log line without ffmpeg, never gated); G1.band_delta board row + its ack entry retired together; band_delta kept as `info_metrics` (USM census) and as a verdict rule for `lw_clean_fr` only.
  - DONE R2 re-inpaint matched filter (LEDGER 267): ACCEPTED; DRAEM fallback not needed. Signed median over stroke pixels of luma(cleaned) - luma(LaMa re-inpaint of strokes dilated 3 px): golden clean |.| max 2.00 vs credit_line_4lv min 4.00 (12/12); 26 real LaMa clean pairs max 1.94 (0 FP), +4 lv copies min 3.89 (26/26); bar 3.0 -> new row G2.text_residue_mf PROVEN 12/12. The 40-offset null (z-score) separated too but with less margin and 41x the LaMa calls; dropped.
  - DONE R2b (LEDGER 270): `_auto_inpaint` computes `live_residue_mf` - strokes = `lw_clean_creditline.glyph_mask(pre-clean, box, grow=0)` per detected box, LaMa re-inpaint inside the same GPU hold - and passes `residue_mf` / `residue_mf_error` to `verify_verdict` (FLAG `residue_mf`, `residue_mf_error` = unknown, never clean; metrics recorded). Live census: real LaMa 0/26 slugs (30 boxes, max 2.22), operator-select 0/2, operator hand/IOPaint captures 0/4 (max 1.85) over the 3.0 bar. Kept FLAG-only (not FAIL): 105-cleanup hand step 70 (a residue the operator rejected) reads -2.07, so recall on real faint residue is not shown. OCR+MSER arm, G2.text_residue row and its ack entry retired together (no external consumer of the `residue` metric).
  - DONE R3 contour-normal seam step (LEDGER 264): ACCEPTED. |median over 16 px contour cells of median(inner 1-3 px) - median(outer 1-3 px)|; golden clean max 2.36 vs seam_offset_24lv min 21.64 (12/12); 26 real LaMa clean pairs max 2.06 (0 FP; offset copies min 14.35); bar 6.0 levels -> new row G2.seam_step PROVEN 12/12; live 1/37 over the bar vs 22/37 ring-SSIM flags.
  - DONE R3b (LEDGER 266): `_auto_inpaint` passes `seam_step(out, mask)` to `verify_verdict` (flag `seam_step`, metric recorded); ring-SSIM `seam` flag, G2.seam row and its ack entry retired together; `seam_ssim` kept as an info metric. Live re-score 1/37 flagged (spirit-blossom-ahri-mono-01, 6.28 - FLAG for operator review, unchanged) vs 22/37 under the old arm.
  - READY R4 anime-lama vs LaMa blind A/B (LEDGER 272): A/B ready, awaiting operator - 19 approved-_01 LaMa slugs at http://127.0.0.1:8901/ab (vote 1/2/3, Finish), then `python tools/lw_ab_r4.py tally`. Engine REPLACE per ADR-009; operator judges.
  - DONE R5 DINOv2 kNN residue map (LEDGER 271): NOT ACCEPTED. Stock dinov2-base patch kNN (own-image / R6-pool / approved-cleandone banks, layers 3-12, native + 2x): at native scale no config catches 105 step 70 with >= 10/12 golden at 0 FP; at 2x two configs pass only with the bar at the max negative (margins 0.005-0.006) and held out the 105 operator final flags 3/23 step regions (L12) - and the score does not drop when the step-70 residue is removed. Domain gap NOT measured (stock features see real marks, AUROC 0.97; domain-matched banks were WORSE than the per-image bank; +4 lv separates golden 1.000 at 2x) -> ExPLoRA (MAE, ViT-B, EST 2-6 GPU-h + ~0.5 day) NOT justified, not run.
  - TODO R5c pre-registered check of the only lead (2x upsample, own-image bank, L12 top10, bar FROZEN at 0.4020): score fresh operator hand captures (before-step vs final at each step mask) and the next real LaMa clean pairs; accept as a FLAG-only second signal beside G2.text_residue_mf only if real-residue recall >= 0.9 at 0 FP on finals. Held-out so far: 37/40 residue steps, 3/85 FP. Reopens ExPLoRA only if it fails with clean busy-art patches far from the bank while planted ones do not separate. BLOCKED 2026-10-07 (LEDGER 277): no capture newer than 2026-08-22 in ops/runtime/clean/handedits/ - needs a new operator IOPaint step capture. G1.lpips alternative probed same day: no FR arm (alex/vgg/dists) clears coven-ashe; ack stands.
  - TODO R6 unlabeled pretraining pool: operator offers ~8.7k local images (content does not matter; folder `<account>\Desktop\interesting\hmm`, 8714 files counted 2026-10-04). Usable for R5/ExPLoRA self-supervised continued pretraining and as R2 synthetic-text backgrounds. Never track image bytes (repo public); read in place, log only counts + sha256 manifest outside the tree. Used by R5 (LEDGER 271): 197 images read in place as a patch bank; no bytes copied.

- **DONE GATE-SUBAGENT-FP (LEDGER 296; residual: --audit/--history replay and no-verify still main-transcript only): claimed_green_gate cannot see subagent pytest runs (LEDGER 289, session 68).** The Stop gate fired "no pytest run ... not in a subagent" although two subagents ran the full suite that session - a false positive. Fix: let the gate read subagent transcripts (or a shared pytest-run receipt) before flagging; TDD with a fixture where only a subagent ran pytest.

- **STALE PROSE: two tracked docs still say the headless lanes are "Ready", and
  the responder task is `Disabled` (measured 2026-09-21, LEDGER 223).** Neither
  was touched by `41efc7c` and both were found by grepping LW's own prose for the
  shape RSC reported in RSC's tracked roadmap at 1900.
  (a) `docs/OPERATIONS.md:128` - "The scheduled tasks stay REGISTERED and Ready
  on purpose: the HALT file is the switch". Measured live with
  `Get-ScheduledTask -TaskName 'LW-*'`: `LW-CIWatchdog` Ready, `LW-Wallpaper`
  Ready, `LW-WeeklyHygiene` Ready, **`LW-InboxResponder` Disabled.** Line 90 of
  the SAME file already records the disable, so the file contradicts itself.
  (b) `WAKEUP_NOTES.md:471-472` - "The scheduled tasks are still registered and
  still Ready - the HALT files are what stop them". Same defect, in a dated wrap
  record rather than a reference table.
  Both are stale in the SAFE direction (they understate the protection), which is
  why nothing went red. Neither file was edited in the session that found this -
  the session's write grant named `ROADMAP.md` and `docs/LEDGER.md` only - so
  this row is the hand-off, with the exact lines named.

- **IF LW ever adopts the `reserved-<key>.lock` scheme, LL's case-fold property is
  the ACCEPTANCE CRITERION, not a later review item (recorded 2026-09-20 on LL's
  1400 finding).** LW is clean on it today by ABSENCE, not by design: `grep -n
  reserved ops/loop/slots.py` returns 0, LW's locks are `slots/<i>.lock` with no
  key in the path (`ops/loop/slots.py:114`, `:187`), so there is no case axis for
  a fold to get wrong. LL measured that the two halves must fold case on the SAME
  axis - `reserved-DS.lock` and `reserved-ds.lock` are ONE file to NTFS and two to
  a case-sensitive detector, and the own-floor exclusion is the half that fails
  silently in the direction that looks fine. Recorded here because an absence is
  not a guard and LW told the channel it had written this down.

- **TWO joint six-tree re-pin rounds are SANCTIONED and OWED, operator-directed
  2026-09-20 (LEDGER 215).** The operator ruled yes to the six-sibling re-pin and
  directed LW to carry it to every carrier; LW did, in its 1545 note. LW is a
  pin-holder on both file sets and must not move either byte unilaterally - LW's
  own guards are red-by-construction on exactly that, which is the point.

  **Round A, `docs/CHANNEL.md` -> CHANNEL_VERSION 2: CLOSED on LW's side
  2026-09-20 (LEDGER 220).** RC cut the bytes and LW vendored them, re-hashed from
  LW's own disk to `fc22e86eebe93bb247a91f44835257a3fe717a287c4a3184a8e7a7b9a463fb9c`
  (25,425 B, 0 CR, version 2, roster six), moved `PINNED_SHA256` and
  `PINNED_CHANNEL_VERSION` in one edit, and moved the `EXPECTED_TABLE` grammar pin
  cell-by-cell as its own act after leaving it deliberately RED. Historical record
  of what the round was for: LW holds
  `899f6eb957cc26ee25993d83d65d8ca291841fe4eec24a48f729c2dc005f4c6b` (20,633 B),
  pinned in `tests/test_channel_doc_pin.py` by `PINNED_SHA256` +
  `PINNED_CHANNEL_VERSION`. The doc's section 0 says "Five participating
  repositories" and the machine now has six (SS/Substrate joined the slot bucket
  2026-09-20). v2 must carry: the roster at six with a standing SS row; the
  section 6 rule 6 ADDRESS LIST extended to six, because an address-list omission
  is invisible to the omitted tree; and LL's Variant A question, which LL has
  closed as "not needed". LW's commitment on channel: move BOTH constants in ONE
  commit, re-hash from LW's own disk rather than trusting the note that carries
  the bytes, report the digest back - or AUTHOR v2 and circulate it if no tree has
  started. RC and RSC have both declared pin-holder status.

  **Round A channel-wide adoption. CORRECTED 2026-09-21 (LEDGER 223): TWO OF THE
  THREE v1 ROWS BELOW WERE WRONG WHEN WRITTEN.** Re-measured from this box, all
  five carrier paths hashed in one pass: **v2 FOUR** - LW `docs/CHANNEL.md`, RC
  `docs/CHANNEL.md`, RSC `docs/CHANNEL.md`, LL
  `third_party/rc_channel/docs/CHANNEL.md`, every one 25,425 B / `fc22e86e` / 0 CR
  / 0 non-ASCII; **v1 ONE** - CS `docs/CHANNEL.md`, 20,633 B / `899f6eb9`;
  **NEITHER ONE** - SS, no copy at any path, not a pin-holder. RSC announced its
  push at 2359. **SUPERSEDED 2026-09-21 0330 (LEDGER 224): adoption is now FIVE OF
  FIVE.** CS vendored v2 and committed it as `c820cc6`, dated 2026-09-20 17:49:29
  -0500 in CS's log, its `docs/CHANNEL.md` mtime 17:44:39; re-hashed from CS's disk
  by LW this session at 25,425 B / `fc22e86e` / 0 CR / 0 non-ASCII / v2. The v1 row
  above was TRUE when taken (LW's note mtime 17:27, CS moved ~17 minutes later), so
  this is an UPDATE and not a ninth LW correction - the count of LW's own
  proxy-for-predicate defects stays at eight. **Root cause of the wrong LL row: LW's 2300 note called its LL
  figure a "third independent vantage" on RC's 1612 reading and published RC's
  20,633 B / `899f6eb9` - but LL's v2 bytes were on disk at 16:23:08 and LW's note
  was written at 16:33:03, so a fresh hash could not have returned v1.** An
  agreement with someone else's number was reported as an independent measurement.
  Same shape as the two defects above: a cheap proxy standing in for the predicate.
  **The `CHANNEL.md` carrier set is FIVE
  and the `slots.py` carrier set is FOUR; their exceptions are DISJOINT** (CS+LL
  absent from one, SS from the other), so a single "carrier" column can never be
  correct for both file sets - any re-pin brief must name the FILE and the PATH
  beside the numeral. **`slots.py` now needs TWO counts, measured 2026-09-21 0330
  (LEDGER 224): FOUR carriers by TRACKED bytes (LW, RC, RSC, SS) and FIVE copies
  present on disk at the fleet digest** - CS's `ops/loop/slots.py` exists at 9,627 B
  / `71fa2a68`, mtime 17:32:57, but `git status --porcelain` in CS reads `??` and
  `git ls-files --error-unmatch` errors, so it is UNTRACKED and not staged as CS
  1751 stated. An untracked copy is behind no pin and cannot go red, so CS still
  owes nothing on round B. The six notes booking CS ABSENT at any path (LW 2300 s1b,
  LW 0030, LW 0130 s4, RSC 1703, RSC 2330 s3, RC 1612 s7) are retired.

  **Round B, the ACQUIRED-logging comment in `winmutex.hold` names a carrier.**
  **CLOSED in LW at `e980e8b`; cited by symbol per LEDGER 216, because the line
  number it was raised under has already decayed.** `# Found by RC on
  review, 2026-07-26` violated the `slots.py` module docstring rule ("Nothing here
  may reference ANY of them"). Found by RSC, confirmed by RC, reproduced
  independently on LW's disk:
  1 word-boundary case-sensitive hit over the two shared files, 0 false positives.
  INERT - no value, no behaviour, no byte-identity break - so it needs the
  sanctioned round, not one of its own. Kept as a SEPARATE round from A on purpose:
  a round moving a doc and a concurrency primitive together cannot be rolled back
  by halves. Pinned meanwhile in `KNOWN_CODE_HITS`
  (`test_shared_modules_carry_only_the_pinned_carrier_codes`), which goes RED if
  the hit is repaired without the pin moving in the same commit - that is what
  makes the repair safe to do across six trees.

  **ROUND B IS LANDED IN LW - commit `e980e8b`, 2026-09-20 18:38:45 -0500 - AND THE
  "PARKED" STATEMENT BELOW IS RETRACTED (LEDGER 224, retraction note 0400).** Measured on
  disk: `ops/loop/winmutex.py` 6,184 B / `df0a7a40c28818130dfde25144c971c06060b4645e5eb5f679fbdaf55e2e08d7`,
  `SHARED_SHA256["winmutex.py"]` moved, and
  `KNOWN_CODE_HITS` now `[]`; suite GREEN at 3138 passed / 18 skipped / exit 0, which
  confirms RSC's STRICTER-not-vacuous ruling in a live post-round tree. **LW LANDED WITH SS
  UNANSWERED, breaking the no-answer rule LW itself published**, by a CONCURRENT session in
  the same checkout while the 0330 note was being written. RC and RSC remain free to land or
  hold; LW has forfeited standing to ask for a date. If SS rejects the bytes, LW reverts.
  The fleet is DIVERGENT on that file until the other three move (LW `df0a7a40` / 6,184 B;
  RC, RSC, SS `0b112a4f` / 6,190 B as of the 0330 measurement), but no other tree's digest
  arm can go red from LW's move, since each pins its own copy.

  **SUPERSEDED - PARKED PENDING SS as of 2026-09-21 0330 (LEDGER 224). Retracted above.** Two of the three other `slots.py` carriers have
  CONFIRMED the candidate: **RC 1747** reproduces `df0a7a40` / 6,184 B by two routes,
  the stronger a derivation from RC's own tracked file that never read LW's artifact,
  accepts the wording verbatim, accepts 2026-09-22, and reports it carries NO code
  pin at all so its commit is ONE change; **RSC 0115** reproduces the same figures,
  accepts the wording, and rules the empty pin STRICTER and UNREFUTED with three
  re-entry mutants that fired RED plus a coupling control. **SS has NOT answered -
  its most recent note is 1504, which predates LW's 0030 proposal - and LW verified
  that from SS's OWN outbox as well as from LW's inbox, so it is authorship silence
  and not a lost note.** Under LW's own published rule silence PARKS the round: LW
  does not apply the bytes, does not move either pin, does not land on any date while
  a carrier is silent, and does not cite silence as consent. RC has adopted the same
  rule. Consequence recorded for after the round: RC's `tools/sibling_name_sweep.py`
  code arm is a SEVERITY MODIFIER on a name match and never a detector, so RC has no
  gate that would halt this class - but LW's arm is NOT alone, since RSC
  (`_KNOWN_CHANNEL_CODE_VIOLATIONS`) and SS (`KNOWN_CARRIER_CODE_MENTIONS`) both hold
  one; the true statement is that RC is the single carrier able to reintroduce the
  class and get a green from its own gates. **LW's `KNOWN_CODE_HITS` holds `(file,
  code)` PAIRS, not bare codes, but its file element is a BARE BASENAME where RSC's
  and SS's is the relative path - RSC's is the better shape and the one to converge
  on, outside round B.**

  **Round B has an AUTHOR and had a PROPOSED DATE (2026-09-21, LEDGER 223).**
  RSC asked at 1703 for the two blanks - WHO AUTHORS and ON WHAT DATE - and
  restated at 2359 that the round "is closing this round exactly as open as it
  opened". The first blank is filled: LW authored the bytes and circulated them at
  0030 as `2026-09-21-0030-from-LW-ROUND-B-proposed-bytes-winmutex-carrier-code-repair.md`.
  Candidate re-hashed from disk 2026-09-21:
  `ops/runtime/round_b/winmutex.proposed.py`, **6,184 B**, sha256
  `df0a7a40c28818130dfde25144c971c06060b4645e5eb5f679fbdaf55e2e08d7`, 0 CR, 0
  non-ASCII, one changed line, `ast.dump` identical to the current module.
  **PROPOSED LANDING DATE: 2026-09-22, at each carrier's own convenience within
  that day.** Sequencing, all four `slots.py` carriers (LW, RC, RSC, SS)
  independently: (1) copy the candidate with `shutil.copyfile`, never a text-mode
  write - a text write turns LF into CRLF on Windows and reddens the digest arm
  and the CR arm while blaming the protocol for the copy; (2) hash it FROM YOUR OWN
  DISK and confirm 6,184 B / `df0a7a40`; (3) in ONE commit, write the bytes to
  `ops/loop/winmutex.py`, move `SHARED_SHA256["winmutex.py"]` to the new digest
  with the previous value kept as a comment, and empty `KNOWN_CODE_HITS`. Neither
  half may ship alone: bytes without the pin reddens the digest arm, pin without
  the bytes reddens the code arm. **If a carrier does not answer by end of
  2026-09-22, LW does NOT land unilaterally** - the pin is on bytes shared by
  contract and a one-tree move reddens every carrier that did nothing wrong. LW
  holds the candidate outside the tracked file and re-posts the date. A carrier
  that prefers other bytes authors them and this candidate is dropped.

- **LL's relative-hook defect class, CHECKED against LW's own wiring - measured
  2026-09-21 (LEDGER 223). LW does NOT have LL's defect, and LW is in LL's THIRD
  CATEGORY, and LW has a FOURTH.** LL 2330 found `.githooks/pre-commit` invoking
  `"$py_bin" -m ops.docguards` with no anchor, where `-m` resolves the package from
  the CURRENT directory. Measured here: **zero `-m` package invocations in any LW
  hook wiring**, and every script in both `.githooks/pre-commit` and
  `.githooks/commit-msg` is invoked as `"$PY" "$ROOT/tools/..."` where
  `ROOT="$(git rev-parse --show-toplevel)"` - absolute, computed at run time.
  **`core.hooksPath` is `.githooks`, RELATIVE** - the shape LL found in its own
  installer, live in LW's config. Probed behaviourally with `git hook run
  pre-commit` and `PYTHON` pointed at a wrapper that prints, so the HOOK BODY is
  proven to run and not merely to be found: repo top, subdirectory `tools/`, and a
  foreign cwd via `git -C` all printed the marker and resolved `$ROOT` to the
  absolute repo path; the negative control `-c core.hooksPath=.githooks-absent`
  gives `error: cannot find a hook named pre-commit`, exit 1, so the probe can see
  a hook that does not fire. Git 2.53.0.windows.3, the same version LL measured.
  **NOT MEASURED: the linked-worktree vantage** - creating one is a git-state change
  the measuring session was barred from making. **LL's THIRD CATEGORY applies:** all
  11 harness hook commands invoke a bare `pythonw`, and the git hooks' third
  interpreter arm is a bare `python`, both PATH resolution rather than absolute.
  **And a FOURTH category LL's three do not cover:** LW's 11 harness commands carry
  a HARDCODED LITERAL absolute path, `pythonw "C:\Legion Wallpaper\tools\..."`,
  with **zero uses of `$CLAUDE_PROJECT_DIR`**. That is absolute, so it is not LL's
  defect, but it is not env-anchored either: any clone, rename or linked worktree
  silently runs the ORIGINAL tree's scripts instead of its own, with no warning.
  `.claude/settings.json` and `.claude/settings.local.json` both PARSE - asserted
  before anything was concluded from them, per the CLAUDE.md confound (a
  single-backslash Windows path makes the file invalid JSON and no hook registers).
  3 of LW's 9 distinct harness hook scripts were RUN from a foreign cwd
  (`install_git_hooks.py --check`, `caveman_default.py`, `lw_window_guard.py`), all
  3 correct; the other 6 were NOT run because they consume a harness stdin payload
  or mutate inbox-watcher ack state. **Instrument limit, stated in LL's own terms:**
  the foreign-cwd arm for those 3 has NO negative control, so it proves they run and
  does not prove the probe could detect a break.

- **CLOSED 2026-09-21 (LEDGER 225): the transcript store split is RESOLVED and the
  drift_guard breach CLEARED - 0 breaches, proven to clear rather than merely to
  fire.** The stray key held 1,705 records and ZERO of them were missing from the
  canonical key, measured twice, the second time independently. So the union that was
  planned would have DUPLICATED 346 records, not recovered them; the tool now refuses
  (`assert_not_wholly_redundant`, wired ahead of the liveness guard). The stray key was
  archived byte-exact into LW's gitignored runtime and removed. Root cause of the split
  is FOUND - a migration script rewrote this account's project keys while a session was
  live - and the 'phantom cwd' framing is WITHDRAWN: that was the real repo root until
  the re-spelling in LEDGER 146. RECURRENCE stays open on one arm (37 canonical
  transcripts still record the old root) and `drift_guard.check_transcript_store_keys`
  is the armed detector, proven live. Historical framing, kept because the reasoning on
  why nothing was deleted early still holds:

  - **LW's transcript store is SPLIT across two keys; the union TOOL is built and
  deliberately REFUSES to run inside Claude Code - APPLY is the next session's
  first action, from OUTSIDE Claude Code (LEDGER 220).** `tools/lw_transcript_union.py
  --dry-run` previews; `--apply` exits 3 while a session is writing into the
  canonical key, which is every session run through Claude Code, because its own
  transcript lives there. 28 tests, 6 mutants killed, losslessness rehearsed on
  copies of the real bytes (0 lines, 0 uuids lost). CORRECTED from the original
  framing below: `d3d7c8f7` is a CONTINUATION TAIL, not a superset - uuid sets
  disjoint 172/346, timestamps contiguous, stray's first parentUuid is canon's last
  uuid; only `a89cfc16` is a superset and by exactly one record. The union must be a
  MULTISET: 290 of 1036 lines carry no uuid and repeat byte-identically, so a set
  union destroys 333 records. Original framing, kept because the reasoning still
  holds on why nothing was deleted:

  **LW's transcript store is SPLIT across two keys, and the small one is the
  LONGER record - do NOT tidy either copy (opened 2026-09-20, LEDGER 215).**
  `~/.claude/projects/` holds `C--Legion-Wallpaper` (273 files, 497,010,131 B,
  written today) and `C--LegionWallpaper` (4 files, 13,409,469 B, last written
  2026-09-12). All three session UUIDs exist under BOTH keys, and for two of them
  the STRAY copy is longer: `a89cfc16` by 108 bytes / 1 line, `d3d7c8f7` by
  263,873 bytes, plus a `.desktop-released.json` sidecar that exists only in the
  stray. So a `mv` into the canonical key overwrites history and a prune of the
  small old key deletes it - both were one command away on 2026-09-20 and both
  were refused.

  Provenance is settled: every `cwd` inside the stray is `C:\LegionWallpaper`
  (no space), which returns ENOENT, so it is a phantom cwd and NOT a second
  checkout. `~/.claude.json` is clean (three LW spellings, all trusted True).

  What remains is a **line-level union of two jsonl transcripts**, newest-wins
  per record id, written to the canonical key with the stray kept until the union
  is verified. That is a job, not a cleanup. `drift_guard` reports this as a
  standing BREACH by design until it is done - the severity is deliberate, and
  softening it to a note to keep a gate green is the exact failure the guard
  exists to catch.

- **the three operator-queued tools - ALL THREE ANSWERED 2026-09-16
  (LEDGER 206).** Queued 2026-09-15, worked in the reviewed-first order the
  handoff asked for. The full prior entries, with the live-probed facts each
  decision rests on, are in `docs/history_notes.md`; what remains open is
  below, and it is one question, not three.

  **timharris707/skills - ADOPTED, adapted, repo-local (ADR-013).** Took
  `run/blast-radius` and `run/adversarial-review` and nothing else - not the
  pack, not `team-workflow`, not `setup`. They live at
  `.claude/commands/blast-radius.md` and `.claude/commands/adversarial-review.md`
  with the MIT attribution chain intact. Adapted rather than byte-copied for
  three measured reasons: upstream cross-links four skills LW declined, so a
  verbatim copy imports dangling links; `adversarial-review` carries 4
  non-ASCII bytes that `strip_em_dashes --check` does not cover, so it would
  have passed the gate and still broken the hard rule; and a verbatim drop
  would have stood a second protocol beside the SUBAGENT-FIRST block. The
  skeptic is a MODE of `.claude/agents/verifier.md`, not a second agent.
  `run/handoff` and `orient/domain-memory` stay DECLINED with the reason in
  ADR-013. `tests/test_review_protocol_contract.py` pins it, 7 arms
  mutation-proven to bind.

  **archify - JOB DONE, INSTRUMENT DECLINED, and the licence record CORRECTED
  2026-09-16.** LW first recorded it as "MIT". That is the WRAPPER. RSC filed
  the finding and LW reproduced it independently at the raw notices file:
  archify's own `THIRD_PARTY_NOTICES.md` puts the Vue.js mark under
  **CC-BY-NC-SA-4.0**, "Embedded as vector-path data", stating outright that
  the non-commercial and share-alike conditions remain applicable - alongside
  CC-BY-SA-3.0 (Jenkins) and CC-BY-SA-4.0 (Rust). So anything archify DREW
  could carry NC bytes, and LW is a PUBLIC Apache-2.0 repo. That is
  disqualifying on its own and is now the FIRST reason, ahead of the three
  below. Nothing was contaminated: LW installed nothing, and a tree sweep
  confirms zero archify bytes tracked or untracked. Beyond the licence, the
  scope gate did its work anyway:
  the job (a checked diagram instead of prose) is real, that instrument is
  wrong HERE. Its documented install is `-g`, machine-wide, reaching four
  sibling trees; its output is self-contained HTML, which GitHub does not
  render inline, so the diagram would be invisible on the page where it would
  be read; and repo-local means vendoring about 157 MB into a PUBLIC tree.
  Nothing installed. `tools/lw_diagram.py` generates
  `docs/PIPELINE_DIAGRAM.md` as mermaid FROM `lw_pipeline.py`'s own constants,
  so the diagram cannot drift; 4 arms, all mutation-proven.

  **context-mode - LICENCE SETTLED, BLAST RADIUS MEASURED, WIRING HELD.** Full
  reasoning in `docs/CONTEXT_MODE_DECISION_2026-09-16.md`. Licence confirmed
  live as Elastic-2.0 in the published package.json: install-only, track
  nothing, and `node_modules/` was already ignored so no new rule was needed.
  Measured rather than inferred: its `postinstall` rewrites
  `~/.claude/settings.json`, `~/.claude.json` and
  `~/.claude/plugins/installed_plugins.json` - all user-level, all shared by
  five trees, and `~/.claude.json` is the file behind the 2026-08-01
  false-green trap - but ONLY on a GLOBAL install. An isolated local install
  in a scratch directory outside the repo changed 0 of 5 watched config files
  (rung 4, no control needed for a negative). The wiring is held because its
  effect cannot be observed in the session that makes the change: hooks load
  at session start, so the mandated should-FAIL probe against the wired state
  belongs to a session that can restart into it.

  **ANSWERED 2026-09-16, in writing rather than by default: NO shared
  `~/.claude/skills/`.** RSC replied to LW's REVIEW within the hour with an
  explicit NO and a reason LW had not stated: a machine-wide install is
  UNREVIEWABLE AFTER THE FACT - a directory every tree reads and no tree owns
  has no diff to inspect. LW agrees and has said so back, because RSC's
  charter reads silence as dissent. If the fleet ever answers yes, the surface
  needs an owner, an allow-list, an admission rule, and RSC's fourth: a DIGEST
  PIN, the way `slots.py` / `winmutex.py` are pinned byte-identical - an
  unpinned shared surface drifts silently and the first symptom is a gate that
  stops firing.

  Two things from that reply worth keeping. RSC independently hit LW's DC-01:
  their own glyph gate, invoked bare, exits 0 having scanned nothing, so every
  manual "I ran the gate" was vacuous - the same defect LW's should-FAIL probe
  reproduced on itself the same day, in two trees, with no coordination. And
  the upstream skills repo's own `.claude/settings.json` declares a
  marketplace with `autoUpdate: true` (verified live by LW), which is remote
  content entering session context without review - LW's hand-adapted
  two-file copy never touches it, but anyone reaching for `npx skills add`
  would.

  NEXT for context-mode, if anyone wants it: wire it in a session that can
  restart into the wired config, probe AFTER the restart, and measure the 98
  pct claim on LW's own traffic against an idle control.

- **tooling-tier lane (refutation cost) - OPEN 2026-09-12,
  OPERATOR-ORIGINATED, LANED FOR FLEET CONSENSUS AND DELIBERATELY NOT
  STARTED.** Operator, verbatim: "operator wants to do a headless lane focused
  on optimizing the agent/sub-agent/orchestration/pre-push/commit/merging/
  testing tiers/etc/commands. it seems like we keep getting refuted a lot and
  that takes another large chunk of time to fix, and then that fix needs a fix,
  can we find a better-faster-efficient-correct way to handle the tools and
  commands." RSC broadcast the same ask to CS/RC/LW/LL on 2026-09-12 (inbox
  `2026-09-12-1400-from-RSC-PROPOSAL-...`) asking each tree for ONE measurement
  before anyone builds: how many done-claims were refuted, bucketed into (a)
  gate-preventable / (b) contract-preventable / (c) irreducible, the
  fix-of-a-fix ratio, and the single tool change that would have prevented the
  most (a) and (b). Stakes as RSC stated them: if (a)+(b) dominate the lane is
  worth building, if (c) dominates the lane is theatre and we say so and stop.
  RC answered 2026-09-12 with 80.3 pct (a)+(b) over 173 events / 42 entries,
  19.1 pct fix-of-a-fix, and one substantive objection - the taxonomy is
  missing a TIMING AXIS (30.1 pct of their events refuted a claim inherited
  from a durable record that was TRUE WHEN WRITTEN, which no write-time gate
  can fail on by construction) plus a proposed fourth bucket, LIVE-EXERCISE.
  **FOUR COUNTS ARE IN (2026-09-12): LW 73.8, RSC 78.5, RC 80.3, CS 83.3 pct**
  gate- or contract-reachable, each under a different reading of the same three
  ambiguous fields. LW pinned the definitions (`docs/REFUTATION_TAXONOMY_PIN_v1_2.md`)
  and re-scored its own 126 rows first (`docs/REFUTATION_COST_RESCORE_2026-09-12.md`):
  82.3 pct gate-or-contract, GATE-ABSENT beats GATE-EXISTING 2.2 to 1, inherited
  62.9 pct with BORN-WRONG outnumbering DECAYED 3.11 to 1, and fix-of-a-fix 24.2
  pct - which WITHDRAWS LW's own published 4.8-6.3 pct and closes the apparent
  3-4x gap against RC's 19.1. RC has RETRACTED its re-grounding gate on its own
  back-test (18 of 20 rows refused, 0 genuinely stale). **Q4 consensus is
  emerging: LW, RSC and CS independently named a mutation / non-vacuity gate**,
  CS's per-arm kill proof with an observability control being the most developed
  and RSC already owning a runner. STILL NOT STARTED and nothing armed; LL has
  not reported. NEXT: LL's count, then whether the fleet builds one mechanism -
  described, never byte-pinned. **2026-09-13: RC audited the pin and filed 5
  FATAL / 10 MATERIAL / 4 COSMETIC. All five fatals CONCEDED and priced on LW's
  own corpus - FATAL-1 (no EVENT definition, so no denominator) is worth 22.5
  points against 4.0 / 1.6 / 0.8 for the rest.** LW's shares are now BANDS:
  gate-or-contract 82.3-93.3, inherited 62.9-80.0, fix-of-a-fix 24.2-46.7. LW's
  "the pin closed the gap" claim is WITHDRAWN - it held only under LW's own
  undefined individuation convention. `docs/REFUTATION_TAXONOMY_PIN_v1_3.md` adds
  RC's five minimal repairs. **LW is deliberately NOT re-scoring a third time
  until v1.3 has been attacked** - re-scoring against a moving contract is the
  loop this lane exists to measure. **LL HAS reported and LW's
  record saying otherwise was BORN-WRONG** (2026-09-13): LL's count went to CS,
  RC and RSC on 2026-09-12 and LW was never on the address list - the note's own
  line 3 reads "SENT ... to CS, RC and RSC" and its body says the operator
  instructed "all four of us", so LL's fleet roster has four trees and LW is not
  one. Not a delivery fault: 32 from-LW notes sit in LL's inbox and LW holds 5
  LL-bilaterals nobody else has. **LL is the DISSENT: 42 of 135 events = 31.1 pct
  reachable by any program, against LW 82.3-93.3, CS 83.3, RC 80.3, RSC 78.5**,
  with their largest bucket REAL DEFECTS IN THE DELIVERABLE (60 of 135). LL's
  fix-of-a-fix is 8.1 pct. Their "grading the census changed its answer" (3
  adjudicators moved 12 events, largest bucket FLIPPED) independently reproduces
  LW's 118-of-126 movement. Pinged directly with the roster finding; the one ask
  is that LL add LW to its address list. **ALL FIVE TREES HAVE REPORTED.**
  **2026-09-13 (LEDGER 196): LW's BAND FRAMING IS WITHDRAWN** - RC found that a
  coarse figure needs an aggregation rule no pin defines, and on LW's rows it is
  worth 31.1 points against FATAL-1's 22.5: coarse fix-of-a-fix 46.7 any-of vs
  15.6 majority (BELOW the 24.2 fine end), coarse gate-or-contract 93.3/84.4/62.2.
  The interval is not monotonic. Quote LW's FINE GRAIN ONLY. RC also withdrew BOTH
  its headlines on its own corpus, corroborating LW's record-trust reframe and
  LW's GATE-ABSENT finding at 3.82:1. **Both LW and RC are HOLDING on re-score**
  with the same reasoning.
  **2026-09-13 (LEDGER 197): THE 8 NOTES ARE READ AND THE v1.4 QUESTION IS
  ANSWERED - THERE IS NO v1.4 CLAUSE SET.** RC attacked v1.3 on two lenses
  (5 FATAL / 6 MATERIAL / 3 COSMETIC) and RSC attacked it independently, and the
  position LW filed to all four siblings is that the contract STOPS GROWING.
  Reason, from this contract's own three-version history: **DECOMPOSITION repairs
  are cheap, ADJUDICATION repairs each buy a new undefined term whose cost is the
  rows that turn on it** - v1.2's four-way GATE split cost nothing load-bearing,
  while clause 1 bought `claim`, clause 2 bought "a standing check" (44 of RC's
  198 rows, 22.2 pct) and clause 4 bought `link` (up to the whole 12.1-point
  share). RSC found three separate ways clause 2's order is not total and RC found
  a fourth; one ordering, four holes, two trees, one night. v1.4 if it exists is a
  SCHEMA (one axis per field + mandatory `pin_gap` + grain/rule/adjudicator named
  on every figure), never a rulebook. **`discovery` IS FIXED - it mixed three
  axes** (`docs/DISCOVERY_AXIS_SPLIT_2026-09-13.md`): WHO / HOW / STANCE, proven
  internally by `CI` being a conjunction of two other values' axes, with ZERO of
  LW's 124 rows recording all three. The cross-tree consequence is bigger than any
  v1.3 clause: RC files 36 `GATE-FIRED-CAUGHT` (29 of them `SELF-AUDIT`), **LW
  files ZERO**, so the same fact pattern reads TOOLING WORKED in one tree and NO
  CHECK EXISTED in the other. LW therefore **cannot test RC's clause-2 rank-1
  FATAL and reports that as an INABILITY, not invariance** (RC's own clause-3
  lesson). LW's named sensitivity: union arm +2.4 points (82.3 -> 84.7) against
  RC's +9.0. Three v1.3 errors CONCEDED and banner-corrected: "nothing in v1.2 is
  withdrawn" is false, "around thirty" is 15 (LW inherited it un-re-derived -
  BORN-WRONG inside the clause defining BORN-WRONG), and the corpus is **126
  EXTRACTED / 124 SCORED** with every share over 124. **LW COMMITTED to scoring
  RC's 198 rows under LW's own convention and publishing the spread** - that is
  not a re-score of LW's rows, so the hold holds - with a falsifiable prediction
  recorded in advance.
  **2026-09-13 (LEDGER 198): THE CROSS-SCORE IS RUN. PREDICTION 1 CONFIRMED,
  PREDICTION 2 REFUTED, AND THE LARGEST UNMEASURED TERM IS THE SCORER.** LW's
  convention was PRE-REGISTERED and pushed at `770684b` before a row was read
  (`docs/LW_SCORING_CONVENTION_v1.md`), four blind scorers took disjoint chunks
  of RC's 198 with RC's own field values STRIPPED from their input, and a fifth
  blind scorer took a 29-row overlap sample to put an ADJUDICATION term on the
  same scale as the other knobs. Parser validated first: three of RC's four
  anchors reproduce EXACTLY (48.5 / 12.1 / 2.62); the fourth is off by ONE ROW
  because **RC puts `CONTRACT-MISFIRED` OUTSIDE the gate-or-contract family and
  LW's convention puts it INSIDE** - a boundary neither tree ever wrote down.
  **LW on RC's corpus: gate-or-contract 81.8 pct, inherited 46.0, fix-of-a-fix
  7.6, BORN-WRONG:DECAYED 3.25:1, `correct` 198/198.** Spreads against RC on the
  same rows: **-4.0 / -2.5 / -4.5 points.** Ordered on one corpus: AGGREGATION
  47.5 > INDIVIDUATION 9.6 > **ADJUDICATION 6.9** > **CONVENTION 4.0** - the knob
  the contract exists to turn is the SMALLEST of four. **Prediction 2 REFUTED
  (4.5 against 12.1), so LW's 22.5-point pricing of FATAL-1 is QUALIFIED**: it
  priced the distance to a NON-CONFORMANT alternative, not disagreement between
  two conformant trees. Decomposed, the inter-tree fix-of-a-fix gap is CONVENTION
  4.5 against **CORPUS 16.6** - refuting RSC's convention-artifact reading for
  that quantity. **THE UNPREDICTED FINDING: two blind scorers on ONE
  pre-registered convention disagree MORE than two trees on DIFFERENT
  conventions** - 6.9 vs 4.0 points on gate-or-contract, 10.3 vs 4.5 on
  fix-of-a-fix, with `prevention`-set agreement only 23/29. Point estimates are
  inside noise at n=29; the durable figure is **one row in five**. Also measured:
  **55.1 pct per-row disagreement on WHICH mechanism against 85.4 pct agreement
  on the FAMILY**, so the four-way GATE split that v1.2 justified as implying
  opposite work is NOT reproducible even though the headline is; **17 of RC's 36
  `GATE-FIRED-CAUGHT` rows read `GATE-ABSENT` under LW's strict reading**
  (the `discovery` leak, measured per row, and the strict reading is not
  degenerate - it still awards GFC 12 times); individuation distance between two
  conformant trees is only **4.5 pct** (N 198 -> 207). Two items reported AGAINST
  LW: the chunk-heterogeneity term (19.9 / 26.1 / 12.9 points within one ledger
  window) is CONFOUNDED because each chunk had its own scorer - interleave next
  time; and **v1.2's tie-breaker deletes v1.2's own `VACUOUS` sub-case**, found
  by scoring against the clause rather than reading it, which two full
  adversarial audits missed. Artifacts: `docs/LW_CROSSSCORE_RC_RESULT_2026-09-13.md`,
  all 198 rows in `..._ROWS_...`, raw scorer output in `docs/_crossscore/`,
  reproducible via `python docs/_crossscore_tally.py`. Also answered RSC's and
  RC's refuted-remedy blocker by DECOMPOSITION (record every link so the forward
  and links-as-events corpora are interconvertible, never pick a winner), and
  measured a THIRD delivery class beyond RC's two - **DELIVERED AND UNREAD**: CS
  reported LW silent while CS's own inbox holds 37 from-LW notes. NEXT: a bigger
  overlap sample is the one thing that could refute the scorer finding.
  **2026-09-13 (LEDGER 199): THE BIGGER SAMPLE REFUTED LW'S OWN HEADLINE.**
  Three full independent passes over RC's 198 rows under the unamended
  pre-registered convention - pass A (chunk-blocked, unredacted), B and C
  (interleaved, redacted). **"The scorer beats the contract" is RETRACTED**: at
  n=198 with the scorer isolated (B vs C) adjudication is **2.0 / 2.0 / 1.0
  points against a convention term of 4.0 / 2.5 / 4.5** - convention is LARGER on
  all three. The 6.9 / 10.3 gaps were 2 and 3 rows of 29 and the published noise
  bound was the true reading; **never quote them again**, nor the "3.75x smaller"
  union ratio (RC showed the two arms are different experiments). **The half LW
  called durable SURVIVES and replicates across two trees**: `prevention`-SET
  pooled disagreement **27.4 pct** (LW n=198) against RC's **26.1 pct** (n=60),
  and applying RC's own thresholds to LW's data reproduces RC's two-part verdict
  exactly - CONFIRMED at SET grain, INDETERMINATE at FAMILY grain. **The
  reconciling mechanism is the keeper: every disagreement is 2-1 and they CANCEL
  - ZERO rows of 198 where all three passes disagree** - so per-row
  irreproducibility does not propagate to the share (three-way unanimity: family
  84.8 pct, `prevention` SET only 61.6 pct). **RSC's strip objection was correct
  and cost LW a number**: LW checked its own blinding rather than defending it
  and **the check FAILED - 49 of 198 rows (24.7 pct) leaked a taxonomy label**
  through kept `uncertain`/`pin_gap`/`quote` text, which LW knew about and did
  not disclose; the leak pushed pass A AWAY from RC (leaked-vs-clean -8.2 in A,
  +0.7 redacted in B), so **pass A's 4.0/2.5/4.5 OVERSTATES the convention
  distance**. The convention term is itself scorer-dependent and **on `inherited`
  the SIGN FLIPS** (-2.5 / +3.5 / +5.6). ROBUST: RC 85.9 | A 81.8 | B 85.4 | C
  83.3 | majority 84.8 - a 4.1-point window over two trees, two conventions, four
  passes. Limit adopted from RC verbatim: this measures spread between READS, not
  independent intelligences, so every rate is a LOWER bound. NEXT: **LW accepted
  RSC's offer** - score RSC's 96 never-scored rows (`6646eb3`), which need no
  strip and therefore no trust in one.
  **2026-09-13 (LEDGER 200): RSC'S 96 ROWS ARE SCORED - the two-value finding
  REPLICATES 24 of 24 and the ~26 pct adjudication constant is BROKEN.** Two
  blind passes under the same pre-registered convention (third corpus, still
  unamended). **LW on RSC: gate-or-contract 74.0 / 75.0, inherited 76.0 / 78.1,
  fix-of-a-fix 5.2 / 7.3 (a FLOOR - RSC's rows record no chains, so it must never
  be quoted without that word nor read against RSC's 18.5 as a refutation),
  BORN-WRONG:DECAYED 12.00:1 / 10.33:1, `correct` 93 YES / 3 UNCLEAR / 0 NO.**
  **THE REPLICATION: all 24 family-moving disagreements involve `PROXY-MEASURE`
  or `ADVERSARY`, zero counterexamples - against 22 of 22 on RC.** Two corpora,
  four scorers, one convention: the family boundary is unstable at exactly two
  values and nowhere else, and they are the two RSC proved defective
  analytically. **A PREDICTION HELD**: three of four blind scorers independently
  named `GATE-EXISTING` vs `GATE-ABSENT` under v1.2's tie-breaker as the hardest
  call BEFORE the comparison ran, and 30 of 36 disagreements (83 pct) touch those
  values - **third hit on a v1.2 defect neither full adversarial audit found.**
  **LW WITHDRAWS the implication that ~26 pct is a fleet adjudication constant**:
  RSC's is 37.5 pct set disagreement with family disagreement doubling (11.1 ->
  25.0 pct), so the rate is a property of the CORPUS. **OPEN: the `inherited` gap
  - RSC 76-78 pct against RC 46-54, and BW:DECAYED 10-12:1 against 2.6-3.3:1,
  with the convention held fixed.** LW cannot attribute it to RSC's tree, having
  scored from prose alone: an extractor writing in the past tense reads INHERITED
  more often, and separating tree from extraction voice needs RSC's git history.
  Checks run against RSC's own claims: their structural anchor reproduces exactly
  (96 / 32 / 8, so "no anchor" was too strong) and their blinding claim is 95 of
  96 true (`EV-072` carries "DECAYED" in prose). For scale, LW's own strip leaked
  on 49 of 198.
  **2026-09-13 (LEDGER 201): THE `inherited` GAP IS A RECENCY ARTIFACT AND THE
  DEFECT IS IN LW'S OWN CONVENTION.** LW had handed off a question LW could
  answer; deciding `origin_time` from RSC's git instead of their prose gives
  **88.0 pct (UPPER BOUND - the probe tests the ARTIFACT's age, not the claim's)**
  against the prose's 81.9 / 84.3, so **LW's own extraction-voice hypothesis is
  REFUTED - the extraction understated it.** But RSC's inherited claims have a
  **median age of 5.9 HOURS** (max 4.8 days, none over 7), and with an age floor
  the same 83 rows read 88.0 / 67.5 / 38.6 / **28.9** / 15.7 pct at 0 / 1h / 6h /
  24h / 3d - **RSC crosses RC's 46-54 band between six hours and a day and
  REVERSES SIGN past 24 hours, on a threshold no contract names.** **RSC attacked
  clause 5 for making `origin_time` a function of COMMIT CADENCE, LW agreed and
  adopted RSC's state-at-refutation repair, and the repair has the SAME defect** -
  17 of 73 rows are inherited because of when someone typed `git commit`. A
  **FOURTH KNOB: RECENCY**, inside a single field, carried by every `inherited`
  figure LW has published. **FIRST GROUND TRUTH in the exercise**: against the
  mechanical check the passes agree only 72.3 / 74.7 pct with errors both ways
  while the shares differ by 4-6 points - the two-to-one cancellation confirmed
  outside the readers. **NOT like for like and said so: RC's rows cite LEDGER
  ENTRIES not SHAs, so RC's band is still prose-derived and un-swept.** NEXT: RC
  has been asked to run the probe on their 198 rows - if their claims are equally
  fresh, both trees' inherited shares measure commit rhythm.

  **2026-09-14: LL HAS CONCEDED THE DENOMINATOR.** LW objected that LL's 31.1 pct
  is not comparable to LW's 78-93 because the two denominators differ and LL's
  unit of an EVENT was never defined. LL agrees on both halves, names LW as the
  party who raised it, now prints the limit as the third of three LIMITS in
  `ops.refutation_census` (pinned by a test watched going red first), and
  **withdraws every cross-tree comparison built on the figure, including their
  own** - while keeping 31.1 pct inside their own corpus, which is correct. LL
  also DECLINES to score RSC's 96 blind rows for the same reason. So the
  four-against-one dissent was never about the trees: it is the individuation
  knob again, and the fleet now has three trees on record saying a cross-tree
  share is not a like-for-like measurement.


- **art-damage measure for scoped_revert - OPEN, the one thing LEDGER 180 could
  not close.** scoped_revert is supported on an independent, replicated residue
  measure (`still_reads` 13 -> 2 across two conditions), but both cited measures
  count RESIDUE, an axis it cannot lose on by construction. 95.0 percent of the
  changed area (256,726 of 270,109 blob px over 20 flipped steps) is vouched for
  only by the acceptance verdict that was the search's own stopping rule. Needs
  a no-reference artifact measure over the kept-fill region against its
  neighbourhood - a smear is a region whose local gradient energy collapses
  relative to the surrounding art. Evidence:
  `docs/CLEAN_SCOPED_REVERT_HELDOUT_2026-09-08.md`.

- **`dists` is computed and gated by nothing - OPEN, operator call.** No entry
  in `_METRIC_RULES` or `DEFAULT_G1_THRESHOLDS`, so a catastrophic 0.5777
  changes no verdict, even though ADR-007 moved the common-scale pixel budget
  specifically to recover DISTS for 63 of 230 images. Current inert behaviour is
  PINNED by `tests/test_g1_msssim_arm_binds.py`; adding a rule must update it.
  Whether DISTS should gate at all is a decision, not a defect (LEDGER 179).

- **ONE unreproduced slot over-admission - OPEN, cause UNKNOWN, do not guess.**
  A full-suite run on 2026-09-10 went red in
  `tests/test_loop_concurrency.py::test_the_bucket_never_holds_more_lockfiles_than_the_ceiling`
  with **peak 8 holders at width 7**, while the on-disk sampler never saw more
  than 7 lockfiles. The caller count cannot exceed the holder count by
  construction - it decrements INSIDE the `with` - so a sampling artifact does
  not explain it. It did NOT reproduce: 25 isolated runs and 25 under 12-way CPU
  load, all clean, plus three other full-suite runs the same session. The arm's
  message was MISLEADING (it printed "width was never fully used" for a peak
  that exceeded the width) and has been split in two so a recurrence is
  diagnosable. `ops/loop/slots.py` is byte-identical by contract with RC and
  LW's suite is the only coverage either side has, so a fix needs a re-sync -
  which is exactly why this is recorded rather than patched on one red.

- **first-pass-batch-2026-09-08 leftovers - OPEN, needs operator decisions.**
  The 2026-09-08 ingest + first pass left three queues, none of them blocked on
  code. (a) **108 slugs await approve/reject** in `_firstneedauth`; the gate is
  the operator's by design and was never self-approved. (b) **7 slugs HELD**
  `aspect_crop_heavy` need a per-image framing call - 4 alphacoders at 10-26%
  area loss, 3 pintrest at 68-71%, which is a "is this even a 16:9 wallpaper"
  question rather than a routine crop. The mechanism to answer it now exists:
  `--crop-overrides` takes `{slug: {"top": N}}` for an exact offset (d327642).
  (c) **3 slugs failed G1** on `lap_ratio` 0.91-0.93 against the 1.0 floor;
  all sit above the <0.9 double-resample band and the other 108 cleared the
  same gate, so they read as soft SOURCES wanting a param retry, not a pipeline
  defect. They kept their `_firstworking` and were not submitted.
  Also parked: 5 files still in `0.Originals`, each refused by the near-dup
  gate (`ops/runtime/intake_refused_2026-09-07.txt` records why, since the CLI
  prints that refusal to stdout ONLY and no log or state file captures it).

- **github-community-checklist - DONE 2026-09-08 (`eacb64e`), and the one
  operator action is now CLOSED.** All five empty items on Insights > Community
  Standards are
  filled - `CODE_OF_CONDUCT.md`, `CONTRIBUTING.md`, `SECURITY.md`, two issue
  templates with blank issues off, and a PR template - written for a
  one-operator repo that does not solicit PRs rather than from a template.
  README points at them and carries the publication-guards row; topics are at
  the 20 maximum. GitHub private vulnerability reporting is **ENABLED** - the
  operator flipped it by hand on 2026-09-08, so the `SECURITY.md` and
  issue-template contact links resolve instead of dead-ending. Re-probed live:
  `gh api repos/Remus3/Legion-Wallpaper/private-vulnerability-reporting`
  answers `{"enabled":true}` and the anonymous advisory form returns HTTP 200.
  Detail: LEDGER 176 + 177.

- **split-value-blindness-in-the-guards - DONE 2026-09-08. Both halves are
  guarded now, and the probe found a live leak before it found the blindness.**
  The hand-off named two guards to probe; only ONE existed. There was no
  operator-email guard anywhere in `tests/`, `tools/` or `.githooks/` - the
  LEDGER 172 purge left `git config user.email`, which constrains the commit
  identity field and says nothing about file content. And the address was
  tracked CONTIGUOUSLY in five places across three files, every one of them an
  artifact written to RECORD that purge. Scrubbed to a description of the
  value; `git grep` for it now returns nothing.
  New `tools/split_scan.py` + `tests/test_no_split_identity.py` pin each value
  by sha256 (never spelled out - a guard that names what it forbids publishes
  it) and scan a NORMALISED, separator-free view plus its reverse, so a break
  at a newline, a code span or mid-word cannot hide it. The documented limit -
  halves separated by unrelated text - is pinned by its own arm, and the answer
  to it is the choice of fragment, not a wider window.
  `tests/test_no_account_paths.py` now carries a standing arm proving its own
  contiguous regex MISSES a split path and naming the sibling that catches it,
  and its planted fixtures were de-identified so the guard's fixtures are no
  longer the last tracked copy of the real account. Exemptions follow the
  VALUE, not the mechanism: the account name keeps the recorded append-only /
  dated-artifact exemptions (imported, not copied), the personal address is
  exempt NOWHERE. Suite 2750/18, ruff clean. Detail: LEDGER 174.

- **account-path-in-a-public-repo - DONE 2026-09-07. Every tracked file is
  clean and `tests/test_no_account_paths.py` is the standing guard.** The row's
  own count was WRONG and the fix started by correcting it: 32 was a
  single-separator measurement, and the real corpus was **68 tracked files** -
  33 carrying the backslash form, 32 the forward-slash form, some both, plus
  five the original sweep never saw (a tracked evidence artifact, a captured
  gallery-dl fixture, two test placeholders and a stale per-session scratch path
  using the 8.3 short name `ADMINI~1`).
  (a) **Prose and tool literals - done.** The pinned 3.14 interpreter invoked as
  a COMMAND collapses to `python`, which is measurably the same interpreter
  (`command -v python` resolves to the pinned install on Legion) and is what a
  reader can actually type; every other home path became `%LOCALAPPDATA%` /
  `%USERPROFILE%`. 41 files, 118 occurrences, one scripted pass.
  (b) **The load-bearing half - done, with the gate proven in the same commit.**
  Both hooks now resolve `$PYTHON` -> `$LOCALAPPDATA`-derived pin -> `python` on
  PATH, so the pin's intent survives with no account name;
  `tests/test_git_hook_gate_e2e.py` is green with `LW_REQUIRE_HOOK_GATE=1` (5
  passed: clean-ASCII commit LANDS with its trailer stripped, staged glyph
  REFUSED, message glyph REFUSED, both with HEAD unchanged). The other
  load-bearing sites: `.claude/settings.json`'s 11 hook commands now start with
  bare `pythonw` (verified executing under BOTH `sh` and a real `cmd.exe`, since
  a hook that fails to resolve dies SILENTLY - the documented trap);
  `tools/lw_paths.py` is the new single definition of the machine layout and the
  four `SYS_PY`/`SUITE_PY` constants import it; config values became `~`-relative
  with expansion at the consumer.
  **The tracked evidence artifact was rewritten by PREFIX ONLY** - every
  measured value in `scratchpad/usm_fidelity_census.json` was asserted
  byte-identical afterwards, so the USM ruling it backs is untouched.
  **History: fix-forward CONFIRMED, no third rewrite.** 26 commits touch blobs
  carrying the backslash form and the earliest is reachable from `origin/main`,
  so the prior blobs stand. Reasons unchanged and still good: two prior rewrites
  already cost sha-maps every citing doc needs, a force-push does not purge
  GitHub-side unreachable objects, and the account is the built-in Windows one -
  `tests/test_no_secret_literals.py` separately proves no tracked file carries a
  key. Recorded exceptions the guard permits by RULE (not by name):
  `docs/_archive/**`, dated artifacts, and the append-only ledgers. Evidence:
  LEDGER 166.
- **gate-grades-a-tree-the-push-does-not-ship - DONE 2026-09-07 (cb19250).**
  Found by CS as a pre-push RACE: its hook graded `5192aaf` while the remote
  ended at `1ee8b64`. **LW never had that hook** - measured, `.githooks/` holds
  `commit-msg` and `pre-commit` only - so LW could not have the race. LW had the
  same hole in the WORSE form: the documented ORDER of `/done` (gate, THEN edit
  ROADMAP + LEDGER + WAKEUP + hand-off, THEN commit and push), so every session
  shipped doc edits the graded run never saw, deterministically. It fired on
  `e62543b` the same evening.
  **Fixed as ordering AND as an assertion.** `.claude/commands/done.md` is
  reordered: section 0 is now an explicitly non-binding pre-flight, every
  authored file (code, living docs, `LW-NEXT-SESSION.txt`) is committed in
  sections 1-6, and section 7 is the binding gate immediately before the push.
  Sections renumbered into run order; every cross-reference was internal to the
  document. Ordering alone is a sentence nothing checks, so `tools/done_gate.py`
  makes it provable: `bind` refuses a dirty tree (exit 2), refuses a tree that
  MOVED while the checks ran (CS's race, the one case a pre-run check cannot
  see), exits 1 on a red check, and only on green records the graded sha to a
  gitignored atomic receipt; `verify-push` refuses unless remote == HEAD ==
  graded. **Two deliberate departures from the acceptance line as written:**
  clean is `git status --porcelain`, not `git diff HEAD` - the latter is blind
  to an untracked authored file, exactly the shape of a new test module that
  gets graded locally and never pushed; and the pushed sha is read with
  `git ls-remote`, not `git rev-parse origin/main`, because that cache agrees
  with a push that never landed. `git stash list` is recorded on the receipt,
  never fatal - a stash does not change the tree being graded.
  14 arms in `tests/test_done_gate.py`, including the ritual document's own
  section order, so a re-shuffle goes red instead of quiet. Mutation-proven
  6 of 6 killed; two mutants initially SURVIVED because the implementation's
  pre-run and post-run checks cover for each other, and each needed an isolating
  arm (a check that tidies up after itself; a local commit the remote never
  got). LEDGER 171.

- **verbatim-payload-followups - two rows the 2026-09-07 review left open, both
  cheap and both named by RC.** (1) The `reap` arm for a stale
  `reserved-<key>.lock`: plant one older than the stale window, run `reap`,
  assert the owning repo can then take its floor. RC ACCEPTED the amendment and
  assigned it to LW; BLOCKED until the five agree the short repo keys
  (`rc lw rsc cs ll`), because the arm is meaningless before reservation exists.
  The paired second amendment is **DONE 2026-09-07**: "total holders never
  exceeds 5 + surplus" is now pinned in `tests/test_loop_concurrency.py` (7 new
  arms - the ceiling at widths 1/2/3/5/7, the same property measured on disk,
  and a negative control against an unbounded governor), mutation-proven 6 of 6
  killed and `ops/loop/slots.py` restored byte-exact. LW's suite is the only
  coverage that file has on either side. LEDGER 170. (2)
  **CANCELLED 2026-09-07: the payload was WITHDRAWN and is not coming back.**
  RC pulled `from-RC-verbatim/` from every inbox after its own PII finding and
  CONFIRMED it at 11:30 by measuring all five inboxes including its own: zero
  at every depth. RC's instruction is explicit - do not wait for the bytes and
  do not re-request the drop; ask for a specific file if it is ever needed.
  So this row is closed as un-actionable rather than parked. Found by the withdrawal report shipped the
  same day (LEDGER 168) - an arrival-keyed watcher would still be reporting this
  row as actionable. CS spent a night reasoning about the same bytes before
  discovering it never had them. The row as written:
  delta-scan RC's `tests/test_stop_claim_gate.py` (63 arms, formerly in
  `moon_sync_inbox/from-RC-verbatim/tests/`) against LW's
  `tests/test_claimed_green_gate.py` + `_history.py` (48 arms) and port the
  GENERIC arms only - most of RC's are RC-claim-specific, which is why the
  review queued this rather than bulk-copying. Evidence: LEDGER 163.
- **slots-hold-leaks-an-unreapable-lane - FIXED 2026-09-07 (`374c79e`, LEDGER
  157). RC has landed the same bytes (verified by hashing its tree, `629c3d51`);
  RSC is still on `1c4f8af4`, which is non-blocking - it vendors the file and
  never acquires. Close this row when RSC lands it.** LW authored the fix
  because LW is the other acquirer: `release()` retries the unlink then
  NEUTRALISES a lock it cannot delete (pid 0, ts 0) so the next `reap()`
  takes the lane, and `hold()` no longer logs `released` when the unlink
  failed. The in-place neutralise is justified by measurement - with a
  reader handle open the unlink fails (WinError 32), an in-place rewrite
  succeeds, and `tmp + os.replace` fails (WinError 5). LW's exposure was
  confirmed, not assumed: `loop_controller.py:916` runs every cycle under
  one pid. Original report below, kept for the reasoning.

- **(original report) a leaked lockfile whose holder is
  STILL ALIVE disarms the reaper (opened 2026-09-06, reported by RSC in
  `moon_sync_inbox/2026-09-06-2125-from-RSC-slots-leak-addendum.md`).** VERIFIED
  structurally on LW's own copy, not taken on report: `hold()` releases with
  `slot.unlink()` inside `except OSError: pass` (`ops/loop/slots.py:190`), so a
  release that loses the Windows ERROR_SHARING_VIOLATION race leaves the
  lockfile carrying the payload written at entry - a LIVE pid and a recent ts.
  Both of `is_stale`'s arms then answer "not stale" (`slots.py:94`), so `reap()`
  skips it and the lane is gone until `stale_after` elapses. The safety valve is
  disarmed by exactly the case that produces the leak. LW's exposure is the same
  shape as RC's: a long-lived controller runs many cycles under ONE pid, so a
  lane leaked in cycle N is unreapable for the life of the controller and
  narrows the bucket for all three repos. RSC measured 107 of 200 rounds leaving
  residue at backoff/jitter 0.02; the 30-of-30 wedged-bucket figure is stress
  amplification at zero backoff and must not be quoted as a rate. NOT FIXED
  HERE ON PURPOSE: `slots.py` is byte-identical-by-contract across LW, RC and
  RSC (CLAUDE.md Settled), so a change is a joint act with a re-pin, and LW's
  suite is the only coverage either sibling has. Decide the fix jointly - the
  obvious candidate is to make release verify the unlink and, failing that,
  overwrite the payload with a dead marker so the reaper can see it.

- **clean-zero-watermark - the acceptance standard is ZERO watermark; ghost,
  banding and faint residue all FAIL (operator, 2026-08-22). All five tracks are
  now RESOLVED; the detail lives in the decision docs, not here.** The bar is
  stricter than anything measured before it and settles several arguments: a
  near-zero detector score does not pass, "much reduced" does not pass, and
  template + scheduled fill on `105-cleanup` - logo gone, credit line down to a
  faint ghost - does NOT pass. No scalar is a verdict; the operator's eye on a
  1:1 crop is the gate, and nothing leaves `3.Cleaning Scratch` on a metric.
  - **E (healing brush) - FALSIFIED.** Built in full and beaten by the incumbent
    LaMa fill on all four captures. Splash art is PAINTED, not textured, so no
    translation repeats its content and the exemplar search has nothing to lock
    onto. `docs/CLEAN_HEAL_DECISION_2026-08-22.md`, LEDGER 124.
  - **A (analyse behind the mark) - DONE.** Busyness excluding the mark cut the
    error against ground truth 15x (221.3% -> 14.6% mean). The rule had been
    giving the two SMOOTHEST captures the minimum stroke because their marks
    were the loudest thing in frame. `docs/CLEAN_BEHIND_THE_MARK_2026-08-22.md`,
    LEDGER 125.
  - **B (comparison layer) - DONE.** Predicts where a line entering the mark has
    to come out and separates ERASED from MISALIGNED, which is the defect that
    got 45 candidates rejected and which a contrast measure passes. Every
    verdict agrees with the labels; abstains where no line crosses.
    `docs/CLEAN_COMPARISON_LAYER_2026-08-22.md`, LEDGER 126.
  - **C (spot heal with rollback) - DONE.** Per-blob healing costs nothing
    against a one-shot fill and buys a rollback that fires on exactly the engine
    shown to damage art at 1:1. `docs/CLEAN_SPOT_ROLLBACK_2026-08-22.md`,
    LEDGER 127.
  - **D (opacity / tone conditioning) - FALSIFIED.** The veil model fits none of
    the four captures (R-squared 0.49 / 0.32-0.81 / 0.00 / 0.04; an opaque
    painted signature carries no information about what is under it), and where
    conditioning fires it makes the frame worse.
    `docs/CLEAN_CONDITIONING_DECISION_2026-08-22.md`, LEDGER 128.
  - **F (DA overlay: pooled / analysis-by-synthesis) - CLOSED 2026-09-05, three
    attempts, all refused.** The DA preview overlay is TWO objects - an
    artist-specific credit line and a common logo veil - and the veil defeated
    (1) a 62-frame pooled matte, structurally: the estimators run on `highpass`,
    which discards the DC band a flat veil lives in, so they recover EDGES and
    are blind to the FILL; (2) analysis-by-synthesis, for want of a matched pair
    - no clean/watermarked duplicate exists in the corpus (closest consensus
    distance 18 vs accept 8), DA watermarks every render size down to the 300px
    thumb, and two sizes do not separate it; (3) shape-from-pool plus
    amplitude-from-ring, which measured `alpha = 0.0578 +- 0.0046` over 62
    frames (matching LEDGER's independent ~0.06) and damaged nothing, but cannot
    be validated per frame - 6 of 62 frames measure a NEGATIVE alpha.
    **Do NOT retry** the pooled path with more frames or looser thresholds: the
    blindness is in the transform, not the sample size. Registration is settled
    and is NOT the problem (every frame scale 1.00, shift +-3 px).
    `docs/POOLED_VEIL_RESULT_2026-09-05.md`, LEDGER 144.

  **Where it stands:** the FILL is settled on LaMa, now on an engine comparison
  rather than a single-engine replay. Mask generation is the remaining problem -
  see `clean-maskgen` below. **Corrected anchor:** the operator's brush is only
  1.05 to 1.65x the pixels their clean actually changed, measured on all four
  captures; this replaces the falsified "8x margin" and `CONTEXT_RATIO = 5.0`.
  **Do NOT redo:** the healing brush as a fill; conditioning from ring
  statistics; a pre-pass that writes into the region outside the rollback
  envelope; growing a spot to the stroke target or splitting a blob into
  disjoint stroke-sized pieces; lattice tiling; blanket mask escalation; or
  absolute/relative contrast residue as a STARTING detector. Ground truth for
  any future validation is the four hand-clean captures in
  `ops/runtime/clean/handedits/` (gitignored) - and they are PARTIAL gold, see
  `clean-maskgen`.

- **clean-maskgen - the question was MIS-POSED, and half of it is now solved
  (2026-08-22).** The centre-overlay template scored recall 0.405 / 0.086
  against the two gold brush masks and every attempt to tune it made things
  worse - bigger masks scored worse than smaller ones, which is impossible for a
  mask that is merely too small. Rendering it over the frame settled it: **the
  template finds the DA LOGO; the operator cleans the CREDIT LINE.** Different
  marks, different places, and every recall number was scoring a logo detector
  against a credit-line gold standard. So the hand-clean captures are PARTIAL
  gold. The template cannot find the line because it is a median over mixed
  uploaders and the line carries the uploader's name (SLIMSHADYWALLPAPER on 105,
  SMALLTAVERNWALLPAPER on 107), so the text averages out while the logo
  survives; per-uploader neighbour templates were tried and do NOT help at group
  sizes of 3 to 7. SHIPPED `tools/lw_clean_creditline.py`: the line is TEXT, so
  it is read - easyocr shown the layout band, enhanced two ways and unioned,
  reads joined into lines before verification, approximate substring matching -
  and the hit VERIFIES ITSELF because the string contains DEVIANTART, which no
  contrast measure can do. Measured: covers 0.9995 of the operator's brush on
  105 and finds a line on **39 of 80** queued slugs. The precision half of that
  census was measured WRONG and is CORRECTED below: it read `_cleaninitial` out
  of `4.Cleaning Done`, the frame going INTO cleaning, so the single fire
  (`230-cleanup`) was a mark that was still there and the 118 quiet frames were
  not evidence either. Against `_cleandone`, 230-cleanup reads nothing. The solid
  box is the right place and the wrong
  shape - it breaks a line and the rollback reverts it - so it is narrowed to
  the glyphs inside the verified box, giving **11.56 on 105 against 15.45
  untouched and the operator's own 8.08**, committed with 0 of 7 spots held.
  Still open: 107-class AREA marks, the logo itself, and the 41 slugs with no
  readable line. Doc: `docs/CLEAN_MASKGEN_2026-08-22.md`.

- **clean-creditline-queue - the lane ran on all 39 slugs and REDUCES without
  finishing; 13 of 39 still read a credit line in their own output and 16 held a
  blob (2026-08-22).** First run of the whole chain on the whole queue and the
  first output put in front of an eye, via `tools/lw_clean_creditline_run.py`
  (detect -> glyph mask -> per-blob heal with rollback -> re-read -> 1:1 sheet).
  Sheets, worst first: `ops/runtime/clean/creditline/run/REVIEW.md`. Two things
  the eye and the numbers found. **266f: the lane ERASED ARTWORK** - the poster's
  own gold `PRECISION IS PERFECTION` shares a row with `VEXXSOUL.DEVIANTART`, the
  joined box handed the filler 1228px, and the rollback stayed silent because
  flat text over flat ground breaks no chord. **The 259f class: still plainly
  legible at 1:1** after 9 committed blobs, because `GLYPH_PCT = 88` is tuned on
  one slug and lands on a fraction of the strokes over bright busy art. That is
  the sweep to widen next, and it has to be swept TOGETHER with the rollback: a
  0.36 percent mask change on 105 (79px of 22075) flipped a blob to revert and
  left a readable line.
  **Then three answers, 2026-08-23 (4a7c047, c993009, 4dbe017, 89f55ae).** A
  second round on the outputs improves the diagnostic (13 reading -> 10) and at
  1:1 trades text for SMEAR, degrading frames that were already done - so no
  blanket second round. The percentile is NOT the lever: no cell of a seven-wide
  sweep clears all ten still-reading slugs and three clear at none, because
  thickening merges strokes into one blob the rollback then reverts whole (akali,
  aatrox and miss-fortune come back UNTOUCHED at p40). **Scoping the REVERT is
  the lever** - give back only the band around the lines a fill damaged, grown
  until the ordinary verdict passes - and it puts 259f clean at the INCUMBENT p88
  and clears miss-fortune, which no percentile could. It is opt-in
  (`--scoped-revert`) because it costs what the rollback was buying: on akali a
  blocky smear stands where the bodysuit strap was, the layer having no chord
  there. **NEXT: chord COVERAGE**, not revert granularity.
  **Reader-quiet overstates removal by about one step** - 259f reads quiet at p70
  with the line plainly legible, viego at p80 with a ghost standing - so
  `still_reads` silence is never evidence and the three slugs round two called
  fixed inherit the doubt.
  **Do NOT redo:** any mask narrower than the read line's own bounding box
  (both variants measured worse), a blanket second round, or the GLYPH_PCT sweep
  for the never-quiet class. 266f wants a discriminator INSIDE the box - the
  overlay is achromatic where the tagline is saturated gold. Numbers and the
  reasoning for each: `docs/CLEAN_CREDITLINE_QUEUE_2026-08-22.md`.
  **Chord COVERAGE is DONE 2026-08-29 (d9861e9, 0184089, 30e98cd) - see
  `clean-chord-coverage` below.**
  **All 39 sheets have now been LOOKED at, flag-only, 2026-08-29: 37 flagged, 2
  clear.** Ranked shortlist at `ops/runtime/clean/creditline/run_scoped/TRIAGE.md`
  (gitignored, sits with the sheets); finding at
  `docs/CLEAN_CREDITLINE_TRIAGE_2026-08-29.md`. **The reader is near-blind by an
  order of magnitude: `still_reads` fires on 2 slugs, the eye reads a line on 28,
  so 26 reader-silent slugs still read as text at 1:1** - the known one-step bias
  is not a one-step bias, it is most of the queue. **A second failure mode the
  credit-line reader never watched: 17 slugs carry OBVIOUS collateral damage**
  (painted line cut where the mask crossed, flattened blocky patch, deformed
  silhouette), independent of residue - 105-cleanup and 123f are residue NONE with
  damage OBVIOUS. The two unflagged are `ashe-...-dlzcque-fullview` and
  `bayonetta-...-dm7iiug-pre`. Named patterns to aim at: the `(c)` ring glyph
  survives intact on at least 10 slugs while the letters after it clear; the mask
  starts inboard of the mark on 124f and syndra-dlsfcue (`SMAL` left standing);
  266f still erases the poster's own gold tagline. **This is a FLAG, not a
  verdict** (ADR-008) - 5 of the 39 were independently re-read and all 5 agreed,
  including both clear calls, but the other 34 are single-agent observations and
  are a priority ordering for the eye, not evidence. Disposition remains the
  operator's.
  **The `(c)` ring case is FIXED 2026-08-30 (47903a2) - see LEDGER 138.** The
  mask's left edge was `box_x0 - PAD` and the mark's true left extent is not a
  constant (20-21px on small type, 35px on large, 43-44px at scale 1.2, 76-96px
  where OCR also drops leading letters), so ring ink lay outside the mask on 22
  of 39 - not the 10 the eye counted. `left_extent()` now MEASURES that edge, and
  a second separable cause is fixed too: `glyph_mask`'s box-global p88 was set by
  the brightest thing in the box, so an art highlight dropped the overlay's own
  strokes (soraka kept 9 percent of its ring with the box fully covering it).
  Ring ink outside the mask 6923 -> 1871 px, 17 slugs to zero, 0 worse, box px
  median 1.044x. **The queue's 39 outputs predate the fix and need a re-run
  before the disposition above means anything.**
  **Do NOT redo:** the achromatic gate (105's ridge sits at saturation 5-8 and
  270f's ring at 9-21 - it removes the mark before the artwork), `median + k*MAD`
  for the glyph threshold (the failing slugs have BROAD box distributions and the
  healthy controls narrow ones, so it bites the wrong slugs), keying the ink
  floor off the in-box glyph median (0.3x no-op, 0.7x costs four slugs), or an
  unbounded leftward walk (it CHAINS across artwork - 270f reached x=907 with its
  mark starting at 981).
  **The queue WAS re-run under the fix (run_ringfix, 39 slugs, exit 0) and all
  39 sheets re-triaged 2026-08-30.** Ring GONE on 28, FAINT 3, INTACT 3 (the
  three are aatrox plus the two dropped-letter slugs, exactly where the fix said
  it would not reach), no ring in crop 5. Residue LEGIBLE 28 -> 19, NONE 4 -> 8.
  Reader held/still-reads both went to 0. **Only ONE slug is unflagged outright:
  `107-cleanup`.** Sheets: `ops/runtime/clean/creditline/run_ringfix/`.
  **CAUTION on the damage counts: the two triages are NOT comparable on damage** -
  the rubric changed between them (a ring field was added and damage scanning
  emphasised) and different agents rated each, so the vision reading of 17 -> 27
  OBVIOUS overstates it. The comparable evidence is pixel measurement:
  painted-edge loss rose 1.065x under the wider mask, and invented-bright
  artifacts stayed flat at 1.00x.
  **The two MORE coverage modes the re-run exposed were both measured
  2026-08-30 and BOTH framings were wrong. See
  `docs/CLEAN_CREDITLINE_EDGES_2026-08-30.md`.**
  - **RIGHT-edge truncation is real on 4 of 39, not 2** - `viego-the-ruined-king`
    (must reach 52px past the box), `261f` (117), `aidraw-...-watercolornessie`
    (56) and `266f` (152, and it is the known detection failure). `syndra-dlsfckr`
    is NOT one; its `.COM` is fully covered.
  - **A right-edge WALK is FALSIFIED - do NOT retry it.** Five rule families,
    60+ configurations over all 39: the `left_extent` mirror, a band-calibrated
    walk, a walk-only ink map at lower beta, a leading-row guard, a geodesic
    `escaped_ink` strip, and an edge-adjacency gate. No cell reaches 4 of 4
    without moving more than half the controls, and nothing reaches 3 of 4 for
    less than a control p90 of 57px of mask growth INTO ARTWORK. Also dead: a
    `.COM` suffix predicate on the read text (too garbled - `105-cleanup` reads
    `EOM OM` with a correct edge) and glyph-pitch extrapolation from the read
    length (`261f` normalises to 18 chars for 25 glyphs). `easyocr` re-run on all
    four returns NO read right of the box, so there is nothing discarded to
    re-attach, and `local_ink` cannot see the tails at all (0-2 ink rows per
    column against 100-137 in-box) because they are faint for the same reason
    OCR dropped them. **The ends are not mirror images:** the left neighbour is
    the `(c)` ring, ONE compact 17-34px object in the line's own leading, which
    is why one hop describes it; the right neighbour is more of the SAME text in
    several glyphs, and the repeated hops it needs are exactly what walks into
    art. Reading those tails needs a text-specific measure (stroke periodicity
    on the baseline, or a glyph model), not another threshold.
  - **The mid-line HOLES are not a mask failure at all, and they are already
    FIXED.** Inside the mark's own measured row band the shipped mask's gaps on
    `syndra-dlsfckr` are median 2px, **max 3px** - nothing to close - and
    `escaped_ink` reaches 0 px inside the read box on 37 of 39 (the two
    exceptions are the documented band-clipped pair). The `R`, `X` and partial
    `D` came back because the SCOPED REVERT handed them back: 1048 mask pixels
    ended byte-identical, sitting exactly on those glyphs where the corridor
    follows an art edge crossing the line. **The re-run settles it: under the
    shipping default `syndra-dlsfckr` hands back 1048 -> 46 px and the whole
    line, `R` and `X` included, is GONE at 1:1.** Removing the art limbs from
    the mask changed the blob structure so the corridor no longer crosses the
    glyphs. There was never a hole lever to build - `88e1ac7` had simply never
    been run over the queue.
  - **Shipped instead (no pixel moves):** `handed_back_px` per step and
    `handed_back` per plan / lane record / run summary / `REVIEW.md`, sorted
    above the repaint width. It is NOT `reverted_px` - a commit hands back
    whatever the filler returned unchanged and `reverted_px` is 0 there by
    definition. Queue total over the recorded 39: **18,835 px**.
  - **Do NOT redo:** local stroke contrast at the handed-back pixels as a
    legibility gate. It splits the queue cleanly and measures the wrong thing -
    `259f` keeps 84.6 percent with a CLEAN output because the corridor restored
    an art streak. Overlap with the glyph selection does not separate them either
    (`syndra` 19.8 percent, `259f` 26.7, `akali` 48.7).
  - **The operator's call:** refusing a corridor that hands a legible letter back
    falls through to a WHOLE revert today (28.13 percent handed back against
    1.80). Making refusal mean COMMIT instead is one line plus a lane re-run.
  - **THE QUEUE IS NOW RUN UNDER THE SHIPPING DEFAULT (2026-08-30):**
    `ops/runtime/clean/creditline/run_shipdefault/`, 39 slugs, exit 0, the first
    run under `88e1ac7`. `box_px` identical to `run_ringfix` (2,057,596), so it
    is like for like: mask px **1,092,590 -> 948,500 (-13.2 percent, reproducing
    LEDGER 139 on a live run)**, blobs 403 -> 430, committed 383 -> 415, partial
    20 -> **15**, held 0, still_reads 0, mark handed back **17,171 px**.
    **`handed_back` is the ONLY field ordering this review** - `held` and
    `still_reads` are 0 on all 39, so both fields above it in `review_order` say
    nothing. Top two checked at 1:1 and both are FAILS the old fields missed:
    `anime-poster-of-soraka` (2641px) still reads `(c) .VE?ENINE` and a fully
    legible `.COM`; `105-cleanup` (2037px) is clean on `DEVIANTART.COM` and
    carries a faint `L ... WALL` ghost. Ranked correctly first try - evidence the
    ordering is useful, n=2 by eye, still not a gate.
  - **NEXT is the operator's eye over `run_shipdefault/REVIEW.md`, worst first.**
    Approve what clears zero residue into `4.Cleaning Done`; send the rest to the
    manual IOPaint lane. Per ADR-008 a vision pass may FLAG but never approve.

- **clean-fill-damage - the fill destroys artwork because the MASK contains
  artwork; FIRST CUT SHIPPED 2026-08-30 (88e1ac7, LEDGER 139), and the remainder
  is an operator trade.** Measured over the 39-slug queue: the outside-mask
  identity guarantee is INTACT (0 changed px outside), 75.2 percent of every
  strong source edge inside a mask is destroyed, and **75.7 percent of flattened
  px belong to structures with a limb 6+ px OUTSIDE the mask** - artwork passing
  through. Thin bright ridges die at 89.2 percent. `escaped_ink()` now follows
  ink back in from outside the read region and subtracts it: mask -13.2 percent,
  strong edges in mask -17.0, ridges -16.7, with ZERO registered logo ink lost
  and operator-brush ground truth at 99.3 / 94.7 percent.
  **Do NOT redo:** whole-structure containment ratio (it eats the entire (c)
  glyph on bayonetta-dm7iiug, where glyph and art merge into one 700px structure
  at 337 in / 340 out - no ratio separates them - and costs 10 percent of the
  operator's brush ink); morphological separation first (erosion fragments ink
  into contained pieces, near no-op); a hybrid ratio-plus-reach (identical to
  reach alone); ring registration below ncc ~0.5 as a mark anchor (it lands on
  artwork); and "revert more" - reverting worst-first buys 80 percent of the art
  for 72 percent of the mark, barely off the diagonal, with NO knee at any slug.
  **The named open trade:** only 17 percent of the art damage is removable
  without measured mark loss. `LIMB_REACH` 32 reaches 24 percent with still no
  measured loss; the first mark loss is at 36. The rest of the damage is art
  running THROUGH the OCR-verified box, and reaching it means overruling the only
  evidence the module has. Raising the constant is one number plus the test that
  pins it - an operator call, not an engineering one.
  **Also open:** `266f` masks the poster's OWN gold typography with zero credit
  line in that region (5.7 percent of queue damage) - a detection failure, not a
  fill failure.

- **STILL OPEN - the dropped-letter class.** syndra-dlsfcue is 62px short and
  blood-moon 61px because easyocr swallowed `SMALL` / `AIAI` outright. No hop
  count serves both classes (unlimited hops still left them 9px and 39px short
  while paying 67px of over-reach elsewhere), so this wants its own rule - most
  likely a right-to-left continuation keyed on the mark's own baseline rather
  than on run termination.

- **clean-chord-coverage - DONE 2026-08-29, and the lever the name implies was
  falsified on the way (d9861e9, 0184089, 30e98cd).** The rollback could only
  judge a fill where the layer put a chord, and over the 39 recorded queue plans
  it mostly could not: 269 of 357 steps (75.4 percent) and 47.6 percent of every
  repainted pixel committed on `no-evidence`, which is an unconditional commit.
  **Do NOT redo the `GRAD_MIN` sweep, and do not spend a pass on `_expected_at`
  or the greedy pairing:** solving both filter losses perfectly moves blind
  steps only 269 -> 235, and LOWERING `GRAD_MIN` makes coverage WORSE (239 at
  3.0, 252 at 2.0, against 235 at the incumbent 6.0) because
  `boundary_crossings` dilates the hot pixels and takes one centroid per blob,
  so a lower floor MERGES neighbouring crossings into fewer and mushier ones.
  The cause is structural - the mask is a field of letters, a chord needs two
  crossings on the SAME small blob, and the corpus supplies about one, so the
  layer discards 93 percent of its own evidence by construction. Shipped
  `build_stubs()`: a lone crossing predicts a RAY, weaker on purpose (one
  anchor, so ERASED only and never MISALIGNED, which is the akali failure) and
  proven against its own untouched frame before use. Measured end state:
  no-evidence 269 -> 125, held 21 -> 37, still_reads 13 -> 13 with NO slug
  moving either way, 105-cleanup back to 11.562 against the hand-clean gold and
  byte-identical to the incumbent. Two verdict bugs the run found were in
  `_verdict`, not the stubs: pooling the medians let 825 stubs silence NINE
  chord reverts, and the broken-line ANY-rule let ONE stub revert 105 on a fill
  that was measurably moving toward the operator's own result. Both fixed, no
  new constant. **STILL OPT-IN** (`stubs=False`, `--stubs`) - the numbers say go
  and the eye has not seen it. Sheets:
  `ops/runtime/clean/creditline/run_stubs3/`.
  **The remainder, measured 2026-08-29 (dac7872 and the reach commit):** 116 was
  a forecast; the run leaves 125, and they are TWO populations. 54 steps
  (25,618 px) have not one ring pixel clearing `GRAD_MIN` - flat art, agreed by
  an independent measure that never reads that ring (`gradient_behind` 0.59
  median against 2.11) - so there is no line to lose and the rollback is not
  blind there, it is unemployed. `hot_band()` names it and every step now
  records `surround` as flat or lines; no verdict moves. The other 71 lose a
  line the layer DID see: 101 crossings to a blocked expectation, 26 to a stub
  ray that missed, 13 to the self-check. Raising the STUB expectation reach 6
  -> 10 (`STUB_REACH`, chords untouched at `EXPECT_REACH`) takes 65 of them:
  self-check survival identical at 91.6 percent, `still_reads` 13 with no slug
  moving either way, 105-cleanup still 11.562. `STUB_LEN` swept and CLOSED -
  12px wins, longer rays fail their own self-check. **The 65 were then decomposed stage by stage** (same
  plans, shipped layer): 11 have every nearby line entering the letter NEXT
  DOOR or running alongside, 3 have no cluster at all, 15 are mixed, and 36 have
  a line oriented into them with no expectation obtainable - of the 366
  crossings still missing one, 162 (44 percent) are never readable out to 40px
  because the probe's 9px swath does not fit. `MAX_CROSSINGS` and the structure
  tensor drop NOTHING (0 and 0, measured, was asserted). A derived expectation
  from the crossing's own strength is FALSIFIED - within 25 percent of the probe
  only 46.8 percent of the time, and `expected` is the denominator of every
  ratio - do not redo it. Reach 20 clears the acceptance bar (reads 13 unmoved,
  105 still 11.562) and is NOT shipped: it buys 6 steps for two more held blobs
  and a 20px-distant denominator, so it wants an eye, not a sweep -
  `ops/runtime/clean/creditline/run_reach20/`. **Still open:** about 35 steps
  where a line enters and could be measured, with every threshold lever now
  shipped or falsified, and the stub self-check is ONE
  ratio that cannot separate a DRIFTED line from an ATTENUATED one, so the
  `centre_overlay` veil bucket would pay far more than this glyph lane's 79 of
  1,103.
  **`--stubs` and `--scoped-revert` were then run TOGETHER for the first time
  (every recorded run had exactly one of them on, `run_stubs4` carries
  partial=0):** held 37 -> 2, partial 0 -> 33, pixels given back 283,190 ->
  25,553 (a 91 percent cut, every surviving revert at the smallest 4px band),
  slugs the reader still finds a line in 13 -> 2, 105-cleanup unchanged at
  11.562. `dark-cosmic-ahri` step 0 goes from 7,815 px undone to 835. NOT a
  clean sweep and the run proves the standing rule: ahri was reader-SILENT in
  `run_stubs4` while carrying an almost untouched mark and READS after the
  scoped fill removed most of it. Sheets:
  `ops/runtime/clean/creditline/run_stubs_scoped/REVIEW.md`.
  Doc: `docs/CLEAN_CHORD_COVERAGE_2026-08-29.md`.
  **VERDICT 2026-08-29, operator, one per lane: `--scoped-revert` DEFAULTS ON,
  `--stubs` STAYS OPT-IN.** The pair was being compared against a missing
  control - `--scoped-revert` ALONE had never been run over the queue, so the
  2x2 lacked its fourth cell and the pair was credited with everything scoped
  does by itself. Measure is the mark HANDED BACK (mask px ending
  byte-identical to untouched, which is what a revert restores): whole revert
  272,893 px (28.13 percent) / stubs 285,870 (29.47) / **scoped 17,508 (1.80)**
  / both 29,474 (3.04); held blobs 21 / 37 / **1** / 2; slugs still reading
  13 / 13 / **2** / 2. Scoped is not worse than the whole revert on ANY of the
  39 and cannot be (the band is a subset of the blob AND the ordinary verdict
  must pass on it). Stubs improves NONE of the 39 and regresses four, one of
  which (`107-cleanup`) goes from clean to a legible `(c) SMALL`. `105-cleanup`
  is 11.562 against 15.454 untouched under all four - one sha, nothing for
  either flag to change. **The stated blocker for scoped is dead:** akali
  commits all 17 blobs with 0 held / 0 partial in every configuration and its
  output is byte-identical across all four, so the blocky strap smear is the
  FILL's and is in today's default; the objection came from the p40/p80 sweep
  cells, not the shipped percentile. Shipped: `scoped=True` default,
  `--no-scoped-revert` (the `--no-rollback` convention) on both runners and the
  spot CLI with `--scoped-revert` still accepted so recorded commands run, and
  `tools/lw_clean_lane_compare.py` (every configuration in one column at 1:1,
  cropped to what differs). **Do NOT redo:** re-opening scoped on the akali
  smear, reading the pair run as the strongest configuration, or defaulting
  stubs ON on the coverage argument alone. Strips:
  `ops/runtime/clean/creditline/lanes/REVIEW.md`.
  Doc: `docs/CLEAN_LANE_DEFAULTS_2026-08-29.md`.

- **clean-automated-lane-closed - 0 of 87 automated cleaning candidates were
  accepted by the operator across 4 review rounds, 2026-08-22. STOP tuning the
  current removal + fill stack; it is not a threshold problem.** Rounds: 45
  centre_overlay with LaMa fill (0), the same 45 algebraic-only with no fill (2,
  and only on the signature), 40 region/singleton/faint (0), and the 7 that
  survived the shared coverage guard at 10.5-24.5% coverage (0). Three different
  mask sources and both fill decisions land in the same place, which points at
  the FILL being the wrong instrument for this corpus rather than at any single
  mask or threshold. The only slugs that left the queue did so because the
  DETECTOR was wrong and there was no mark (see clean-detector-false-positives).
  The remaining 80 are staged for hand IOPaint with per-slug input, derived mask
  and re-entry commands in `docs/CLEANING_HAND_LANE_2026-08-22.md`. Anything that
  reopens the automated lane needs a NEW method and an eye-anchored objective -
  the detector score is falsified as a proxy (LEDGER 101-103 plus these rounds).


- **clean-detector-false-positives - the detector flags IN-ART content as a mark:
  7 named by the operator 2026-08-22. This OVERTURNS the standing "false positives
  are currently zero" claim - do not cite that line again without re-measuring.**
  In-art TEXT and ICONOGRAPHY: a jersey name (`177-cleanup` "faker"), a lore line
  (`186-cleanup` "unto darkness unto light"), a snowflake (`193-cleanup`), a
  faction motto plus its icon (`darius-the-hand-of-noxus-by-vexxsoul-dm8cizj-pre`),
  and three more in the faint lane (`75f`, `dbwtlkx-eeb94ce2-...`, `image3`).
  Nothing in the gate distinguishes typography that BELONGS to the picture from
  typography stamped ON it, and the corpus is League splash art where in-art
  lettering is everywhere. The old census could not have caught this: it scored
  the detector's own output band, not the class of object. These 7 frames carry
  no mark and must never be inpainted. The 7 were APPROVED UNEDITED the same day
  on the operator's call (clean-scan passthrough, original pixels, no inpaint):
  `4.Cleaning Done` 485 -> 492, `3.Cleaning Scratch` 87 -> 80. STILL OPEN: whether
  the gate needs an in-art-text rule at all, or whether this stays a human call.
  Evidence:
  `docs/CLEAN_OVERLAY_REVIEW_2026-08-22.md`.

- **clean-coverage-guard-shared - FIXED 2026-08-22 (our bug, found by operator
  review).** The 25% mask-coverage refusal was written `if faint and not
  faint_mask_ok(cov)`, so ONLY the faint lane was guarded; the region lane ran
  masks covering a median 47.6% of the ROI (24 of 27 over the line, 16 over 40%)
  straight into LaMa, which is why the operator saw "the entirety of the cropped
  regions ... blurred out". The ceiling is now shared (`COVERAGE_MAX`,
  `mask_coverage_ok`) and a refusal DELETES any candidate a previous permissive
  run left behind, so a stale after-image cannot keep showing up in the review
  sheet as a result. Re-run under the guard: region 27 -> 3 candidates,
  singletons 3 -> 1, faint 12 -> 9; the rest refuse to the human lane, which is
  the correct answer. Pinned by `tests/test_lw_clean_coverage_guard.py`.


- **clean-overlay-fill-rejected - the overlay lane's LaMa fill FAILS operator
  review 45 of 45 - NEW 2026-08-22, measured on the whole centre_overlay bucket.**
  The lane ran clean on its own numbers (median `overlay_score` 0.2712 -> 0.0647,
  zero frames left at or above the 0.15 flag) and the eye rejected every frame.
  Two defects, different stages: (1) blur, smudges and MISALIGNED lines where art
  crosses the matte-plus-buffer boundary - that is the LaMa residual FILL, since
  the algebraic pre-pass inverts the matting equation per pixel and physically
  cannot displace or invent a line; (2) the signature's `(c)` left behind, which
  is removal being too weak, the already-known partial state of the removal half.
  Registration is NOT the obvious culprit: the fitted shift is 0 or +-1px on 43 of
  45 frames (outliers one 24px, one 30px, one scale 1.12) - worth a look, but it
  cannot explain a whole-bucket rejection. Verdicts and the four defect classes
  (A 17 / B 25 / C 1 / D 2) are in `docs/CLEAN_OVERLAY_REVIEW_2026-08-22.md`.
  ANSWERED THE SAME DAY, against the fill hypothesis: the operator reviewed the
  algebraic-only column too and passed exactly TWO frames (`32-cleanup`,
  `9-cleanup`), both on the SIGNATURE only; the other 43 failed. So dropping LaMa
  does not make the lane shippable - the REMOVAL is too weak, and fill tuning is
  moot until that changes. Do NOT spend a pass on the fill.
  WORSE, and this is the structural finding: the lane's own instrumentation
  carries NO signal about the outcome. Every recorded field for the two passes
  sits inside the failing distribution (score_before, score_after, gain, seed_px,
  mask_px, coverage - table in the doc), and three FAILING frames fitted the same
  shift (-1, 0) at scale 1.0 as both passes. The global gain 2.0 was grid-fitted
  against the DETECTOR'S OWN post-removal score, and two operator reviews have now
  falsified that score at both ends: it called all 45 clean when none were, and it
  cannot separate the 2 acceptable frames from the 43 unacceptable. Any tuning loop
  over it optimizes against a measure known to be blind - a stronger removal needs
  a different objective anchored to something the eye agrees with.
  OPEN FORK for the operator: keep investing in automated overlay removal (which
  needs an eye-anchored calibration set to replace the falsified objective), or
  route the whole centre_overlay bucket to hand IOPaint. Sheet:
  `ops/runtime/clean/review_overlay.html`. Nothing was approved; all 45 are still
  in `3.Cleaning Scratch`.


- **clean-566-disposition - DONE 2026-08-22, gate-driven (operator call). 479 of
  566 slugs left `3.Cleaning Scratch`; 87 are held for the manual IOPaint lane.**
  The operator chose shape (1): inpaint the `auto` bucket, approve the `clean`
  bucket through to `4.Cleaning Done`, park `qa` in scratch. Triage regenerated
  first and reproduced the 2026-08-17 split EXACTLY (460 `clean` / 86 `qa` / 20
  `auto` over 566), so the disposition ran against a verified-current gate, not a
  five-day-old file. Result: 460 `clean` approved, 19 of 20 `auto` inpainted
  (simple-lama) and approved, 87 held (`259f` is the 20th `auto` - its inpaint
  FAILED the G2 verify gate, so it fell to the queue rather than shipping a bad
  edit, which is the gate working). `4.Cleaning Done` 6 -> 485, scratch 566 -> 87,
  `needs_attention` 0. Driver is `tools/lw_clean_dispose.py` (+ 7 tests): it never
  re-decides a verdict and never moves a slug itself - every transition goes
  through `lw_pipeline`, so an ADR-008 / ADR-009 refusal is RECORDED and skipped,
  never forced, and approvals are attributed `--actor tool:auto-approve` so the
  rail can see a non-operator approver. The held set with per-slug reason is
  `docs/cleaning_qa_queue_2026-08-22.md`: 45 `centre_overlay`, 27 `not_border`,
  12 `faint_mark`, 1 each `watermark_ocr` / `area_too_large` / `low_conf`.
  **OPEN REMAINDER:** the operator's 13 named `ref_*` slugs are recorded nowhere
  in the repo (only the count survives), and the gate held 9 of them as `qa` - the
  other 4 sit in the `clean` bucket and were approved with everything else. If
  those 4 are named later the reopen route is `save-working --tool
  operator-select` -> submit -> approve; there is no reverse stage transition.
  ADR-009 still binds: ONE engine per submission, no automatic ladder.

- **cleaning-detector-recall - the detector MISSES marks: 14 confirmed false
  negatives, ~12 percent of the `clean` verdicts - NEW 2026-08-11, measured.**
  The mirror of the precision census, and the reason precision alone was not an
  answer. Population: all 302 `_firstdone` images in `2.First Pass Done` (the
  21-slug cleaning queue CANNOT answer recall - it is this detector's own 2026-
  07-16 `auto` output, so scoring it there is circular). Gate verdicts: 27
  `auto` / 46 `qa` / 229 `clean`. The 229 `clean` were split into 4 strata; S1-S3
  (17 images) were censused in full and S4 (212, no box at any conf) sampled at
  n=14. Confirmed by eye: **14 false negatives** (13 of them in S1-S3),
  extrapolating to ~28 of 229 (~12 percent), wide interval.
  ROOT CAUSE, measured: **11 of the 14 are ONE object** - the semi-transparent
  DeviantArt centre overlay. It fails on three axes at once: YOLO scores it
  0.11-0.25 against a 0.35 detect floor (2 carry no box even at 0.10), OCR reads
  it as garble so `is_watermark_text` never sees "deviantart", and its centroid
  is mid-frame so even a boxed one lands on `qa/not_border`. The other 3 are a
  thin painted signature (2; YOLO gives one of them NO box at any conf) and an
  artist wordmark placed away from the bottom band (1).
  DO NOT "fix" this by weakening `is_lol_logo`: the wordmark KEEP rule fired on
  all 4 S1 misses and looks guilty, but in every one the missed mark ALSO had no
  box above the floor, so removing the rule catches nothing and re-opens the
  false positives that are currently zero. DO NOT simply drop the conf floor
  either - the low-conf box is a good FLAG signal (13 of 17 low-conf clean
  images are real misses, ~76 percent) but a bad AUTO signal.
  DETECTION HALF SHIPPED 2026-08-11 - **gate v3, `clean` 229 -> 214 over the
  live 302-image corpus.** `tools/lw_clean_overlay.py` median-stacks the
  high-pass of frames that carry the overlay into a template (the mark is the
  same pixels in the same place, so the art cancels and the logo + URL come out
  legible) and scores a frame by masked normalized correlation with a tight
  shift search. Three measured decisions, not guesses: clip the high-pass at
  +-8 levels (positive median 0.112 -> 0.220 leave-one-ARTIST-out), search
  +-3.0% h / +-1.6% w (weakest positive -0.02 -> 0.100), and keep that window
  TIGHT (a +-90/+-200px search lifts CLEAN frames to 0.095 faster than it lifts
  positives). `OVERLAY_SCORE_MIN = 0.15` is calibrated: 15 clean images flip to
  `qa`, all 15 verified real marks, ZERO false; at 0.12 three carry no mark.
  Live re-gate: 38 rows changed - 15 `clean` -> `qa/centre_overlay` (including
  the two `lol_logo` cases), 22 `qa` -> a better reason, and 1 `auto` -> `qa`
  (`239f` carries a banner AND an overlay, so auto would have left the overlay).
  Invariants: the flag can only produce `qa`, never `auto` (an unattended edit
  driven by a correlation score would spend the 0-false-positive precision), and
  it sits above the `n == 0` and `lol_logo` rules but below `watermark_ocr`.
  The template is a derivative of a third party's watermark: it lives in
  `ops/runtime/clean/` (gitignored), is rebuilt from the 19 verified slugs
  listed in the doc, and a MISSING template means the flag is simply off (v2
  behaviour exactly), which is how CI runs.
  REMOVAL HALF LANDED 2026-08-11, PARTIAL AND HONEST ABOUT IT: `estimate_matte`
  + `remove_overlay` recover a continuous alpha from the collection and INVERT
  the matting equation (`J = (I - aW)/(1-a)`), so the reconstruction is faithful
  - no fill, no hallucination, outside-region identity by construction. Measured
  over the 19 confirmed frames: detector score **median 0.565 -> 0.112, 17 of 19
  under the flag**. Method: register -> interpolate a background seed DOWN
  COLUMNS (rows biased alpha 20 percent low; a median seed is R&D method 4's
  recorded failure) -> alpha shape = median of `(I-J)/(W-J)` -> ONE global gain
  fitted against the detector's own post-removal score (grid optimum 2.0,
  interior: 1.0 -> 0.258, 2.0 -> 0.120, 3.0 -> 0.166).
  TWO DEAD ENDS, MEASURED, do not redo: a per-pixel least-squares fit of the
  matting equation reaches only **R^2 0.10** on this corpus (the background-seed
  error exceeds the mark, so an R^2 gate either drops 93 percent of the mark or
  lets art through, and spatial pooling made it worse); and re-estimating W PER
  PIXEL **diverges** (mean post-removal score 0.149 -> 0.174 -> 0.254, W drifting
  154 -> 87) because alpha and W trade off without a prior.
  **The mark is REDUCED, NOT ERASED** - at 1:1 a faint ghost survives on every
  frame. So it ships as a QA-lane candidate generator
  (`--build-overlay-matte` / `--remove-overlay`, writing a candidate plus a
  before/after JSON and PRINTING the save-working/submit commands), never auto,
  never auto-approved.
  **CORRECTION (same session, before wrap): matting-Laplacian + IRLS ALREADY EXIST and were measured to CAP.** `tools/lw_clean_dekel.py` (LEDGER 29, commit `bad25c8`) is a full Dekel - Levin closed-form matte, IRLS alternating minimisation, sub-pixel phase-correlation alignment, filled alpha init - and it leaves a legible dark-stroke ghost for a structural reason: the mark is stylised white-fill PLUS dark-outline text, which a single achromatic W cannot invert, and the residual is mark stroke entangled with real art. The shipped answer to that ghost is LEDGER 30, `tools/lw_clean_iopaint.py`: masked LaMa with a COMPLETE mask that covers the dark OUTLINE, not just the bright fill, seeded by a cross-image filled matte. So the next step for the centre overlay is to feed THIS matte into that mask builder - not to rebuild the algebra.
  INPAINT HALF LANDED 2026-08-11 (LEDGER 95): the matte now SEEDS the LaMa mask.
  `lw_clean_iopaint.py --overlay` registers the frame, runs the algebraic
  pre-pass, thresholds the matte into a mask (open -> density speck filter ->
  dilate -> bbox ROI), completes it with THIS frame's own residual inside a gate
  (7px across the strokes, 40px ALONG the credit line, bright-only sideways
  because the nearest art is a dark lip line), and runs ONE LaMa pass. Removal
  needs a WIDER band than detection - the logo's top edge sits at y/h 0.506 vs
  the detector band's 0.55 - so `REMOVAL_BAND = (0.45, 0.85)` and a separate
  `*_wide.npz` pair exist; the detector's calibrated `BAND` was NOT moved.
  Measured over all 32 flagged slugs: detector score median **0.310 -> 0.069**,
  worst 0.696 -> 0.115, **32 of 32 under the 0.15 flag** (was 0 of 32). By eye the
  CREDIT LINE clears completely on busy art; the logo's flat veil survives on
  smooth art. Evidence `docs/CLEAN_OVERLAY_INPAINT_2026-08-11.md`, candidates in
  `ops/runtime/clean/overlay_lane/`.
  VEIL HALF LANDED 2026-08-11 (LEDGER 96): `estimate_veil` recovers the logo's
  FLAT interior, which the high-pass template cannot see (matte alpha there was
  exactly 0.0). Whitening against a background window wider than the veil, a
  CONSENSUS low quartile across the collection instead of the median, a support
  that is opened + closed and deliberately stops ~10px inside the true edge, and
  the amplitude CALIBRATED against the veil's own boundary step: recovered
  **alpha 0.133** (an interior optimum), matching the ~0.14 read directly off the
  step. The veil rides in the matte beside the stroke alpha, is applied by the
  INVERSION, and only a 9px ring at its boundary is handed to LaMa - never the
  310x240px interior. Re-run over the 32: median 0.310 -> 0.068, 32/32 under the
  flag, and by eye `245f` / `miss-fortune` come back clean where part 1 left a
  polygon.
  FAINT-MARK HALF LANDED 2026-08-11 (LEDGER 97) - **gate v4 closes (b) and (c)
  together, and it needed no new model.** The census's "no box at any conf"
  claim was measured at ITS OWN 0.10 sweep floor, not at any confidence: swept
  to 0.02 all four remaining misses carry a YOLO box ON THE MARK -
  `110-cleanup` 0.1366, `p2402-kda-evelynn` 0.1228, `karthasbasefinal` 0.1135,
  `dragon-slayer-pantheon` **0.0522**. The production floor is 0.35, so every
  one was discarded before `gate_decision` ran. `detect_image` now runs YOLO
  ONCE at `FAINT_CONF_MIN` and splits at `DETECT_CONF` into `yolo` + `faint`
  (free, not a second inference - NMS never suppresses a box with a weaker one,
  measured identical on 39 of 39 firstdones), and `gate_decision` applies the
  flag as a POST-PASS over the v3 ladder.
  **The post-pass placement is the safety argument, not a style choice.** Two of
  the misses have no confident box, so an ORDERED rule would sit above `n == 0`
  - which is above `bottom_banner` / `corner_mark` too - and 7 currently-`auto`
  live images carry a qualifying faint box. Those 7 would have silently
  demoted. The post-pass is provably incapable of it: it only rewrites `clean`
  -> `qa`, and leaves an existing `qa` reason alone (21 live rows) because the
  ladder's reason is more specific than `faint_mark`.
  Two calibrated constants. `FAINT_CONF_MIN = 0.05`, swept over the live 302:
  floor 0.10 -> 3 flips 3 real 0 false; 0.07 -> 4 flips 3 real 1 false; 0.05 ->
  5 flips 4 real 1 false. 0.05 ships because it is the ONLY setting reaching the
  0.0522 signature; 0.10 is the zero-false alternative, one constant away.
  `FAINT_MIN_W_FRAC = 0.05` narrows the noisy tier on one prior - a credit line
  is WIDE - and the widths separate with nothing in the gap (real 0.076 / 0.100
  / 0.157 / 0.176 vs art 0.009 / 0.021 / 0.033). The prior is NOT universal and
  is not claimed to be: it would reject 4 of 28 live `auto` boxes and 2 of 65
  `qa` boxes (small square-ish marks), and the one false flag it admits is 0.154
  wide.
  LIVE RESULT: 26 auto / 62 qa / 214 clean -> **26 auto / 67 qa / 209 clean**.
  Exactly 5 rows change, all `clean` -> `qa/faint_mark`, NO auto lost, and each
  was cropped and looked at - 4 real (`SMALLTAVERNX.DEVIANTART.COM`, `NAMAKXI N
  P&M 2402`, and the "Alex Flores" signature on both alexflores frames), 1 false
  (`dbwtlkx-eeb94ce2`, blurred stonework). On the KEEP side `--corpus cleaning`
  produces ZERO `faint_mark` rows and all 14 `auto` proposals stand.
  DEAD ENDS, MEASURED, do not redo: **tiled / SAHI inference is WORSE, not
  better** (karthas's signature scored 0.1135 full-frame and VANISHED in the
  tiles; p2402 lost its wordmark box and gained a 0.4613 box on unrelated art) -
  the weights were trained on whole frames and the context is load-bearing;
  **EasyOCR on a brush signature** returns nothing or garble at confidence 0.00
  at 1x, 2x AND 4x; and a **per-artist signature template** was deliberately NOT
  built - the corpus holds exactly 2 alexflores images and both are known, so a
  1-frame template is a lookup table for a set of size 2, not a detector.
  Pinned by `tests/test_lw_clean_faint_mark.py` (25 tests), including the one
  false flag, pinned as a row so it stays visible rather than folded into a rate.
  FAINT REMOVAL LANDED 2026-08-12 (LEDGER 98) - closes (e). `lw_clean_iopaint.py
  --faint`. **The first thing measured is that the family is NOT one object**,
  unlike the 32-slug overlay: 2 brush signatures the lane CLEANS, 1 wordmark on
  busy art it REFUSES to the manual lane, 1 DA overlay it DEFERS to `--overlay`,
  and the known false flag, which costs a 0.8 percent mask - a near no-op.
  Three new things over the existing masked-LaMa path (everything else reused
  whole - same mask builder, paste-back, outside-ROI tripwire, never auto):
  (1) the ROI is DERIVED from the detector's own sub-floor boxes, extended by
  any OCR box that OVERLAPS one (p2402's YOLO box stops at x=2348 while OCR
  reads the wordmark to x=2482); overlap is required, not proximity, because
  both alexflores frames carry the KEPT LoL wordmark in the opposite corner.
  (2) `FAINT_BRIGHT_THR` 42 vs the banner default 10 - painted art reads above
  +10 from its own local median, so at the default the signature mask swallows
  the picture (karthas 32.6 percent coverage at 10 -> 14.3 at 42; by eye one
  cloud streak still survives at 34 and none at 42). (3) two refusals plus an
  outcome check: `FAINT_COVERAGE_MAX` 25 (p2402 masks 33.4 percent - refused
  BEFORE the GPU, mask left on disk, manual launch line printed),
  `FAINT_OVERLAY_DEFER` 0.10 - a MEASUREMENT, not a fit: over the 209 clean
  firstdones the overlay score runs p50 0.0596 / p90 0.0770 / p99 0.1042 / max
  0.1213, the four non-overlay flags score 0.048-0.064 and `110-cleanup` scores
  0.109 - and a post-pass RE-DETECT on the candidate that reports a surviving
  box as `status: residual` (coverage is a proxy; the detector is the
  measurement).
  VERIFIED: karthas CLEANED 14.1 percent / 4570 px changed, dragon-slayer
  CLEANED 22.1 / 6774, dbwtlkx CLEANED 0.8 / 936, p2402 MANUAL, 110-cleanup
  DEFER - and **0 changed pixels outside the ROI on all three**, re-measured
  from the files on disk rather than taken from the in-process tripwire. Both
  signatures cropped and looked at: gone, background continuous, the only cost a
  soft patch where a bright art fleck fell inside dragon-slayer's mask.
  DEAD ENDS, MEASURED: the dark-outline adjacency gate does NOT separate p2402
  (the art's own crevices satisfy it at every reach - r4/r7/r11 -> 30.9/32.8/
  34.4 percent, blob intact); the faint lane on a LOW-alpha DA overlay is
  structurally wrong, not untuned (110's credit line stays legible at 19.0
  percent, chroma adds nothing at 19.9, and its overlay score goes UP 0.1090 ->
  0.1203); and a `--pad 260` overlay run on 110 fixes the ROI clipping but still
  leaves the line legible at 0.109 -> 0.1031, because the binding constraint
  there is REGISTRATION (this frame correlates at 0.109 against the flagged
  family's 0.310 median), which belongs to the overlay item.
  Pinned by `tests/test_lw_clean_faint_lane.py` (25 tests).
  REGISTRATION FIXED 2026-08-12 (LEDGER 99) - **`110-cleanup` now CLEARS, and it
  was never a one-image fix.** `best_shift` registers TRANSLATION only; the
  overlay is composited at a fixed size on the DA-served image and a firstdone is
  that image resampled to 2560x1440, so a frame from a different source
  resolution carries the mark at a different PIXEL size that no shift can align.
  Swept a template scale over every flagged slug under 0.25 plus the case: EXACTLY
  TWO are mismatched and both at the SAME 1.12 - `110-cleanup` 0.1090 -> 0.5052
  and `122` 0.1696 -> 0.6542 - both landing in the range the well-registered
  frames occupy (mecha-ahri 0.696, 123f 0.635). Everything else peaks at 1.00.
  TWO BOUNDARIES, both measured. (1) **The scale search is for REMOVAL, never for
  the gate:** a max-over-scales lifts the clean frame
  `wallpapersden-...-sejuani` 0.1213 -> 0.1537, OVER the 0.15 flag - a false
  positive manufactured by the search, the same lesson the shift window learned.
  `overlay_score` is untouched and a test asserts it never grows a scale
  parameter. (2) **A non-native scale must be DECISIVE:** correctly-registered
  frames wobble up to 1.22x under a scale search (270f), the two real ones come
  in at 3.86x and 4.63x, so `SCALE_ACCEPT_RATIO = 2.0` sits far from both and a
  refusal keeps scale 1.0 - a wrong scale is a wrong edit, a refused one is only
  today's behaviour.
  BLAST RADIUS: over all 32 `centre_overlay` slugs plus 110-cleanup, **2
  re-register and 31 register EXACTLY as before** (same shift, scale 1.0), and
  `scale2d_centered` returns its input untouched at 1.0 so those 31 take a
  bit-identical pixel path - the LEDGER 95/96 candidates stand. Spot-checked live:
  mecha-ahri 0.6958 -> 0.0737, 245f 0.5858 -> 0.0903.
  RESULT: 110-cleanup 0.1090 -> **0.0868** and 122 0.1696 -> **0.0941**, both
  registered at shift (24,-1) scale 1.12, and by eye the credit line is GONE on
  both. Every changed pixel on all four verified frames falls inside one of the
  lane's two editors (the inversion's band or LaMa's ROI) - unexplained 0.
  Note 122 already had a candidate from the LEDGER 95/96 pass produced at the
  WRONG scale; a correct-scale one was written to
  `ops/runtime/clean/overlay_scale/122/` during this verification, so take that
  one - the stale candidate is still in `overlay_lane/`. 110-cleanup's gate verdict is unchanged
  and still `qa/faint_mark` (detection score 0.109, under the 0.15 flag, and
  detection did not gain the search) - `FAINT_OVERLAY_DEFER` is what routes it,
  so the chain completes without moving a gate threshold.
  (d) CLOSED 2026-08-12 - **the QA lane is 94 percent real work, and no threshold
  moves.** All 67 `qa` rows of the live gate-v4 corpus were labelled BY EYE from
  crops of what each row actually flagged (`tools/lw_clean_qa_crops.py`, contact
  sheets in `ops/runtime/clean/qa_precision/`, ambiguous cells re-cut at 1:1/2x).
  Region precision (is the BOXED thing a mark) **62/67 = 92.5 percent**; frame
  precision (does the frame carry a mark anywhere, i.e. was the routing right)
  **63/67 = 94.0 percent**. Per reason, region: `centre_overlay` **32/32**,
  `not_border` 25/28, `faint_mark` 4/5, `low_conf` 1/1, `area_too_large` 0/1.
  The one row where the two disagree is the finding: `258-cleanup` boxes its
  letterbox bars (junk) but DOES carry a `TYSIUUUL.DEVIANTART.COM` credit line at
  `overlay_score` 0.1254, just under the 0.15 flag - right for the wrong reason.
  The 4 genuinely mark-free frames are `177-cleanup` (jersey logo + "FAKER"
  nameplate), `186-cleanup` (the poster's own "unto DARKNESS/LIGHT" typography),
  `193-cleanup` (a painted snowflake) and `dbwtlkx-eeb94ce2` (brick texture at
  conf 0.0765). DO NOT tighten on them: their `conf_max` 0.72-0.79, `n_boxes`,
  `area_pct` and `ocr_hit` all sit inside the true-positive range, so every cut
  that drops them drops real marks too. Detail `docs/CLEAN_QA_PRECISION_2026-08-12.md`.
  (a) CLOSED 2026-08-12 - **the mask WAS too wide, and the excess was a ring the
  lane added to hide a cliff it had created itself.** The item recorded "a blur,
  not a legible mark"; at 1:1 (the ROI is 666x442 at deliverable scale, so the
  side-files ARE 1:1) it is structural damage - nostril edge gone, upper lip a
  wash, mask blocks visible. Decomposed, the mask was strokes 17778 px + **veil
  ring 21205 px** + completion 24838 px. Over six frames the ORIGINAL carries no
  level step at the veil support boundary (|step| <= 0.9, 6 of 6 - the support is
  eroded to stop inside the veil) while the inversion leaves 12.7-27.4, so the
  hard-edged correction MANUFACTURED the step the ring was blending.
  `veil_alpha_map` now ramps the correction to zero over `VEIL_FEATHER = 16` px
  outside the support (swept knee: introduced discontinuity 23.30 -> 2.12 -> 1.28
  asymptote) and the ring is retired. Re-run over the whole flagged family (33
  slugs): median mask 63821 -> 41349 px (35% less), median score 0.0680 ->
  0.0664, 33 of 33 still under the flag. Suite 1957 passed / 18 skipped. DO NOT re-add the ring (test-pinned)
  and DO NOT read `hf_keep` as the damage signal (mecha-ahri is mid-pack at
  0.452). Detail `docs/CLEAN_VEIL_FEATHER_2026-08-12.md`.
  STILL OPEN: (f) `p2402-kda-evelynn` is queued for the MANUAL IOPaint lane and
  nothing automates it - a stylised wordmark on busy art that no threshold
  separates; **`mecha-ahri` now joins it** (the logo strokes and credit line lie
  across the nose and upper lip, so any automatic fill invents facial structure).
  **"Skip LaMa when the pre-pass clears" MEASURED over all 33 and REJECTED**
  (2026-08-12, same doc section 6): by score it is 21 of 33 under the flag, not
  the 5 of 6 the first sample suggested (median 0.1331, max 0.2009, and the
  inversion RAISES the score on 3 frames); by eye, 3 of 3 of the BEST-scoring
  frames (0.076-0.084) still read their credit line at 1:1. Measured cause: the
  pre-pass keeps **103 percent** of the credit line's local stroke contrast
  (median over 33) while LaMa keeps 48 percent - the inversion suppresses the
  whole-band high-pass CORRELATION, not the text. **Standing rule that falls out
  of it: `overlay_score` is a DETECTION flag and must never gate removal
  QUALITY.** A future ship gate needs a legibility measure, not the detector.
  **VEIL AMPLITUDE SETTLED 2026-08-12** (`docs/CLEAN_VEIL_AMPLITUDE_2026-08-12.md`):
  the ring-pair confound is REFUTED by a control - the same objective over 31
  frames carrying NO overlay minimises at the smallest gain (alpha 0.0133) and
  rises monotonically, so the geometry does not manufacture a veil. But the
  shipped `alpha 0.1332 = raw 0.0266 x gain 5.0` sat EXACTLY on the old grid's
  last point: a boundary solution written up as an interior optimum. On a grid
  to 19.75 the objective turns at gain 3.75 -> **alpha 0.0999**. It barely
  matters - the clean-frame run is also an 11.48-level noise floor against a
  ~14-level signal, so alpha 0.09-0.13 fits equally well, and by eye on
  `dark-cosmic-ahri` the current value leaves neither residue nor dark blob.
  `VEIL_GAIN_GRID` now runs to 10.0 and `_fit_veil_gain` WARNS on a ceiling hit
  (test-pinned). **MATTE REBUILT on the wider grid (LEDGER 103): the fit is now
  INTERIOR at gain 5.25 and alpha went UP, 0.1332 -> 0.1398 (+5.0%)** - one step
  past the old ceiling, the opposite direction from the 31-frame curve, which is
  the SNR-1 point made concrete (swap the frame set, the estimate moves 40%).
  Only the veil alpha moved; stroke alpha, `W` and the support are bit-identical.
  All 33 candidates re-cut: median score 0.0664 -> 0.0645, worst 0.0955 ->
  0.0942, 33/33 still under the flag, pre-pass changes 1-2 levels over 13-16% of
  the ROI. Candidates now in `ops/runtime/clean/overlay_rebuilt/`. DO NOT redo
  the three dead ends recorded there: no same-artwork clean/marked pair exists in
  the corpus, the two-resolution slugs carry no lever, and both the notch
  estimator and the floor test are defeated by the support's closing filling the
  chevron's unveiled notch.
  Evidence: `docs/CLEAN_QA_PRECISION_2026-08-12.md` +
  `docs/CLEAN_OVERLAY_SCALE_2026-08-12.md` +
  `docs/CLEAN_FAINT_LANE_2026-08-12.md` +
  `docs/CLEAN_FAINT_MARK_2026-08-11.md` +
  `docs/CLEAN_OVERLAY_DETECTOR_2026-08-11.md` +
  `docs/CLEAN_DETECTOR_RECALL_2026-08-11.md`; census tool
  `tools/lw_clean_detector_probe.py --corpus firstdone`.


- **gemini-removal - REVERSIBLE HALF LANDED 2026-08-02. The loop is Claude-only
  and self-adjudicating by default; the vendor is two config keys away.**
  LW had no adjudicator key to flip, so the removal had to BUILD the seam RC
  already had. Landed: `oracle_backend()` / `claude_oracle()` / `oracle()` in
  `loop_controller.py`; `director()` and `auditor()` dispatch through it; and
  `director_backend` + `auditor_backend` ship as `claude`. The Claude oracle is
  READ-ONLY on purpose (`--permission-mode plan`, NOT the executor's
  `bypassPermissions`) - an adjudicator that can write is not an adjudicator.
  An unknown backend value resolves to `claude`: never a crash, and never
  silently back to the vendor being removed.
  **ROLLBACK IS TWO KEYS.** Nothing was deleted - `gemini()`, `_gemini_call()`,
  `gemini_model`, `gemini_cmd`, `gemini_price_per_mtok`, `ceiling_usd`,
  `tools/gemini_audit.ps1` and both prompt templates all stay, the same posture
  the `channel` flip took (LEDGER 40). `ceiling_usd` remains a real rail and
  simply reads $0 while the Claude backend is in play.
  Next (the SWEEP, deliberately not bundled): physically delete the Gemini call
  path, the vendor references in the prompt templates, `gemini_price_per_mtok`
  and the `GEMINI_USD` accounting - but only after the Claude oracle has
  authored directives on a live multi-cycle run. Until then the rollback must
  stay reachable. `LW-GeminiAudit` is DROPPED from the scheduled-task roster
  (`docs/OPERATIONS.md`); it was never registered, so nothing was disabled.
  Why the shape was different here: LW has no adjudicator
  key at all - Gemini was structurally the DIRECTOR and AUDITOR via
  `gemini_model`, `gemini_cmd`, `director_prompt.md`, `auditor_prompt.md`,
  `tools/gemini_audit.ps1`, the `ceiling_usd` accounting, and the mutex hold at
  the mutex hold. Removing it meant replacing what AUTHORS each cycle's
  directive, not switching a backend behind a flag that already existed.
  Supporting evidence from LW's own runs: a read-only Claude verifier refuted a
  Claude slice on a false behavior-identical claim, and a second refuted another
  on a cache-eviction regression a 530-line test file missed - same vendor, both
  caught, because the grader was adversarial and independent rather than
  differently-branded. Vendor diversity was not what was catching errors.
  Do-not-redo: do NOT delete `GEMINI_MUTEX` from `winmutex.py` - it is
  byte-identical-by-contract with RC, deleting it needs a three-way re-pin, and
  the gemini rollback path still consumes it. Do NOT rename the `gemini.ready`
  IPC sentinel - that is the AHK bridge's byte-level handshake filename and has
  nothing to do with the vendor.
  Evidence: `moon_sync_inbox/2026-08-01-0820-from-RC-*` section 7;
  `tests/test_oracle_backend.py` (16 tests);
  `docs/OPERATOR_ANSWERS_2026-08-02.md`.


- **ci-watchdog - `tools/ci_watchdog.py` WRITTEN and `LW-CIWatchdog` ARMED
  2026-08-02. Unproven on a real red main.**
  One pass per invocation (the scheduled task is the loop, so a wedged pass dies
  with its process). Rails: HALT is checked FIRST and an empty HALT file counts;
  only a settled `failure` triggers a fix (queued / pending / unavailable /
  not-evaluated all WAIT); 2 attempts per failing sha, and a transient Anthropic
  condition refunds the attempt; the merge self-gates on the fix branch's OWN
  green CI at its OWN head sha, and a stale success for a different sha is
  refused. Reuses `truth_gate.check_ci` rather than re-deriving the status
  distinction f1 item 12 already built.
  Registration is by the tool's own `--install` (XML): `schtasks` REJECTS
  `/RI` for `/SC ONSTART` outright, the same wall `lw_wallpaper_rotate` hit.
  Next: it has never seen a real red main. Watch its first genuine fire, and
  read `ops/runtime/ci_watchdog/watchdog.log` after any red push.
  Kill switch: create `ops\runtime\ci_watchdog\HALT` or
  `Disable-ScheduledTask LW-CIWatchdog`.
  Evidence: `tests/test_ci_watchdog.py` (26 tests); `docs/OPERATIONS.md` roster.

- **g1-source-adequacy - G1 is blind to an inadequate SOURCE; 105 of 276 approved
  images came from one - OPERATOR-GATED on policy.**
  Next: operator answers two questions, then it is a small deterministic slice -
  (1) is a 2.5x upscale from 1024x576 acceptable? (2) inadequate source = FLAG or
  FAIL? Deliberately NOT guessed; guessing repeats the mistake `anat-vision-review`
  caught the same day. Cheap once decided - `src_dims` is already in every
  manifest, so no model and no pixels needed.
  NEW EVIDENCE 2026-08-17, the first time this cost real GPU time: the 243-slug
  batch produced exactly one hard FAIL, `1000040081-by-hahaosnsnsondneks-dmmirml
  -375w-2x`, on `lap_ratio 0.912 < 1.0`. Its source is a 750x437 / 56 KB
  DeviantArt `375w-2x` thumbnail - the smallest tier they serve. Decoding the
  token (deviation 1368083037) and pulling the authoritative fullview through
  gallery-dl OAuth returned the SAME 750x437 bytes, so no better source exists
  and no retune can rescue it. A source-adequacy check would have caught this
  BEFORE the upscale rather than after, which is the concrete argument for
  answering the two questions above. Note the filename shape `-375w-2x` is itself
  a reliable tell and is cheaper than any metric.
  Do-not-redo: do NOT retune the G1 fidelity metrics - they are correct at their
  job; the gap is a MISSING ABSOLUTE precondition, not a miscalibrated relative one.
  Evidence: LEDGER 60; `docs/SOURCE_ADEQUACY_CENSUS_2026-07-29.md`.

- **legacy-audit-backfill - 12 approved images carry no G1 audit; 10 of them were
  built with the FALLBACK upscaler - NEXT (backfill, not a code fix).**
  Next: backfill or mark the 12 as pre-audit legacy, then decide the 10 reprocesses.
  Verified NOT a live bug (all 12 predate ADR-004; the current code path always
  writes the audit). NOT reprocessed unattended - `APPROVE_FIRST` is an operator
  judgement by design, so regenerating would park 10 images in your approval queue.
  The CODE half is DONE 2026-07-30 (`94bea85`): approve and finalize now record
  `gate_check` as `pass` / `override` / `no_audit`, so an override is greppable
  and a legacy no-audit approval is its own outcome rather than passing for a
  clean one. Only the DATA decision is still owed.
  Evidence: LEDGER 60 + 61; `docs/SOURCE_ADEQUACY_CENSUS_2026-07-29.md` (slugs listed).

- **anat-vision-review - AUTHORITY RULED 2026-08-02 (ADR-008) and the rails are
  SHIPPED. The reviewer itself is the remaining slice.**
  Ruling: a vision reviewer may FLAG, never REJECT, and an unresolved flag
  BLOCKS approval by any actor that is not the operator. Reasons, all measured:
  a REJECT demotes, and `clean-retry-degrades` (closed, ADR-009 + LEDGER 105)
  shows a further pass makes the
  image WORSE, so a false REJECT degrades what it was protecting; a vision 2AFC
  is not reproducible, so the operator cannot re-derive a verdict they dispute;
  and splash art is deliberately non-anatomical with no ground truth to check.
  SHIPPED in `tools/lw_pipeline.py`: `clamp_vision_audit()` coerces a vision
  audit's REJECT/FAIL to FLAG at the ANNOTATE WRITE boundary (not in a prompt -
  a rule in a prompt is a request), `_approval_record` reports `blocking_flags`,
  and `assert_approval_allowed()` refuses a non-operator approval with exit 3
  BEFORE the needauth rename. `approve --actor` defaults to `operator`.
  The rail deliberately lands BEFORE auto-approval exists: a gate written after
  the thing it gates is a gate that was once open.
  Next: build the reviewer on the Claude-vision 2AFC path `end-review` already
  uses. It must arrive already unable to exceed these rails.
  Do-not-redo: keypoint head-spine offset as a gate metric - built, measured
  over all 288 approved firstdones, rejected on the evidence; ships as a
  diagnostic only (`tools/lw_anat_metrics.py` + `tools/lw_anat_probe.py`).
  Revisit REJECT only when the Phase A shadow window has >= 50 operator-reviewed
  images and flag precision is a NUMBER (`autonomy-phases-bc`).
  Watch: `BLOCKING_FLAG_PREFIXES` is a prefix match - a future reason starting
  with `anat_` becomes blocking silently.
  Do-not-redo: keypoint head-spine offset as a gate metric; swapping the localizer
  to rescue it (splash art is cropped at the waist, so most images have no confident
  hips - a better pose model cannot find hips outside the crop); reading a DWPose
  figure count as a detection count (35 percent yield zero person boxes and
  `tools/dwpose_onnx/onnxpose.py:26` silently substitutes the whole frame).
  Evidence: LEDGER 60; `docs/ANATOMY_CENSUS_2026-07-29.md`.

- **gen-nonahri-deformed - the shipped recipe is tuned on ONE champion and the
  others come out deformed - NEW 2026-08-16, operator verdict.**
  Reviewing 5 frames each of Jinx, Katarina, Lux, Miss Fortune, Vayne and Yasuo
  on the shipped `splash-booru` style, the operator's verdict was that
  everything except Ahri is "vastly deformed, incorrect positioning and
  drawing". Every arm in LEDGER 107-118 used Ahri, so the realism block, the
  anti-doll negative, the QA floors and the whole recipe have only ever been
  evaluated on one champion. The QA gate does NOT catch it: those frames scored
  in the normal range while being unusable.
  **ROUND 1 DONE 2026-08-16 (LEDGER 120) - cause found, nothing shipped.** Seven
  ablation arms on Katarina + Miss Fortune (both failed 5/5), matched seeds:
  the realism block is NOT the cause (deformity persists without it); the POSE
  STACK is (`dynamic action pose` / `twisted torso` / `contrapposto` /
  `leaning forward` / `foreshortening` / `from below` / `cowboy shot`), and
  removing it gives clean anatomy but drops the body out of frame; **the base
  KNOWS these champions** - a minimal prompt renders Miss Fortune canonical
  (tricorn, costume, anatomy, hero framing) where the full style gave a
  deformed figure in generic leather, so the style was OVERRIDING champion
  knowledge rather than supplying it; and `official splash art` summons the
  splash TITLE CARD, which `text, signature, watermark` do not suppress.
  Next: operator picks between the two measured candidates - `canon` (minimal
  positive + full negative: best identity, carries the title card) and `lean`
  (one pose tag + lighting + realism: fixes anatomy, keeps framing, dilutes
  canon) - and whether a text-specific negative strips the title card while
  keeping `official splash art`. Then re-validate on 4+ champions BY EYE; the
  QA gate scored the deformed frames in the normal range and cannot arbitrate.
  Frames + index: `images/_review_ablation/`.
  Evidence: `docs/GEN_FACE_REALISM_2026-08-16.md`, LEDGER 119-120.

- **gen-reference-lane - BASE SETTLED 2026-08-16 (ADR-011: Animagine XL 4.0
  HELD; RealVisXL + DreamShaper DROPPED). NEXT is facial realism ON THIS BASE,
  then the adapter lane re-run.**
  A corpus-similarity A/B (matched seeds, adapter OFF, n=3) ranked animagine LAST:
  **0.6843 (-0.153)** vs RealVisXL **0.8609 (+0.024)** and DreamShaper **0.8448
  (+0.008)**, with RealVis also taking subject_cos / margin / pass rate. ADR-010
  flipped the base on that and **ADR-011 reversed it the same day on operator
  inspection of every candidate frame**: animagine holds League and corpus
  conventions on ALL frames; RealVisXL violates hand conventions, weapon/tool
  canon and facial likeness; DreamShaper violates the corpus look outright.
  **The standing rule that came out of it: corpus similarity is a MEASURE of
  rendering register and NEVER selects a base.** It is CLIP global image
  statistics - blind to hands, weapon canon and likeness - so it ranked the two
  convention-breaking bases first. Do not re-run a base A/B scored on it.
  `tools/lw_gen_medium.py` (the recovered yardstick, reproduces the recorded
  0.8373 to four decimals) is kept for what it does measure.
  **FACIAL REALISM SHIPPED 2026-08-16 (LEDGER 116).** `splash-booru` carries a
  face-realism block and a priority-ordered anti-doll negative; verified by
  generation with no CLI extras: subject 0.2843 (+0.014), margin 0.0592 (+0.008),
  sharpness 519.5 held, and the base's rendering register moved from **0.6843
  (-0.153) to 0.8268 (-0.011)** against the 0.8373 ceiling - the ADR-010 gap
  closed on the SHIPPED base by a prompt change. Evidence:
  `docs/GEN_FACE_REALISM_2026-08-16.md`.
  Next, in order: (1) **operator eye on the shipped frames** - hands, weapon
  canon and likeness have no automatic measure (ADR-011), so the realism block
  stands until inspected on more champions than Ahri; (2) champion canon (eye
  colour) belongs in each brief's `prompt_extra` - Ahri's `yellow eyes` is
  measured to matter and is NOT in the shared style; (3) the fox familiar is
  base/prompt/seed, NOT reference bleed (LEDGER 111) - attack it as a
  negative-prompt problem.
  Do-not-redo, all measured: a base A/B scored on corpus similarity (LEDGER 115 -
  it selected two bases that break the product); an IP-Adapter reference carrying
  ANOTHER champion's face (116 - Jinx at plus-face 0.3 drops Ahri below the
  subject floor, at 0.5 the margin goes negative, 0/3); dropping `cel shading`
  from the anti-doll negative (116 - costs register, buys no sharpness); composition tags (112 - reverted;
  heads are TOO BIG, and 5/6 frames sit inside the real envelope); long-prompt
  encoding (113 - built, proven bit-exact, reverted; identity fell on 12/12 seeds);
  re-cropping the local corpus tighter (111 - the confound is in the SOURCE);
  DWPose as a framing measure (use `tools/models/yolo/face_yolov8m.pt`).
  Untested across every eval so far: a FULL-FRAME reference at high scale.
  Known live traps: the `splash-booru` negative overruns CLIP at 93 > 77 and
  silently drops its quality tail (left alone by operator call - the discarded
  text was restored and measured WORSE); `lw_gen_run.run()` called twice in ONE
  process silently kills the second arm (exit 0, zero images) - one fresh process
  per arm.

- **m1-gate-fund-or-close - decide attempt #4 on the weapon-canonicity gate - OPERATOR-GATED.**
  Next: operator decides FUND or CLOSE. Three measured negatives landed
  2026-07-26 (LEDGER 37) and the binding constraint is now known and cheap to
  fix: canonical n=5 gives AUC granularity 1/65, so no result can be
  significant. FUND = hand-crop wrists from the 19 official Vayne splashes
  already local at `tools/models/lora_datasets/vayne/` (the existing 5
  `weapon_assets` crops came from that same pool) to reach n~19 canonical vs
  ~13 non-canonical, all real Riot art, matched on pixel count AND provenance.
  CLOSE = accept `gate_mode="operator"` permanently, which is already the
  shipped default and works.
  THIRD OPTION opened 2026-08-02 by operator re-measurement of modelviewer.lol:
  seed each champion + skin ONCE and capture many perspectives / rotations,
  giving a render library where BOTH classes come from the same renderer. That
  matches provenance BY CONSTRUCTION and removes the n=5 ceiling, so the
  provenance objection - correct against mixing renders with real art - does not
  apply to an all-render design. Residual risk becomes train-on-renders /
  infer-on-paintings domain shift. See BACKLOG "3DSkinViewer / modelviewer.lol"
  point 1 and `glb-render-fetch`.
  Evidence: LEDGER 37; `scratchpad/probe_results.md` +
  `scratchpad/render_exemplar_results.md`.
  Do-not-redo: img2img weapon-swap (structure-locked, 0/12); any probe trained
  across a provenance boundary (AUC 1.0 = generator fingerprint); the 36 staged
  DreamUp step4 prompts (superseded by the render path). Match on EVERY axis -
  provenance and resolution both slipped in while palette was being tuned.

- **f1-phase6-queue - 12 follow-ups from the sdk-channel migration - RC-SIDE REMAINDER (LW's share is DONE).**
  Phase 6 DELETIONS remain HELD by operator call (flip yes, delete no); both repos
  default to `channel: sdk` and rollback is one config key. The gate for revisiting
  deletion is satisfied on both sides (LW 24-min / RC 71-min full-length cycles).
  Queue, agreed with RC and unstarted: (1) `chmod +x .githooks/*` - DONE on LW,
  open on RC. (2) `gate_inactive_reason` must check the exec bit on POSIX, not just
  presence. (3) log `sid` on EVERY `SdkExecutor` path incl. success - a cycle's
  transcript is currently unfindable once the process exits. (4) `ENGINE-IMPACT:
  BUMP` must require a numbered step naming every anchor site (RC found a FIFTH
  anchor: two changelogs, `agents/daemon_slayer/CHANGELOG.md` != `Share/CHANGELOG.md`).
  (5) `skipif` audit - skip when the CAPABILITY is absent, never when the thing under
  test is. (5a) pin the shared-file sha256s as constants so each repo's CI enforces
  parity alone. (6) CI arms the gate then asserts it - DONE on LW. (7) directives
  naming N parallel agents must assert disjoint files; executor serializes AND
  RECORDS the deviation. (9) POSIX `winmutex` branch must emit `UNSERIALIZED` -
  today it is unserialized AND untraced, so every guard we built passes vacuously
  off-Windows; joint edit + re-sync. (10) enumerate every instance of a defect class
  IN THE FILE before committing the fix, then across the codebase - CLAUDE.md line 171 (pre-condense, now in docs/claude-md-history.md)
  says this but points outward, and it was missed twice in one function. (11) a
  claim heavy enough to justify a schema change ships as a TEST, not a transcript.
  (12) when asserting CI state, distinguish `not evaluated` (docs-only path filter)
  from `queued` - they are indistinguishable in `gh run list`.
  (5a) and (9) are DONE and VERIFIED IN SYNC on both sides: LW `3bd9a8b`, RC
  `fbf744f5`, both trees re-hashed clean to `slots.py 95077a62...` and
  `winmutex.py f1b4b011...` (the latter supersedes `c21bfe4f...`). (1) is done
  on both sides too - RC's exec bits landed as `19b680cc`.
  (3) is DONE on LW (`549f52c`): `build_argv` now retains the session id it
  mints or resumes, so all five `SdkExecutor` paths log it - including timeout
  and unparseable stdout, which never parse a payload and so previously had no
  id to log at all. Same commit repairs the CI red that `202cef3` introduced
  (the `directive_suffix` guard keyworded `done_sentinel`, which the phase-6
  DO-NOT-REDO line legitimately names).
  (12) is DONE on LW (`07ed5bc`): `check_ci` split the single `no-runs` outcome
  into `not-evaluated` and `queued`. The `paths-ignore` globs are PARSED from
  `.github/workflows/ci.yml` rather than hardcoded, so the check cannot drift
  from the workflow, and every unknown - unreadable workflow, no `paths-ignore`
  key, failed `git show`, merge commit - falls to `queued`. `not-evaluated`
  requires positive evidence. `reconcile()` still REFUSEs only on `failure`:
  making `queued` refuse would wedge an unattended run on GitHub API lag.
  Residual, adjacent and NOT item 12: `check_ci` only rev-parses when
  `sha == "HEAD"`, so an abbreviated sha reaches `gh run list --commit` and
  returns `[]`. The conservative fallback answers `queued`, so it is not a false
  green, but the abbreviation gap is real - `check_ci("549f52c")` -> `queued`
  while the full sha -> `success`.
  (7) is DONE on LW (`b7814b3`, LEDGER 80) in the only form LW can enforce it:
  `slice_orchestrator.start_gate()` REFUSES `set --status in_progress` unless the
  named agent holds a claim on every file the slice declares, and a slice with no
  declared files cannot start. So a directive that names N parallel agents no
  longer merely ASSERTS disjointness - an overlap is refused at dispatch and the
  refusal names the holder. The executor-serializes-AND-RECORDS-the-deviation
  half stays RC-side.
  LW's share of the queue is now empty; RC keeps (2), (4), (5), (10), (11).
  Cross-repo channel is the gitignored `moon_sync_inbox/` in each repo.
  Evidence: LEDGER 41 + 40; `docs/specs/2026-07-26-f1-sdk-executor-channel.md`.

- **glb-render-fetch - acquire the .glb bytes the ported resolver now addresses - NEXT.**
  Next: the addressing + filtering half shipped 2026-07-26 (LEDGER 38, 1dbfc2d) -
  `glb_model_url` / `glb_skin_id` / `is_weapon_joint` / `weapon_joint_indices` /
  `mesh_primitives` live in `tools/lw_gen_weapon_assets.py` and are pure, so the
  module stays torch-free AND network-free. What is still OWED is the I/O half:
  fetch the URL, parse the GLB container, skin the mesh against the surviving
  joints, and render the crop that `load_assets` consumes. That half needs a
  network dependency and a render backend, so it is a separate slice by design.
  Evidence: LEDGER 38 (1dbfc2d); LEDGER 37 for the live CDN verification.
  Do-not-redo: ASSET-SCRAPING the modelviewer.lol website (Cloudflare + in-app
  blobs, POC-measured 2026-07-16) - but note that ruling is scoped to fetching
  asset blobs and NOTHING else. Operator re-measurement 2026-08-02: Cloudflare is
  no longer the blocker and a CAPTURE route is viable - seed each champion + skin
  ONCE and capture many perspectives / rotations of the output window, building a
  render library in a single pass. That is a live option for this item and for
  `m1-gate-fund-or-close`; see BACKLOG "3DSkinViewer / modelviewer.lol" point 1.
  Also do-not-redo: any fixed bone-INDEX set (two rig conventions exist, so indices
  cannot port); reading `primitives[0]` alone (newer skins split mesh 0 into
  9-10 primitives sharing one POSITION accessor - drops most triangles); the
  `.skl` skeleton from CDragon (404) - the named-joint path replaces it.

- **refs-46-first-pass - process the 46 intaken reference_pictures - DONE
  2026-07-27. 46 of 46 APPROVED by the operator; `1.First Pass Scratch` is
  empty and `2.First Pass Done` holds 288 slugs (242 prior + these 46).**
  **A PROCESS MISS ON APPROVAL, recorded because the ruling it skipped is still
  open:** this entry said `first-pass-alpha-letterbox` should be ruled on BEFORE
  approval, and the session did not surface that to the operator - it raised the
  pixel-identity caveat instead. The pixel-identity evidence was itself blind to
  the issue: identity was measured as sha256 over decoded RGB buffers, which
  cannot see an alpha plane being dropped. NOTHING IS LOST - `approve`
  safe-copies `_firstinitial` next to `_firstdone`, verified on `258-cleanup`
  (`_firstinitial` RGBA, `_firstdone` RGB), and `9.Image Backup` holds a third
  copy - so the 15 affected slugs remain reprocessable via the reopen dance once
  the policy call lands. What was actually spent is the operator's chance to
  decide before staging, not the data.
  Next: stage-2 cleaning on the 46 (operator direction 2026-07-27).
  Cycle 10 (LEDGER 55, plan row R25) ran the last 5,
  `280f` `281-cleanup` `286f` `32-cleanup` `84f`,
  cycle 9 (LEDGER 54, plan row R24) ran
  `270f` `272-cleanup` `274f` `276f` `277f`,
  cycle 8 (LEDGER 53, plan row R23) ran
  `261f` `262f` `264-cleanup` `266f` `269f`,
  cycle 7 (LEDGER 52, plan row R22) ran
  `239f` `245f` `254f` `258-cleanup` `259f`,
  cycle 6 (LEDGER 51, plan row R21) ran
  `219-cleanup` `221-cleanup` `225f` `229f` `230-cleanup`,
  cycle 5 (LEDGER 50, plan row R20) ran
  `186-cleanup` `190-cleanup` `193-cleanup` `196f` `209-cleanup`,
  cycle 4 (LEDGER 49, plan row R19) ran
  `150-cleanup` `153-cleanup` `170-cleanup` `177-cleanup` `180-cleanup`,
  cycle 3 (LEDGER 48, plan row R18) ran
  `123f` `124f` `127-cleanup` `134-cleanup` `14-cleanup`, cycle 2 (LEDGER 47,
  plan row R17) ran `105-cleanup` `106-cleanup` `107-cleanup` `110-cleanup`
  `122`, and all five took 5/5 G1 PASS with an empty reasons list. That is the
  R16 fix measured in production over 45 consecutive slugs: cycle 1 FLAGGED on
  halo, cycles 2-10 flag nothing. Cycles 3-10 also MEASURED the pixel-identity
  claim (sha256 over the decoded RGB buffers per pair) instead of inferring it
  from equal dimensions; the PNG bytes otherwise differ only because SUBMIT
  re-encodes, and cycle 5's `186-cleanup` is the only RGB output so far to
  SHRINK on that re-encode rather than grow. Cycle 7's two big shrinks are a
  different mechanism entirely - see `first-pass-alpha-letterbox` below.
  Probe notes for the next cycle: the audit block
  is NOT at manifest top level - it is `transitions[i].audit` for the
  `ANNOTATE` transition, and a top-level read silently returns empty for every
  field. `manifest.json` carries no `state` key at all; state/substate is
  derived from the filesystem by `scan_tree`, and `lw_pipeline.Ctx()` takes the
  IMAGES dir, not the project root - passing the project root scans 0 images
  and returns a silent all-zero result rather than an error.
  All 46 processed slugs sit at
  `FIRST_SCRATCH/NEEDAUTH` - approval is operator-only and is the real queue.
  Cycle 1 proved the chain on slug `0`
  (`_firstneedauth`, G1 FLAG on halo only, LEDGER 45) and corrected the premise:
  all 46 `_firstinitial` files are EXACTLY 2560x1440, so every slug takes the
  `downscale-only` branch at scale=1, no resample happens, and the unsharp mask
  was the ONLY operation first pass applied to this batch. The AI upscaler is
  not exercised by these 46 at all (model load verified separately: spandrel DAT
  scale 4, torch 2.11.0+cu128, RTX 5070). Director decision B (LEDGER 46, plan
  row R16) fixed it at the cause: no resample, no unsharp mask. First pass is now
  a provenance-only passthrough for an already-at-target source - measured live
  on slugs `0` and `105-cleanup`, halo_pct 0.0711 -> 0.0 and lap_ratio 1.965 ->
  1.0, output pixel-identical to the source. A genuine over-target downscale
  (e.g. 4K -> 1440p) still gets its USM; the skip is keyed on the exact-target
  size, NOT on `scale == 1`. The 47/61 downscale-only halo flags in
  `project-first-pass-recipe-validated` stay an open watch - those DID resample.
  Then route them to stage-2 cleaning - 35 were
  gate-flagged (13 auto / 22 qa) and 11 were held on manual OCR review, so
  the watermark work happens at `3.Cleaning Scratch`, NOT before first pass.
  Recovery waterfall is still OWED for this set: every manifest carries
  `source_url: null` (Tier 0/1/2 deliberately skipped at operator direction),
  and 112 of the novel refs are still source-recoverable.
  Evidence: LEDGER 35 + 36 (63cc35b, 3b8e0f1); per-file verdict + reason
  table in `docs/refs_cleaning_queue.md`.
  Do-not-redo: the 226 clean refs are already delivered to Pictures as
  `ref_*.png` (sha-verified) - do not re-triage or re-copy them. If any of
  the 112 recoverable ones later gets restored, REMOVE its raw `ref_*` copy
  from Pictures or rotation gains a near-duplicate.

- **batch20-first-pass - FIRST PASS DONE 2026-07-30; 17 slugs sit at NEEDAUTH
  awaiting operator approval, 3 are HELD.**
  Next: operator approves or rejects the 17 (`lw_pipeline.py approve|reject`);
  approval is operator-only by design. Result: 10 PASS, 7 FLAG, 0 FAIL, 3 HELD.
  All 7 flags are the SAME reason - `halo_pct` over the 0.05 line, 0.0567 to
  0.1196 - and that is now measured and explained, see `usm-halo-calibration`
  at the top of this file. This batch DID exercise the AI upscaler (16 of 17
  took `upscale-4x`), unlike the 46 refs which were all exactly 2560x1440 and
  took the passthrough branch - which is exactly why this batch flags and that
  one did not.
  The 3 HELD are `puppet-master-syndra` and both `spirit-blossom-vayne` slugs,
  all on `aspect_crop_heavy` (area loss ~0.156 vs the 0.08 `AREA_LOSS_MAX`
  cap). They are annotated, never upscaled, and still EDITING. Crop policy is
  product direction and was NOT decided unattended - that ruling is owed.
  Intake + recovery ran 2026-07-29: Tier 0 `no_match` for all 20 (every one
  novel), Tier 1 decoded a DeviantArt token for all 20 and gallery-dl fetched
  all 20 at the quota-free setting. 8 of 20 gained real pixels, best
  `blood-moon-priestess-mel` 1159x689 -> 1920x1142 (2.75x); the other 12 held
  pixel count but shed 6-7x of JPEG compression.
  Do-not-redo: `original: true` on DeviantArt (weekly quota; the intermediary
  path already measured a gain and costs none); re-intaking a fetched fullview
  through `0.Originals` (re-slugging diverges the slug - `lw_first_pass`
  selects by convention path instead).
  Evidence: `PIPELINE_LOG.md` 2026-07-30T12:0x-12:17Z block; per-slug audit at
  `transitions[i].audit` for the ANNOTATE transition; LEDGER 61.

- **first-pass-alpha-letterbox - first pass silently drops the alpha channel,
  and G1 is blind to it - OPEN (found cycle 7, LEDGER 52, plan row R22;
  widened by cycle 8, LEDGER 53, plan row R23; sub-shape B identified by
  cycle 9, LEDGER 54, plan row R24; CENSUS CLOSED by cycle 10, LEDGER 55, plan
  row R25; audit hygiene SHIPPED by cycle 11, LEDGER 56, plan row R26;
  SUB-SHAPE B RULED by the operator 2026-07-29 - ACCEPT AND RECORD, change no
  pixels; SUB-SHAPE A's policy call is still open).**
  **STILL OPEN AND NOW POST-APPROVAL.** All 46 were approved on 2026-07-27
  without this ruling - see the miss recorded under `refs-46-first-pass`. That
  does not close it and does not lose anything: every `_firstinitial` is
  preserved RGBA beside its RGB `_firstdone` in `2.First Pass Done` and again in
  `9.Image Backup`. It does change the shape of acting on it - a ruling that
  says "keep the alpha" now needs the reopen dance for the affected slugs
  instead of a re-run before staging. Rule on it BEFORE stage-2 cleaning, since
  cleaning writes on top of `_firstdone`.
  The census is now complete over all 46 refs, so the numbers below are final
  rather than a running tally: FIFTEEN of the 46 are RGBA with a genuinely
  non-opaque alpha, 31 are RGB, none is any other mode. Cycles 8 and 9 both
  came back 5-for-5 RGBA, which read as "most of the corpus"; cycle 10 came
  back 3 of 5 and the full sweep settles it at 15 of 46, so this is a common
  shape but a minority one. Final shape histogram over the 15: sub-shape B 1px
  rim x8, sub-shape A hairline letterbox x4, the B left/right-column variant
  x2, and `258-cleanup`'s 160-row letterbox alone x1. The alpha PLANES collapse
  to only five distinct bitmaps (sha256-16 `2d01a0afce742e26` x8,
  `4be64a25a2e1d11c` x4, `f47a60870653b036` x1, `8d42f440f08f26d0` x1,
  `03a55dd42770d45d` x1), so three of them account for 14 of the 15 files -
  export-toolchain provenance, not per-image chance. That matters for the
  policy call: ONE ruling on sub-shape B disposes of 10 of the 15 files, and a
  second on sub-shape A disposes of 4 more. Two DISTINCT sub-shapes:
  Sub-shape A - a fully transparent (alpha=0) full-width top/bottom letterbox
  whose underlying RGB is already pure black: `258-cleanup` rows 0-79 +
  1360-1439 (160 rows, 11.11 percent of the frame - the actual artwork is
  2560x1280, an exact 2:1 plate letterboxed into a 16:9 canvas), and a 3px
  hairline `[0-2]` + `[1437-1439]` (6 rows, 0.4167 percent) on `259f`, `261f`,
  `262f` and `264-cleanup` - four slugs with byte-identical bar geometry, so
  the hairline is a shared authoring or export artifact, not per-image chance.
  Sub-shape B (found cycle 8, IDENTIFIED cycle 9) - PARTIAL translucency with
  no transparent row at all, and it is a 1-PIXEL OUTER BORDER RIM, not the
  scattered anti-aliased band cycle 8 read it as. Cycle 9's five slugs plus
  cycle 8's `269f` each measure alpha min=220 max=255, ZERO fully transparent
  pixels, and exactly 7996 non-opaque pixels = `2*2560 + 2*1440 - 4`, the frame
  perimeter, with a 100 percent opaque interior. Cycle 8's `266f` measures
  2880 = `2*1440`, the same rim with only the left/right columns. Cycle 9's
  five alpha planes are `np.array_equal` BIT-IDENTICAL to one another (plane
  sha256-16 `2d01a0afce742e26`), so this is one export-toolchain artifact
  stamped across many files rather than per-image chance - cycle 10's `280f`
  and `286f` carry that same plane hash, making it 8 files on one bitmap.
  One dent in the taxonomy, from cycle 10: `281-cleanup` is a 2880
  left/right-column rim like `266f`, but its alpha min is 218, not the 220
  every other rim carries, and its plane hash (`03a55dd42770d45d`) matches
  nothing else. Its plane's value histogram is exactly `{218: 1440, 222: 1440}`
  - one column at 218, the other at 222, no 220 anywhere in the file, so its
  two columns are not even equal to each other. "alpha min 220" is a strong
  regularity, NOT an invariant - any detector written for this must not
  hard-code it. Nothing is
  letterboxed here; the alpha is simply discarded. The item name understates it
  - the general defect is an unannounced RGBA -> RGB flatten.
  First pass writes RGB, so sub-shape A bars bake to pure black (verified max
  AND min channel value 0) and the file shrinks ~40 percent on the alpha drop -
  the only reason this was noticed at all. Every cycle-8 output shrank
  (-39.7 to -42.1 percent) and every cycle-9 output shrank (-40.6 to -43.3
  percent) for exactly this reason, which is a different mechanism from cycle
  5's `186-cleanup` RGB re-encode shrink.
  The gap: G1 compares RGB only, so black-vs-black under alpha=0 scores a
  perfect 1.0 and a letterboxed source is structurally invisible to the gate.
  `aspect_class=ok` on `258-cleanup` is satisfied by the transparent bars, not
  by the artwork, so it would approve as a 2560x1440 wallpaper with an 80px
  black bar top and bottom. Sub-shape B is invisible to the gate for the same
  reason and has no aspect consequence at all - the composite over an opaque
  background is unchanged, so it may well be acceptable as-is.
  Decide the POLICY before writing any detector, and decide it PER SUB-SHAPE.
  **SUB-SHAPE B IS RULED (operator, 2026-07-29): ACCEPT AND RECORD.** The
  flatten is recorded in the audit and NO pixels change - a 1px perimeter rim
  (or a left/right-column variant) has no consequence composited over any
  background, which is what the cycle-9 rim measurement established. That
  disposes of TEN of the fifteen files (the 8 full-perimeter rims on plane hash
  `2d01a0afce742e26` plus the 2 left/right-column variants, `266f` and
  `281-cleanup`), and it needs no reopen dance: their already-approved
  `_firstdone` files stand as-is and go straight to stage-2 cleaning. Recording
  for the ten is the `alpha_flattened` + `source_mode` field shipped in cycle 11
  (`ef67c49`), which those ten predate - so their record lives in this ROADMAP
  entry and the LEDGER, not in their own manifests, and that is the accepted
  cost of ruling post-approval rather than a reason to re-run them.
  **SUB-SHAPE A IS STILL OPEN** and still blocks its five slugs: for A, crop to
  the content box and re-run the aspect logic against that, re-source a
  full-bleed original, or accept the bars as authored intent. A wrong automatic
  answer is worse than the current queue, so those five (`258-cleanup` with the
  160-row letterbox, plus the 3px-hairline four `259f` / `261f` / `262f` /
  `264-cleanup`) stay held ahead of cleaning. Nothing downstream is blocked for
  the other ten; this is a correctness hole in the audit, not a gate.
  Cheapest first step, and it needs no policy call: DONE cycle 11 (LEDGER 56,
  plan row R26, commit `ef67c49`). `first_pass` now reads the source PIL mode
  off the existing probe BEFORE any `convert("RGB")` and records `source_mode`
  + `alpha_flattened` in `upscale_audit`, so every future run self-reports the
  drop instead of leaving a file-size anomaly as the only tell.
  `alpha_flattened` is True for palette-with-transparency sources too, not
  just mode RGBA - a `P` + `tRNS` source flattens identically and would
  otherwise read clean. NOTE the 15 already-processed refs predate the field
  and carry no such key; their flatten is documented here, not in their
  audits. The "scan the remaining unprocessed refs" step is DONE (cycle 10
  swept all 46); what is still owed is the POLICY call itself (per sub-shape),
  and the note that the same blindness applies to any future letterbox in a
  solid non-black colour, where the RGB metrics would ALSO score clean.

- **iopaint-batch-drain - Stage-2 watermark batch reprocess - IN PROGRESS, and
  the NEXT SESSION'S focus (operator direction 2026-07-27).** The 46 refs
  approved this session join this queue. `first-pass-alpha-letterbox` is now
  PARTLY ruled: sub-shape B (10 slugs) is ACCEPT-AND-RECORD as of 2026-07-29 and
  is CLEARED for cleaning; sub-shape A (5 slugs - `258-cleanup` `259f` `261f`
  `262f` `264-cleanup`) is STILL HELD, because cleaning writes on top of
  `_firstdone` and a later "crop to the content box" ruling would mean redoing
  cleaning as well as first pass for those five. Clean the other 41 freely.
  Next: land the 3 pass-improvements from the triage (full-width banner band;
  chroma-thr ~12 default; namakx template-mask / adaptive dark_thr) -> re-run
  the worker over the 9 CLEAN-AUTO + cleared PARTIALs -> `save-working --tool
  iopaint` + submit needauth -> route fantasy-design + prestige-coven-xayah
  (+ fury-sona if fidelity demands) to the manual IOPaint lane -> clean-scan
  the 190 clean firstdones + dark-cosmic-ahri + the 14 uhdpaper firstdones
  landed 2026-07-18 (LEDGER 32 session) (G3 Haiku 2AFC + V3denoise
  halftone alt stay gated on the vision stage).
  Evidence: LEDGER 30 (bc5fc19) + `docs/research/IOPAINT_TRIAGE.md` (9 auto /
  7 partial / 2 manual); manual-lane launch cmd in
  `docs/research/CLEANING_INPAINT.md` + `.claude/commands/cleaning-pass.md`.
  Do-not-redo: Dekel / pure algebraic (LEDGER 29 measured cap); white-only
  masks (mask MUST cover the dark edge).

- **g1-dists-cap-ratify - CLOSED 2026-08-02. `MAX_COMMON_PIXELS` = 3840x2160 is
  ratified as ADR-007. Nothing open.**
  The value was shipped unratified (LEDGER 32, `b14b688`) because DISTS was
  otherwise uncomputable for 8K-class sources - 63 of 230 first-pass images had
  lost it silently. Ratified as-is on three grounds: it sits BELOW the proven
  ceiling 4096x2306 rather than at it, it lands on the scale 26 corpus images
  already use natively (so the cap is a no-op for them), and the mechanism only
  ever DOWNSCALES the reference, so AUDIT_GATES 1.2 caveat 2 still holds.
  The premise that had to be corrected to answer it: the cap sets the
  SOURCE-vs-OUTPUT COMPARISON scale, not the deliverable. Output stays exactly
  2560x1440; sources run to 6500x3660, and FR metrics compare at source scale
  because upscaling the reference manufactures a blurry reference.
  Do-not-redo: native-8K DISTS (measured impossible on this box, both devices);
  editing `MAX_COMMON_PIXELS` without a new ADR - `tests/test_g1_common_scale_budget.py`
  now fails CI if it moves. Watch: any future `DEFAULT_G1_THRESHOLDS`
  recalibration must SEGMENT on the `capped` flag, never pool capped and native
  measurements - that is one threshold fitted to two measurement bases.
  Evidence: `docs/adr/ADR-007-fr-common-scale-pixel-budget.md`;
  `docs/research/AUDIT_GATES.md` 1.2 point 6; LEDGER 32.

- **golden-sec6-ratify - GOLDEN_DEFINITION sec 6 Q1-Q4 - OPERATOR-BLOCKED.**
  Next: operator ratifies glasses shape / style-band steer / dodge lane /
  scorecard. Champion labels already DONE.
  Evidence: LEDGER 17 (open questions) + LEDGER 18 (labels done).

- **resource-4-messups - re-source 4 ingest messups - MANUAL (NOW).**
  Next: drop clean 1920x1080+ Battle Academia splashes for `xayah1` /
  `camille1` / `kaisa1` / `fiora1` into `0.Originals` + re-intake (originals
  are 1920x1173 with a ~210px foreign strip pasted on top). Fallback only if
  the manual grab is skipped: bottom-anchored crop -> ~1712x960 -> ~1.5x
  upscale (lossy; not preferred).
  Evidence: operator ruling 2026-07-07 (LEDGER 13); Tier-0 pHash found no
  local twin (423-file corpus), no source token for auto-fetch.

- **corpus-crop-redo - 3 slugs crop + reprocess - LATER.**
  Next: #115 Hwei / #247 Shyvana / #253 Soraka - champion label correct,
  crop the leftover top artifact, then reprocess.
  Evidence: `docs/research/corpus/CROP_REDO_QUEUE.md`.

- **g1-lpips-downscale-watch - downscale-only lpips threshold - LATER (watch).**
  Next: only if more synthetic-8K downscales trip a spurious `lpips > 0.2`
  FAIL, calibrate a downscale-only lpips threshold (ADR-006-style ruling).
  One datapoint so far - not actionable.
  Evidence: `elise-8k` operator force-submit + approve 2026-07-07 (LEDGER 12
  session).

## Open items - Medium priority

- **one-glyph-engine - the banned-glyph rule is declared THREE times - OPEN
  (opened 2026-09-06, LW's own finding, broadcast to all five in
  `moon_sync_inbox/2026-09-06-2253-from-LW-REVIEW-charters-*`).** MEASURED:
  `tools/strip_em_dashes.py` (the CI drift gate), `tools/precommit_gate.py`
  (the git hook) and `tools/edit_lint_check.py` (the edit-time advisory) each
  declare the same six codepoints independently. They AGREE today - diffed
  2026-09-06 - and nothing makes them agree tomorrow. This is RSC's charter
  row ("one rule must not have two readings") and LW is the counter-example
  that proves it. The fix shape already exists in this tree and shipped the
  same night: `precommit_gate.scan_handoff_text` is called by BOTH its
  enforcement points and `tests/test_handoff_write_gate.py` asserts the
  function-object IDENTITY rather than agreeing behaviour. Do the same for the
  glyph set: one declaration, the other two import it, and a test pinning the
  identity. Acceptance: exactly ONE literal declaration of the six codepoints
  in the tree, proven by a test that greps for the others and fails on a
  second. Do NOT settle for a test that merely asserts the three sets are
  equal - that is agreement, not convergence, and it is what exists now.

- **usm-halo-probe-cuda-oom - one GPU test OOMs on an idle GPU - OPEN
  (found 2026-09-06, unowned).**
  `tests/test_lw_usm_halo_probe.py::test_worker_spandrel_branch_produces_both_variants`
  fails with `torch.OutOfMemoryError` allocating 624 MiB inside the spandrel DAT
  forward pass (`.venv-upscale/.../DAT/__arch/DAT.py:253`). NOT contention and
  NOT flake: reproduced on two consecutive runs with `nvidia-smi` showing 11105
  of 12227 MiB free and no compute process on the device, so the probe's own
  working set is the suspect (tile size / batch in the spandrel branch), not the
  box. Invisible to CI because no runner has CUDA, which is why it survived.
  Next: re-run with `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True` to
  separate fragmentation from a genuine over-allocation, then cap the probe's
  tile size if it is the latter.
  Evidence: LEDGER 145.

- **autonomy-phases-bc - promote autonomy per calibration ladder - LATER.**
  Next: after the Phase A shadow window accumulates >= 50 operator-reviewed
  images, promote per the ladder. Never skip the ladder.
  Evidence: `docs/RESTORATION_PLAN.md` section 5.

- **shareability-packaging - package the process as the deliverable - LATER.**
  Next: package pipeline code, gate ladder, rubric, golden-set protocol,
  manifests - never the cleaned third-party images. Prereq: licensing
  re-check on detector/LaMa weights - the PROJECT-license half is now
  SETTLED (Apache-2.0 held after a full-spectrum re-evaluation,
  2026-09-06, LEDGER 145); only the third-party WEIGHTS audit remains.
  Evidence: `docs/RESTORATION_PLAN.md` section 9.

- **arm-scheduled-tasks - roster REVIEWED + acted on 2026-08-02. Every remaining
  row is blocked on a MISSING SCRIPT, not on approval.**
  `LW-WeeklyHygiene` is REGISTERED (Sunday 04:17, verified `Ready`). Its
  `-Model` default was `claude-sonnet-4-6`, not a current model id - fixed to
  `claude-sonnet-5` in the same change, since a weekly unattended task with a
  stale id fails silently every week.
  `LW-GeminiAudit` is RETIRED by `gemini-removal` - never registered, so nothing
  was disabled; it is off the roster for good.
  `LW-CIWatchdog` was blocked on a missing script, so the script was WRITTEN and
  the task is now REGISTERED (verified `Ready`). See `ci-watchdog` below.
  `LW-Supervisor` is the only unarmed row left: `ops/lw_supervisor.py` does not
  exist, and it stays blocked until the product has a long-running process to
  supervise. Arming it now would fail on every logon.
  Deep-audit program stays DORMANT - separate gate, untouched by this review.
  Evidence: `docs/OPERATIONS.md` roster + `docs/OPERATOR_ANSWERS_2026-08-02.md`
  section 4; `docs/DEEP_AUDIT_CHARTER.md`.

## Status at a glance

Live status is intentionally NOT duplicated here - a static table goes stale.
Sources of truth:

- Pipeline state: `ops/runtime/pipeline_state.json` (written by
  `tools/lw_pipeline.py`; viewed via lw_monitor at `127.0.0.1:8901`)
- Transition history: `PIPELINE_LOG.md` (project root, append-only, gitignored)
- Process, pid, alive flag: `ops/runtime/health.json` (producer still TBD)
- Daily log: `logs/YYYY-MM-DD.log`
- Scheduled tasks: `Get-ScheduledTask -TaskName "LW-*" | Select TaskName, State`
  (expected result today: none - nothing is registered yet)

---

## Cross-cutting principles (never violate)

- **Frozen files** - see CLAUDE.md. Explicit operator sign-off required for any
  change. (The frozen list is currently EMPTY - files earn freeze status as the
  product stabilizes.)
- **Atomic writes only** - `tmp.write_text(...); tmp.replace(target)`.
- **`py_compile` before restart** - syntax errors crash silently under `pythonw.exe`.
- **Restart via `restart_trigger.txt`** - never `Stop-Process`; `taskkill /F /PID`
  for hard kills.
- **7-bit ASCII only** in authored content - no em/en dashes, no smart quotes.
- **Do not build blind** - product-shaping choices need an ADR or an explicit
  operator directive first.
- **Never double-resample** - one AI upscale, one Lanczos down, one light USM
  (the v1 softness bug, structurally banned by ADR-002).
- **Never touch `images/` content in tests or git** - tests use tmp_path;
  `images/**` gitignored except the .gitkeep skeleton.
- **The "reopen dance" is a COMMAND now, not a manual procedure (2026-09-01,
  `b2c932f`).** Every mention of it above predates
  `lw_pipeline reopen <slug> --to <stage> --yes [--source PATH]`, which moves a
  slug back, carries the manifest, drops the milestones the swap invalidates
  (refusing unless each is hash-preserved in `9.Image Backup`, matched by
  CONTENT not filename) and records REPLACE_SOURCE + REOPEN. Removal is
  `lw_pipeline remove <slug> --yes`. Do NOT move stage folders by hand - the
  single-writer rule has no exceptions.
