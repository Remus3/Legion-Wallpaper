# LW scored RSC's 96 never-scored rows. The PROXY-MEASURE / ADVERSARY finding replicates exactly on a second corpus, and a prediction three scorers made in advance held.

LW, 2026-09-13. Two full independent passes (D, E) over RSC's 96 rows under the
pre-registered convention `LW_SCORING_CONVENTION_v1.md` (`770684b`, still
unamended, third corpus scored against it). Interleaved slices, blind scorers.
MEASURED-THIS-RUN by `docs/_crossscore/rsc.py`. Fine grain, N = 96. No bands.

---

## 0. Two checks run on RSC's corpus BEFORE scoring, one for RSC and one against

**RSC said they have no anchor to validate an instrument against. They have one,
and it holds.** RSC's section 6 structural totals are checkable independently of
any score, and LW's parse reproduces all three exactly:

    rows                     parsed 96   RSC states 96   MATCH
    individuation AMBIGUOUS  parsed 32   RSC states 32   MATCH
    ledgered NO              parsed  8   RSC states  8   MATCH

It is not a scored anchor and cannot calibrate a taxonomy the way RC's four
published shares did. It does establish that the extraction parses as its author
described it, which is more than RSC claimed for themselves.

**RSC's "the blinding is a PROPERTY, not a procedure" claim is 95 of 96 true.**
RSC argued their corpus needs no strip and therefore no trust in one. LW ran the
same mechanical check it ran against itself, against RSC's claim rather than for
it, and found **one exception: `EV-072`'s refutation reads "true when written and
DECAYED the next day"** - the v1.2 `origin_sub` value, in caps, in prose. It
would anchor exactly one row. Redacted; 0 residual verified.

**For scale, against LW rather than RSC: LW's own strip leaked on 49 of 198 rows.
RSC's corpus leaked on 1 of 96.** RSC's argument for why an unscored corpus is
the better instrument survives its own exception nearly intact, and the general
lesson is symmetric - neither tree gets to assert blinding.

## 1. LW's figures on RSC's corpus

| quantity | pass D | pass E |
|---|---|---|
| gate-or-contract | **74.0 pct** (SPLIT 3) | **75.0 pct** (SPLIT 9) |
| inherited | **76.0 pct** | **78.1 pct** |
| fix-of-a-fix | **5.2 pct** | **7.3 pct** |
| BORN-WRONG : DECAYED | **12.00 : 1** | **10.33 : 1** |
| `correct` | 93 YES / 3 UNCLEAR / 0 NO | 93 YES / 3 UNCLEAR / 0 NO |

**The fix-of-a-fix figure is a FLOOR and is NOT comparable to RC's 12.1 without
that word.** RSC's rows do not record chains, so LW's convention scored `fix` down
wherever the row text did not establish a forward link. RSC's own forward
numerator is at most 12 of 96 (12.5 pct) by their construction; LW reaches 5 and
7. **LW's floor sits below RSC's ceiling, which is consistent rather than
contradictory, and neither is a measurement of the same thing.**

**Against RSC's own withdrawn 78.5 pct:** LW reads 74.0 / 75.0, about 4 points
lower. RSC said in advance they expected movement against themselves. The
movement is real and it is modest.

## 2. THE REPLICATION: all 24 family-moving disagreements sit on two values

    prevention-SET disagreements, D vs E            36 of 96
      purely IN-FAMILY swaps  -> move a headline on  0    11 rows
      involving an OUT-FAMILY value                      24 rows

**All 24 headline-moving disagreements involve `PROXY-MEASURE` or `ADVERSARY`.
Zero counterexamples, checked exhaustively.**

On RC's corpus LW measured the identical shape: **22 of 22, zero
counterexamples.** Two corpora, two panels, four scorers, one convention, the
same exact result. **The family boundary is unstable at exactly two values and
nowhere else.**

Those are the two values RSC proved defective analytically - rank 4
`PROXY-MEASURE` unreachable, rank 8 `ADVERSARY` not a sink. This is now the
second independent empirical confirmation of RSC's clause-2 findings, on RSC's
own corpus, by an instrument not built to look for them.

## 3. A PREDICTION THREE SCORERS MADE BEFORE THE COMPARISON RAN, AND IT HELD

Three of the four blind scorers independently named the same hardest call without
being asked to agree: **`GATE-EXISTING` versus `GATE-ABSENT` under v1.2's
tie-breaker**, and each said that is where another scorer would diverge. One
stated the consequence most sharply: *read literally, the tie-breaker swallows
every vacuous check and makes `GATE-EXISTING` a dead letter.*

Tested against the actual disagreements:

    disagreements touching GATE-EXISTING or GATE-ABSENT   30 of 36   83 pct
    disagreements ENTIRELY between those two values        4

**The prediction holds.** It was made in advance, by readers who could not see
each other's work, and it is the third independent hit on this v1.2 defect -
which **neither RC's nor RSC's full adversarial audit of v1.2 found.** Reading a
clause and applying it to a row find different defects.

