# Transcript-store split: measured diff, union semantics, and the apply command

Measured 2026-09-20 on Legion. Tool `tools/lw_transcript_union.py`, tests
`tests/test_lw_transcript_union.py`. Nothing has been applied - see section 6.

## 1. The defect, re-measured

`~/.claude/projects` carries TWO store keys encoding one tree:

| key | files | bytes | last write |
| --- | --- | --- | --- |
| `C--Legion-Wallpaper` (canonical) | 65 | 343,655,472 | this session, continuously |
| `C--LegionWallpaper` (stray) | 4 | 13,409,469 | 2026-09-12 |

The per-file figures in the brief were confirmed EXACTLY. The directory totals were not:
the brief said the canonical key held 273 files / 497,010,131 B, and it holds **65 files /
343,655,472 B**. Stated here because a stale total is what a future reader would otherwise
carry forward.

Per-file, byte counts as measured:

| file | canon | stray | delta |
| --- | --- | --- | --- |
| `cf160e3d-747a-470c-918f-24a1c289f454.jsonl` | 990,558 | 990,558 | 0, identical |
| `a89cfc16-da15-4cce-a7cf-8315d284fecd.jsonl` | 11,702,629 | 11,702,737 | +108 |
| `d3d7c8f7-c332-4666-898d-65575bb2065c.jsonl` | 452,223 | 716,096 | +263,873 |
| `d3d7c8f7-...desktop-released.json` | ABSENT | 78 | sidecar, stray only |

## 2. Record-level diff - and the correction the brief needs

Records were parsed and keyed on `uuid` where present. Note up front that **384 of 1036
lines in `a89cfc16` carry no `uuid` at all**: types `queue-operation`, `last-prompt`,
`custom-title`, `bridge-session`, `atis-latch` and `mode` have no record id, and many are
byte-identical repeats within one file. Those key on their raw bytes, and their
MULTIPLICITY matters (section 3).

| uuid | canon lines | stray lines | canon-only | stray-only | in-both bytes identical | verdict |
| --- | --- | --- | --- | --- | --- | --- |
| `cf160e3d` | 575 | 575 | 0 | 0 | yes (all 575 lines identical in order) | **IDENTICAL** |
| `a89cfc16` | 1036 | 1037 | 0 | 1 | yes (first 1036 lines identical in order) | **stray SUPERSET by one record** |
| `d3d7c8f7` | 216 | 426 | 186 | 369 | n/a - only 3 keys shared | **CONTINUATION TAIL** |

### `d3d7c8f7` is NOT a superset - and NOT a divergent fork either

**The brief's framing is wrong on this file and must be corrected.** Calling the stray "the
longer record" implies a superset; a set-difference alone would imply a fork (both sides
hold records the other lacks). Neither is what this is. Four measurements settle it:

* the `uuid` sets are **disjoint**: canon holds 172 distinct uuids, stray holds 346, and the
  intersection is **0**;
* the timestamp ranges are **contiguous and non-overlapping**: canon runs
  `2026-09-06T21:53:27.549Z -> 22:05:12.903Z`, stray runs `22:05:13.312Z -> 22:32:09.054Z`;
* the stray's **very first record** is parented on
  `881ef3fa-42c6-4a87-b834-dea45a4f16a7`, which is the canonical copy's **last** uuid
  (verified equal);
* no canonical record is parented on any stray-only uuid (0 of them).

So this is ONE session whose transcript was cut in two by a mid-session store-key flip: the
canonical file is the head, the stray file is the tail. Appending the stray after the
canonical bytes is therefore not merely lossless, it **reconstructs the original causal
order**. The 3 "shared" keys are uuid-less boilerplate lines (`custom-title`,
`bridge-session`, `atis-latch`) repeated 10x in canon and 19x in stray, not shared content.

The sidecar `d3d7c8f7-...desktop-released.json` is `{"v":1,"releasedAt":
"2026-09-07T04:24:13.055Z","reason":"delete"}`. It has no canonical counterpart, so it is
copied, not merged.

### The phantom cwd is in BOTH copies

Every `cwd` in the stray is `C:\LegionWallpaper` (no space), a path that returns ENOENT -
confirmed. But the **canonical** copies of the same three sessions carry the identical
phantom cwd. So the phantom cwd is a property of these three sessions, not a marker that
distinguishes the stray key from the canonical one, and it cannot be used to route records.

## 3. Union semantics, and why

