"""ROADMAP R4: anime-lama vs LaMa blind A/B on approved-_01 LaMa slugs.

ADR-009 binds: this is an engine REPLACE test, never a cross-engine ladder.
Each slug's approved clean is an auto LaMa `_cleanworking_01`; the SAME mask
(`ops/runtime/clean/<slug>/<slug>_mask.png`, proven to belong to that run by
the candidate's sha256 equalling the approved sha256) is re-run on the SAME
`_cleaninitial` with the anime/manga Big-LaMa (IOPaint `anime-lama`, official
Sanster release; identical SimpleLama preprocessing and the identical
`lw_clean_pass.inpaint_lama` composite, so pixels outside the mask stay
byte-identical - asserted per slug).

The OPERATOR judges. This tool never picks a winner, never writes into an
images/ stage folder and never changes a slug's pipeline state. Everything it
writes lives under ops/runtime/ab_r4/ (gitignored):

  key.json    slug -> which engine is on the left/right (+ provenance shas).
              Never served; read only by `tally`.
  items.json  the display order - slug names only, no engine.
  votes.json  the operator's per-slug choice as a SIDE (left/right/same),
              never an engine; locked by `finished: true`.
  gen.json    hidden per-slug generation facts (outside identity, timings).
  <slug>/     before_/left_/right_ {tight,context}.png 1:1 crops + anime_full.png

Subcommands:
  python tools/lw_ab_r4.py prepare [--n 20]      (py314; select + blind key)
  <lw-clean venv python> tools/lw_ab_r4.py generate   (GPU; RC-live gate + GPU mutex)
  python tools/lw_ab_r4.py status
  python tools/lw_ab_r4.py tally                  (only after the operator finishes)

Review page: the LW Monitor at http://127.0.0.1:8901/ab .
Pure helpers are stdlib-only; numpy/PIL/torch are imported inside generate.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import random
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AB_ROOT = ROOT / "ops" / "runtime" / "ab_r4"
IMAGES = ROOT / "images"
DONE_STAGE = "4.Cleaning Done"
CLEAN_RUNTIME = ROOT / "ops" / "runtime" / "clean"

ENGINES = ("lama", "anime-lama")
CHOICES = ("left", "right", "same")
TIGHT_PAD = 48
CONTEXT_PAD = 320

# Official weights (fetched 2026-10-04 by R4 from the URL below; the md5 equals
# IOPaint 1.6.0's pinned ANIME_LAMA_MODEL_MD5, iopaint/model/lama.py:25-27).
ANIME_WEIGHTS_URL = ("https://github.com/Sanster/models/releases/download/"
                     "AnimeMangaInpainting/anime-manga-big-lama.pt")
ANIME_WEIGHTS_MD5 = "29f284f36a0a510bcacf39ecf4c4d54f"
ANIME_WEIGHTS_SHA256 = "479d3afdcb7ed2fd944ed4ebcc39ca45b33491f0f2e43eb1000bd623cfb41823"
ANIME_WEIGHTS_BYTES = 205717870
ANIME_WEIGHTS_NAME = "anime-manga-big-lama.pt"

SLUG_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,200}$")
IMG_NAME_RE = re.compile(r"^(before|left|right)_(tight|context)\.png$")


class ABError(Exception):
    """A refused A/B operation (message is safe to show; never a path)."""


# ----------------------------------------------------------------- io helpers

def write_json_atomic(path, obj):
    path = Path(path)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_bytes((json.dumps(obj, indent=2, sort_keys=True) + "\n").encode("ascii"))
    tmp.replace(path)


def _read_json(path, default=None):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def _now():
    return datetime.datetime.now(datetime.UTC).isoformat(timespec="seconds")


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def weights_dir():
    """torch hub checkpoint dir (where IOPaint and simple-lama cache weights)."""
    home = os.environ.get("TORCH_HOME") or os.path.join(
        os.path.expanduser("~"), ".cache", "torch")
    return Path(home) / "hub" / "checkpoints"


# ------------------------------------------------------------------ selection

def approved_lama01(manifest):
    """Provenance dict when the slug's approved clean IS its auto LaMa _01.

    None for every other shape: no approval, a clean-scan / operator-select /
    other-engine approval, an approved _02+, or a slug that was ever REOPENed
    (that excludes the 14 LEDGER 268 slugs by construction).
    """
    tr = manifest.get("transitions") or []
    if any(t.get("op") == "REOPEN" for t in tr):
        return None
    approvals = [t for t in tr if t.get("op") == "APPROVE_CLEAN"]
    if not approvals:
        return None
    sha = approvals[-1].get("sha256_out")
    starts = [t for t in tr if t.get("op") == "START_CLEAN"]
    for t in tr:
        if (t.get("op") == "SAVE_WORKING" and t.get("tool") == "lama"
                and str(t.get("dst") or "").endswith("_cleanworking_01.png")
                and t.get("sha256_out") == sha and sha):
            if not starts:
                return None
            return {"approved_sha": sha,
                    "initial_sha": starts[-1].get("sha256_out"),
                    "mask_bbox": (t.get("params") or {}).get("mask_bbox")}
    return None


def select(slugs, n=20):
    """Deterministic, name-order-free pick: first n by sha256(slug)."""
    ordered = sorted(set(slugs), key=lambda s: hashlib.sha256(s.encode("utf-8")).hexdigest())
    return sorted(ordered[:n])


def assign_sides(slugs, rng=None):
    """Counterbalanced blind sides: LaMa on the left for half (+-1) the slugs."""
    rng = rng or random.SystemRandom()
    slugs = list(slugs)
    half = len(slugs) // 2
    lefts = ["lama"] * half + ["anime-lama"] * (len(slugs) - half)
    rng.shuffle(lefts)
    order = list(slugs)
    rng.shuffle(order)
    out = {}
    for s, left in zip(order, lefts, strict=True):
        right = "anime-lama" if left == "lama" else "lama"
        out[s] = {"left": left, "right": right}
    return out


def crop_box(bbox, w, h, pad):
    x0, y0, x1, y1 = (int(v) for v in bbox)
    return (max(0, x0 - pad), max(0, y0 - pad), min(int(w), x1 + pad), min(int(h), y1 + pad))


def eligible(images=IMAGES, clean_runtime=CLEAN_RUNTIME):
    """Slugs in 4.Cleaning Done whose approved clean is the auto LaMa _01 AND
    whose saved run artifacts still prove the mask (candidate sha == approved)."""
    out = {}
    for m in sorted((Path(images) / DONE_STAGE).glob("*/manifest.json")):
        man = _read_json(m, {}) or {}
        rec = approved_lama01(man)
        if rec is None:
            continue
        slug = m.parent.name
        d = m.parent
        initial = d / f"{slug}_cleaninitial.png"
        done = d / f"{slug}_cleandone.png"
        run = Path(clean_runtime) / slug
        mask = run / f"{slug}_mask.png"
        cand = run / f"{slug}_clean_cand.png"
        if not (initial.is_file() and done.is_file() and mask.is_file() and cand.is_file()):
            continue
        if sha256_file(done) != rec["approved_sha"] or sha256_file(cand) != rec["approved_sha"]:
            continue
        if sha256_file(initial) != rec["initial_sha"]:
            continue
        out[slug] = dict(rec, mask_sha=sha256_file(mask))
    return out


# --------------------------------------------------------------- blind state

def _items(root):
    data = _read_json(Path(root) / "items.json", {}) or {}
    return [i["slug"] for i in data.get("items", []) if isinstance(i, dict) and "slug" in i]


def _votes(root):
    data = _read_json(Path(root) / "votes.json", None)
    if not isinstance(data, dict):
        data = {"votes": {}, "finished": False}
    data.setdefault("votes", {})
    data.setdefault("finished", False)
    return data


def items_view(root=AB_ROOT):
    """What the page may see: slug order, side-only votes, finished flag."""
    slugs = _items(root)
    v = _votes(root)
    return {"items": [{"slug": s, "n": i + 1} for i, s in enumerate(slugs)],
            "total": len(slugs),
            "votes": {s: v["votes"][s]["choice"] for s in slugs if s in v["votes"]},
            "finished": bool(v["finished"])}


def _check_slug(root, slug):
    if not isinstance(slug, str) or not SLUG_RE.match(slug) or ".." in slug:
        raise ABError("bad slug")
    if slug not in _items(root):
        raise ABError("slug is not in this A/B")


def record_vote(root, slug, choice, now=None):
    _check_slug(root, slug)
    if choice not in CHOICES:
        raise ABError("choice must be left, right or same")
    v = _votes(root)
    if v["finished"]:
        raise ABError("A/B already finished - votes are locked")
    v["votes"][slug] = {"choice": choice, "ts": now or _now()}
    write_json_atomic(Path(root) / "votes.json", v)
    return v


def finish(root, now=None):
    slugs = _items(root)
    v = _votes(root)
    missing = [s for s in slugs if s not in v["votes"]]
    if not slugs or missing:
        raise ABError(f"{len(missing)} slug(s) still need a vote")
    v["finished"] = True
    v["finished_ts"] = now or _now()
    write_json_atomic(Path(root) / "votes.json", v)
    return v


def tally(root=AB_ROOT):
    """Engine counts from the operator's side votes. Refuses until finished.
    Reports counts only - the operator's verdict is the decision, not this."""
    v = _votes(root)
    if not v["finished"]:
        raise ABError("operator has not finished the A/B - no tally yet")
    key = (_read_json(Path(root) / "key.json", {}) or {}).get("slugs", {})
    counts = {"lama": 0, "anime-lama": 0, "same": 0}
    rows = []
    for s in _items(root):
        choice = v["votes"][s]["choice"]
        pref = "same" if choice == "same" else key[s][choice]
        counts[pref] += 1
        rows.append({"slug": s, "choice": choice, "preferred": pref})
    return {"counts": counts, "n": len(rows), "per_slug": rows}


