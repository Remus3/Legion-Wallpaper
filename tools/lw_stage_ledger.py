"""Stage ledger: which pipeline step touched what it should not (directive P1-1).

The cleaning pass already asserts outside-mask identity for ITS step. Across the
whole chain (first -> clean -> final -> last) nothing recorded which stage
changed which region. This ledger does, per slug per run:

  - the stage list is READ from lw_pipeline.STAGES, never restated, and every
    stage needs an entry in STAGE_COVERAGE. A stage with no coverage is reported
    UNWATCHED - "nobody watched" outranks "nothing happened".
  - each stage is compared input -> output at a fixed common scale: the input is
    the stage's `_initial`, the output is the next stage's `_initial` (start-
    stage copies the verified `_done` forward) or `_lastdone` for the last.
  - a stage ASSERTS the region it declared when it saved its working
    (manifest SAVE_WORKING params: mask_bbox / boxes), dilated by the cleaning
    mask dilation. `first` asserts the whole frame (it re-renders every pixel).
  - watched regions: every operator LOCK in force (ops/runtime/locks/<slug>.json,
    an approved face, an approved clean) plus `outside_edit`, the complement of
    the stage's own declared region. A changed region that its stage did not
    assert is UNEXPLAINED.
  - a step that applies locks writes a note even when there are none.

End review (lw_pipeline finalize) reads the ledger and refuses a pass when a
locked region changed without an asserting stage, when a stage under a lock is
unwatched or absent, or when the lock file cannot be read.

Comparison basis: BOX resampling by an integer factor (2560x1440 -> 640x360),
so a common-scale pixel whose 4x4 block lies wholly outside an edit is EXACTLY
equal across an identity pair; blocks touching the dilated edit are excluded
from `outside_edit`. CHANGE_TOL is calibrated on real known-identity pairs
(`calibrate`), recorded below with its evidence.

  python tools/lw_stage_ledger.py run <slug>
  python tools/lw_stage_ledger.py lock <slug> --name face --box x0 y0 x1 y1 --after-stage clean
  python tools/lw_stage_ledger.py calibrate [--limit N]
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import lw_pipeline  # noqa: E402  (sibling tool; stdlib-only at import)

ROOT = Path(__file__).resolve().parents[1]
LOCKS_DIR = ROOT / "ops" / "runtime" / "locks"
LEDGER_DIR = ROOT / "ops" / "runtime" / "stage_ledger"

COMMON_MAX_W = 640          # common scale: frame // integer factor, <= 640 wide
# Max |luma diff| at common scale still counted as "unchanged". CALIBRATED by
# `calibrate` on real known-identity pairs (cleaninitial -> cleandone outside the
# dilated LaMa mask, which the composite keeps byte-identical): see
# docs/GATE_BOARD.md "stage ledger tolerance". 0.5 = any whole-level change.
CHANGE_TOL = 0.5
EDIT_DILATE_PX = 15 + 4     # lw_clean_pass.DILATE_PX + a 4px safety margin


def stages():
    return list(lw_pipeline.STAGES)


def _declared_from_params(stage, manifest):
    """Boxes the stage declared in its SAVE_WORKING params (latest wins)."""
    boxes = None
    scratch = lw_pipeline.SCRATCH_DIR[stage]
    for t in (manifest or {}).get("transitions", []):
        if t.get("op") != "SAVE_WORKING" or not str(t.get("dst", "")).startswith(scratch):
            continue
        p = t.get("params") or {}
        found = []
        if isinstance(p.get("mask_bbox"), (list, tuple)) and len(p["mask_bbox"]) == 4:
            found.append([int(v) for v in p["mask_bbox"]])
        for b in p.get("boxes") or []:
            if isinstance(b, (list, tuple)) and len(b) == 4:
                found.append([int(v) for v in b])
        boxes = found
    return boxes or []


def _declared_whole_frame(stage, manifest):
    return "whole_frame"


# stage -> how its asserted region is read. Every lw_pipeline stage MUST appear
# (tests/test_lw_stage_ledger.py); a missing one is reported unwatched.
STAGE_COVERAGE = {
    "first": _declared_whole_frame,
    "clean": _declared_from_params,
    "final": _declared_from_params,
    "last": _declared_from_params,
}


# ---------------------------------------------------------------- geometry
def _factor(size):
    w, _h = size
    return max(1, w // COMMON_MAX_W)


def _common_size(size):
    f = _factor(size)
    return (max(1, size[0] // f), max(1, size[1] // f))


def region_mask_common(frame_size, boxes, dilate=0):
    """Common-scale bool mask: True on every common pixel whose block touches
    any box (dilated by `dilate` frame px)."""
    f = _factor(frame_size)
    cw, ch = _common_size(frame_size)
    m = np.zeros((ch, cw), dtype=bool)
    for x0, y0, x1, y1 in boxes:
        x0, y0 = max(0, x0 - dilate), max(0, y0 - dilate)
        x1, y1 = min(frame_size[0], x1 + dilate), min(frame_size[1], y1 + dilate)
        if x1 <= x0 or y1 <= y0:
            continue
        cx0, cy0 = x0 // f, y0 // f
        cx1, cy1 = -(-x1 // f), -(-y1 // f)
        m[cy0:min(ch, cy1), cx0:min(cw, cx1)] = True
    return m


def _luma_common(path, frame_size):
    from PIL import Image
    with Image.open(path) as im:
        im = im.convert("RGB")
        cs = _common_size(frame_size)
        if im.size != frame_size:
            im = im.resize(frame_size, Image.LANCZOS)
        im = im.resize(cs, Image.BOX)
        a = np.asarray(im, dtype=np.float64)
    return 0.299 * a[..., 0] + 0.587 * a[..., 1] + 0.114 * a[..., 2]


def _stats(diff, mask):
    if not mask.any():
        return {"max_abs": 0.0, "frac_changed": 0.0, "changed": False, "px": 0}
    d = diff[mask]
    frac = float(np.count_nonzero(d > CHANGE_TOL)) / float(d.size)
    return {"max_abs": round(float(d.max()), 3), "frac_changed": round(frac, 6),
            "changed": bool(frac > 0.0), "px": int(d.size)}


def _intersects(box, boxes):
    x0, y0, x1, y1 = box
    return any(x0 < b[2] and b[0] < x1 and y0 < b[3] and b[1] < y1 for b in boxes)


# ---------------------------------------------------------------- inputs
def _find(root, slug, name):
    """A milestone file anywhere it can legitimately sit at end review."""
    root = Path(root)
    dirs = [root / lw_pipeline.DONE_DIR["last"] / slug, root / lw_pipeline.BACKUP / slug]
    dirs += [root / lw_pipeline.SCRATCH_DIR[s] / slug for s in lw_pipeline.STAGES]
    dirs += [root / lw_pipeline.DONE_DIR[s] / slug for s in lw_pipeline.STAGES]
    for d in dirs:
        for ext in ("png", "jpg", "jpeg", "webp"):
            p = d / f"{slug}_{name}.{ext}"
            if p.is_file():
                return p
    return None


def _manifest(root, slug):
    root = Path(root)
    # The LIVE manifest travels with the slug; the backup copy can be an older
    # snapshot (intake-only), so it is the last resort.
    live = []
    for s in reversed(lw_pipeline.STAGES):
        live += [root / lw_pipeline.DONE_DIR[s] / slug, root / lw_pipeline.SCRATCH_DIR[s] / slug]
    for d in (*live, root / lw_pipeline.BACKUP / slug):
        p = d / "manifest.json"
        if p.is_file():
            try:
                return json.loads(p.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                return None
    return None


def load_locks(slug, locks_dir=LOCKS_DIR):
    """(locks, error). No file = no locks. An unreadable file is an error that
    blocks end review - an approval nobody can read is not 'no approval'."""
    p = Path(locks_dir) / f"{slug}.json"
    if not p.is_file():
        return [], None
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        locks = [lk for lk in data.get("locks", [])
                 if isinstance(lk.get("box"), list) and len(lk["box"]) == 4]
        return locks, None
    except (OSError, ValueError, AttributeError) as exc:
        return [], f"lock file unreadable ({exc.__class__.__name__})"


def _pairs(root, slug):
    st = stages()
    out = []
    for i, s in enumerate(st):
        src = _find(root, slug, f"{s}initial")
        dst = _find(root, slug, f"{st[i + 1]}initial") if i + 1 < len(st) else None
        if i + 1 == len(st):
            dst = _find(root, slug, f"{s}done")
        out.append((s, src, dst))
    return out


# ---------------------------------------------------------------- ledger
def _lock_in_force(lock, stage):
    st = stages()
    after = lock.get("after_stage")
    if after not in st:
        return True  # an unscoped lock binds every stage
    return st.index(stage) > st.index(after)


def build_ledger(root, slug, locks_dir=LOCKS_DIR):
    locks, lock_err = load_locks(slug, locks_dir)
    man = _manifest(root, slug)
    frame_size = None
    last = _find(root, slug, f"{stages()[-1]}done")
    if last is not None:
        from PIL import Image
        with Image.open(last) as im:
            frame_size = im.size
    rec = {"slug": slug, "created": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "locks": locks, "lock_error": lock_err, "stages": [],
           "common_scale": list(_common_size(frame_size)) if frame_size else None,
           "change_tol": CHANGE_TOL}
    for stage, src, dst in _pairs(root, slug):
        in_force = [lk for lk in locks if _lock_in_force(lk, stage)]
        entry = {"stage": stage, "status": "watched", "regions": [], "notes": [],
                 "asserts": None, "locks_in_force": [lk.get("name") for lk in in_force]}
        if not in_force:
            entry["notes"].append("no locks in force at this stage")
        cover = STAGE_COVERAGE.get(stage)
        if cover is None:
            entry["status"] = "unwatched"
            entry["notes"].append("no ledger coverage for this stage")
            rec["stages"].append(entry)
            continue
        if src is None or dst is None or frame_size is None:
            entry["status"] = "absent"
            entry["notes"].append("stage input or output milestone not found")
            rec["stages"].append(entry)
            continue
        declared = cover(stage, man)
        entry["asserts"] = declared
        a = _luma_common(src, frame_size)
        b = _luma_common(dst, frame_size)
        diff = np.abs(a - b)
        whole = declared == "whole_frame"
        boxes = [] if whole else declared
        for lk in in_force:
            m = region_mask_common(frame_size, [lk["box"]])
            st = _stats(diff, m)
            asserted = stage if (whole or _intersects(lk["box"], boxes)) else None
            entry["regions"].append({"region": f"lock:{lk.get('name')}", **st,
                                     "asserted_by": asserted})
        if not whole:
            edit = region_mask_common(frame_size, boxes, dilate=EDIT_DILATE_PX)
            st = _stats(diff, ~edit)
            entry["regions"].append({"region": "outside_edit", **st, "asserted_by": None})
        rec["stages"].append(entry)
    rec["summary"] = _summarize(rec)
    return rec


def _summarize(rec):
    unexplained, unwatched, absent = [], [], []
    for s in rec["stages"]:
        if s["status"] == "unwatched":
            unwatched.append(s["stage"])
        if s["status"] == "absent":
            absent.append(s["stage"])
        for r in s["regions"]:
            if r["changed"] and r["asserted_by"] is None:
                unexplained.append({"stage": s["stage"], "region": r["region"]})
    return {"unexplained": unexplained, "unwatched": unwatched, "absent": absent}


def end_review_check(ledger):
    """(ok, reasons): refuse a pass when an approved region changed without an
    asserting stage, or when a stage under a lock could not be watched."""
    reasons = []
    if ledger.get("lock_error"):
        reasons.append(ledger["lock_error"])
    for s in ledger["stages"]:
        under_lock = bool(s.get("locks_in_force"))
        if under_lock and s["status"] in ("unwatched", "absent"):
            reasons.append(f"stage {s['stage']} is {s['status']} while locks "
                           f"{s['locks_in_force']} are in force")
        for r in s["regions"]:
            if r["region"].startswith("lock:") and r["changed"] and r["asserted_by"] is None:
                reasons.append(f"{r['region']} changed in stage {s['stage']} "
                               f"(max {r['max_abs']} levels) without an asserting stage")
    return (not reasons), reasons


def write_ledger(ledger, out_dir=LEDGER_DIR):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{ledger['slug']}.json"
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(ledger, indent=1, sort_keys=True) + "\n", encoding="ascii")
    os.replace(tmp, path)
    return path


def add_lock(slug, name, box, after_stage, locks_dir=LOCKS_DIR, by="operator"):
    """Operator-initiated: record an approved region as a lock."""
    if after_stage not in stages():
        raise ValueError(f"after_stage must be one of {stages()}")
    locks, err = load_locks(slug, locks_dir)
    if err:
        raise ValueError(err)
    locks = [lk for lk in locks if lk.get("name") != name]
    locks.append({"name": name, "box": [int(v) for v in box], "after_stage": after_stage,
                  "approved_by": by,
                  "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())})
    d = Path(locks_dir)
    d.mkdir(parents=True, exist_ok=True)
    p = d / f"{slug}.json"
    tmp = p.with_name(p.name + ".tmp")
    tmp.write_text(json.dumps({"locks": locks}, indent=1) + "\n", encoding="ascii")
    os.replace(tmp, p)
    return p


# ---------------------------------------------------------------- calibration
def calibrate(images_root, limit=None):
    """Max common-scale diff OUTSIDE the dilated edit on real clean pairs that
    the LaMa composite keeps byte-identical outside its mask."""
    root = Path(images_root)
    done = root / lw_pipeline.DONE_DIR["clean"]
    rows = []
    for d in sorted(p for p in done.iterdir() if p.is_dir()):
        if limit is not None and len(rows) >= limit:
            break
        slug = d.name
        man = _manifest(root, slug)
        saves = [t for t in (man or {}).get("transitions", [])
                 if t.get("op") == "SAVE_WORKING"
                 and str(t.get("dst", "")).startswith(lw_pipeline.SCRATCH_DIR["clean"])]
        if not saves or saves[-1].get("tool") not in ("lama", "simple-lama"):
            continue
        src = d / f"{slug}_cleaninitial.png"
        dst = d / f"{slug}_cleandone.png"
        if not (src.is_file() and dst.is_file()):
            continue
        from PIL import Image
        with Image.open(dst) as im:
            size = im.size
        boxes = _declared_from_params("clean", man)
        a, b = _luma_common(src, size), _luma_common(dst, size)
        outside = ~region_mask_common(size, boxes, dilate=EDIT_DILATE_PX)
        diff = np.abs(a - b)[outside]
        rows.append({"slug": slug, "max_abs": float(diff.max()) if diff.size else 0.0,
                     "px": int(diff.size)})
    return rows


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(prog="lw_stage_ledger")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="build + write the ledger for a slug")
    r.add_argument("slug")
    r.add_argument("--root", default=str(lw_pipeline.DEFAULT_ROOT))
    k = sub.add_parser("lock", help="record an operator-approved region")
    k.add_argument("slug")
    k.add_argument("--name", required=True)
    k.add_argument("--box", type=int, nargs=4, required=True)
    k.add_argument("--after-stage", required=True)
    c = sub.add_parser("calibrate", help="identity tolerance on real clean pairs")
    c.add_argument("--root", default=str(lw_pipeline.DEFAULT_ROOT))
    c.add_argument("--limit", type=int, default=None)
    a = ap.parse_args(argv)
    if a.cmd == "run":
        led = build_ledger(a.root, a.slug)
        path = write_ledger(led)
        ok, reasons = end_review_check(led)
        print(f"{path} end_review={'OK' if ok else 'BLOCK'} "
              f"unexplained={len(led['summary']['unexplained'])}")
        for x in reasons:
            print("  " + x)
        return 0 if ok else 1
    if a.cmd == "lock":
        print(add_lock(a.slug, a.name, a.box, a.after_stage))
        return 0
    rows = calibrate(a.root, a.limit)
    mx = max((x["max_abs"] for x in rows), default=None)
    print(json.dumps({"pairs": len(rows), "max_abs_outside": mx,
                      "nonzero": sum(1 for x in rows if x["max_abs"] > 0)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
