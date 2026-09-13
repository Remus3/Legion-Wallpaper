"""LW's two independent passes over RSC's 96 never-scored rows.

D vs E isolates the scorer: same pre-registered convention, same input, same
interleaving, different reader. Reports paired structure rather than bare share
gaps, because at n=96 a two-point gap is two rows.
"""
import collections
import math
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import tally  # noqa: E402

D, E = {}, {}
for s in ("D0", "D1"):
    D.update(tally.load_psv(HERE / f"scored_{s}.psv", 48))
for s in ("E0", "E1"):
    E.update(tally.load_psv(HERE / f"scored_{s}.psv", 48))
ids = sorted(D)
assert set(D) == set(E), "panel id sets differ"
N = len(ids)
print(f"=== LW on RSC's corpus, N = {N} rows, two independent passes\n")


def two_sided_binom(b, c):
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    return min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n)


def shares(d):
    g = 100 * sum(1 for r in d.values() if r["gof_derived"] == "TRUE") / N
    sp = sum(1 for r in d.values() if r["gof_derived"] == "SPLIT")
    i = 100 * sum(1 for r in d.values() if r["orig"] == "INHERITED") / N
    f = 100 * sum(1 for r in d.values() if r["fix"] >= 1) / N
    return g, sp, i, f


print(f"{'pass':10s} {'gate-or-contract':>17s} {'SPLIT':>6s} "
      f"{'inherited':>10s} {'fix-of-a-fix':>13s}")
for nm, d in (("LW pass D", D), ("LW pass E", E)):
    g, sp, i, f = shares(d)
    print(f"{nm:10s} {g:14.1f} pct {sp:6d} {i:7.1f} pct {f:10.1f} pct")

print("\n--- D vs E: paired structure (the scorer isolated)")
preds = {
    "gate-or-contract": lambda d, k: d[k]["gof_derived"] == "TRUE",
    "inherited": lambda d, k: d[k]["orig"] == "INHERITED",
    "fix-of-a-fix": lambda d, k: d[k]["fix"] >= 1,
}
for name, fn in preds.items():
    b = sum(1 for k in ids if fn(D, k) and not fn(E, k))
    c = sum(1 for k in ids if fn(E, k) and not fn(D, k))
    p = two_sided_binom(b, c)
    print(f"  {name:18s} D-only {b:2d}  E-only {c:2d}  "
          f"gap {100*(b-c)/N:+5.1f} pts on {b+c:2d} discordant pairs, "
          f"p = {p:.3f}  -> {'NOT' if p > 0.05 else ''} distinguishable from zero")

print("\n--- per-row agreement, D vs E")
for nm, fn in (("gof family", lambda k: D[k]["gof_derived"] == E[k]["gof_derived"]),
               ("origin_time", lambda k: D[k]["orig"] == E[k]["orig"]),
               ("origin_sub", lambda k: D[k]["sub"] == E[k]["sub"]),
               ("fix>=1", lambda k: (D[k]["fix"] >= 1) == (E[k]["fix"] >= 1)),
               ("prevention SET", lambda k: D[k]["prev"] == E[k]["prev"])):
    v = sum(1 for k in ids if fn(k))
    print(f"  {nm:18s} {v:3d}/{N}  {100*v/N:5.1f} pct agreement  "
          f"({100-100*v/N:.1f} pct disagreement)")

dis = [k for k in ids if D[k]["prev"] != E[k]["prev"]]
print(f"\n--- the {len(dis)} prevention-SET disagreements")
nested = [k for k in dis if D[k]["prev"] < E[k]["prev"] or E[k]["prev"] < D[k]["prev"]]
disj = [k for k in dis if not (D[k]["prev"] & E[k]["prev"])]
print(f"  DISJOINT {len(disj)}  NESTED {len(nested)}  "
      f"PARTIAL {len(dis)-len(disj)-len(nested)}")

OUTF = {"PROXY-MEASURE", "ADVERSARY"}
fam = [k for k in ids if D[k]["gof_derived"] != E[k]["gof_derived"]]
hit = [k for k in fam if (D[k]["prev"] | E[k]["prev"]) & OUTF]
print(f"\n--- FAMILY-MOVING disagreements: {len(fam)}")
print(f"  involving PROXY-MEASURE or ADVERSARY: {len(hit)} of {len(fam)}")
print(f"  counterexamples: {[k for k in fam if k not in hit] or 'NONE'}")
inonly = [k for k in dis if not ((D[k]["prev"] | E[k]["prev"]) & OUTF)]
print(f"  purely IN-FAMILY swaps: {len(inonly)} -> move a headline on 0 rows")

print("\n--- THE TIE-BREAKER PREDICTION, made by the scorers BEFORE this ran")
print("  Three scorers independently named GATE-EXISTING-vs-GATE-ABSENT under")
print("  v1.2's tie-breaker as the hardest call, and predicted it is where")
print("  another scorer would diverge. Testing that against the actual rows:")
TB = {"GATE-EXISTING", "GATE-ABSENT"}
tb = [k for k in dis if (D[k]["prev"] | E[k]["prev"]) & TB]
tb_only = [k for k in dis
           if D[k]["prev"] <= TB and E[k]["prev"] <= TB]
print(f"    disagreements touching GATE-EXISTING or GATE-ABSENT: "
      f"{len(tb)} of {len(dis)}  ({100*len(tb)/len(dis) if dis else 0:.0f} pct)")
print(f"    disagreements ENTIRELY between those two values:      {len(tb_only)}")

print("\n--- value-level drift (rows where exactly one pass assigns it)")
drift = collections.Counter()
for k in ids:
    for v in D[k]["prev"] ^ E[k]["prev"]:
        drift[v] += 1
for v, n in drift.most_common():
    ind = sum(1 for k in ids if v in D[k]["prev"] and v not in E[k]["prev"])
    print(f"    {v:20s} {n:3d}   (D-only {ind:3d}, E-only {n-ind:3d})")

print("\n--- prevention histogram, both passes (set members, sums > N)")
for nm, d in (("D", D), ("E", E)):
    h = collections.Counter(v for r in d.values() for v in r["prev"])
    print(f"  {nm}: " + "  ".join(f"{k}={v}" for k, v in h.most_common()))

print("\n--- origin_sub and correct")
for nm, d in (("D", D), ("E", E)):
    sub = collections.Counter(r["sub"] for r in d.values() if r["orig"] == "INHERITED")
    cor = collections.Counter(r["correct"] for r in d.values())
    bw, dc = sub["BORN-WRONG"], sub["DECAYED"]
    ratio = f"{bw/dc:.2f} : 1" if dc else "undefined"
    print(f"  {nm}: BORN-WRONG {bw}  DECAYED {dc}  OVER-GENERALISED "
          f"{sub['OVER-GENERALISED']}   BW:DEC {ratio}   correct {dict(cor)}")

print("\n--- individuation")
for nm, d in (("D", D), ("E", E)):
    nk = [(r["id"], r["indiv"]) for r in d.values() if r["indiv"] != "KEEP"]
    print(f"  {nm}: {len(nk)} rows not KEEP -> {nk}")
