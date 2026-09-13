"""Tally LW's cross-score of RC's 198 rows, and compare against RC's own filing.

Refuses to print if any input is malformed. Every printed figure is
MEASURED-THIS-RUN from the .psv files the blind scorers wrote plus RC's
published rows file.
"""
import re
import sys
import collections
import pathlib

SCRATCH = pathlib.Path(__file__).parent / "_crossscore"
RC_ROWS = pathlib.Path(
    r"C:\Legion Wallpaper\moon_sync_inbox"
    r"\2026-09-13-from-RC-REFUTATION_COST_ROWS_PINNED.md"
)

IN_FAMILY = {
    "GATE-EXISTING", "GATE-ABSENT", "GATE-FIRED-IGNORED",
    "GATE-FIRED-CAUGHT", "CONTRACT", "CONTRACT-MISFIRED",
}
OUT_FAMILY = {"PROXY-MEASURE", "ADVERSARY"}
PREV = IN_FAMILY | OUT_FAMILY
KINDS = {"SELF", "SIBLING-SURFACE", "INTRODUCED", "SAME-ARTIFACT", "NA"}

EXPECT = {"chunk1": 60, "chunk2": 48, "chunk3": 47, "chunk4": 43}


def load_psv(path, expect_n):
    rows = {}
    text = path.read_text(encoding="utf-8")
    bad = sorted({c for c in text if ord(c) > 126})
    if bad:
        sys.exit(f"FATAL non-ascii in {path.name}: {bad}")
    for ln, line in enumerate(text.splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        f = line.split("|")
        if len(f) < 9:
            sys.exit(f"FATAL {path.name}:{ln} has {len(f)} fields: {line[:90]}")
        rid, gof, prev, orig, sub, fix, kind, correct, indiv = f[:9]
        note = f[9] if len(f) > 9 else ""
        prevset = set(x for x in prev.split(",") if x)
        if gof not in ("TRUE", "FALSE", "SPLIT"):
            sys.exit(f"FATAL {path.name}:{ln} gof={gof}")
        if not prevset or not prevset <= PREV:
            sys.exit(f"FATAL {path.name}:{ln} prev={prev}")
        if orig not in ("FRESH", "INHERITED"):
            sys.exit(f"FATAL {path.name}:{ln} orig={orig}")
        if sub not in ("DECAYED", "BORN-WRONG", "OVER-GENERALISED", "NA"):
            sys.exit(f"FATAL {path.name}:{ln} sub={sub}")
        if (orig == "FRESH") != (sub == "NA"):
            sys.exit(f"FATAL {path.name}:{ln} orig/sub mismatch {orig}/{sub}")
        if not re.fullmatch(r"\d+", fix):
            sys.exit(f"FATAL {path.name}:{ln} fix={fix}")
        if not set(kind.split(";")) <= KINDS:
            sys.exit(f"FATAL {path.name}:{ln} kind={kind}")
        if correct not in ("YES", "NO", "UNCLEAR"):
            sys.exit(f"FATAL {path.name}:{ln} correct={correct}")
        # recompute gof from the set so a scorer's arithmetic cannot leak in
        derived = ("TRUE" if prevset <= IN_FAMILY
                   else "FALSE" if prevset <= OUT_FAMILY else "SPLIT")
        if rid in rows:
            sys.exit(f"FATAL duplicate id {rid} in {path.name}")
        rows[rid] = dict(id=rid, gof=gof, gof_derived=derived, prev=prevset,
                         orig=orig, sub=sub, fix=int(fix),
                         kind=kind, correct=correct, indiv=indiv, note=note)
    if expect_n is not None and len(rows) != expect_n:
        sys.exit(f"FATAL {path.name}: {len(rows)} rows, expected {expect_n}")
    return rows


def load_rc():
    rows = {}
    cur = None
    for line in RC_ROWS.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^- `([a-z_]+)`: (.*)$", line)
        if not m:
            continue
        k, v = m.group(1), m.group(2)
        if k == "id":
            cur = {"id": v}
            rows[v] = cur
        elif cur is not None:
            cur.setdefault(k, v)
    return rows


def rc_norm(r):
    """RC's filed values, normalised to the same shape LW scored."""
    prev = r.get("prevention", "").strip().strip("`")
    orig_raw = r.get("origin_time", "")
    orig = "INHERITED" if "INHERITED" in orig_raw else "FRESH"
    sub = "NA"
    for s in ("BORN-WRONG", "DECAYED", "OVER-GENERALISED"):
        if s in orig_raw:
            sub = s
            break
    fm = re.match(r"\s*(\d+)", r.get("fix_chain", "0"))
    fix = int(fm.group(1)) if fm else 0
    gof = "TRUE" if prev in IN_FAMILY else "FALSE" if prev in OUT_FAMILY else "?"
    return dict(prev=prev, orig=orig, sub=sub, fix=fix, gof=gof)


def pct(n, d):
    return 100.0 * n / d if d else float("nan")


def main():
    lw = {}
    for ch, n in EXPECT.items():
        lw.update(load_psv(SCRATCH / f"scored_{ch}.psv", n))
    rc = load_rc()
    assert set(lw) == set(rc), (
        f"id mismatch: lw-only {sorted(set(lw)-set(rc))[:5]} "
        f"rc-only {sorted(set(rc)-set(lw))[:5]}")
    N = len(lw)
    print(f"=== LW cross-score of RC's corpus, N = {N} rows (as filed by RC)")

    # ---- gof arithmetic check
    mism = [r for r in lw.values() if r["gof"] != r["gof_derived"]]
    print(f"scorer gof vs derived-from-set mismatches: {len(mism)}"
          + (f"  {[r['id'] for r in mism][:8]}" if mism else ""))

    g = collections.Counter(r["gof_derived"] for r in lw.values())
    o = collections.Counter(r["orig"] for r in lw.values())
    fixpos = [r for r in lw.values() if r["fix"] >= 1]
    nonsame = [r for r in fixpos
               if set(r["kind"].split(";")) - {"SAME-ARTIFACT", "NA"}]
    subs = collections.Counter(r["sub"] for r in lw.values()
                               if r["orig"] == "INHERITED")
    corr = collections.Counter(r["correct"] for r in lw.values())
    indiv = collections.Counter(
        "KEEP" if r["indiv"] == "KEEP" else r["indiv"].split("-")[0]
        for r in lw.values())

    print(f"\n--- LW's figures on RC's corpus (fine grain, N = {N})")
    print(f"gate_or_contract TRUE  {g['TRUE']:3d}  {pct(g['TRUE'], N):5.1f} pct")
    print(f"                 FALSE {g['FALSE']:3d}  {pct(g['FALSE'], N):5.1f} pct")
    print(f"                 SPLIT {g['SPLIT']:3d}  {pct(g['SPLIT'], N):5.1f} pct")
    lo = pct(g["TRUE"], N)
    hi = pct(g["TRUE"] + g["SPLIT"], N)
    print(f"  -> gof share {lo:.1f} pct excluding SPLIT, {hi:.1f} pct including")
    print(f"inherited        {o['INHERITED']:3d}  {pct(o['INHERITED'], N):5.1f} pct")
    print(f"  BORN-WRONG {subs['BORN-WRONG']}  DECAYED {subs['DECAYED']}  "
          f"OVER-GENERALISED {subs['OVER-GENERALISED']}")
    if subs["DECAYED"]:
        print(f"  BORN-WRONG:DECAYED = {subs['BORN-WRONG']/subs['DECAYED']:.2f} : 1")
    print(f"fix-of-a-fix     {len(fixpos):3d}  {pct(len(fixpos), N):5.1f} pct "
          f"(all chains)")
    print(f"                 {len(nonsame):3d}  {pct(len(nonsame), N):5.1f} pct "
          f"(non-SAME-ARTIFACT only)")
    print(f"correct          {dict(corr)}")
    print(f"individuation    {dict(indiv)}")

    # ---- RC's own filing, recomputed from RC's published rows
    rcn = {k: rc_norm(v) for k, v in rc.items()}
    rg = collections.Counter(v["gof"] for v in rcn.values())
    ro = collections.Counter(v["orig"] for v in rcn.values())
    rfix = sum(1 for v in rcn.values() if v["fix"] >= 1)
    rsubs = collections.Counter(v["sub"] for v in rcn.values()
                                if v["orig"] == "INHERITED")
    print("\n--- RC's own filing on the same corpus (recomputed from RC's rows)")
    print(f"gate_or_contract {rg['TRUE']:3d}  {pct(rg['TRUE'], N):5.1f} pct "
          f"(unparsed: {rg['?']})")
    print(f"inherited        {ro['INHERITED']:3d}  {pct(ro['INHERITED'], N):5.1f} pct")
    print(f"  BORN-WRONG {rsubs['BORN-WRONG']}  DECAYED {rsubs['DECAYED']}")
    if rsubs["DECAYED"]:
        print(f"  BORN-WRONG:DECAYED = {rsubs['BORN-WRONG']/rsubs['DECAYED']:.2f} : 1")
    print(f"fix-of-a-fix     {rfix:3d}  {pct(rfix, N):5.1f} pct")

    # ---- THE CONVENTION SPREAD
    print("\n--- CONVENTION SPREAD (LW minus RC, same rows)")
    print(f"gate_or_contract  {pct(g['TRUE'], N) - pct(rg['TRUE'], N):+6.1f} pts "
          f"(excl SPLIT)   {hi - pct(rg['TRUE'], N):+6.1f} pts (incl SPLIT)")
    print(f"inherited         "
          f"{pct(o['INHERITED'], N) - pct(ro['INHERITED'], N):+6.1f} pts")
    print(f"fix-of-a-fix      {pct(len(fixpos), N) - pct(rfix, N):+6.1f} pts")

    # ---- per-field row-level disagreement
    print("\n--- per-row disagreement, LW vs RC, same row ids")
    dprev = [k for k in lw if rcn[k]["prev"] not in lw[k]["prev"]]
    dorig = [k for k in lw if rcn[k]["orig"] != lw[k]["orig"]]
    dfix = [k for k in lw if (rcn[k]["fix"] >= 1) != (lw[k]["fix"] >= 1)]
    dgof = [k for k in lw if rcn[k]["gof"] != lw[k]["gof_derived"]]
    print(f"prevention: RC's value NOT in LW's set   {len(dprev):3d}  "
          f"{pct(len(dprev), N):5.1f} pct")
    print(f"origin_time disagreement                 {len(dorig):3d}  "
          f"{pct(len(dorig), N):5.1f} pct")
    print(f"fix_chain >= 1 disagreement              {len(dfix):3d}  "
          f"{pct(len(dfix), N):5.1f} pct")
    print(f"gate_or_contract family disagreement     {len(dgof):3d}  "
          f"{pct(len(dgof), N):5.1f} pct")

    # ---- RC's GATE-FIRED-CAUGHT rows under LW's strict reading
    rc_gfc = [k for k in rc if rcn[k]["prev"] == "GATE-FIRED-CAUGHT"]
    lw_gfc = [k for k in lw if "GATE-FIRED-CAUGHT" in lw[k]["prev"]]
    kept = [k for k in rc_gfc if "GATE-FIRED-CAUGHT" in lw[k]["prev"]]
    print(f"\nRC filed GATE-FIRED-CAUGHT on {len(rc_gfc)} rows; "
          f"LW's strict reading keeps {len(kept)} of them; "
          f"LW assigns GFC to {len(lw_gfc)} rows total")
    moved = collections.Counter(
        ",".join(sorted(lw[k]["prev"])) for k in rc_gfc
        if "GATE-FIRED-CAUGHT" not in lw[k]["prev"])
    for val, n in moved.most_common(10):
        print(f"    RC GFC -> LW {val}: {n}")

    # ---- ADJUDICATION: second blind scorer over the overlap sample
    ov_path = SCRATCH / "scored_overlap.psv"
    if ov_path.exists():
        ov = load_psv(ov_path, None)
        shared = sorted(set(ov) & set(lw))
        n = len(shared)
        print(f"\n--- ADJUDICATION: two blind LW scorers, same convention, "
              f"{n} overlap rows")
        ag = sum(1 for k in shared if ov[k]["gof_derived"] == lw[k]["gof_derived"])
        ao = sum(1 for k in shared if ov[k]["orig"] == lw[k]["orig"])
        af = sum(1 for k in shared
                 if (ov[k]["fix"] >= 1) == (lw[k]["fix"] >= 1))
        ap = sum(1 for k in shared if ov[k]["prev"] == lw[k]["prev"])
        print(f"gate_or_contract agreement  {ag}/{n}  {pct(ag, n):5.1f} pct")
        print(f"origin_time agreement       {ao}/{n}  {pct(ao, n):5.1f} pct")
        print(f"fix_chain>=1 agreement      {af}/{n}  {pct(af, n):5.1f} pct")
        print(f"prevention SET identical    {ap}/{n}  {pct(ap, n):5.1f} pct")
        s1 = pct(sum(1 for k in shared if lw[k]["gof_derived"] == "TRUE"), n)
        s2 = pct(sum(1 for k in shared if ov[k]["gof_derived"] == "TRUE"), n)
        print(f"gof share on the sample: scorer A {s1:.1f} pct, "
              f"scorer B {s2:.1f} pct, ADJUDICATION TERM {abs(s1-s2):.1f} pts")
        f1 = pct(sum(1 for k in shared if lw[k]["fix"] >= 1), n)
        f2 = pct(sum(1 for k in shared if ov[k]["fix"] >= 1), n)
        print(f"fix-of-a-fix on the sample: A {f1:.1f} pct, B {f2:.1f} pct, "
              f"ADJUDICATION TERM {abs(f1-f2):.1f} pts")
    else:
        print("\n(overlap scorer output not present yet)")


if __name__ == "__main__":
    main()
