# WAKEUP_NOTES - LW hand-off ledger

---

## 2026-09-07 - the account path is out of the public tree, and guarded

- **`account-path-in-a-public-repo` CLOSED (LEDGER 166).** The ROADMAP row's
  own count was wrong and correcting it was the first move: 32 was a
  single-separator measurement, the real corpus was **68 tracked files**. Five
  were invisible to the original sweep entirely - a tracked evidence artifact, a
  captured gallery-dl fixture, two test placeholders, and a stale per-session
  scratch path using the 8.3 short name `ADMINI~1`.
- **RED first, and the guard proven ARMED rather than merely failing.**
  `tests/test_no_account_paths.py` failed on 111 hits while all 15 of its
  detector / placeholder / exemption arms passed. It parses the ACCOUNT SEGMENT
  instead of banning `C:\Users\`, because ROADMAP and CLAUDE.md have to write
  the shape down to document the rule - and that also catches a path pasted from
  another machine in the fleet, which a ban on one name would miss.
- **The split the ROADMAP demanded was respected.** (a) prose + tool literals,
  one scripted pass, 41 files / 118 occurrences, the pinned interpreter
  collapsing to `python` on MEASURED equivalence. (b) load-bearing by hand: both
  hooks resolve `$PYTHON` -> `$LOCALAPPDATA` pin -> PATH, with
  `test_git_hook_gate_e2e.py` green in the SAME change (5 passed, both refusals
  with HEAD unchanged, positive control landing).
- **A hook that fails to resolve dies SILENTLY, so presence was not accepted.**
  `.claude/settings.json`'s 11 commands became bare `pythonw` and were verified
  EXECUTING under both `sh` and a real `cmd.exe` before the change was trusted.
- **`tools/lw_paths.py` is new** - the one place the machine layout is written
  down. Four interpreter constants import it; config values became `~`-relative
  and expand at the consumer.
- **Evidence was not damaged to pass a guard.**
  `scratchpad/usm_fidelity_census.json` was rewritten by path PREFIX only and
  the rewrite ASSERTED every non-path value byte-identical, so the USM ruling it
  backs is untouched.
- **Verified:** full suite `2640 passed, 18 skipped` exit 0 with
  `LW_REQUIRE_HOOK_GATE=1`; ruff clean; `drift_guard.py` exit 0; every rewired
  module re-probed live and resolving to the SAME values as before.
- **History decision HELD and re-confirmed with measurement:** fix forward, no
  third rewrite. Do not re-open it.
- **Inbox:** 0 unread of 97 at session start and again on a mid-session
  re-check; newest note is `2026-09-07-0210-from-CS`, already answered. Nothing
  to ack.

---

## 2026-09-07 - the hook refusal probe, ported real and proven by mutation

- **`test_git_hook_gate_e2e.py` SHIPPED (LEDGER 160, commit 0d5211a).** RC's
  real file out of `moon_sync_inbox/from-RC-verbatim/`, adapted to LW's two
  hooks. NOT a fifth paraphrase - the note-channel versions are superseded.
- **Premise CORRECTED before porting.** LW already had four real-commit tests
  in `tests/test_git_hooks_gate.py`, so the gap was never the happy path - it
  was the FIXTURE. The old one inherited the operator's global git config, did
  not pin `PYTHON` (the hooks' default interpreter path does not exist on the
  Linux runner), did not set `commit.gpgsign=false`, and passed the banned
  glyph through `-m`, which tests argv encoding rather than the gate.
- **The positive control is the whole point and it is EARNED, not asserted.**
  Mutation run on LW's own tree: make the fixture silently fail to copy
  `tools/precommit_gate.py` and BOTH refusal tests still PASS while only the
  clean-commit test goes red. A refusal-only probe would have called that
  green. Second mutation: swap the glyph for an ASCII hyphen, both refusals go
  red, so they depend on the glyph and not on the harness.
- **CI can no longer go green by skipping.** `LW_REQUIRE_HOOK_GATE=1` prefixes
  the suite in all three jobs and turns the probe's environment skips into
  failures; `tests/test_ci_gate_arming.py` grew the parity guard so a fourth
  job cannot dodge it. Guard-the-guard: un-arming `check` turns it red.
- **The tracked `.claude/settings.json` was publishing the operator's posture
  (LEDGER 161, `09a68f4`).** `bypassPermissions` and three siblings plus an
  allow list of `[".*"]`, in a PUBLIC repo. Split: tracked keeps `env` +
  `hooks`, the rest moved to gitignored `settings.local.json`; allow lists
  UNIONed, no local value overwritten, so this box is unchanged. Severity was
  overstated at first and is corrected in place: the app gates permissions on
  workspace TRUST above the settings file, so this is a category error, not a
  hazard. The ruling holds either way - a value identical in five trees is
  environment, not repo config. Guarded by `test_tracked_settings_is_safe.py`.
- **The ack defect is FIXED, not just ritualised (LEDGER 162).** It bit a third
  time this session before the fix landed. `--mark-inbox-seen` now marks only
  what the last report SHOWED (`ops/runtime/sync_inbox_reported.json`); the
  fallbacks (no record yet, or `--all`) are explicit and the CLI names which
  mode it used. The hand-off ritual alone could never close this - a note that
  lands a minute after the report is still in the listing at ack time.
- **Clock convention adopted: stamp notes with REAL wall clock.** RSC measured
  per-sender skew growing through a session (LW was worst at +375 min). LW's
  first reply tonight went out mis-stamped `0510`, was re-filed as `2340`, and
  the mis-stamped copies were removed from all four inboxes.
- **RC ACCEPTED both LW amendments to the reserved-slot design** (its 0020
  note) and LW is to AUTHOR the reap arm: plant a `reserved-cs.lock` older than
  the stale window, run `reap`, assert CS can then take its floor. Blocked on
  the repo-key round landing first. RC also corrected its own cite - LW's
  acquirer is `ops/loop/loop_controller.py:951`.
- **The watcher was measured against RC's five properties and failed three
  (LEDGER 165).** All three fixed: notes keyed on name alone (an in-place
  CORRECTION was invisible), payloads keyed on the SENDER's manifest (a check
  whose evidence comes from the thing being checked), and SessionStart firing
  once (mail landing mid-session invisible until the next start - now a
  UserPromptSubmit hook, which was DECLARED WITH AN EMPTY HOOKS ARRAY).
- **Key change re-baselines the seen set once** - done deliberately with
  `--mark-inbox-seen --all` after reading. Not a bug.
- **The account-path row now carries its HISTORY measurement:** 26 commits,
  published on origin/main. Decision recorded: fix forward, no third history
  rewrite for a built-in account name. Operator can overrule.
- **The inbox was answered END TO END (LEDGER 164, `9db4371`).** 15 unread
  including two URGENT. Both watcher defects FIXED here: subdirectory
  blindness (LW was hiding `from-RSC-verbatim/` and a top-level payload) and
  the `(N files)` key RC refuted within the hour - a REPLACED file leaves the
  count equal, so the key is a digest now (MANIFEST.sha256 when shipped).
- **RSC's `test_no_secret_literals.py` ported and credited.** Two false
  positives fixed rather than exempted: a PowerShell `$var` re-export is not a
  literal, and every exemption is now asserted load-bearing.
- **CS's digest disagreement was LW's own doing.** `1de8d4e` (ADR-012) rotated
  the mutex names; CS's `f1b4b011` pin is pre-rotation. Nothing drifted. LW
  supports CS's vendored-or-declared-fork counter-proposal.
- **OPEN and split in two: 32 tracked files carry the operator home path in a
  PUBLIC repo.** Prose is cleanup; `.githooks/*` are LOAD-BEARING (they resolve
  the interpreter through that path). Do NOT bulk-sed - the hook half needs
  `tests/test_git_hook_gate_e2e.py` green in the same commit. ROADMAP row open.
- **STANDING, operator directive 2026-09-07 to all five repos: review the sync
  inbox AND ITS SUBDIRECTORIES for ingest, review, implementation and REPLY.**
  Not just the notes - the payload directories too. LW had ingested 1 of the 48
  files in `from-RC-verbatim/` when the directive landed.
- **Full payload review done (LEDGER 163).** 2 files byte-IDENTICAL
  (`slots.py` `629c3d511d25`, `winmutex.py` `0b112a4f6bfa`) - three trees now
  agree by measurement, closing the round RSC refuted. 2 ingested
  (hook probe, port map). 1 ingested as a FINDING rather than a file: RC's
  ascii sweep does not port, but the divergence it describes was LIVE here -
  an ellipsis or NBSP committed clean and reddened CI on the same commit,
  because three modules carried three different banned sets. Converged and
  pinned (`test_glyph_rule_has_one_reading.py`, `df6f5bc`); the widening
  exposed an NBSP-blind byte prefilter in `strip_em_dashes`.
- **Queued, not guessed at:** RC's `test_stop_claim_gate.py` has 63 arms to
  LW's 48 across `test_claimed_green_gate*.py`. Most are RC-claim-specific; a
  delta scan for the GENERIC arms is the one real gap the review left open.
- **Inbox: 3 notes read THEN acked, in that order.** RC's 0135 slot-reservation
  REVIEW, 0140 (the watcher survives `/clear`; the real gap is no session at
  all), 0150 (the repo-key blocker is measured - LW's root rename would have
  moved its reservation). Replied in one note; see `moon_sync_inbox/`.
- **Open, and it is a REVIEW so silence is not assent:** RC's reserved-slot
  design needs the short repo keys agreed FIRST (`rc lw rsc cs ll`). LW's
  `ops/loop/loop_controller.py:952` passes `repo=str(ROOT)`, a full path with a
  space in it, which is exactly the value that must stop being cosmetic.
## 2026-09-06 (late night) - both gates built: the hand-off WRITE gate and the inbox watcher

- **Charters reviewed and answered, both broadcast to all five.** LW ADOPTED
  v2 sections 1-6 and v1 sections 1 and 3, and filed TWO dissents. RC accepted
  BOTH within the hour in CHARTER v3: (1) v2 section 5's "no timebox" inverts
  for a DEFECT FIX, which then waits on the slowest carrier (~7h) while the
  defect runs - amended to "author may land, must broadcast the digest, pin
  stays PROVISIONAL until trees hash equal", plus RC's addition that the
  broadcast must carry the DEMONSTRATION not the assertion; (2) v1 0(b)'s
  tie-break needed a party-disclosure line and reopen-on-new-evidence, because
  RC owned four of the nine defects in v2's own table. **Do not re-litigate
  either - both are settled in LW's favour.**
- **`handoff-write-gate` SHIPPED (LEDGER 158, a573363).** One rule engine,
  `precommit_gate.scan_handoff_text`, called at BOTH enforcement points - the
  test asserts the function-object IDENTITY, not agreement. `--scan-files`
  matches RC's CLI name deliberately. No exemption list.
- **`sync-inbox-visible-at-session-start` SHIPPED (LEDGER 159, 486c448).**
  Unread mail now prints at session start; UNREAD is a set of seen FILENAMES,
  never a watermark. Acknowledge with `python tools/lw_facts.py
  --mark-inbox-seen` and ONLY after reading. An unread `REVIEW-`/`ACTION-`
  note raises an anomaly, which is how this session found the two REVIEWs it
  answered. It caught three notes that landed WHILE the code was being written.
- **Inbox baseline was set this session** (all 58 notes marked seen). Anything
  the next session sees as UNREAD is genuinely new mail.
- **LW's hooks are declared AND their targets exist**, by RC's corrected
  `hookcheck.py` (the first version RC sent was vacuous and would have passed
  LW too): 10 script targets checked, 0 missing, exit 0. `caveman_default.py`
  and `lw_facts.py` both fire - their output is in this session's own context.
- **LW has NO worktree/branch risk**: one worktree (the repo), one branch
  (`main`), `ahead=0 onremote=2`. Nothing matching RC's `ahead>0 onremote=0`
  single-copy shape.
- **Still open and unchanged:** LW has no temp-repo hook refusal probe with a
  positive control (RC was asked for the shape); LW's THREE separate
  declarations of the banned-glyph rule are a real divergence risk and are
  recorded as such; the `123f` hand-clean in Photoshop is operator manual work.
- Suite 2574 passed / 18 skipped, run fresh after both changes.

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
