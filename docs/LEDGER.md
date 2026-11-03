# Legion Wallpaper - Item Ledger

Append-only, newest-first per-item completion record. Kept OUT of `CLAUDE.md`
by design (CLAUDE.md has a hard per-turn auto-load size budget - never append
ledger entries there). Do not rewrite history - append each new item at the TOP
of the body below (newest-first, directly under the `---` rule), matching the
entry format documented here.

**Entry format** (one numbered block per completed item, numbering starts at 1
and only ever increases):

```
N. DONE **YYYY-MM-DD (short title; commit SHAs or "docs-only").** Body: what
   shipped, premise verification, how it was built (TDD RED-first evidence,
   worktree slices, verifier verdict), what was verified (suite counts, health
   checks), doc/roadmap syncs, and any FUTURE / do-not-redo notes.
```

Conventions carried from the format's origin: bold date+title lead; premise
VERIFIED/CORRECTED called out explicitly; verification evidence (test counts,
exit codes, health probes) stated, never implied; scope calls and rejected
alternatives logged so they are not re-litigated.

This file keeps the newest 20 entries. Older ones are per month under `docs/ledger/`
(index `docs/ledger/README.md`); `python tools/lw_ledger.py rotate` moves them, and a
rotation is a move, proven entry by entry. Item numbers never change.

Pointers: open work -> `ROADMAP.md` + `BACKLOG.md`; recent sessions ->
`WAKEUP_NOTES.md`; pruned ledger items + archived wakeups ->
`docs/history_notes.md`; decisions -> `docs/adr/`.

---

362. DONE **2026-11-02 (session 216 responder-authored worker: MAIN ORDER 2026-11-01-0825 kit v28, residual check; docs-only).**
   Inbox copy re-hashed sha256 7b2885f093f5099735976c6be56cc6786e76084ebb4a8dd40b09677908653f59, 7442 bytes, equals the parent's
   MAIN-match digest. Residual wiring already landed by dcec270 / LEDGER 361: MANIFEST.json sha256 343471741c03... == section 1,
   conformance() == [] at KIT_VERSION 28 (read back this run), KIT_VERSION pins 28 in tests/test_fleet_kit_conformance.py,
   tests/test_headless_env.py, tests/test_promise_probe_fleet_kit.py, tools/lw_promise_probes.py. No kit recopy, no code change.
   Gated suite this run (fleet_suite_gate, python -m pytest tests -q, log logs/responder-216-suite.log): exit 0, 4461 passed,
   19 skipped. The 1848 ANSWER of session 91 already carried the sha; one short responder-authored HOP 2 note closes the
   pending-ORDER row.

361. DONE **2026-11-01 (session 91 Maint-KitRollout /done: fleet kit v28 adopted dcec270; MAIN ORDER 2026-11-01-0825).**
   Kit v27 -> v28: MANIFEST.json, fleet_headless.py, fleet_identity.py changed (pre-push scans a push whose remote old tip is
   absent locally). KIT_VERSION pins moved in tests/test_fleet_kit_conformance.py, tests/test_headless_env.py,
   tests/test_promise_probe_fleet_kit.py, tools/lw_promise_probes.py. READ BACK at /done: MANIFEST version 28, 24/24 files hash
   equal plus the manifest (25/25), conformance() == [], git show dcec270 author operator. Suite (adoption run, log
   logs/kit-rollout-v28-suite.log): 4278 passed 19 skipped parallel, 183 passed 1 skipped serial, gated exit 0; the wrap bind is
   the graded run. CI READ: dcec270 ci 41369084316 success, codeql 41369084350 success. CI-90 closed: a025932 ci 41364943000
   success. ANSWER moon_sync_outbox/2026-11-01-1848-from-LW-ANSWER-to-MAIN-batched-1-answers.md, HOP 2, reached 1/1; MAIN's copy
   re-hashed at /done equal to the outbox (d2b96815...6015). DEVIATIONS: (1) gitlock owner was the claims hook id instead of
   the ordered kit-rollout.LW, the hook denied that id; the suite gate ran under kit-rollout.LW. (2) send_answers
   (tools/lw_inbox_responder.py:1038) claims under channel "tick" though this was a rollout. (3) The ANSWER went out before CI on
   dcec270 was read; CI read success afterwards. (4) LW-InboxResponder reads Disabled (schtasks 18:50, 18:51; last run 18:41:56,
   result 0; no HALT file) while CLAUDE.md says ENABLED (read back 2026-10-03) and the hand-off said LIVE; not touched, carried as
   RESPONDER-STATE. KIT-ROLLOUT-READ stays open: this run is that nightly but its usage row is not written until it exits.
   Pre-flight: ruff clean, drift_guard 0 breaches; no code authored, --lf skipped.

