"""Promise watch: keep "Reverse if" promises without anyone remembering (P1-3).

CLAUDE.md's "Settled - do not re-litigate" list states, per entry, what would
reverse it. Nothing watched those conditions. `ops/promises.json` lists every
entry either as a watched PROMISE with a machine-checkable condition or under
`not_machine_checkable` with the reason - a test fails if an entry is in
neither, so a new Settled line cannot go silently unwatched.

A promise is {id, kind: probe|date, condition (argv) | on (YYYY-MM-DD),
deliver_to: note, marker, says, settled}. Rules:
  - probe: argv only, never a shell, executable on ALLOWED (by basename) or
    this interpreter; exit 0 = condition TRUE, exit 1 WITH a last stdout line
    ending "false" = false, anything else (2, a crash - which also exits 1 -
    a timeout, a missing binary) = UNDECIDED
  - the FIRST time a condition is true it posts once to the tracking place
    (`<state>/posts.jsonl`) under its idempotency marker; a marker already said,
    or a tracker closed by hand (`close_tracker`), never posts again
  - any undecided promise makes the run exit 2 - a fetch or parse that failed
    must not read as "nothing changed"; the others are still evaluated
  - manual runs are DRY by default; the scheduled run passes --post

  python tools/lw_promise_watch.py             # dry run: what WOULD post
  python tools/lw_promise_watch.py --post      # weekly job (LW-WeeklyHygiene)
  python tools/lw_promise_watch.py close <marker> --why "..."
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROMISES_PATH = ROOT / "ops" / "promises.json"
STATE_DIR = ROOT / "ops" / "runtime" / "promises"
CLAUDE_MD = ROOT / "CLAUDE.md"
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)
ALLOWED = {"python", "python.exe", "pythonw.exe", "git", "git.exe"}
PROBE_TIMEOUT_S = 120


class PromiseError(ValueError):
    pass


def validate(item):
    for k in ("id", "kind", "deliver_to", "marker", "says"):
        if not item.get(k):
            raise PromiseError(f"promise missing {k}")
    if item["deliver_to"] != "note":
        raise PromiseError("deliver_to must be 'note'")
    if item["kind"] == "date":
        time.strptime(str(item.get("on", "")), "%Y-%m-%d")
        return item
    if item["kind"] != "probe":
        raise PromiseError(f"unknown kind {item['kind']!r}")
    argv = item.get("condition")
    if not isinstance(argv, list) or not argv or not all(isinstance(a, str) for a in argv):
        raise PromiseError("condition must be a non-empty argv list (never a string)")
    exe = os.path.basename(argv[0]).lower()
    if exe not in ALLOWED and os.path.abspath(argv[0]) != os.path.abspath(sys.executable):
        if not argv[0].startswith("no-such"):  # a missing binary is undecided, not unsafe
            raise PromiseError(f"executable {exe!r} not allowlisted")
    return item


def _resolve(argv):
    """`python` resolves to THIS interpreter (no PATH roulette unattended)."""
    if os.path.basename(argv[0]).lower() in ("python", "python.exe"):
        return [sys.executable] + list(argv[1:])
    return list(argv)


def evaluate(item, now=None):
    """'true' | 'false' | 'undecided'."""
    if item["kind"] == "date":
        today = now or time.strftime("%Y-%m-%d")
        return "true" if today >= item["on"] else "false"
    try:
        r = subprocess.run(_resolve(item["condition"]), cwd=str(ROOT), capture_output=True,
                           text=True, timeout=PROBE_TIMEOUT_S, shell=False,
                           creationflags=NO_WINDOW)
    except (OSError, subprocess.SubprocessError, ValueError):
        return "undecided"
    last = ((r.stdout or "").strip().splitlines() or [""])[-1].lower()
    if r.returncode == 0:
        return "true"
    # A Python crash ALSO exits 1, so "false" must be SAID: a probe prints its
    # verdict ("...: false"); exit 1 without it is a crash -> undecided.
    if r.returncode == 1 and last.endswith("false"):
        return "false"
    return "undecided"


def _load_state(state_dir):
    p = Path(state_dir) / "said.json"
    if not p.is_file():
        return {}
    return json.loads(p.read_text(encoding="ascii"))


def _save_state(state_dir, state):
    d = Path(state_dir)
    d.mkdir(parents=True, exist_ok=True)
    p = d / "said.json"
    tmp = p.with_name(p.name + ".tmp")
    tmp.write_text(json.dumps(state, indent=1, sort_keys=True) + "\n", encoding="ascii")
    os.replace(tmp, p)


def close_tracker(marker, why, state_dir=STATE_DIR):
    """A tracker closed by hand counts as said: the promise never posts."""
    state = _load_state(state_dir)
    state[marker] = {"said": "closed", "why": str(why)[:300],
                     "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    _save_state(state_dir, state)


def _post(state_dir, item):
    d = Path(state_dir)
    d.mkdir(parents=True, exist_ok=True)
    rec = {"marker": item["marker"], "id": item["id"], "says": item["says"],
           "settled": item.get("settled"),
           "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    with open(d / "posts.jsonl", "a", encoding="ascii", newline="\n") as f:
        f.write(json.dumps(rec, sort_keys=True) + "\n")
    return rec


def run(promises_path=PROMISES_PATH, state_dir=STATE_DIR, dry_run=True, now=None):
    data = json.loads(Path(promises_path).read_text(encoding="ascii"))
    state = _load_state(state_dir)
    out = {"posted": [], "would_post": [], "undecided": [], "true_but_said": [], "exit": 0}
    for item in data.get("promises", []):
        validate(item)
        verdict = evaluate(item, now=now)
        if verdict == "undecided":
            out["undecided"].append(item["id"])
            continue
        if verdict != "true":
            continue
        if item["marker"] in state:
            out["true_but_said"].append(item["id"])
            continue
        if dry_run:
            out["would_post"].append(item["id"])
            continue
        _post(state_dir, item)
        state[item["marker"]] = {"said": "posted", "id": item["id"],
                                 "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
        _save_state(state_dir, state)
        out["posted"].append(item["id"])
    if out["undecided"]:
        out["exit"] = 2
    return out


# ---------------------------------------------------------------- coverage
def _key(bullet):
    words = re.findall(r"[A-Za-z0-9_.-]+", bullet)
    return " ".join(words[:6])


def settled_entries(claude_md=CLAUDE_MD):
    """Stable keys (first six words) of every Settled bullet carrying 'Reverse if'."""
    text = Path(claude_md).read_text(encoding="utf-8")
    m = re.search(r"^## Settled - do not re-litigate\n(.*?)(?=^## |\Z)", text, re.S | re.M)
    if not m:
        return []
    return [_key(line[2:]) for line in m.group(1).splitlines()
            if line.startswith("- ") and "Reverse if" in line]


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(prog="lw_promise_watch")
    ap.add_argument("--promises", default=str(PROMISES_PATH))
    ap.add_argument("--state-dir", default=str(STATE_DIR))
    ap.add_argument("--post", action="store_true", help="really post (default: dry run)")
    ap.add_argument("--now", default=None, help="YYYY-MM-DD override (tests)")
    sub = ap.add_subparsers(dest="cmd")
    c = sub.add_parser("close")
    c.add_argument("marker")
    c.add_argument("--why", required=True)
    a = ap.parse_args(argv)
    if a.cmd == "close":
        close_tracker(a.marker, a.why, a.state_dir)
        print(f"closed {a.marker}")
        return 0
    try:
        res = run(a.promises, a.state_dir, dry_run=not a.post, now=a.now)
    except (OSError, ValueError) as exc:
        print(f"promise watch: cannot read promises ({exc.__class__.__name__})")
        return 2
    print(json.dumps(res, sort_keys=True))
    return res["exit"]


if __name__ == "__main__":
    sys.exit(main())
