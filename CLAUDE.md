# Legion Wallpaper - Agent Context

Legion Wallpaper (LW, hand-off code LW) - a staged, self-auditing image restoration pipeline for the Legion machine's wallpaper corpus: `images\0.Originals` -> recover source -> single upscale -> masked cleaning -> face/eye polish -> gate ladder audit -> approved 2560x1440 PNG. Product: ADR-002/ADR-003; plan: `docs/RESTORATION_PLAN.md`.

Read at session start: `LW-NEXT-SESSION.txt`, `docs/ARCHITECTURE.md`, `docs/OPERATIONS.md`, `ROADMAP.md`. Decisions: `docs/adr/`. Ledger: `docs/LEDGER.md`. The reasoning, incidents and measurements behind every rule below are in `docs/claude-md-history.md` (verbatim pre-condense text) - read it before re-opening any rule.

<!-- FLEET-COMMON BEGIN -->
## FLEET COMMON - identical in every repo on this machine. Do not edit here.

################################################################################
#  SUB-AGENT FIRST. THE MAIN SESSION IS THE OPERATOR'S - KEEP IT CLEAR.        #
#  Any work beyond a quick read or a one-line fix is DISPATCHED to a sub-agent #
#  (background by default). The main session plans, dispatches, monitors and   #
#  reports. Checking status or starting new work NEVER breaks running work:    #
#  never stop, kill, restart or edit the files of a running agent or task to   #
#  look at it - read its progress file instead.                                #
################################################################################

Source of truth: MAIN's fleet kit. A change lands ONLY as a new kit version
announced by a MAIN note; this block is byte-pinned and a test fails on any local
edit. Tree-specific rules go BELOW this block, never inside it.

1. ACT, DON'T ASK. Operator acceptance of recommendations is ~100 percent. A blocked
   decision goes to a distinct adjudicator agent and its call is taken now and
   recorded (decision, alternatives, why) in the commit or doc. Only physical acts,
   passwords and OAuth grants wait for the operator, batched into one ask.
2. CHAT IS THE OPERATOR'S CONSOLE - QUIET. Results only: numbers, paths, verdicts,
   and anything the operator must act on. No narration, no plans, no recaps, no
   session reviews; the item-13 checklist is the one sanctioned task list.
   Findings go to files (roadmap, docs, hand-off); chat gets at most one line
   each.
