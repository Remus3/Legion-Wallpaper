# WAKEUP_NOTES - LW hand-off ledger

---

## 2026-09-07 - the operator email is out of the tree AND out of history (LEDGER 172)

- **Shipped:** two scrubs. `219fdb7` replaced
  `Moonbeam <close.benham@gmail.com>` with `Moonbeam <redacted>` in the only
  two tracked files that carried it (`docs/LEDGER.md` item 154,
  `docs/_archive/2026-09-06-sha-rewrite-map.md`). Then a `git filter-repo`
  rewrite of ALL 526 commits took it out of history.
- **Why the second scrub was the real one:** the address was on the author AND
  committer field of every commit. The doc scrub closed the smaller half; the
  operator asked for the rewrite on exactly that finding.
- **One mailmap line + one replace-text literal.** Identity ->
  `7991173+Remus3@users.noreply.github.com`, GitHub's ID-prefixed noreply for
  this account. That choice is load-bearing: GitHub attributes commits BY
  EMAIL, so any other replacement would have zeroed the contribution credit.
- **526 in, 525 out.** Only `219fdb7` pruned - once replace-text put `redacted`
  into its parent, its own diff was empty. HEAD tree byte-identical at
  `336db8f1` before and after, which doubles as proof the automated replacement
  wrote exactly what the manual edit did. New HEAD `3dec9e3`; 0 of 526 shas
  survived.
- **Verified live on the GitHub API after the force-push:** HEAD author +
  committer read the noreply address, the commit still resolves to `Remus3`,
  and `/contributors` returns one entry, `Remus3` with 525 contributions.
  Locally: one identity across 525 commits, zero hits in any blob over
  `git rev-list --all`, never in a commit message.
- **NOT purged, and it matters:** `GET /commits/219fdb70...` still answered 200
  after the push. Old shas still resolve on GitHub and their identity fields
  still carry the address. Only a Support purge or delete-and-recreate closes
  that - the standing CLAUDE.md ruling, re-confirmed here rather than assumed.
- **Followed up so it cannot come back:** `git config user.email` reset to the
  noreply address globally and repo-locally.
- Map `docs/_archive/2026-09-07-sha-rewrite-map.md` (275 cited shas, chaining
  note for walking three maps oldest-first). Backup bundle off-repo at
  `C:\LW-backups\lw-pre-email-scrub-2026-09-07.bundle` - it still contains the
  address by design, it is the rollback path.

---

## 2026-09-07 - the /done gate now grades the tree that gets pushed (LEDGER 171)

- **Shipped:** `.claude/commands/done.md` reordered - section 0 is an
  explicitly NON-BINDING pre-flight, everything authored (code, ROADMAP,
  LEDGER, WAKEUP, `LW-NEXT-SESSION.txt`) is committed in sections 1-6, and
  section 7 is the binding gate immediately before the push. Sections
  renumbered into run order; every "section N" reference to this doc was
  internal to it.
- **Premise CORRECTED:** CS found this as a pre-push RACE. LW has no pre-push
  hook (`.githooks/` = `commit-msg` + `pre-commit` only), so LW cannot have the
  race - LW had the worse form, the documented ORDER, which shipped ungraded
  doc edits every single session.
- **Ordering alone asserts nothing,** so `tools/done_gate.py`: `bind` refuses a
  dirty tree / a tree that moved mid-run, exits 1 on red, records the graded
  sha to a gitignored atomic receipt; `verify-push` refuses unless
  remote == HEAD == graded, asking the remote via `ls-remote`.
- **Two departures from the acceptance line, deliberate:** clean is
  `git status --porcelain` (a `git diff HEAD` is blind to an untracked authored
  file) and the pushed sha comes from `ls-remote` (the remote-tracking ref is a
  cache that a failed push leaves stale).
- **The arms bind:** 14 hermetic arms incl. the ritual doc's own order;
  6 of 6 mutants killed, source restored byte-exact. TWO mutants survived the
  first pass because the implementation's checks cover for each other - each
  needed an isolating arm. A six-of-six that looks like proof may not be.
- **Verified:** 2693 passed / 18 skipped in 145.9s (baseline 2677/18), ruff
  clean, drift_guard exit 0, and the gate dogfooded on this session's own push.
- **Still BLOCKED, not started:** the `reap` arm for a stale
  `reserved-<key>.lock` - needs the five repos to agree `rc lw rsc cs ll`.

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
