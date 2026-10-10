"""LW Monitor - read-only pipeline dashboard server (spec: docs/research/LW_MONITOR_SPEC.md).

Serves web/monitor.html plus JSON APIs over 127.0.0.1:8901 on the shared
tools/lw_httpd.py scaffold (stdlib only, zero required dependencies; Pillow
optional for real thumbnails). This module owns the pipeline routes and the
pipeline view; the transport, the Host guard and the bind-first single-instance
guard are lw_httpd's. Reads
ops/runtime/pipeline_state.json written atomically by lw_pipeline.py and the
append-only PIPELINE_LOG.md at the project root. The reader is tolerant per
the 7 binding rules in spec section 3.2 - drift in the producer's shape is
never fatal.

Launch: pythonw.exe tools/lw_monitor.py --open  (Desktop shortcut "LW Monitor").
Runs under pythonw - no console, all output goes to logs/lw_monitor.log.
Stop: POST /api/shutdown, or taskkill /F /PID <pid> (pid from /api/health).
"""

from __future__ import annotations

import argparse
import io
import json
import logging
import os
import re
import sys
import threading
import time
import webbrowser
from collections import OrderedDict, deque
from pathlib import Path
from urllib.parse import parse_qs, urlparse

# Legion focus-steal rule: every subprocess authored in this repo must pass
# creationflags=CREATE_NO_WINDOW. No subprocess is spawned in v1, but the
# constant stays as the seam for any future widget (git/HEAD etc).
CREATE_NO_WINDOW = 0x08000000 if os.name == "nt" else 0

ROOT = Path(__file__).resolve().parent.parent

if str(ROOT) not in sys.path:  # launched as a script, not as tools.lw_monitor
    sys.path.insert(0, str(ROOT))
if str(ROOT / "tools") not in sys.path:  # sibling tools (lw_review_threads -> lw_pipeline)
    sys.path.insert(0, str(ROOT / "tools"))

from tools.lw_httpd import (  # noqa: E402
    BaseLWHandler,
    LWServer,
    age_text,
    iso_from_epoch,
    parse_ts,
    read_json_tolerant,
    serve_or_defer,
    setup_logging,
)

STATE_PATH = ROOT / "ops" / "runtime" / "pipeline_state.json"
LOG_PATH = ROOT / "PIPELINE_LOG.md"  # project-root append-only log (build-wave contract)
PAGE_PATH = ROOT / "web" / "monitor.html"
REVIEW_PAGE_PATH = ROOT / "web" / "review.html"   # spatial review bench (P1-2)
REVIEW_ROOT = ROOT / "ops" / "runtime" / "review"
REVIEW_BODY_MAX = 65536
AB_ROOT = ROOT / "ops" / "runtime" / "ab_r4"   # R4 blind A/B (tools/lw_ab_r4.py)
AB_PAGE_PATH = ROOT / "web" / "ab_r4.html"
DEFAULT_IMAGE_ROOTS = [ROOT / "images"]
MONITOR_LOG = ROOT / "logs" / "lw_monitor.log"


def default_log_file() -> Path:
    """lw_monitor.log under $LW_LOG_DIR when non-blank, else MONITOR_LOG - resolved at
    call time (lw_paths.log_dir mirrored; LOG-LEAK-2)."""
    env = os.environ.get("LW_LOG_DIR", "").strip()
    return Path(env) / "lw_monitor.log" if env else MONITOR_LOG


HOST = "127.0.0.1"
DEFAULT_PORT = 8901
STUCK_S = 900.0
DONE_CAP = 5
LOG_TAIL_MAX = 200
THUMB_MAX_RAW_BYTES = 2 * 1024 * 1024
THUMB_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}
THUMB_CACHE_CAP = 128

log = logging.getLogger("lw_monitor")

