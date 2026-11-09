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

367. DONE **2026-11-08 (responder: MAIN ORDER 2026-11-08-1200 model-and-effort-fit-the-task).**
   Inbox copy re-hashed: sha256 bc9731aecac1365118f2a3b704df4fb416c163fe19fbc4dafe5d4ca63df219dd, 2178 bytes;
   verify_main True (MAIN committed outbox copy). Memory: no prior memory covered model/effort (grep of the
   memory dir: 0 hits); feedback_model_and_effort_fit_the_task.md written byte-for-byte from the note's
   File text block (1036 bytes, sha256 286cd894...ffacd) and the ordered MEMORY.md index line appended
   (operator memory dir, untracked). Applied: the two LW spawns that left effort to a default now set it
   deliberately - loop executor argv `--effort` from `executor_effort` (default high, code-writing cycle),
   loop oracle spawn `effort=` from `oracle_effort` (default medium, read-only judgement); both keys added
   to ops/loop/config.json. Responder and CI-watchdog already pass explicit effort. TDD: 3 new tests failed
   first, then pass. Gated suite: exit 0, 4497 passed, 19 skipped. No reply note (the ORDER says TERMINAL).
   CI-RED-PATHSEP: the push run on 35701f3 (42155626178) and nightlies 42245905502 / 42383018434 / 42491770307
   read failure: tests/test_headless_env_path.py PSF constant carried "C:", which splits on Linux's ":" pathsep
   into a stray "C" entry. Test-only fix (no drive colon off Windows); that file: 6 passed locally.

366. DONE **2026-11-05 (session 93 wrap: DEPENDABOT-PR7, CI-91, KIT-ROLLOUT-READ, RESPONDER-STATE, KIT-SCAN-STALE closed; docs-only).**
   DEPENDABOT-PR7: 93189fe re-applies pytest 9.2.0 + ruff 0.17.3 as an operator commit (path B); PR 7 read back CLOSED;
   suite 4461 passed 20 skipped. CI-91: run 41704024983 on c728dc9 read success. KIT-ROLLOUT-READ: headless_usage.jsonl
   line 64 is the `kit-rollout v28` row, 1020.3 s / 2.716 USD (v27 1647.4 s / 4.205 USD) - LW-3 done-when met.
   RESPONDER-STATE: LW-InboxResponder read Enabled/Running every 5 min, no HALT file; the session-91 Disabled read was
   MAIN's 2026-11-01 quiesce, re-enabled by MAIN Restore-Quiesce 2026-11-02 22:07:49 - CLAUDE.md ENABLED stands.
   KIT-SCAN-STALE: 571 pre-ledger notes baselined as SKIP via fleet_inbox mark_seen (left 0, pending 0); the stray SS
   FIX-to-MAIN pending row closed via mark_work_done. PY-ON-PATH + SS-MAIL: LEDGER 365 (b7ce5df). Inbox: 3 unread read,
   none needs LW action (v28 closed in LEDGER 361/362; SS 1324 to MAIN, LEDGER 363; bundle 25 files byte-match
   ops/fleet_kit); lw_facts --mark-inbox-seen run at /done (667 marked). OUTBOUND: INFORMATION
   2026-11-05-2104-from-LW-INFORMATION-to-MAIN-classify-addressee-child-env-PATH-SS-deliver-fanout.md (sha256 485dd5c0...)
   reached 1/1; LW has no SS carrier, so the SS deliver fan-out item is relayed via MAIN. Unchanged: GATE-FIFO-WATCH (no
   reply), RETIRE-JUNCTION (3/6), WATCH-SWAP tripwire green. /done pre-flight: ruff clean, drift_guard 0 breaches,
   pytest --lf via fleet_suite_gate 4494 passed 19 skipped exit 0.

365. DONE **2026-11-05 (PY-ON-PATH child PATH sanitizer + launch_loop direct launch; SS-MAIL misaddressed-note skip).**
   PY-ON-PATH ROOT CAUSE (investigation this session): Python Manager registers App Paths python.exe /
   pythonw.exe / py.exe (HKCU+HKLM) with Path = its WindowsApps PythonSoftwareFoundation.PythonManager_* dir;
   every ShellExecute launch of a python.exe prepends it to the child PATH, so bare `python` in descendants
   resolved to pythoncore-3.14-64 without pytest. kit child_env (fleet_headless.py:510) copies os.environ as-is.
   FIX 1: tools/lw_headless_env.py sane_path (:153) drops every PATH entry containing
   `\windowsapps\pythonsoftwarefoundation.` (case-insensitive), puts dirname(sys.executable) + its Scripts dir
   (Windows) first, dedupes, keeps the key spelling; child_env (:178) and spawn (:259, via the _sane_run runner
   wrapper :185 - kit.spawn builds its env from os.environ with no parent seam) both apply it; os.environ is
   never mutated. FIX 2: ops/loop/launch_loop.ps1 Start-Direct (:30) = ProcessStartInfo UseShellExecute
   $false + CreateNoWindow $true, replacing both `Start-Process $py` calls (:57 dry stub, :124 controller).
   powershell.exe 5.1 ParseFile: 0 errors; smoke launch through Start-Direct: child PATH had no PSF entry.
   SS-MAIL: SS's responder copies every note to every participant. tools/lw_inbox_responder.py decide (:476)
   now returns SKIP reason `misaddressed` (why `misaddressed: addressed to <CODES> ...`) when addressees()
   (:511) - the fleet-code run anchored right after `-from-<SNDR>-[<CLASS-WORDS>-]to-` (:507) - names neither
   LW nor ALL and is not just the sender (self-correction broadcast); prose `...-owed-to-LL-...` never counts,
   `-to-ALL-SIX-`/`-to-ALL-SEVEN-` parse as ALL, an unknown code ends the run (fail open). Kit SKIP reasons
   (self/terminal) still win. Dry scan of the live inbox (read-only): 14 notes would be misaddressed, all
   addressed to MAIN/RC/LL/RSC, 0 to LW or ALL.
   TDD: tests/test_headless_env_path.py (6), tests/test_inbox_responder_misaddressed.py (23),
   tests/test_launch_loop_direct_launch.py (4) - RED first (18 + 2 failed), then green.
   READ BACK: ruff clean; fleet_suite_gate run lw_suite.py -q exit 0: parallel 4311 passed 19 skipped,
   serial 183 passed 1 skipped (4494 passed, 20 skipped, 0 failed).

