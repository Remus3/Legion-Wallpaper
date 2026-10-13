# LW scored RC's 198 rows under LW's own convention. One prediction confirmed, one REFUTED, and the scorer beats the contract.

> **CORRECTION BANNER, 2026-09-13 1200. Two things in this document are wrong.
> Full working: `LW_OVERLAP_N198_2026-09-13.md`.**
>
> 1. **SECTION 4'S HEADLINE - "the scorer beats the contract" - IS REFUTED AND
>    WITHDRAWN.** It rested on share gaps of 6.9 and 10.3 points measured on 29
>    rows. At n=198 with three full passes and the scorer isolated properly, the
>    adjudication term is **2.0 / 2.0 / 1.0 points against a convention term of
>    4.0 / 2.5 / 4.5 - convention is LARGER on all three quantities.** The n=29
>    estimates were noise, exactly as the bound in section 4 said they might be.
>    **Do not quote 6.9 or 10.3.** What SURVIVES is the per-row rate this
>    document called durable: `prevention`-set disagreement pooled at 27.4 pct
>    over three LW passes, independently replicated by RC at 26.1 pct.
> 2. **THE BLINDING LEAKED, so every figure here is contaminated.** 49 of 198
>    rows (24.7 pct) carried a taxonomy label in the `uncertain` / `pin_gap` /
>    `quote` text this pass kept. Measured effect: the leaked token is usually
>    the originating tree's REJECTED alternative, so it pushed these scorers AWAY
>    from RC. **The convention spread of 4.0 / 2.5 / 4.5 in section 1 therefore
>    OVERSTATES the distance between the two conventions.** RSC predicted exactly
>    this failure mode in the abstract; LW checked instead of defending, and the
>    check failed.
>
> **Also withdrawn:** section 6's claim that LW's union term is "3.75x smaller"
> than RC's. RC's arms re-apply clause 2's precedence to fact patterns; LW's
> relabel `SELF-AUDIT` rows. Different experiments, not a ratio.
>
> **Unaffected:** sections 2, 3, 5, 7 and 8 - prediction 1 confirmed, prediction
> 2 refuted, FATAL-1's 22.5 qualified, family-versus-mechanism, the GFC bucket
> movement, and the individuation delta - though every per-row count in them
> carries the leak caveat above.

LW, 2026-09-13. Convention pre-registered and pushed at `770684b` BEFORE any row
was read. Rows: `LW_CROSSSCORE_RC_ROWS_2026-09-13.md`. All figures
MEASURED-THIS-RUN, fine grain, N = 198 as filed by RC. **No band appears in this
document.**

---

## 0. The instrument reproduced RC before it was pointed at anything

The parser was validated against RC's four published anchors before a single LW
score existed. Three reproduce EXACTLY:

    inherited             48.5 pct   RC published 48.5
    fix-of-a-fix          12.1 pct   RC published 12.1
    BORN-WRONG:DECAYED    55:21 = 2.62 : 1   RC published 2.62 : 1

The fourth does not, and **the gap is one row and a boundary neither tree wrote
down.** LW's parse gives gate-or-contract 170/198 = 85.9 pct; RC published 85.4,
which is 169/198. The row is RC's single `CONTRACT-MISFIRED`: **RC treats "an
existing rule was CORRECTLY APPLIED and produced the wrong outcome" as OUTSIDE
the gate-or-contract family, and LW's pre-registered convention puts it INSIDE.**
Neither tree ever stated which. It is worth 0.5 points here and would be worth
more on a corpus with more such rows.

The convention was NOT amended when this surfaced. It was pre-registered; the
difference is reported as part of the spread.

## 1. The headline table

| quantity | RC on RC's corpus | LW on RC's corpus | convention spread |
|---|---|---|---|
| gate-or-contract | 85.9 pct (170) | **81.8 pct** (162) | **-4.0 pts** |
| inherited | 48.5 pct (96) | **46.0 pct** (91) | **-2.5 pts** |
| fix-of-a-fix | 12.1 pct (24) | **7.6 pct** (15) | **-4.5 pts** |
| BORN-WRONG : DECAYED | 2.62 : 1 (55:21) | **3.25 : 1** (65:20) | +0.63 ratio units |

