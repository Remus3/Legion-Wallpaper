# Transcript store key flip - root cause, measured 2026-09-20

**The cause is established for the mid-flight flip and NARROWED, not proven, for the
key-derivation rule that made the two spellings possible.** The flip instant is known to
0.4 s and the event that correlates with it is known by name. What I could not see is the
harness code that turns a path into a store key, so the last step is an inference from
artifacts, labelled as such below.

**Two recorded claims are WRONG and are corrected here, loudly:**

1. `C:\LegionWallpaper` is **NOT a phantom cwd**. It was LW's REAL project root until
   2026-09-06 (LEDGER 146: root re-spelled to `C:\Legion Wallpaper`, `1ef672e` +
   `81de837` + `a019586`; LEDGER 150: RC held `LW_ROOT = C:\LegionWallpaper`). It returns
   ENOENT today because it was renamed away, not because it never existed. The claim
   "A phantom cwd, not a second checkout" in `tools/lw_transcript_union.py` and in
   `docs/TRANSCRIPT_UNION_2026-09-20.md` inverts the diagnosis: the RECORDS are right and
   it is the canonical KEY that carried a spelling the root did not have.
2. The stray store holds **ZERO records the canonical key does not already carry.** Every
   one of the 746 / 441 / 346 stray uuids is present in a canonical file under a DIFFERENT
   session id, byte-for-byte identical apart from `sessionId` (0 missing, 0 differing, all
   three sessions). So "a quarter-MB of history that exists nowhere else" is wrong: it
   exists in `C--Legion-Wallpaper` under another file name. A `--apply` run would append
   426 lines to canonical `d3d7c8f7` that already live in canonical `eed18e6e`. The union
   is still lossless and still causally ordered - it is just no longer a RECOVERY.

Read-only throughout. Nothing under the store was written, moved, renamed or reflowed, and
the union tool was never run with `--apply`.

## 1. Timeline

The box is UTC-0500. Record timestamps are the `timestamp` field (Z); file times are local.
`native` = 100 ns NTFS precision (a real write). `ms-stamped` = a whole-millisecond mtime,
which is a value set explicitly by a writer, not produced by an append.

### The two key directories

| key | created | last entry added (dir mtime) | files | bytes | newest file mtime |
|---|---|---|---|---|---|
| `C--Legion-Wallpaper` | 2026-07-03 16:23:37.523024 | 2026-09-20 18:06:21 | 306 | 513,241,077 | live this session |
| `C--LegionWallpaper` | **2026-09-06 17:05:13.323282** | 2026-09-07 17:29:20.499670 | 4 | 13,409,469 | 2026-09-12 11:35 |

The canonical key was created on LW's genesis day, 2026-07-03, and its `memory/`
subdirectory carries the IDENTICAL creation time to the nanosecond, so both were made by
one operation that day. The stray key did not exist until 2026-09-06 17:05:13.323282 -
**0.389 s after the canonical `d3d7c8f7` stopped being written and 0.011 s after the
stray's own first record.** The stray key was born at the flip.

### Session a89cfc16-da15-4cce-a7cf-8315d284fecd

| | bytes | lines | uuids | created | modified | records |
|---|---|---|---|---|---|---|
| canon | 11,702,629 | 1036 | 746 | 2026-08-29 18:30:32.401242 | 2026-09-11 13:14:57.352000 [ms-stamped] | 2026-08-29T23:30:32.357Z -> 2026-08-30T03:59:30.532Z |
| stray | 11,702,737 | 1037 | 746 | 2026-09-07 17:29:20.499670 | 2026-09-11 13:14:57.352000 [ms-stamped] | identical range |

The two mtimes are equal to the nanosecond and both are whole-millisecond values: one
writer stamped both. The single stray-only line is
`{"type":"custom-title","customTitle":"Legion Wallpaper","sessionId":"a89cfc16-da15-4cce-a7cf-8315d284fecd"}`.
Canonical twin under another id: `4930ea5c-9828-4a53-a390-1b2b735d0967`, 11,703,253 B,
1042 lines, 746 uuids, created 2026-09-07 17:32:06.053626 (9 days after its own first
record). Every record inside it is stamped `sessionId: a89cfc16...`, not `4930ea5c`.

