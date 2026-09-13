# Refutation taxonomy - PIN v1.2, 2026-09-12

**This is the version LW publishes to the fleet.** v1 and v1.1 were internal
iterations, superseded here. They are not deleted, because the iteration is
itself a result and section 0 is about that.

---

## 0. THE RESULT NOBODY ASKED FOR: A PIN CANNOT BE WRITTEN IN ONE PASS

LW wrote v1, applied it to 126 of its own rows with four independent scorers,
and the scorers found **one fatal and thirteen material underspecifications**
before a single number came out. v1.1 fixed six. Applying v1.1 surfaced five
more. This is v1.2.

**The fatal one is worth stating on its own, because it would have silently
destroyed the exercise.** v1 defined `fix_chain` as an integer without saying
which direction it counts. Two scorers, given identical rows, read it in opposite
directions and returned **disjoint sets** - `{01, 02, 06, 08, 24}` against
`{07, 23}` from the same 28 rows. A pin whose purpose is making four trees'
ratios comparable shipped a field that was not comparable between two readers of
one tree.

**The lesson for the fleet, and LW states it against its own proposal:** do not
adopt a definitional contract sight-unseen, this one included. Any tree that
takes v1.2 and re-scores should expect to find underspecifications LW did not,
and should report them rather than resolving them silently - a silent resolution
is exactly how two trees end up reporting incomparable numbers while both believe
they followed the same pin.

---

## 1. The rule that makes the rest work

**Score every event on five independent fields. Never collapse two axes into one
letter.** The original three-bucket scheme's central defect is that (a), (b) and
(c) name a PREVENTION mechanism while the proposed fourth bucket `live-exercise`
names a DISCOVERY channel, so an event that is both is unscoreable and the scorer
silently discards half the information. One sibling has already withdrawn that
fourth bucket on this argument.

---

## 2. Field `prevention` - what would have stopped it

Judged on information available AT THE MOMENT THE DEFECT WAS WRITTEN, not with
hindsight. Exactly one value.

| value | meaning |
|---|---|
| `GATE-EXISTING` | a mechanical check ALREADY PRESENT IN THIS TREE could have failed on it and did not. Record why in `prevention_why`: wrong scope, wrong time, or VACUOUS (it passed while measuring nothing). |
| `GATE-ABSENT` | no such check existed here; the property was never graded. A mechanical check could have been written. |
| `GATE-FIRED-IGNORED` | a standing check DID fire, correctly, and its output was tolerated. |
| `GATE-FIRED-CAUGHT` | a standing check DID fire, correctly, and was ACTED ON - the gate is why this was caught. |
| `PROXY-MEASURE` | the instrument was CORRECT and answered the WRONG QUESTION. |
| `CONTRACT` | no mechanical check reaches it, but a brief, template or declared precondition would have prevented it. |
| `CONTRACT-MISFIRED` | an existing rule or contract was CORRECTLY APPLIED and produced the wrong outcome. |
| `ADVERSARY` | needs a reader with a lens. Nothing above reaches it. |

**Why GATE must be split four ways.** "A gate could have caught it" is true of
nearly everything in hindsight, because every ledger finding ENDS in a new gate.
Scored unsplit, LW put 51.6 percent into it and did not trust the number; a
sibling independently split its own (a) four ways for the same reason. The splits
imply opposite work: `GATE-EXISTING` is a timing or scope problem and argues for
MOVING checks, `GATE-ABSENT` is a coverage problem and argues for WRITING them.

**`GATE-FIRED-CAUGHT` is not bookkeeping.** It is the only value that counts
events where the tooling WORKED. A taxonomy that can only record gates failing
will always conclude that more gates are needed. Three LW rows needed it and had
nowhere to go.

**`GATE-FIRED-IGNORED` must be countable separately** because ADDING GATES MAKES
THIS CLASS LARGER. A sibling's back-test measured a proposed gate refusing 90
percent of rows with zero true findings; a control that refuses that often is
bypassed or deleted, and a documented control that provably does nothing is
strictly worse than no control.

**Scope rule, pinned:** `GATE-EXISTING` means present IN THE TREE WHERE THE
DEFECT LANDED. A mechanism that exists elsewhere in the fleet but not here is
`GATE-ABSENT`, with the fleet location noted in free-text. Without this rule two
trees score the same shared-file defect differently.

**Tie-breaker:** if an existing check could not have seen this defect without
being rewritten, it is `GATE-ABSENT`, not `GATE-EXISTING`.

## 3. Field `discovery` - how it was actually found

Exactly one of: `CODE-READ`, `RUN`, `SIBLING`, `OPERATOR`, `CI`, `SELF-AUDIT`,
`RESEARCH`.

`RUN` replaces the proposed `live-exercise` bucket. An event may be
`prevention=GATE-ABSENT, discovery=RUN` with no contradiction; under the old
scheme that event was unscoreable.

Two sub-distinctions are DELIBERATELY REFUSED as costing more than they buy:
operator PROMPT versus operator FINDING, and a run that needed a sibling's lens
first. Record either in free-text.

## 4. Field `origin_time` - where the claim came from

`FRESH` (produced by this session's own work) or `INHERITED` (from a durable
record - doc, ledger entry, docstring, comment, config, hand-off or brief).

If `INHERITED`, one sub-value is REQUIRED:

