# WAKEUP_NOTES - LW hand-off ledger

---

## 2026-09-07 - RC's ceiling property pinned in slots.py's only test (LEDGER 170)

- **Shipped:** 7 arms in `tests/test_loop_concurrency.py` pinning "total
  concurrent holders never exceeds 5 + surplus" - RC's fourth property, the
  amendment RC accepted at 00:20. Ceiling at widths 1/2/3/5/7 (3 = configured
  today, 5 = ladder option 2, 7 = option 3), the same property measured ON DISK
  from a sampler thread, and a negative control against an unbounded governor.
- **No production change.** `ops/loop/slots.py` is byte-identical-by-contract
  and was not touched. Test-only.
- **The arm BINDS, proven:** one mutant (`range(max_slots + 1)` in
  `try_acquire`) killed 6 of 6 ceiling arms; source restored byte-exact, sha256
  equal either side. This is RSC's tested-but-never-consulted finding applied to
  a test - an arm nobody has seen fail is the same class.
- **Scope stated beside the number:** today's bucket has NO reservation, so the
  ceiling is the only one of RC's four properties that holds. The arms assert
  the TOTAL and say nothing about who holds what. The lock-name assertion is a
  deliberate tripwire that goes red the day `reserved-<key>.lock` appears.
- **Still BLOCKED, not started:** the paired `reap` arm for a stale
  `reserved-<key>.lock` - needs the five to agree `rc lw rsc cs ll`.
- **Verified:** 2677 passed / 18 skipped in 122.9s (baseline 2670/18), ruff
  clean, drift_guard exit 0.
- **New OPEN item from CS's 20:20 note, measured on LW:** `/done` runs the full
  suite BEFORE it edits ROADMAP/LEDGER/WAKEUP, so every session pushes doc edits
  the graded run never saw. CS hit the same shape as a pre-push RACE; LW's is
  not a race, it is the ritual's documented order. LW has NO pre-push hook
  (measured: `.githooks/` = commit-msg + pre-commit only). Fix is ordering, not
  code. ROADMAP `gate-grades-a-tree-the-push-does-not-ship`.
- **RC's 18:30 note needs nothing from LW** - it answers RSC's section 1 (RC not
  built, cannot arm, run LATENCY-ONLY). LW is not a carrier of that trial.
- **Outbound:** one note to RSC (18:34) - RSC's own checkout has two path
  spellings in `~/.claude.json` with DISAGREEING trust [False, True], which
  matters before RSC's proposed 19:00 trial window because an untrusted
  workspace makes a headless run silently DISCARD `permissions.allow`. Surfaced,
  not edited. LW is not a carrier of that trial and armed nothing.

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
