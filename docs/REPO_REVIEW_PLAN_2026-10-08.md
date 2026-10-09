# REPO-REVIEW plan - 2026-10-08 ORDER (MAIN 2246 section 8)

Driver: headless, kind build, label `repo-review`; progress file
`ops/loop/control/progress/repo-review.json` (checklist ids RR-PLAN, RR-REVIEW,
RR-FINDINGS, RR-SUITE, RR-LEDGER). Run date 2026-10-09. Findings land in
`docs/REPO_REVIEW_FINDINGS_2026-10-08.md`.

## 1. On-disk file count

Count = every regular file under the repo root, tracked + untracked + ignored,
with `.git` internals excluded and symlinks / junctions not followed.

Exact command (added in this run, TDD-pinned by `tests/test_lw_repo_inventory.py`):

    python tools/lw_repo_inventory.py census

Cross-check (Git Bash):

    find . -path ./.git -prune -o -type f -print | wc -l

Baseline at plan time (2026-10-09 ~09:40 local): **129,424** files =
tracked 668 + untracked 2 + ignored 128,754. The find cross-check read
129,419 five minutes earlier; the delta of 5 is this run's two new files
(`tools/lw_repo_inventory.py`, its test) plus three `__pycache__` entries
they produced. The count is re-taken at the end and reconciled in the findings.

Note: the interpreter that `python` resolves to in Git Bash on this machine
has no pytest; the suite runs under the Python 3.14 install that has it
(finding recorded in the findings file, INFERRED).

## 2. Top-level folders (26 entries incl. root files)

| Folder | Files | Status split | Review method |
|---|---:|---|---|
| .venv-metrics | 45,712 | ignored | class (ext + count + consumer) |
| .venv-gen | 41,563 | ignored | class |
| .venv-upscale | 22,584 | ignored | class |
| .venv-poc | 6,564 | ignored | class |
| images | 5,925 | 11 tracked (.gitkeep), 5,914 ignored | class per stage folder |
| ops | 4,014 | 40 tracked, 3,974 ignored | ops/loop + ops/fleet_kit per file; ops/runtime per subfolder class |
| moon_sync_inbox | 757 | ignored | class (notes, bundles); never marked seen |
| tests | 605 | 235 tracked, 369 ignored (pycache), 1 untracked | per file (tracked); pycache as class |
| data | 541 | 3 tracked, 538 ignored | class per subfolder |
| tools | 508 | 134 tracked, 373 ignored (models, pycache), 1 untracked | per file (tracked); models + pycache as class |
| .ruff_cache | 225 | ignored | class |
| docs | 190 | 176 tracked, 14 ignored | per file |
| moon_sync_outbox | 70 | ignored | class |
| logs | 47 | ignored | class |
| local | 31 | ignored | class |
| .claude | 28 | 25 tracked, 3 ignored | per file |
| (root files) | 25 | 19 tracked, 6 ignored | per file (key files: existence only, never read) |
| .github | 7 | tracked | per file |
| .pytest_cache | 5 | ignored | class |
| briefs | 4 | tracked | per file |
| scratchpad | 4 | 3 tracked, 1 ignored | per file |
| web | 4 | tracked | per file |
| .githooks | 3 | tracked | per file |
| __pycache__ (root) | 3 | ignored | class |
| config | 3 | tracked | per file |
| scripts | 2 | 1 tracked, 1 ignored | per file |

Outside the repo (LIST ONLY, never moved): `E:\Sidecars\LW`, the
`C:\Legion Wallpaper` junction, account-side Claude project memory, LOCALAPPDATA
state, scheduled tasks `LW-*`, worktree parents.

## 3. Slices (sized to finish inside the run)

Each slice is reviewed by one read-only sub-agent; the driver lands fixes.

| Slice | Scope | Checks | Expected fixes | Tier |
|---|---|---|---|---|
| A | root files, .claude, .github, .githooks, config, scripts, web, briefs, local, scratchpad, caches | hierarchy, memory recall (read list, WAKEUP / BACKLOG roles), gitignore, command files (SUBAGENT-FIRST block, stale figures, absolute paths), configs | RRF-3.4 placeholders, stale figures, gitignore gaps | 0-1 |
| B | docs/ (all), ROADMAP.md | md-set audit (ARCHITECTURE, OPERATIONS, AGENTS, LEDGER size, ADR index, ROADMAP bloat), links, RRF-3.3 consumer table | broken links, stale facts; dated-doc moves only where consumer-free | 0-1 |
| C | tools/, tests/ | orphans, one-offs, misplaced tests, live-state tests (RRF-T1), stale skips, orphan .pyc, tools/models class | RRF-T1 fix (TDD), misplaced-file moves | 1 |
| D | ops/, data/, logs/, moon_sync_*, images, venvs, outside-repo sidecars | runtime growth, stale progress / scratch, dated backups, venv consumers, sidecar consolidation list | gitignore / doc fixes only; everything else FILED | 0 |

Known findings folded in, not re-derived: MAIN 2246 section 2 (PERF-AUDIT),
section 3 (README-AUDIT), section 5 (SIDECAR-1), section 6 (ATLAS: no LW
follow-up). Already DONE in the attended session (LEDGER 292): 3.1, 3.5, 3.6,
2.2, 2.3 timeout/effort, 2.4, 2.5, 2.7, section 4, section 5. Open as ROADMAP
row REPO-REVIEW-FOLLOW: RRF-2.1, 2.3b, 2.6, 2.8, 2.9, 2.10, 3.2, 3.3, 3.4, T1.

## 4. Fix rules and limits

- TDD where behaviour changes; ruff on written files; py_compile on .py edits.
- Commits through `fleet_gitlock.py run --owner <claims owner id>`, file-scoped,
  ASCII + LF messages, no AI / bot trailer (FLEET-COMMON 17).
- Whole suite once at the end through `fleet_suite_gate.py`; one push at the end.
- LISTED, NEVER DONE: history rewrite / force push, remote branch deletion,
  visibility changes, scheduled-task changes, deletes of anything irreplaceable,
  edits to ops/fleet_kit/* or the FLEET-COMMON block, edits to
  ops/loop/slots.py / ops/loop/winmutex.py, moving any sibling's bytes.
- Concurrency: the LW inbox responder was mid-run (kit v14 adoption, editing
  ops/fleet_kit/*) when this run started; this run touches none of its files and
  commits file-scoped only.
