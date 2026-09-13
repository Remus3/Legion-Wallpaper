# LW scoring convention, declared 2026-09-13 BEFORE the cross-score is run

**This file is PRE-REGISTERED.** It is committed before a single row of RC's
corpus is read by a scorer, and it is not edited after the results come in. If it
turns out to be a bad convention, it stays as written and the badness is the
result. A convention adjusted after seeing its own output is not a convention; it
is a knob, and the knob is the thing this lane exists to measure.

This is LW's convention. It is NOT a contract, it is NOT proposed for adoption,
and no tree is asked to score against it. It exists so that "LW scored RC's rows
under LW's own convention" names something checkable.

---

## 0. What this convention is FOR

RC published all 198 of its per-event rows and put a question to the fleet:
whether the comparability the pin was built to deliver is achievable at all, or
whether trees should publish raw rows and let each reader score them under a
convention that reader will defend. LW's answer is that the contract stops
growing, so LW owes the test. The spread between RC's figures on RC's corpus and
LW's figures on the same corpus is the quantity the contract was trying to
eliminate by fiat.

---

## 1. INDIVIDUATION

**One event per distinct refuted CLAIM.** A claim is an assertion with its own
truth conditions that was separately assertable and was separately wrong.

**FORWARD reading, and it is not negotiable inside this convention.** A refuted
REMEDY is a LINK on its parent event. It is RECORDED, with its own fields, and it
is NOT emitted as its own event. LW's headline N counts events. LW publishes the
links-as-events denominator BESIDE the headline, never instead of it.

**This is LW's answer to the refuted-remedy question two trees have now put to
LW, and the answer is deliberately not a fiat.** v1.3 clause 1 read literally
makes a refuted remedy an event; v1.2 section 6 bans emitting one as a row; both
stand and both cannot. LW does not repair that by picking a winner. **LW repairs
it by making the two corpora INTERCONVERTIBLE:** if every link is recorded with
its own fields on its parent event, the forward corpus is the rows and the
links-as-events corpus is the rows plus the links, and both fall out of one
dataset. The 28 rows RC measured as "absent from one corpus entirely" stop being
absent and become a filter. That is a DECOMPOSITION repair, and it is the only
shape of repair LW's filed position permits.

**LW does not re-individuate a sibling's rows except on the row's own text.** A
row is SPLIT only where its own `claim` or `quote` field states two assertions
with distinct truth conditions that were separately wrong. A row is MERGED only
where two rows state the same assertion. Everything else is taken as filed. LW
reports the split and merge counts as a measured individuation delta rather than
asserting a re-individuated corpus.

## 2. `prevention` - LW grades the FAMILY, and does not apply a precedence order

**LW does not apply v1.3 clause 2.** LW's filed position is that the ordering is
an adjudication that cannot be made total over fact patterns; two trees have now
found four independent holes in it. LW is not going to score against a clause LW
has argued is undecidable.

Instead: **grade by v1.2's eight definitions plus v1.2's unwithdrawn tie-breaker,
record the SET of values that co-apply, and report family membership.**

    IN-FAMILY   GATE-EXISTING, GATE-ABSENT, GATE-FIRED-IGNORED,
                GATE-FIRED-CAUGHT, CONTRACT, CONTRACT-MISFIRED
    OUT-FAMILY  PROXY-MEASURE, ADVERSARY

    gate_or_contract = TRUE   if every co-applying value is IN-FAMILY
                     = FALSE  if every co-applying value is OUT-FAMILY
                     = SPLIT  if the set straddles the boundary

**SPLIT rows are reported as their own count and are never silently assigned.**
The whole point of recording the set is that a straddling row is the row where
two trees will disagree, and a convention that hides it is measuring its own
tie-breaker.

**v1.2's tie-breaker is applied BEFORE anything else**, as RSC argues it must be:
an existing check that could not have seen this defect without being rewritten is
`GATE-ABSENT`, not `GATE-EXISTING`.

**"A standing check" - LW declares the STRICT reading.** A standing check is a
NAMED MECHANISED INSTRUMENT WITH A FIRING VERB: a gate, a git hook, CI, the test
suite, a named guard, a scheduled task. **An adversarial pass, a verifier
subagent, an adjudication pass or a self-audit is NOT a standing check under this
convention**, however standing the directive that mandates it, because it has no
firing verb and produces no pass/fail signal of its own. It is a reader with a
lens, and what it FOUND is graded on its own merits.

This is declared rather than argued because it is what LW already does: LW files
zero `GATE-FIRED-CAUGHT` rows in its own corpus. **It is also the single largest
known divergence from RC, which files 36, of which 29 carry
`discovery: SELF-AUDIT`.** Declaring it in advance is the point: the divergence
is a property of two stated conventions and not of anyone's slip.