Output = **multiset union** keyed on each record's stable id:

* key = the record's `uuid` when it has one;
* key = the record's **raw bytes** when it has none;
* an unparseable line keys on its own bytes and is kept rather than discarded;
* output count per key = `max(canon_count, stray_count)`.

Order: **every canonical line first, in its original order**, then any stray record beyond
what canon already held, in the stray's own order.

Three properties this buys, each one a rule from the brief:

* **No record is dropped.** A naive set union would be wrong here, not merely inelegant:
  `d3d7c8f7` repeats a byte-identical `custom-title` line 10 times in canon and 19 in
  stray, so collapsing by set would destroy 27 records across the three shared keys. The
  multiset rule is why the union appends **396** records to `d3d7c8f7` and not the 369 a
  set-difference reports - the extra 27 are the higher-multiplicity shared keys.
* **No record's bytes are rewritten.** Lines are copied verbatim, never re-serialized.
  `read_lines` opens with `newline=""`; without it, universal-newline translation would
  silently rewrite a CRLF record as LF. A test pins this.
* **Canonical order is preserved**, which for `d3d7c8f7` also happens to be causal order.

## 4. The guard, and why the obvious version of it does not work

A live session appends to the canonical directory continuously, including the session
running this tool. Unioning a file under a live writer loses whatever it appends between
the read and the replace. Three checks, strongest first:

1. **The running session's own transcript.** Refuse if
   `$CLAUDE_CODE_SESSION_ID.jsonl` exists in the canonical directory.
2. **mtime window.** Refuse if any canonical-dir file was modified in the last 120 s.
3. **Write-lock probe.** Refuse if any target opens non-appendable.

**Check 1 exists because check 2 is not sufficient, and this was measured, not assumed.**
The brief predicted the mtime guard would refuse. It did not: on the first real dry-run the
live session's own transcript had last been flushed **353.8 s** ago, because Claude Code
batches transcript flushes rather than writing per turn. A guard resting on the mtime alone
would have passed a live writer straight through and been recorded as a green. The session
id is a deterministic liveness signal where the mtime is a racy one. Check 2 is kept as a
backstop for sessions other than this one; check 3 can false-green when the holder shared
write access, so it is a further line of defence only, never the basis of a claim.

Scope: the guard gates **`--apply`**, where the data risk is. A dry run writes nothing and
so cannot lose a byte; it stays usable as a preview and prints `WOULD REFUSE on --apply`.
That is a scoping decision, not a weakening - the apply path is unconditional, and a test
asserts a refused apply does not touch a byte.

Other safety properties: `--dry-run` is the default; the pre-union canonical file is copied
to the backup dir **before** the replace; the canonical file is written atomically (tmp in
the same directory, then `os.replace`); the **stray directory is never touched** - not
deleted, not moved. Closing the split is a separate decision the operator owns.

## 5. Mutants killed

Six, each broken in place, confirmed RED, then restored **byte-exact** (sha256 verified)
and confirmed GREEN at 28 passed.

| # | mutation | arms that went RED |
| --- | --- | --- |
| 1 | `union_lines` emits every stray line unconditionally | 10 |
| 2 | dedupe by set membership instead of multiplicity | 1 - `test_uuidless_records_dedupe_on_raw_bytes_not_collapsed_by_multiplicity` |
| 3 | live-session mtime guard disabled | 3 |
| 4 | write-lock probe never fires | 1 - `test_refuses_when_a_target_file_is_locked_for_writing` |
| 5 | backup taken AFTER the replace instead of before | 2 |
| 6 | session-id live check disabled | 1 - `test_refuses_when_the_running_sessions_own_transcript_is_in_the_canonical_dir` |

Mutant 2 is the no-duplicate proof and mutants 3/4/6 are the refusal proofs, as required.
Mutant 2 killing exactly one arm is the point: that arm was written for it and nothing else
covers it, so without it a set-based union would have shipped green.

Two real bugs were found by the tests during the red phase, not after: universal-newline
translation rewriting CRLF records, and `union_lines` dropping a blank line it was handed
(filtering belongs at the read boundary, so the arm was moved to `read_lines`).

Every test injects its state via `tmp_path`. Nothing reads the real `~/.claude/projects`
and nothing depends on this machine - `tests/test_drift_guard_agent_config.py` was written
the same way after a test that read machine state passed locally and went red on CI.

## 6. Dry-run against the real store, verbatim