### Session cf160e3d-747a-470c-918f-24a1c289f454

| | bytes | lines | uuids | created | modified | records |
|---|---|---|---|---|---|---|
| canon | 990,558 | 575 | 441 | 2026-09-05 09:13:48.575124 | 2026-09-12 11:35:22.130000 [ms-stamped] | 2026-09-05T14:13:48.504Z -> 2026-09-06T14:35:49.395Z |
| stray | 990,558 | 575 | 441 | 2026-09-06 19:51:52.825254 | 2026-09-12 11:35:22.130000 [ms-stamped] | identical range |

Byte-identical pair, mtimes equal to the nanosecond, both ms-stamped. Canonical twin:
`6f3ec7f6-093d-4641-a764-1d421280c74d`, 1,610,977 B, 771 lines, 583 uuids, created
2026-09-06 21:19:40.594527; it carries both session ids internally.

### Session d3d7c8f7-c332-4666-898d-65575bb2065c - the mid-flight split

| | bytes | lines | uuids | created | modified | records |
|---|---|---|---|---|---|---|
| canon | 452,223 | 216 | 172 | 2026-09-06 16:53:34.898062 | 2026-09-06 17:05:12.934072 [native] | 2026-09-06T21:53:34.780Z -> 22:05:12.903Z |
| stray | 716,096 | 426 | 346 | 2026-09-06 17:05:13.323282 | 2026-09-06 17:32:09.057118 [native] | 2026-09-06T22:05:13.312Z -> 22:32:09.054Z |

Both mtimes are native and both land within 40 ms of their own last record, so both halves
were written live, in place. Sidecar present ONLY in the stray:
`d3d7c8f7-c332-4666-898d-65575bb2065c.desktop-released.json`, 78 B, mtime
2026-09-06 23:24:13.056365, content
`{"v": 1, "releasedAt": "2026-09-07T04:24:13.055Z", "reason": "delete"}`.

Canonical twin: `eed18e6e-d588-4181-af5f-66b6dd81ddc8`, 816,175 B, 450 lines, 359 uuids,
created 2026-09-06 19:50:58.339658, and its FIRST record timestamp is
**2026-09-06T22:05:13.312Z - the same millisecond as the stray's first record.** It holds
both session ids internally.

Correction to a figure carried into this task: the canonical half's first record timestamp
is **21:53:34.780Z**, not 21:53:27.549Z. 21:53:27.549Z appears nowhere as a `timestamp` in
either copy. Everything else in the stated premise re-verifies exactly: uuid sets disjoint
(172 vs 346, intersection 0), timestamps contiguous and non-overlapping, and the stray's
first `parentUuid` is `881ef3fa-42c6-4a87-b834-dea45a4f16a7`, the canonical copy's last
uuid-bearing record.

## 2. The boundary records, verbatim

Last three lines of the canonical copy (shallow, no nesting to elide):

```
{"type":"custom-title","customTitle":"Legion Wallpaper","sessionId":"d3d7c8f7-c332-4666-898d-65575bb2065c"}
{"type":"atis-latch","atis":"","sessionId":"d3d7c8f7-c332-4666-898d-65575bb2065c"}
{"type":"bridge-session","bridgeSessionId":"cse_01BBtXt79RHmvicAPnrbWhgA","lastSequenceNum":0,
 "ownerAccountUuid":"4eb3a75e-c116-4528-a6fb-d53971a1adf2",
 "ownerOrganizationUuid":"dd2ba0f8-c6bf-435d-8680-05c246859c4c",
 "sessionId":"d3d7c8f7-c332-4666-898d-65575bb2065c"}
```

Preceded by `last-prompt`, and before that the last uuid-bearing record
`881ef3fa` at 22:05:12.903Z. First record of the stray copy:

