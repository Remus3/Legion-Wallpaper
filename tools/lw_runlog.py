"""One JSON line per scheduled-job run: what the job says about its own run.

# arch: per-job run log for tools/lw_job_health.py (ingest P0-4)

A scheduled job is judged by the status it RECORDED about its own run, not by
its exit code: a job that exits 0 while one sub-source is dead records
"partial". Each run appends ONE line to `ops/runtime/runlog/<task>.jsonl`:

    {"task", "started", "ended", "status": ok|partial|failed|skipped|halted,
     "detail", "pid"}

`record()` never raises (a job must not die because its log could not be
written; it returns False instead), coerces an unknown status to "failed"
with the reason in `detail`, and rotates the file to `<task>.jsonl.1` past
MAX_BYTES so a PT2M job cannot grow it without bound.

The CLI takes every value as an ARGUMENT, never through stdin: a double
redirect once made an interpreter execute the data as a script and exit 0 - a
green check over a hole. Used by tools/weekly_hygiene_run.ps1.

Root override: `LW_RUNLOG_ROOT` (the suite points it at a per-test dir).
Coverage: tests/test_lw_job_health.py.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ROOT_ENV = "LW_RUNLOG_ROOT"
STATUSES = ("ok", "partial", "failed", "skipped", "halted")
MAX_BYTES = 512 * 1024


def default_root() -> Path:
    env = os.environ.get(ROOT_ENV, "").strip()
    return Path(env) if env else ROOT / "ops" / "runtime" / "runlog"


def utc_now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def record(task: str, started: str, status: str, detail: str = "", *, root=None,
           pid: int | None = None, ended: str | None = None) -> bool:
    """Append one run record. Returns False (never raises) when it cannot."""
    if status not in STATUSES:
        detail = f"unknown status {status!r}: {detail}"
        status = "failed"
    row = {"task": task, "started": started, "ended": ended or utc_now(),
           "status": status, "detail": str(detail)[:500],
           "pid": os.getpid() if pid is None else pid}
    line = json.dumps(row, sort_keys=True) + "\n"
    try:
        base = Path(root) if root is not None else default_root()
        base.mkdir(parents=True, exist_ok=True)
        path = base / f"{task}.jsonl"
        if path.exists() and path.stat().st_size + len(line) > MAX_BYTES:
            path.replace(path.with_name(path.name + ".1"))
        with path.open("a", encoding="utf-8", newline="\n") as fh:
            fh.write(line)
        return True
    except OSError:
        return False


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--task", required=True)
    ap.add_argument("--started", required=True)
    ap.add_argument("--status", required=True)
    ap.add_argument("--detail", default="")
    ap.add_argument("--root", type=Path, default=None)
    args = ap.parse_args(argv)
    return 0 if record(args.task, args.started, args.status, args.detail,
                       root=args.root) else 1


if __name__ == "__main__":
    raise SystemExit(main())
