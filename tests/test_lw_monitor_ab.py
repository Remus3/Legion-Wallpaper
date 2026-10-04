"""R4 blind A/B routes on the monitor server (/ab, /api/ab/*).

Real HTTP on an ephemeral loopback port with a tmp_path A/B root. Pins: the
page is served; items never name an engine; a vote needs a JSON content type;
votes and finish round-trip to votes.json; the image route serves only the
fixed crop names; no route exposes the key or a tally.
"""
from __future__ import annotations

import http.client
import json
import sys
import threading
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

import lw_ab_r4 as ab  # noqa: E402

from tools import lw_monitor  # noqa: E402


@pytest.fixture
def bench(tmp_path):
    root = tmp_path / "ab_r4"
    root.mkdir()
    ab.write_json_atomic(root / "items.json", {"items": [{"slug": "alpha"}, {"slug": "beta"}]})
    ab.write_json_atomic(root / "key.json", {"slugs": {
        "alpha": {"left": "lama", "right": "anime-lama"},
        "beta": {"left": "anime-lama", "right": "lama"}}})
    for s in ("alpha", "beta"):
        (root / s).mkdir()
        (root / s / "right_context.png").write_bytes(b"\x89PNG-" + s.encode())
    page = tmp_path / "ab.html"
    page.write_text("<h1>AB</h1>", encoding="utf-8")
    state = tmp_path / "state.json"
    state.write_text("{}", encoding="utf-8")
    srv = lw_monitor.MonitorServer(
        ("127.0.0.1", 0), lw_monitor.Handler, state_path=state,
        log_path=tmp_path / "log.md", page_path=tmp_path / "monitor.html",
        image_roots=[tmp_path / "images"], cache={}, review_root=tmp_path / "review",
        review_page=tmp_path / "review.html", ab_root=root, ab_page=page)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    try:
        yield srv, root
    finally:
        srv.shutdown()
        srv.server_close()
        t.join(timeout=5)


def _req(srv, method, path, body=None, ctype="application/json"):
    conn = http.client.HTTPConnection("127.0.0.1", srv.server_address[1], timeout=10)
    headers = {}
    data = None
    if body is not None:
        data = body if isinstance(body, bytes) else json.dumps(body).encode()
        headers["Content-Type"] = ctype
    conn.request(method, path, body=data, headers=headers)
    r = conn.getresponse()
    out = (r.status, r.getheader("Content-Type") or "", r.read())
    conn.close()
    return out


def test_page_is_served(bench):
    srv, _ = bench
    status, ctype, body = _req(srv, "GET", "/ab")
    assert status == 200 and ctype.startswith("text/html") and b"AB" in body


def test_items_are_blind(bench):
    srv, _ = bench
    status, _, body = _req(srv, "GET", "/api/ab/items")
    assert status == 200
    assert b"lama" not in body
    assert [i["slug"] for i in json.loads(body)["items"]] == ["alpha", "beta"]


def test_vote_needs_json_and_round_trips(bench):
    srv, root = bench
    status, _, _ = _req(srv, "POST", "/api/ab/vote",
                        json.dumps({"slug": "alpha", "choice": "left"}).encode(),
                        ctype="text/plain")
    assert status == 415 and not (root / "votes.json").exists()
    status, _, body = _req(srv, "POST", "/api/ab/vote", {"slug": "alpha", "choice": "left"})
    assert status == 200, body
    status, _, body = _req(srv, "POST", "/api/ab/vote", {"slug": "alpha", "choice": "lama"})
    assert status == 400
    status, _, body = _req(srv, "POST", "/api/ab/finish", {})
    assert status == 400  # beta has no vote yet
    _req(srv, "POST", "/api/ab/vote", {"slug": "beta", "choice": "same"})
    status, _, body = _req(srv, "POST", "/api/ab/finish", {})
    assert status == 200
    votes = json.loads((root / "votes.json").read_text(encoding="ascii"))
    assert votes["finished"] and set(votes["votes"]) == {"alpha", "beta"}


def test_image_route_serves_only_fixed_names(bench):
    srv, _ = bench
    status, ctype, body = _req(srv, "GET", "/api/ab/img?slug=beta&name=right_context.png")
    assert status == 200 and ctype == "image/png" and body == b"\x89PNG-beta"
    for q in ("slug=beta&name=key.json", "slug=..&name=right_context.png",
              "slug=beta&name=..%2Fkey.json"):
        status, _, body = _req(srv, "GET", f"/api/ab/img?{q}")
        assert status in (400, 404) and b"ab_r4" not in body


def test_no_route_exposes_the_key_or_a_tally(bench):
    srv, _ = bench
    for p in ("/api/ab/key", "/api/ab/tally", "/api/ab/key.json"):
        status, _, body = _req(srv, "GET", p)
        assert status == 404 and b"anime" not in body