```
{"parentUuid":"881ef3fa-42c6-4a87-b834-dea45a4f16a7","isSidechain":false,
 "userType":"external","cwd":"C:\\LegionWallpaper","sessionId":"d3d7c8f7-c332-4666-898d-65575bb2065c",
 "version":"2.1.260","gitBranch":"main","entrypoint":"claude-desktop","type":"user",
 "uuid":"364c364c-3268-4d55-a26e-58ecb5e0bcfa","timestamp":"2026-09-06T22:05:13.312Z",
 "promptId":"dbe68cab-dabb-4c1d-b7b8-f06e5d13607b",
 "sourceToolAssistantUUID":"881ef3fa-42c6-4a87-b834-dea45a4f16a7",
 "message":{...tool_result...},"toolUseResult":{...}}
```

**Every field that could distinguish the two keys is IDENTICAL across the boundary.**
Measured over whole files, not just the two adjacent records:

| field | canonical half | stray half |
|---|---|---|
| `cwd` | `C:\LegionWallpaper` (172/172) | `C:\LegionWallpaper` (346/346) |
| `version` | `2.1.260` (172/172) | `2.1.260` (346/346) |
| `gitBranch` | `main` | `main` |
| `sessionId` | `d3d7c8f7-...` (216/216) | `d3d7c8f7-...` (426/426) |
| `userType` | `external` | `external` |
| `entrypoint` | `claude-desktop` | `claude-desktop` |
| `isSidechain` | false | false |

**There is no harness upgrade at the boundary and no cwd change at the boundary.** The
version is 2.1.260 on both sides of every one of the 518 records. That candidate is
eliminated.

The only thing that differs is record TYPE, and it is decisive. The canonical half ends
with the control quartet `last-prompt` / `custom-title` / `atis-latch` / `bridge-session`,
and the stray half opens with the tool_result for `toolu_012nxsNzi9CHkSj9zT1Q3kQK` - the
result of the Bash call issued by `881ef3fa`. **That tool result names the event.** The
command was

```
tasklist /FI "IMAGENAME eq pythonw.exe" 2>&1 | tail -3
echo "=== test run, no --move ==="
"<python314>" "C:/lw_rename_fixup.py" 2>&1 | tail -20
```

and its stdout, crossing the boundary, reads:

```
### step_trust_keys
trust keys: dropped 3 stale, wrote 3 agreeing spellings

### step_memory_dir
memory dir: C--LegionWallpaper -> C--Legion-Wallpaper

### step_tasks
task LW-Wallpaper: recreated
task LW-WeeklyHygiene: recreated
task LW-CIWatchdog: recreated
```

So at the exact second the key flipped, a migration script rewrote `~/.claude.json`'s
project-key spellings and the agent memory directory **out from under a live session** -
and it did so in a mode that deliberately skipped the directory move (`no --move`), so the
registry was pointed at the post-rename spelling while the root on disk still carried the
pre-rename one. The stray key directory was created 0.389 s later.

## 3. What determines the key

**The encoding is confirmed empirically.** Every run of non-alphanumeric characters
becomes one `-`, so a colon, a backslash and a space are indistinguishable in the result.
Checked against live keys whose trees exist on this disk with spaces in their names:
`C:\Riot Commander` -> `C--Riot-Commander`, `C:\Resin Compute` -> `C--Resin-Compute`,
`C:\Legion Wallpaper` -> `C--Legion-Wallpaper`. That is why the two LW spellings land one
hyphen apart, and it is what `drift_guard.collide_store_keys` folds on.

**It is NOT the cwd recorded in the records, and this is the load-bearing measurement.**
`C--Legion-Wallpaper` was created 2026-07-03 and **37 of its 66 transcripts record cwd
`C:\LegionWallpaper`**, the pre-rename root. Those files were written there LIVE, not
migrated in afterwards: each was created 0.04 s to 0.35 s after its own first record, and
the whole run forms a sequential chain in which each file's creation time equals the
previous file's last-write time to about 0.1 s (for example `8548dfb0` modified
2026-08-11 18:47:20.441834, `56554c69` created 2026-08-11 18:47:20.353249). A bulk move
would have had to reproduce that chain exactly across thirty-odd files. So for 65 days the
live key carried a hyphen the live root did not have, and the two disagreed without
consequence.

The trap in the task brief is therefore real but points the other way: the recorded cwd
appears in both keys because it was simply the truth at the time. It never distinguished
the two keys because it was never what selected them.

