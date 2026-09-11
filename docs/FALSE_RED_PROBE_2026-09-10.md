# False-RED probe: LW's suite with git off PATH (2026-09-10)

LW ran RC's reproduction on its own tree rather than static-reading its call
sites. This file is the method and the measurement, so the numbers can be
re-derived by someone who was not here.

## Why

RC audited its own tree on 2026-09-08 and reported a result against itself:
115 external-binary call sites, 39 correct, **39 FALSE-RED risk**, 4 false-green
risk, 33 not applicable. The structural half is the part that generalises:

> a 2116-line machine guard against false-GREEN skips and NOTHING against
> false-RED, and that guard is STRUCTURALLY BLIND to the dominant defect,
> because it audits skip CONDITIONS and an ungated
> `subprocess.run([...], check=True)` has no skip to inspect.

RSC's converging finding is the rule it violates: there are THREE dispositions,
not two. The tool ran and found nothing is a true skip; the tool ran and broke
is a FAIL; **the tool is not present at all is a true skip, not a FAIL**. LW hit
the same root cause in production code on 2026-09-08 (`tools/lw_model_pins.py`,
four states, ABSENT never reads as verified - LEDGER 178).

LW's static counts predicted exposure: 102 `subprocess` call sites across
`tools/` (39), `ops/` (9) and `tests/` (54), 10 of them passing `check=True`,
against only 9 `shutil.which` guards in the whole tree.

## Method

`tools/lw_false_red_probe.py`, run from the repo root:

    python tools/lw_false_red_probe.py

1. Copy the environment and drop every `PATH` entry that holds a `git`
   executable.
2. **Assert the stripped environment really cannot resolve git** before
   measuring anything. A stripper that quietly left git reachable would report
   zero false-RED sites and be believed - the false-GREEN failure mode of a
   false-RED probe, and the reason `tests/test_false_red_probe.py` exists.
3. Run the full suite twice, once in each environment, into
   `ops/runtime/false_red_probe/`.
4. Report the DELTA. A test that fails with git present is not this probe's
   finding, so the result is `failing_no_git - failing_with_git`, by test id.

Running it on a mid-session tree is a measurement error, not a result: the two
arms must see the same code. The first attempt here compared an early tree
against a later one and was discarded.

## Measurement, 2026-09-10, Legion, Python 3.14

    with git      exit 0    2865 passed,   18 skipped              157s
    without git   exit 1      15 failed, 2783 passed, 57 skipped,
                              28 errors                            125s

    NEW failures/errors attributable ONLY to git being absent:  43

By file:

    tests/test_git_hooks_gate.py          21
    tests/test_loop_executor.py            9
    tests/test_no_split_identity.py        2
    tests/test_no_account_paths.py         2
    tests/test_no_secret_literals.py       2
    tests/test_lw_facts_inbox.py           2
    tests/test_mojibake_hygiene.py         1
    tests/test_lw_next_session_guard.py    1

The with-git arm reads 2865 rather than the 2870 the session ends on: the probe
ran before its own three arms, and before the two tool-set-parametrised arms
that this session's new `tools/` files add, existed. Both arms of the probe saw
the same tree, which is the only comparison it makes.

## What the numbers say

**43 arms report RED for a tool that is simply not installed.** Not one of them
is a defect in the thing under test. On a machine without git, LW's identity,
secret and mojibake sweeps - the guards that exist to keep a public repo clean -
announce failure rather than "could not check", and a reader who cannot act on a
red suite learns to ignore red. That is the cost, and it is the same cost RSC
named from the other direction.

**The mirror direction is measured too, and it is the good news.** Skips rose
from 18 to 57: 39 arms already degrade correctly when git is gone. The tree is
not uniformly broken, it is uniformly UNGRADED, which is why a count was worth
having.

**Why it is latent.** CI and Legion both ship git, so none of this has ever
fired in anger. Latent is not absent - it is the same shape as LW's MS-SSIM arm,
silent for 719 audits and load-bearing all along.

**Why the sweeps are the interesting cluster.** Seven of the 43 are the
tracked-corpus sweeps, which select their corpus with `git ls-files`. Their
`test_the_sweep_selects_a_real_corpus` arms exist specifically so an empty
corpus cannot pass vacuously - a false-GREEN guard. Under a missing git they
convert straight into a false RED. One conflation, both directions, in arms
written to prevent exactly this.

## The repair, and the measurement after it

Repaired the same day. `tests/gitdep.py` answers ONE factual question - can this
machine resolve a git executable - and every call site decides for itself what
that answer means there. It is not a sweep and not a matcher: widening one
matcher over 43 sites is the move RSC's charter names as the wrong response
after the second defeat, and it would have relocated the conflation rather than
closing it. Three site shapes, chosen per file by what the file actually does:

    module-level pytestmark   test_git_hooks_gate.py - all 21 arms build a real
                              repository with `git init`, so the marker is not
                              over-skipping. Measured, not assumed.
    fixture-level skip        test_loop_executor.py - only 9 of its 35 arms need
                              git, and they reach it through the `worktree_pair`
                              fixture, which is why they arrived as ERRORs in
                              setup rather than FAILEDs in the test
    per-arm decorator         the eight remaining files - 13 arms, each named,
                              the rest of each file untouched

What the repair deliberately does NOT do: a git that IS installed and then fails
is still a FAIL. `gitdep` only knows about absence.

    BEFORE   without git   15 failed, 2783 passed, 57 skipped, 28 errors   -> 43
    AFTER    without git       0 failed, 2794 passed, 101 skipped, 0 errors -> 0
    AFTER    with git      exit 0, 2877 passed, 18 skipped

**The repair is graded behaviourally, not by reading conditions.**
`tests/test_git_absence_is_a_skip.py` runs one representative node per repaired
file TWICE - once with git stripped, once with git present - and asserts SKIP
then RUN. That mirror arm is the whole point: a marker that always skips
satisfies the absence half perfectly and grades nothing, which is the
false-GREEN trap sitting directly behind this false-RED one. A third arm asserts
the skip reason names git, because a reason a reader cannot act on is not a
reason.

Five mutants, one per repair shape plus both halves of the primitive, all
KILLED, each restored byte-exact: the shared marker never skipping, the
module-level `pytestmark` removed, the fixture-level skip removed, one decorated
arm undecorated, and the imperative form never skipping.

**One more measurement error worth recording, since it is the same one twice.**
The first post-repair probe reported 2 remaining failures - both timing-sensitive
concurrency arms, neither git-related. It had been run while a mutation harness
was hammering the same box. Re-run uncontended, both pass and the count is 0. A
probe on a contended machine is no more a result than a probe on a mid-session
tree.

## What is NOT being claimed

The 0 is a count of arms that go RED for a missing git. It is NOT a claim that
every external-binary dependency in the tree is now graded: `gitdep` knows about
git and about absence only. LW has 102 subprocess call sites and other binaries
behind some of them, and no equivalent probe has been run for any of those.

Nor is it a claim that a git-less machine is a good place to trust this suite.
83 more arms skip there, and a skip is an ungraded arm - the disposition is now
TRUE, which is all the three-disposition rule promises.