# Stage names fall back to the agreed images/ folder contract when the state
# file does not carry its own stage_names map.
DEFAULT_STAGE_NAMES = {
    "0": "Originals",
    "1": "First Pass Scratch",
    "2": "First Pass Done",
    "3": "Cleaning Scratch",
    "4": "Cleaning Done",
    "5": "Final Scratch",
    "6": "Final Done",
    "7": "Last Scratch",
    "8": "End Review",
    "9": "Image Backup",
    "?": "Unknown Stage",
}

# PIPELINE_STATE_MACHINE.md section 2.3 state names -> stage folder number.
STATE_TO_STAGE = {
    "PENDING_INTAKE": 0,
    "FIRST_SCRATCH": 1,
    "FIRST_DONE": 2,
    "CLEAN_SCRATCH": 3,
    "CLEAN_DONE": 4,
    "FINAL_SCRATCH": 5,
    "FINAL_DONE": 6,
    "LAST_SCRATCH": 7,
    "END_REVIEW": 8,
    "PASSED": 9,
}

CANONICAL_PHASES = ("_initial", "_working", "_needauth", "_done")

# Accepts both the generic four (_working) and the producer's stage-prefixed
# tokens (_firstworking_02, _cleanneedauth, _lastdone, ...).
_PHASE_RE = re.compile(r"^_(?:first|clean|final|last)?(initial|needauth|done|working)(?:_[0-9]+)?$")

_MODULE_VIEW_CACHE: dict = {}  # last-good pipeline_state payloads, keyed by path


# ------------------------------------------------------------------ helpers


def classify_phase(phase):
    """Phase string -> one of the four canonical classes, or None for unknown."""
    if not isinstance(phase, str):
        return None
    m = _PHASE_RE.match(phase.strip())
    if not m:
        return None
    return "_" + m.group(1)


def _derive_stage(item):
    """Stage bucket key as str, or '?' (tolerance rule 3)."""
    s = item.get("stage")
    if isinstance(s, bool):
        return "?"
    if isinstance(s, int):
        return str(s)
    if isinstance(s, str) and s.strip().isdigit():
        return str(int(s.strip()))
    # producer shape: derive from the section 2.3 state name
    st = item.get("state")
    if isinstance(st, str) and st.strip().upper() in STATE_TO_STAGE:
        return str(STATE_TO_STAGE[st.strip().upper()])
    return "?"


def _derive_phase(item):
    """Verbatim phase string; producer state/substate mapped; default _initial."""
    phase = item.get("phase")
    if isinstance(phase, str) and phase.strip():
        return phase.strip()
    sub = item.get("substate")
    if isinstance(sub, str):
        u = sub.strip().upper()
        if u == "NEEDAUTH":
            return "_needauth"
        if u == "APPROVED_PENDING_MOVE":
            return "_done"
        if u == "EDITING":
            wm = item.get("working_max")
            if isinstance(wm, int) and not isinstance(wm, bool) and wm >= 1:
                return "_working"
            return "_initial"
    st = item.get("state")
    if isinstance(st, str):
        u = st.strip().upper()
        if u in ("FIRST_DONE", "CLEAN_DONE", "FINAL_DONE", "END_REVIEW", "PASSED"):
            return "_done"
        if u.endswith("_SCRATCH"):
            return "_working"
    return "_initial"


def _derive_id(item, key_id, index):
    if key_id:
        return str(key_id)
    v = item.get("id")
    if isinstance(v, str) and v.strip():
        return v.strip()
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        return str(v)
    f = item.get("file")
    if isinstance(f, str) and f.strip():
        stem = Path(f.replace("\\", "/")).stem
        if stem:
            return stem
    return f"item-{index}"