def image_path(root, slug, name):
    """Path of a served crop, or None (bad slug, unknown name, missing file)."""
    try:
        _check_slug(root, slug)
    except ABError:
        return None
    if not isinstance(name, str) or not IMG_NAME_RE.match(name):
        return None
    p = Path(root) / slug / name
    return p if p.is_file() else None


def guard_fresh(root):
    """prepare must not reshuffle a key the operator is already voting on."""
    if _votes(root)["votes"]:
        raise ABError("votes exist - refusing to rebuild the key (blinding)")


# ------------------------------------------------------------------- commands

def cmd_prepare(args):
    root = Path(args.root)
    root.mkdir(parents=True, exist_ok=True)
    guard_fresh(root)
    if (root / "key.json").exists() and not args.force:
        raise ABError("key.json exists - pass --force to rebuild (no votes yet)")
    pool = eligible()
    chosen = select(pool, n=args.n)
    if not chosen:
        raise ABError("no eligible approved-_01 LaMa slugs")
    sides = assign_sides(chosen)
    order = list(chosen)
    random.SystemRandom().shuffle(order)
    key = {"created": _now(), "adr": "ADR-009 engine REPLACE A/B (R4)",
           "pool": len(pool), "slugs": {s: dict(sides[s], **pool[s]) for s in chosen}}
    write_json_atomic(root / "key.json", key)
    write_json_atomic(root / "items.json", {"items": [{"slug": s} for s in order]})
    print(f"R4 prepare: {len(chosen)} of {len(pool)} eligible slugs; key + items written")
    return 0


