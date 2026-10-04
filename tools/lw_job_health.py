"""Tri-state scheduled-job health, judged by observed cadence and recorded status.

# arch: read-only per-task OK / UNHEALTHY / UNKNOWN for LW's scheduled tasks (ingest P0-4)

Exit 0 = every job healthy (or halted), 1 = at least one UNHEALTHY, 2 = none
unhealthy but at least one could not be determined. OBSERVATION ONLY: this
script reads run logs and `schtasks /Query /XML` and writes
`ops/runtime/job_health.json` for the dashboards. It never starts, stops,
enables or edits anything.

Rules (each pinned in tests/test_lw_job_health.py):
  * a job is judged by the status it RECORDED (tools/lw_runlog.py), never its
    exit code: ok resets the staleness clock; partial and failed do not, so a
    partial that never recovers ages into UNHEALTHY; skipped (a lock held by a
    long pass) keeps the clock fresh unless a partial/failed came after the ok;
  * staleness threshold = max(declared interval x 2, observed p90 gap x 1.5),
    where "observed" is the gaps between the last successful runs - a
    scheduler that drops runs under load moves the threshold with it, and a
    daily job's long gaps do not false-alarm;
  * FAIL_STREAK consecutive failed runs are UNHEALTHY at once;
  * a missing or empty run log is UNKNOWN ("could not determine"), never OK;
  * a HALT file, or the task disabled in the scheduler, reads HALTED - an
    operator's stop is not a fault;
  * the schtasks query is retried QUERY_TRIES times and the first line of its
    error is kept, so one blip is not a causeless alarm; a query that never
    answers only loses the declared interval.

CLI: python tools/lw_job_health.py [--runlog-dir D] [--out F]
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import statistics
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RUNTIME = ROOT / "ops" / "runtime"
OUT_PATH = RUNTIME / "job_health.json"
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)

OK, UNHEALTHY, UNKNOWN, HALTED = "OK", "UNHEALTHY", "UNKNOWN", "HALTED"
QUERY_TRIES = 3
FAIL_STREAK = 3
GAP_WINDOW = 20


@dataclass(frozen=True)
class JobSpec:
    task: str
    halt_file: Path | None = None


JOBS = (
    JobSpec("LW-InboxResponder", RUNTIME / "inbox_responder" / "HALT"),
    JobSpec("LW-CIWatchdog", RUNTIME / "ci_watchdog" / "HALT"),
    JobSpec("LW-Wallpaper", None),
    JobSpec("LW-WeeklyHygiene", RUNTIME / "weekly_hygiene" / "HALT"),
)


# ---------------------------------------------------------------------------
# Scheduler query (read-only)
# ---------------------------------------------------------------------------

def _decode(raw: bytes) -> str:
    if raw[:2] in (b"\xff\xfe", b"\xfe\xff"):
        return raw.decode("utf-16", "replace")
    return raw.decode("utf-8", "replace")


def schtasks_query(task: str):
    """(rc, stdout, stderr) of `schtasks /Query /TN task /XML`. Never raises."""
    try:
        r = subprocess.run(["schtasks", "/Query", "/TN", task, "/XML"],
                           capture_output=True, timeout=30, creationflags=NO_WINDOW,
                           stdin=subprocess.DEVNULL)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return 1, "", f"{type(exc).__name__}"
    return r.returncode, _decode(r.stdout or b""), _decode(r.stderr or b"")


def query_with_retry(task: str, query=schtasks_query, tries: int = QUERY_TRIES,
                     pause_s: float = 0.0):
    """(xml or None, first error line or "")."""
    first_err = ""
    for i in range(tries):
        rc, out, err = query(task)
        if rc == 0 and out.strip():
            return out, ""
        if not first_err:
            lines = (err or out or f"exit {rc}").strip().splitlines()
            first_err = lines[0].strip() if lines else f"exit {rc}"
        if pause_s and i + 1 < tries:
            time.sleep(pause_s)
    return None, first_err


_ISO_DUR = re.compile(r"^P(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?)?$")


def _iso_duration_s(text: str) -> int | None:
    m = _ISO_DUR.match(text.strip())
    if not m or not any(m.groups()):
        return None
    d, h, mi, s = (int(x or 0) for x in m.groups())
    return ((d * 24 + h) * 60 + mi) * 60 + s


def declared_interval_s(xml: str) -> int | None:
    """The shortest declared repeat: a Repetition Interval, DaysInterval or WeeksInterval."""
    cands = []
    for m in re.finditer(r"<Interval>([^<]+)</Interval>", xml):
        v = _iso_duration_s(m.group(1))
        if v:
            cands.append(v)
    for m in re.finditer(r"<DaysInterval>(\d+)</DaysInterval>", xml):
        cands.append(int(m.group(1)) * 86400)
    for m in re.finditer(r"<WeeksInterval>(\d+)</WeeksInterval>", xml):
        cands.append(int(m.group(1)) * 7 * 86400)
    return min(cands) if cands else None


def task_enabled(xml: str) -> bool:
    m = re.search(r"<Settings>.*?<Enabled>(\w+)</Enabled>", xml, re.S)
    return not (m and m.group(1).lower() == "false")


# ---------------------------------------------------------------------------
# Run log
# ---------------------------------------------------------------------------

def _parse_ts(text) -> dt.datetime | None:
    try:
        t = dt.datetime.fromisoformat(str(text).replace("Z", "+00:00"))
    except ValueError:
        return None
    return t if t.tzinfo else t.replace(tzinfo=dt.UTC)


def read_runs(path: Path) -> list[dict]:
    """Rows with a parsed `_t` (ended, else started). A torn line is skipped."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return []
    rows = []
    for line in text.splitlines():
        try:
            row = json.loads(line)
        except ValueError:
            continue
        if not isinstance(row, dict):
            continue
        t = _parse_ts(row.get("ended") or row.get("started"))
        if t is not None:
            rows.append({**row, "_t": t})
    rows.sort(key=lambda r: r["_t"])
    return rows