```
$ python tools/lw_transcript_union.py
lw_transcript_union - DRY-RUN (nothing written; pass --apply to act)
  UNION a89cfc16-da15-4cce-a7cf-8315d284fecd.jsonl
        lines 1036 -> 1037 (+1 stray-only)
        bytes 11702629 -> 11702737
        backup -> a89cfc16-da15-4cce-a7cf-8315d284fecd.canon.bak
  NOOP  cf160e3d-747a-470c-918f-24a1c289f454.jsonl  (already identical)
  COPY  d3d7c8f7-c332-4666-898d-65575bb2065c.desktop-released.json  (78 B, no canonical counterpart to merge)
  UNION d3d7c8f7-c332-4666-898d-65575bb2065c.jsonl
        lines 216 -> 612 (+396 stray-only)
        bytes 452223 -> 1163739
        backup -> d3d7c8f7-c332-4666-898d-65575bb2065c.canon.bak
  the stray store is left in place, untouched.
  WOULD REFUSE on --apply (exit 3): 3ac8447f-322c-477a-9456-11aac6c27a3e.jsonl is the RUNNING session's own transcript and it lives in the canonical store - this process is itself a live writer there. Re-run from a session whose transcript is not in this directory, or when none is open.
exit=0
```

### The apply was attempted and REFUSED. Nothing was applied.

```
$ python tools/lw_transcript_union.py --apply
REFUSE (exit 3): 3ac8447f-322c-477a-9456-11aac6c27a3e.jsonl is the RUNNING session's own transcript and it lives in the canonical store - this process is itself a live writer there. Re-run from a session whose transcript is not in this directory, or when none is open.
This is the correct outcome while a session is open. Do NOT weaken the guard.
exit=3
```

This is the correct outcome. The guard was not weakened to force it through; it was
STRENGTHENED (check 1) after the mtime window was measured to pass a live writer. Verified
after the refusal: canonical `d3d7c8f7` still 452,223 B, all four stray files present, and
the backup dir `ops/runtime/transcript_union` does not exist - not a byte moved.

### Rehearsal on copies of the real bytes

Because the live apply is correctly blocked, the union was rehearsed against **copies** of
the three real file pairs in a scratchpad, with the guard satisfied by construction. An
audit independent of the tool's own verification block:

```
  a89cfc16: canon 1036 stray 1037 -> out 1037 | canon lines lost 0 | stray lines lost 0 | uuids missing 0
  cf160e3d: canon  575 stray  575 -> out  575 | canon lines lost 0 | stray lines lost 0 | uuids missing 0
  d3d7c8f7: canon  216 stray  426 -> out  612 | canon lines lost 0 | stray lines lost 0 | uuids missing 0
  backup matches PRE-union bytes: True
  stray untouched: True
```

`612 = 216 + 396`, and `426 - 396 = 30` is the 3 shared uuid-less keys at canon
multiplicity 10 each. No record from either side is lost on any of the three files.

## 7. The exact command the next session runs

First action of the next session, run **before** anything else opens a session on this
project - and note the constraint this tool's own guard imposes: a session whose transcript
lives in `C--Legion-Wallpaper` cannot apply it, so run it from a shell outside Claude Code
(or from a session on another project).

```
python "C:\Legion Wallpaper\tools\lw_transcript_union.py"            # preview
python "C:\Legion Wallpaper\tools\lw_transcript_union.py" --apply    # act
```

Expected: exit 0, the two UNION lines above, and a VERIFICATION block reading
`all pre-union canonical lines present: yes` for both, `overall: OK`. Backups land in
`C:\Legion Wallpaper\ops\runtime\transcript_union\`.

If it refuses, a session is open somewhere - that is the guard working. Do not pass
`--window 0` and do not edit the guard.

Rollback: copy `ops/runtime/transcript_union/<uuid>.canon.bak` back over
`~/.claude/projects/C--Legion-Wallpaper/<uuid>.jsonl`.

## 8. What this does NOT do

The stray key `C--LegionWallpaper` is **left in place with all four files**. After the
apply the canonical key holds a superset of its content, so deleting the stray key becomes
safe - but that is a separate, operator-owned decision and this tool never takes it. The
root cause (whatever wrote a `C:\LegionWallpaper` cwd and a second store key) is **not**
fixed here either; this closes the data split only. `drift_guard` will keep reporting the
two-key breach until the stray key is removed.