**The stray key IS exactly the encoding of the then-live root.** `C:\LegionWallpaper` ->
`C--LegionWallpaper`. So the resolution that produced the stray key derived it from the
live cwd, and the resolution that had been in use for 65 days did not.

**NARROWED, NOT PROVEN.** The best-supported mechanism, and I cannot close it because the
derivation code is not visible to me:

- the canonical key already carried the space-form spelling on 2026-07-03, when nothing on
  disk had a space, so it came from something the app held rather than from the filesystem -
  a registered project entry or project label. The session's own `custom-title` is
  `Legion Wallpaper`, with the space, which is suggestive and nothing more.
- at 17:05:13 the fixup script replaced the `~/.claude.json` project spellings ("dropped 3
  stale, wrote 3 agreeing spellings") with the post-rename form while the root had not
  moved. A live session whose registered entry has just been replaced no longer matches a
  registered project, and the observed behaviour is a fall back to encoding its own cwd.
- the correlation is 0.389 s and the causal chain is visible in one record: the tool that
  rewrote the registry is the tool whose RESULT is the first record in the new key.

Candidates eliminated, with the evidence:

| candidate | verdict | why |
|---|---|---|
| harness version changed mid-session | ELIMINATED | `2.1.260` on all 518 records, both sides |
| cwd changed mid-session | ELIMINATED | `C:\LegionWallpaper` on all 518 records, both sides |
| a second checkout at the no-space path | ELIMINATED | `C:\LegionWallpaper` ENOENT; LEDGER 146 records the re-spelling of the one tree |
| the recorded cwd selects the key | ELIMINATED | 37 of 66 canonical files record the no-space root and were written there live |
| gitBranch / userType / entrypoint / sessionId | ELIMINATED | identical across the boundary |
| the pre-rename transcripts were migrated into the canonical key | ELIMINATED | ctime-to-first-record deltas of 0.04-0.35 s and the sequential ctime chain |
| the registry rewrite under a live session re-derived the key from cwd | BEST SUPPORTED, unproven | 0.389 s correlation, the causing tool named in the boundary record |

## 4. A second instance on this machine

**No second two-spelling instance.** `drift_guard.collide_store_keys` run over all 35 live
key directory names returns exactly one group:
`[('clegionwallpaper', ['C--Legion-Wallpaper', 'C--LegionWallpaper'])]`. LW's own, and
nothing else. The sibling trees are each represented by exactly one key.

**The OTHER shape is present.** `C--` exists: created 2026-09-01 08:28:02.601150, modified
2026-09-20 13:16:11, 143 files, 61,074,668 B, four session ids and a `memory/` directory.
It encodes `C:\` and names no tree at all, which is the shape a sibling reported.
`collide_store_keys` normalizes it to `c`, which collides with nothing, so the existing
guard is blind to it by construction - already recorded, LEDGER 694. Per the read-only
instruction I looked only at names, sizes and times there and read none of its content.

Also present and NOT this defect: five worktree-derived keys, one responder-export key,
one nested-projects key, five Design-lane keys and nine scratchpad-derived keys (three of
them this session's own). Each names a distinct real directory.

## 5. Recurrence verdict

**It can still recur. Two shapes: one closed for now, one OPEN.**

**(A) The mid-flight flip - closed until the next root re-spelling.** It needs the project
registry rewritten under a live session while the root spelling is in transition. Today:
`C:\LegionWallpaper` returns ENOENT; `~/.claude.json` holds exactly three LW spellings
(`C:\Legion Wallpaper`, `C:/Legion Wallpaper`, `c:/legion wallpaper`), all of the current
root, all `hasTrustDialogAccepted` True, and no no-space key; and `C:\lw_rename_fixup.py`
no longer exists. This re-arms in full the next time the root is re-spelled, and the
operator has re-spelled it once already. **The transferable rule: do not rewrite
`~/.claude.json` project keys, or the store's own directory names, while a session is
open on that project - not even in a mode that skips the filesystem move.**

**(B) Re-materialization of an old session - OPEN.** 37 of 66 canonical transcripts still
record the pre-rename root, and the store demonstrably rewrites old sessions long after
they end: `a89cfc16` first appeared in the stray key on 2026-09-07 17:29:20, a full day
after the flip, and both `a89cfc16` and `cf160e3d` were rewritten on 2026-09-11 13:14:57.352
and 2026-09-12 11:35:22.130 with whole-millisecond mtimes identical on both sides of the
split. A writer that stamps mtime rather than appending, writing the same conversation into
two keys at once, is the observed behaviour. I cannot prove that writer derives its
directory from the recorded cwd - but every stray file's recorded cwd is the old root, and
the stray key is exactly that root's encoding. Nothing has been written to the stray key
since 2026-09-12 11:35 (8 days at the time of writing) and the app has moved 2.1.260 ->
2.1.275 since, so the trigger may already be gone; **I cannot show that it is, so the
honest verdict is that it can recur.**

## 6. Does the existing guard catch it

**Yes, and no second guard should be added.** Proven live this session, not assumed:
`drift_guard.collide_store_keys` over the 35 real key names returns the LW group and only
the LW group; `str(ROOT)` normalizes to `clegionwallpaper`, which equals that group's
normalized form, so `check_transcript_store_keys` files it via `warn()` as a BREACH rather
than a note; and `drift_guard.main` calls it on every session. A recreated
`C--LegionWallpaper` would be caught the moment the directory appears, because the arm
enumerates directory names and folds separators rather than grading the spellings it
happens to find. Coverage is already pinned hermetically in
`tests/test_drift_guard_agent_config.py` (the space-to-nospace fold, the
breach-versus-note split, the three-spelling enumeration, the empty-input case).

Two limitations worth stating rather than patching:

- while the stray directory persists, the arm reports continuously, so it cannot tell
  "recurred" from "never closed". The arm only works as a DETECTOR once the split is
  closed. Given finding 2 above - the stray holds nothing unique - closing it is now a
  defensible decision, but it is the operator's call and this session is read-only there.
- the arm is blind to the tree-less `C--` shape by construction, since that name normalizes
  to a string nothing else collides with. Detecting that shape needs a different predicate
  (a key that decodes to a filesystem root, or to a path that does not exist), which is a
  separate question from this one and is not proposed here.

## 7. What remains UNKNOWN

- **the harness's key-derivation code.** Everything in section 3 is inferred from
  artifacts on disk. I never saw the function that turns a path into a store key.
- **why `C--Legion-Wallpaper` carried the space-form hyphen from 2026-07-03** while the
  root had no space. The registered-project-label candidate fits every observation and is
  unproven.
- **the direction of the `a89cfc16` / `cf160e3d` writes.** Identical whole-millisecond
  mtimes on both sides prove that one writer set both. They do not prove which side it
  read.
- **what `step_memory_dir` actually moved.** The canonical `memory/` directory's creation
  time is identical to its parent's to the nanosecond (2026-07-03 16:23:37.523024), so it
  was not created by that move; the step may have reported an idempotent no-op.
  `C:\lw_rename_fixup.py` is gone, so its source cannot be read.
- **whether 2.1.275 still re-materializes to a cwd-derived key.** Untested, and it cannot
  be tested without provoking it.
- **the `.desktop-released.json` semantics.** `{"reason":"delete"}` written at
  2026-09-07T04:24:13.055Z is suggestive of a release-and-delete handshake that never
  completed, and I have one instance in the stray key plus two in `C--`. Three samples is
  not a mechanism.

## 8. Limits of the instrument

- **Read-only on the store.** No write, move, rename or reflow, and the union tool was
  never run with `--apply`. Sibling keys were inspected by name, size and time only, never
  by content.
- **NTFS creation time survives a same-volume move**, so ctime alone cannot separate
  "written here" from "moved here". The discriminator I relied on is the ctime-to-first-record
  DELTA plus the sequential ctime-to-previous-mtime chain across 30-plus files. That is
  strong evidence, not a proof.
- **mtime precision is used as evidence**: 100 ns granularity for a native NTFS write,
  whole milliseconds for a value set explicitly by a writer. A strong signature, not an
  airtight one.
- **The cloud side is invisible.** `bridge-session` records name a `cse_` session and an
  owner account, and I can see only what landed on this disk.
- **No reproduction was attempted.** Provoking a key flip means renaming the live root
  under an open session, which is the incident, not a probe.
