"""Post-merge identity scan of the default branch (MAIN 0034
DEPENDABOT-MERGE-RULE section 2.2; LW rule in CLAUDE.md "Bot PRs").

Why: fleet_identity's commit-msg strip runs only on a LOCAL commit and its
pre-push refusal only on a LOCAL push. A merge done on GitHub (squash dialog or
`gh pr merge`) runs neither, so a bot author, a GitHub web-flow committer or a
`Co-authored-by:` trailer lands on the remote unseen. This scan reads the
default branch after every bot-PR merge (and on demand):

    python tools/lw_postmerge_scan.py            fetch origin, scan new commits
    python tools/lw_postmerge_scan.py --all      rescan the whole branch
    python tools/lw_postmerge_scan.py --no-fetch --ref main

Flags, per commit: non-operator-author, non-operator-committer, and ANY
`Co-authored-by:` trailer line (the order says any; fleet_identity strips only
AI/bot ones). Exit 1 on a hit, 2 on a git/config error, 0 clean. The last
CLEAN tip is kept in ops/runtime/postmerge_scan.json (gitignored), so a hit
is re-reported on every run until it is fixed - with fleet_rewrite.py under
MAIN 2312's scope, never by another path. Output names short shas and
classes only, never a name or an address. Operator identities come ONLY from
local git config `fleet.operatorIdent` (the kit's single source).
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ops" / "fleet_kit"))
import fleet_identity as fi  # noqa: E402

STATE = ROOT / "ops" / "runtime" / "postmerge_scan.json"
_CO_AUTHOR = re.compile(r"^\s*co-authored-by\s*:", re.I)
_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0) if sys.platform == "win32" else 0


def _idents(raw) -> set[str]:
    return fi.operator_idents(None, reader=lambda _cwd: "\n".join(raw))


def scan(repo, rev_range: str, operator: list[str]) -> list[tuple[str, str]]:
    """[(short sha, class)] for every commit in `git log <rev_range>`."""
    idents = _idents(operator)
    if not idents:
        raise ValueError("no operator identity: set git config --local fleet.operatorIdent")
    rows = fi.commits(Path(repo), [rev_range])
    if rows is None:
        raise OSError(f"git log failed for {rev_range}")
    hits = []
    for r in rows:
        short = r["sha"][:7]
        if not fi.is_operator(r["an"], r["ae"], idents):
            hits.append((short, "non-operator-author"))
        if not fi.is_operator(r["cn"], r["ce"], idents):
            hits.append((short, "non-operator-committer"))
        if any(_CO_AUTHOR.match(ln) for ln in r["msg"].splitlines()):
            hits.append((short, "co-authored-by"))
    return hits


def _git(repo, *args) -> str | None:
    try:
        r = subprocess.run(["git", "-C", str(repo), *args], capture_output=True,
                           text=True, timeout=120, creationflags=_NO_WINDOW)
    except (OSError, subprocess.SubprocessError):
        return None
    return r.stdout.strip() if r.returncode == 0 else None


def _load(state: Path) -> dict:
    try:
        return json.loads(state.read_text(encoding="ascii"))
    except (OSError, ValueError):
        return {}


def _save(state: Path, data: dict) -> None:
    state.parent.mkdir(parents=True, exist_ok=True)
    tmp = state.with_suffix(state.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=1) + "\n", encoding="ascii", newline="\n")
    tmp.replace(state)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--repo", default=str(ROOT))
    ap.add_argument("--remote", default="origin")
    ap.add_argument("--ref", default=None, help="default: <remote>/main")
    ap.add_argument("--no-fetch", action="store_true")
    ap.add_argument("--all", action="store_true", help="ignore the last clean tip")
    ap.add_argument("--state", default=str(STATE))
    a = ap.parse_args(argv)
    repo, state = Path(a.repo), Path(a.state)
    if not a.no_fetch and _git(repo, "fetch", "-q", a.remote) is None:
        print("postmerge-scan: fetch failed")
        return 2
    ref = a.ref or f"{a.remote}/main"
    tip = _git(repo, "rev-parse", "--verify", ref + "^{commit}")
    if not tip:
        print(f"postmerge-scan: cannot resolve {ref}")
        return 2
    last = None if a.all else _load(state).get("clean_tip")
    if last and _git(repo, "merge-base", "--is-ancestor", last, tip) is None:
        last = None                       # history rewritten: rescan everything
    rng = f"{last}..{tip}" if last else tip
    operator = (_git(repo, "config", "--local", "--get-all", fi.CONFIG_KEY) or "").splitlines()
    try:
        hits = scan(repo, rng, operator)
    except (ValueError, OSError) as exc:
        print(f"postmerge-scan: {exc}")
        return 2
    now = datetime.now().astimezone().isoformat(timespec="seconds")
    data = _load(state)
    data.update({"checked": now, "ref": ref, "tip": tip[:12], "hits": hits})
    if not hits:
        data["clean_tip"] = tip
    _save(state, data)
    if hits:
        for sha, cls in hits:
            print(f"postmerge-scan: HIT {sha} {cls}")
        print("postmerge-scan: fix with ops/fleet_kit/fleet_rewrite.py (plan, bundle, run) "
              "under MAIN 2312 scope; record it in docs/LEDGER.md")
        return 1
    print(f"postmerge-scan: clean ({rng[:30]})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
