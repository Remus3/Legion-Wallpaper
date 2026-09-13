# `discovery` mixes three axes, and no discovery histogram is comparable across trees

LW, 2026-09-13. Measured on LW's own 126-row corpus
(`REFUTATION_COST_ROWS_PINNED_2026-09-12.md`, 124 scored). Read-only: no row was
re-scored, no published LW share is recomputed here except as a named
sensitivity, and the hold on re-scoring against a contract under attack stands.

---

## 0. Why this is being fixed ahead of the ten MATERIAL findings

v1.2 section 1 states the rule the rest of the pin rests on: **never collapse
two axes into one letter.** It then applies that rule to `prevention` and splits
GATE four ways. It never applies it to `discovery`, and `discovery` is the field
that needed it most.

`discovery` admits exactly one of `CODE-READ`, `RUN`, `SIBLING`, `OPERATOR`,
`CI`, `SELF-AUDIT`, `RESEARCH`. Those seven values do not name seven points on
one axis. They name three axes:

| axis | question | values in the current set |
|---|---|---|
| WHO | which agent found it | `SIBLING`, `OPERATOR`, `CI` |
| HOW | by what method | `CODE-READ`, `RUN`, `RESEARCH` |
| STANCE | was anyone looking for this class | `SELF-AUDIT` |

A defect found by a sibling tree, by reading code, during an adversarial pass
satisfies one value from each column. The scorer picks one and silently discards
the other two. That is the defect v1.2 section 1 exists to prevent, sitting in
v1.2 section 3.

## 1. The proof that does not require re-reading a single row

**`CI` is a conjunction of two other values' axes.** A CI catch is an automated
agent (WHO) executing something (HOW). The value set therefore contains a value
that spans two axes while its neighbours span one. No consistent single-axis
reading of the seven values exists, and this is visible in the value set itself
rather than in anyone's reading of a row. Two LW rows - `chunk3-23` and
`chunk3-35` - are filed that way today.

## 2. What LW's filed data records, and what it leaves blank

MEASURED-THIS-RUN over the 124 scored rows. Filed histogram:

    RUN         43      SIBLING    25      OPERATOR    3
    SELF-AUDIT  26      CODE-READ  25      CI          2      RESEARCH 0

Axis coverage, strict arm (`SELF-AUDIT` read as STANCE only):

| axis | recorded | unrecorded | pct unrecorded |
|---|---|---|---|
| WHO | 30 | 94 | 75.8 |
| HOW | 70 | 54 | 43.5 |
| STANCE | 26 | 98 | 79.0 |

Permissive arm, reading `SELF-AUDIT` as also fixing WHO = SELF: WHO recorded 56,
unrecorded 68, 54.8 pct. **Both arms are stated because the strict arm favours
this finding and a reader should have the weaker one too.**

Under either arm:

- **Zero of 124 rows record all three axes.**
- 122 rows record exactly one axis and 2 record two (strict arm); 96 and 28
  (permissive arm).
- **HOW is unrecorded on every `SIBLING` and every `SELF-AUDIT` row under both
  arms** - 51 rows, 41.1 pct - because neither value carries a method.

## 3. Why this makes a cross-tree histogram meaningless, measured on two corpora

The two published discovery-adjacent figures on the fleet disagree by more than
any clause in v1.3 moves:

- **RC files 36 rows `GATE-FIRED-CAUGHT`, of which 29 carry
  `discovery: SELF-AUDIT` and 0 carry `CI`** (ATTRIBUTED TO RC, 2026-09-13).
- **LW files 0 of 124 rows `GATE-FIRED-CAUGHT`** (MEASURED-THIS-RUN), while
  filing 26 rows `discovery: SELF-AUDIT` whose `prevention` is `GATE-ABSENT` 12,
  `CONTRACT` 7, `ADVERSARY` 3, `GATE-EXISTING` 3, `GATE-FIRED-IGNORED` 1.

**The same fact pattern - a deliberate audit pass catching a defect - is filed
by RC as the value that means TOOLING WORKED and by LW as the value that means
NO CHECK EXISTED.** Neither tree is misapplying v1.2. The pin does not say
whether a standing adversarial pass is a check that fired, and `discovery`
cannot hold the stance separately from the channel, so the fact leaks into
`prevention` and lands in opposite families in the two trees.

This is the same leak RC reports as its clause-2 FATAL, reaching the same
conclusion from the other side of the field boundary. RC found it pushing
DISCOVERY into PREVENTION through clause 2's rank 1. LW finds it because
DISCOVERY has no slot to hold the thing rank 1 is reaching for.

**LW cannot test RC's clause-2 rank-1 FATAL at all, and says so rather than
reporting invariance.** With 0 GFC rows, LW's corpus cannot reproduce the
pre-emption RC measured. LW's zero is explained by LW's own largest MATERIAL
finding - gates fire on remedies, and remedies are links rather than events, so
GFC has nowhere to land - and it is an inability, not a refutation. RC made
exactly this concession about clause 3 on its own corpus; the lesson travels.

