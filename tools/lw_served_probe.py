"""Served-version probe: ask each LW server what it is running, not the launcher.

# arch: GET /api/version on every lw_ports allocation vs repo HEAD -> ops/runtime/served_versions.json (ingest P0-5)

WHY. Restarts go through restart_trigger.txt and health.json, but nothing
proved a dashboard serves the code that was committed: a silently failed
reload serves old code for days. Every lw_httpd server answers
`GET /api/version` with {commit, started, pid, config_hash}, captured at BIND.
This probe asks the SERVER and compares with the repo HEAD:

  current            served commit == HEAD
  stale              served commit != HEAD - recorded with the served commit,
                     the server's start time, and `stale_first_seen`, carried
                     across runs so "stale for longer than one restart cycle"
                     is a fact, and dropped the run it clears
  no-commit-reported an HTML page, a missing route, non-JSON or a null commit -
                     NEVER a guess
  down               nothing answered

The probe never fails its caller: every error is a state. Output is atomic.
CLI: python tools/lw_served_probe.py      (prints one line per service, exit 0)
Coverage: tests/test_served_version.py.
"""
from __future__ import annotations

import datetime as dt
import http.client
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_PATH = ROOT / "ops" / "runtime" / "served_versions.json"

sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

import lw_ports  # noqa: E402

from tools import lw_httpd  # noqa: E402


def _now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def probe_one(name: str, port: int, *, head: str | None, timeout: float = 3.0) -> dict:
    rec = {"service": name, "port": port, "state": "down", "served": None, "since": None,
           "pid": None, "detail": ""}
    try:
        conn = http.client.HTTPConnection("127.0.0.1", port, timeout=timeout)
        conn.request("GET", "/api/version", headers={"Host": "127.0.0.1"})
        resp = conn.getresponse()
        body = resp.read(65536)
        conn.close()
    except (OSError, http.client.HTTPException) as exc:
        rec["detail"] = f"no answer ({type(exc).__name__})"
        return rec
    try:
        doc = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        doc = None
    commit = doc.get("commit") if isinstance(doc, dict) else None
    if resp.status != 200 or not isinstance(commit, str) or not commit.strip():
        rec.update(state="no-commit-reported",
                   detail=f"HTTP {resp.status}, no commit in the answer")
        return rec
    rec.update(served=commit, since=doc.get("started"), pid=doc.get("pid"))
    if head and commit == head:
        rec.update(state="current", detail=f"serving {commit[:7]} (HEAD)")
    elif head:
        rec.update(state="stale", detail=f"stale server, serving {commit[:7]} since "
                   f"{doc.get('started')}; HEAD is {head[:7]}")
    else:
        rec.update(state="no-head", detail=f"serving {commit[:7]}; repo HEAD unreadable")
    return rec


def _read_previous(out: Path) -> dict:
    try:
        doc = json.loads(out.read_text(encoding="utf-8"))
        return doc.get("services") or {}
    except (OSError, ValueError, AttributeError):
        return {}


def run(services: dict | None = None, *, head: str | None = None, out: Path = OUT_PATH,
        now: str | None = None) -> dict:
    services = dict(lw_ports.ALLOCATIONS) if services is None else services
    head = head if head is not None else lw_httpd.git_head(cwd=ROOT)
    now = now or _now()
    prev = _read_previous(Path(out))
    result = {"checked": now, "head": head, "services": {}}
    for name, port in services.items():
        rec = probe_one(name, port, head=head)
        if rec.get("state") == "stale":
            old = prev.get(name) or {}
            same = old.get("state") == "stale" and old.get("served") == rec.get("served")
            rec["stale_first_seen"] = old.get("stale_first_seen") if same else now
        result["services"][name] = rec
    try:
        p = Path(out)
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_suffix(p.suffix + ".tmp")
        tmp.write_text(json.dumps(result, indent=2), encoding="utf-8")
        tmp.replace(p)
    except OSError as exc:
        result["write_error"] = type(exc).__name__
    return result


def main(argv: list[str] | None = None) -> int:
    res = run()
    for name, rec in res["services"].items():
        print(f"{rec.get('state', '?'):<19} {name:<10} {rec.get('detail', '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
