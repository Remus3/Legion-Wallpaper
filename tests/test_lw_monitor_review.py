"""Review bench routes on the monitor server (directive P1-2).

Real HTTP on an ephemeral loopback port, tmp_path images and review roots.
Pins: the page is served; a mark POST needs a JSON content type (a simple
cross-site form post cannot write); bad slugs and shot names are refused with
no path echo; three marks + one publish = one notification listing three ids;
the image route serves the slug's latest working image byte-for-byte (no
re-encode, no downscale).
"""
from __future__ import annotations

import http.client
import json
import sys
import threading
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

from tools import lw_monitor  # noqa: E402


@pytest.fixture
def bench(tmp_path):
    images = tmp_path / "images"
    d = images / "3.Cleaning Scratch" / "ahri"
    d.mkdir(parents=True)
    arr = np.random.default_rng(0).integers(0, 256, size=(144, 256, 3), dtype=np.uint8)
    Image.fromarray(arr).save(d / "ahri_cleanworking_01.png")
    review = tmp_path / "review"
    page = tmp_path / "review.html"
    page.write_text("<h1>BENCH</h1>", encoding="utf-8")
    state = tmp_path / "state.json"
    state.write_text("{}", encoding="utf-8")
    srv = lw_monitor.MonitorServer(
        ("127.0.0.1", 0), lw_monitor.Handler, state_path=state,
        log_path=tmp_path / "log.md", page_path=tmp_path / "monitor.html",
        image_roots=[images], cache={}, review_root=review, review_page=page)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    try:
        yield srv, d / "ahri_cleanworking_01.png", review
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


MARK = {"slug": "ahri", "xy": [100, 60], "r": 12, "said": "ghost here",
        "view": {"x0": 0, "y0": 0, "x1": 200, "y1": 120}}


def test_page_is_served(bench):
    srv, _, _ = bench
    status, ctype, body = _req(srv, "GET", "/review")
    assert status == 200 and ctype.startswith("text/html") and b"BENCH" in body


def test_image_route_serves_the_latest_working_byte_for_byte(bench):
    srv, path, _ = bench
    status, ctype, body = _req(srv, "GET", "/api/review/image?slug=ahri")
    assert status == 200 and ctype == "image/png"
    assert body == path.read_bytes()


def test_mark_requires_json_content_type(bench):
    srv, _, review = bench
    status, _, _ = _req(srv, "POST", "/api/review/mark", json.dumps(MARK).encode(),
                        ctype="text/plain")
    assert status == 415
    assert not review.exists() or not list(review.rglob("m*.json"))


def test_three_marks_one_publish_one_notification(bench):
    srv, _, review = bench
    ids = []
    for i in range(3):
        m = dict(MARK, xy=[20 + 30 * i, 40], said=f"spot {i}")
        status, _, body = _req(srv, "POST", "/api/review/mark", m)
        assert status == 200, body
        ids.append(json.loads(body)["id"])
    status, _, body = _req(srv, "GET", "/api/review/threads?slug=ahri")
    payload = json.loads(body)
    assert payload["unpublished"] == 3 and len(payload["threads"]) == 3
    status, _, body = _req(srv, "POST", "/api/review/publish", {})
    assert status == 200 and json.loads(body)["count"] == 3
    lines = (review / "notifications.jsonl").read_text(encoding="ascii").splitlines()
    assert len(lines) == 1
    note = json.loads(lines[0])
    assert sorted(note["ids"]) == sorted(f"ahri/{i}" for i in ids)


def test_followup_reopens(bench):
    srv, _, _ = bench
    _, _, body = _req(srv, "POST", "/api/review/mark", MARK)
    mid = json.loads(body)["id"]
    _req(srv, "POST", "/api/review/publish", {})
    status, _, body = _req(srv, "POST", "/api/review/followup",
                           {"slug": "ahri", "id": mid, "said": "still there"})
    assert status == 200 and json.loads(body)["state"] == "new"


def test_bad_inputs_refused_without_path_echo(bench):
    srv, _, _ = bench
    for path in ("/api/review/image?slug=..%2F..%2Fx", "/api/review/shot?slug=ahri&name=..%2Fx.png",
                 "/api/review/shot?slug=ahri&name=secret.txt", "/api/review/threads?slug=%3Cx%3E"):
        status, _, body = _req(srv, "GET", path)
        assert status in (400, 404), path
        assert b"\\\\" not in body and b"images" not in body
    status, _, _ = _req(srv, "POST", "/api/review/mark", dict(MARK, xy=[9999, 1]))
    assert status == 400


def test_shot_route_serves_the_before_crop(bench):
    srv, _, _ = bench
    _, _, body = _req(srv, "POST", "/api/review/mark", MARK)
    rec = json.loads(body)
    status, ctype, png = _req(srv, "GET", f"/api/review/shot?slug=ahri&name={rec['id']}_before.png")
    assert status == 200 and ctype == "image/png" and png[:8] == b"\x89PNG\r\n\x1a\n"


def test_post_body_is_capped(bench):
    srv, _, _ = bench
    status, _, _ = _req(srv, "POST", "/api/review/mark", b"{" + b" " * 70000 + b"}")
    assert status == 413


# ---------------------------------------------------------------- operator test 2026-10-04
# REAL FAILURE: the operator opened /review three times and no image ever showed.
# The server log holds three GET /review and ZERO image requests: the page
# offered no slug to load (a blank text box nobody can fill from memory) and
# showed a broken <img> placeholder with no src. These pin the fix: the page
# lists loadable slugs, auto-loads one, never shows a src-less <img>, and a
# pasted file name or path resolves to its slug.
def test_slugs_route_lists_only_slugs_whose_image_route_serves(bench, tmp_path):
    srv, _, _ = bench
    empty = tmp_path / "images" / "4.Cleaning Done" / "nothing-here"
    empty.mkdir(parents=True)
    status, _, body = _req(srv, "GET", "/api/review/slugs")
    slugs = json.loads(body)["slugs"]
    assert status == 200 and slugs == ["ahri"]
    for s in slugs:
        st, ctype, data = _req(srv, "GET", f"/api/review/image?slug={s}")
        assert st == 200 and ctype.startswith("image/") and len(data) > 0


def test_pasted_file_name_or_path_resolves_to_the_slug(bench):
    srv, path, _ = bench
    for raw in ("ahri_cleanworking_01.png", "3.Cleaning%20Scratch/ahri/ahri_cleanworking_01.png",
                "%20ahri%20"):
        st, ctype, data = _req(srv, "GET", f"/api/review/image?slug={raw}")
        assert st == 200 and data == path.read_bytes(), raw


def test_page_never_shows_a_src_less_image_and_offers_slugs():
    page = (Path(__file__).resolve().parents[1] / "web" / "review.html").read_text(encoding="utf-8")
    assert '<img id="img" alt="working image at 1:1" hidden>' in page
    assert "/api/review/slugs" in page and "<datalist" in page
    assert "img.hidden = false" in page


def test_path_like_slugs_reduce_to_a_basename_never_a_traversal(bench):
    """A pasted path is reduced to its last component: '../..' can never walk."""
    import lw_review_threads as rt
    assert rt.normalize_slug("../../etc/passwd") == "passwd"
    assert rt.normalize_slug("..") == ".."
    assert not rt.SLUG_RE.match(rt.normalize_slug(".."))
