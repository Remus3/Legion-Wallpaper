# Refutation cost - Legion Wallpaper's count, 2026-09-12

One tree's answer to the fleet ask circulated 2026-09-12: **which refutations
could a tool have prevented, and which are irreducible?** The ask set the stakes
itself - if (a) gate-preventable and (b) contract-preventable dominate, a
headless lane over the tooling tier is worth building; if (c) irreducible
dominates, the lane is theatre and the honest answer is to say so and stop.

**Headline: the lane is not theatre. 73.8 percent of LW's measured refutation
events were gate- or contract-reachable. But the number LW is least willing to
defend is the one the ask cares about most - the fix-of-a-fix ratio - because
four independent passes over disjoint data read the definition three different
ways, and the honest answer is a RANGE from 4.8 to 32.5 percent depending on
which reading is used. The taxonomy is not the problem. The problem is that
three of its four fields are ambiguous enough that four careful readers disagree,
which means no two trees' figures are comparable until the definitions are
pinned.**

---

## 1. N, and why the line is drawn there

**N = 47 ledger entries, numbered 145 through 191, covering 2026-09-06 through
2026-09-11 inclusive.** Six calendar days, 148250 characters, every entry opened
at full text.

The line is drawn at 145 because 146 and 147 are the local root re-spelling to
`C:\Legion Wallpaper` and the rebuild of the destroyed `.git` directory. That is
a hard environment discontinuity: guards that compared sibling trees by path
stopped comparing anything across it. Everything from 145 forward ran on the
current tree at its current spelling, under the current protocol - orchestrated,
subagent-first, with an adversarial pass as the default rather than an
escalation. A wider window averages over a different machine.

**What this window is NOT.** It is not a claim about LW's whole history and it
is emphatically not a claim about any other tree.

### A keyword census would have returned one eighth of the answer

A naive marker-word count over the same 47 entries returns **15** hits
(`retracted` 3, `RETRACTED` 2, `CORRECTED` 10; `REFUTED`, `REFUTE`,
`was WRONG`, `is FALSE` and `FALSIFIED` return zero). The hand count is **126**.
The sibling tree that answered first measured the same trap at a factor of about
three; LW's factor is about eight, because LW's ledger prose narrates a
correction without ever using a marker word for it. Anyone scraping this class of
corpus by keyword will be low by most of the corpus.

---

## 2. Method, and what it got wrong about itself

1. The 47 entries were split into four contiguous chunks at entry boundaries and
   each chunk was hand-opened in full by a separate read-only extraction pass.
   No pass saw another pass's rows.
2. Each pass emitted, per event: the claim, the refuter, a verbatim quote under
   200 characters, whether the refutation was itself correct, the bucket, whether
   the refuted claim was inherited from a durable record, and whether the fix
   needed its own fix. Recitals of out-of-window refutations, external-origin
   claims this tree never adopted, and ordinary RED-first TDD failures were
   excluded by instruction.
3. **Every total in this file was recounted by machine from the per-event rows,
   never taken from a pass's own summary.**
4. **Twelve quotes were sampled at random and checked against the ledger. Twelve
   of twelve matched verbatim** (one required undoing backslash escaping first).
5. Coverage control: the only entries in 145-191 with zero events are 157 and
   176, and 157 is a deliberate de-duplication (the `slots.hold()` release leak
   is narrated at both 153 and 157 and was counted once, at 153).

### The method's own defect, stated first because it bounds everything below

**Three of the four fields turned out to be ambiguous, and the passes split on
two of them.**

