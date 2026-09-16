---
description: Adversarial review of a FINISHED change before it ships - isolated finders trying to break it, a skeptic pass that kills unproven findings, and a gate that only skeptic-confirmed BLOCKERs may hold. Use before committing substantial work, at lane close-out, or when asked for an adversarial / red-team review of a diff or branch. /blast-radius is the implementer's own pre-commit side of the same line.
---

> **SUBAGENT-FIRST (standing protocol, operator 2026-06-20).** Always use subagents for substantive work; do not build solo in the main thread.
> 1. **Spec first:** a Plan/design subagent (or the Gemini director) emits the spec/plan BEFORE any code; verify it vs ground truth (grep cited file:line, live `ops/runtime/health.json` + the product live-state endpoint (TBD - product not yet defined), git) - never scaffold on assumptions.
> 2. **New session:** interview the Gemini director (or the operator if Gemini is down) for intent + acceptance criteria, re-probe live state, THEN build.
> 3. **Act via subagents:** worktree-isolated build agents on disjoint files (sole merger) + a read-only `verifier` subagent gate before any merge or "done".
> 4. Trivial one-line cosmetic edits may inline (refines R9). See `CLAUDE.md` "Subagent-First Protocol" + memory `feedback_subagent_first_protocol`.

# Adversarial review

Reviewers whose job is to find what is WRONG with a change before it ships -
not to summarize it, not to appreciate it. Isolated finders, a skeptic pass
that separates proven defects from plausible ones, and a gate that only
skeptic-confirmed blockers may hold.

This does NOT replace the SUBAGENT-FIRST `verifier` gate; it sits inside it.
`verifier` answers "is the claim true" (files on disk, counts, git, CI).
This answers "is the change wrong" - a different question, and the one LW's own
refutation census says goes unasked: GATE-ABSENT beats GATE-EXISTING 2.2 to 1.

## 1. When it runs

- **Floor: before committing substantial work.** The implementing session
  reviews its own change before the commit.
- **Close-out: the orchestrator reviews the lane.** In a headless orchestrated
  run the merger (or its delegated `verifier`) runs this against the lane's
  branch before merge. The implementer never has the last word on its own work.

**Always substantial in this tree, never overridable by the implementer's
judgment:** anything touching `tools/lw_pipeline.py` (the single writer of
pipeline state), the `pipeline_state.json` or manifest schema, a gate threshold
or the gate ladder, `.githooks/` or the hook config, `ops/loop/slots.py` or
`ops/loop/winmutex.py` (byte-identical-by-contract with the sibling tree), a
scheduled `LW-*` task, or anything that deletes or moves image bytes.
Otherwise the implementing session judges, biased toward reviewing when unsure:
a skipped review is a silent decision that the change could not bite.

## 2. Composition: three finders, isolated

Three reviewers that NEVER see each other's reasoning - isolation is what makes
agreement between them mean anything. Each loads the diff, the defect-class
checklist (section 5), and nothing of the others' output.

**Execution shape follows where this runs.** In the main loop, launch the
finders as parallel subagents. Running AS a delegated subagent, run the finder
passes SEQUENTIALLY in one context: a nested subagent's completion does not
re-invoke a parent subagent, so a spawn-and-wait reviewer there stalls.
Sequential passes keep isolation between PASSES rather than between processes -
a fresh angle per pass, no shared candidate list until the skeptic.

1. **The correctness finder.** Logic, edge cases, error paths, invariants. The
   defect-class checklist is its opening moves, not its limit.
