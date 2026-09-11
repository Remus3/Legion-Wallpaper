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

## What is NOT being claimed

No repair shipped with this probe. Fixing 43 sites is a per-site application of
the three-disposition rule, not a matcher and not a sweep - RSC's own charter
already records that widening a matcher is the wrong response after the second
defeat. The count is the deliverable; the repair is a ROADMAP item.
