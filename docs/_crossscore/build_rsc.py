"""Parse RSC's 96 unscored rows, verify the blinding is a PROPERTY, build panels.

RSC's claim is that their corpus needs no strip because it was never scored, so
there is no blinding step to trust. LW does not take that on trust either - the
same mechanical check LW ran against itself is run here, against the tree that
made the claim rather than for it.
"""
import collections
import pathlib
import re

SRC = pathlib.Path(r"C:\Resin Compute\docs\REFUTATION_ROWS.md")
OUT = pathlib.Path(__file__).parent

KEEP = ("citation", "claim", "refutation", "artifact", "ledgered",
        "individuation")
TAXONOMY = sorted({
    "GATE-EXISTING", "GATE-ABSENT", "GATE-FIRED-IGNORED", "GATE-FIRED-CAUGHT",
    "PROXY-MEASURE", "CONTRACT-MISFIRED", "ADVERSARY", "SELF-AUDIT",
    "CODE-READ", "SIBLING-SURFACE", "SAME-ARTIFACT", "INTRODUCED",
    "BORN-WRONG", "OVER-GENERALISED", "INHERITED", "DECAYED",
    "fix_chain", "chain_kind", "origin_time", "prevention", "discovery",
}, key=len, reverse=True)
WB = r"\b"

text = SRC.read_text(encoding="utf-8")
rows, cur, field = [], None, None
for line in text.splitlines():
    m = re.match(r"^### (EV-\d+)\s*$", line)
    if m:
        cur = {"id": m.group(1)}
        rows.append(cur)
        field = None
        continue
    if cur is None:
        continue
    m = re.match(r"^- ([a-z_]+): (.*)$", line)
    if m:
        field = m.group(1)
        cur[field] = m.group(2).strip()
    elif field and line.startswith("  ") and line.strip():
        cur[field] = (cur[field] + " " + line.strip()).strip()
    elif not line.strip():
        field = None

print(f"parsed {len(rows)} EV rows")
print("fields:", dict(collections.Counter(k for r in rows for k in r)))
print("rows missing claim or refutation:",
      [r["id"] for r in rows
       if "claim" not in r or "refutation" not in r] or "none")

# ---- STRUCTURAL ANCHOR. RSC says they have no anchor to validate against.
# Their section 6 totals are one, and they are checkable.
ind = sum(1 for r in rows
          if str(r.get("individuation", "")).startswith("AMBIGUOUS"))
led_no = sum(1 for r in rows if str(r.get("ledgered", "")).startswith("NO"))
print("\n=== STRUCTURAL ANCHOR against RSC's own section 6")
for label, got, want in (("rows", len(rows), 96),
                         ("individuation AMBIGUOUS", ind, 32),
                         ("ledgered NO", led_no, 8)):
    print(f"  {label:26s} parsed {got:3d}  RSC states {want:3d}  "
          f"{'MATCH' if got == want else 'MISMATCH'}")

# ---- BLINDING CHECK
hits = collections.Counter()
hit_rows = {}
for r in rows:
    body = " ".join(str(r.get(k, "")) for k in KEEP)
    for val in TAXONOMY:
        if re.search(WB + re.escape(val) + WB, body):
            hits[val] += 1
            hit_rows.setdefault(r["id"], []).append(val)
print("\n=== BLINDING CHECK on RSC's corpus")
print(f"rows carrying a taxonomy label in kept text: "
      f"{len(hit_rows)} of {len(rows)}")
print("labels found:", dict(hits) or "NONE")
for rid, vals in hit_rows.items():
    print(f"   {rid}: {vals}")
print("RSC's claim that the blinding is a PROPERTY of the corpus:",
      "CONFIRMED" if not hit_rows else
      f"NOT CONFIRMED - {len(hit_rows)} exception(s), redacted below")

REDACTIONS = 0


def render(r):
    global REDACTIONS
    out = [f"## {r['id']}"]
    for k in KEEP:
        if k in r:
            txt = str(r[k])
            for val in TAXONOMY:
                txt, n = re.subn(WB + re.escape(val) + WB,
                                 "[REDACTED-LABEL]", txt)
                REDACTIONS += n
            out.append(f"- {k}: {txt}")
    return out


order = [r["id"] for r in rows]
by_id = {r["id"]: r for r in rows}
panels = {"D": {s: [order[i] for i in range(len(order)) if i % 2 == s]
                for s in range(2)}}
walk, seenl = [order[(i * 3) % len(order)] for i in range(len(order))], []
for x in walk + order:
    if x not in seenl:
        seenl.append(x)
panels["E"] = {s: [seenl[i] for i in range(len(seenl)) if i % 2 == s]
               for s in range(2)}

for p in ("D", "E"):
    for s in range(2):
        ids = panels[p][s]
        buf = [f"# RSC rows - panel {p} slice {s} - {len(ids)} rows",
               "# This corpus was NEVER SCORED by its author, so almost nothing",
               "# has been stripped. One taxonomy token appearing in prose has",
               "# been replaced with [REDACTED-LABEL].",
               "# Rows are INTERLEAVED, not a contiguous block.",
               "# `individuation` is RSC's OWN flag about THEIR two conventions;",
               "# it is NOT a score. Decide the LW `indiv` column from the claim",
               "# and refutation text, never from that flag.", ""]
        for rid in ids:
            buf += render(by_id[rid]) + [""]
        (OUT / f"rsc_{p}{s}.md").write_text("\n".join(buf), encoding="utf-8")
    flat = [x for s in range(2) for x in panels[p][s]]
    assert sorted(flat) == sorted(order) and len(flat) == len(set(flat))
    print(f"panel {p}: slices {[len(panels[p][s]) for s in range(2)]}")

print(f"redactions applied per full pass: {REDACTIONS // 2}")
resid = 0
for p in ("D", "E"):
    for s in range(2):
        lines = (OUT / f"rsc_{p}{s}.md").read_text(encoding="utf-8").splitlines()
        body = " ".join(ln for ln in lines if not ln.startswith("#"))
        for val in TAXONOMY:
            resid += len(re.findall(WB + re.escape(val) + WB, body))
print(f"POST-REDACTION residual taxonomy labels across both panels: {resid}")

d = {rid: s for s in range(2) for rid in panels["D"][s]}
e = {rid: s for s in range(2) for rid in panels["E"][s]}
print(f"rows in the same slice index in both panels: "
      f"{sum(1 for r in order if d[r] == e[r])} of {len(order)}")