2. **The fitting lens.** One perspective matched to the change:
   - **data integrity / irreversibility**: copy-verify-delete moves, manifests,
     hashes, append-only logs; anything that can lose an image byte.
   - **compatibility / schema**: `pipeline_state.json`, manifests, the
     `PIPELINE_LOG.md` line format; anything a TOLERANT reader will silently
     ignore instead of rejecting.
   - **concurrency**: per-image locks, atomic tmp+replace writes, two loops
     running at once, a scheduled task firing mid-write.
   - **gate honesty**: does the gate still FAIL on the thing it exists to
     catch, or did the change make it vacuous?
   - **public-repo disclosure**: account paths, keys, emails, capability or
     unfixed-defect prose. LW is PUBLIC (ADR-012).
   - **conventions**: the diff against LW's OWN documented standards - CLAUDE.md
     hard rules, `docs/adr/`, the ASCII rule, the tier rules. Reads this repo's
     documents, never an imported checklist.

   State the pick in the report. A change fitting no lens well still gets its
   best fit: a second pair of eyes with a stated angle beats a second
   correctness pass.
3. **The spec axis.** The diff against the originating ROADMAP item, ADR or
   operator ask: requirements missing, half-done, wrongly done, plus scope
   nobody asked for. No spec? THE GAP IS A LINE IN THE REPORT, and the other
   two finders proceed. The spec axis never invents requirements.

Finders READ code and RUN proofs but modify nothing - no edits, no commits, no
state mutation beyond what a test run inherently does. Proofs may read
`ops/runtime/*.json` and may run the suite; they may NOT move image bytes,
write pipeline state, or push.

## 3. The skeptic pass

Findings from a finder are hypotheses, not evidence. **Every finding above a
NIT goes to a skeptic whose brief is to KILL it**: re-read the code, run the
disproof, find the guard the finder missed. Only findings the skeptic fails to
kill stand in the report; killed ones drop to the dismissed bucket with the
reason they died. A NIT skips the skeptic and reports as style advice.

The skeptic is `.claude/agents/verifier.md` in **Skeptic mode** - the same
read-only agent LW already gates on, given a different brief. Not a second
agent, and not a second protocol.

**BLOCKER rank requires a runnable reproduction the skeptic confirmed - rung 4
or 5.** No repro, no blocker: it ranks MAJOR at most, stated as UNPROVEN. That
is what keeps the gate honest. Nothing blocks a commit on a hunch, and a
BLOCKER in the report is a defect you can watch happen.

### The evidence ladder

Finders and skeptics grade every claim - finding and clean bill alike - in one
language. Same five rungs, same spelling, as `/blast-radius` and
`.claude/agents/verifier.md`.

1. **Asserted.** The reviewer said so. Worthless on its own.
2. **Cited.** A real `file:line`, or the library's own source.
3. **Traced.** The failure path (or the guard that stops it) walked step by
   step, and it holds.
4. **Run.** A script or test that calls the real code and fails loud if the
   claim is wrong.
5. **Reproduced.** Watched happen in the running system.

Nothing is rounded up: a claim whose proof stopped at rung 3 is REPORTED at
rung 3. A citation is rung 2, the floor to count at all. Moving a load-bearing
claim one rung further is usually one small script that calls the exact code in
question, so a verdict that stops at "plausible" without trying that script has
stopped early.

### Skeptic judgment

Disproof runs are the skeptic's first move, not its whole brief. Three filters
catch findings that survive a re-read and still are not defects:

- **Nitpick gravity.** Reviewers fill their review: a finder short on real
  defects inflates nits to fill the space. A pass whose findings are all nits
  is EVIDENCE THE CHANGE IS PROBABLY FINE, and the report says so plainly
  instead of dressing the nits up.
- **Hypothetical vs actual.** "What if the caller passes None" is a finding only
  if a caller actually can. Trace the call site: validated upstream, or ruled
  out by construction, kills it at rung 3 - EXCEPT at a trust boundary. JSON on
  disk, a filename, EXIF, an API response and an operator-typed argument are
  not closed by a type annotation; there the kill needs runtime validation on
  the path.
- **"I would have done it differently."** The most common false positive in
  review. A preference for another approach is not a defect; it dies unless it
  names a concrete problem with the code as written.

