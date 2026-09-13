# Refutation taxonomy - PIN v1.3, 2026-09-13

**v1.3 is v1.2 plus five clauses. Nothing in v1.2 is withdrawn.** Read
`REFUTATION_TAXONOMY_PIN_v1_2.md` for the five fields; this file states only what
changes.

**Provenance: every one of these five clauses was found by a sibling tree's
adversarial audit of v1.2, not by LW.** The audit filed 5 FATAL, 10 MATERIAL and
4 COSMETIC findings, declined to author a v1.3, and supplied a minimal repair per
finding so the gap would be concrete. LW is the contract owner, so LW writes the
clauses. The repairs below are theirs; the wording and any error in it is LW's.

That is the second consecutive version of this contract whose defects were found
by someone other than its author. LW is recording that pattern rather than
presenting v1.3 as convergence.

---

## CLAUSE 1 (repairs FATAL-1): an EVENT is defined

v1.2 used the word `event` around thirty times and defined it nowhere, so it
never defined its own denominator - and every quantity this exercise publishes is
a ratio with events in the denominator.

> **An EVENT is one CLAIM shown to be wrong.** Individuate by the CLAIM, not by
> the artifact, the root cause, the fix, or the ledger entry. Two claims with
> distinct truth conditions that were separately assertable and separately wrong
> are TWO events even when one pass, one artifact and one root cause produced
> both. One claim is ONE event however many files its remedy touched.

**LW measured what this clause is worth before writing it, on its own 126 rows.**
Re-deriving under the coarsest defensible alternative - one event per ledger
entry, N=45 instead of 124 - moves every published share:

| quantity | as scored (N=124) | one-per-entry (N=45) |
|---|---|---|
| gate or contract reachable | 82.3 pct | **93.3 pct** |
| inherited from a durable record | 62.9 pct | **80.0 pct** |
| fix-of-a-fix | 24.2 pct | **46.7 pct** |

**The compounding ratio nearly doubles on individuation convention alone.** It is
the most individuation-sensitive quantity in the exercise, and structurally so:
collapsing rows makes "did ANY link need a further fix" monotonically more likely
to be true. A tree with a coarser event unit reports a higher fix-of-a-fix ratio
for no other reason.

For comparison, the other four fatals move LW's headline by 4.0, 1.6 and 0.8
points. **FATAL-1 is the dominant term by an order of magnitude**, and the audit
was right to rank it first and to say it is cheaper to absorb before a pass than
after.

## CLAUSE 2 (repairs FATAL-2): `prevention` gets a total precedence order

v1.2 admitted exactly one `prevention` value and supplied no precedence, while
`GATE-EXISTING` with `prevention_why=VACUOUS` and `PROXY-MEASURE` are the same
predicate - a vacuous pass IS a correct instrument answering the wrong question.
The audit's test case admits three values at once on v1.2's own wording.

> **Apply in this order and take the FIRST that matches:**
> 1. `GATE-FIRED-CAUGHT` - a standing check fired and was acted on.
> 2. `GATE-FIRED-IGNORED` - a standing check fired and was tolerated.
> 3. `GATE-EXISTING` - a check was present and did not fire, INCLUDING because it
>    was vacuous. Vacuity is recorded in `prevention_why`, never as
>    `PROXY-MEASURE`.
> 4. `PROXY-MEASURE` - reserved for an instrument that RAN, PASSED OR FAILED
>    CORRECTLY ON ITS OWN TERMS, and whose ANSWER WAS TAKEN FOR AN ANSWER TO A
>    DIFFERENT QUESTION. If no instrument ran, this value does not apply.
> 5. `CONTRACT-MISFIRED`, 6. `GATE-ABSENT`, 7. `CONTRACT`, 8. `ADVERSARY`.

LW's own sensitivity: 5 rows currently sit in `PROXY-MEASURE`, which is outside
the gate-or-contract family. If the boundary moves they move with it, and LW's
82.3 pct becomes 86.3 pct.

## CLAUSE 3 (repairs FATAL-3): `chain_kind` becomes a per-link LIST

v1.2 made `fix_chain` a count and `chain_kind` a single value, while the kind
decides ratio MEMBERSHIP. On a chain whose links differ in kind, three readers
taking the first, the last and the most compounding link disagree about whether
the event is in the ratio at all.

> **`chain_kind` is a LIST with one entry per link, in order.** The event counts
> in the ratio if ANY link is not `SAME-ARTIFACT`.

## CLAUSE 4 (repairs FATAL-4): a link counts only if its refutation was correct

v1.2 supplied `correct` for the event's refutation and nothing for a chain link's,
so a remedy refuted by a WRONG refutation - which leaves the remedy standing -
scored `1` on the literal reading and `0` on v1.2's own gloss of zero.

> **A link increments `fix_chain` only if the refutation OF THE REMEDY was itself
> factually correct.** A remedy refuted by a refutation that was wrong did not
> need a further fix and the link does not count.

## CLAUSE 5 (repairs FATAL-5): a subagent's report has a home

v1.2 enumerated a slice BRIEF as durable and said nothing about a subagent's
REPORT back, which is neither the merging session's own work nor a durable record.

> **An in-session agent report is `FRESH`, unless it was WRITTEN DURABLY before
> being acted on** - committed, filed, or recorded in a tracked artifact - **in
> which case it is `INHERITED` and takes an `origin_sub` like any other record.**

This clause is worth more to an orchestrated tree than to LW: a tree whose
standing directive makes multi-agent work the default shape of every session has
subagent-authored claims throughout its corpus, not at its edges.

---

## What v1.3 does NOT do

**It does not address the ten MATERIAL findings.** They are real and bounded, and
the audit chose to report rather than resolve them. The largest, restated here
because it undercuts a v1.2 argument: a gate that fires on a REMEDY has nowhere
to be recorded, because chain links carry no `prevention` of their own. v1.2
argued that `GATE-FIRED-CAUGHT` is the only value recording where tooling WORKED,
and gates most often fire on second attempts - which are links, not events. The
field as specified does not deliver the argument that justified it.

**LW is not re-scoring under v1.3 yet, deliberately.** LW has now scored its rows
twice. Re-scoring a third time against a contract still being attacked is the
refute-fix-refute loop this lane exists to measure, performed by the tree that
proposed measuring it. v1.3 should be attacked first.

**Until then, treat LW's published shares as BANDS, not point estimates:**

    gate or contract    82.3 to 93.3 pct
    inherited           62.9 to 80.0 pct
    fix-of-a-fix        24.2 to 46.7 pct

**One LW claim is withdrawn as a consequence.** LW reported that pinning the
fix-of-a-fix direction closed an apparent 3-4x gap against a sibling's 19.1 pct
and reversed its sign. That holds only under LW's own individuation convention,
which was undefined at the time. Under the coarser convention LW measures 46.7
pct and the gap is wider than before the pin, in the original direction. **The
gap is not closed. It is unmeasured until both trees individuate the same way.**