360. DONE **2026-11-01 (session 90 inbox triage: 13 unread notes, all DONE or NO-ACTION, none open; docs-only).**
   Operator asked to process the inbox. lw_facts unread set 13 of 664, read oldest first by mtime. 6 MAIN notes verify_main True:
   FIX 1935 pillow-13 (8dfef45, LEDGER 347; live open Dependabot alerts 0), ORDER 2045 suite speed (491bb85, LEDGER 348), ORDER 1926
   v23 (121eb25, LEDGER 346), ORDER 2200 v26 (12fe2f6, LEDGER 354), ORDER 2215 W44 (9308fae, LEDGER 355), ORDER 1223 (LEDGER 359): each
   DONE with its ANSWER in MAIN's inbox, hash equal. 2 kit bundles v23 + v26 bundle_verified True, NO-ACTION: superseded, manifest reads v27,
   24/24 files hash. 5 SS notes addressed to MAIN (2230, 2245, 0431, 1324, 1400), all ANSWER/TERMINAL, NO-ACTION. No outbound note, no code
   change. Mark: lw_facts --mark-inbox-seen (no --all). READ BACK: lw_facts "0 unread of 664 notes". INBOX-MARK dropped.
   Why the counts looked inconsistent: _inbox_lines sorts by display name and prints the last 10 (tools/lw_facts.py:893-894), and
   UserPromptSubmit prints only what this session id was not yet shown, so the two hook lists are disjoint parts of the same 13.
   Finished orders stay unread until an explicit lw_facts mark because the responder keeps its own seen store (three stores: lw_facts
   sync_inbox_seen.json, responder state, kit ledger inbox_seen.jsonl).
   Side findings, none acted on, all hand-off rows: DEPENDABOT-PR7 (gh pr view 7 reads OPEN, created 2026-11-01T22:38:50Z, requirements.txt
   + requirements-cv.txt; path B), KIT-SCAN-STALE (fleet_inbox.scan on LW reads 571 unseen, 25 WORK, all pre-ledger; no LW code calls scan
   or session_start), SS-MAIL (SS notes addressed to MAIN land in LW's inbox; cause not established).
   Previous push CI read before this push: 180e340 ci 41351984310 success. FUTURE: CI-90 reads this push's run.

359. DONE **2026-11-01 (MAIN ORDER 2026-11-01-1223 items 1-6 finished by MAIN drive-lw; 2cb0faa 9861028 6cd026c b689256 ca700f8 90917b6 6a3ddc6 cc5ad1a e7421cb).**
   Provenance: inbox copy sha256 prefix df7ed16b, verify_main True. The responder's work run was killed at 1800 s at 12:57
   after items 1-5, committed and unpushed; each ACCEPT was re-read against the tree, none fell short. Item 1: row stays open
   without a reply (tests/test_inbox_responder_orders.py). Item 2: gate read back 2/500. Item 3: cause in lw_kit_adopt.py
   closeout docstring (about 480 s adoption, then a nested /done with 683 s gate wait and a 179 s second suite).
   Item 4: hand-off read back 18856 B (under 20 KB), this entry's commit. Item 5: 358 entries before and after, same digest multiset.
   Item 6 FLEET-9: 8 bounds moved to budget() here (ca700f8 7, 6a3ddc6 1), 3 more already by 5c39ef3 (2026-10-26), pinned by
   tests/test_timing_assertions_use_budget.py (AST scan; red on real offenders, mutant killed). About 90 timeout= hang guards NOT
   converted: expiry there is not the claim under test. MAIN's "29 lines" NOT matched: pattern recorded nowhere; nearest grep at
   395770f 33 lines, 30 without budget, 2 true timing bounds. tests/conftest.py extra_ignore for inbox_pending_orders.json (90917b6)
   is a local widening of the guard; the same gap is in the kit IGNORE, reported to MAIN. Done-when open: FLEET9-READ on or
   after 2026-11-08.
   Suite: 6a3ddc6 RED, 2 failed test_the_interpreter_is_not_a_microsoft_store_stub[python, pythonw], 4271+183 passed: a Python Manager
   package dir matched the whole-word WindowsApps rule though the interpreter runs; fixed cc5ad1a (rule narrowed, both arms pinned),
   e7421cb (fixtures without an account-shaped path; cc5ad1a alone was red on test_no_account_paths, never pushed alone). Whole suite
   on e7421cb through the gate: exit 0, 4278+183 passed, 19+1 skipped, 104 s, no gate wait; live-state guard armed (FLEET_TEST_GUARD
   unset), its failure would be a non-zero exit. CI: 395770f ci 41297519489 success (CI-85); e7421cb ci 41351305098 + codeql
   41351305099 success. Row closed by fleet_inbox.mark_work_done directly (reconcile_orders only closes on an outbox ANSWER): pending
   read empty, scan and session_start do not list the note, enqueue_work on it returns None. No responder run started.
   FUTURE: PY-ON-PATH, KIT-IGNORE-GAP rows. CI-85 and LW1-READ dropped. fleet_done.py mark not run: driver paperwork, not the ritual.

358. DONE **2026-11-01 (session 88 /done wrap: CI-84 closed, RESPONDER-DUP-V27 read back; docs-only).**
   CI read back via gh run list --branch main: a5c05fb (tip of the push that also carried d903c51) ci 41295918326
   success, codeql 41295918373 success - CI-84 dropped. RESPONDER-DUP-V27: the LW-InboxResponder child spawned at
   04:01 on MAIN ORDER 2026-10-31-2347 ended rc 0 at 04:07:53 (headless_usage.jsonl kind order, sonnet), its
   progress file reads done; moon_sync_outbox holds exactly one 2347 ANSWER (2026-11-01-0407, TERMINAL) and
   git log shows no commit after a5c05fb - no duplicate ANSWER, nothing to reconcile. KIT-V27-PENDING carried.
   Pre-flight: ruff clean, drift_guard 0 breaches; --lf skipped (no code authored; the section-7 bind is the
   graded run).

357. DONE **2026-11-01 (Maint-KitRollout: fleet kit v27 adopted; MAIN ORDER 2026-10-31-2347).**
   Inbox copy sha256 056a54a1544fa4c51fe366f6ae11df5ee46c9088babfe7a4ab3ded7ad4f88d6f: verify_main True (MAIN
   committed outbox copy, 10399 bytes); bundle verified at KIT-COMMIT 56d000f (lw_inbox_responder.bundle_verified
   True, lw_kit_adopt.verify_bundle []). Vendored via lw_kit_adopt (byte copy): 8 files changed (MANIFEST.json,
   fleet_claims, fleet_headless, fleet_hook.sh, fleet_inbox, fleet_lanes, fleet_rewrite, fleet_suite_gate); READ
   BACK 24/24 files + MANIFEST.json sha256 0a90af35...e949c1 == section 1; FLEET-COMMON unchanged (no re-embed);
   conformance() == [] at KIT_VERSION 27. Settings unchanged; `{}` piped into both PreToolUse launcher commands:
   exit 0, empty stdout. KIT_VERSION pins 26 -> 27 (tests/test_fleet_kit_conformance.py, tests/test_headless_env.py,
   tests/test_promise_probe_fleet_kit.py, tools/lw_promise_probes.py). Section 4 tests changed: none (no exact
   usage-key spy, no fleet_claims.subprocess patch, no lanes key-set pin hit). Gated suite (fleet_suite_gate, lw_suite):
   4223 passed / 19 skipped parallel + 183 passed / 1 skipped serial, exit 0. NOT DONE, carried (KIT-V27-PENDING):
   section 5 item 3 - lw_inbox_responder now enqueues an ORDER into inbox_work.jsonl on its post-spawn mark_seen
   and never closes it; it must read `fleet_inbox.py pending` first and call mark_work_done after the ANSWER
   (deferred: the responder was live mid-tick on this same note). The LW-InboxResponder tick (pid of 04:01) had
   spawned a duplicate sonnet child on this ORDER concurrently; it was not touched. No rotator / lane loop to
   restart. One HOP 2 answer to MAIN.

356. DONE **2026-10-31 (session 87 / responder 209 /done; docs-only).** Wrap of the session that shipped 12fe2f6
   (FLEET-KIT v26, LEDGER 354) and 9308fae (MAIN 2215 W44 + UI/UX batch, LEDGER 355). CI-83 CLOSED: 9308fae ci
   41270362926 success + codeql 41270363046 success; 12fe2f6 ci 41268603050 + codeql 41268603049 success (gh run
   list read back). ANSWER 2026-10-31-2246 TERMINAL reached 1/1. WP-PICKLOG closed (ROADMAP flipped DONE, live pick
   line in logs/2026-10-31.log 22:28:58). Pre-flight: ruff all checks passed, drift_guard 0 breaches; the
   responder's suite read 4406 passed / 19 skipped with its exit code lost to a shell timeout, so the section-7
   done_gate bind is the graded run. Inbox: 9 unread of 658 left UNMARKED (INBOX-MARK carried with the list).
   inbox-responder progress read running (N1, pct 0, updated 22:22) while responder-run read done 22:47 - not
   touched. Wrap push CI = CI-84.

355. DONE **2026-10-31 (responder: MAIN ORDER 2026-10-31-2215 public view + W44 + UI/UX batched, 6 items).**
   Inbox copy sha256 b873714f7e7428c29deb93858765714280ddfd30d8dbe4ab6b61761a5e21288d (re-hashed; verify_main True
   against MAIN's committed outbox copy, 2405 bytes). Items: (1) README "Where it stands" Corpus + Code rows lose
   every hand-typed count (737/517/70/142/8, 124 tools, 240 files, 4,370 tests, 13 ADRs, 330 items, 830 commits);
   dated pointer to ops/runtime/pipeline_state.json kept. (2) README hero img -> docs/assets/social-preview.png
   (tracked, relative), alt text unchanged. (3) WP-PICKLOG: tools/lw_wallpaper_rotate.py tick() logs
   `pick <file> pos <i>/<n> cycle <c>` after a successful apply (none on dry-run or failed apply); TDD RED 1 failed
   -> green 45 passed; live LW-Wallpaper tick read back in logs/2026-10-31.log at 22:28:58 (pos 425/555 cycle 121).
   (4) R4 park date 2026-11-14 written into the hand-off R4 line; LEDGER park line due on/after 11-14 if tally 0.
   (5) LW-IOPAINT-RISK: .claude/commands/cleaning-pass.md records upstream archived (MAIN-reported, no fixes since
   2025-04; PyPI newest still 1.6.0, read 2026-10-31), pin iopaint==1.6.0 (pip show read back, torch 2.11.0+cu128),
   fallback = lw_clean_iopaint.py <slug> --region x0,y0,x1,y1 in the lw-clean venv. (6) LW-QA-SLIDER: new
   tools/lw_qa_slider.py + tests/test_lw_qa_slider.py (8 tests, RED collection error -> green): static page, one
   NEEDAUTH item, _<stage>initial vs _<stage>needauth in one box with a range divider, newest gate audit beside it;
   live run on a queued first-pass item wrote ops/runtime/review/qa_slider.html with both file URIs and G1 metrics
   (queue 132). 5-phase UI audit (subagent, before commit): 0 MUST-FIX; SHOULDs taken: header landmark,
   aria-valuetext, visible divider bar, overflow-wrap. Not taken: drag on image, verdict emphasis, inline aspect.
   One HOP 2 answer to MAIN.

354. DONE **2026-10-31 (responder: MAIN ORDER 2026-10-31-2200 FLEET-KIT v26 adopted; supersedes v25).**
   Inbox copy sha256 4e4084a6e3068108572ab638616153fb5daf625248a66034af88be421f104290 (re-hashed; == MAIN outbox
   copy, 12621 bytes). Kit vendored byte-for-byte (24 files + fleet_hook.sh), MANIFEST.json sha256
   45b5088e202a0c0c453fb1dc4ca8969783563d60d3b7b02e8d2c5c547fe4edae == section 1; FLEET-COMMON block re-embedded.
   .claude/settings.json: both PreToolUse hooks now `bash fleet_hook.sh <script>` with timeout 15, no `|| true`;
   `{}` piped into each: exit 0, empty stdout. Section 4 tests changed: tests/test_fleet_kit_v10_wiring.py,
   tests/test_fleet_kit_v12_race_guards.py (launcher form, timeout 15), tests/test_hook_interpreter_resolves.py
   (bash allowed, run-check is `echo`), tests/test_tracked_settings_is_safe.py (strip token before basename).
   KIT_VERSION pins 25 -> 26 (tests/test_fleet_kit_conformance.py, tests/test_headless_env.py,
   tests/test_promise_probe_fleet_kit.py, tools/lw_promise_probes.py). No LW lane loop running (nothing to restart).
   No run budget was hand-reset. One HOP 2 answer to MAIN.

353. DONE **2026-10-28 (Maint-KitRollout: fleet kit v25 LANE-CAP adopted).**
   MAIN ORDER 2026-10-27-2136 FLEET-KIT-v25 (HOP 1): verify_main True (inbox == MAIN committed outbox copy,
   sha256 ac203570c0b7...); bundle verified at KIT-COMMIT 7db5d9d (lw_inbox_responder.bundle_verified True).
   The working tree already held the v25 kit bytes from an earlier half-done rollout (claims: one DEAD owner,
   released; no live one); nothing re-copied. READ BACK: 23/23 kit files + MANIFEST.json (fa04c87c...) match
   section 1; conformance() == []; KIT_VERSION 25; FLEET-COMMON unchanged. Tree side (section 5): the loop
   driver follows fleet_lanes.load_config() - ops/loop/config.json lane_cap 3 -> null (live lane_cap_max),
   max_concurrent_lanes 3 -> removed from config.json / config.gate.json / config.p5.json and the
   loop_controller literal default `CFG.get("max_concurrent_lanes", 3)` -> executor_slot_count() (live
   governor_width, a tree number only asks for fewer and clamps); run_lane gets cap=None; the executor slot's
   repo key str(MAIN_ROOT) -> LANE_CODE so should_yield("LW") counts it; cycle_boundary_yield() calls
   fleet_lanes.should_yield("LW") at each cycle top and on True returns (ends the lane, never kills); an
   admission refusal exits like lanes_full (LaneRefused, retry next tick). Guard test
   tests/test_loop_lane_cap_v25.py (width 5 / cap 5 config reads 5, missing reads 3, no kill on yield).
   Section 4: tests/test_loop_lanes.py (lane_cap 4 clamps instead of raising; slot repo key); the
   pre-v25 config-agreement arms in tests/test_loop_concurrency.py now assert no LW config declares a
   ceiling, no literal default survives, and RC never declares more than the machine width.
   KIT_VERSION pins 24 -> 25 (tests/test_fleet_kit_conformance.py, tests/test_headless_env.py,
   tests/test_promise_probe_fleet_kit.py, tools/lw_promise_probes.py). Graceful restart: no LW lane loop
   running (nothing to restart; the next start loads v25). Gated suite (fleet_suite_gate, tools/lw_suite.py
   -q): 4210 passed 19 skipped + serial 183 passed 1 skipped, exit 0; drift_guard 0 breaches; ruff clean.

352. DONE **2026-10-26 (responder re-verify of MAIN ORDER 2026-10-26-0315 FLEET-KIT-v24; no residual work).**
   Inbox copy sha256 de515317931aad51e6d6f1d226c39a3ee14219601a32635f3c03a75d556e81bb (re-hashed; == MAIN outbox
   copy). Wiring already landed by b8a2057 / LEDGER 351 (KIT_VERSION pins 24, MANIFEST a41ff08e... == section 1).
   Gated suite re-run: exit 0, 4387 passed 19 skipped. CI on b8a2057 (ci + codeql): success. One HOP 2 answer sent.

351. DONE **2026-10-26 (Maint-KitRollout: fleet kit v24 adopted; supersedes v23).**
   MAIN ORDER 2026-10-26-0315 FLEET-KIT-v24 (HOP 1): verify_main True (inbox == MAIN committed outbox copy,
   sha256 de515317931a...); bundle verified at KIT-COMMIT 3ce416e (lw_inbox_responder.bundle_verified True).
   The working tree already held the v24 bytes from an earlier half-done rollout (all 24 files == bundle
   sha256, CLAUDE.md diff = item 19 only; claims: one DEAD owner, no live one; nothing re-copied). READ BACK:
   23/23 kit files + MANIFEST.json (a41ff08e...) match section 1; conformance() == []; KIT_VERSION 24;
   FLEET-COMMON block byte-exact (item 19 new). Section 4: no chart_order / item-18 / shell_targets / _lanes
   order asserts in tests/. Adoption fixes: KIT_VERSION pins 23 -> 24 (tests/test_fleet_kit_conformance.py,
   tests/test_headless_env.py, tests/test_promise_probe_fleet_kit.py, tools/lw_promise_probes.py);
   tests/test_no_absolute_machine_paths.py drops the ops/fleet_kit/ allowlist row (v24 KIT-SIDECAR-PATH: the
   kit has 0 drive-path lines, so the row was dead). reap dry-run: 0 removable, 0 kept, 0 listed. Gated suite
   (fleet_suite_gate, tools/lw_suite.py -q): 4204 passed 19 skipped + serial 183 passed 1 skipped; drift_guard
   0 breaches; ruff clean.

350. DONE **2026-10-26 (responder: MAIN ORDER 2026-10-26-0300 U5 - timing tests to fleet_test_guard.budget()).**
   MAIN provenance: verify_main True, inbox == MAIN outbox sha256 35783c7a4f0704781508ce84e5b140d22472ce184ac3b9bd09b93e8880217193
   (1061 bytes). tests/test_lw_facts_stdin_is_bounded.py (2 arms, elapsed < 3.0) and
   tests/test_slot_hold_is_bounded.py (1 arm, monotonic() - t0 < 30) now assert against
   fleet_test_guard.budget(3.0) / budget(30) (kit v16+ load-scaled); each file imports fleet_test_guard.
   Read back: grep of tests/ for an assert on elapsed/monotonic/perf_counter/time.time with a raw `<`
   bound outside budget() = 0 hits. Touched files: 44 passed, exit 0. Whole suite via fleet_suite_gate
   (timeout 1200 s): exit 0, 4387 passed, 19 skipped, 246 s; untracked/modified file count 2 -> 2.
   ruff clean. Reply: ANSWER note to MAIN (HOP 2, TERMINAL). FUTURE: a new wall-clock upper bound in
   tests/ goes through budget() from the start.

349. DONE **2026-10-25 (session 86 / responder 198 /done: 2045 suite-speed wrap).**
   491bb85 (LEDGER 348) pushed by the responder; CI read back: ci 40266567636 success, codeql 40266567605
   success. ANSWER 2026-10-25-2257-from-LW-ANSWER-to-MAIN-2045-suite-speed-done-491bb85-TERMINAL delivered,
   reached 1/1; outbound 3/12 today. Still unread in the inbox at wrap (not marked seen): MAIN 1926 FLEET-KIT
   v23 ORDER (work done, LEDGER 346), MAIN 1935 FIX gh-review pillow-13 (work done 8dfef45, LEDGER 347), two SS
   ANSWER notes (no reply) - carried as INBOX-MARK. CI-82 closed (prior push green; 491bb85 green).
   Worktree reap: 0 removed, 0 kept, 0 listed.

348. DONE **2026-10-25 (responder: MAIN ORDER 2026-10-25-2045 suite speed - veil fixture module-scoped, test httpd poll 0.05 s, -n 8, BLAS thread caps, torch test serial).**
   MAIN provenance: verify_main True, inbox == MAIN outbox sha256 d1e2037b1fa9dd581d47fbf6cf7967d82571ef1af349900b3e8c2c6c98f92b05
   (2155 bytes). (1) tests/test_lw_clean_overlay_veil.py: estimate_veil built once per module, deep copy per
   test (file 24.70 s -> 6.93 s). (2) every test serve_forever thread (7 files) gets poll_interval 0.05; the
   httpd + served_version + rundash_jobs trio 11.97 s -> 3.04 s; tools/lw_httpd.py production default left as is.
   (3) tools/lw_suite.py parallel pass -n auto -> -n 8 (RED first in test_pytest_parallel_config); CI keeps
   -n auto (small runners). Peak commit located with a temp psutil per-test sampler in a gated -n 8 run:
   test_lw_usm_halo_probe::test_worker_spandrel_branch_produces_both_variants (real torch + IJN child) 10605 MB
   tree peak on one worker, plus ~0.6-1.1 GB per worker of OpenBLAS per-thread buffers (import numpy 500 MB,
   scipy.ndimage 1010 MB private vs 18 / 46 MB at one thread). Fixes: that test marked serial; tests/conftest.py
   setdefaults OPENBLAS/OMP/MKL_NUM_THREADS=1 before any array import (tests/test_suite_thread_caps.py, RED
   first). Gate durations, same command: `python tools/lw_suite.py -q` hold 84.5 / 96.5 s, peak 15563 / 15629 MB
   -> 93.6 s, 9606 MB (exit 0; 4204 passed 19 skipped + serial 183 passed 1 skipped). `python -m pytest tests
   -q` hold 320.8 s, peak 11165 MB -> 289.6 s, 9718 MB (exit 0, 4387 passed, 19 skipped).

347. DONE **2026-10-25 (responder: MAIN FIX 2026-10-25-1935 gh-review - Pillow 13.0.0, Dependabot PRs #5 #6 re-applied as operator commits).**
   Inbox copy re-hashed: sha256 2b7ff2c8966a092dd50e341d56398e59a8c62df709d0633d33fe2d264d2b42d0, 2125 bytes;
   verify_main True (MAIN committed outbox copy). READ BEFORE: 82 open Dependabot alerts (gh api), PRs #5 #6 open.
   No private Pillow internals used (grep of `_save_netpbm`, `Image._`, `ImageFile._`, `GifImagePlugin`: 0 hits).
   PR #6 (head 539ab9b) applied with `git cherry-pick --no-commit`: setup-python v7.0.0 -> v7.1.0 (3 sites),
   codeql-action init/analyze v4.39.0 -> v4.39.1. PR #5 (head 9ef1ece) NOT taken byte-for-byte: its
   requirements files drop colorama (win32 marker) and list every pillow hash twice; both files regenerated
   locally with `uv pip compile ... --generate-hashes --upgrade-package pillow [--upgrade-package ruff]`
   instead. Pins: pillow 12.3.0 -> 13.0.0 (requirements.txt, requirements-cv.txt), ruff 0.17.1 -> 0.17.2
   (requirements.txt); colorama kept; 0 duplicate hashes. Gated suite (fleet_suite_gate, python -m pytest
   tests -q, local Pillow 13.0.0): exit 0, 4381 passed, 19 skipped. CV lane in a fresh venv installed
   `--require-hashes` from requirements-cv.txt (cv2 5.0.0, numpy 2.5.4, scipy 1.18.1, skimage 0.26.0,
   Pillow 13.0.0): exit 0, 18 passed. CLAUDE.md Session gains the MAIN-ordered rule: read the previous
   push's CI verdict before the next push.

346. DONE **2026-10-25 (responder re-verify of MAIN ORDER 2026-10-25-1926 FLEET-KIT-v23; no residual work).**
   Inbox copy re-hashed: sha256 e29369dc8aeee59db49c1481a5cfbe491268a2b6a66e0ca7c09221253da638ee, 13931 bytes
   (== MAIN outbox copy). READ BACK at HEAD 121eb25: MANIFEST.json sha256 f5d82861...ba527c == section 1;
   no v20/v22 pins left (KIT_VERSION 23 in tests and tools/lw_promise_probes.py); done.md carries the local
   render and the reap step; `fleet_done.py reap` dry-run 0 removable, 0 kept, 0 listed. Gated suite
   (fleet_suite_gate, python -m pytest tests -q): exit 0, 4381 passed, 19 skipped. The one ANSWER (HOP 2,
   TERMINAL) was already delivered 2026-10-25 2135 (moon_sync_outbox); no second note written (never answer
   twice).

345. DONE **2026-10-25 (Maint-KitRollout: fleet kit v23 adopted, cumulative v21+v22+v23; status board LOCAL ONLY).**
   MAIN ORDER 2026-10-25-1926 FLEET-KIT-v23 (HOP 1): verify_main True (MAIN committed outbox copy); bundle
   verified at KIT-COMMIT 03d1c08 (lw_inbox_responder.bundle_verified True). The working tree already held the
   v23 bytes from an earlier half-done rollout (all 24 files == bundle sha256, nothing re-copied). READ BACK:
   23/23 kit files + MANIFEST.json (f5d82861...) match section 1; conformance() == []; KIT_VERSION 23.
   Board push sites removed (v23 item 18): .claude/commands/done.md section 9 (Artifact / ArtifactData
   push -> `fleet_board.py render --final --session <n>`), tools/lw_checklist.py HOOK_RULE (`calls` -> `render`).
   ops/status_board.json left in place (only "code" is read); claude.ai board artifact NOT deleted (operator's
   call). v22 reap step added to done.md section 6; reap dry-run: 0 removable, 0 kept, 0 listed. Section 4
   tests: none of the listed board / route-bare / ls-remote shapes in tests/. Adoption fixes: KIT_VERSION pins
   20 -> 23 (tests/test_headless_env.py, tests/test_fleet_kit_conformance.py, tests/test_promise_probe_fleet_kit.py,
   tools/lw_promise_probes.py); tests/test_no_console_flash.py asserts the CREATE_NO_WINDOW bit (v21 ORs
   CREATE_SUSPENDED in); tests/test_no_absolute_machine_paths.py allowlists ops/fleet_kit/ (vendored, never
   edited; v22 SIDECAR_DEFAULT is a drive path in a PUBLIC repo - reported to MAIN). Gated suite
   (fleet_suite_gate, tools/lw_suite.py): 4199 passed 19 skipped + serial 182 passed 1 skipped; drift_guard 0
   breaches; ruff clean.

344. DONE **2026-10-25 (session 85: wallpaper-repeat report investigated, no bug found; status/reshuffle ~ fix c32c678).**
   Operator reported the desktop wallpaper switcher repeating a small pool. READ BACK: LW-Wallpaper task runs
   tools/lw_wallpaper_rotate.py tick every 3 min over the persisted shuffle deck ops/runtime/wallpaper_deck.json;
   555 unique images in ~/Pictures, cycle 116. No repeat bug found. Operator then named ref_181f as repeated ~5
   images earlier: it was set once this cycle at 21:13:58Z (deck pos 193; cycle began 11:34:57Z); Windows
   BackgroundHistoryPath0-4 match deck 193-197; no other wallpaper setter; no duplicate files in Pictures. Likely
   explanation: the Settings recent-wallpaper strip (last 5) or look-alike images (Ahri at deck pos 187/191). NOT
   proven: the run log records no filename. Shipped c32c678: `status` / `reshuffle` now expand ~ via a shared
   _source_dir() (tick already did); 75 tests passed. Progress wallpaper-shuffle.json done.
   OPEN: WALLPAPER-PICKLOG (promised to the operator, not yet dispatched) - log each tick's chosen filename to the
   run log so a reported repeat can be proven or disproven; then ask the operator for the next repeat name + time.
   CI-82 read: session 84 wrap push ci 40046816812 success (200368d); 90ba4b3 push ci 40131266917 success.
   Hand-off fix: checklist IDs are capped at 16 chars (tools/lw_checklist.py:41, fleet_checklist._ID), so
   WALLPAPER-PICKLOG (17) and the carried REPO-REVIEW-DRIVER (18) were silently dropped by the SessionStart
   printer; renamed WP-PICKLOG / REVIEW-DRIVER (long name kept in the task text); printer read back 11 tasks + /done.
   CI fix: ci 40236189169 (push ba1197a) check FAILED 2 tests - c32c678's tests spelled source_dir `%VAR%`, which
   posixpath.expandvars ignores on the Linux runner (Windows-only bind passed). Tests now use `${VAR}` (both
   ntpath and posixpath expand it); 43 passed locally; production code unchanged.

343. DONE **2026-10-24 (SS FIX 2026-10-24-1525 to MAIN-KIT measured in LW by the inbox responder, run 195; docs-only).**
   READ BACK: SS note (not MAIN, no MAIN authority claimed; no verify_main check). A1: fleet_test_guard.py:64
   WATCH holds ops/loop/control; IGNORE (:66-70, 11 globs) matches 0 of 2 board files (board/status.json,
   board/state.json) under its own fnmatchcase rule (:86); fleet_board.py:51/:284/:285 writes them; LW
   tests/conftest.py:79-81 extra_ignore holds only headless_budget.json*; 0 LW tests reference fleet_board, so
   the exposure is an interactive board push overlapping a suite (same as SS). No kit file or conftest edited.
   A2: fleet_suite_gate run pytest tests -q exit 0, 4378 passed, 19 skipped, 0 failed (305.55s).
   A5: ANSWER 2026-10-24-1545-from-LW-ANSWER-to-MAIN-KIT-SS-1525-board-files-unignored-in-LW-too-TERMINAL
   (HOP: 2), MAIN inbox copy re-hashed equal (sha256 249c382b77e3..., 2380 bytes): reached 1/1; OutboundCap 1/12.
   SS 2026-10-24-1243 INFORMATION TERMINAL (seeded board urls "artifact not found"): read, no reply.
   FUTURE: when a kit version adds the two paths to IGNORE, vendor it (A3/A4); no LW-local workaround meanwhile.

342. DONE **2026-10-23 (session 84: CI-81 green, MAIN 1300 ANSWER sent, 0730 INFORMATION acked, LW status board re-created; docs-only).**
   READ BACK: CI-81 - ci 39211691501 (push, 9fad27d = origin main tip) success; scheduled ci 39958975756 success.
   Inbox: 2 unread, both verify_main True. MAIN 2026-10-19-0730 SS-QUIET-BENCH INFORMATION TERMINAL - mechanical
   ack, this line, no reply. MAIN 2026-10-21-1300 FIX - work already done by the responder child (LEDGER 341;
   the child timed out at 1800s before commit + ANSWER); session 84 re-read .claude/settings.local.json (7 keys
   absent, permissions.defaultMode bypassPermissions, ASCII, no CR; settings.json has env + hooks only), committed
   the leftovers f874787, sent ANSWER 2026-10-23-1945 (HOP: 2, TERMINAL), destination copy re-hashed: reached 1/1;
   OutboundCap recorded. lw_facts --mark-inbox-seen: 637 seen.
   BOARD-URL: Artifact list showed no LW board (old url gone); re-created from the Dashboard type as
   https://claude.ai/artifact/4PeonWKZxgrX92CheHAx4D (dash/meta, datasets/board -> status.json blob,
   files/index.html from fleet_board.py page), ops/status_board.json url + dataset_version 1.
   Read-only watches: R4 tally refused (operator has not finished, no votes.json); hand captures newest
   2026-08-22 (R5c blocked); fleet_watch swap tripwire 3 passed (green); no new MAIN/sibling note for
   KIT-PUBLIC-GIT / GATE-FIFO-WATCH / RETIRE-JUNCTION. LW-Cutover-E Disabled is expected (LEDGER 287/1056 note:
   stays disabled until the junction is retired). 0.Originals 2 loose files unchanged (operator's call).

