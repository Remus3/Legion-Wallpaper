"""Spatial review bench: marks on the image become threads (directive P1-2).

The operator's eye is the cleaning gate (zero-residue bar), but feedback used to
be prose, and the exact location of a ghost or a band was lost between
sessions. Here a mark is a point plus a radius on the slug's latest working
image, the words that go with it, and the exact 1:1 VIEW the operator was
looking at. Each mark is a thread: new -> answered -> fixed | wont; a follow-up
from the operator reopens it.

  - submissions land in ops/runtime/review/<slug>/<id>.json (+ a 1:1 crop of
    the view as the "before" shot, runtime only - no image bytes in git)
  - `publish` stamps every UNPUBLISHED mark with one batch id, writes one
    manifest and sends ONE notification for the batch
  - `answer` renders the reply shot from the SAME stored view of the current
    image, so before and after line up pixel for pixel
  - the bench never edits the artifact; applying a request is a separate step.
    `promote` turns a mark into a mask seed for the cleaning lane - operator
    initiated only.

Served by tools/lw_monitor.py (127.0.0.1 only) at /review.

  python tools/lw_review_threads.py list [--slug S]
  python tools/lw_review_threads.py publish
  python tools/lw_review_threads.py answer <slug> <id> --said "..."
  python tools/lw_review_threads.py state <slug> <id> fixed|wont
  python tools/lw_review_threads.py promote <slug> <id>
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

ROOT = Path(__file__).resolve().parents[1]
REVIEW_ROOT = ROOT / "ops" / "runtime" / "review"
IMAGES_ROOT = ROOT / "images"

STATES = ("new", "answered", "fixed", "wont")
SLUG_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,159}$")
ID_RE = re.compile(r"^m[0-9]{8}T[0-9]{6}-[0-9a-f]{6}$")
MAX_SAID = 2000
MAX_R = 1024


class ReviewError(ValueError):
    pass


def _now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _atomic_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(obj, indent=1, sort_keys=True) + "\n", encoding="ascii")
    os.replace(tmp, path)


def _check_slug(slug):
    if not isinstance(slug, str) or not SLUG_RE.match(slug):
        raise ReviewError("bad slug")
    return slug


def _check_id(mid):
    if not isinstance(mid, str) or not ID_RE.match(mid):
        raise ReviewError("bad id")
    return mid


def _ascii_text(text):
    if not isinstance(text, str) or not text.strip():
        raise ReviewError("said is required")
    text = text.strip()[:MAX_SAID]
    # stored files are ASCII by rule; keep the words, replace anything else
    return text.encode("ascii", "replace").decode("ascii")


# ---------------------------------------------------------------- the image
_MILESTONE_TAIL = re.compile(r"_(first|clean|final|last)(initial|done|needauth|working_[0-9]+)$")


def normalize_slug(raw):
    """A slug from what an operator pastes: a slug, a milestone file name, or a
    path ending in one (operator test 2026-10-04 - nobody types a slug from
    memory). Returns the bare slug string (validated later by _check_slug)."""
    text = str(raw or "").strip().replace("\\", "/")
    text = text.rsplit("/", 1)[-1]
    stem, dot, ext = text.rpartition(".")
    if dot and ext.lower() in ("png", "jpg", "jpeg", "webp"):
        text = stem
    return _MILESTONE_TAIL.sub("", text)


def reviewable_slugs(images_root=IMAGES_ROOT, cap=500):
    """Slugs that have a milestone image the bench can show, newest first."""
    import lw_pipeline
    root = Path(images_root)
    seen = {}
    for s in lw_pipeline.STAGES:
        for d in (root / lw_pipeline.SCRATCH_DIR[s], root / lw_pipeline.DONE_DIR[s]):
            if not d.is_dir():
                continue
            for sub in d.iterdir():
                if not sub.is_dir() or not SLUG_RE.match(sub.name) or sub.name in seen:
                    continue
                img = latest_image(sub.name, root)
                if img is not None:
                    seen[sub.name] = img.stat().st_mtime
    return [k for k, _ in sorted(seen.items(), key=lambda kv: -kv[1])][:cap]


def latest_image(slug, images_root=IMAGES_ROOT):
    """The slug's newest milestone image anywhere in the stage folders (the
    working the operator is reviewing), or None."""
    import lw_pipeline
    _check_slug(slug)
    root = Path(images_root)
    dirs = []
    for s in lw_pipeline.STAGES:
        dirs += [root / lw_pipeline.SCRATCH_DIR[s] / slug, root / lw_pipeline.DONE_DIR[s] / slug]
    best = None
    for d in dirs:
        if not d.is_dir():
            continue
        for p in d.iterdir():
            if (p.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp")
                    and p.name.startswith(slug + "_") and lw_pipeline.parse_milestone(p.name)):
                m = p.stat().st_mtime
                if best is None or m > best[0]:
                    best = (m, p)
    return best[1] if best else None


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _clamp_view(view, size):
    w, h = size
    try:
        x0, y0 = int(view["x0"]), int(view["y0"])
        x1, y1 = int(view["x1"]), int(view["y1"])
    except (KeyError, TypeError, ValueError):
        raise ReviewError("view needs integer x0 y0 x1 y1") from None
    x0, y0 = max(0, min(x0, w - 1)), max(0, min(y0, h - 1))
    x1, y1 = max(x0 + 1, min(x1, w)), max(y0 + 1, min(y1, h))
    return {"x0": x0, "y0": y0, "x1": x1, "y1": y1, "scale": 1.0}


def render_view(image_path, view, out_path):
    """1:1 crop of `view` from `image_path`, written atomically as PNG."""
    from PIL import Image
    with Image.open(image_path) as im:
        crop = im.convert("RGB").crop((view["x0"], view["y0"], view["x1"], view["y1"]))
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = out_path.with_name(out_path.name + ".part")
    crop.save(tmp, format="PNG")
    os.replace(tmp, out_path)
    return out_path


# ---------------------------------------------------------------- threads
def _path(review_root, slug, mid):
    return Path(review_root) / _check_slug(slug) / f"{_check_id(mid)}.json"


def new_id(now=None):
    stamp = time.strftime("%Y%m%dT%H%M%S", time.gmtime(now))
    return f"m{stamp}-{os.urandom(3).hex()}"


def submit(slug, xy, r, said, view, review_root=REVIEW_ROOT, images_root=IMAGES_ROOT,
           image_path=None):
    """Record one mark. Returns the stored record."""
    _check_slug(slug)
    img = Path(image_path) if image_path else latest_image(slug, images_root)
    if img is None or not img.is_file():
        raise ReviewError("no image for slug")
    from PIL import Image
    with Image.open(img) as im:
        size = im.size
    try:
        x, y = int(xy[0]), int(xy[1])
        rr = int(r)
    except (TypeError, ValueError, IndexError):
        raise ReviewError("xy must be [x, y] and r an integer") from None
    if not (0 <= x < size[0] and 0 <= y < size[1]) or not (1 <= rr <= MAX_R):
        raise ReviewError("mark outside the image or radius out of range")
    v = _clamp_view(view, size)
    mid = new_id()
    rec = {"kind": "mark", "id": mid, "slug": slug, "xy": [x, y], "r": rr,
           "said": _ascii_text(said), "view": v, "state": "new", "published": None,
           "created": _now(),
           "image": {"name": img.name, "sha256": _sha256(img), "size": list(size)},
           "shots": {"before": f"{mid}_before.png"},
           "thread": [{"role": "operator", "said": _ascii_text(said), "ts": _now()}]}
    render_view(img, v, Path(review_root) / slug / rec["shots"]["before"])
    _atomic_json(_path(review_root, slug, mid), rec)
    return rec


def load(slug, mid, review_root=REVIEW_ROOT):
    p = _path(review_root, slug, mid)
    if not p.is_file():
        raise ReviewError("no such thread")
    return json.loads(p.read_text(encoding="ascii"))


def list_threads(review_root=REVIEW_ROOT, slug=None):
    root = Path(review_root)
    out = []
    if not root.is_dir():
        return out
    dirs = [root / _check_slug(slug)] if slug else sorted(p for p in root.iterdir() if p.is_dir())
    for d in dirs:
        if not d.is_dir() or not SLUG_RE.match(d.name):
            continue
        for p in sorted(d.glob("m*.json")):
            if ID_RE.match(p.stem):
                try:
                    out.append(json.loads(p.read_text(encoding="ascii")))
                except (OSError, ValueError):
                    continue
    return out


def _file_sink(review_root):
    def notify(message: dict):
        p = Path(review_root) / "notifications.jsonl"
        p.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(p, "a", encoding="ascii", newline="\n") as f:
                f.write(json.dumps(message, sort_keys=True) + "\n")
            return True, str(p.name)
        except OSError as exc:
            return False, exc.__class__.__name__
    return notify


def publish(review_root=REVIEW_ROOT, notify=None, now=None):
    """Stamp every unpublished mark with one batch id; ONE notification.
    Returns the manifest, or None when there was nothing to publish."""
    pending = [t for t in list_threads(review_root) if not t.get("published")]
    if not pending:
        return None
    batch = "b" + time.strftime("%Y%m%dT%H%M%S", time.gmtime(now)) + "-" + os.urandom(2).hex()
    for t in pending:
        t["published"] = batch
        _atomic_json(_path(review_root, t["slug"], t["id"]), t)
    manifest = {"batch": batch, "created": _now(),
                "items": [{"slug": t["slug"], "id": t["id"], "state": t["state"]}
                          for t in pending]}
    _atomic_json(Path(review_root) / "publish" / f"{batch}.json", manifest)
    sink = notify or _file_sink(review_root)
    ok, detail = sink({"kind": "review_batch", "batch": batch, "count": len(pending),
                       "ids": [f"{t['slug']}/{t['id']}" for t in pending]})
    manifest["notified"] = {"ok": bool(ok), "detail": str(detail)}
    _atomic_json(Path(review_root) / "publish" / f"{batch}.json", manifest)
    return manifest


def answer(slug, mid, said, review_root=REVIEW_ROOT, images_root=IMAGES_ROOT,
           image_path=None):
    """Agent reply: a shot rendered from the SAME stored view of the current
    image, appended to the thread; state -> answered."""
    t = load(slug, mid, review_root)
    img = Path(image_path) if image_path else latest_image(slug, images_root)
    if img is None or not img.is_file():
        raise ReviewError("no image for slug")
    n = sum(1 for e in t["thread"] if e["role"] == "agent") + 1
    shot = f"{mid}_reply_{n:02d}.png"
    render_view(img, t["view"], Path(review_root) / slug / shot)
    t["thread"].append({"role": "agent", "said": _ascii_text(said), "shot": shot,
                        "image": {"name": img.name, "sha256": _sha256(img)}, "ts": _now()})
    t["state"] = "answered"
    _atomic_json(_path(review_root, slug, mid), t)
    return t


def follow_up(slug, mid, said, review_root=REVIEW_ROOT):
    """Operator follow-up: appended, the thread REOPENS (state new, unpublished)."""
    t = load(slug, mid, review_root)
    t["thread"].append({"role": "operator", "said": _ascii_text(said), "ts": _now()})
    t["state"] = "new"
    t["published"] = None
    _atomic_json(_path(review_root, slug, mid), t)
    return t


def set_state(slug, mid, state, review_root=REVIEW_ROOT):
    if state not in STATES:
        raise ReviewError(f"state must be one of {STATES}")
    t = load(slug, mid, review_root)
    t["state"] = state
    t["thread"].append({"role": "agent", "said": f"state -> {state}", "ts": _now()})
    _atomic_json(_path(review_root, slug, mid), t)
    return t


def promote(slug, mid, review_root=REVIEW_ROOT):
    """Operator-initiated: the mark becomes a mask seed (a box) for the
    cleaning lane. Writes <id>_seed.json beside the thread; edits nothing."""
    t = load(slug, mid, review_root)
    x, y = t["xy"]
    r = t["r"]
    w, h = t["image"]["size"]
    seed = {"slug": slug, "from_mark": mid, "box": [max(0, x - r), max(0, y - r),
                                                  min(w, x + r), min(h, y + r)],
            "said": t["said"], "created": _now(), "by": "operator"}
    _atomic_json(Path(review_root) / slug / f"{mid}_seed.json", seed)
    return seed


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(prog="lw_review_threads")
    sub = ap.add_subparsers(dest="cmd", required=True)
    ls = sub.add_parser("list")
    ls.add_argument("--slug")
    sub.add_parser("publish")
    a1 = sub.add_parser("answer")
    a1.add_argument("slug")
    a1.add_argument("id")
    a1.add_argument("--said", required=True)
    st = sub.add_parser("state")
    st.add_argument("slug")
    st.add_argument("id")
    st.add_argument("state", choices=STATES)
    pr = sub.add_parser("promote")
    pr.add_argument("slug")
    pr.add_argument("id")
    a = ap.parse_args(argv)
    try:
        if a.cmd == "list":
            for t in list_threads(slug=a.slug):
                print(f"{t['slug']}/{t['id']} {t['state']:<8} "
                      f"pub={t.get('published') or '-'} xy={t['xy']} r={t['r']} {t['said'][:60]}")
        elif a.cmd == "publish":
            m = publish()
            print("nothing to publish" if m is None else
                  f"published {len(m['items'])} as {m['batch']} notified={m['notified']}")
        elif a.cmd == "answer":
            t = answer(a.slug, a.id, a.said)
            print(f"{a.slug}/{a.id} answered -> {t['thread'][-1]['shot']}")
        elif a.cmd == "state":
            set_state(a.slug, a.id, a.state)
            print(f"{a.slug}/{a.id} -> {a.state}")
        elif a.cmd == "promote":
            print(json.dumps(promote(a.slug, a.id)))
    except ReviewError as exc:
        print(f"refused: {exc}")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