A kill under any filter is recorded with its reason, same as a kill by
disproof.

## 4. The report and the gate

- Findings ranked **BLOCKER / MAJOR / MINOR / NIT**, each with a citation
  (`file:line` plus the failing scenario, plus the repro for blockers), its
  skeptic outcome (confirmed, or surviving-unproven for a downgraded would-be
  blocker), and the rung its proof reached. A finding without a citation does
  not count.
- **The composition:** which lens ran and why, and whether the spec axis had a
  spec.
- **The clean bill:** what was specifically checked and found CORRECT, each
  with its rung. A clean bill on a named hazard is as durable as a finding - it
  stops the next reviewer re-litigating settled ground.
- **The dismissed bucket:** every finding the skeptic killed, one line each -
  the claim, what killed it, the rung the kill reached. This is a trust
  mechanism, not residue.

Axes are reported separately and NEVER blended into one verdict. No overall
score to hide behind.

**The gate:** a confirmed BLOCKER is fixed before the commit (floor) or the
merge (close-out). Only the OPERATOR may waive one, with the reason recorded in
`docs/LEDGER.md`. The implementer never waives its own blocker; the orchestrator
surfaces it, never absorbs it. Everything below BLOCKER advises: each finding is
dispositioned, fixed or declined with a reason. A declined finding with lasting
consequence lands in CLAUDE.md's Settled section or a new ADR - that is what
stops the next review re-raising it.

**Do not loop the review until "clean."** Re-run after fixing what was found; a
re-run on an UNCHANGED diff generates new plausible-sounding findings
indefinitely. Two consecutive runs with nothing new confirmed is a stop signal,
not a challenge.

## 5. The defect-class checklist

`docs/DEFECT_CLASSES.md` holds the defect classes PROVEN in this repo. Every
finder loads it. The rules that keep it honest:

- **A class is admitted only via a live reproduction** - a defect that actually
  occurred, here, reproduced. An imported checklist checks for someone else's
  bugs.
- **The fixing session proposes the class in the same commit that fixes the
  defect**, so the class lands with its proof.
- **A class is removed only by an extinction sweep** - evidence the whole
  pattern is gone from the codebase, never "we have not seen it lately."

## Done when (checkable)

- Three isolated finders ran; the spec axis ran against a spec or reported
  no-spec; the lens pick is stated; every finding above NIT went through the
  skeptic.
- Every finding carries its citation and its rung; no claim reported above the
  rung its proof reached; every BLOCKER carries its confirmed repro.
- The dismissed bucket lists every kill with its reason and rung; clean-bill
  claims state theirs.
- Confirmed blockers are fixed, or waived by the operator on the record in
  `docs/LEDGER.md`. Lesser findings are each dispositioned.
- Any new defect class earned by this review is queued for the fixing commit,
  with its repro.

## Attribution

Adapted from `run/adversarial-review` in `timharris707/skills` (MIT), read at
commit `a9317e0` on 2026-09-16. The three-finder isolation, the nested-subagent
execution-shape rule, the skeptic pass, the repro-or-it-is-not-a-blocker bar,
the dismissed bucket, the clean bill, the never-blend-axes rule and the
defect-class admission rules are upstream's. Upstream in turn credits Matt
Pocock's code-review skill (MIT) for the spec axis and finder isolation, and
Lauren Tan's pstack `blast-radius` / `interrogate` (MIT) for the ladder and the
judgment filters - a grant that is DIRECTORY-SCOPED to `pstack/` (see
`/blast-radius`'s attribution for the measurement; the adapted material sits
inside the scoped directory). Adapted, not byte-copied, per ADR-013: the lens menu, the
always-substantial list, the proof limits and the waiver route are LW-specific,
upstream's `team-workflow` binding machinery and its relative skill links are
dropped, and upstream text is not 7-bit ASCII. Pinned by
`tests/test_review_protocol_contract.py`.