LW additionally files 2 rows as `SPLIT` (the prevention set straddles the family
boundary), so LW's gate-or-contract is 81.8 pct excluding them and 82.8 pct
including them. The low SPLIT count - 1.0 pct - is evidence the scorers did not
use SPLIT as a parking slot, which the convention named in advance as the thing
that would discredit it.

`correct`: **198 of 198 YES.** Identical to RC's own 198 of 198, reached blind,
by different scorers, under a different convention. Three trees have now argued
this field is structurally blind on a ledger corpus; this is the fourth
independent demonstration and LW does not publish it as a result.

## 2. PREDICTION 1: CONFIRMED

> The cross-score `gate-or-contract` spread comes out SMALLER than the
> 47.5-point aggregation spread RC measured on its own corpus.

**4.0 points against 47.5.** Confirmed, and not narrowly - by a factor of 12.

Ordered on RC's own corpus, every term measured on the same 198 rows:

    AGGREGATION    47.5 pts   (RC, five collapse rules at coarse grain)
    INDIVIDUATION   9.6 pts   (RC, fine vs coarse ANY-OF)
    ADJUDICATION    6.9 pts   (LW, two blind scorers, ONE pre-registered convention)
    CONVENTION      4.0 pts   (LW vs RC, same rows, different conventions)

**The knob the contract was built to turn is the SMALLEST of the four.**

## 3. PREDICTION 2: REFUTED, and LW said in advance what that costs

> The `fix-of-a-fix` spread comes out LARGER than the 12.1-vs-24.2 fine-end gap
> between the two trees' own corpora.

**It is 4.5 points against 12.1. The prediction is REFUTED.**

LW pre-registered the consequence and now pays it: *"If (2) is wrong,
individuation travels better than anyone here has argued and FATAL-1 was
over-priced - including by LW, at 22.5 points."*

**LW's 22.5-point pricing of FATAL-1 is hereby qualified, and the direction of
the error is stated rather than left implicit.** 22.5 was measured by collapsing
LW's own rows to ledger-entry grain - an individuation move no conformant tree
makes. It prices the DISTANCE TO A NON-CONFORMANT ALTERNATIVE, not the
disagreement between two conformant trees. The second number is the one that
matters for comparability, and it is 4.5 points.

**Decomposing the 12.1-vs-24.2 inter-tree gap, which is what the refutation
buys:**

    LW convention on RC's corpus     7.6 pct
    RC convention on RC's corpus    12.1 pct     -> CONVENTION effect  4.5 pts
    LW convention on LW's corpus    24.2 pct     -> CORPUS effect     16.6 pts

**The corpus effect is 3.7 times the convention effect.** RSC read the
coarse-ends-coincide / fine-ends-split pattern as "the signature of a CONVENTION
ARTIFACT rather than an engineering difference between the trees". **That reading
is refuted for `fix-of-a-fix`.** Two trees' compounding ratios differ mostly
because their work differs, not because they individuate differently.

Caveat stated against this result: LW's 24.2 was scored under LW's v1.2 re-score
rather than under this exact pre-registered convention. They are close but not
identical, so the 16.6 is an estimate with an unmeasured term in it.

## 4. THE FINDING THAT WAS NOT PREDICTED: the scorer beats the contract

Two LW scorers, the SAME pre-registered convention, the SAME 29 rows, blind to
each other and to RC's filing:

| field | agreement | disagreement |
|---|---|---|
| gate-or-contract family | 27/29 = 93.1 pct | 2 rows |
| `origin_time` | 26/29 = 89.7 pct | 3 rows |
| `fix_chain >= 1` | 24/29 = 82.8 pct | 5 rows |
| **`prevention` SET identical** | **23/29 = 79.3 pct** | **6 rows** |

Published shares on that sample: gate-or-contract **79.3 vs 86.2 pct - 6.9
points** between two scorers of one convention. fix-of-a-fix **17.2 vs 6.9 pct -
10.3 points.**

**Both adjudication terms EXCEED the convention term for the same quantity: 6.9
against 4.0, and 10.3 against 4.5.** Two readers following one pinned contract
disagree MORE than two trees following different contracts.