def _norm_item(item, key_id, index, fallback_ts, now_ts, stuck_s):
    phase = _derive_phase(item)
    phase_class = classify_phase(phase)
    ts_raw = item.get("ts")
    if not isinstance(ts_raw, str):
        ts_raw = item.get("last_op_ts")
    ts_epoch = parse_ts(ts_raw)
    ts_iso = ts_raw if isinstance(ts_raw, str) and ts_epoch is not None else None
    if ts_epoch is None and fallback_ts is not None:
        ts_epoch = fallback_ts
        ts_iso = iso_from_epoch(fallback_ts)
    age_s = None
    if ts_epoch is not None:
        age_s = max(0.0, round(now_ts - ts_epoch, 1))
    error = item.get("error")
    error = str(error) if error not in (None, "") else None
    needauth = item.get("needauth")
    needauth = str(needauth) if needauth not in (None, "") else None
    note = item.get("note")
    note = str(note) if note not in (None, "") else None
    actor = item.get("actor")
    actor = str(actor) if actor not in (None, "") else None
    file_field = item.get("file")
    file_field = str(file_field) if isinstance(file_field, str) and file_field.strip() else None
    thumb = item.get("thumb")
    thumb = str(thumb) if isinstance(thumb, str) and thumb.strip() else None
    stuck = bool(phase_class == "_working" and age_s is not None and age_s > stuck_s)
    return {
        "id": _derive_id(item, key_id, index),
        "file": file_field,
        "stage": _derive_stage(item),
        "phase": phase,
        "phase_class": phase_class,
        "ts": ts_iso,
        "ts_epoch": ts_epoch,
        "actor": actor,
        "note": note,
        "error": error,
        "needauth": needauth,
        "thumb": thumb,
        "age_s": age_s,
        "stuck": stuck,
    }


# ------------------------------------------------------------- pure builder