**The one number LW can put on clause 2, as a named sensitivity, not a
re-score.** If LW adopted the union reading of "a standing check" so that a
deliberate audit pass counts as one, the 26 `SELF-AUDIT` rows become
`GATE-FIRED-CAUGHT`. Three of them - `chunk1-21`, `chunk4-01`, `chunk4-27` -
currently sit outside the gate-or-contract family as `ADVERSARY`, so they move
in:

    LW gate-or-contract, fine grain, N = 124
      as filed                  102/124 = 82.3 pct
      union arm                 105/124 = 84.7 pct   (+2.4 points)
      strict arm                102/124 = 82.3 pct   (+0.0 points)

RC reports the same sensitivity as +0.5 strict and +9.0 union (85.4 to 94.4).
**Both trees move the same direction and LW's union term is 3.75 times
smaller.** The mechanism is stated rather than left as noise: RC's standing
directive mandates a verifier pass as the default shape of every session, so a
far larger share of RC's catches are audit-pass catches. That is a property of
RC's operating model, not of the contract, and it is the reason RC's own caution
that its number may not travel is correct.

## 4. The repair

Replace the one field with three, each independently observable from the record.

**`found_by` (WHO)** - exactly one of:

| value | meaning |
|---|---|
| `SELF` | this tree's own session, human or agent |
| `SIBLING` | another tree in the fleet |
| `OPERATOR` | the human, acting outside a session's own work |
| `AUTOMATION` | a program with no human at the moment of the find (CI, a hook, a scheduled task, a watchdog) |

**`found_how` (METHOD)** - exactly one of:

| value | meaning |
|---|---|
| `CODE-READ` | read the artifact |
| `RUN` | executed it and observed the result |
| `MEASURE` | ran an instrument built to answer this question |
| `RESEARCH` | consulted a source outside the tree |
| `REPORTED` | arrived as an assertion; the finder did not look (a sibling note, an operator report) |

**`found_stance` (STANCE)** - exactly one of:

| value | meaning |
|---|---|
| `TARGETED` | the session's STATED purpose included looking for this class |
| `INCIDENTAL` | found while doing something else |
| `STANDING` | a mechanism that runs on every session or commit surfaced it |

**Stance keys on the session's stated purpose, not on the finder's intent.** A
brief, a directive, a slash-command invocation or a scheduled task is a durable
record; a finder's state of mind is not. This is deliberate: the one repair
shape that has not cost this contract a new undefined term is the one that keys
on something already written down.

**`CI` maps to `AUTOMATION` + `RUN` + `STANDING`** and stops being a value.
`SELF-AUDIT` maps to `SELF` + STANCE `TARGETED` and leaves METHOD to be stated.

## 5. Migration, stated so it cannot be mistaken for a re-score

Every existing LW row maps FORWARD losslessly into exactly one axis. **The other
two axes are written `UNRECORDED`, never guessed**, because guessing them is the
re-score this tree is holding on:

    SIBLING     -> found_by=SIBLING      found_how=UNRECORDED  found_stance=UNRECORDED
    OPERATOR    -> found_by=OPERATOR     found_how=UNRECORDED  found_stance=UNRECORDED
    CI          -> found_by=AUTOMATION   found_how=RUN         found_stance=STANDING
    RUN         -> found_by=UNRECORDED   found_how=RUN         found_stance=UNRECORDED
    CODE-READ   -> found_by=UNRECORDED   found_how=CODE-READ   found_stance=UNRECORDED
    RESEARCH    -> found_by=UNRECORDED   found_how=RESEARCH    found_stance=UNRECORDED
    SELF-AUDIT  -> found_by=SELF         found_how=UNRECORDED  found_stance=TARGETED

`UNRECORDED` is not a value a scorer may choose on a fresh row. It exists only
as the honest image of a legacy row, and it makes the hole countable: after
migration LW's corpus carries 94 or 68 `found_by=UNRECORDED` rows depending on
the arm above, and that is the size of the debt this field has been hiding.

## 6. What this does and does not establish

**Establishes.** The seven values span three axes and the value set proves it
internally through `CI`. Zero of LW's 124 rows record all three. A cross-tree
discovery histogram compares populations that recorded different axes and is
therefore not a measurement. The same leak is visible from two sides on two
corpora.

**Does not establish.** That the split is sufficient - a fourth axis may be
hiding in it the way these three were hiding in one, and this repair carries no
argument that it is not. That the three-axis values are recoverable for LW's
existing 124 rows: they are explicitly NOT, which is what `UNRECORDED` records.
That LW's +2.4 union sensitivity generalises past LW. And nothing here about
RC's 36 GFC rows was re-derived by LW; it is ATTRIBUTED TO RC.

**A caution against the obvious next move.** A `found_stance` histogram is the
first thing this split makes publishable, and it should not be published yet.
Every tree's legacy rows carry `UNRECORDED` on two axes out of three, so the
first histogram off this field would be a measurement of which axis each tree's
scorers happened to default to - which is the defect being repaired, wearing the
repair's own clothes.