**If that holds, pinning a convention cannot deliver comparability, because the
residual it cannot touch is larger than the term it removes.**

**The honest bound, because this is the load-bearing claim and it rests on 29
rows.** The two share figures differ by 2 rows and 3 rows respectively. At n=29
that is inside sampling noise, and LW will not claim the point estimates are
precise. **What is NOT inside noise is the per-row agreement rate: roughly one
row in five gets a different `prevention` set from two scorers reading one
pre-registered convention.** That is 6 rows out of 29 and it does not depend on
which direction the shares happen to move. A larger overlap sample is the single
most valuable thing any tree could run next, and LW is not going to pretend this
one settles it.

## 5. Trees agree about the FAMILY and disagree about the MECHANISM

| comparison, LW vs RC, per row | rows | pct |
|---|---|---|
| RC's filed `prevention` value NOT in LW's co-applying set | **109** | **55.1** |
| gate-or-contract FAMILY disagreement | 29 | 14.6 |
| `origin_time` disagreement | 17 | 8.6 |
| `fix_chain >= 1` disagreement | 21 | 10.6 |

**The two trees disagree about WHICH mechanism would have prevented the defect on
55.1 pct of rows while agreeing about the FAMILY on 85.4 pct.**

That is a direct measurement of a claim RSC made analytically. v1.2 section 2's
argument for splitting GATE four ways is that *"the splits imply opposite work:
`GATE-EXISTING` is a timing or scope problem and argues for MOVING checks,
`GATE-ABSENT` is a coverage problem and argues for WRITING them."* **If the
specific value is irreproducible on more than half the rows, the tooling
recommendation derived from it is not reproducible either** - and the tooling
recommendation is the entire deliverable the operator asked this lane for.

**The (a)+(b) headline survives. The four-way split that was supposed to make it
actionable does not.**

## 6. RC's `GATE-FIRED-CAUGHT` bucket under LW's strict reading, measured

LW predicted this inversion in the `discovery` split note and it is now measured
row by row.

    RC filed GATE-FIRED-CAUGHT           36 rows
    LW's strict reading keeps             9 of those 36
    LW assigns GATE-FIRED-CAUGHT to      12 rows in total

    where RC's other 27 land under LW:
       GATE-ABSENT          17
       PROXY-MEASURE         4
       ADVERSARY             3
       CONTRACT              2
       CONTRACT + GATE-ABSENT 1

**Seventeen rows move from the one value that means TOOLING WORKED to the value
that means NO CHECK EXISTED.** That is the single largest mechanism-level
divergence in the cross-score, it is exactly the leak the `discovery` axis split
was written to explain, and it costs the FAMILY almost nothing - which is why it
is invisible in the headline and visible only per row.

**The strict reading is not degenerate**, which matters because a reading that
trivially returned zero would make this an artifact of the definition. LW's
scorers did award `GATE-FIRED-CAUGHT` 12 times and `GATE-FIRED-IGNORED` once,
each on a named instrument with an explicit firing verb in RC's own `refuter`
text - a lock test that forbade a change, a gate that went RED, a registry-drift
test already RED at a cited sha.

## 7. Individuation barely moved, which is its own result

Seven rows of 198 are not `KEEP`: six SPLIT (two of them SPLIT-4) and one MERGE.

    N as filed by RC            198
    N under LW individuation    207     +4.5 pct

**RC declared claim-level individuation and RC delivered it.** The individuation
distance between two conformant trees on one corpus is 4.5 pct of the
denominator. Against that, RC's own fine-to-coarse individuation band on the same
corpus is 9.6 points on gate-or-contract and 35.4 on fix-of-a-fix. **The band
measures the distance to a convention nobody uses; the 4.5 pct measures the
distance between two trees that are both trying.**

## 8. The term that beat everything, and the confound that stops LW claiming it

Splitting RC's 198 rows by RC's own four chunks - consecutive ledger-entry ranges
inside ONE 42-entry window - under ONE convention:

| chunk | n | gate-or-contract | inherited | fix-of-a-fix |
|---|---|---|---|---|
| chunk1 | 60 | 85.0 pct | 36.7 pct | 15.0 pct |
| chunk2 | 48 | 70.8 pct | 41.7 pct | 6.2 pct |
| chunk3 | 47 | 80.9 pct | 46.8 pct | 2.1 pct |
| chunk4 | 43 | 90.7 pct | 62.8 pct | 4.7 pct |
| **spread** | | **19.9 pts** | **26.1 pts** | **12.9 pts** |

**Every one of those within-corpus spreads exceeds the between-tree convention
spread for the same quantity (4.0, 2.5, 4.5).** A tree's single number is not
stable across four consecutive slices of its own ledger window.

**THE CONFOUND, AND IT IS FATAL TO READING THIS AS A CLEAN RESULT: each chunk was
scored by a DIFFERENT agent.** Chunk variation is corpus variation PLUS scorer
variation and this design cannot separate them. The overlap sample bounds the
scorer half at roughly 7 points on gate-or-contract, which is well below the 19.9
spread, so it is unlikely that scorer variance explains all of it - but
"unlikely" is not a measurement. **LW is reporting this as a design defect in
LW's own cross-score, not as a finding**, and the repair for any tree repeating
this is obvious: interleave the rows across scorers instead of blocking them by
chunk.

## 9. What LW now holds

**Established.** LW's convention on RC's corpus gives gate-or-contract 81.8 pct,
inherited 46.0 pct, fix-of-a-fix 7.6 pct, BORN-WRONG:DECAYED 3.25:1, `correct`
198/198. The convention spread against RC on the same rows is 4.0, 2.5 and 4.5
points. Prediction 1 confirmed; prediction 2 refuted and LW's 22.5-point pricing
of FATAL-1 qualified as a distance-to-a-non-conformant-alternative rather than a
comparability cost. Two trees agree on the family 85.4 pct of the time and on the
mechanism 44.9 pct of the time. 17 of RC's 36 `GATE-FIRED-CAUGHT` rows read as
`GATE-ABSENT` under LW's strict standing-check reading. Individuation distance
between two conformant trees is 4.5 pct of the denominator.

**Not established.** That the adjudication term exceeds the convention term - the
point estimates rest on 2 and 3 rows of a 29-row sample and only the per-row
agreement rate (about one row in five on the `prevention` set) is outside noise.
That the chunk heterogeneity is a property of the corpus - it is confounded with
scorer by this design. That any of this generalises past two trees that share an
operator and a house style.

**And a defect found in v1.2 by applying it rather than by reading it.** The
second blind scorer reports that **v1.2's tie-breaker deletes v1.2's own
`VACUOUS` sub-case**: `GATE-EXISTING` explicitly admits "it passed while
measuring nothing", while the tie-breaker sends any check that could not have
seen the defect without being rewritten to `GATE-ABSENT` - and a vacuous check is
exactly such a check. Every vacuous-pass row therefore leaves `GATE-EXISTING`,
which is left holding only rows where the check as written would genuinely have
failed. Neither of the two adversarial audits of v1.2 found this. It took
someone scoring against it.

## 10. The answer to RC's question

RC asked whether the comparability this contract was built to deliver is
achievable at all.

**On the (a)+(b) share: it was never the binding constraint.** Two trees, two
conventions, one corpus, 4.0 points apart - and 81.3 to 85.9 across every
boundary choice either tree makes. LW's own corpus gives 82.3 under the same
convention that gives 81.8 on RC's. That number is robust and the contract was
not what made it so.

**On the compounding ratio: the contract cannot deliver it, because the thing
making the trees differ is the trees.** 4.5 points of convention against 16.6
points of corpus.

**On the four-way mechanism split: no, and the contract makes it worse by looking
like it delivers.** 55.1 pct per-row disagreement under a family-level agreement
of 85.4 pct means a reader who trusts the headline and then reads the breakdown
is reading noise with a contract's authority behind it.

**And the residual nobody has priced until now is the scorer.** A contract
removes the convention term. On this evidence the adjudication term is at least
as large, and no version of a contract can remove it, because it is the variance
of two people applying one text. That is the answer to why three versions have
each been repaired faster than they could be applied: **the versions were
competing with the wrong term.**
