"""Backfill the 2026-08-22 actor mislabel in manifests + PIPELINE_LOG (LEDGER 269).

Until LEDGER 268, `_complete_approve` wrote actor=operator for every approval
(the `--actor` flag reached the ADR-008 rail only) and SUBMIT had no actor at
all. On 2026-08-22 every APPROVE_CLEAN was run with `--actor tool:auto-approve`:
479 by `lw_clean_dispose` (12:04-12:17Z, LEDGER 122) and 7 detector-false-
positive passthroughs at 19:08Z (docs/CLEAN_OVERLAY_REVIEW_2026-08-22.md,
"Disposition of the seven"). The dispose burst's SUBMITs were run by the dispose
driver; the driver of the 19:08 SUBMITs is not recorded -> `unattributed`.

PIPELINE_LOG.md is append-only: history lines are NEVER edited. One
`CORRECT_ACTOR` line per corrected slug is appended in the standard 8-field
format. Each corrected manifest transition gets the true actor and a
`corrected_from` record. Idempotent: a corrected row no longer says operator.

    python tools/lw_actor_backfill.py            # dry run, prints the rows
    python tools/lw_actor_backfill.py --apply
"""
from __future__ import annotations

import argparse
import json
import os
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REF = "LEDGER 269"
ACTOR = "tool:lw_actor_backfill"
BATCH_DATE = "2026-08-22"
DISPOSE_WINDOW = ("2026-08-22T12:00:00Z", "2026-08-22T12:20:00Z")


def true_actor(t):
    """The actor a mislabelled transition should carry, else None."""
    ts = t.get("ts") or ""
    if t.get("actor") != "operator" or not ts.startswith(BATCH_DATE):
        return None
    if t.get("op") == "APPROVE_CLEAN":
        return "tool:auto-approve"
    if t.get("op") == "SUBMIT":
        if DISPOSE_WINDOW[0] <= ts <= DISPOSE_WINDOW[1]:
            return "tool:lw_clean_dispose"
        return "unattributed"
    return None


def _iso_now():
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _write_manifest(path, man, crlf):
    text = json.dumps(man, indent=2) + "\n"
    if crlf:
        text = text.replace("\n", "\r\n")
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_bytes(text.encode("utf-8"))
    os.replace(tmp, path)


def run(images, log_path, apply=False, now=None):
    """Correct every manifest under `images`; return one row per slug."""
    now = now or _iso_now()
    rows = []
    for mp in sorted(Path(images).rglob("manifest.json")):
        raw = mp.read_bytes()
        man = json.loads(raw)
        changes = []
        for t in man.get("transitions") or []:
            new = true_actor(t)
            if new is None:
                continue
            changes.append(f"{t['op']}@{t['ts']} operator->{new}")
            t["corrected_from"] = {"actor": t["actor"], "at": now, "ref": REF}
            t["actor"] = new
        if not changes:
            continue
        sha = next((t.get("sha256_out") or "" for t in reversed(man["transitions"])
                    if t.get("op") == "APPROVE_CLEAN"), "") or "-"
        stage = mp.parent.parent.name
        line = "{} | {} | CORRECT_ACTOR | {} -> {} | actor={} | sha12={} | ok | note={} ({})".format(
            now, mp.parent.name, stage, stage, ACTOR, sha[:12], "; ".join(changes), REF)
        rows.append({"slug": mp.parent.name, "manifest": str(mp),
                     "changes": changes, "line": line})
        if apply:
            _write_manifest(mp, man, b"\r\n" in raw)
    if apply and rows:
        # Same open() as lw_pipeline.Ctx.log, so the line endings match.
        with open(log_path, "a", encoding="ascii", errors="replace") as f:
            for r in rows:
                f.write(r["line"] + "\n")
    return rows


def main(argv=None):
    ap = argparse.ArgumentParser(prog="lw_actor_backfill")
    ap.add_argument("--images", default=str(ROOT / "images"))
    ap.add_argument("--log", default=str(ROOT / "PIPELINE_LOG.md"))
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args(argv)
    rows = run(a.images, a.log, apply=a.apply)
    n_ops = sum(len(r["changes"]) for r in rows)
    print(f"{'applied' if a.apply else 'dry-run'}: {len(rows)} slugs, {n_ops} transitions")
    for r in rows[:3]:
        print(r["line"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