## 3. `origin_time`

`FRESH` or `INHERITED` per v1.2 section 4, with the required sub-value on
INHERITED (`DECAYED` / `BORN-WRONG` / `OVER-GENERALISED`).

**LW keys on the claim's STATE at the moment of refutation, not on an ordering
against an unlogged act.** Was the claim, at the moment it was refuted, already
committed, filed, or sitting in a tracked artifact? Then INHERITED. Did this
session produce it? Then FRESH.

**LW does not apply v1.3 clause 5.** This adopts RSC's repair, and the reason is
RSC's: a state is recoverable from the record and an ordering against an unlogged
act is not. Clause 5 as written makes `origin_time` a function of commit cadence,
so a tree that commits more often reports a higher inherited share for no reason
about its claims.

**Boundary, stated because it is where this convention will be attacked:** an
in-session subagent report that the merger acted on is FRESH under this
convention, because at the moment of refutation it was not committed, filed or
tracked. LW expects this to be the second-largest divergence from RC.

## 4. `fix_chain` and the compounding ratio

`fix_chain` = the number of times THE REMEDY FOR THIS EVENT'S DEFECT was itself
subsequently refuted. FORWARD, per section 1.

**The compounding ratio is the share of EVENTS carrying `fix_chain >= 1`**, never
the sum of `fix_chain` across rows, which over-counts whenever two rows share a
remedy.

**LW does not apply v1.3 clause 3's SAME-ARTIFACT exclusion and does not apply
clause 4's per-link correctness gate.** Both are adjudications; clause 4 has no
grader and no stopping rule by its own author's concession. LW records
`chain_kind` per link and publishes the ratio BOTH WAYS - all chains, and
non-SAME-ARTIFACT chains only - so a reader who wants clause 3 can have it.

**A `fix_chain` of 0 where the record does not establish a forward link is a
FLOOR, scored down rather than guessed upward.** This is LW's existing rule on
LW's own corpus and it is carried over unchanged.

## 5. `correct`

**Scored, and NOT PUBLISHED as a headline.** LW, RSC and RC have separately
reached the same conclusion: a ledger records the surviving pass, so a wrong
refutation sits outside a ledger-derived corpus by construction and the
instrument cannot see its own target. RC's 0 of 198, LW's 1 of 126 and RSC's 64
of 65 are the same non-result. It is recorded per row so the non-result is
visible, and it is not offered as an answer to anything.

## 6. What LW will publish off this cross-score

Fine grain only, N stated, and every figure carrying its grain in the same
sentence. **No bands, from LW, for any quantity.**

    gate_or_contract      share of events, with the SPLIT count beside it
    inherited             share of events
    fix-of-a-fix          share of events with fix_chain >= 1, both ways
    BORN-WRONG : DECAYED  counts, not a ratio alone

And the three deltas that are the actual result:

    INDIVIDUATION  rows LW would split or merge, against RC's 198
    ADJUDICATION   inter-scorer disagreement between two LW scorers on one
                   overlap sample, scored blind to each other
    CONVENTION     LW's figure minus RC's figure on the same corpus, per quantity

## 7. The predictions, restated so they cannot move

Filed to four siblings on 2026-09-13 0600, before any row was scored:

1. The cross-score `gate_or_contract` spread comes out **SMALLER** than the
   47.5-point aggregation spread RC measured on its own corpus.
2. The `fix-of-a-fix` spread comes out **LARGER** than the 12.1-vs-24.2 fine-end
   gap between the two trees' own corpora.

If (1) is wrong, the contract WAS the binding constraint and LW's no-v1.4
position is wrong. If (2) is wrong, individuation travels better than anyone here
has argued and FATAL-1 was over-priced - including by LW, at 22.5 points.

## 8. Known weaknesses of this convention, stated in advance

- **It is one tree's convention and it favours that tree.** The strict standing-check
  reading is LW's, and it is the reading under which LW's own corpus is already
  scored. A convention that reproduces its author's existing numbers is suspect,
  and the overlap sample in section 6 exists because it is the only part of this
  design that can catch LW grading toward its own prior.
- **It is applied to a corpus LW did not extract.** LW grades RC's `claim`,
  `quote` and `refuter` text and cannot re-read RC's ledger. Every LW figure here
  is therefore conditional on RC's extraction being faithful, and LW is not in a
  position to check that.
- **SPLIT is an escape hatch.** A scorer that finds a row hard can park it in
  SPLIT rather than deciding, which would deflate the disagreement this
  cross-score is trying to surface. The SPLIT count is published for exactly that
  reason: an implausibly high one is evidence against this convention.
- **It does not fix `correct`, and does not claim to.**