def build_pipeline_view(state_path, now_ts=None, *, done_cap=DONE_CAP, stuck_s=STUCK_S, cache=None):
    """Normalize pipeline_state.json into the /api/pipeline payload.

    Pure and injectable: state_path + now_ts + cache come from the caller.
    Implements every tolerance rule in spec section 3.2; never raises on
    producer drift, garbage JSON, or a missing file.
    """
    if now_ts is None:
        now_ts = time.time()
    if cache is None:
        cache = _MODULE_VIEW_CACHE
    state_path = Path(state_path)
    out = {
        "ok": True,
        "state_present": False,
        "stale": False,
        "run_id": None,
        "state_updated_at": None,
        "state_mtime_iso": None,
        "counts": {"?": 0},
        "phase_counts": {p: 0 for p in CANONICAL_PHASES},
        "attention": [],
        "stages": [],
        "updated_at": iso_from_epoch(now_ts),
    }
    # rules 5 + 6: absent or unparsable is normal traffic, and a torn read
    # falls back to the last good payload rather than blanking the board.
    read = read_json_tolerant(state_path, cache, now_ts=now_ts)
    state = read["data"]
    mtime = read["mtime"]
    if read["stale"]:
        out["stale"] = True
        out["stale_since"] = read["stale_since"]
    if state is None:
        return out
    if not isinstance(state, dict):
        state = {}
    out["state_present"] = True
    out["state_mtime_iso"] = iso_from_epoch(mtime) if mtime is not None else None

    run_id = state.get("run_id")
    out["run_id"] = str(run_id) if run_id not in (None, "") else None
    updated = state.get("updated_at")
    if not isinstance(updated, str):
        updated = state.get("generated_ts")
    out["state_updated_at"] = updated if isinstance(updated, str) else None

    stage_names = {}
    raw_names = state.get("stage_names")
    if isinstance(raw_names, dict):
        for k, v in raw_names.items():
            if isinstance(v, str) and v.strip():
                stage_names[str(k)] = v.strip()

    # rule 1: images as list or dict-keyed-by-id; anything else -> empty
    imgs_raw = state.get("images")
    items = []
    if isinstance(imgs_raw, list):
        for i, it in enumerate(imgs_raw):
            items.append(_norm_item(it if isinstance(it, dict) else {}, None, i, mtime, now_ts, stuck_s))
    elif isinstance(imgs_raw, dict):
        for i, (k, it) in enumerate(imgs_raw.items()):
            items.append(_norm_item(it if isinstance(it, dict) else {}, str(k), i, mtime, now_ts, stuck_s))

    # counts + phase_counts
    counts = {"?": 0}
    phase_counts = {p: 0 for p in CANONICAL_PHASES}
    buckets = {}
    for item in items:
        bucket = item["stage"]
        counts[bucket] = counts.get(bucket, 0) + 1
        pkey = item["phase_class"] or item["phase"]
        phase_counts[pkey] = phase_counts.get(pkey, 0) + 1
        buckets.setdefault(bucket, []).append(item)
    # producer-counts top-up (tolerance spirit, spec 3.2): lw_pipeline's
    # scan_tree tracks pre-intake originals ONLY as counts.pending_intake -
    # no per-image entries exist before intake - so count-only stages must
    # still surface their pressure. Never double counts tracked images.
    extra_counts = {}
    raw_counts = state.get("counts")
    if isinstance(raw_counts, dict):
        for k, v in raw_counts.items():
            if isinstance(v, bool) or not isinstance(v, int) or v <= 0:
                continue
            u = str(k).strip().upper()
            if u not in STATE_TO_STAGE:
                continue  # e.g. 'anomalies' - not a stage bucket
            bucket = str(STATE_TO_STAGE[u])
            extra = v - len(buckets.get(bucket, ()))
            if extra <= 0:
                continue
            extra_counts[bucket] = extra_counts.get(bucket, 0) + extra
            counts[bucket] = counts.get(bucket, 0) + extra
            if u == "PENDING_INTAKE":
                cls = "_initial"
            elif u.endswith("_SCRATCH"):
                cls = "_working"
            else:
                cls = "_done"
            phase_counts[cls] = phase_counts.get(cls, 0) + extra
    out["counts"] = counts
    out["phase_counts"] = phase_counts

    # attention lane: needauth > error > stuck, newest first within kind
    kind_rank = {"needauth": 0, "error": 1, "stuck": 2}
    attention = []
    for item in items:
        if item["phase_class"] == "_needauth":
            kind = "needauth"
            reason = item["needauth"] or item["note"] or "needs authorization"
        elif item["error"]:
            kind = "error"
            reason = item["error"]
        elif item["stuck"]:
            kind = "stuck"
            reason = f"working for {age_text(item['age_s'])}"
        else:
            continue
        attention.append({
            "id": item["id"], "file": item["file"], "stage": item["stage"],
            "phase": item["phase"], "reason": reason, "ts": item["ts"],
            "ts_epoch": item["ts_epoch"], "actor": item["actor"],
            "age_s": item["age_s"], "kind": kind,
        })
    anomalies = state.get("anomalies")
    if isinstance(anomalies, list):
        for i, a in enumerate(anomalies):
            if not isinstance(a, dict):
                a = {}
            aid = a.get("slug") or a.get("id") or f"anomaly-{i}"
            klass = a.get("class")
            detail = a.get("detail")
            parts = [str(x) for x in (klass, detail) if x not in (None, "")]
            attention.append({
                "id": str(aid), "file": None, "stage": "?", "phase": None,
                "reason": ": ".join(parts) or "anomaly", "ts": None,
                "ts_epoch": None, "actor": None, "age_s": None, "kind": "error",
            })
    attention.sort(key=lambda a: (kind_rank[a["kind"]], -(a["ts_epoch"] or 0.0)))
    for a in attention:
        a.pop("ts_epoch", None)
    out["attention"] = attention

    # stage groups: 0-9 ascending then "?", active-first then newest inside
    phase_rank = {"_working": 0, "_needauth": 1, "_initial": 2, None: 3, "_done": 4}
    def bucket_sort(b):
        return (1, 0) if b == "?" else (0, int(b))
    stages = []
    for bucket in sorted(set(buckets) | set(extra_counts), key=bucket_sort):
        group = buckets.get(bucket, [])
        group.sort(key=lambda it: (phase_rank.get(it["phase_class"], 3),
                                   -(it["ts_epoch"] or 0.0)))
        listed = []
        done_listed = 0
        for it in group:
            if it["phase_class"] == "_done":
                if done_listed >= done_cap:
                    continue
                done_listed += 1
            listed.append(it)
        for it in listed:
            it.pop("ts_epoch", None)
        name = stage_names.get(bucket) or DEFAULT_STAGE_NAMES.get(bucket) or f"Stage {bucket}"
        stages.append({
            "stage": bucket if bucket == "?" else int(bucket),
            "name": name,
            "count": len(group) + extra_counts.get(bucket, 0),
            "items": listed,
        })
    out["stages"] = stages
    return out