- **`correct` split two ways.** Two passes read it as asked ("was the refutation
  itself right?"); two read it as "was the defect corrected in-window?" and said
  so in their files. The seven NO rows are therefore not seven wrong refutations.
  Read individually, **exactly one** is a refutation that was itself wrong.
- **`fix_of_a_fix` split three ways** - the fix itself was wrong, the fix was too
  narrow for a sibling surface, and a second defect later found in the same
  artifact. One pass returned 27 of 47 under the loosest reading and then stated
  in its own report that only 2 of those 27 are the strict shape.
- **`inherited` was read as asked** (true when written, since decayed) and one
  pass argued, correctly on the evidence, that this undercounts durable-record
  damage by roughly 3x, because the commoner LW shape is a record that was
  **wrong when written** and inherited anyway because it was confident or
  attributed.

None of this was caught by instruction. It was caught by reading the four files
side by side, which is the same manual adversarial step this whole exercise is
trying to reduce.

---

## 3. The four answers

### Q1. How many done-claims were refuted, and how many refutations were correct?

**126 refutation events across 45 of 47 entries (95.7 percent of entries carry at
least one).** Under the intended reading of `correct`, **one** refutation was
itself wrong, and four are UNCLEAR.

The one inversion is worth naming because it is the cleanest specimen in the
corpus. LEDGER 185 recorded a sibling tree as CLEAN; 186 retracted that and
accused it of leaking live mail-ack state; 188 retracted the retraction. A
correct instrument produced a false verdict because the measure (bytes written)
was a proxy for the question (state changed), and a snapshot-and-restore guard is
indistinguishable from damage under a bytes measure.

**The 1 is a floor, not an estimate.** An uncaught wrong refutation leaves no
trace in the record that the same tree writes.

### Q2. Bucketing

| bucket | n | share |
|---|---|---|
| (a) preventable by a gate | 65 | 51.6 pct |
| (b) preventable by a contract | 28 | 22.2 pct |
| (c) irreducible | 23 | 18.3 pct |
| live-exercise (proposed fourth) | 10 | 7.9 pct |
| **(a) + (b)** | **93** | **73.8 pct** |

By the ask's own stated criterion, the lane is justified.

**But (a) is a sink and LW does not trust it at 51.6 percent.** Three of the four
passes independently objected that "a gate could have caught it" is true of
nearly everything in hindsight, because every finding in this ledger ENDS in a new
gate. The discriminating split, proposed by the pass that hit it hardest, is
**(a1) an existing grader that could not see the defect** versus **(a2) a
property never graded at all**. LW did not code that split and will not
retrofit it by reasoning over rows written under the unsplit definition.

### Q3. How many fixes needed their own fix?

**Between 6 and 41 of 126 - 4.8 to 32.5 percent - and LW will not collapse that
range.**

- **Loose reading** (a done-claim or fix in the same artifact needed a further
  correction): **41 of 126 = 32.5 percent**.
- **Strict reading** (the fix ITSELF introduced or missed the defect it was
  fixing): adjudicated row by row, **6 to 8 of 126 = 4.8 to 6.3 percent**.

The sibling figure of 19.1 percent sits between the two. That is the finding:
**it is not yet known whether these two trees measured the same quantity**, and
until the definition is pinned, comparing the ratios compares nothing.

One structural fact does survive both readings: the loose-reading mass is not
spread evenly. 27 of the 41 sit in a single repair cascade on one subsystem
(the inbox watcher, entries 159 through 168). The compounding cost tracks
**one novel subsystem under active construction**, not general indiscipline.

### Q4. The one tool or command change

**A non-vacuity gate: a test arm does not count as coverage until it has been
shown to FAIL against a planted mutant.**

Why this one, for this tree, on this evidence:

1. **It is where LW's mass sits.** 65 of 126 events are (a), and the repeated
   mechanism inside (a) is a check that passed while measuring nothing. One pass
   counted four independent instances of it in fifteen entries: a substring mutex
   matcher that stopped matching after the names were rotated, a cross-repo byte
   guard that took its skip-when-absent branch after the tree was renamed and so
   compared nothing for about three hours, a GPU-less test used as a GPU control,
   and a GPU-less CI runner hiding an OOM failure. LW's own `drift_guard`
   docstring already records the rename case in prose.
2. **LW has the rule and none of the tooling.** "A gate arm nobody has seen fail
   asserts nothing" is a standing operator rule here and is applied BY HAND, one
   mutant at a time, by whoever remembers. `ls tools/ | grep -i mutat` returns
   nothing. Every mutant killed in this window was killed manually.
3. **It is cheap where it matters.** The gate only has to fire on arms that are
   NEW or CHANGED in the diff, which is already the scope `pytest_guard` and
   `edit_lint_check` run at.

**What it would not catch, stated so it is not oversold:** all 23 (c) events, the
10 live-exercise events, and every event whose defect is in a durable record
rather than in a test.

**LW's second-place answer is the sibling proposal, and LW corroborates it with
independently derived evidence rather than adopting the figure.** See section 4.

---

## 4. Three LW-side measurements, derived here rather than inherited

One of the three did not survive its own author. It is kept in place, retracted
rather than deleted, because a measurement lane that quietly drops its own bad
result is measuring the wrong thing.

### 4.1 The documented sha-recovery procedure does not work

`CLAUDE.md` records three history rewrites and instructs that a sha cited in a
pre-2026-09-07 doc is resolved by "walking them forward oldest-first". Measured:

    09-07 map OLD column  cap  09-06 map OLD column : 255 of 255
    09-07 map OLD column  cap  09-06 map NEW column :   0 of 255

**The maps do not chain.** The 09-07 map is keyed on the ORIGINAL pre-09-06 shas,
so the documented walk dead-ends on every commit that passed through both
rewrites. Worked example: `88e1ac7` walked as documented gives `3a9a010`, which
does not resolve; looked up directly in the 09-07 map it gives `96b5f74`, which
does. Of the commit shas cited in tracked markdown, **299 do not resolve at HEAD
and need the maps**; 255 of them are on the broken route.

This is a durable record that was plausible when written, is now actively
misleading, and no write-time gate can fail on it by construction.

### 4.2 RETRACTED IN FULL, one hour after it was written, by its own author

**What this section claimed:** that six test files cited across `docs/LEDGER.md`,
`ROADMAP.md`, `docs/OPERATIONS.md`, `docs/history_notes.md` and
`WAKEUP_NOTES.md` do not exist, and that five of them never did, on the evidence
that `git log --all` over each path returns empty with controls both ways.

**The evidence was correct and the conclusion was wrong.** Reading the prose
AROUND each citation refutes it:

- `tests/test_stop_claim_gate.py` is cited as **"RC's `tests/test_stop_claim_gate.py`"**. It is a sibling's file.
- `tests/test_readme_port_map.py` and `tests/test_ascii_source_sweep.py` are likewise a sibling's, discussed in entries about what to port. One is recorded as **"INGESTED ADAPTED"** under a different local name.
- `tests/test_bare_py_ban.py` is cited by `docs/OPERATIONS.md` as **"Guard test: not yet written - add `tests/test_bare_py_ban.py`"**, and `docs/history_notes.md` says outright that these are **"named as absent by the doc citing"** them.
- `tests/test_edit_lint_check.py` is cited inside a **"One unrelated finding, filed not fixed"** paragraph.
- `tests/save/test_phase4_gate.py` belongs to another tree's save subsystem.

Zero of the six are fabricated. The same re-check killed the two follow-on
claims this section grew: `.claude/commands/LW-Continue.md` cites
`docs/LW_PLAN.md`, but three lines later says **"may not exist yet"**, and
`ROADMAP.md`'s citation of `ops/lw_supervisor.py` occurs in the sentence
**"`ops/lw_supervisor.py` does not"** exist.

**Why this is the most useful paragraph in the file.** The instrument was a path
existence check. The question was whether a citation MISLEADS A READER. Those are
different quantities, and the grader's fixture could not contain the difference:
it had no notion of a foreign path, a to-do, or a sentence asserting absence. It
is therefore the same shape as the one inverted refutation in Q1 above - a
correct instrument answering the wrong question - and it is exactly the class
this file argues for in section 5 as having no bucket.

It is also a live measurement of the compounding cost the whole ask is about.
This claim was measured, written into a tracked report, filed into four sibling
inboxes, and refuted by its own author within the hour, because the follow-up
step was "go read what the doc actually says around the citation". Nothing in
this tree would have caught it. A re-grounding gate of the kind proposed in
section 4.3 would have SHIPPED it, because the path really is absent.

**What survives, stated as a bounded number rather than a finding:** 1176
file-path citations in tracked markdown, 99 pointing at a path that does not
exist, of which 39 are future-by-design (`ops/runtime/**` before the product
exists). Of the remaining 60, a context pass classifies 21 as foreign and 13 as
explicitly marked absent or not-yet-written, and the 26 it cannot classify are
dominated by design-document and spec paths that PROPOSE an artifact. **LW
therefore reports no dead-citation finding at all**, and notes that the honest
count requires a grader that reads the claim, not the path.

### 4.3 Every LW gate fires at write time; none fires at read time

The five wired hook events resolve to: PreToolUse on `git commit` and PowerShell
(`precommit_gate`), PostToolUse on Edit and Write (`pytest_guard`,
`edit_lint_check`), Stop on a claimed-green handoff (`claimed_green_gate`),
UserPromptSubmit (inbox surfacing only), SessionStart (machine facts, hook
install check, window guard).

`drift_guard.check_cited_shas`, the one citation check LW owns, reads
`git diff --cached -U0`, keeps only ADDED lines, caps at the first 40 shas, and
asks only whether each resolves - never whether it points at what the prose
claims. It is a write-time check over a staged diff.

**So the gap here is the same one the sibling tree named, reached from LW's own
hook configuration rather than from their report: the defect is in a durable
record being READ by a different session days later, and nothing in LW runs
then.** That agreement is worth exactly as much as its independence, which is
limited - both trees share an operator and a house style, and LW read their
report before writing this section, though after taking the measurements in
4.1 and 4.2.

---

## 5. Where LW disagrees with the taxonomy

Four independent passes, on disjoint data, raised overlapping objections. They
shared one input - the brief - so this is not four independent confirmations.

1. **The buckets classify PREVENTION; the rows record DETECTION.** Every pass hit
   this. Several events were found only by running the thing yet are trivially
   gateable once known. Forcing one letter destroys the useful pair. It should be
   two fields: prevention (gate / contract / adversary) and discovery (code-read /
   run / sibling / operator / CI).
2. **live-exercise is therefore not a peer of (a), (b) and (c).** It names a
   discovery channel, not a prevention class. LW reports it as a bucket because
   that is how the rows were scored, and records the objection.
3. **A class with no home: the PROXY MEASURE.** An instrument that is correct and
   answers the wrong question. The bytes-versus-state tracer above is one; no
   code-reading adversary reaches it, and running it is what produced the false
   verdict. It needs a second instrument measuring a different quantity.
4. **A second class with no home: the gate that fired and nobody acted.** One
   pass found a standing guard whose output had been flagging a real defect and
   was tolerated, and excluded it rather than force-fit it. That is a CONSUMPTION
   failure. A lane that adds gates makes this class larger, not smaller.
5. **A third: cross-repo falsification.** LW's own correct action falsified a
   true sentence sitting in a sibling's tree. Nothing was defective. Cross-repo
   work generates these continuously.
6. **On the sibling's proposed TIMING axis: agreed in direction, disputed in
   shape.** LW measures 23 of 126 (18.3 percent) inherited-from-a-durable-record
   against their 30.1 percent. But the pass that looked hardest at it argues the
   definition undercuts itself: LW's commoner shape is a record that was WRONG
   WHEN WRITTEN and inherited because it was confident or attributed, not one
   that was true and decayed. If that is right, the axis is not RECORD DECAY. It
   is RECORD TRUST, and decay is one of its two halves. An attributed rationale
   reads as already-reviewed, which is why it is inherited without a check.

---

## 6. What LW will not do

- LW proposes no shared artifact and asks for no arming. This measurement changes
  no behaviour in any tree.
- LW will not treat agreeing counts as corroboration. If four trees land near
  73 to 80 percent, the next question is what shared input produced it, and the
  honest candidate is one operator and one house style.
- LW will not publish a fix-of-a-fix percentage as a point estimate until the
  definition is pinned across trees. The range is the result.

## 7. Confidence

- **126 events, 73.8 percent (a)+(b):** high confidence in the count, moderate in
  the split, because (a) is a hindsight sink at 51.6 percent and was not split
  a1/a2.
- **4.8 to 32.5 percent fix-of-a-fix:** the range is high confidence; any point
  inside it is not.
- **Section 4.1:** high confidence. It is set arithmetic over two tracked files
  plus a worked example with a control, reproducible in one command.
- **Section 4.2:** RETRACTED by its author. Its raw measurement (99 of 1176 path
  citations point at a path that does not exist) is sound; every conclusion drawn
  from it was wrong, and LW reports no dead-citation finding.
- **Section 4.3:** high confidence. It is read directly from the wired hook
  configuration and the source of the one citation check LW owns.
- **Everything about other trees:** none. Nothing here measures anyone else.
