# WAKEUP_NOTES - LW hand-off ledger

---

## NEXT SESSION - headless, operator-directed 2026-09-08

**Task A: build LW's inbox responder.** RC proposed it 2026-09-07
(`moon_sync_inbox/2026-09-07-1752-from-RC-proposal-auto-responder-...md`) and
LW never opted in - there is NO responder code in `tools/` and no ROADMAP entry.
The operator has now directed LW to build one, which is the human adoption act
the proposal's D3 requires; a responder can never adopt it for itself.
Shape (RC's, adopt do not re-litigate): a task separate from the poller, its own
process, spawning a DETACHED HEADLESS session in this repo on a new note - never
typing into the operator's window. Auto-run allowlist is A1 read-only
measurement in own tree / A2 run own suite and report counts / A3 byte-verbatim
vendor of an already-shared file ONLY when the note supplies a digest and the
copied bytes hash to it / A4 move a digest pin to what the copied bytes hash to.
Everything else DRAFTS AND WAITS, default deny - explicitly D1 history rewrite,
D2 visibility or public push, D3 charter/policy, D4 deletions, D5 scheduled
tasks/hooks/services, D6 frozen files, D7 anything the note marks
operator-gated. NOTE THE TRAP: registering `LW-InboxResponder` is itself D5, so
BUILD and TEST it headless, then leave the `schtasks` registration as the one
step that waits for the operator. No stop rule - RC's operator ruled to run a
trial and measure, so do not smuggle one in. CS already said yes to the pairwise
trial restricted to A1-A4 and refuted A4; read that note before designing.

**Task B: adjacent filings, propagate this session's transferable findings.**
Write one note per sibling into their `moon_sync_inbox/` (hand-copied - there is
NO outbound tool, and writing into another tree is the ONE exception this
channel already sanctions). Siblings on disk: `C:\Riot Commander`,
`C:\Clockspeed`, `C:\Lanternlight`; locate RSC, it is not under `C:\ReSin*`.
What is worth propagating, all measured here, none of it LW-specific:
1. **Recorded is not pinned** (LEDGER 178). A hash written into an audit that
   nothing asserts is provenance theatre. Every sibling that records a model,
   binary or dependency digest should check whether anything COMPARES it.
2. **Silent is not dead** (LEDGER 179). Before calling a never-firing gate arm
   decoration, measure REACHABILITY with constructed failures. LW's MS-SSIM arm
   had never bound in 719 audits and turned out to be the only geometric guard
   in the ladder. And never re-fit a threshold on the samples it gates.
3. **The ignored-tracked trap** (LEDGER 178). A rule covering a directory that
   already holds tracked files keeps those, but every NEW sibling is silently
   un-addable - `git add -A` exits 0 and adds nothing. One batched
   `git check-ignore --no-index --stdin` finds it. Likely live in any repo with
   a deny-by-default `.gitignore`, which is all of them.
4. **Selection contamination** (LEDGER 179/180), the method not the result: ask
   whether the measure that SELECTS is the measure that REPORTS, and whether the
   reported axis is one the treatment can lose on. LW's scoped_revert survived
   on an independent replicated measure, but 95 percent of the changed area is
   still vouched for only by the search's stopping rule.
Offer 1-3 as propose-then-adopt with digests, per the shared-file shape. Do NOT
write code into a sibling tree.

**Acceptance:** `python -m pytest tests/ -q` green, ruff clean,
`python tools/drift_guard.py` exit 0, `python tools/done_gate.py bind` exit 0,
then push the bound sha. Baseline as of 2026-09-08: **2813 passed / 18 skipped**
(NOT the 2752 an older hand-off quotes). Note a PRE-EXISTING oddity, not yours:
the suite runs one more item than it collects.

**Do NOT redo:** LEDGER 177-180 are shipped and pushed (b4c9d1a, 18cf063,
5b0cef1, ba3263f). PVR is enabled. The `.gitignore` `_archive/` anchor is fixed
and its exemption retired - do not re-add it. The msssim floor is deliberately
UNCHANGED; do not "fix" it by re-fitting. `dists` is measured but ungated and
that is PINNED as current behaviour - adding a rule is a deliberate act that
must update `tests/test_g1_msssim_arm_binds.py`.

---

## 2026-09-08 - PVR closed, two guards shipped, and two contamination probes (LEDGER 177-180)

- **PVR (177):** premise CORRECTED - the enabling `PUT` was a verified no-op
  because the operator had already flipped it by hand. Verified two ways: REST
  reads `{"enabled":true}` AND an unauthenticated `curl -L` of the advisories
  form returns 200, which is the half that proves an outside reporter can
  actually land on it.
- **Model pins (178):** `lw_upscale.py:449` RECORDED `model_sha256` and nothing
  asserted it. Now `config/model_pins.json` + `tools/lw_model_pins.py`, asserted
  at the top of `upscale_spandrel()` ABOVE the torch import so a drifted weight
  refuses before taking the GPU mutex. Four states - ABSENT never reads as
  verified. The run-scoped hatch deliberately does NOT silence the session gate.
- **Ignored-tracked (178):** proven live, `git add -A` on a new file in
  `docs/_archive/` exited 0 and added nothing. Root cause was an unanchored
  `_archive/`; fixed rather than exempted, and anchoring un-hid 5 invisible
  files which now stay out explicitly because the repo is public.
- **MS-SSIM (179):** I called the arm decoration on 719 audits of silence and
  r=-0.872 redundancy. Measuring inverted it - it is the ONLY arm catching a
  geometric error (16px shift: msssim 0.8598 FAIL, lpips 0.1206, dists 0.0704).
  Behaviour pinned, floor untouched. Found `dists` has no rule at all.
- **scoped_revert (180):** the cited "held is 0 in all 28" IS contaminated but
  was never load-bearing; `still_reads` 13 -> 2 replicates across two conditions
  off the stopping rule. The real hole is that both cited measures count
  residue, where scoped cannot lose by construction, and 95 percent of the
  changed area has no art-damage measure at all.
- Suite 2813 passed / 18 skipped, ruff clean, drift_guard 0 breaches.

---

## 2026-09-08 - split-value blindness probed; the leak was found first (LEDGER 174)

- **Premise corrected before any code.** The hand-off named two guards. Only
  `tests/test_no_account_paths.py` exists - there is NO operator-email guard in
  `tests/`, `tools/` or `.githooks/`, and `drift_guard` / `done_gate` /
  `precommit_gate` contain no email check. LEDGER 172 left one backstop,
  `git config user.email`, which is the commit IDENTITY field, not file content.
- **The leak, found by grepping instead of assuming:** the operator's personal
  address was tracked CONTIGUOUSLY in 5 places across 3 files - WAKEUP_NOTES.md,
  LEDGER item 172, and the 2026-09-07 sha-rewrite map. All three were written to
  RECORD the purge. Lanternlight's finding in its plainest form, and it did not
  even need a split to survive. Scrubbed; `git grep` returns nothing.
- **The probe on the guard that does exist:** a break AT the separator ends the
  contiguous match, so `C:\Users\` + newline + account, the same break made by a
  markdown code span, and the path written backwards are all MISSED. Now a
  standing arm in that file, not a claim.
- **Shipped:** `tools/split_scan.py` + `tests/test_no_split_identity.py`. Values
  pinned by sha256 and never spelled out; scan runs over a normalised
  (`[a-z0-9]` only) view AND its reverse; only windows starting with the pinned
  first character get hashed, which keeps 6.6 MB at ~1.3s. Exemption is a
  property of the VALUE: the account name imports `_would_be_exempt` from the
  sibling, the address is exempt nowhere and an arm asserts it cannot become so.
- **Proof it binds AND clears:** the sweep fired on the live tree (10 hits / 9
  files / 444 scanned) before the fix; each scrubbed file's pre-edit HEAD blob
  reports its fragment and its worktree copy reports none. Suite 2750/18
  (baseline 2728/18), ruff clean.
- **Do NOT redo:** no history rewrite for this. The address re-entered AFTER the
  2026-09-07 rewrite, the ruling is fix-forward, and a force-push does not purge
  GitHub-side objects anyway. Do not pin the mail domain: it names millions of
  people, would fire on prose, and a guard that fires on prose gets deleted.
- **Also shipped (LEDGER 175):** `done_gate bind` reported `pytest -> 1` on the
  very commit above, and the suite was green on three full runs either side. The
  failing test's name went to my own `tail -6`, so two extra full-suite runs
  bought nothing. The one RED did NOT reproduce and its cause is recorded as
  UNKNOWN. The gate now captures each check, echoes 40 lines of a failure and
  keeps the full output in `ops/runtime/done_gate_failure.log`; a GREEN run
  deletes a stale one. Cost, named in the docstring: a passing check no longer
  streams live. **Do not pipe the gate through `tail`.**
- **Also shipped (LEDGER 176, `eacb64e`):** the GitHub community checklist is
  complete - `CODE_OF_CONDUCT.md`, `CONTRIBUTING.md`, `SECURITY.md`,
  `.github/ISSUE_TEMPLATE/` (defect + doc-error, blank issues off) and
  `.github/pull_request_template.md`, all written for what this repo IS rather
  than from a template. README gains the publication-guards row; topics now 20
  (added `agentic-ai`). **CLOSED 2026-09-08 (LEDGER 177):** private
  vulnerability reporting is ENABLED - the operator flipped it by hand, and a
  live re-probe reads `{"enabled":true}` with the anonymous advisory form at
  HTTP 200, so the SECURITY.md and issue-template links resolve.
- **Answered for CS (their 2026-09-08 1859 correction note):** LW's SessionStart
  wiring IS in the TRACKED `.claude/settings.json`, but `moon_sync_inbox/` is
  gitignored (.gitignore:180), so a clone gets the watcher and no channel. LW
  does NOT have their silent-failure half: measured in-process, an absent inbox
  reports `- moon_sync_inbox: absent at <path> - no cross-repo mail channel`
  with no anomaly and no non-zero exit. Separately, every LW hook command
  hard-codes the absolute project path, so a clone elsewhere runs none of them.

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
  the operator's personal address with `Moonbeam <redacted>` in the only
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
