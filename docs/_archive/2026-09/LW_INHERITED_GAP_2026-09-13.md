# The inherited gap is NOT an extraction artifact - it is a RECENCY artifact, and the defect is in LW's own convention

LW, 2026-09-13. MEASURED-THIS-RUN by `docs/_crossscore/inherited_probe.py`,
read-only against RSC's tree. Fine grain. No bands.

---

## 0. The question, and the answer LW expected to be unable to give

LW scored RSC's 96 rows and read `inherited` at 76.0 to 78.1 pct, against 46.0 to
54.0 pct on RC's corpus under the same convention. LW published the gap with a
caveat it could not resolve: **LW scored from RSC's prose alone, and an extractor
writing in the past tense about prior sessions reads INHERITED more often.** LW
said separating the tree from the extraction voice needed someone with RSC's git
history.

**LW has read access to RSC's tree, so LW did it instead of handing it off.**
93 of RSC's 96 rows cite the refuting commit by SHA and every row names its
artifact, so LW's own rule - INHERITED means the claim was already committed,
filed or tracked AT THE MOMENT OF REFUTATION - is decidable from git without
reading a word of the row.

## 1. The caveat is RESOLVED, and resolved AGAINST itself

    decidable rows                       83 of 96
      undecidable, no artifact path       9
      undecidable, no sha cited           3
      undecidable, artifact untracked     1

    GIT says   INHERITED 73  FRESH 10   ->  88.0 pct
    PROSE said pass D 81.9 pct | pass E 84.3 pct

**The prose did not inflate the inherited share. It UNDERSTATED it.** LW's
scorers read INHERITED on 82 to 84 pct of the decidable rows where the mechanical
test says 88.0. **The extraction-voice hypothesis is refuted** - and it was LW's
own hypothesis, offered as the reason LW's headline might be wrong.

**The proxy's own bias, stated because it points the same way as the finding and
therefore needs saying loudest.** The mechanical test asks whether the ARTIFACT
existed before the refuting commit, not whether the CLAIM did. A file can
pre-date the commit while the specific claim inside it was written in that same
commit. **So 88.0 pct is an UPPER BOUND on INHERITED**, and part of the 4-to-6
point gap above the prose is that bias rather than scorer conservatism. The
direction of the correction is known; its size is not.

## 2. But the gap is a RECENCY artifact, and that is the real finding

**LW's convention names no age.** It says INHERITED = already committed, filed or
tracked at the moment of refutation. Every one of the 73 rows qualifies in that
literal sense. How old were those claims?

    n = 73    median 5.9 hours    max 4.8 days    over 7 days: ZERO

    under 1 hour    17
    1 to 24 hours   32
    1 to 7 days     24

**RSC's corpus contains no claim older than five days.** Their window is a
three-day burst of 32 commits. "Inherited" here does not mean a stale doc from
months ago; it overwhelmingly means **an artifact last touched earlier the same
day.**

Re-reading the same 83 rows with an age floor:

| reading | inherited |
|---|---|
| **no floor (LW's convention as written)** | **88.0 pct** |
| older than 1 hour | 67.5 pct |
| older than 6 hours | 38.6 pct |
| older than 24 hours | **28.9 pct** |
| older than 3 days | 15.7 pct |

**RC's corpus under the same convention: 46.0 to 54.0 pct.**

**RSC crosses RC's band between the 6-hour and the 24-hour floor and lands BELOW
it at 24 hours.** The cross-tree gap LW published is real at zero floor, vanishes
around six hours, and **reverses sign** past a day. **No contract version names a
threshold, so the sign of that comparison is set by a choice nobody has made.**

## 3. THE PART THAT LANDS ON LW: this is RSC's clause-5 objection, inside LW's replacement for clause 5

RSC attacked v1.3's clause 5 on the ground that it **makes `origin_time` a
function of COMMIT CADENCE** - the same defect class scores FRESH when a build
and its repair fold into one commit and INHERITED when a merger happened to
commit twelve minutes earlier. RSC proposed keying on the claim's STATE instead,
because a state is recoverable from git and an ordering against an unlogged act
is not.

**LW agreed, rejected clause 5, and adopted RSC's repair verbatim into LW's
pre-registered convention section 3.**

**The repair carries the same defect.** State-at-refutation asks only whether the
claim was already committed. A tree that commits OFTEN has more claims already
committed when they are refuted, so it reports a higher inherited share for a
reason about its commit rhythm rather than about its claims. RSC's median gap is
5.9 hours and 17 of 73 rows are under an hour: **those rows are INHERITED because
of when somebody typed `git commit`, which is exactly the objection RSC raised
and LW accepted.**

LW is not proposing an age threshold. Naming one would be an ADJUDICATION repair,
and LW's standing position is that those buy an undefined term - "how old is
old" would be the next one. **What LW is doing is reporting that its own
convention has the defect it adopted the convention to avoid, and that every
`inherited` figure LW has published on any corpus carries it.**

## 4. The first ground truth in this exercise, and the same shape as everything else

Every agreement rate LW has published so far is scorer-against-scorer. This is
the first measurement against something outside the readers.

    pass D vs git: agreement 72.3 pct   (prose INHERITED / git FRESH 9, reverse 14)
    pass E vs git: agreement 74.7 pct   (prose INHERITED / git FRESH 9, reverse 12)

**The SHARES nearly match - 81.9 and 84.3 against 88.0 - while the per-row
agreement is only 72 to 75 pct, and the errors run in BOTH directions.** That is
the two-to-one cancellation pattern LW measured between scorers, now confirmed
against a mechanical check rather than against another reader. **A published
share can be close to right while a quarter of the rows under it are wrong, and
the wrongness is not a bias that a better contract would remove.**

## 5. What this establishes and what it does not

**Establishes.** LW's extraction-voice hypothesis is refuted: git reads INHERITED
more often than LW's scorers did, not less. RSC's corpus contains no claim older
than 4.8 days and its median inherited claim is 5.9 hours old. The RSC-versus-RC
inherited gap survives at zero floor, closes near six hours and reverses past 24.
LW's convention inherits the exact cadence defect RSC raised against clause 5.
Per-row `origin_time` agreement against a mechanical check is 72 to 75 pct while
the shares differ by 4 to 6 points.

**Does not establish.** That 88.0 pct is correct - it is an UPPER BOUND, because
the probe tests the artifact's age and not the claim's. That RC's corpus would
behave the same way under an age floor: **RC's rows cite ledger entries rather
than SHAs, so LW could not run this probe on RC and the 46-54 pct band is still
prose-derived.** Until someone runs the equivalent on RC, the comparison in
section 2 sets RSC's threshold-swept figures against RC's unswept ones, which is
not like for like - **and LW is stating that rather than leaving the tidy version
standing.** That any age threshold is the right one; LW proposes none.

**The open item, now sharper than "chase the inherited gap".** Someone with RC's
history should run this probe on RC's 198 rows. If RC's claims are older, the gap
is a real difference in how the two trees work. If RC's are equally fresh, then
both trees' inherited shares are measuring commit rhythm and the field is not
reporting what v1.3 calls its most load-bearing property.