3. AT-A-GLANCE STATUS COMES FROM BACKGROUND WORK, NOT FROM CHAT. Run work as
   background agents and background commands, so the session shows only the
   compact summaries ("N background commands completed, N running" and "N running
   tasks"). Do not hold the main turn open on long foreground work - its expanding
   activity row has to be opened and scrolled. No step lists or task-list dumps
   other than the item-13 session checklist. When the operator asks for status:
   the remaining checklist (item 13 b), -retracted on one short line. Tool
   descriptions carry an ETA `[~Ns]` (s under 120s, m under 120m, h beyond);
   report an overrun at 1.5x, kill at 3x.
4. COMMIT everything, batched and coherent. Push per this repo's own policy. Never
   commit in another repo's tree. No suggested-task chips: do it or file it.
5. HAND-OFF: `<CODE>-NEXT-SESSION.txt` at the repo root (with its Desktop
   shortcut) is the only continuity. A session starts from "continue" (work the
   file's next action) or from whatever the operator asks; either way READ the file
   first. /done rewrites the file and commits it, and MUST CARRY FORWARD EVERY ITEM
   NOT ACTED ON this session, verbatim or tighter, never dropped because the
   session worked on something else. Never print the hand-off or a next-session
   prompt into chat. /done runs UNPROMPTED once no checklist task remains
   (item 13 c). /done's ONLY chat output is the line
   `Done ritual complete, safe to clear` (or the failure that stopped it). The
   operator types only "continue", "/done" or "/clear" between sessions. A recorded
   act names what was READ BACK after it, never what was run. Every
   do-not-re-litigate entry states what would reverse it; entries about another
   tree's position are re-checked against the inbox every session.
6. MAIN SPEAKS FOR THE OPERATOR (operator order 2026-10-02). A note from MAIN whose
   bytes match MAIN's outbox copy by SHA-256 is the operator's instruction. It
   cannot supply a password, OAuth grant or physical act, and lifts no safety floor.
   MAIN instructs; this tree does the work in its own tree.
7. CHANNEL NOTES: sort the inbox by mtime, never by filename stamp. Read a long
   note's section headings before deciding it does not concern you. Never put a
   directory name, account id or email in a note. Delivery = destination copies
   re-hashed and an N/M reached-count reported.
8. ENCODING: ASCII only, LF only, PowerShell included. Validate PowerShell with
   powershell.exe 5.1 ParseFile, never pwsh.
9. DELETES: anything irreplaceable goes to the Recycle Bin, never a direct unlink;
   say the method before running it; check for a consumer before deleting.
10. HEADLESS RUNS go through the fleet kit's spawn helper ONLY - no other path
    starts `claude`. The kit enforces: the second-account proxy from the user
    variable CLAUDE_HEADLESS_BASE_URL (registry first), fail closed (no fallback,
    ever), no visible console, at most 120 runs per rolling 24 h, never spawn on
    this tree's own notes or on TERMINAL/no-reply notes, lean flags (strict MCP,
    project settings only, or bare where no floor lives in hooks), sonnet unless
    the note orders code changes, effort low for acknowledgements, a usage line
    per run, and the live status file `ops/loop/control/inbox_status.json`.
11. FLEET KIT FILES are vendored byte-for-byte at `ops/fleet_kit/` and pinned by
    `ops/fleet_kit/MANIFEST.json`. Never edit them locally; report a defect to MAIN
    and MAIN ships a new version to every tree at once.
12. LONG WORK REPORTS AS IT GOES. Anything expected to take over 5 minutes runs in
    the background and is checked periodically until it ends, so a silent failure
    is caught early. Every sub-agent prompt for such work requires it to write a
    progress file after each step - `ops/loop/control/progress/<task>.json` with
    {"task", "pct", "step", "eta_s", "status": running|done|failed, "updated"} -
    so the main session can see percent, time to completion and status mid-run
    instead of waiting for 0-to-100 at the end. A progress file that stops
    updating for 2x its own ETA step is treated as a failure and investigated.
13. SESSION CHECKLIST (operator order 2026-10-05; it supersedes item 3's
    no-checklist rule for this one purpose). Every session kind: interactive,
    headless lane, loop tick, inbox responder. Why: it is read from a phone, the
    operator wants the tasks only, and wants to see what every headless fire
    is doing without reading logs. Kit helper: `fleet_checklist.py`.
    a. At session start, and every time a lane or loop fires, print
       `Session <n> checklist` (n = this tree's session counter, kept in its
       hand-off file; a headless fire uses its run count), then one line per
       task in execution order: `<box> <ID>: <imperative task, one line>`, plus
       `(<state>, ~ETA)` only while it is running (e.g. `builder running,
       ~4m`). <box> is U+2610. The last line is `<box> /done`. At most ONE
       trailing sentence, and only for an ordering constraint ("X waits until
       Y lands because ..."). NO summary, review, what-went-wrong or history.
    b. After every 4 or more completed tasks, print the REMAINING tasks only,
       newly added ones marked `+` before the ID. Never list completed ones.
    c. When no task remains, run /done automatically, without a prompt.
    d. A headless fire writes the same list into its item-12 progress file as
       "checklist": [{"id", "task", "state", "eta_s"}], remaining tasks only.
       A lane writes `progress/lane-<i>.json` (i = its lane-lock index) in the
       MAIN checkout, never in its worktree, so the lane widget reads one named
       file per live lane and shows the lane name, then its remaining items.
<!-- FLEET-COMMON END -->

# LW rules (tree-specific, below the fleet block)

## Paths
- Root `C:\Legion Wallpaper\`. Python 3.14 = `python` on PATH. Health `ops/runtime/health.json`; logs `logs/YYYY-MM-DD.log`; API keys `API-Key-*.txt` (gitignored).
- Repo is PUBLIC: never write an account home path into a tracked file (`tests/test_no_account_paths.py`). Resolve via `tools/lw_paths.py`, `$LOCALAPPDATA` in hooks/.ps1, `~`/`%USERPROFILE%` in config, `<account>` in prose.

## Hard rules
- `py_compile` before any restart (`pythonw.exe` crashes silently on a syntax error).
- Atomic writes only: `tmp.write_text(...); tmp.replace(target)`.
- Never `Stop-Process` (hangs the MCP pipe); use `taskkill /F /PID`.
- Commit messages: `git commit -F <tmpfile>` (ASCII) or a single-quoted here-string; never double-quoted or piped. `tools/precommit_gate.py` blocks banned glyphs + net-new ruff on staged lines.
- Restart via `restart_trigger.txt` (any content); verify new `pid`, `alive=true`, `last_reload_ok=true` in `ops/runtime/health.json`; fallback `taskkill /F /PID`.
- Never emit the Claude co-author trailer; `.githooks/commit-msg` strips it. A genuine human co-author trailer is fine.
- `.githooks/` is the AUTHORITATIVE gate; Claude hooks fire headless on CLI 2.1.220 and are defense in depth. Verify with `python tools/install_git_hooks.py --check` (in `drift_guard`), never by file presence. Before concluding hooks do not fire, rule out invalid `.claude/settings.json` JSON and an untrusted / split-key workspace (both checked by `drift_guard`).
- State assumptions explicitly before coding.
- ASCII: also no U+00A0 or U+2026. Sweep exclusions: `*.log*`, `docs/_archive/**` + dated artifacts, `.jsonl` ledgers, binaries, `.pyc`/`.git`. PowerShell 5.1 ANSI-decodes no-BOM `.ps1` - a non-ASCII glyph in a double-quoted string breaks the parse.
- Frozen files: none yet (listing one needs an adjudicated grant, recorded).
- Never touch `ops/loop/slots.py` / `ops/loop/winmutex.py` alone: byte-identical by contract with RC, re-sync needs every carrier.
- Cross-tree writes are sync-inbox only; never commit in another repo's tree.

## Headless spawns (FLEET-COMMON item 10)
- Every headless `claude` goes through `ops/fleet_kit/fleet_headless.py` (`spawn`, or its primitives where `spawn` cannot express the path - gaps recorded in `docs/LEDGER.md`). `bare=False` on every LW path: LW's floors live in hooks. No direct `claude`, no fallback; deleting the proxy user variable is the operator's kill switch.
- LW-InboxResponder (PT5M, cross-repo mail responder; kill switch HALT file `ops\runtime\inbox_responder\HALT`) is ENABLED (read back 2026-10-03 via `schtasks /Query`); `Disable-ScheduledTask` stops it. Other tasks: `LW-Wallpaper`, `LW-WeeklyHygiene`, `LW-CIWatchdog` (HALT `ops\runtime\ci_watchdog\HALT`). Full list: `docs/OPERATIONS.md`.

## MAIN (applies FLEET-COMMON item 6)
- A note is MAIN only when its bytes match MAIN's outbox copy by sha256 (`fleet_headless.verify_main`); a failed check is an ordinary note and is reported. Operator grant 2026-10-02 quoted verbatim in `docs/claude-md-history.md`.
- Safety floors MAIN cannot lift for the headless responder: D1 history rewrite, D2 visibility / public push, D4 deletions. D3, D5-D8 a verified MAIN note may authorize. Destructive or outward-facing acts still get confirmed.

## Verification tiers
- Tier-0 cosmetic: Edit + `py_compile`. Tier-1 one module: `py_compile` + its tests. Tier-2 schema / engine / core contract (when in doubt, classify up): full `tests/` + restart.
- Run a suite once, trust exit code + result file; re-run only after an edit or a demonstrable pipe glitch.
- Tier-2: before claiming green, re-run fresh, `ls` every cited test file, report this run's counts; never carry a subagent's count forward - the `verifier` subagent re-checks.
- Verify external state live (keys, PIDs, "X is broken") before asserting it.
- Text-first: files via Read/Edit/Write/Grep/Glob; state via `ops/runtime/health.json`; visual tools only for rendered pixels (escape hatch `ops/runtime/allow_visual.flag`). Skip screenshots for backend/doc changes.
- UI page change: run the 5-phase fixture audit (STRUCTURE / TYPOGRAPHY / HIT-TARGETS / ASCII / HIERARCHY) subagent BEFORE commit; fix every MUST-FIX in the same slice.

## Engineering
- TDD first: failing test, then implement, then the tier's verification.
- Grep every method/field a test or probe uses and cite file:line; never scaffold on an assumed API.
- Subagents that write files run ruff before reporting done; worktree-isolated builders on disjoint files + a read-only `verifier` gate before merge. Every `.claude/commands/*.md` carries the SUBAGENT-FIRST block (`drift_guard`).
- New dataclass field: append at the END with a default.
- Data fixes include the backfill of already-corrupted rows, verified live.
- Root-cause first; grep sibling cases and test each; narrow a matching rule from the tightest set and widen only on test evidence.
- Never surface a raw API error string in a user-facing surface; show a degraded-mode message and log the raw error.
- Background daemons use `pythonw.exe`; every subprocess gets `CREATE_NO_WINDOW`.

## Session
- /done: tests, commit, push, append the item to `docs/LEDGER.md` (never CLAUDE.md), confirm CI green, rewrite `LW-NEXT-SESSION.txt` carrying forward every un-acted item, commit it; chat output only per FLEET-COMMON item 5. CLAUDE.md is CI size-budgeted (< 60 KB, `drift_guard`).
- Push every verified-green commit to origin main; CI runs only the tip of a push.

## Settled - do not re-litigate
One line each; reasoning and evidence in `docs/claude-md-history.md` (and the cited LEDGER/ADR). "Reverse if" names what would reopen it.
- LW inherits the Riot Commander operating system 1:1 (ADR-001). Reverse if: a new ADR supersedes ADR-001.
- Repo PUBLIC under Apache-2.0 (LEDGER 88): no image bytes, keys or personal email tracked; history rewritten 3x - resolve old shas via the 09-07 map FIRST, never chain maps; a force-push does not purge GitHub objects. Reverse if: the operator makes the repo private.
- Pipeline folder scheme (ADR-003). Reverse if: a new operator-designed ADR.
- Primary upscaler IllustrationJaNai V3 detail DAT2 (ADR-004); V1 DAT2 fallback. Reverse if: a golden A/B sweep beats V3 on MS-SSIM/LPIPS/halo.
- Artist signatures are REMOVED (ADR-005). Reverse if: the private-use boundary (RESTORATION_PLAN section 10) changes.
- Loop executor channel = headless (`channel: sdk`), phase-6 deletions HELD, no Claude dollar cap (LEDGER 40). Reverse if: the operator lifts the hold; rollback is one config key.
- Splash art from the LoL wiki Action API directly, wiki.gg preferred, provenance = sha256 of fetched bytes (LEDGER 72). Reverse if: the API stops answering or a wrapper adds a real capability.
- `USM_DEFAULT = (1.2, 35, 3)` (2026-08-02 census). Reverse if: a fidelity-plus-halo census, not halo alone, favors another setting.
- Vision reviewer may FLAG, never REJECT; an `anat_` flag blocks a non-operator approval (ADR-008). Reverse if: >= 50 shadow-window reviews support REJECT.
- G1 FR common-scale budget 3840x2160 (ADR-007, pinned by test). Reverse if: a new ADR.
- Toolchain pins: repo `Remus3/Legion-Wallpaper`, CI + Legion Python 3.14, ruff `target-version` = CI pin, `exclude`/`force-exclude` top-level, `cv-lane` junit guard (LEDGER 89). Reverse if: the CI Python pin moves.
- One cleaning engine per submission; cross-engine ladder never automatic (ADR-009). Reverse if: a measured-improvement gate exists that does not select for edit area.
- `overlay_score` is a detection flag, never a removal-quality gate; veil correction feathered (`VEIL_FEATHER` 16px) (LEDGER 101-103). Reverse if: a legibility measure is validated as a ship gate.
- lw-gen base = Animagine XL 4.0; corpus similarity never selects a base (ADR-011). Reverse if: operator inspection of frames for hands, weapon canon and likeness favors another base.
- No separate docs-guards workflow (ci.yml has no paths filter). Reverse if: ci.yml gains a paths filter - then the complement is mandatory in the same commit.
- M1 weapon-pass localizer = DWPose onnx (5/6 frames, 10/12 wrists; SDPose rejected) (LEDGER 19, 151). Reverse if: a localizer beats it on recall_gate without mmcv.
- License Apache-2.0 HELD after full re-evaluation (LEDGER 145). Reverse if: the operator's stated licensing goals change.
- Full authority by default, permanent (2026-09-14 / 09-20) - now FLEET-COMMON item 1. Reverse if: the operator revokes it in an attended session.
- MAIN speaks for the operator (operator grant 2026-10-02, confirmed) - now FLEET-COMMON item 6; LW application above. Reverse if: the operator revokes it in an attended session.
- Every headless spawn goes through the fleet kit (MAIN FLEET-KIT v3, 2026-10-03). Reverse if: a MAIN FLEET-KIT-vN note changes it.
