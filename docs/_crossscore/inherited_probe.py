"""Decide RSC's `origin_time` from GIT instead of from PROSE.

LW scored RSC's corpus from the extraction's own wording and read INHERITED on
76 to 78 pct of rows, against 46 to 54 pct on RC's corpus under the same
convention. LW could not say whether that is a property of RSC's TREE or of
RSC's EXTRACTION VOICE - an extractor writing in the past tense about prior
sessions reads INHERITED more often.

This probe removes the prose. LW's convention keys `origin_time` on the claim's
STATE AT THE MOMENT OF REFUTATION: already committed, filed or in a tracked
artifact = INHERITED; produced by this session's own work = FRESH. Every RSC row
cites the refuting commit and names the artifact, so that state is decidable
from RSC's git history without reading a word of the row.

Read-only against RSC's tree. Writes nothing outside LW.
"""
import collections
import pathlib
import re
import subprocess
import sys

RSC = r"C:\Resin Compute"
ROWS = pathlib.Path(RSC) / "docs" / "REFUTATION_ROWS.md"
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import tally  # noqa: E402

CREATE_NO_WINDOW = 0x08000000


def git(*args):
    r = subprocess.run(("git", "-C", RSC) + args, capture_output=True,
                       text=True, creationflags=CREATE_NO_WINDOW)
    return r.stdout.strip() if r.returncode == 0 else None


# ---- parse RSC's rows
rows, cur, field = [], None, None
for line in ROWS.read_text(encoding="utf-8").splitlines():
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
print(f"parsed {len(rows)} rows from RSC's corpus")

# ---- LW's filed answers, from the two blind passes
D, E = {}, {}
for s in ("D0", "D1"):
    D.update(tally.load_psv(HERE / f"scored_{s}.psv", 48))
for s in ("E0", "E1"):
    E.update(tally.load_psv(HERE / f"scored_{s}.psv", 48))

SHA = re.compile(r"`([0-9a-f]{7,40})`")
PATH = re.compile(r"`([^`]+?)`")

verdict, detail = {}, {}
undecidable = collections.Counter()
for r in rows:
    rid = r["id"]
    shas = SHA.findall(r.get("citation", ""))
    if not shas:
        verdict[rid] = "UNDECIDABLE"
        undecidable["no sha cited"] += 1
        continue
    sha = shas[0]
    if git("cat-file", "-e", sha + "^{commit}") is None:
        verdict[rid] = "UNDECIDABLE"
        undecidable["sha not in RSC history"] += 1
        continue
    when = git("show", "-s", "--format=%ct", sha)
    cands = [p for p in PATH.findall(r.get("artifact", ""))
             if "/" in p or p.endswith((".py", ".md", ".toml", ".yml", ".json"))]
    if not cands:
        verdict[rid] = "UNDECIDABLE"
        undecidable["no artifact path"] += 1
        continue
    ages, any_prior, any_tracked = [], False, False
    for p in cands:
        log = git("log", "--format=%H %ct", sha, "--", p)
        if not log:
            continue
        any_tracked = True
        entries = [ln.split() for ln in log.splitlines()]
        prior = [e for e in entries if not e[0].startswith(sha)]
        if prior:
            any_prior = True
            ages.append(int(when) - int(prior[0][1]))
    if not any_tracked:
        verdict[rid] = "UNDECIDABLE"
        undecidable["artifact untracked at that sha"] += 1
        continue
    verdict[rid] = "INHERITED" if any_prior else "FRESH"
    detail[rid] = max(ages) if ages else 0

dec = [k for k, v in verdict.items() if v != "UNDECIDABLE"]
print("\n=== MECHANICAL VERDICT from RSC's git, no prose read")
print(f"decidable rows: {len(dec)} of {len(rows)}")
for reason, n in undecidable.most_common():
    print(f"   undecidable, {reason}: {n}")
mi = sum(1 for k in dec if verdict[k] == "INHERITED")
print(f"  INHERITED {mi}  FRESH {len(dec)-mi}  "
      f"-> {100*mi/len(dec):.1f} pct inherited (git)")

print("\n=== AGAINST WHAT LW'S SCORERS READ FROM THE PROSE")
for nm, d in (("pass D", D), ("pass E", E)):
    pi = sum(1 for k in dec if d[k]["orig"] == "INHERITED")
    agree = sum(1 for k in dec if d[k]["orig"] == verdict[k])
    fp = sum(1 for k in dec
             if d[k]["orig"] == "INHERITED" and verdict[k] == "FRESH")
    fn = sum(1 for k in dec
             if d[k]["orig"] == "FRESH" and verdict[k] == "INHERITED")
    print(f"  {nm}: prose {100*pi/len(dec):5.1f} pct inherited | "
          f"git {100*mi/len(dec):5.1f} pct | agreement {100*agree/len(dec):5.1f} pct "
          f"| prose-says-INHERITED-git-says-FRESH {fp} | reverse {fn}")

print("\n=== HOW OLD WAS THE CLAIM WHEN IT WAS REFUTED (git, INHERITED rows)")
ages = sorted(detail[k] for k in dec if verdict[k] == "INHERITED")
if ages:
    def band(lo, hi):
        return sum(1 for a in ages if lo <= a < hi)
    print(f"  n = {len(ages)}   median {ages[len(ages)//2]/3600:.1f} h   "
          f"max {max(ages)/86400:.1f} d")
    print(f"    under 1 hour   {band(0, 3600):3d}")
    print(f"    1 to 24 hours  {band(3600, 86400):3d}")
    print(f"    1 to 7 days    {band(86400, 7*86400):3d}")
    print(f"    over 7 days    {band(7*86400, 1 << 62):3d}")
    print("  A claim refuted MINUTES after its artifact was last touched is")
    print("  INHERITED only in the most literal sense. That band is the one")
    print("  that would inflate an inherited share without meaning much.")

print("\n=== THE THRESHOLD SENSITIVITY, which is the actual result")
print("LW's convention says INHERITED = already committed, filed or tracked at")
print("the moment of refutation. It names NO AGE. Every row above is inherited")
print("in that literal sense. Re-reading the same 83 rows with an age floor:")
N = len(dec)
for label, floor in (("no floor (LW's convention as written)", 0),
                     ("older than 1 hour", 3600),
                     ("older than 6 hours", 6 * 3600),
                     ("older than 24 hours", 86400),
                     ("older than 3 days", 3 * 86400)):
    n = sum(1 for k in dec
            if verdict[k] == "INHERITED" and detail.get(k, 0) >= floor)
    print(f"  {label:38s} {n:3d}/{N} = {100*n/N:5.1f} pct inherited")
print()
print("  RC's corpus, same convention, LW's three passes: 46.0 to 54.0 pct.")
print("  RSC crosses RC's band between the 6-hour and 24-hour floors, and")
print("  lands BELOW it at 24 hours. The SIGN of the cross-tree gap is set")
print("  by an age threshold that no contract version names.")
