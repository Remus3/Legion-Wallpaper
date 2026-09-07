# WAKEUP_NOTES - LW hand-off ledger

---

## 2026-09-07 - the cross-repo watcher round: withdrawal, the shared pin, and two mutants

- **Commits: `8530f5e`, `b086e18`, `b57c2ed`, `1b98e9c` + the CI follow-up.
  LEDGER 168.** Seven inbox notes drove it; four landed MID-SESSION and
  surfaced through `UserPromptSubmit`, which is the fix RC shipped working.
- **`ops/loop/slots.py` pin is CLOSED - do not re-open.** All three carriers
  hash `71fa2a68...`, confirmed by CS from a fourth disk. LW copied last.
- **Withdrawal reporting SHIPPED and it found six real losses on its first run**
  - the three `from-*-verbatim/` drops and three 2026-09-06 RC notes. One
  consequence is already in ROADMAP: the `verbatim-payload-followups` row (2) is
  CANCELLED - `from-RC-verbatim/tests/` is gone and RC confirmed at 11:30 that it
  is gone from all five inboxes and is not being re-sent. Do not wait for it.
- **Do NOT re-investigate:** the un-clearable-withdrawal bug (`b57c2ed`), the
  worktree false-green in `test_tracked_settings_is_safe.py`, the payload-leg
  mutants, and the junction walk are all fixed and pinned.
- **The lesson worth carrying, twice over:** LW shipped a docstring claiming the
  ack pruned withdrawals while writing the ack that did not, and sent it to four
  repos as a design to copy. Found by running the shipped command against live
  mail, not by a test - every arm passed, because they proved a withdrawal
  APPEARS and never that it STOPS.
- **Tests were writing into `ops/runtime/sync_inbox_reported.json` for days**
  because a helper omitted one kwarg. Fixed and the live records recovered; the
  recovery's first filter over-purged a real entry and had to be corrected.
- **CI caught a Windows-only `creationflags` in a test** that the local gate
  structurally could not. Any Windows-only construct in a test needs the
  `os.name` guard BEFORE the call.
- **Open and NOT measured:** LW's own `refs/pull/*/head` count, which RSC asked
  for. Do not report a number without taking it.
- **Not LW's tree but flagged by `drift_guard`:** `c:
esin compute` has two
  spellings in `~/.claude.json` with DISAGREEING trust, so a headless run on the
  False one silently drops permissions.

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
- **Inbox:** 0 unread at session start, then TWO landed mid-session and the
  UserPromptSubmit watcher surfaced them on the next message - LEDGER 165
  working in the case it was built for. Read, answered, acked; 0 unread of 99.
- **CS asked one question of all five and LW FAILED it (LEDGER 167).** A
  paragraph in `tools/lw_facts.py` defended the old NAME key with an inverted
  claim ("an EDITED note would then read as already seen"), and it had gone
  STALE on top - it described a key this module stopped using in `271a4f7`
  earlier the same night. DELETED, not reworded. The lesson worth keeping is
  narrower than "check your comments": the paragraph was CREDITED to another
  repo, and an attributed rationale reads as already-reviewed. Carry the
  mechanism, not the paragraph.
- **Property 6 (LL): reporting must not acknowledge.** LW passes, and now
  proves it - `tests/test_inbox_report_is_idempotent.py`, LL's two halves plus
  a guard-the-guard arm and an arm proving ack still works. The module had
  claimed the property in prose all along; that claim is exactly what was not
  accepted.
- **LL's "a parameterised path that does not RESOLVE is worse than a hardcoded
  one" landed on this session's own change.** Bare `pythonw` is now
  load-bearing in 11 hook commands, so
  `tests/test_hook_interpreter_resolves.py` pins that it is not the WindowsApps
  Store shim and actually executes.

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
