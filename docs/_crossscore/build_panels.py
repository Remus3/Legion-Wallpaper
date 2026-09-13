"""Verify the blinding mechanically, REDACT the leaks, build interleaved panels.

RSC objected that a strip has to be trusted. Checked here instead - and the
check FAILED on LW's first pass: taxonomy labels survive inside the `uncertain`
and `pin_gap` free-text fields LW deliberately kept. This script quantifies that,
redacts the labels while keeping the evidence, and partitions all 198 rows
round-robin so no scorer holds a contiguous ledger block.
"""
import re
import pathlib
import collections

SRC = pathlib.Path(
    r"C:\Legion Wallpaper\moon_sync_inbox"
    r"\2026-09-13-from-RC-REFUTATION_COST_ROWS_PINNED.md")
OUT = pathlib.Path(__file__).parent

KEEP = ("entry", "claim", "quote", "refuter", "uncertain", "pin_gap")
# Every taxonomy token a scorer could anchor on. Longest first so that
# GATE-FIRED-CAUGHT is redacted before GATE would ever match inside it.
VALUES = sorted({
    "GATE-EXISTING", "GATE-ABSENT", "GATE-FIRED-IGNORED", "GATE-FIRED-CAUGHT",
    "PROXY-MEASURE", "CONTRACT-MISFIRED", "ADVERSARY", "SELF-AUDIT",
    "CODE-READ", "SIBLING-SURFACE", "SAME-ARTIFACT", "INTRODUCED",
    "BORN-WRONG", "OVER-GENERALISED", "INHERITED", "DECAYED",
    "fix_chain", "chain_kind", "origin_time", "prevention_why", "prevention",
    "discovery",
}, key=len, reverse=True)

rows = []
cur = None
for line in SRC.read_text(encoding="utf-8").splitlines():
    m = re.match(r"^- `([a-z_]+)`: (.*)$", line)
    if not m:
        continue
    k, v = m.group(1), m.group(2)
    if k == "id":
        cur = {"id": v}
        rows.append(cur)
    elif cur is not None:
        cur.setdefault(k, v)
print(f"parsed {len(rows)} rows")

# ---- BLINDING AUDIT of the FIRST pass (fields kept verbatim, no redaction)
per_field = collections.Counter()
leak_rows = set()
label_hits = collections.Counter()
for r in rows:
    for k in KEEP:
        txt = str(r.get(k, ""))
        for val in VALUES:
            if re.search(r"\b" + re.escape(val) + r"\b", txt):
                per_field[k] += 1
                label_hits[val] += 1
                leak_rows.add(r["id"])
print("\n=== BLINDING AUDIT of LW's FIRST pass (pass A)")
print(f"rows carrying at least one taxonomy label in kept text: "
      f"{len(leak_rows)} of {len(rows)} "
      f"({100*len(leak_rows)/len(rows):.1f} pct)")
print("by field:", dict(per_field))
print("most-leaked labels:", label_hits.most_common(8))
pathlib.Path(OUT / "leak_rows.txt").write_text(
    "\n".join(sorted(leak_rows)), encoding="utf-8")


def redact(txt):
    n = 0
    for val in VALUES:
        txt, k = re.subn(r"\b" + re.escape(val) + r"\b", "[REDACTED-LABEL]", txt)
        n += k
    return txt, n


def render(r):
    out = [f"## {r['id']}"]
    total = 0
    for k in KEEP:
        if k in r:
            txt, n = redact(str(r[k]))
            total += n
            out.append(f"- {k}: {txt}")
    return out, total


# ---- interleaved panels, now on REDACTED text
order = [r["id"] for r in rows]
by_id = {r["id"]: r for r in rows}
panels = {"B": {s: [order[i] for i in range(len(order)) if i % 4 == s]
                for s in range(4)}}
walk, seen = [order[(i * 3) % len(order)] for i in range(len(order))], []
for x in walk + order:
    if x not in seen:
        seen.append(x)
panels["C"] = {s: [seen[i] for i in range(len(seen)) if i % 4 == s]
               for s in range(4)}

redactions = 0
for p in ("B", "C"):
    for s in range(4):
        ids = panels[p][s]
        buf = [f"# BLINDED RC rows - panel {p} slice {s} - {len(ids)} rows",
               "# Rows are INTERLEAVED across the corpus on purpose: this slice",
               "# is NOT a contiguous block of one ledger range.",
               "# The originating tree's own scores are absent, and any taxonomy",
               "# label surviving in free text has been replaced with",
               "# [REDACTED-LABEL]. Score from the evidence, not from a label.", ""]
        for rid in ids:
            block, n = render(by_id[rid])
            if p == "B":
                redactions += n
            buf += block + [""]
        (OUT / f"blind_{p}{s}.md").write_text("\n".join(buf), encoding="utf-8")
    flat = [x for s in range(4) for x in panels[p][s]]
    assert sorted(flat) == sorted(order), f"panel {p} misses rows"
    assert len(flat) == len(set(flat)), f"panel {p} has duplicates"
    print(f"panel {p}: 4 slices {[len(panels[p][s]) for s in range(4)]}")
print(f"redactions applied per full pass: {redactions}")

# ---- verify the redaction actually worked
resid = 0
for p in ("B", "C"):
    for s in range(4):
        t = (OUT / f"blind_{p}{s}.md").read_text(encoding="utf-8")
        body = "\n".join(ln for ln in t.splitlines() if not ln.startswith("#"))
        for val in VALUES:
            resid += len(re.findall(r"\b" + re.escape(val) + r"\b", body))
print(f"POST-REDACTION residual taxonomy labels across both panels: {resid}")

bslice = {rid: s for s in range(4) for rid in panels["B"][s]}
cslice = {rid: s for s in range(4) for rid in panels["C"][s]}
same = sum(1 for rid in order if bslice[rid] == cslice[rid])
print(f"rows in the same slice index in both panels: {same} of {len(order)}")