# ------------------------------------------------------------------ log tail


def tail_log(log_path, n=60):
    """Tail of PIPELINE_LOG - deque big-file idiom, absent file fail-soft."""
    try:
        n = int(n)
    except (TypeError, ValueError):
        n = 60
    n = max(1, min(n, LOG_TAIL_MAX))
    try:
        with Path(log_path).open("r", encoding="utf-8", errors="replace") as fh:
            lines = list(deque(fh, maxlen=n))
    except OSError:
        return {"ok": True, "present": False, "lines": []}
    return {"ok": True, "present": True, "lines": [ln.rstrip("\r\n") for ln in lines]}


# -------------------------------------------------------------------- thumbs


_THUMB_CACHE: "OrderedDict[tuple, tuple]" = OrderedDict()
_THUMB_LOCK = threading.Lock()
_RAW_CTYPES = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}


def _validate_thumb_path(raw, roots):
    """Spec 5.1: resolve + is_relative_to root(s) + suffix allowlist + is_file."""
    if not isinstance(raw, str) or not raw.strip():
        return None
    try:
        p = Path(raw.strip())
        if not p.is_absolute():
            p = ROOT / p
        resolved = p.resolve()
    except (OSError, ValueError):
        return None
    if resolved.suffix.lower() not in THUMB_SUFFIXES:
        return None
    inside = False
    for root in roots:
        try:
            if resolved.is_relative_to(Path(root).resolve()):
                inside = True
                break
        except (OSError, ValueError):
            continue
    if not inside:
        return None
    try:
        if not resolved.is_file():
            return None
    except OSError:
        return None
    return resolved


def make_thumb(resolved):
    """(bytes, content_type) or None. Pillow downscale; raw-bytes fallback <= 2 MB."""
    try:
        mtime = resolved.stat().st_mtime
    except OSError:
        return None
    key = (str(resolved), mtime)
    with _THUMB_LOCK:
        cached = _THUMB_CACHE.get(key)
        if cached is not None:
            _THUMB_CACHE.move_to_end(key)
            return cached
    try:
        from PIL import Image
    except ImportError:
        Image = None
    if Image is None:
        try:
            if resolved.stat().st_size > THUMB_MAX_RAW_BYTES:
                return None
            data = resolved.read_bytes()
        except OSError:
            return None
        result = (data, _RAW_CTYPES.get(resolved.suffix.lower(), "application/octet-stream"))
    else:
        try:
            with Image.open(resolved) as im:
                im.thumbnail((256, 256))
                if im.mode in ("RGBA", "LA", "P"):
                    rgba = im.convert("RGBA")
                    bg = Image.new("RGB", rgba.size, (255, 255, 255))
                    bg.paste(rgba, mask=rgba.split()[-1])
                    im = bg
                elif im.mode != "RGB":
                    im = im.convert("RGB")
                buf = io.BytesIO()
                im.save(buf, "JPEG", quality=80)
            result = (buf.getvalue(), "image/jpeg")
        except (OSError, ValueError):
            return None
    with _THUMB_LOCK:
        _THUMB_CACHE[key] = result
        while len(_THUMB_CACHE) > THUMB_CACHE_CAP:
            _THUMB_CACHE.popitem(last=False)
    return result


# -------------------------------------------------------------------- server


