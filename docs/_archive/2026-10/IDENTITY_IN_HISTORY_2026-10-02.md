# The operator's address in LW history: measured, declined, guarded (2026-10-02)

Status: **CLOSED, with a recorded permanent residual.** Remediation was
considered and **DECLINED by the operator on 2026-10-02**. The forward guard is
`tests/test_no_identity_enters_history.py`. Read that file's docstring for the
guard's scope and - more importantly - for the list of things it cannot see.

This file exists because a finding nobody can find again is not recorded. It
names no value. Every sensitive quantity here is a sha256 digest or a git blob
sha, and neither reconstructs anything. That is deliberate: the standing lesson
`feedback-documenting-a-leak-republishes-it` was learned on this exact repo,
when the three artifacts written to RECORD the 2026-09-07 purge re-published
the purged address five times.

## What was measured

A full scan of the object database, run twice on 2026-10-02 - once as a probe
and once as the guard's own census arm, which asserts set equality against the
recorded population below.

| quantity | value |
| --- | --- |
| objects streamed | 4,772 |
| blobs scanned | 2,338 |
| blob bytes | 137.1 MiB |
| wall clock | 3.5s probe / 4.1s as the census arm |
| commits on all refs | 620 |
| carrier blobs found | 5 |
| commits whose tree publishes a carrier | 3 |
| distinct author/committer identities on all refs | 1, the GitHub noreply |

Reachability: the stream is `git cat-file --batch-all-objects`, so it covers
objects no ref points at, not just the reachable set.

## Findings

**1. No credential is in history.** No API key, token, private key, AWS key id,
JWT or connection string with an inline password, anywhere in the object
database, beyond the fixtures that are planted on purpose and say so in place.

**2. The operator's personal email address survives in FIVE history blobs.**
Pinned in the guard as `operator-address`, sha256 of the lowercased value, first
sixteen hex `6c69aeec06d41b08`, length 22, a public-webmail domain. A second pin
`operator-address-local-part` covers the local part alone - sha256 prefix
`4d3cb93c7b82d7c4`, length 12 - which is what a line break at the at-sign
leaves behind.

The carriers, by blob sha. These are not secret and they are what make this
record checkable: `git cat-file -e <sha>` proves one still exists, and
`git cat-file blob <sha>` shows it.

| blob sha | path |
| --- | --- |
| `100427ca360ae449797c4f0f3289d8d8cd81402b` | `docs/LEDGER.md` |
| `150d6d32e19fbd3397fb9aecb2e9d1594814bd7d` | `docs/LEDGER.md` |
| `611053d509d91183461f2fe2c252d685acb25b91` | `WAKEUP_NOTES.md` |
| `a1f888295cc66f831a3a7ad6e75a5412073d6cc2` | `WAKEUP_NOTES.md` |
| `b9992ac6744de4c9ec3053eb2fe645698cfd7f96` | `docs/_archive/2026-09-07-sha-rewrite-map.md` |

The three commits whose trees publish one or more of them, all three ancestors
of `origin/main`:

| commit | date | subject |
| --- | --- | --- |
| `e685573` | 2026-09-07 | docs: record the operator-email history purge (LEDGER 172) |
| `d327642` | 2026-09-07 | feat(first-pass): crop overrides can name an exact offset, not just an edge |
| `1bf2363` | 2026-09-08 | docs: sync living docs - the 0.Originals ingest + first pass session (LEDGER 173) |

**It is HISTORY ONLY. It is NOT in HEAD.** The tracked tree is clean, asserted
live by `test_the_carriers_are_history_only_and_not_in_head`. That is why the
three existing working-tree sweeps report green, and they are right to: it is
their scope.

**3. Commit METADATA is clean.** One distinct identity across the author and
committer fields of every commit on every ref, and it is the GitHub noreply
address. The 2026-09-07 rewrite worked on its targets. What survived is inside
the DOCUMENTS - including the document that recorded the purge.

