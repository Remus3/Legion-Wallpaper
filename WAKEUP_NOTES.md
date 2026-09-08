# WAKEUP_NOTES - LW hand-off ledger

---

## 2026-09-08 - 0.Originals ingest, then first pass on the batch (LEDGER 173)

- **Intake:** 122 loose files in `0.Originals` -> **117 intaken**, 5 refused by
  the near-dup perceptual gate and LEFT in place (`--allow-near-dup` is an
  operator override; not taken). 117 INTAKE + 117 ANNOTATE log lines all `ok`,
  `lw_pipeline verify` ok on 713 images, verifier subagent PASS on all 7 claims.
- **Recovery:** Tier 0 (pHash vs 292 reference_pictures) found NOTHING for this
  batch - 0 accepts, 1 borderline 14/14 review, and a self-match control proved
  the hash path live, so it is a real null. Tier 1 decoded 9/9 DeviantArt
  tokens, 4 oEmbed-confirmed alive. The other 108 are QUEUED for Tier 2 in
  `ops/runtime/tier2_queue_2026-09-07.txt` - SauceNAO free tier is ~4/30s and
  ~100/day, so it is an overnight batch, NEVER a loop.
- **Shipped code (d327642):** `--crop-overrides` gained a second grammar, a
  one-key `{side: pixels}` offset. The sides grammar could only say three
  anchors per axis and the operator picked a frame between them. It also fixed
  a latent bug: `list(crop_sides)` on a dict yields its KEYS, so an offset
  would have been recorded in the manifest as `["top"]` with the offset lost.
  35 new tests, RED-first evidence captured. Suite 2728/18 (was 2693/18).
- **First pass:** 111 processed, **108 submitted** to `_firstneedauth`, all
  exactly 2560x1440, upscaler V3detail DAT2 via spandrel at 4x (ADR-004).
- **Do NOT redo:** the two `dmrl7u8-*` slugs are NOT duplicates. They share one
  deviation (1376595440) but are phash 26 / dhash 27 apart - a multi-image
  upload. Both crops are operator-approved and already shipped.
- **Open, needs the operator:** 108 await approve/reject (never self-approved);
  7 slugs HELD `aspect_crop_heavy` need a framing call (3 pintrest lose 68-71%
  of area to reach 16:9); 3 slugs failed G1 on `lap_ratio` 0.91-0.93 vs floor
  1.0 - soft SOURCES, not the double-resample bug, and they kept their working.

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
