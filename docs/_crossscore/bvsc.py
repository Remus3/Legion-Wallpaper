"""B vs C in full: the only pairing in LW's design that isolates the scorer.

Same convention, same redaction, same interleaving, different reader. Reports
the paired (McNemar) structure rather than the raw share gap, because a share
gap of 2.0 points on 198 rows is 4 rows and the question is whether 4 rows is
distinguishable from zero.
"""
import collections
import math
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import tally  # noqa: E402

B, C = {}, {}
for s, n in (("B0", 50), ("B1", 50), ("B2", 49), ("B3", 49)):
    B.update(tally.load_psv(HERE / f"scored_{s}.psv", n))
for s, n in (("C0", 50), ("C1", 50), ("C2", 49), ("C3", 49)):
    C.update(tally.load_psv(HERE / f"scored_{s}.psv", n))
rc = tally.load_rc()
rcn = {k: tally.rc_norm(v) for k, v in rc.items()}
ids = sorted(B)
assert set(B) == set(C) == set(rc)
N = len(ids)


def two_sided_binom(b, c):
    """Exact two-sided binomial p on the b+c discordant pairs, H0: p=0.5."""
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    tail = sum(math.comb(n, i) for i in range(0, k + 1)) / (2 ** n)
    return min(1.0, 2 * tail)


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (100 * max(0.0, c - h), 100 * min(1.0, c + h))


print(f"=== B vs C, n = {N} rows, scorer isolated\n")

print("--- 1. PAIRED STRUCTURE OF EACH SHARE (McNemar table)")
print("    b = rows B says yes and C says no;  c = the reverse.")
print("    The share gap is (b - c) / N. Discordant pairs are b + c.\n")
preds = {
    "gate-or-contract": lambda d, k: d[k]["gof_derived"] == "TRUE",
    "inherited": lambda d, k: d[k]["orig"] == "INHERITED",
    "fix-of-a-fix": lambda d, k: d[k]["fix"] >= 1,
}
for name, fn in preds.items():
    b = sum(1 for k in ids if fn(B, k) and not fn(C, k))
    c = sum(1 for k in ids if fn(C, k) and not fn(B, k))
    both = sum(1 for k in ids if fn(B, k) and fn(C, k))
    neither = N - both - b - c
    gap = 100 * (b - c) / N
    p = two_sided_binom(b, c)
    lo, hi = wilson(b, b + c)
    verdict = ("NOT distinguishable from zero" if p > 0.05
               else "distinguishable from zero")
    print(f"  {name}")
    print(f"    both {both:3d}   neither {neither:3d}   B-only {b:2d}   C-only {c:2d}")
    print(f"    share gap {gap:+.1f} pts on {b+c} discordant pairs, "
          f"exact two-sided p = {p:.3f}  -> {verdict}")
    if b + c:
        print(f"    of the discordant pairs, B says yes "
              f"{100*b/(b+c):.0f} pct [95 pct CI {lo:.0f} to {hi:.0f}]")
    print()

print("--- 2. IS EITHER SCORER SYSTEMATICALLY HARSHER? (prevention set size)")
for nm, d in (("B", B), ("C", C)):
    sizes = collections.Counter(len(r["prev"]) for r in d.values())
    multi = sum(v for k, v in sizes.items() if k > 1)
    print(f"  {nm}: singleton {sizes[1]:3d}  multi-value {multi:3d}  "
          f"SPLIT rows {sum(1 for r in d.values() if r['gof_derived']=='SPLIT'):2d}")

print("\n--- 3. THE 52 prevention-SET DISAGREEMENTS, characterised")
dis = [k for k in ids if B[k]["prev"] != C[k]["prev"]]
print(f"  rows where the SET differs: {len(dis)} of {N} "
      f"({100*len(dis)/N:.1f} pct)")
nested = [k for k in dis if B[k]["prev"] < C[k]["prev"] or C[k]["prev"] < B[k]["prev"]]
disjoint = [k for k in dis if not (B[k]["prev"] & C[k]["prev"])]
overlap = [k for k in dis if k not in nested and k not in disjoint]
print(f"    NESTED   (one set contains the other): {len(nested):3d}  "
      f"{100*len(nested)/len(dis):.0f} pct of disagreements")
