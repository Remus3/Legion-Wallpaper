# ADR-013: Adopt the evidence ladder and the skeptic gate; adapt, do not vendor

**Date:** 2026-09-16
**Status:** Accepted

## Context

The operator queued three external tools on 2026-09-15 and asked that
`timharris707/skills` be reviewed for implementation. That review landed in
`ROADMAP.md` the same day with a verdict: of the three, it is the least popular
by three orders of magnitude and the most relevant, because two of its 23
skills are almost verbatim the mechanism the refutation-cost lane converged on.

That lane is not speculative. Five trees each counted how many of their own
done-claims were later refuted and how many a program could have caught. LW's
own re-scored census (`docs/REFUTATION_COST_RESCORE_2026-09-12.md`) put
gate-or-contract-reachable at 82.3 pct, with GATE-ABSENT beating GATE-EXISTING
2.2 to 1 - the dominant failure is not a gate that let something through, it is
that no gate was asked. LW, RSC and CS then independently named the same
remedy: a mutation / non-vacuity gate. `run/blast-radius` and
`run/adversarial-review` are that remedy, already written down:

- `blast-radius` states outright that "a blast-radius writeup that sounds right
  is worth nothing on its own" and grades every safety claim on a five-rung
  evidence ladder, with anything short of rung 4 said out loud as unproven.
- `adversarial-review` runs isolated finders, then a SKEPTIC whose brief is to
  kill each finding, and gates only on skeptic-confirmed blockers - where
  BLOCKER rank requires a runnable reproduction. A finding nobody could make
  fail does not hold a merge.

Both were read in full at upstream commit `a9317e0` before this decision.

Three things made a verbatim vendoring wrong even though the licence permits it:

1. **Dangling cross-links.** Upstream's two files link to `plainspoken`,
   `orchestrate`, `domain-memory` and a `team-workflow` binding doc. LW is
   taking two skills, not the pack, so every one of those links resolves to
   nothing on disk.
2. **Not 7-bit ASCII.** Measured on the downloaded blobs: `blast-radius` is
   clean, `adversarial-review` carries 4 non-ASCII bytes (section signs).
   `strip_em_dashes.py --check` does not cover that codepoint, so it would have
   passed the gate and still broken the CLAUDE.md hard rule.
3. **It would have stacked a second protocol.** LW already runs SUBAGENT-FIRST
   in 20 command docs and gates on `.claude/agents/verifier.md`. Dropping in a
   document that names its own reviewer roles, its own binding slots and its own
   decider would leave two protocols describing the same moment with different
   words - the same two-disagreeing-durable-records failure LW has already paid
   for elsewhere.

## Decision

Adopt `blast-radius` and `adversarial-review` from `timharris707/skills` (MIT),
ADAPTED into `.claude/commands/blast-radius.md` and
`.claude/commands/adversarial-review.md`, with MIT attribution and the upstream
credit chain (pstack, mattpocock) preserved in each file. Not a byte-copy, not
the pack, not `team-workflow`, not `setup`.

The skeptic is a **mode of the existing `verifier` agent**, not a new agent.
The five ladder rungs - Asserted, Cited, Traced, Run, Reproduced - are spelled
identically on all three surfaces, and `tests/test_review_protocol_contract.py`
fails if any surface forks the spelling, drops the SUBAGENT-FIRST block, loses
attribution, reintroduces a dangling upstream link, or admits a byte above 127.

**Declined, with the reason, so nobody re-opens them:** `run/handoff` defaults
to an UNTRACKED `.claude/handoff.md` loaded by a session-start hook; LW's
equivalent is `WAKEUP_NOTES.md` plus `docs/LEDGER.md`, both TRACKED, and the
tracking is the point - a public append-only record is what makes a claim
auditable later. `orient/domain-memory` overlaps CLAUDE.md's Settled section
and `docs/adr/` the same way. Adopting either would split a durable record in
two.

## Consequences

**Good:** the non-vacuity gate the refutation lane named now exists as
something a session can be held to, in LW's own vocabulary, bound to the agent
LW already gates on. A claim that stops at "plausible" now has a name and a
rung number instead of passing as settled. The adopted text carries its
licence chain, so a reader can trace every borrowed idea to its author.

**Trade-off:** adaptation means LW's copy will drift from upstream, and there
is no pin that would tell us. That is deliberate - a byte pin (the
`docs/CHANNEL.md` pattern) is right for a doc two trees must agree on
character-for-character, and wrong for one that had to be rewritten to be
correct here. The cost is that an upstream improvement has to be noticed and
re-adapted by hand.

**Watch for:** the review protocol is prose, and prose decays. The contract
test is the only thing keeping it from becoming decoration, so an arm that is
weakened or deleted is the failure mode to watch. The ladder's value also
depends entirely on rung 4 being cheap here; if writing the script that proves
a claim is routinely expensive in this tree, sessions will stop at rung 3 and
report it, which is honest but buys nothing - that is the signal to invest in
fixtures, not to lower the bar. And `docs/DEFECT_CLASSES.md` is admitted-by-
reproduction only; the first time a class lands there on a hunch, the file
starts its slide into an unread checklist.