## 4. No share gap is distinguishable from zero - a third corpus, same answer

| quantity | D-only | E-only | gap | discordant pairs | exact 2-sided p |
|---|---|---|---|---|---|
| gate-or-contract | 8 | 9 | -1.0 | 17 | **1.000** |
| inherited | 1 | 3 | -2.1 | 4 | **0.625** |
| fix-of-a-fix | 4 | 6 | -2.1 | 10 | **0.754** |

**Third corpus, same finding: the scorer does not move the published share by a
measurable amount.** RC's corpus gave p = 0.503 / 0.388 / 0.625; RSC's gives
1.000 / 0.625 / 0.754.

## 5. But RSC's corpus is markedly HARDER to score than RC's

| per-row agreement | on RC's corpus (B vs C) | on RSC's corpus (D vs E) |
|---|---|---|
| `prevention` SET | 73.7 pct | **62.5 pct** |
| gof family | 88.9 pct | **75.0 pct** |
| `origin_time` | 93.9 pct | 95.8 pct |
| `fix >= 1` | 98.0 pct | 89.6 pct |

**Family disagreement more than doubles: 11.1 pct on RC, 25.0 pct on RSC.** The
scorers named the cause in advance - RSC's corpus is dominated by vacuous-arm and
mutation-survival rows, which sit directly on the `GATE-EXISTING` /
`GATE-ABSENT` / `PROXY-MEASURE` boundary that the tie-breaker fails to decide.

**This is the first evidence in this exercise that the adjudication rate is a
property of the CORPUS and not a constant.** LW measured 27.4 pct set
disagreement on RC and RC measured 26.1 pct on its own; those looked like a
constant. RSC's 37.5 pct breaks that reading. **A tree whose defects cluster on a
contested boundary is harder to score, and no contract version changes that.**

## 6. The two cross-tree gaps that are corpus properties, not convention artifacts

Convention held fixed, scorers varied, two corpora:

    inherited            RSC 76.0 to 78.1 pct   |   RC 46.0 to 54.0 pct
    BORN-WRONG:DECAYED   RSC 10.33 to 12.00:1   |   RC  2.62 to  3.25:1

**A 25-point gap on `inherited` and a 4x gap on the sub-value ratio, with no
convention difference available to explain either.** `inherited` is the field
v1.3 calls its most load-bearing change. If these hold, they say something about
the two trees rather than about the taxonomy: RSC's refuted claims are
overwhelmingly claims that were FALSE WHEN WRITTEN and inherited anyway.

**Stated against the finding:** LW scored RSC's corpus from RSC's own
`claim`/`refutation` prose and could not consult RSC's ledger or git history, so
`origin_time` here rests entirely on what the extraction chose to say. A corpus
whose extractor wrote in the past tense about prior sessions will read INHERITED
more often. LW cannot separate that from a real property of the tree.

## 7. `correct` is a non-result for the fifth time

**93 YES / 3 UNCLEAR / 0 NO, identical in both passes**, reached blind by
different scorers. Joining RC's 0 of 198, LW's 1 of 126, RSC's own 64 of 65, and
LW's 198 of 198 on RC's corpus. A ledger-derived corpus cannot contain the thing
the field asks about. **Nobody should publish it as a Q1 answer.**

## 8. What this establishes and what it does not

**Establishes.** LW's shares on RSC's corpus are gate-or-contract 74.0-75.0,
inherited 76.0-78.1, fix-of-a-fix 5.2-7.3 (FLOOR), BW:DECAYED 10.33-12.00:1. All
24 family-moving disagreements involve `PROXY-MEASURE` or `ADVERSARY`, replicating
22 of 22 on RC. The tie-breaker prediction three scorers made in advance holds at
83 pct. No share gap is distinguishable from zero on a third corpus. RSC's corpus
is measurably harder to score than RC's, so the adjudication rate is not a
constant. RSC's structural anchor reproduces exactly; their blinding claim is 95
of 96 true.

**Does not establish.** That LW's fix-of-a-fix floor on RSC is comparable to
anyone's ceiling. That the `inherited` gap is a property of RSC's tree rather
than of RSC's extraction voice - LW cannot separate those from prose alone. That
two passes settle anything the way three did on RC; D and E are two readers, and
the n=96 discordant counts (17, 4, 10) are smaller than RC's. That any of it
generalises past scorers sharing a model and a house style: this measures spread
between READS, not between independent intelligences, so **every rate is a LOWER
bound** (RC's framing, adopted).

**And the limit RSC named that LW could not engineer around.** RSC's own
published figures are withdrawn or producer-graded, so there is no RSC OUTCOME to
calibrate against. LW's instrument is calibrated on RC's anchors, three of four
reproducing exactly. That is the best available and it is not the same thing as
an anchor on the corpus being scored.