print(f"    DISJOINT (no value in common):         {len(disjoint):3d}  "
      f"{100*len(disjoint)/len(dis):.0f} pct")
print(f"    PARTIAL  (overlap but neither nests):  {len(overlap):3d}  "
      f"{100*len(overlap)/len(dis):.0f} pct")
print("\n  most common DISJOINT swaps (B set -> C set):")
sw = collections.Counter(
    (",".join(sorted(B[k]["prev"])), ",".join(sorted(C[k]["prev"])))
    for k in disjoint)
for (x, y), n in sw.most_common(8):
    print(f"    {x:34s} -> {y}   x{n}")

print("\n--- 4. WHICH VALUES DRIVE THE DISAGREEMENT")
print("  value: rows where exactly one of B/C assigns it")
drift = collections.Counter()
for k in ids:
    for v in B[k]["prev"] ^ C[k]["prev"]:
        drift[v] += 1
for v, n in drift.most_common():
    inb = sum(1 for k in ids if v in B[k]["prev"] and v not in C[k]["prev"])
    inc = n - inb
    print(f"    {v:20s} {n:3d}   (B-only {inb:3d}, C-only {inc:3d})")

print("\n--- 5. DO THE DISAGREEMENTS CLUSTER? (by RC's filed value)")
print("  RC filed value      rows   B/C set differs   rate")
by = collections.defaultdict(lambda: [0, 0])
for k in ids:
    by[rcn[k]["prev"]][0] += 1
    if B[k]["prev"] != C[k]["prev"]:
        by[rcn[k]["prev"]][1] += 1
for v, (tot, d) in sorted(by.items(), key=lambda x: -x[1][0]):
    print(f"    {v:20s} {tot:4d}   {d:9d}      {100*d/tot:5.1f} pct")

print("\n--- 6. FAMILY disagreements, listed (the 22 that move a headline)")
fam = [k for k in ids if B[k]["gof_derived"] != C[k]["gof_derived"]]
print(f"  {len(fam)} rows:")
for k in fam:
    print(f"    {k:12s} B {B[k]['gof_derived']:5s} "
          f"{','.join(sorted(B[k]['prev'])):28s} | "
          f"C {C[k]['gof_derived']:5s} {','.join(sorted(C[k]['prev']))}")

print("\n--- 7. WHEN B AND C AGREE, DO THEY AGREE WITH RC?")
agree = [k for k in ids if B[k]["prev"] == C[k]["prev"]]
hit = sum(1 for k in agree if rcn[k]["prev"] in B[k]["prev"])
hit_d = sum(1 for k in dis
            if rcn[k]["prev"] in B[k]["prev"] or rcn[k]["prev"] in C[k]["prev"])
print(f"  rows where B and C AGREE      {len(agree):3d}: "
      f"RC's value is in that set {hit:3d}  ({100*hit/len(agree):.1f} pct)")
print(f"  rows where B and C DISAGREE   {len(dis):3d}: "
      f"RC's value is in EITHER set {hit_d:3d}  ({100*hit_d/len(dis):.1f} pct)")
print("  THAT SECOND FIGURE IS BIASED AND MUST NOT BE READ AS A FINDING:")
print("  on a disagreement row there are TWO sets to hit, so it gets two")
print("  draws against RC's one value. The unbiased comparison holds the")
print("  number of draws fixed at one, using each scorer separately:")
for nm, d in (("B", B), ("C", C)):
    a = sum(1 for k in agree if rcn[k]["prev"] in d[k]["prev"])
    x = sum(1 for k in dis if rcn[k]["prev"] in d[k]["prev"])
    print(f"    scorer {nm}: on AGREE rows {100*a/len(agree):5.1f} pct, "
          f"on DISAGREE rows {100*x/len(dis):5.1f} pct  "
          f"-> {100*x/len(dis) - 100*a/len(agree):+.1f} pts")
print("  A row the two LW scorers cannot agree on is a row EITHER of them is")
print("  markedly less likely to reach RC's value on. That is the signature of")
print("  a HARD ROW, not of one scorer being wrong.")
