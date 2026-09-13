"""Three full independent passes over RC's 198 rows under ONE convention.

A = LW's first pass  (chunk-BLOCKED slices, UNREDACTED input)
B = second pass      (INTERLEAVED slices, REDACTED input)
C = third pass       (INTERLEAVED slices, REDACTED input, different partition)

B vs C is the ONLY pairing that isolates the scorer: same convention, same
redaction, same interleaving, different people. A vs B and A vs C each mix
three differences and are reported as such.
"""
import pathlib
import sys
import collections

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
import tally  # noqa: E402

A = {}
for ch, n in (("chunk1", 60), ("chunk2", 48), ("chunk3", 47), ("chunk4", 43)):
    A.update(tally.load_psv(HERE / f"scored_{ch}.psv", n))
B = {}
for s, n in (("B0", 50), ("B1", 50), ("B2", 49), ("B3", 49)):
    B.update(tally.load_psv(HERE / f"scored_{s}.psv", n))
C = {}
for s, n in (("C0", 50), ("C1", 50), ("C2", 49), ("C3", 49)):
    C.update(tally.load_psv(HERE / f"scored_{s}.psv", n))
rc = tally.load_rc()
rcn = {k: tally.rc_norm(v) for k, v in rc.items()}
ids = sorted(A)
assert set(A) == set(B) == set(C) == set(rc), "pass id sets differ"
N = len(ids)
print(f"three full passes over N = {N} rows\n")


def shares(d):
    g = 100 * sum(1 for r in d.values() if r["gof_derived"] == "TRUE") / N
    i = 100 * sum(1 for r in d.values() if r["orig"] == "INHERITED") / N
    f = 100 * sum(1 for r in d.values() if r["fix"] >= 1) / N
    sp = sum(1 for r in d.values() if r["gof_derived"] == "SPLIT")
    return g, i, f, sp


rows = [("RC (own filing)",
         100 * sum(1 for v in rcn.values() if v["gof"] == "TRUE") / N,
         100 * sum(1 for v in rcn.values() if v["orig"] == "INHERITED") / N,
         100 * sum(1 for v in rcn.values() if v["fix"] >= 1) / N, 0)]
for nm, d in (("LW pass A", A), ("LW pass B", B), ("LW pass C", C)):
    g, i, f, sp = shares(d)
    rows.append((nm, g, i, f, sp))
print(f"{'pass':18s} {'gate-or-contract':>17s} {'inherited':>10s} "
      f"{'fix-of-a-fix':>13s} {'SPLIT':>6s}")
for nm, g, i, f, sp in rows:
    print(f"{nm:18s} {g:14.1f} pct {i:7.1f} pct {f:10.1f} pct {sp:6d}")

lw = [r for r in rows if r[0].startswith("LW")]
print("\n--- ADJUDICATION spread across LW's three passes (max - min)")
for j, name in ((1, "gate-or-contract"), (2, "inherited"), (3, "fix-of-a-fix")):
    vals = [r[j] for r in lw]
    print(f"  {name:20s} {min(vals):5.1f} to {max(vals):5.1f}  "
          f"spread {max(vals)-min(vals):5.1f} pts")

print("\n--- B vs C ONLY (the clean scorer-isolating pair)")
for j, name in ((1, "gate-or-contract"), (2, "inherited"), (3, "fix-of-a-fix")):
    b, c = lw[1][j], lw[2][j]
    print(f"  {name:20s} B {b:5.1f}  C {c:5.1f}  |B-C| {abs(b-c):5.1f} pts")

CONV = {"gate-or-contract": 4.0, "inherited": 2.5, "fix-of-a-fix": 4.5}
print("\n--- ADJUDICATION (B vs C) against CONVENTION (LW pass A vs RC)")
for j, name in ((1, "gate-or-contract"), (2, "inherited"), (3, "fix-of-a-fix")):
    adj = abs(lw[1][j] - lw[2][j])
    conv = CONV[name]
    verdict = ("ADJUDICATION larger" if adj > conv else
               "CONVENTION larger" if conv > adj else "equal")
    print(f"  {name:20s} adjudication {adj:5.1f}  convention {conv:5.1f}  "
          f"-> {verdict}")


def agree(d1, d2, label):
    out = {}
    for nm, fn in (("gof family", lambda k: d1[k]["gof_derived"] == d2[k]["gof_derived"]),
                   ("origin_time", lambda k: d1[k]["orig"] == d2[k]["orig"]),
                   ("fix>=1", lambda k: (d1[k]["fix"] >= 1) == (d2[k]["fix"] >= 1)),
                   ("prevention SET", lambda k: d1[k]["prev"] == d2[k]["prev"])):
        out[nm] = sum(1 for k in ids if fn(k))
    print(f"\nper-row agreement {label} (n={N})")
    for nm, v in out.items():
        print(f"  {nm:18s} {v:3d}/{N}  {100*v/N:5.1f} pct")
    return out


agree(B, C, "B vs C  [scorer only]")
agree(A, B, "A vs B  [scorer + redaction + interleave]")
agree(A, C, "A vs C  [scorer + redaction + interleave]")

print("\n--- THREE-WAY per-row unanimity")
for nm, fn in (("gof family", lambda k: len({A[k]['gof_derived'], B[k]['gof_derived'], C[k]['gof_derived']}) == 1),
               ("origin_time", lambda k: len({A[k]['orig'], B[k]['orig'], C[k]['orig']}) == 1),
               ("fix>=1", lambda k: len({A[k]['fix'] >= 1, B[k]['fix'] >= 1, C[k]['fix'] >= 1}) == 1),
               ("prevention SET", lambda k: A[k]['prev'] == B[k]['prev'] == C[k]['prev'])):
    v = sum(1 for k in ids if fn(k))
    print(f"  all three agree on {nm:18s} {v:3d}/{N}  {100*v/N:5.1f} pct")

print("\n--- DID THE PASS-A LEAK MATTER? agreement with RC, leaked vs clean rows")
leaked = set((HERE / "leak_rows.txt").read_text(encoding="utf-8").split())
cleanr = set(ids) - leaked
for nm, d in (("A (leaky input)", A), ("B (redacted)", B), ("C (redacted)", C)):
    for lbl, grp in (("leaked", leaked), ("clean", cleanr)):
        inset = 100 * sum(1 for k in grp if rcn[k]["prev"] in d[k]["prev"]) / len(grp)
        fam = 100 * sum(1 for k in grp if rcn[k]["gof"] == d[k]["gof_derived"]) / len(grp)
        print(f"  {nm:16s} {lbl:6s} n={len(grp):3d}   "
              f"RC value in set {inset:5.1f} pct   family agrees {fam:5.1f} pct")

print("\n--- consensus corpus: majority of the three passes per row")
maj = {}
for k in ids:
    votes = collections.Counter(d[k]["gof_derived"] for d in (A, B, C))
    maj[k] = votes.most_common(1)[0][0]
g = 100 * sum(1 for k in ids if maj[k] == "TRUE") / N
print(f"  gate-or-contract under 3-pass majority: {g:.1f} pct")
ties = sum(1 for k in ids
           if collections.Counter(d[k]["gof_derived"]
                                  for d in (A, B, C)).most_common(1)[0][1] == 1)
print(f"  rows where all three passes DISAGREE with each other: {ties}")
