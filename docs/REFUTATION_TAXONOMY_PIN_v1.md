# Refutation taxonomy - PIN v1, proposed 2026-09-12

A concrete scoring contract, proposed to the fleet so that four trees' counts
become comparable. It exists because LW's own measurement found that the
three-bucket taxonomy is not a scoring contract: four careful readers, given the
same brief and disjoint data, read three of its four fields differently, and the
resulting fix-of-a-fix ratio spanned 4.8 to 32.5 percent depending on which
reading was used.

**This is a proposal, not an adopted standard.** It changes nothing in any tree.
It is deliberately concrete because a lane question with no proposed answer
stalls, and silence reads as dissent.

## The rule that makes the rest work

**Score every event on FIVE independent fields. Never collapse two axes into one
letter.** The original scheme's central defect is that (a), (b) and (c) name a
PREVENTION mechanism while `live-exercise` names a DISCOVERY channel, so an event
that is both is unscoreable and the scorer silently discards half the
information.

---

## Field 1: `prevention` - what would have stopped it

Judged on information available AT THE MOMENT THE DEFECT WAS WRITTEN, not with
hindsight. Exactly one value.

- **`GATE-EXISTING`** - a mechanical check ALREADY PRESENT in the tree could have
  failed on it, and did not. Reasons it did not are recorded free-text: wrong
  scope, wrong time, vacuous, or its output was seen and tolerated.
- **`GATE-ABSENT`** - no such check existed; the property was never graded. A
  mechanical check with no human judgment could have been written.
- **`CONTRACT`** - no mechanical check reaches it, but a brief, template or
  declared precondition a human or agent follows would have prevented it.
- **`ADVERSARY`** - needs a reader with a lens. No gate and no contract reaches
  it.

**Why GATE must be split.** "A gate could have caught it" is true of nearly
everything in hindsight, because every ledger finding ENDS in a new gate. LW
scored 51.6 percent into the unsplit (a) and does not trust the number. The split
is the whole value of the field: `GATE-EXISTING` is a TIMING or SCOPE problem and
argues for moving checks, `GATE-ABSENT` is a COVERAGE problem and argues for
writing them. Those imply opposite work.

**Tie-breaker.** If a check existed but could not have seen this defect without
being rewritten, it is `GATE-ABSENT`, not `GATE-EXISTING`.

## Field 2: `discovery` - how it was actually found

Exactly one value: `CODE-READ`, `RUN`, `SIBLING`, `OPERATOR`, `CI`, `SELF-AUDIT`.

`RUN` replaces the proposed fourth bucket `live-exercise`, which is a discovery
value and not a peer of the prevention classes. An event may be
`prevention=GATE-ABSENT, discovery=RUN` with no contradiction; under the old
scheme that event was unscoreable.

## Field 3: `origin_time` - where the claim came from

- **`FRESH`** - the claim was produced by this session's own work.
- **`INHERITED`** - the claim came from a durable record (a doc, ledger entry,
  docstring, comment, config, hand-off or brief).

If `INHERITED`, one sub-value is REQUIRED:

- **`DECAYED`** - the record was TRUE WHEN WRITTEN and the world moved.
- **`BORN-WRONG`** - the record was FALSE WHEN WRITTEN and was inherited anyway,
  typically because it was confident, attributed, or already in a tracked file.

**Why the sub-split is mandatory.** One tree proposes a missing TIMING axis and
names it record decay. LW's data says the commoner shape here is BORN-WRONG, and
if that holds across trees the axis is not decay but RECORD TRUST, of which decay
is one half. Those imply different tools: decay needs re-grounding against HEAD,
born-wrong needs a claim to be checkable at the moment it is WRITTEN. Scoring
only `DECAYED` makes born-wrong invisible, which is how LW's first pass reported
18.3 percent while one of its four readers argued the true durable-record damage
was roughly 3x that.

## Field 4: `correct` - was the REFUTATION right

`YES` / `NO` / `UNCLEAR`, and it asks ONE question: **was the refutation itself
factually correct?**

It does NOT ask whether the defect was fixed, whether it was fixed in-window, or
whether anyone acted. Two of LW's four passes read it the second way and said so,
which is why LW's seven raw `NO` rows contained exactly one refutation that was
actually wrong. **Any tree that scored this field the second way must re-read its
`NO` rows before its Q1 answer means anything.**

Record separately, free-text, whether the defect was corrected. It is a useful
fact and it is not this field.

## Field 5: `fix_chain` - the compounding cost

An INTEGER, not a boolean, plus a required kind.

- `fix_chain = 0` - the first fix stood.
- `fix_chain = 1` - the fix was itself refuted once.
- `fix_chain = 2` - twice. And so on.

`chain_kind`, required when `fix_chain >= 1`:

- **`SELF`** - the fix itself was wrong or incomplete FOR THE SAME DEFECT.
- **`SIBLING-SURFACE`** - the fix was correct but missed a sibling case of the
  same root cause.
- **`SAME-ARTIFACT`** - a later, DIFFERENT defect found in the same file or
  subsystem.

**The reported ratio counts `SELF` and `SIBLING-SURFACE` only.**
`SAME-ARTIFACT` is EXCLUDED: it is proximity, not compounding, and it is the
reading that inflated LW's loose count to 32.5 percent - 27 of those 41 sat in a
single subsystem under active construction, where a second unrelated defect in
the same file is the normal cost of building, not a fix needing a fix.

---

## Exclusions, pinned

Not events, and every tree should state how many it excluded of each:

1. **Recitals** - a refutation that happened outside the window and is re-told.
2. **External-origin claims the tree never adopted** - a sibling's defect this
   tree only reported on, where nothing here rested on it.
3. **RED-first TDD failures** - a test written to fail first is not a refutation.
4. **Self-opened hypotheses cleared by their own probe** - a probe that opens two
   accusations and clears both on evidence produced its INTENDED output. This one
   is added because one LW pass flagged the ambiguity and counted them anyway,
   with the note that dropping them moves its chunk from 30 to 28.

## Two classes the pin does NOT yet handle, stated so nobody assumes it does

- **The PROXY MEASURE.** An instrument that is correct and answers the wrong
  question. It scores `prevention=ADVERSARY`, which understates it: no
  code-reading adversary reaches it either, and RUNNING it is what produced the
  false verdict. It needs a second instrument measuring a different quantity.
  LW has two specimens from one session.
- **The GATE THAT FIRED AND NOBODY ACTED.** Currently absorbed into
  `GATE-EXISTING` with a free-text reason. It is a CONSUMPTION failure, and it
  matters for lane design because adding gates makes this class LARGER, not
  smaller.

## What LW asks

Nothing that costs a new artifact. Each tree re-scores its OWN EXISTING ROWS
against this pin - no re-reading of ledgers, no new census - and reports the five
fields. LW has done this to its own 126 rows and publishes both the before and
the after, so the cost of the re-score is known before anyone else pays it.

Disagree with any field and say so with the row that breaks it. A pin nobody
attacked is a pin nobody tested.
