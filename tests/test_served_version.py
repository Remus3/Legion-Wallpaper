"""Served-version probe (ingest P0-5): ask the SERVER what it runs.

Arms: the scaffold answers GET /api/version with the commit captured at BIND
(injected), behind the existing Host guard, leaking no path or account name;
the probe treats non-JSON / a missing commit as "no commit reported", never a
guess; a mismatch with the repo HEAD is "stale" with the served commit and its
start time, and it clears when the server serves HEAD again.
"""
from __future__ import annotations

import http.client
import json
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from tools import lw_httpd  # noqa: E402

import lw_served_probe as probe  # noqa: E402

A = "a" * 40
B = "b" * 40


class _H(lw_httpd.BaseLWHandler):
    def _route(self, method):
        self._send_json(200, {"ok": True})


@pytest.fixture
def served(monkeypatch, tmp_path):
    cfg = tmp_path / "cfg.json"
    cfg.write_text('{"x": 1}', encoding="utf-8")
    monkeypatch.setattr(lw_httpd, "git_head", lambda: A)
    srv = lw_httpd.LWServer(("127.0.0.1", 0), _H, config_paths=(cfg,))
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    try:
        yield srv
    finally:
        srv.shutdown()
        srv.server_close()
        t.join(timeout=5)


def _get(port, path, host="127.0.0.1"):
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    conn.request("GET", path, headers={"Host": host})
    r = conn.getresponse()
    body = r.read()
    conn.close()
    return r.status, body


def test_the_scaffold_reports_the_commit_captured_at_bind(served, monkeypatch):
    monkeypatch.setattr(lw_httpd, "git_head", lambda: B)    # HEAD moves after bind
    status, body = _get(served.server_address[1], "/api/version")
    doc = json.loads(body)
    assert status == 200
    assert doc["commit"] == A and doc["pid"] > 0 and doc["started"]
    assert isinstance(doc["config_hash"], str) and len(doc["config_hash"]) == 12


def test_the_version_route_keeps_the_host_guard(served):
    status, _body = _get(served.server_address[1], "/api/version", host="evil.example")
    assert status == 403


def test_the_version_payload_leaks_no_path(served):
    _s, body = _get(served.server_address[1], "/api/version")
    text = body.decode("utf-8")
    # MAIN 0020 section 5: exactly these keys, schema 1, nothing else.
    doc = json.loads(text)
    assert set(doc) == {"commit", "started", "pid", "config_hash", "schema"}
    assert doc["schema"] == 1
    assert "\\" not in text and "Users" not in text and "/" not in text.replace(":", "")


def test_a_failed_git_read_reports_no_commit(monkeypatch):
    monkeypatch.setattr(lw_httpd, "git_head", lambda: None)
    srv = lw_httpd.LWServer(("127.0.0.1", 0), _H)
    try:
        assert srv.version_info["commit"] is None
        assert srv.version_info["config_hash"] is None
    finally:
        srv.server_close()


def test_git_head_never_raises_outside_a_repo(tmp_path):
    assert lw_httpd.git_head(cwd=tmp_path) is None


# -- the probe -----------------------------------------------------------------

def test_probe_current_when_the_server_serves_head(served):
    rec = probe.probe_one("x", served.server_address[1], head=A)
    assert rec["state"] == "current" and rec["served"] == A


def test_probe_stale_names_the_served_commit_and_since(served):
    rec = probe.probe_one("x", served.server_address[1], head=B)
    assert rec["state"] == "stale"
    assert rec["served"] == A and rec["since"]
    assert A[:7] in rec["detail"]


class _Html(BaseHTTPRequestHandler):
    def do_GET(self):
        body = b"<html>an old server with no version route</html>"
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass


def test_probe_treats_html_as_no_commit_reported_never_a_guess():
    srv = ThreadingHTTPServer(("127.0.0.1", 0), _Html)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    try:
        rec = probe.probe_one("x", srv.server_address[1], head=A)
    finally:
        srv.shutdown()
        srv.server_close()
    assert rec["state"] == "no-commit-reported" and rec["served"] is None


def test_probe_reports_down_and_never_raises():
    rec = probe.probe_one("x", 1, head=A, timeout=0.5)
    assert rec["state"] == "down"


def test_stale_since_is_carried_across_runs_and_clears(tmp_path, served):
    out = tmp_path / "served_versions.json"
    port = served.server_address[1]
    first = probe.run({"x": port}, head=B, out=out, now="2026-10-04T00:00:00Z")
    assert first["services"]["x"]["state"] == "stale"
    assert first["services"]["x"]["stale_first_seen"] == "2026-10-04T00:00:00Z"
    second = probe.run({"x": port}, head=B, out=out, now="2026-10-04T00:10:00Z")
    assert second["services"]["x"]["stale_first_seen"] == "2026-10-04T00:00:00Z"
    third = probe.run({"x": port}, head=A, out=out, now="2026-10-04T00:20:00Z")
    assert third["services"]["x"]["state"] == "current"
    assert "stale_first_seen" not in third["services"]["x"]
    assert json.loads(out.read_text(encoding="utf-8"))["services"]["x"]["state"] == "current"


def test_the_probe_iterates_the_port_registry(monkeypatch, tmp_path):
    import lw_ports
    seen = []
    monkeypatch.setattr(probe, "probe_one", lambda name, port, **k: seen.append((name, port))
                        or {"state": "down"})
    probe.run(head=A, out=tmp_path / "o.json")
    assert sorted(seen) == sorted(lw_ports.ALLOCATIONS.items())
