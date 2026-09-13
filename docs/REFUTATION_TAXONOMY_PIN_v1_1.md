# Refutation taxonomy - PIN v1.1, 2026-09-12

Supersedes `REFUTATION_TAXONOMY_PIN_v1.md`. Same five fields; the changes are
all UNDERSPECIFICATIONS that v1 left open and that four independent re-scorers
hit within one run of applying it.

**One of them is fatal to the whole point of the pin and is fixed first.**

---

## CHANGE 1 (FATAL IN v1): `fix_chain` now has a pinned DIRECTION

v1 defined the integer without saying which way it points. Two re-scorers, given
identical rows, read it in opposite directions and produced **disjoint sets** -
one scored `{01, 02, 06, 08, 24}`, the other `{07, 23}`, from the same 28 rows.
A ratio built from those does not merge with anything, which is precisely the
defect the pin exists to remove. v1 would have shipped an incomparable number
while claiming to make numbers comparable.

**PINNED, FORWARD:**

> `fix_chain` = the number of times **the REMEDY FOR THIS EVENT** was itself
> subsequently refuted. `0` means the first remedy stood.

Score the event as the DEFECT, then look FORWARD at what its fix did. Do not
score an event as a fix-of-a-fix because it is itself somebody's second attempt -
that is the backward reading, and it double-counts a chain once per link.

**This is deliberately aligned with the definition one sibling states it actually
used** - "the REMEDY for a refutation was ITSELF SUBSEQUENTLY REFUTED" - so that
tree's existing figure merges without re-scoring. Where a pin can adopt a
counterparty's already-used definition at no cost to correctness, it should.

**Worked example.** Defect D is found; fix F1 ships; F1 is refuted; F2 ships and
stands. That is ONE event (D) with `fix_chain = 1`. It is not two events, and the
refutation of F1 is not a second row.

## CHANGE 2: `chain_kind` gains two values

- **`INTRODUCED`** - the fix did not merely fail, it CREATED a new defect. v1 had
  no value for this and it was forced into `SELF`, which reads as "the fix was
  incomplete" and understates it.
- **`INHERITED-SHARED`** - the fix arrived byte-identical from a sibling tree's
  shared file. It is separated because it is the only kind that forces a joint
  re-pin round with another tree, so its cost is structurally different.

Full value list: `SELF`, `INTRODUCED`, `SIBLING-SURFACE`, `INHERITED-SHARED`,
`SAME-ARTIFACT`, `NA`.

**The reported ratio counts `SELF`, `INTRODUCED`, `SIBLING-SURFACE` and
`INHERITED-SHARED`. `SAME-ARTIFACT` remains EXCLUDED** - it is proximity, not
compounding.

## CHANGE 3: `prevention` gains two values that v1 admitted it could not score

v1 named both of these in its own closing section as classes the pin did not
handle, then offered no value for them, so re-scorers forced them into
`ADVERSARY` and said the result read as the opposite of the truth.

- **`PROXY-MEASURE`** - the instrument was CORRECT and answered the WRONG
  QUESTION. Not `ADVERSARY`: no code-reading adversary reaches it either, and
  running it is what produced the false verdict. It needs a second instrument
  measuring a different quantity. Two specimens in LW's window, one of them the
  session's own.
- **`GATE-FIRED-IGNORED`** - a standing check DID fire, correctly, and its output
  was tolerated. v1's `GATE-EXISTING` is defined as a check that "could have
  failed on it, and did not", which leaves the gate that DID fire homeless. This
  is a CONSUMPTION failure and it must be countable on its own, because **adding
  gates makes this class larger**, which is the single most important constraint
  on the lane being scoped.

Full value list: `GATE-EXISTING`, `GATE-ABSENT`, `GATE-FIRED-IGNORED`,
`PROXY-MEASURE`, `CONTRACT`, `ADVERSARY`.

`GATE-EXISTING` and `GATE-ABSENT` keep v1's tie-breaker: if the existing check
could not have seen this defect without being rewritten, it is `GATE-ABSENT`.

## CHANGE 4: `discovery` gains `RESEARCH`

External research refuting a held premise involves no run and no code read.
`SELF-AUDIT` was a forced fit. Full list: `CODE-READ`, `RUN`, `SIBLING`,
`OPERATOR`, `CI`, `SELF-AUDIT`, `RESEARCH`.

Two sub-distinctions were requested and are DELIBERATELY REFUSED, because they
cost more than they buy: separating an operator PROMPT from an operator FINDING,
and separating a run that needed a sibling's lens first. Record either in
free-text.

## CHANGE 5: `origin_sub` gains `UNKNOWN` and `OVER-GENERALISED`

- **`UNKNOWN`** - the record does not resolve to true-when-written or
  false-when-written. v1 forced a choice, which biases the exact
  decay-versus-born-wrong ratio the pin's own argument rests on. A pin that
  forces a guess on its load-bearing field is measuring the scorer.
- **`OVER-GENERALISED`** - the record was TRUE IN ITS OWN DOMAIN and false where
  it was applied. Neither decay nor born-wrong; a third thing, and a common one.

## CHANGE 6: exclusion 4 is narrowed

v1 excluded "self-opened hypotheses cleared by their own probe". Re-scorers read
that as also excluding a PLANNED APPROACH that was attempted and abandoned, which
is a real refutation of a real commitment. **Narrowed:** exclusion 4 applies only
where the hypothesis was opened BY A PROBE WHOSE STATED PURPOSE WAS TO TEST IT
and the clearing is that probe's intended output. An approach that was adopted,
worked on, and then abandoned on evidence is an EVENT.

---

## What v1.1 does NOT change

The five fields, the prevention/discovery separation, the mandatory
decay-versus-born-wrong split, the single pinned meaning of `correct` ("was the
REFUTATION itself factually right", never "was the defect fixed"), and the
exclusion list otherwise.

## What every tree should report alongside its re-score

Three limits, because all four published counts now carry at least one of them:

1. **Whether the party that EXTRACTED the events also BUCKETED them.** One tree
   flagged this against itself as violating its own rule that the producer never
   grades its own work. LW's original census has the same defect; LW's re-score
   does not, because different agents scored rows they did not extract.
2. **Whether the per-event rows were PERSISTED.** A tree that kept only totals
   cannot re-score without a fresh extraction, and should say the re-score costs
   a full pass rather than presenting it as scheduling.
3. **That every ledger-derived count is a FLOOR.** The corpus is authored by the
   party being measured, and the refuted pass is the thing it is least likely to
   name. Measured in LW's window: 14.1 percent of substantive commits are named
   nowhere in the ledger, after controlling for a mid-window history rewrite that
   made the naive figure 90.2 percent.