**4. A second reported residual was CHECKED and is not one.** A hand-off report
listed an account-name-shaped segment under a `C:\Users\...` fixture as a
low-severity residual, sha256 prefix `66f86641108109a0`, length 11, in two
blobs. Measured: that digest is the string the fixtures use as a stand-in - a
synthetic eleven-character placeholder, planted by
`tests/test_handoff_write_gate.py` and `tests/test_inbox_responder.py` to prove
their redaction gates fire. It is not this machine's login, which is thirteen
characters and hashes to a different digest entirely. One of the two blobs is
live in HEAD today and is correct there. Nothing is pinned for it: pinning a
deliberate fake would make this guard fire on the fixtures that prove the other
guards work, and a guard that fights its siblings gets deleted. **This residual
is retracted, not downgraded.**

## Why the structural gap existed

LW's three identity sweeps are all WORKING-TREE guards, and none of them could
ever have seen any of the above. Verified against the live source before the new
guard was written, not taken from a report:

| guard | corpus taken at | bytes read at |
| --- | --- | --- |
| `tests/test_no_secret_literals.py` | :153-159 (`git ls-files`) | :194 (from disk) |
| `tests/test_no_account_paths.py` | :122-129 (`git ls-files`) | :151 (from disk) |
| `tests/test_no_split_identity.py` | :93-100 (`git ls-files`) | :109 (from disk) |

`git ls-files` is the index. A blob that is no longer checked out is outside all
three corpora by construction. git, however, keeps every blob it was ever
handed.

## Remediation: considered and DECLINED

The operator's decision, 2026-10-02: **do not rewrite history a fourth time.**
Reasons, all of them already recorded elsewhere in this repo and restated here
so the decision does not have to be reconstructed:

1. **Three rewrites have already happened** - 2026-08-01 (stray jpg), 2026-09-06
   (84 `Co-Authored-By: Claude` trailers), 2026-09-07 (the author/committer
   email). Each one moved every sha and cost a sha-rewrite map that citing docs
   still need. CLAUDE.md records that the maps **do not chain and must not be
   walked forward**. A fourth rewrite adds a fourth map and a fourth resolution
   hop to every historical citation in the repo.
2. **HEAD is clean.** The cost of the residual is bounded to blobs nobody
   checks out.
3. **A force-push does not purge GitHub-side unreachable objects.** CLAUDE.md
   states this as settled: delete-and-recreate the repository, or a Support
   request, is the only real purge. So the rewrite would pay the full local cost
   for a partial remedy, and the five blobs would remain fetchable from the
   remote by sha regardless.
4. **The value is already public.** It has been world-readable since 2026-09-07
   on a public repo. Removing it now changes availability, not disclosure.

Do not re-litigate this on the strength of the finding alone. The finding was
already known when the decision was made.

## What exists instead

`tests/test_no_identity_enters_history.py`, a fail-on-NEW gate in three scopes:

- **entry gate**, always runs, every tracked path on disk plus every staged
  blob that differs from HEAD. 551 items, 7.9 MiB, under 0.1s. This is the arm
  that binds in CI, because `ci.yml` uses `actions/checkout@v6` with no
  `fetch-depth` and that action's default is a one-commit shallow clone.
- **history delta**, every blob reachable from a ref but not from the recorded
  baseline `6dbe5e9be79d0e726432dc6d324a25a12ad5e3b9`. 0.016s at the baseline.
  Any pin hit in a blob outside the recorded carrier set fails. Skips on a
  shallow clone with a reason that says so, and FAILS rather than skipping if
  the baseline does not resolve in a repository that is not shallow - a stale
  baseline silently narrows the delta to nothing.
- **full census**, opt-in via `LW_IDENTITY_CENSUS=1`, asserts set equality
  between the live population and the five carriers recorded above. Both
  directions: an appearance is a new leak, a disappearance means this document
  is stale.

Re-derive this record at any time:

```
LW_IDENTITY_CENSUS=1 python -m pytest tests/test_no_identity_enters_history.py -q
```

or run the file directly, which turns the census on for you:

```
python tests/test_no_identity_enters_history.py
```

## If history is ever rewritten again

Both recorded constants become stale in the same instant, and the guard is
built to say so rather than to go quiet:

1. `BASELINE_COMMIT` stops resolving. The two history arms FAIL with a message
   naming the rewrite.
2. The five carrier blob shas may or may not survive, and the tables above stop
   resolving with them.

The repair is: re-run the census, re-record `KNOWN_CARRIERS` and
`BASELINE_COMMIT` in the guard, and update the tables in this file. Do not
delete the arms to make the suite green.