def _rc_gate():
    sys.path.insert(0, str(ROOT / "tools"))
    import lw_gen_run as G
    cfg = json.loads((ROOT / "tools" / "lw_gen_config.json").read_text(encoding="utf-8"))
    flag_rel = (cfg.get("rc_live") or {}).get("flag_path")
    status = G.rc_live_check(cfg, flag_path=str(ROOT / flag_rel) if flag_rel else None)
    ok, msg = G.rc_live_gate(status)
    return ok, msg or status.reason


def cmd_generate(args):
    import time

    import numpy as np
    from PIL import Image

    root = Path(args.root)
    key = (_read_json(root / "key.json", {}) or {}).get("slugs") or {}
    if not key:
        raise ABError("no key.json - run prepare first")
    weights = weights_dir() / ANIME_WEIGHTS_NAME
    if not weights.is_file():
        raise ABError(f"anime-lama weights absent - fetch {ANIME_WEIGHTS_URL}")
    if sha256_file(weights) != ANIME_WEIGHTS_SHA256:
        raise ABError("anime-lama weights sha256 mismatch - refusing")
    ok, msg = _rc_gate()
    print(f"RC-live gate: {'clear' if ok else 'REFUSED'} ({msg})")
    if not ok:
        return 3

    sys.path.insert(0, str(ROOT / "tools"))
    import lw_clean_pass as C
    import torch
    from simple_lama_inpainting import SimpleLama

    dev = C._cuda_device()
    gen = _read_json(root / "gen.json", {}) or {}
    with C.gpu_lock(dev):
        os.environ["LAMA_MODEL"] = str(weights)
        try:
            anime = SimpleLama(device=torch.device(dev))
        finally:
            os.environ.pop("LAMA_MODEL", None)
        for slug in sorted(key):
            rec = key[slug]
            d = IMAGES / DONE_STAGE / slug
            initial = d / f"{slug}_cleaninitial.png"
            done = d / f"{slug}_cleandone.png"
            mask_p = CLEAN_RUNTIME / slug / f"{slug}_mask.png"
            if (sha256_file(initial) != rec["initial_sha"] or sha256_file(done) != rec["approved_sha"]
                    or sha256_file(mask_p) != rec["mask_sha"]):
                print(f"R4 {slug}: provenance drifted - skipped")
                gen[slug] = {"status": "skipped-drift"}
                continue
            t0 = time.time()
            with Image.open(initial) as im:
                base = im.convert("RGB")
            with Image.open(mask_p) as im:
                mask = np.asarray(im.convert("L"))
            with Image.open(done) as im:
                lama_arr = np.asarray(im.convert("RGB"))
            out = C.inpaint_lama(base, mask, anime)
            out_arr = np.asarray(out)
            base_arr = np.asarray(base)
            mask_bool = mask > 127
            outside = C.outside_max_abs(base_arr, out_arr, mask_bool)
            if outside != 0:
                print(f"R4 {slug}: outside-mask identity broken ({outside}) - discarded")
                gen[slug] = {"status": "discard-outside", "outside_max_abs": outside}
                continue
            sd = root / slug
            sd.mkdir(parents=True, exist_ok=True)
            C.atomic_write_png(str(sd / "anime_full.png"), out)
            ys, xs = np.nonzero(mask_bool)
            bbox = (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)
            h, w = mask.shape
            arrays = {"lama": lama_arr, "anime-lama": out_arr}
            for tag, pad in (("tight", TIGHT_PAD), ("context", CONTEXT_PAD)):
                x0, y0, x1, y1 = crop_box(bbox, w, h, pad)
                crops = {"before": base_arr, "left": arrays[rec["left"]],
                         "right": arrays[rec["right"]]}
                for side, arr in crops.items():
                    C.atomic_write_png(str(sd / f"{side}_{tag}.png"),
                                       Image.fromarray(arr[y0:y1, x0:x1]))
            gen[slug] = {"status": "ok", "outside_max_abs": outside,
                         "mask_bbox_px": list(bbox), "mask_px": int(mask_bool.sum()),
                         "seam_step_lama": round(float(C.seam_step(lama_arr, mask_bool)), 4),
                         "seam_step_anime": round(float(C.seam_step(out_arr, mask_bool)), 4),
                         "anime_sha256": sha256_file(sd / "anime_full.png"),
                         "secs": round(time.time() - t0, 2), "device": dev}
            print(f"R4 {slug}: ok ({gen[slug]['secs']}s)")
            write_json_atomic(root / "gen.json", gen)
    write_json_atomic(root / "gen.json", gen)
    ok_n = sum(1 for g in gen.values() if g.get("status") == "ok")
    print(f"R4 generate: {ok_n}/{len(key)} slugs ready")
    return 0 if ok_n else 1


def cmd_status(args):
    v = items_view(args.root)
    print(f"R4 A/B: {len(v['votes'])}/{v['total']} voted, finished={v['finished']}")
    return 0


def cmd_tally(args):
    print(json.dumps(tally(args.root), indent=2))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", default=str(AB_ROOT))
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("prepare")
    p.add_argument("--n", type=int, default=20)
    p.add_argument("--force", action="store_true")
    sub.add_parser("generate")
    sub.add_parser("status")
    sub.add_parser("tally")
    args = ap.parse_args(argv)
    fn = {"prepare": cmd_prepare, "generate": cmd_generate,
          "status": cmd_status, "tally": cmd_tally}[args.cmd]
    try:
        return fn(args)
    except ABError as exc:
        print(f"R4: refused - {exc}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
