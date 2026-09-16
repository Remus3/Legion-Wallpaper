# Defect classes proven in this repo

Every `/adversarial-review` finder loads this file. It is the distilled record
of what has actually shipped-and-been-caught HERE - not a checklist imported
from someone else's war record, which would check for their bugs and not ours.

**Admission rule (ADR-013):** a class is admitted only via a LIVE REPRODUCTION -
a defect that actually occurred in this tree and was reproduced. The fixing
session proposes the class in the same commit that fixes the defect, so the
class lands with its proof. A hunch dressed as a class bloats this file until
nobody reads it.

**Removal rule:** a class is removed only by an EXTINCTION SWEEP - evidence the
whole pattern is gone from the codebase. Never "we have not seen it lately."

Each entry: what it looks like, where it was proven, and the question a finder
should ask.

---

## DC-01 - The gate that is present but does not fire

A hook file exists, a guard is installed, the config names it - and it gates
nothing. Proven twice on 2026-07-26: `core.hooksPath` pointed at `.githooks`,
so anything written into `.git/hooks` was dead; and `.githooks/pre-commit`
invoked `precommit_gate.py` with NO ARGS from 2026-07-03, where the gate
self-gates to a silent no-op. It ran on every commit for three weeks and gated
nothing. A third instance on 2026-08-01: an invalid `.claude/settings.json`
(single backslashes in a Windows path are not valid JSON escapes) is silently
unparsed, presenting exactly as a config with no hooks.

A fourth instance, 2026-09-16, found by the probe written to catch the class:
`precommit_gate.py --staged` is not a flag the gate has. It fell through to the
stdin path, found no commit command, and returned 0 - a silent pass that read
as a green gate. Run the gate the way the HOOK runs it (`--git-hook`), then
prove it through a real `git commit`. CROSS-TREE CORROBORATION the same day,
uncoordinated: RSC reports their own glyph gate, invoked bare, exits 0 having
scanned nothing for the same reason, so every manual "I ran the gate" there was
vacuous. Two trees, no coordination, same defect, same day.

**Finder asks:** has anyone SEEN this gate fail? Presence is not proof it
fires. The kill for a "gate works" claim is a mutation that the gate must
reject - see `feedback-mutation-prove-the-arm-binds`.

## DC-02 - The arm that asserts nothing

A test arm that passes whether or not the behaviour exists. Its family: an arm
gated on a condition that is never true in CI; an arm whose assertion is
implied by its own setup; an arm racing a clock (a guard-the-guard arm
depending on mtime granularity is a coin flip - 80 pct of back-to-back writes
share a tick, measured 2026-09-16); and an arm proving a command is NOT RUN,
which says nothing about whether it WORKS.

**Finder asks:** mutate the thing this arm guards. Does the arm go red? If
nobody can say, the arm is decoration.

## DC-03 - The tolerant reader that swallows a rename

`pipeline_state.json` and the manifests are read TOLERANTLY on purpose -
unknown fields ignored, stale-cache belt. That is correct for resilience and
it means a renamed or dropped field does not raise: it reads as absent, and
downstream silently takes the default path.

**Finder asks:** if this field were renamed, what would fail? If the answer is
"nothing, it would read as absent", that is the defect.

## DC-04 - The fix that prevents the future and leaves the past wrong

A data-corruption or pollution fix that guards future writes and never
backfills the rows already wrong. Carried in from the RC record, where a race
guard shipped prevention and still needed two further backfill-and-recovery
rounds.

**Finder asks:** does this change alter the shape of data already on disk? If
so, where is the recovery pass, and was it verified against the historical
rows live?

## DC-05 - The too-narrow first fix

A case-specific fix validated on one case, shipping while its siblings - other
variants, other modes, a duplicate code path - stay broken, which forces a
second comprehensive cleanup. The matching-rule variant is the mirror image:
a fold widened before there was test evidence for the wider set.

**Finder asks:** grep for the sibling cases. Is there a test covering each one,
or only the reported one?

## DC-06 - The claim inherited from a durable record

A claim the session did not make and cannot check, read out of `WAKEUP_NOTES`,
a doc or a prior ledger entry and repeated as current. LW's own census put
inherited claims at 62.9 pct of refutations, with BORN-WRONG outnumbering
DECAYED 3.11 to 1 - so the dominant case is not a fact that went stale, it is
one that was never true. No write-time gate can catch it by construction.

**Finder asks:** does this change rest on a fact nobody re-probed this session?
Re-probe it, or report it at rung 1.

## DC-07 - The count from an unanchored match

A number produced by an unanchored substring search, reported without a sample
beside it. Proven 2026-09-07: an unanchored name match inflated a count 218x.
Its sibling is the redaction nobody checked - a strip or blinding is a CLAIM
about your instrument, and LW leaked on 49 of 198 rows while believing
otherwise.

**Finder asks:** what exactly did the pattern match? Show ten of them.

## DC-08 - The path that only exists on this machine

A real account's home path written into a tracked file, or a Windows-only call
made unguarded in a test authored on Windows and run on Linux CI, or a test
reading live machine state (`~/.claude.json`) that passes locally and fails in
CI. This repo is PUBLIC and CI is Linux; both cut.

**Finder asks:** would this line run on CI, and would it disclose anything on a
world-readable page?