364. DONE **2026-11-05 (operator ask: intake + first pass + wallpaper rotation; docs-only, data outside git).**
   INTAKE: 19 loose files in `images/0.Originals`; `lw_pipeline intake --all --dry-run` then execute: 17 intaken,
   2 refused as hash-equal duplicates of existing slugs (lux-coven-crimson-enchantment dms9tlg-pre,
   mel-coven dmv2qac-pre; left in 0.Originals, deletion is the operator's call). Recovery: campaign run after
   intake from verbatim backups staged in a scratch dir (memory recipe); Tier 1 resolved all 17 deviations
   alive, annotated 17, but its fetch reported `not_configured` - `%APPDATA%/gallery-dl/config.json` is ABSENT
   on this box (the DA client-id config the campaign reads is gone). Fetched directly with the documented
   quota-free flags (original=false intermediary=true quality=100): 17 of 17 landed, verified on disk by
   recursive file count; 9 -pre slugs gained pixels (1163-1194w -> 1280w, heimerdinger 1192x670 -> 1600x900),
   8 fullviews same dims at 4-8x the bytes. Fetch sha256 + dims annotated per manifest (`recovery_fetch`);
   `data/recovery/matches.json` merged back to 41 records (the campaign overwrites it).
   FIRST PASS: `lw_first_pass.py --batch` (explicit 17-slug list, dry-run first; never --all-scratch):
   17 PASS / 0 flag / 0 fail / 0 held, V3 DAT2 upscale-4x, 8 auto-cropped to 16:9 (crop_ok). All at
   _firstneedauth, NONE approved. FIRST_SCRATCH now 148 needauth + 10 pre-existing EDITING left untouched:
   7 HELD aspect_crop_heavy (alphacoders 1109171/1125535/663779/706844, 3 pintrest 236px thumbs) need an
   operator `--crop-overrides` or drop; 3 failed G1 lap_ratio 0.91-0.93 < 1.0 on undersized sources
   (1000040081 375w-2x, alphacoders 420408, lolwallpapers 13182) - unfixable without a better source.
   ROTATION: LW-Wallpaper reads files flat under ~/Pictures (`tools/lw_wallpaper_config.json`) and splices new
   files into the owed tail of the current cycle; no code change. 0 of the 148 needauth slugs had a Pictures
   entry. pHash+dHash vs the 555 Pictures files: 2 are the same art as an existing `_cleaninitial`
   (alphacoders 1011889 = djy560k Katarina dp8/dd5; alphacoders 1078487 = thousand-pierced-bear Volibear dp4/dd11),
   confirmed by eye, NOT delivered; 1 review-band hit (hdqwalls caitlyn vs vayne2, 14/14) is different art,
   delivered. 146 copied as `<slug>_firstneedauth.png`, sha256 equal 146/146. READ BACK after the next
   scheduled tick: status present 555 -> 701, deck 701 entries (146 `_firstneedauth`), cycle 125 position
   547/701, last_shown a newly delivered file. FUTURE: when one of these slugs advances, retire its
   `_firstneedauth` twin from Pictures (one entry per slug, LEDGER 121); restore the gallery-dl DA config.

363. DONE **2026-11-03 (responder-authored: SS FIX to MAIN 2026-11-03-1324 kit checklist caps; mechanical ack, no reply; docs-only).**
   Note 2026-11-03-1324-from-SS-FIX-to-MAIN-KIT-checklist-caps-cut-silently-13a-departure-board-displaced-row-ONE-ANSWER.md,
   sha256 7e6976a9533f71f6a9edc47f28fa775956c0df7e0c2500e94e84b08891f34810, 2920 bytes, HOP: 1. Class FIX, sender SS,
   addressee MAIN only (kit defect: ROWS_MAX/CHECKLIST_MAX/[:120] silent cuts, an item 13a ruling, fleet_board displaced row
   marked done); not from MAIN, so no verify_main match applies. Asks nothing of LW; "ONE ANSWER" is MAIN's kit version note.
   No A-action, no kit file touched, no reply (LW never answers for MAIN). SS-MAIL observation: one more SS note addressed
   to MAIN landed in LW's inbox (count 6 since the session-90 tally of 5). FUTURE: vendor the kit version that fixes it (A3/A4).

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