def _p90(values: list[float]) -> float:
    s = sorted(values)
    return s[min(len(s) - 1, int(round(0.9 * (len(s) - 1))))]


def _mins(seconds: float) -> str:
    return f"{seconds / 60:.0f}m" if seconds < 7200 else f"{seconds / 3600:.1f}h"


# ---------------------------------------------------------------------------
# Judge
# ---------------------------------------------------------------------------

def judge(spec: JobSpec, *, runlog_dir: Path, now: dt.datetime, query=schtasks_query) -> dict:
    v = {"task": spec.task, "state": UNKNOWN, "reason": "", "declared_s": None,
         "observed_median_s": None, "threshold_s": None, "last_ok": None,
         "last_status": None, "query_error": ""}
    if spec.halt_file is not None and Path(spec.halt_file).exists():
        v.update(state=HALTED, reason="HALT file present - stopped by the operator")
        return v
    xml, qerr = query_with_retry(spec.task, query)
    v["query_error"] = qerr
    if xml is not None:
        if not task_enabled(xml):
            v.update(state=HALTED, reason="task disabled in the scheduler")
            return v
        v["declared_s"] = declared_interval_s(xml)
    rows = read_runs(Path(runlog_dir) / f"{spec.task}.jsonl")
    if not rows:
        v["reason"] = "no run log - cannot determine"
        return v
    judged = [r for r in rows if r.get("status") != "skipped"]
    last = judged[-1] if judged else rows[-1]
    v["last_status"] = last.get("status")
    streak = 0
    for r in reversed(judged):
        if r.get("status") != "failed":
            break
        streak += 1
    if streak >= FAIL_STREAK:
        v.update(state=UNHEALTHY, reason=f"last {streak} runs failed: "
                 f"{str(last.get('detail') or '')[:120]}")
        return v
    oks = [r["_t"] for r in rows if r.get("status") == "ok"]
    gaps = [(b - a).total_seconds() for a, b in zip(oks, oks[1:], strict=False)][-GAP_WINDOW:]
    if gaps:
        v["observed_median_s"] = statistics.median(gaps)
    declared = v["declared_s"] or 0
    observed = _p90(gaps) * 1.5 if len(gaps) >= 2 else 0
    threshold = max(declared * 2, observed)
    if not threshold:
        v["reason"] = "cadence unknown (no declared interval, under 3 ok runs)"
        return v
    v["threshold_s"] = threshold
    # A SKIPPED run (lock held by a long pass, nothing to do) proves the job is
    # firing, so it keeps the clock fresh - but only when nothing since the
    # last ok was partial/failed, and it never enters the cadence gaps.
    fresh = oks[-1] if oks else rows[0]["_t"]
    after = [r for r in rows if r["_t"] > fresh]
    if after and not any(r.get("status") in ("partial", "failed") for r in after):
        skips = [r["_t"] for r in after if r.get("status") == "skipped"]
        fresh = skips[-1] if skips else fresh
    since = fresh
    v["last_ok"] = oks[-1].isoformat() if oks else None
    age = (now - since).total_seconds()
    tail = ""
    if last.get("status") in ("partial", "failed"):
        tail = f"; last run {last.get('status')}: {str(last.get('detail') or '')[:120]}"
    if age > threshold:
        what = f"no ok run for {_mins(age)}" if oks else f"no ok run ever ({_mins(age)})"
        v.update(state=UNHEALTHY, reason=f"{what} (threshold {_mins(threshold)}){tail}")
        return v
    v.update(state=OK, reason=f"last ok {_mins(age)} ago (threshold {_mins(threshold)}){tail}")
    return v


def exit_code(verdicts: list[dict]) -> int:
    states = {v["state"] for v in verdicts}
    if UNHEALTHY in states:
        return 1
    if UNKNOWN in states:
        return 2
    return 0


def _atomic_json(path: Path, doc: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(doc, indent=2), encoding="utf-8")
    tmp.replace(path)


def main(argv: list[str] | None = None, *, now: dt.datetime | None = None,
         query=schtasks_query) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--runlog-dir", type=Path, default=None)
    ap.add_argument("--out", type=Path, default=OUT_PATH)
    args = ap.parse_args(argv)
    if args.runlog_dir is None:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import lw_runlog
        args.runlog_dir = lw_runlog.default_root()
    now = now or dt.datetime.now(dt.UTC)
    verdicts = [judge(j, runlog_dir=args.runlog_dir, now=now, query=query) for j in JOBS]
    code = exit_code(verdicts)
    for v in verdicts:
        print(f"{v['state']:<9} {v['task']:<20} {v['reason']}")
    try:
        _atomic_json(args.out, {"generated": now.replace(microsecond=0).isoformat(),
                                "exit": code, "jobs": verdicts})
    except OSError as exc:
        print(f"could not write {args.out.name}: {type(exc).__name__}", file=sys.stderr)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
