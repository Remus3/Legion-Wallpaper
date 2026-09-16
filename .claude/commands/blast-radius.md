---
description: Find what an in-flight change breaks somewhere else, before it ships - past the diff and past where grep stops - and PROVE the one fact it is safe because of by running real code. Use when asked for the blast radius of a change, when deciding whether an in-flight change is safe to submit, or when reviewing a small diff you do not trust yet. This is the implementer's own pre-commit discipline; /adversarial-review is the reviewer's side of the same line.
---

> **SUBAGENT-FIRST (standing protocol, operator 2026-06-20).** Always use subagents for substantive work; do not build solo in the main thread.
> 1. **Spec first:** a Plan/design subagent (or the Gemini director) emits the spec/plan BEFORE any code; verify it vs ground truth (grep cited file:line, live `ops/runtime/health.json` + the product live-state endpoint (TBD - product not yet defined), git) - never scaffold on assumptions.
> 2. **New session:** interview the Gemini director (or the operator if Gemini is down) for intent + acceptance criteria, re-probe live state, THEN build.
> 3. **Act via subagents:** worktree-isolated build agents on disjoint files (sole merger) + a read-only `verifier` subagent gate before any merge or "done".
> 4. Trivial one-line cosmetic edits may inline (refines R9). See `CLAUDE.md` "Subagent-First Protocol" + memory `feedback_subagent_first_protocol`.

# Blast radius

Find what a change breaks somewhere else, before it ships. Listing the callers
is not the job - any agent can grep those in a second. The job is the breakage
grep will not show you.

This runs on YOUR OWN work while it is still yours, before or during the
change, pre-commit. `/adversarial-review` is the other side of the line: it
reviews a FINISHED change with isolated finders and a skeptic gate.

## The writeup is not the deliverable

A blast-radius writeup that sounds right is worth nothing on its own. It reads
as convincing whether or not it is true, and that is the trap - it is the same
trap LW measured on its own record, where GATE-ABSENT refutations beat
GATE-EXISTING 2.2 to 1 and 62.9 pct of refuted claims were INHERITED from a
durable record that read as settled. The deliverable is the proof: find the one
fact the change's safety depends on (occasionally two; then each gets the same
treatment) and get it proven by running code. Words are where you start, not
what you hand back.

## The evidence ladder

Push each safety fact as far down this ladder as is cheap, and SAY WHERE IT
STOPPED. These five rungs are spelled the same way here, in
`/adversarial-review`, and in `.claude/agents/verifier.md` - one grading
language, no second spelling.

1. **Asserted.** You said so. Worthless on its own.
2. **Cited.** A real `file:line`, or the library's own source.
3. **Traced.** The failure path (or the guard that stops it) walked step by
   step, and the bad case does not reach.
4. **Run.** A script or test that calls the real code and fails loud if you are
   wrong.
5. **Reproduced.** Watched happen in the running system.

Any safety fact that stops short of rung 4 is said out loud as UNPROVEN, never
written up as settled, and never rounded up. Rung 4 is usually one small script
that imports the same module the pipeline ships and calls the exact function
you are worried about.

## Steps

1. **Read the change.** The working diff, the symbols it adds, changes and
   deletes, and what it now does differently - including the part the diff does
   not spell out. Mid-change, before any commit, read the working diff and the
   branch's commit messages.
2. **Find the one fact it is safe because of.** Most changes that look scary
   are safe because of a single fact ("this only ever re-reads an already
   hash-verified manifest and writes nothing"). Find that fact. If it holds,
   most of the scary cases die at once. Spend your time here, not on a long
   list of maybes.
3. **Look where grep stops.** In this tree that is a short, concrete list:
   the `pipeline_state.json` schema the monitor reads TOLERANTLY (an unknown
   field is ignored, so a rename is silent); the append-only `PIPELINE_LOG.md`
   line format; the SHA-256 manifests; the multi-venv split (`.venv-upscale`,
   `.venv-metrics`, `.venv-gen`, `C:\Tools\lw-clean\venv` - a change to a
   shared module is read by interpreters this suite never imports); the
   `ops/loop/slots.py` + `ops/loop/winmutex.py` pair that is
   BYTE-IDENTICAL-by-contract with the sibling tree; the git hooks under
   `.githooks/`; and anything a scheduled `LW-*` task runs unattended.
4. **Grade each risk honestly.** Real chance of happening, real cost if it
   does. Keep the risks you confirmed; list the ones you checked and CLEARED
   separately. Cite a real `file:line`, treat a search that finds nothing as an
   answer worth recording, and never invent a caller or an API.
5. **Prove the one fact.** Write the script or test, run it, paste what
   happened. If you cannot prove it cheaply, mark it unproven. Never round up.
6. **Escalate a wide change.** When the change is big or touches many seams,
   finish your own pass first, then hand it to `/adversarial-review`.

## What to hand back

- **What it does.** Including the part that is not obvious.
- **The one fact it is safe because of.** State it, name the rung it reached,
  show the proof. If you could not prove it, write UNPROVEN.
- **Risks.** Only the real ones. Each names how it breaks, the `file:line`, how
  likely, how bad, and how to check.
- **Cleared.** What you checked and why it is fine.
- **Before you submit.** The cheapest test or repro that catches the real bug,
  including the script you wrote.

Keep the prose 7-bit ASCII (CLAUDE.md hard rule) and strip anything private -
this repo is PUBLIC.

## Done when (checkable: verify each line before reporting complete)

- The one fact the change is safe because of is stated in a single sentence
  with the ladder rung it reached; two facts get two sentences and two rungs.
- Every safety fact that stopped short of rung 4 is labeled UNPROVEN; none
  reads as settled.
- Every kept risk carries a real `file:line`, a likelihood, a cost, and a way
  to check it.
- Cleared items sit in their own list, apart from confirmed risks.
- At least one place grep stops (step 3's list) was actually read, or the
  writeup says why none applies.
- The rung-4 script, where one exists, appears in the writeup with its pasted
  output.

## Attribution

Adapted from `run/blast-radius` in `timharris707/skills` (MIT), read at commit
`a9317e0` on 2026-09-16. The evidence ladder, the one-fact discipline, the
steps and the hand-back shape are upstream's, kept intact. Upstream in turn credits Lauren
Tan's pstack `blast-radius` (MIT). **That grant is DIRECTORY-SCOPED and LW
records it as such** (RC found it 2026-09-16, LL independently, LW verified):
`cursor/plugins` carries NO licence at its root - the API reports none and
LICENSE / LICENSE.md / LICENSE.txt all 404 - and the MIT grant exists only at
`pstack/LICENSE`, "Copyright (c) 2026 Lauren Tan". The material LW adapted sits
in `pstack/skills/blast-radius/`, INSIDE the scoped directory, so the
adoption is covered; it is recorded here because a reader checking the root
would find nothing and conclude the wrong thing. Adapted,
not byte-copied, per ADR-013: upstream's relative links to `plainspoken`,
`adversarial-review` and `orchestrate` are remapped or dropped because LW took
two skills and not the pack, upstream text is not 7-bit ASCII, and step 3's
seam list is LW-specific. Pinned by `tests/test_review_protocol_contract.py`.