class MonitorServer(LWServer):
    def __init__(self, addr, handler, *, state_path=STATE_PATH, log_path=LOG_PATH,
                 page_path=PAGE_PATH, image_roots=None, cache=None,
                 review_root=REVIEW_ROOT, review_page=REVIEW_PAGE_PATH,
                 ab_root=AB_ROOT, ab_page=AB_PAGE_PATH):
        super().__init__(addr, handler)
        self.ab_root = Path(ab_root)
        self.ab_page = Path(ab_page)
        self.review_root = Path(review_root)
        self.review_page = Path(review_page)
        self.state_path = Path(state_path)
        self.log_path = Path(log_path)
        self.page_path = Path(page_path)
        self.image_roots = [Path(r) for r in (image_roots or DEFAULT_IMAGE_ROOTS)]
        self.view_cache = {} if cache is None else cache


class Handler(BaseLWHandler):
    server_version = "LWMonitor/1.0"
    logger_name = "lw_monitor"

    def _route(self, method):
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)
        srv = self.server
        if method == "GET":
            if path in ("/", "/monitor"):
                try:
                    body = srv.page_path.read_bytes()
                except OSError:
                    self._send_json(404, {"ok": False, "error": "monitor page missing"})
                    return
                self._send(200, body, "text/html; charset=utf-8", {"Cache-Control": "no-store"})
                return
            if path == "/review" or path.startswith("/api/review/"):
                self._review_get(path, query)
                return
            if path == "/ab" or path.startswith("/api/ab/"):
                self._ab_get(path, query)
                return
            if path == "/api/pipeline":
                view = build_pipeline_view(srv.state_path, cache=srv.view_cache)
                self._send_json(200, view, {"Cache-Control": "no-store"})
                return
            if path == "/api/log":
                n = (query.get("n") or ["60"])[0]
                self._send_json(200, tail_log(srv.log_path, n), {"Cache-Control": "no-store"})
                return
            if path == "/api/thumb":
                raw = (query.get("path") or [""])[0]
                resolved = _validate_thumb_path(raw, srv.image_roots)
                if resolved is None:
                    self._send_json(403, {"ok": False})  # no path echo
                    return
                result = make_thumb(resolved)
                if result is None:
                    self._send_json(503, {"ok": False, "error": "thumb unavailable - install Pillow"})
                    return
                data, ctype = result
                self._send(200, data, ctype, {"Cache-Control": "max-age=300"})
                return
            if path == "/api/health":
                self._send_json(200, {
                    "ok": True,
                    "pid": os.getpid(),
                    "started_iso": srv.started_iso,
                    "port": srv.server_address[1],
                    "state_present": srv.state_path.is_file(),
                })
                return
        if method == "POST" and path.startswith("/api/review/"):
            self._review_post(path)
            return
        if method == "POST" and path.startswith("/api/ab/"):
            self._ab_post(path)
            return
        if method == "POST" and path == "/api/shutdown":
            self._send_json(200, {"ok": True})
            threading.Thread(target=srv.shutdown, daemon=True).start()
            return
        self._send_json(404, {"ok": False, "error": "not found"})


    # ------------------------------------------------ review bench (P1-2)
    # Loopback only (the scaffold's Host guard runs first). Writes need a JSON
    # content type, so a cross-site "simple" form post cannot reach them, and a
    # capped body. Errors never echo a path.

    def _review_get(self, path, query):
        import lw_review_threads as rt
        srv = self.server
        images = srv.image_roots[0] if srv.image_roots else DEFAULT_IMAGE_ROOTS[0]
        if path == "/review":
            try:
                body = srv.review_page.read_bytes()
            except OSError:
                self._send_json(404, {"ok": False, "error": "review page missing"})
                return
            self._send(200, body, "text/html; charset=utf-8", {"Cache-Control": "no-store"})
            return
        if path == "/api/review/slugs":
            self._send_json(200, {"ok": True, "slugs": rt.reviewable_slugs(images)},
                            {"Cache-Control": "no-store"})
            return
        slug = rt.normalize_slug((query.get("slug") or [""])[0])
        if not rt.SLUG_RE.match(slug or ""):
            self._send_json(400, {"ok": False, "error": "bad slug"})
            return
        if path == "/api/review/image":
            img = rt.latest_image(slug, images)
            if img is None or img.suffix.lower() not in _RAW_CTYPES:
                self._send_json(404, {"ok": False, "error": "no image for that slug"})
                return
            # 1:1 and byte-for-byte: no re-encode, no downscale (a review of
            # faint residue from a resampled view is the unreliable case).
            self._send(200, img.read_bytes(), _RAW_CTYPES[img.suffix.lower()],
                       {"Cache-Control": "no-store"})
            return
        if path == "/api/review/threads":
            threads = rt.list_threads(srv.review_root, slug=slug)
            every = rt.list_threads(srv.review_root)
            self._send_json(200, {"ok": True, "threads": threads,
                                  "unpublished": sum(1 for t in threads if not t.get("published")),
                                  "unpublished_all": sum(1 for t in every if not t.get("published"))},
                            {"Cache-Control": "no-store"})
            return
        if path == "/api/review/shot":
            name = (query.get("name") or [""])[0]
            if not _SHOT_RE.match(name or ""):
                self._send_json(400, {"ok": False, "error": "bad shot name"})
                return
            p = srv.review_root / slug / name
            if not p.is_file():
                self._send_json(404, {"ok": False, "error": "no such shot"})
                return
            self._send(200, p.read_bytes(), "image/png", {"Cache-Control": "no-store"})
            return
        self._send_json(404, {"ok": False, "error": "not found"})

    def _review_body(self):
        ctype = (self.headers.get("Content-Type") or "").split(";")[0].strip().lower()
        if ctype != "application/json":
            self._send_json(415, {"ok": False, "error": "application/json required"})
            return None
        try:
            n = int(self.headers.get("Content-Length") or "0")
        except ValueError:
            n = -1
        if n < 0 or n > REVIEW_BODY_MAX:
            self._send_json(413, {"ok": False, "error": "body too large"})
            self.close_connection = True
            return None
        try:
            return json.loads(self.rfile.read(n) or b"{}")
        except ValueError:
            self._send_json(400, {"ok": False, "error": "body is not JSON"})
            return None

    def _review_post(self, path):
        import lw_review_threads as rt
        srv = self.server
        body = self._review_body()
        if body is None:
            return
        images = srv.image_roots[0] if srv.image_roots else DEFAULT_IMAGE_ROOTS[0]
        try:
            if path == "/api/review/mark":
                rec = rt.submit(rt.normalize_slug(body.get("slug")), body.get("xy"), body.get("r"), body.get("said"),
                                body.get("view") or {}, review_root=srv.review_root,
                                images_root=images)
                self._send_json(200, {"ok": True, "id": rec["id"], "state": rec["state"]})
                return
            if path == "/api/review/publish":
                m = rt.publish(srv.review_root)
                self._send_json(200, {"ok": True, "count": len(m["items"]) if m else 0,
                                      "batch": m["batch"] if m else None})
                return
            if path == "/api/review/followup":
                t = rt.follow_up(body.get("slug"), body.get("id"), body.get("said"),
                                 review_root=srv.review_root)
                self._send_json(200, {"ok": True, "state": t["state"]})
                return
        except rt.ReviewError as exc:
            self._send_json(400, {"ok": False, "error": str(exc)})
            return
        self._send_json(404, {"ok": False, "error": "not found"})

    # ------------------------------------------------ R4 blind A/B (ADR-009)
    # The page sees slug order, crops and SIDE-only votes. The key (which
    # engine is on which side) and the tally are never served: the tally is
    # `python tools/lw_ab_r4.py tally`, and it refuses until the operator has
    # pressed Finish. Same loopback + JSON-content-type write rules as review.

    def _ab_get(self, path, query):
        import lw_ab_r4 as ab
        srv = self.server
        if path == "/ab":
            try:
                body = srv.ab_page.read_bytes()
            except OSError:
                self._send_json(404, {"ok": False, "error": "A/B page missing"})
                return
            self._send(200, body, "text/html; charset=utf-8", {"Cache-Control": "no-store"})
            return
        if path == "/api/ab/items":
            self._send_json(200, dict(ab.items_view(srv.ab_root), ok=True),
                            {"Cache-Control": "no-store"})
            return
        if path == "/api/ab/img":
            p = ab.image_path(srv.ab_root, (query.get("slug") or [""])[0],
                              (query.get("name") or [""])[0])
            if p is None:
                self._send_json(404, {"ok": False, "error": "no such crop"})
                return
            self._send(200, p.read_bytes(), "image/png", {"Cache-Control": "no-store"})
            return
        self._send_json(404, {"ok": False, "error": "not found"})

    def _ab_post(self, path):
        import lw_ab_r4 as ab
        srv = self.server
        body = self._review_body()
        if body is None:
            return
        try:
            if path == "/api/ab/vote":
                v = ab.record_vote(srv.ab_root, body.get("slug"), body.get("choice"))
                self._send_json(200, {"ok": True, "voted": len(v["votes"])})
                return
            if path == "/api/ab/finish":
                ab.finish(srv.ab_root)
                self._send_json(200, {"ok": True, "finished": True})
                return
        except ab.ABError as exc:
            self._send_json(400, {"ok": False, "error": str(exc)})
            return
        self._send_json(404, {"ok": False, "error": "not found"})


