# WAKEUP_NOTES - LW hand-off ledger

---

## 2026-09-07 - independent audit of RC's public history (67c87bf, 4fd66f7)

- **RC invited it; the operator authorised it.** RC went public at 15:15 by
  DELETE-and-RECREATE (13 `refs/pull/N/head` are permanent) and reported 11
  sibling-name hits in 8 blobs of the two byte-pinned modules.
- **RC's 11 is EXACT** - re-derived hit-by-hit from an ANONYMOUS mirror clone
  (`-c credential.helper=`, so it measures what a stranger gets), all 66620
  objects streamed and split by object TYPE. **RC's "all in" is NOT:** 14 hits /
  10 blobs / 4 filenames, the extra 3 in two DOCUMENTS a module-scoped scan
  cannot see. Per-name: LW 8, RSC 3, Red Moon 3, LL 0, CS 0. Trees 0, commits 0.
- **The one worth carrying: LW's first Red Moon pass returned 653 and was
  wrong.** All substring matches inside longer words (`form-empowe`+`red moon`+
  `stone`). Anchoring took it to 3 - a 218x inflation. Caught ONLY because the
  tool printed a sample line beside the count. Rule: a name-matching rule is not
  evidence until run against a string it must NOT match; a count without its
  matched text is not reviewable.
- **Three things RC did not measure:** `refs/pull` is a genuine zero with a
  control; `backup-pre-scrub-20260621` is public but CLEAN (ancestor of main
  inside the rewritten history); and **6 commits carry the operator's personal
  email plus 5 Claude attributions, all post-recreate.** A history rewrite has
  no opinion about the commits you make after it - same operator, all five repos.
- **Delivered:** RC 18:13, then CS/LL/RSC 18:17 as three byte-identical copies
  (sha256 `ded8c547849ead67`), plus an 18:20 correction to RC because the copy
  reversed a sentence already in RC's tree. Sibling copy OMITS the email
  deliberately - unknown whether they track their inboxes.
- **Do NOT redo:** the audit is done and the mirror clone deleted; reproduction
  recipe is in the notes. Operator DECLINED a further RC rewrite of LW's name.
- **Live finding, not acted on:** `drift_guard` reports `c:
esin compute` has
  2 spellings in `~/.claude.json` with DISAGREEING trust [False, True] - the
  exact bug CLAUDE.md records as fixed machine-wide 2026-09-05, regressed. A
  headless RSC run on the False spelling silently drops permissions, and RSC has
  just agreed to build an unattended responder. Not fixed here: it is a trust
  setting outside LW's tree. Tell RSC.

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
