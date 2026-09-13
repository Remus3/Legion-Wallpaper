"""Did the pass-A blinding leak ANCHOR pass A's scorers toward RC's filing?

If leaked rows agree with RC more than clean rows do, pass A's convention spread
is biased DOWNWARD and LW's published 4.0 / 2.5 / 4.5 are too small.
"""
import pathlib
import sys

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
import tally  # noqa: E402

lw = {}
for ch, n in (("chunk1", 60), ("chunk2", 48), ("chunk3", 47), ("chunk4", 43)):
    lw.update(tally.load_psv(HERE / f"scored_{ch}.psv", n))
rc = tally.load_rc()
rcn = {k: tally.rc_norm(v) for k, v in rc.items()}
leaked = set((HERE / "leak_rows.txt").read_text(encoding="utf-8").split())
clean = set(lw) - leaked
print(f"leaked rows {len(leaked)}   clean rows {len(clean)}")


def rate(ids, fn):
    ids = list(ids)
    return 100.0 * sum(1 for k in ids if fn(k)) / len(ids), len(ids)


tests = {
    "RC's prevention value IS in LW's set":
        lambda k: rcn[k]["prev"] in lw[k]["prev"],
    "prevention value EXACTLY equal (singleton match)":
        lambda k: lw[k]["prev"] == {rcn[k]["prev"]},
    "gate-or-contract family agrees":
        lambda k: rcn[k]["gof"] == lw[k]["gof_derived"],
    "origin_time agrees":
        lambda k: rcn[k]["orig"] == lw[k]["orig"],
    "fix_chain>=1 agrees":
        lambda k: (rcn[k]["fix"] >= 1) == (lw[k]["fix"] >= 1),
}
print(f"\n{'agreement with RC':52s} {'LEAKED':>14s} {'CLEAN':>14s} {'delta':>8s}")
for name, fn in tests.items():
    a, na = rate(leaked, fn)
    b, nb = rate(clean, fn)
    print(f"{name:52s} {a:8.1f} pct  {b:8.1f} pct  {a-b:+7.1f}")

# Only the rows whose leaked label was a PREVENTION value are the ones that
# could anchor `prevention` specifically. Narrow to those.
PREVVALS = tally.PREV
narrow = set()
import re  # noqa: E402
for r in rc.values():
    kept = " ".join(str(r.get(k, "")) for k in
                    ("entry", "claim", "quote", "refuter", "uncertain", "pin_gap"))
    for v in PREVVALS:
        if re.search(r"\b" + re.escape(v) + r"\b", kept):
            narrow.add(r["id"])
            break
print(f"\nrows leaking a PREVENTION value specifically: {len(narrow)}")
if narrow:
    a, _ = rate(narrow, tests["RC's prevention value IS in LW's set"])
    b, _ = rate(set(lw) - narrow,
                tests["RC's prevention value IS in LW's set"])
    print(f"  RC's value in LW's set:  leaked {a:.1f} pct   rest {b:.1f} pct"
          f"   delta {a-b:+.1f}")
    a2, _ = rate(narrow, tests["gate-or-contract family agrees"])
    b2, _ = rate(set(lw) - narrow, tests["gate-or-contract family agrees"])
    print(f"  family agrees:           leaked {a2:.1f} pct   rest {b2:.1f} pct"
          f"   delta {a2-b2:+.1f}")