_SHOT_RE = re.compile(r"^m[0-9]{8}T[0-9]{6}-[0-9a-f]{6}_(before|reply_[0-9]{2})\.png$")


# ---------------------------------------------------------------------- main


def resolve_state_path(args):
    """--state-file, else <--runtime-root>/pipeline_state.json (ingest P2-6), else live."""
    if args.state_file:
        return Path(args.state_file)
    if getattr(args, "runtime_root", None):
        return Path(args.runtime_root) / STATE_PATH.name
    return STATE_PATH


def main(argv=None):
    ap = argparse.ArgumentParser(description="LW pipeline monitor server (127.0.0.1 only)")
    ap.add_argument("--open", action="store_true", dest="open_browser",
                    help="open the monitor page in the default browser")
    ap.add_argument("--port", type=int, default=DEFAULT_PORT)
    ap.add_argument("--images-root", action="append", default=None,
                    help="allowed thumbnail root (repeatable); default <repo root>\\images")
    ap.add_argument("--log-file", default=None, help="PIPELINE_LOG path override")
    ap.add_argument("--state-file", default=None, help="pipeline_state.json path override")
    ap.add_argument("--runtime-root", default=None,
                    help="read pipeline_state.json from this dir (a verify copy made by "
                         "tools/lw_verify_snapshot.py); --state-file still wins")
    # INJECTION POINT, added 2026-09-11. Without it `main()` always attached a
    # handler to the operator's real log, so every arm driving `main()` reached
    # it. Measured by tracing the suite's writes, alongside the same defect in
    # `lw_facts`, where it was writing acknowledgement state rather than a log.
    ap.add_argument("--monitor-log", default=None,
                    help="lw_monitor.log path override (tests inject a temporary one)")
    args = ap.parse_args(argv)
    setup_logging(Path(args.monitor_log) if args.monitor_log else default_log_file())
    image_roots = [Path(r) for r in args.images_root] if args.images_root else list(DEFAULT_IMAGE_ROOTS)
    state_path = resolve_state_path(args)
    url = f"http://{HOST}:{args.port}/"
    log.info("lw_monitor state=%s", state_path)

    def factory():
        return MonitorServer(
            (HOST, args.port), Handler,
            state_path=state_path,
            log_path=Path(args.log_file) if args.log_file else LOG_PATH,
            image_roots=image_roots,
        )

    # webbrowser.open routes through os.startfile - no console flash
    return serve_or_defer(factory, url, name="lw_monitor", log=log,
                          open_url=webbrowser.open if args.open_browser else None)


if __name__ == "__main__":
    raise SystemExit(main())