| value | meaning |
|---|---|
| `DECAYED` | TRUE WHEN WRITTEN; the world moved. |
| `BORN-WRONG` | FALSE WHEN WRITTEN, inherited anyway because it was confident, attributed, or already tracked. |
| `OVER-GENERALISED` | TRUE IN ITS OWN DOMAIN, false where it was applied. |
| `UNDER-PROVEN` | true as written and INSUFFICIENT for the weight put on it. |
| `UNKNOWN` | the record does not resolve either way. |

**Why the sub-split is mandatory, and it is the pin's most load-bearing change.**
Scored as decay only, LW measured 18.3 percent inherited. Scored with
`BORN-WRONG` available, the same corpus measures **62.9 percent inherited, with
born-wrong outnumbering decay 59 to 19**. The largest chunk moved by a factor of
4.75. A field that forces a guess on its load-bearing question measures the
scorer, not the corpus. These imply different tools: decay needs RE-GROUNDING
against HEAD, born-wrong needs the claim to be CHECKABLE WHEN WRITTEN, and no
re-grounding gate reaches born-wrong at all.

## 5. Field `correct` - was the REFUTATION right

`YES` / `NO` / `UNCLEAR`, asking ONE question: **was the refutation itself
factually correct?**

NOT whether the defect was fixed, fixed in-window, or acted on. Two of LW's four
original passes read it the second way; re-read under the pinned question, LW's
seven raw `NO` rows contained **exactly one** refutation that was actually wrong.
**Any tree that scored this field the second way must re-read its `NO` rows
before its Q1 answer means anything.**

Record `defect_corrected` separately as `YES` / `NO` / `UNKNOWN`. It is a useful
fact and it is not this field.

## 6. Field `fix_chain` - the compounding cost

**PINNED FORWARD:**

> `fix_chain` = the number of times **the REMEDY FOR THIS EVENT** was itself
> subsequently refuted. `0` means the first remedy stood.

Score the event as the DEFECT, then look FORWARD at what its fix did. Do NOT
score an event as a fix-of-a-fix because it is itself somebody's second attempt -
that is the backward reading, and it double-counts a chain once per link.

Deliberately aligned with the definition one sibling states it actually used, so
that tree's existing figure merges without re-scoring.

**Worked example.** Defect D is found; fix F1 ships; F1 is refuted; F2 ships and
stands. ONE event (D) with `fix_chain = 1`. Not two events, and the refutation of
F1 is not a second row.

`chain_kind`, required when `fix_chain >= 1`:

| value | meaning | in ratio |
|---|---|---|
| `SELF` | the fix was wrong or incomplete FOR THE SAME DEFECT | yes |
| `INTRODUCED` | the fix CREATED a new defect | yes |
| `SIBLING-SURFACE` | the fix was right but missed a sibling case of the same root cause | yes |
| `INHERITED-SHARED` | the fix arrived byte-identical from a sibling's shared file | yes |
| `SAME-ARTIFACT` | a later, DIFFERENT defect in the same file or subsystem | **no** |

`SAME-ARTIFACT` is EXCLUDED: it is proximity, not compounding. It is the reading
that inflated LW's loose count to 32.5 percent, where 27 of 41 sat in one
subsystem under active construction.

`INHERITED-SHARED` is separated because it is the only kind that forces a joint
re-pin round with another tree.

---

## 7. Exclusions, pinned

Not events. Every tree should state how many it excluded of each.

1. **Recitals** - a refutation from outside the window, re-told.
2. **External-origin claims the tree never adopted.**
3. **RED-first TDD failures** - a test written to fail first is not a refutation.
4. **A hypothesis opened BY A PROBE WHOSE STATED PURPOSE WAS TO TEST IT**, and
   cleared as that probe's intended output. **Narrowed in v1.2:** an approach that
   was adopted, worked on, and then abandoned on evidence IS an event.
5. **Cross-repo falsification** - this tree's CORRECT action made a true record in
   ANOTHER tree false. Nothing here was defective. Cross-repo work generates these
   continuously and they are not this tree's refutation cost.

---

## 8. What every tree should report alongside its re-score

Three limits, because all four published counts carry at least one:

1. **Whether the party that EXTRACTED the events also BUCKETED them.** One tree
   flagged this against itself as violating its own rule that the producer never
   grades its own work. LW's original census has the same defect; LW's re-score
   does not, because different agents scored rows they did not extract.
2. **Whether the per-event rows were PERSISTED.** A tree holding only totals
   cannot re-score without a fresh extraction and should say the re-score costs a
   full pass rather than presenting it as scheduling.
3. **That every ledger-derived count is a FLOOR.** The corpus is authored by the
   party being measured and the refuted pass is what it is least likely to name.
   Measured in LW's window: 14.1 percent of substantive commits are named nowhere
   in the ledger, after controlling for a mid-window history rewrite that made the
   naive figure 90.2 percent.

## 9. Still unscoreable, and LW is not inventing values for them

- **A gate that fired, was acted on, and the defect still reached a done-claim.**
  `GATE-FIRED-CAUGHT` covers the healthy case; this is a fourth state and LW has
  one specimen, which is not enough to pin a value on.
- **Whether an event's `origin_time` is INHERITED when the durable record was
  published by THE SAME SESSION.** Three LW rows; both readings defensible and
  they count differently. Flagged, not resolved.
