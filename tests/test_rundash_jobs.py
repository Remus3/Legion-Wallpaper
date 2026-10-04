"""Rundash tri-state for LW's scheduled jobs (ingest P0-4): /api/jobs.

The view reads ops/runtime/job_health.json when it is fresh and otherwise
recomputes it through tools/lw_job_health.py (observation only; schtasks is
injected here). Overall state is tri-state: UNHEALTHY if any job is,
UNKNOWN if any job could not be determined or the record is missing, else OK.
"""
from __future__ import annotations

import datetime as dt
import http.client
import json
import sys
import threading
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

import lw_rundash  # noqa: E402
import lw_rundash_state as st  # noqa: E402


def _doc(states, generated):
    return {"generated": generated, "exit": 0,
            "jobs": [{"task": f"LW-{i}", "state": s, "reason": f"r{i}"}
                     for i, s in enumerate(states)]}


def _iso(ts):
    return dt.datetime.fromtimestamp(ts, dt.UTC).isoformat()


@pytest.mark.parametrize("states,overall", [
    (["OK", "OK"], "OK"),
    (["OK", "HALTED"], "OK"),
    (["OK", "UNKNOWN"], "UNKNOWN"),
    (["UNKNOWN", "UNHEALTHY"], "UNHEALTHY"),
])
def test_overall_state_is_tri_state(tmp_path, states, overall):
    now = time.time()
    p = tmp_path / "job_health.json"
    p.write_text(json.dumps(_doc(states, _iso(now - 60))), encoding="utf-8")
    view = st.read_job_health(p, now)
    assert view["state"] == overall and len(view["jobs"]) == len(states)


def test_a_missing_record_is_unknown_never_ok(tmp_path):
    view = st.read_job_health(tmp_path / "absent.json", time.time())
    assert view["state"] == "UNKNOWN" and "absent" in view["reason"]


def test_a_stale_record_is_unknown(tmp_path):
    now = time.time()
    p = tmp_path / "job_health.json"
    p.write_text(json.dumps(_doc(["OK"], _iso(now - 7200))), encoding="utf-8")
    view = st.read_job_health(p, now)
    assert view["state"] == "UNKNOWN" and view["stale"] is True


def test_garbage_is_unknown(tmp_path):
    p = tmp_path / "job_health.json"
    p.write_text("{nope", encoding="utf-8")
    assert st.read_job_health(p, time.time())["state"] == "UNKNOWN"


def _serve(tmp_path, **kw):
    page = tmp_path / "rundash.html"
    page.write_text("<h1>x</h1>", encoding="utf-8")
    srv = lw_rundash.RunDashServer(
        ("127.0.0.1", 0), lw_rundash.Handler, control_dir=tmp_path, page_path=page,
        manifest_path=tmp_path / "m.json", config_path=tmp_path / "c.json",
        repo_root=tmp_path, pid_alive=lambda pid: False, cache={},
        mirror_path=tmp_path / "mirror.json", **kw)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    return srv, t


def _get(port, path):
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
    conn.request("GET", path)
    r = conn.getresponse()
    out = r.status, r.getheader("Cache-Control"), json.loads(r.read())
    conn.close()
    return out


def test_api_jobs_serves_a_fresh_record(tmp_path):
    p = tmp_path / "job_health.json"
    p.write_text(json.dumps(_doc(["OK", "UNHEALTHY"], _iso(time.time()))), encoding="utf-8")
    srv, t = _serve(tmp_path, job_health_path=p,
                    job_health_refresh=lambda: pytest.fail("fresh record recomputed"))
    try:
        status, cache, body = _get(srv.server_address[1], "/api/jobs")
    finally:
        srv.shutdown()
        srv.server_close()
        t.join(timeout=5)
    assert status == 200 and cache == "no-store"
    assert body["state"] == "UNHEALTHY"


def test_api_jobs_recomputes_a_stale_record(tmp_path):
    p = tmp_path / "job_health.json"
    calls = []

    def refresh():
        calls.append(1)
        p.write_text(json.dumps(_doc(["OK"], _iso(time.time()))), encoding="utf-8")
    srv, t = _serve(tmp_path, job_health_path=p, job_health_refresh=refresh)
    try:
        _s, _c, body = _get(srv.server_address[1], "/api/jobs")
    finally:
        srv.shutdown()
        srv.server_close()
        t.join(timeout=5)
    assert calls == [1] and body["state"] == "OK"


def test_the_page_renders_the_jobs_panel():
    html = (Path(lw_rundash.__file__).resolve().parents[1] / "web" / "rundash.html").read_text(
        encoding="utf-8")
    assert 'id="jobsboard"' in html and '"/api/jobs"' in html
