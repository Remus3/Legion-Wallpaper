# WAKEUP_NOTES - LW hand-off ledger

---

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

## 2026-09-06 (late) - the 5/6 localizer number, re-measured on CUDA

Commit `5f6f119` (+ this docs sync). Suite 2519 passed / 18 skipped, ruff
clean, drift_guard 0 breaches. Ledger 151. ROADMAP's top open item is closed;
`golden-overtarget-refreeze` moves to the top and is still the operator's.

**The 5/6 holds, but say it as 5/6 frames / 10/12 WRISTS.** Positions are not
the issue: CPU and CUDA agree within 2.8 px on a 1344x768 frame, CUDA is
deterministic run-to-run, and today's CPU arm reproduces the 2026-07-11 run to
0.0000 px, so that arm is an exact control. What moves is the CONFIDENCE score
(about -0.015 on CUDA) and two of twelve wrists sit at 0.304 and 0.305 against
`min_conf=0.3`. `seed22` left and `cand_02` right fall through; their ROIs go
`missing_wrist`. `seed22` still has its RIGHT wrist on a weapon so the frame
verdict holds, but the ROI it loses is the one over the PRIMARY crossbow. The
floor is left at 0.3 on purpose - 0.25 would restore both, and that is a tuning
call the measurement was not asked to make.

**The transferable bit: a number is only as portable as its provenance.** LEDGER
19's 5/6 had to be re-measured from scratch, at real cost, only because
`summary.json` never recorded which execution provider produced it. `run()` now
stamps a `_run` block with the providers actually BOUND - read off the live
session, because ORT drops to CPU silently while still advertising CUDA in
`get_available_providers()`.

**Golden set RE-FROZEN under USM 35 (operator blessing granted mid-session).**
All 12 regenerated through the live pipeline, `pv 6d43a6d4 -> ed249af6`, regress
PASS 12/12 with `pv_changed=False`. The hand pin to USM 70 is retired - the
frozen set finally validates the recipe that ships. Every fidelity metric
improved on every case (msssim +0.0008, lpips -0.0083, halo_pct -0.0229 mean)
and lap_ratio fell -0.4220, the 2026-08-02 census reproduced on a different
sample. `1341679-banding` reads lap_ratio 0.8416 now - below the G1 floor,
correctly ungated by ADR-006 for `downscale-only`, NOT a regression.
`lw_golden candidates` + `data/golden/cases.json` shipped so the next re-freeze
is three commands rather than archaeology.

**Cross-repo: RSC's `slots.hold()` leak is real here too, and LW took the one
measurement RC was blocked on.** A lockfile leaked by a lost unlink race keeps a
LIVE pid, so both arms of `is_stale` say "not stale" and `reap()` skips it - the
valve is disarmed by the case that trips it, and `loop_controller.py:952` holds
a slot per cycle under one pid. RC proposed neutralizing the payload but would
not ship without knowing whether a write is permitted against an open reader
handle. Measured on this disk: `unlink` fails WinError 32, `write_text`
SUCCEEDS, `tmp + os.replace` fails WinError 5. So the fix is viable and must be
a NON-atomic in-place write, which collides with both repos' atomic-writes rule
and will be tidied back into brokenness unless the comment says so. Ack filed in
RSC's inbox. `slots.py` NOT touched - joint round, top ROADMAP item.

**docs-guards badge: NO for LW, structurally.** RC's ci.yml ignores every `.md`
so a docs-only commit fires nothing there; LW's carries no filter, so a
docs-only push already runs the whole suite plus the drift gate. Recorded in the
ci.yml header + CLAUDE.md Settled, with the trigger that would flip it. The
header's "~28s suite" figure was stale and is now 2521/18.

**QA of the previous hand-off, one correction.** "Settling the USM 70 -> 35
question" reads as if USM were open. It is not: `USM_DEFAULT = (1.2, 35, 3)` is
SETTLED (2026-08-02) and CLAUDE.md says so. The real entanglement is narrower
and now written into the ROADMAP item: a 4096x2305 source is not exactly
2560x1440, so `_usm_applies` is True and the over-target downscale-only branch
DOES apply an unsharp mask, which makes the flagged `lap_ratio` directly
USM-sensitive; the regress had to pin USM to 70 by hand, so the frozen set is
currently validating a recipe that has not shipped since 2026-08-02. Re-freezing
under the live default retires the pin. Still a blessing call, still untouched.
