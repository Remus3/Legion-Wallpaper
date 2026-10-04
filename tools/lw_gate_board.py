"""Fault-proven gate board: every green row must have been seen red.

Directive P0-3 (fleet ideas ingest, 2026-10-04). A requirement is a ROW: a
name, the person's wording, a measurement, a bar and a unit. A measured row
registers a FAULT - a pure function that plants a defect into a COPY of the
subject. `prove()` runs every row on the clean subject and on its planted copy:

    PROVEN      passes clean AND fails planted - the gate can still fire
    BROKEN      the fault did not move the measurement past the bar, or the
                fault aliased the original subject - the gate is decoration
    UNPROVEN    no fault registered - nobody has ever seen this row red
    UNKNOWN     the measurement raised / returned nothing, or the clean subject
                already fails the row - never green
    NA          the live gate does not apply to this subject (e.g. lap_ratio on
                a downscale-only frame, ADR-006)
    VALIDATION  a row only the operator can judge ("reads like the original
                art"); listed, never measured, never counts toward done

Rows judge through the LIVE gate code wherever a live gate exists
(`lw_g1_gate.verdict`, `lw_first_pass.gate_metrics`, `lw_clean_pass.
verify_verdict`, `lw_upscale._finish`), and thresholds are read at evaluation
time - so a mutant that deletes or loosens a live threshold flips its row.

Fault amplitudes are CALIBRATED and each carries its evidence string; see
FAULT_EVIDENCE below and docs/GATE_BOARD.md. Image bytes are never written to
the repo: faults are synthetic numpy edits on in-memory copies, the golden set
stays gitignored, and the only artifact is ops/runtime/gate_proofs.json.

Envs: rows tagged "base" run on system python (numpy + PIL). "metrics" rows
(MS-SSIM, LPIPS via pyiqa) run under .venv-metrics; "clean" rows (OCR + MSER
text residue) run under the lw-clean venv. `prove --golden --env all`
dispatches each env to its own interpreter and merges the partial tables.

CLI:
    python tools/lw_gate_board.py prove --golden [--env base|metrics|clean|all]
    python tools/lw_gate_board.py check        # exit 1 unless every row PROVEN
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
import os
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

ROOT = Path(__file__).resolve().parents[1]
PROOFS_PATH = ROOT / "ops" / "runtime" / "gate_proofs.json"
SCHEMA = 1
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)

PASS, FAIL, UNKNOWN, NA, VALIDATION = "PASS", "FAIL", "UNKNOWN", "NA", "VALIDATION"
PROVEN, UNPROVEN, BROKEN = "PROVEN", "UNPROVEN", "BROKEN"

ENVS = ("base", "metrics", "clean")


# ============================================================== core types
@dataclass
class Bar:
    """at_most / at_least / between. lo / hi may be callables, resolved at
    evaluation time so the bar follows the live threshold table."""
    kind: str
    lo: Any = None
    hi: Any = None

    @staticmethod
    def _v(x):
        return x() if callable(x) else x

    def resolved(self):
        return self._v(self.lo), self._v(self.hi)

    def holds(self, value: float) -> bool:
        lo, hi = self.resolved()
        v = float(value)
        if self.kind == "at_most":
            return v <= float(hi)
        if self.kind == "at_least":
            return v >= float(lo)
        if self.kind == "between":
            return float(lo) <= v <= float(hi)
        raise ValueError(f"unknown bar kind {self.kind!r}")

    def describe(self) -> str:
        try:
            lo, hi = self.resolved()
        except Exception as exc:  # noqa: BLE001 - a missing live threshold is reported, not raised
            return f"{self.kind} <unresolvable: {exc.__class__.__name__}>"
        if self.kind == "at_most":
            return f"<= {hi:g}"
        if self.kind == "at_least":
            return f">= {lo:g}"
        return f"in [{lo:g}, {hi:g}]"


@dataclass
class Row:
    name: str
    said: str
    measure: Optional[Callable[[dict], Any]] = None
    bar: Optional[Bar] = None
    unit: str = ""
    where: str = ""
    judge: Optional[Callable[[Any, dict], bool]] = None  # True = passes (live gate path)
    applies: Optional[Callable[[dict], bool]] = None
    env: str = "base"
    kind: str = "measured"  # measured | validation
    gate: str = ""


@dataclass
class Fault:
    name: str
    plant: Callable[[dict], dict]
    amplitude: str
    evidence: str


@dataclass
class Reading:
    row: str
    state: str
    value: Any = None
    detail: str = ""


@dataclass
class Proof:
    row: str
    state: str
    clean: Optional[Reading] = None
    planted: Optional[Reading] = None
    fault: str = ""
    detail: str = ""
    subject: str = ""


def _is_missing(value) -> bool:
    if value is None:
        return True
    if isinstance(value, float) and math.isnan(value):
        return True
    if isinstance(value, dict):
        return any(_is_missing(v) for v in value.values()) or not value
    return False


def _jsonable(value):
    if isinstance(value, dict):
        return {k: _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    if isinstance(value, (np.floating, float)):
        f = float(value)
        return None if math.isnan(f) else round(f, 6)
    if isinstance(value, (np.integer, int)) and not isinstance(value, bool):
        return int(value)
    return value


def _fingerprint(subject: dict) -> str:
    h = hashlib.sha256()
    for k in sorted(subject):
        v = subject[k]
        if isinstance(v, np.ndarray):
            h.update(k.encode())
            h.update(np.ascontiguousarray(v).tobytes())
    return h.hexdigest()


def _copy_subject(subject: dict) -> dict:
    """Deep copy, minus private caches (keys starting with '_')."""
    return {k: copy.deepcopy(v) for k, v in subject.items() if not k.startswith("_")}


def _aliases(planted: dict, original: dict) -> bool:
    for k, v in planted.items():
        if not isinstance(v, np.ndarray):
            continue
        for ov in original.values():
            if isinstance(ov, np.ndarray) and np.shares_memory(v, ov):
                return True
    return False


class Board:
    def __init__(self):
        self.rows: List[Row] = []
        self.faults: Dict[str, Fault] = {}

    def add(self, row: Row) -> Row:
        if any(r.name == row.name for r in self.rows):
            raise ValueError(f"duplicate row {row.name!r}")
        self.rows.append(row)
        return row

    def fault(self, row_name: str, amplitude: str, evidence: str):
        def deco(fn):
            self.faults[row_name] = Fault(fn.__name__, fn, amplitude, evidence)
            return fn
        return deco

    # ---------------------------------------------------------- evaluation
    def evaluate(self, row: Row, subject: dict) -> Reading:
        if row.kind == "validation":
            return Reading(row.name, VALIDATION, detail="operator judgement")
        try:
            if row.applies is not None and not row.applies(subject):
                return Reading(row.name, NA, detail="live gate does not apply")
        except Exception as exc:  # noqa: BLE001 - an applicability crash is UNKNOWN, never green
            return Reading(row.name, UNKNOWN, detail=f"applies raised {exc!r}")
        try:
            value = row.measure(subject)
        except Exception as exc:  # noqa: BLE001 - a crashed measurement is UNKNOWN, never green
            return Reading(row.name, UNKNOWN, detail=f"measure raised {exc!r}")
        if _is_missing(value):
            return Reading(row.name, UNKNOWN, value=_jsonable(value),
                           detail="measurement returned no value")
        try:
            ok = row.judge(value, subject) if row.judge else row.bar.holds(value)
        except Exception as exc:  # noqa: BLE001
            return Reading(row.name, UNKNOWN, value=_jsonable(value),
                           detail=f"judge raised {exc!r}")
        return Reading(row.name, PASS if ok else FAIL, value=_jsonable(value))

    def report(self, subject: dict) -> List[Reading]:
        return [self.evaluate(r, subject) for r in self.rows]

    def prove_row(self, row: Row, subject: dict) -> Proof:
        slug = str(subject.get("slug", ""))
        clean = self.evaluate(row, subject)
        if clean.state in (VALIDATION, NA):
            return Proof(row.name, clean.state, clean=clean, subject=slug)
        f = self.faults.get(row.name)
        if f is None:
            return Proof(row.name, UNPROVEN, clean=clean, subject=slug,
                         detail="no fault registered")
        if clean.state == UNKNOWN:
            return Proof(row.name, UNKNOWN, clean=clean, fault=f.name, subject=slug,
                         detail=f"clean reading unknown: {clean.detail}")
        if clean.state == FAIL:
            return Proof(row.name, UNKNOWN, clean=clean, fault=f.name, subject=slug,
                         detail="clean subject already fails the row; cannot prove")
        before = _fingerprint(subject)
        try:
            planted_subj = f.plant(_copy_subject(subject))
        except Exception as exc:  # noqa: BLE001
            return Proof(row.name, UNKNOWN, clean=clean, fault=f.name, subject=slug,
                         detail=f"fault raised {exc!r}")
        if _fingerprint(subject) != before or _aliases(planted_subj, subject):
            return Proof(row.name, BROKEN, clean=clean, fault=f.name, subject=slug,
                         detail="fault aliased the original subject")
        planted = self.evaluate(row, planted_subj)
        if planted.state == FAIL:
            return Proof(row.name, PROVEN, clean, planted, f.name, subject=slug)
        if planted.state == PASS:
            return Proof(row.name, BROKEN, clean, planted, f.name, subject=slug,
                         detail=f"fault did not move the row past its bar "
                                f"(clean {clean.value}, planted {planted.value})")
        return Proof(row.name, UNKNOWN, clean, planted, f.name, subject=slug,
                     detail=f"planted reading {planted.state}: {planted.detail}")

    def prove(self, subject: dict) -> List[Proof]:
        return [self.prove_row(r, subject) for r in self.rows]


# ============================================================== aggregation
_ORDER = {BROKEN: 0, UNKNOWN: 1, UNPROVEN: 2, PROVEN: 3, NA: 4, VALIDATION: 5}


def aggregate(per_subject: List[List[Proof]], board: Optional[Board] = None) -> List[dict]:
    """Fold per-subject proofs into one record per row (worst state wins)."""
    by_row: Dict[str, List[Proof]] = {}
    for proofs in per_subject:
        for p in proofs:
            by_row.setdefault(p.row, []).append(p)
    rows_meta = {r.name: r for r in board.rows} if board else {}
    out = []
    for name, proofs in by_row.items():
        states = [p.state for p in proofs]
        applicable = [p for p in proofs if p.state not in (NA,)]
        if all(s == VALIDATION for s in states):
            state = VALIDATION
        elif not applicable:
            state = UNKNOWN  # applies to no subject: nothing was ever seen red
        else:
            state = min((p.state for p in applicable), key=lambda s: _ORDER[s])
        rec = {
            "row": name, "state": state,
            "n_proven": sum(1 for s in states if s == PROVEN),
            "n_applicable": len(applicable) if state != VALIDATION else 0,
            "n_subjects": len(proofs),
            "fault": next((p.fault for p in proofs if p.fault), ""),
            "subjects": [{"slug": p.subject, "state": p.state, "detail": p.detail,
                          "clean": p.clean.value if p.clean else None,
                          "planted": p.planted.value if p.planted else None}
                         for p in proofs],
        }
        meta = rows_meta.get(name)
        if meta is not None:
            rec.update({"gate": meta.gate, "said": meta.said, "unit": meta.unit,
                        "env": meta.env, "kind": meta.kind,
                        "bar": meta.bar.describe() if meta.bar else ""})
            f = board.faults.get(name)
            if f is not None:
                rec["fault_amplitude"] = f.amplitude
                rec["fault_evidence"] = f.evidence
        out.append(rec)
    return out


def summary(proofs_or_agg) -> dict:
    """green iff every measured row is PROVEN. Validation rows never count."""
    states = {}
    for p in proofs_or_agg:
        name, state = (p["row"], p["state"]) if isinstance(p, dict) else (p.row, p.state)
        states[name] = state
    validation = sorted(n for n, s in states.items() if s == VALIDATION)
    bad = sorted(n for n, s in states.items() if s not in (PROVEN, VALIDATION))
    measured = [n for n, s in states.items() if s != VALIDATION]
    return {"green": bool(measured) and not bad, "not_proven": bad,
            "validation": validation}


def proof_table(agg: List[dict]) -> str:
    lines = [f"{'row':<22} {'state':<10} {'proven':>8}  bar / fault",
             "-" * 78]
    for rec in sorted(agg, key=lambda r: (r.get("gate", ""), r["row"])):
        n = (f"{rec['n_proven']}/{rec['n_applicable']}"
             if rec["state"] != VALIDATION else "-")
        tail = rec.get("bar", "")
        if rec.get("fault"):
            tail = f"{tail}  fault={rec['fault']} ({rec.get('fault_amplitude', '')})"
        if rec["state"] == VALIDATION:
            tail = "operator only: " + rec.get("said", "")
        lines.append(f"{rec['row']:<22} {rec['state']:<10} {n:>8}  {tail}")
    s = summary(agg)
    lines.append("-" * 78)
    lines.append("board: " + ("GREEN - every measured row PROVEN" if s["green"]
                              else "NOT GREEN - " + ", ".join(s["not_proven"])))
    return "\n".join(lines).encode("ascii", "replace").decode("ascii")


# ============================================================== proofs file
def registry_digest(board: Board) -> str:
    """Hash of row names, envs, bars (resolved) and fault identities+amplitudes.
    A changed threshold or fault invalidates a recorded proof."""
    items = []
    for r in sorted(board.rows, key=lambda r: r.name):
        f = board.faults.get(r.name)
        items.append([r.name, r.env, r.kind, r.bar.describe() if r.bar else "",
                      f.name if f else "", f.amplitude if f else ""])
    return hashlib.sha256(json.dumps(items, sort_keys=True).encode("ascii")).hexdigest()


def _atomic_write_json(path: Path, data) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(data, indent=1, sort_keys=True) + "\n", encoding="ascii")
    os.replace(tmp, path)


def write_proofs(path, agg, registry: str, subjects, extra: Optional[dict] = None) -> dict:
    data = {"schema": SCHEMA, "created": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "registry": registry, "subjects": list(subjects),
            "green": summary(agg)["green"], "summary": summary(agg),
            "rows": _jsonable(agg)}
    if extra:
        data.update(extra)
    _atomic_write_json(Path(path), data)
    return data


def check_proofs(path, board: Board):
    """Problems with a recorded proof table, [] when every row is PROVEN.

    None when the file is absent (CI, fresh clone): absent is reported by the
    caller as a note - it must never read as verified."""
    path = Path(path)
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="ascii"))
        rows = {r["row"]: r for r in data["rows"]}
    except (OSError, ValueError, KeyError, TypeError) as exc:
        return [f"gate proofs unreadable ({exc.__class__.__name__}: {exc})"]
    problems = []
    if data.get("registry") != registry_digest(board):
        problems.append("gate proofs stale: registry changed since the last "
                        "`lw_gate_board.py prove --golden --env all`")
    for r in board.rows:
        if r.kind == "validation":
            continue
        rec = rows.get(r.name)
        if rec is None:
            problems.append(f"registered gate {r.name} has no proof")
        elif rec.get("state") != PROVEN:
            problems.append(f"gate {r.name} is {rec.get('state')}")
    return problems


ACK_PATH = ROOT / "config" / "gate_board_ack.json"
LEDGER_PATH = ROOT / "docs" / "LEDGER.md"


def _ledger_ids(ledger_path) -> set:
    import re
    try:
        text = Path(ledger_path).read_text(encoding="utf-8")
    except OSError:
        return set()
    return {int(m.group(1)) for m in re.finditer(r"(?m)^(\d+)\. ", text)}


def _failing(rec) -> set:
    return {s["slug"] for s in rec.get("subjects", [])
            if s.get("state") not in (PROVEN, NA, VALIDATION)}


def check_proofs_acked(path, board: Board, ack_path=ACK_PATH, ledger_path=LEDGER_PATH,
                       golden_present: Optional[bool] = None):
    """(problems, notes) for drift_guard. Adjudicated 2026-10-04 (option b):

    every non-PROVEN row breaches unless a TRACKED ack entry names it with an
    existing LEDGER item and a checkable clearing condition, and the recorded
    state is no worse than the entry pins (state, n_proven, failing subjects).
    An absent table is a note only where the golden set is absent (CI, a fresh
    clone); on Legion it breaches. A stale table always breaches."""
    notes: List[str] = []
    if golden_present is None:
        golden_present = (ROOT / "data" / "golden" / "inputs").is_dir()
    base = check_proofs(path, board)
    if base is None:
        if golden_present:
            return ["gate proofs absent on a machine holding the golden set - run "
                    "`python tools/lw_gate_board.py prove --golden --env all`"], notes
        notes.append("gate proofs absent (no golden set here) - not verified")
        return [], notes
    try:
        ack = json.loads(Path(ack_path).read_text(encoding="ascii")).get("entries", [])
    except (OSError, ValueError) as exc:
        if Path(ack_path).exists():
            return base + [f"gate board ack unreadable ({exc.__class__.__name__})"], notes
        ack = []
    data = json.loads(Path(path).read_text(encoding="ascii"))
    rows = {r["row"]: r for r in data.get("rows", [])}
    ids = _ledger_ids(ledger_path)
    acked, problems = {}, []
    for e in ack:
        name = e.get("row", "?")
        if not (isinstance(e.get("ledger"), int) and e["ledger"] in ids):
            problems.append(f"ack {name}: LEDGER item {e.get('ledger')} does not exist")
            continue
        if not str(e.get("clears_when", "")).strip() or not str(e.get("reason", "")).strip():
            problems.append(f"ack {name}: needs a reason and a clears_when condition")
            continue
        acked[name] = e
    for p in base:
        name = next((n for n in acked if f" {n} " in f" {p} "), None)
        if name is None:
            problems.append(p)
            continue
        e, rec = acked[name], rows.get(name, {})
        state = rec.get("state")
        worse = (state not in _ORDER or _ORDER[state] < _ORDER.get(e["state"], 0)
                 or int(rec.get("n_proven", 0)) < int(e.get("n_proven", 0))
                 or not _failing(rec) <= set(e.get("failing", [])))
        if worse:
            problems.append(f"gate {name} is worse than its ack ({state} "
                            f"{rec.get('n_proven')}/{rec.get('n_applicable')}, failing "
                            f"{sorted(_failing(rec))}) - LEDGER {e['ledger']}")
        else:
            notes.append(f"ACKNOWLEDGED {name} {state} {rec.get('n_proven')}/"
                         f"{rec.get('n_applicable')} (LEDGER {e['ledger']}; clears when "
                         f"{e['clears_when']}) - NOT a pass")
    for name, e in acked.items():
        if rows.get(name, {}).get("state") == PROVEN:
            notes.append(f"ack {name}: row is now PROVEN - remove the entry")
    return problems, notes


# ============================================================== fault primitives
def _u8(a) -> np.ndarray:
    return np.clip(np.rint(np.asarray(a, dtype=np.float64)), 0, 255).astype(np.uint8)


def fault_downup(img: np.ndarray, factor: float = 2.0) -> np.ndarray:
    """The double-resample softness bug: down by `factor`, back up (bicubic)."""
    from PIL import Image
    h, w = img.shape[:2]
    small = Image.fromarray(np.ascontiguousarray(img)).resize(
        (max(1, int(round(w / factor))), max(1, int(round(h / factor)))), Image.BICUBIC)
    return np.array(small.resize((w, h), Image.BICUBIC), dtype=np.uint8)


def fault_usm(img: np.ndarray, radius: float = 2.0, percent: int = 150,
              threshold: int = 0) -> np.ndarray:
    """Over-sharpening: one extra unsharp mask - USM ringing at every edge."""
    from PIL import Image, ImageFilter
    im = Image.fromarray(np.ascontiguousarray(img))
    return np.array(im.filter(ImageFilter.UnsharpMask(
        radius=radius, percent=percent, threshold=threshold)), dtype=np.uint8)


def fault_posterize(img: np.ndarray, step: int = 8) -> np.ndarray:
    """Banding: quantize every channel to `step`-level plateaus."""
    a = np.asarray(img, dtype=np.float64)
    return _u8(np.floor(a / step) * step + step / 2.0)


def fault_shift(img: np.ndarray, px: int = 16) -> np.ndarray:
    """Misregistration: shift right by `px`, replicating the left edge."""
    out = np.empty_like(img)
    out[:, px:] = img[:, :-px]
    out[:, :px] = img[:, :1]
    return out


def fault_letterbox(img: np.ndarray, ratio: float = 16.0 / 10.0) -> np.ndarray:
    """Letterbox to a non-16:9 frame (black bars top and bottom)."""
    h, w = img.shape[:2]
    new_h = int(round(w / ratio))
    pad = max(1, (new_h - h) // 2)
    shape = (h + 2 * pad,) + img.shape[1:]
    out = np.zeros(shape, dtype=np.uint8)
    out[pad:pad + h] = img
    return out


def _outside_block_origin(mask: np.ndarray, size: int):
    h, w = mask.shape
    for y, x in ((h // 8, w // 8), (h // 8, w - w // 8 - size), (h // 2, w // 2)):
        y, x = max(0, min(y, h - size)), max(0, min(x, w - size))
        if not mask[y:y + size, x:x + size].any():
            return y, x
    raise ValueError("no outside-mask block position found")


def fault_outside_block(img: np.ndarray, mask: np.ndarray, size: int = 32,
                        delta: float = 16.0) -> np.ndarray:
    """One pixel block OUTSIDE the edit mask moved by `delta` levels."""
    s = max(1, min(size, mask.shape[0] // 4, mask.shape[1] // 4))
    y, x = _outside_block_origin(mask, s)
    out = np.asarray(img, dtype=np.float64).copy()
    out[y:y + s, x:x + s] += delta
    return _u8(out)


def fault_seam(img: np.ndarray, mask: np.ndarray, offset: float = 24.0) -> np.ndarray:
    """A hard seam: the whole fill offset by `offset` levels against its ring."""
    out = np.asarray(img, dtype=np.float64).copy()
    out[np.asarray(mask, dtype=bool)] += offset
    return _u8(out)


# 5x7 bitmap glyphs for the planted credit line. Pure numpy on purpose: the
# lw-clean venv's Pillow FreeType segfaults (measured 2026-10-04, access
# violation in ImageFont.getbbox), and a font file would make the fault differ
# between machines. OCR reads a block font fine.
_GLYPHS = {
    "W": ["10001", "10001", "10001", "10101", "10101", "11011", "10001"],
    "D": ["11110", "10001", "10001", "10001", "10001", "10001", "11110"],
    "E": ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    "V": ["10001", "10001", "10001", "10001", "01010", "01010", "00100"],
    "I": ["11111", "00100", "00100", "00100", "00100", "00100", "11111"],
    "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    "N": ["10001", "11001", "10101", "10011", "10001", "10001", "10001"],
    "T": ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
    "R": ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
    "C": ["01111", "10000", "10000", "10000", "10000", "10000", "01111"],
    "O": ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
    "M": ["10001", "11011", "10101", "10101", "10001", "10001", "10001"],
    "S": ["01111", "10000", "10000", "01110", "00001", "00001", "11110"],
    ".": ["00000", "00000", "00000", "00000", "00000", "01100", "01100"],
    "/": ["00001", "00010", "00010", "00100", "01000", "01000", "10000"],
    " ": ["00000"] * 7,
}


def text_mask(text: str, bw: int, bh: int) -> np.ndarray:
    """Coverage in [0, 1] of `text` rendered centred in a bw x bh box."""
    cols = []
    for ch in text.upper():
        g = _GLYPHS.get(ch, _GLYPHS[" "])
        cols.append(np.array([[c == "1" for c in row] for row in g], dtype=np.float64))
        cols.append(np.zeros((7, 1)))
    line = np.concatenate(cols[:-1], axis=1) if cols else np.zeros((7, 1))
    k = max(1, min(bh // 9, bw // max(1, line.shape[1])))
    big = np.kron(line, np.ones((k, k)))
    out = np.zeros((bh, bw), dtype=np.float64)
    hh, ww = min(bh, big.shape[0]), min(bw, big.shape[1])
    oy, ox = (bh - hh) // 2, (bw - ww) // 2
    out[oy:oy + hh, ox:ox + ww] = big[:hh, :ww]
    return out


def fault_text(img: np.ndarray, box, alpha: Optional[float] = None,
               text: str = "WWW.DEVIANTART.COM/ARTIST", white: float = 255.0,
               levels: Optional[float] = None) -> np.ndarray:
    """A credit-line watermark inside the rendered glyphs, fitted to `box`
    (x0, y0, x1, y1). Either a fixed blend `alpha` (out = (1-a)*art + a*W) or
    a fixed luma step `levels` toward W per pixel (alpha = levels/|W - art|),
    which is how the faintest real residue is specified (docs/GATE_BOARD.md)."""
    if (alpha is None) == (levels is None):
        raise ValueError("give exactly one of alpha / levels")
    x0, y0, x1, y1 = (int(v) for v in box)
    bw, bh = max(1, x1 - x0), max(1, y1 - y0)
    cover = text_mask(text, bw, bh)
    out = np.asarray(img, dtype=np.float64).copy()
    region = out[y0:y0 + bh, x0:x0 + bw]
    cover = cover[:region.shape[0], :region.shape[1]]
    if region.ndim == 3:
        cover = cover[:, :, None]
    if levels is not None:
        a = np.clip(float(levels) / np.maximum(np.abs(white - region), 1.0), 0.0, 1.0)
    else:
        a = float(alpha)
    g = cover * a
    out[y0:y0 + region.shape[0], x0:x0 + region.shape[1]] = (1.0 - g) * region + g * white
    return _u8(out)


# ============================================================== LW measurements
def _g1():
    import lw_g1_gate
    return lw_g1_gate


def _common(subject: dict):
    """(source gray, output gray at source scale) - the lw_golden metric basis."""
    cache = subject.setdefault("_cache", {})
    if "common" not in cache:
        from PIL import Image
        g1 = _g1()
        src = subject["source_rgb"]
        sh, sw = src.shape[:2]
        out = Image.fromarray(np.ascontiguousarray(subject["output_rgb"]))
        out = out.resize((sw, sh), Image.LANCZOS)
        cache["common"] = (g1._to_gray(src), g1._to_gray(np.asarray(out)))
    return cache["common"]


def _g1_value(metric: str):
    def measure(subject):
        g1 = _g1()
        src_g, out_g = _common(subject)
        if metric == "lap_ratio":
            return g1.laplacian_ratio(src_g, out_g)
        if metric == "halo_pct":
            return g1.overshoot_halo(src_g, out_g)["halo_pct"]
        if metric == "band_delta":
            return g1.banding_delta(src_g, out_g)
        raise KeyError(metric)
    return measure


def _cambi_value(subject):
    """lw_g1_gate.cambi_delta at OUTPUT scale (no common-scale resample - that
    resample is what blinds band_delta). None when ffmpeg/libvmaf is absent:
    the board then reads UNKNOWN, never green."""
    cache = subject.setdefault("_cache", {})
    if "cambi" not in cache:
        cache["cambi"] = _g1().cambi_delta(subject["source_rgb"], subject["output_rgb"])
    return cache["cambi"]


def _g1_gated(metric: str):
    def applies(subject):
        import lw_first_pass
        return metric in lw_first_pass.gate_metrics({metric: 0.0},
                                                    subject.get("backend", ""))
    return applies


def _g1_judge(metric: str):
    """PASS iff the LIVE G1 verdict raises no reason for this metric. The
    threshold table is read from the module at call time."""
    def judge(value, subject):
        import lw_first_pass
        g1 = _g1()
        gated = lw_first_pass.gate_metrics({metric: value}, subject.get("backend", ""))
        v = g1.verdict(gated, g1.DEFAULT_G1_THRESHOLDS)
        return not any(r.startswith(metric) for r in v["reasons"])
    return judge


def _g1_bar(metric: str, kind: str, key: str):
    def th(k):
        return lambda: _g1().DEFAULT_G1_THRESHOLDS[metric][k]
    if kind == "at_least":
        return Bar("at_least", lo=th(key))
    return Bar("at_most", hi=th(key))


def _fr(subject: dict) -> dict:
    """MS-SSIM + LPIPS through the live fr_metrics (pyiqa; .venv-metrics only).
    Planted outputs go to a temp PNG outside the repo and are removed."""
    cache = subject.setdefault("_cache", {})
    if "fr" not in cache:
        import tempfile

        from PIL import Image
        g1 = _g1()
        src_path = subject["source_path"]
        tmpdir = tempfile.mkdtemp(prefix="lw_gate_board_")
        try:
            dist = os.path.join(tmpdir, "out.png")
            Image.fromarray(np.ascontiguousarray(subject["output_rgb"])).save(dist)
            fr = g1.fr_metrics(dist, src_path, src_path, names=("ms_ssim", "lpips"))
        finally:
            for n in os.listdir(tmpdir):
                os.remove(os.path.join(tmpdir, n))
            os.rmdir(tmpdir)
        cache["fr"] = {"msssim": fr.get("ms_ssim"), "lpips": fr.get("lpips")}
    return cache["fr"]


def _fr_value(metric: str):
    def measure(subject):
        v = _fr(subject)[metric]
        return float(v) if isinstance(v, (int, float)) else None
    return measure


def _aspect_judge(value, subject):
    """PASS iff lw_upscale._finish accepts the frame's aspect (it raises on a
    non-16:9 frame - that refusal IS the gate firing)."""
    from PIL import Image

    import lw_upscale
    h, w = subject["output_rgb"].shape[:2]
    try:
        lw_upscale._finish(Image.new("RGB", (w, h)))
    except ValueError:
        return False
    return True


# ---------------------------------------------------------------- G2 subject
def _cp():
    import lw_clean_pass
    return lw_clean_pass


def coons_fill(img: np.ndarray, box) -> np.ndarray:
    """Smooth fill of box interior from all four boundary lines (a Coons
    patch): continuous with the art on every side, so a correct fill carries
    no seam of its own. Returns the interior block, float64."""
    a = np.asarray(img, dtype=np.float64)
    x0, y0, x1, y1 = (int(v) for v in box)
    h, w = a.shape[:2]
    ty, by_ = max(0, y0 - 1), min(h - 1, y1)
    lx, rx = max(0, x0 - 1), min(w - 1, x1)
    top, bot = a[ty, x0:x1], a[by_, x0:x1]
    left, right = a[y0:y1, lx], a[y0:y1, rx]
    tl, tr, bl, br = a[ty, lx], a[ty, rx], a[by_, lx], a[by_, rx]
    bh, bw = y1 - y0, x1 - x0
    v = ((np.arange(bh) + 1.0) / (bh + 1.0)).reshape((bh, 1) + (1,) * (a.ndim - 2))
    u = ((np.arange(bw) + 1.0) / (bw + 1.0)).reshape((1, bw) + (1,) * (a.ndim - 2))
    return ((1 - v) * top[None] + v * bot[None] + (1 - u) * left[:, None]
            + u * right[:, None]
            - ((1 - u) * (1 - v) * tl + u * (1 - v) * tr
               + (1 - u) * v * bl + u * v * br))


def g2_subject(g1_subject: dict) -> dict:
    """A clean-pass subject built from a frame: a credit-line-shaped mask in the
    bottom band (geometry from the operator's hand-clean captures, 549x69 at
    2560x1440 - docs/CLEAN_HANDEDIT_ANALYSIS_2026-08-22.md), placed over the
    busiest candidate patch so the fill really changes it, and a smooth
    Coons-patch fill standing in for a good inpaint. Outside the
    mask the frame is byte-identical, exactly as the live paste-back keeps it.
    """
    before = np.ascontiguousarray(g1_subject["output_rgb"]).copy()
    h, w = before.shape[:2]
    bw = max(24, int(round(w * 549 / 2560)))
    bh = max(12, int(round(h * 69 / 1440)))
    y0 = min(h - bh - 2, int(h * 0.88))
    gray = _g1()._to_gray(before)
    best = None
    for frac in (0.2, 0.35, 0.5, 0.65):
        x0 = max(1, min(w - bw - 1, int(w * frac) - bw // 2))
        var = float(np.var(gray[y0:y0 + bh, x0:x0 + bw]))
        if best is None or var > best[0]:
            best = (var, x0)
    x0 = best[1]
    box = (x0, y0, x0 + bw, y0 + bh)
    mask = np.zeros((h, w), dtype=bool)
    mask[y0:y0 + bh, x0:x0 + bw] = True
    after = before.astype(np.float64)
    after[y0:y0 + bh, x0:x0 + bw] = coons_fill(after, box)
    # "restored": the perfect clean - the golden frame carries no mark, so its
    # own art IS what a zero-residue removal must give back. The residue row
    # judges that (and its planted faint-residue copy) against a strong mark.
    subj = {"slug": g1_subject.get("slug", ""), "before": before,
            "after": _u8(after), "mask": mask, "box": box,
            "restored": before.copy()}
    for k in ("source_rgb", "output_rgb", "backend", "source_path"):
        if k in g1_subject:
            subj[k] = g1_subject[k]
    return subj


def _ring(subject):
    cache = subject.setdefault("_cache", {})
    if "ring" not in cache:
        cache["ring"] = _cp()._ring_mask(subject["mask"])
    return cache["ring"]


def _m_outside(subject):
    cp = _cp()
    b, a, m = subject["before"], subject["after"], subject["mask"]
    ssim, mad = cp.masked_identity(b, a, m)
    out = {"outside_ssim": ssim, "mad_outside": mad}
    if hasattr(cp, "outside_max_abs"):
        out["outside_max_abs"] = cp.outside_max_abs(b, a, m)
    return out


def _j_outside(value, subject):
    kw = {}
    if "outside_max_abs" in value:
        kw["outside_max_abs"] = value["outside_max_abs"]
    v = _cp().verify_verdict(value["outside_ssim"], value["mad_outside"], 0.0, False, 1.0,
                             **kw)
    return v["verdict"] != "discard"


def _m_noop(subject):
    return _cp()._inside_change_ssim(subject["before"], subject["after"], subject["mask"])


def _j_noop(value, subject):
    v = _cp().verify_verdict(1.0, 0.0, value, False, 1.0)
    return v["verdict"] != "fail"


def _m_seam(subject):
    return _cp().seam_ring_ssim(subject["after"], _ring(subject))


def _j_seam(value, subject):
    return "seam" not in _cp().verify_verdict(1.0, 0.0, 0.0, False, value)["flags"]


_READER = {}


def _reader():
    if "r" not in _READER:
        import easyocr  # lw-clean venv only
        _READER["r"] = easyocr.Reader(["en"], gpu=True, verbose=False)
    return _READER["r"]


STRONG_MARK_ALPHA = 0.9  # the "before" credit line: a fully legible mark


def _m_residue(subject):
    cp = _cp()
    marked = fault_text(subject["before"], subject["box"], alpha=STRONG_MARK_ALPHA)
    before_e = cp.text_energy(marked, subject["box"], _reader())
    after_e = cp.text_energy(subject["restored"], subject["box"], _reader())
    return {"before_energy": before_e, "after_energy": after_e}


def _plant_residue(subject):
    subject["restored"] = fault_text(subject["restored"], subject["box"],
                                     levels=RESIDUE_LEVELS)
    return subject


def _j_residue(value, subject):
    return not _cp()._residue_decision(value["before_energy"], value["after_energy"])


# ============================================================== calibration
# Each fault amplitude is set from evidence, not from "whatever turns it red".
# Values marked CALIBRATED were measured on the golden set by
# `lw_gate_board.py calibrate --golden`; the evidence string says how.
FAULT_EVIDENCE = {
    "G1.lap_ratio": ("down-up x2 bicubic",
                     "the historic double-resample softness bug AUDIT_GATES 3.1 names "
                     "(ratio < 0.9); a 2x round trip is the mildest real recurrence "
                     "(one extra resample pair at the 2560->1280 scale)"),
    "G1.halo_pct": ("USM r2 p150 t0 on the finished frame",
                    "realistic over-sharpen: a second USM pass at the clamp ceiling "
                    "lw_upscale._clamp_usm allows (percent <= 150); the fallback "
                    "upscaler measured halo 0.049-0.145 (QA Session 2)"),
    "G1.band_delta": ("posterize step 8 levels",
                      "8-level plateaus = a 5-bit-per-channel quantization, the "
                      "classic 8-bit gradient banding; band_delta bound 8 times in "
                      "719 audits (tests/test_g1_msssim_arm_binds.py census)"),
    "G1.cambi_delta": ("posterize step 8 levels",
                       "same fault as G1.band_delta (5-bit quantization); research R1 "
                       "measured CAMBI mlc=5 delta clean max 1.21 vs posterize_8 min "
                       "3.00 on the 12 golden frames (LEDGER 263)"),
    "G1.msssim": ("16 px horizontal shift",
                  "measured 2026-09-08: shift 16px -> msssim 0.8598 on a real frame "
                  "(tests/test_g1_msssim_arm_binds.py); the only geometric error class"),
    "G1.lpips": ("down-up x4 bicubic",
                 "measured blur r8 -> lpips 0.1568 (flag band) on a real frame "
                 "(tests/test_g1_msssim_arm_binds.py); a 4x round trip is that "
                 "order of detail loss"),
    "G0.aspect": ("letterbox to 16:10",
                  "the commonest non-16:9 drop in 0.Originals (16:10 monitor "
                  "wallpapers); ASPECT_TOL refuses it in lw_upscale._finish"),
    "G2.outside_identity": ("one 32x32 block +16 levels outside the mask",
                            "a localized composite bug; the live arm is a frame MEAN "
                            "(ssim 0.995 / mad 1.0) - see the proof table"),
    "G2.no_op": ("fill returned the input unchanged",
                 "the inpaint no-op the arm exists for (model returned its input)"),
    "G2.seam": ("fill offset +24 levels against its ring",
                "a hard seam: 24 levels is twice the operator's median per-step "
                "edit delta (11.8, CLEAN_HANDEDIT_ANALYSIS)"),
    "G2.text_residue": ("credit line at +4 luma levels over the fill",
                        "faintest real residue the operator's eye rejected: 105-cleanup "
                        "hand-clean step 70 median 3.77 levels (n=733) and final step "
                        "4.5 levels (n=2813), alpha ~0.02 white / 0.06 dark; the DA "
                        "veil (alpha 0.09-0.13) is ~5x stronger (docs/GATE_BOARD.md)"),
}


FAULT_NAME = {
    "G0.aspect": "letterbox_16x10", "G1.lap_ratio": "downup_x2",
    "G1.halo_pct": "usm_r2_p150", "G1.band_delta": "posterize_8",
    "G1.cambi_delta": "posterize_8",
    "G1.msssim": "shift_16px", "G1.lpips": "downup_x4",
    "G2.outside_identity": "outside_block_32px_16lv", "G2.no_op": "noop_fill",
    "G2.seam": "seam_offset_24lv", "G2.text_residue": "credit_line_4lv",
}


def _amp(name):
    return FAULT_EVIDENCE[name][0]


def _ev(name):
    return FAULT_EVIDENCE[name][1]


# Calibrated amplitudes (see FAULT_EVIDENCE and docs/GATE_BOARD.md).
LAPRATIO_DOWNUP = 2.0
HALO_USM = (2.0, 150, 0)
BAND_STEP = 8
MSSSIM_SHIFT_PX = 16
LPIPS_DOWNUP = 4.0
OUTSIDE_BLOCK = (32, 16.0)
SEAM_OFFSET = 24.0
RESIDUE_LEVELS = 4.0


# ============================================================== LW registry
def lw_board(envs=ENVS) -> Board:
    """The LW gate ladder as fault-proven rows. `envs` restricts which
    interpreter-specific rows are registered (CI and system python: base)."""
    board = Board()
    envs = tuple(envs)

    def add(row, plant):
        if row.kind != "validation" and row.env not in envs:
            return
        board.add(row)
        if plant is not None:
            plant.__name__ = FAULT_NAME[row.name]
            board.fault(row.name, amplitude=_amp(row.name), evidence=_ev(row.name))(plant)

    def on_output(fn):
        def plant(subj):
            subj["output_rgb"] = fn(subj["output_rgb"])
            return subj
        plant.__name__ = fn.__name__
        return plant

    # ---- G0: aspect refusal (lw_upscale._finish)
    def m_aspect(s):
        h, w = s["output_rgb"].shape[:2]
        return w / h

    add(Row("G0.aspect", "never squash or ship a non-16:9 frame", m_aspect,
            Bar("between", lo=lambda: 16 / 9 - _aspect_tol(), hi=lambda: 16 / 9 + _aspect_tol()),
            unit="w/h", where="whole frame", judge=_aspect_judge, gate="G0"),
        on_output(lambda a: fault_letterbox(a)))

    # ---- G1: upscale gate (numpy arms)
    add(Row("G1.lap_ratio", "the upscale must not soften the art",
            _g1_value("lap_ratio"), _g1_bar("lap_ratio", "at_least", "fail"),
            unit="ratio", where="whole frame at source scale",
            judge=_g1_judge("lap_ratio"), applies=_g1_gated("lap_ratio"), gate="G1"),
        on_output(lambda a: fault_downup(a, LAPRATIO_DOWNUP)))
    add(Row("G1.halo_pct", "no sharpening halos around edges",
            _g1_value("halo_pct"), _g1_bar("halo_pct", "at_most", "flag"),
            unit="frac of near-edge px", where="strong source edges",
            judge=_g1_judge("halo_pct"), applies=_g1_gated("halo_pct"), gate="G1"),
        on_output(lambda a: fault_usm(a, *HALO_USM)))
    add(Row("G1.band_delta", "no banding added to smooth gradients",
            _g1_value("band_delta"), _g1_bar("band_delta", "at_most", "flag"),
            unit="density delta", where="smooth regions",
            judge=_g1_judge("band_delta"), applies=_g1_gated("band_delta"), gate="G1"),
        on_output(lambda a: fault_posterize(a, BAND_STEP)))
    add(Row("G1.cambi_delta", "no banding added to smooth gradients",
            _cambi_value, _g1_bar("cambi_delta", "at_most", "flag"),
            unit="CAMBI mlc5 delta", where="whole frame at output scale",
            judge=_g1_judge("cambi_delta"), applies=_g1_gated("cambi_delta"), gate="G1"),
        on_output(lambda a: fault_posterize(a, BAND_STEP)))
    # ---- G1: full-reference arms (.venv-metrics)
    add(Row("G1.msssim", "the frame keeps the source's structure and geometry",
            _fr_value("msssim"), _g1_bar("msssim", "at_least", "pass"),
            unit="MS-SSIM", where="whole frame at common scale",
            judge=_g1_judge("msssim"), applies=_g1_gated("msssim"), env="metrics",
            gate="G1"),
        on_output(lambda a: fault_shift(a, MSSSIM_SHIFT_PX)))
    add(Row("G1.lpips", "the frame stays perceptually the source",
            _fr_value("lpips"), _g1_bar("lpips", "at_most", "pass"),
            unit="LPIPS", where="whole frame at common scale",
            judge=_g1_judge("lpips"), applies=_g1_gated("lpips"), env="metrics",
            gate="G1"),
        on_output(lambda a: fault_downup(a, LPIPS_DOWNUP)))

    # ---- G2: clean-pass verify (lw_clean_pass.verify_verdict)
    def on_after(fn):
        def plant(subj):
            subj["after"] = fn(subj)
            return subj
        plant.__name__ = getattr(fn, "__name__", "plant")
        return plant

    add(Row("G2.outside_identity", "nothing outside the edit mask changes",
            _m_outside, Bar("at_least", lo=lambda: _cp().OUTSIDE_SSIM_MIN),
            unit="ssim / mad", where="outside the mask", judge=_j_outside,
            applies=lambda s: "mask" in s, gate="G2"),
        on_after(lambda s: fault_outside_block(s["after"], s["mask"], *OUTSIDE_BLOCK)))
    add(Row("G2.no_op", "the clean actually changed the marked region",
            _m_noop, Bar("at_most", hi=lambda: _cp().CHANGE_SSIM_MAX),
            unit="ssim inside", where="inside the mask", judge=_j_noop,
            applies=lambda s: "mask" in s, gate="G2"),
        on_after(lambda s: np.array(s["before"], copy=True)))
    add(Row("G2.seam", "no visible seam at the edit boundary",
            _m_seam, Bar("at_least", lo=lambda: _cp().SEAM_SSIM_MIN),
            unit="ssim ring", where="8px ring around the mask", judge=_j_seam,
            applies=lambda s: "mask" in s, gate="G2"),
        on_after(lambda s: fault_seam(s["after"], s["mask"], SEAM_OFFSET)))
    add(Row("G2.text_residue", "zero watermark: no text left where the mark was",
            _m_residue, None, unit="text energy", where="the mark's box",
            judge=_j_residue, applies=lambda s: "mask" in s, env="clean", gate="G2"),
        _plant_residue)

    # ---- operator validation rows (never measured, never count toward done)
    add(Row("V.reads_like_original", "reads like the original art", kind="validation",
            gate="G4"), None)
    add(Row("V.zero_watermark_eye", "no ghost, band or faint residue visible at 1:1",
            kind="validation", gate="G4"), None)
    return board


def _aspect_tol():
    import lw_upscale
    return lw_upscale.ASPECT_TOL


def registered_rows() -> List[str]:
    """Every measured row of the full LW registry (all envs)."""
    return [r.name for r in lw_board().rows if r.kind != "validation"]


# ============================================================== golden driver
def golden_subjects(manifest_path, root=ROOT, limit=None):
    """Yield (g1 subject, g2 subject) per golden case. Bytes stay on disk."""
    from PIL import Image

    import lw_upscale
    man = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    for i, case in enumerate(man["cases"]):
        if limit is not None and i >= limit:
            break
        src_path = str(Path(root) / case["input"]["path"])
        out_path = str(Path(root) / case["baseline"]["path"])
        with Image.open(src_path) as im:
            src = np.asarray(im.convert("RGB")).copy()
        with Image.open(out_path) as im:
            out = np.asarray(im.convert("RGB")).copy()
        sh, sw = src.shape[:2]
        backend = "downscale-only" if lw_upscale._covers_target(sw, sh) else "ijn"
        g1s = {"slug": case["slug"], "source_rgb": src, "output_rgb": out,
               "backend": backend, "source_path": src_path}
        yield g1s, g2_subject(g1s)


def prove_golden(envs, progress=None, limit=None, root=ROOT) -> dict:
    board = lw_board(envs=envs)
    g1_rows = [r for r in board.rows if r.gate in ("G0", "G1") or r.kind == "validation"]
    g2_rows = [r for r in board.rows if r.gate == "G2"]
    per, slugs = [], []
    manifest = Path(root) / "data" / "golden" / "golden_set.json"
    for i, (g1s, g2s) in enumerate(golden_subjects(manifest, root, limit=limit)):
        proofs = [board.prove_row(r, g1s) for r in g1_rows]
        proofs += [board.prove_row(r, g2s) for r in g2_rows]
        per.append(proofs)
        slugs.append(g1s["slug"])
        if progress:
            progress(i + 1, g1s["slug"])
    agg = aggregate(per, board)
    return {"board": board, "agg": agg, "slugs": slugs}


def _env_py(env, root):
    if env == "metrics":
        return Path(root) / ".venv-metrics" / "Scripts" / "python.exe"
    return Path(_cp().CLEAN_VENV_PY)  # definition site: lw_clean_pass


def _proofs_path(root):
    return Path(root) / "ops" / "runtime" / "gate_proofs.json"


def _partial_path(env, root):
    return _proofs_path(root).with_name(f"gate_proofs.{env}.json")


def _progress_writer(root, task, total, eta_per):
    """FLEET-COMMON item 12 progress file, one write per subject."""
    path = Path(root) / "ops" / "loop" / "control" / "progress" / f"{task}.json"

    def write(done, step, status="running"):
        rec = {"task": task, "pct": int(100 * done / max(1, total)), "step": step,
               "eta_s": int(eta_per * max(0, total - done)), "status": status,
               "updated": time.strftime("%Y-%m-%dT%H:%M:%S")}
        try:
            _atomic_write_json(path, rec)
        except OSError:
            pass
    return write


def _run_env_subprocess(env, limit, root):
    py = _env_py(env, root)
    if not py.is_file():
        return f"{env}: interpreter missing"
    argv = [str(py), str(Path(__file__).resolve()), "prove", "--golden", "--env", env,
            "--repo-root", str(root), "--out", str(_partial_path(env, root))]
    if limit is not None:
        argv += ["--limit", str(limit)]
    r = subprocess.run(argv, cwd=str(root), capture_output=True, text=True,
                       creationflags=NO_WINDOW, timeout=7200)
    last = (r.stdout or "").strip().splitlines()[-1:] or (r.stderr or "").strip().splitlines()[-1:]
    return f"{env}: rc={r.returncode} {last}"


def _merge_partials(agg, root, notes):
    for env in ("metrics", "clean"):
        try:
            part = json.loads(_partial_path(env, root).read_text(encoding="ascii"))
            have = {r["row"] for r in agg}
            agg += [r for r in part["rows"] if r["row"] not in have]
        except (OSError, ValueError, KeyError) as exc:
            notes.append(f"{env}: partial unreadable ({exc.__class__.__name__})")
    full = lw_board()
    have = {x["row"] for x in agg}
    for r in full.rows:
        if r.name not in have:
            agg.append({"row": r.name, "state": UNKNOWN, "n_proven": 0, "n_applicable": 0,
                        "n_subjects": 0, "fault": "", "subjects": [], "gate": r.gate,
                        "env": r.env, "detail": "env run produced no proof"})
    return agg, full


def _prove_clean_held(limit, root):
    """The OCR residue rows (EasyOCR on cuda) under ONE machine-wide GPU hold,
    borrowed from lw_g1_gate (same venv family; no forked helper). A leaf: no
    subprocess is started inside the hold. fr_metrics acquires for itself, so
    the metrics env needs no hold here, and the `--env all` parent never holds
    while it spawns the env children."""
    with _g1().gpu_lock("cuda"):
        return prove_golden(("clean",), limit=limit, root=root)


def main(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser(prog="lw_gate_board")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("prove", help="prove every row over the golden set")
    p.add_argument("--golden", action="store_true", required=True)
    p.add_argument("--env", default="all", choices=ENVS + ("all",))
    p.add_argument("--out", default=None)
    p.add_argument("--limit", type=int, default=None)
    c = sub.add_parser("check", help="exit 1 unless the recorded table is all PROVEN")
    for sp in (p, c):
        sp.add_argument("--repo-root", default=None,
                        help="tree holding data/golden and ops/runtime (default: this tree)")
    a = ap.parse_args(argv)
    root = Path(getattr(a, "repo_root", None) or str(ROOT))

    if a.cmd == "check":
        problems = check_proofs(_proofs_path(root), lw_board())
        if problems is None:
            print("gate proofs: absent - run `prove --golden --env all`")
            return 2
        for pr in problems:
            print("  " + pr)
        print(f"gate proofs: {'GREEN' if not problems else 'NOT GREEN'}")
        return 0 if not problems else 1

    if a.env == "all":
        prog = _progress_writer(root, "gate-board-prove", 3, 600)
        prog(0, "env metrics (.venv-metrics, MS-SSIM + LPIPS)")
        notes = [_run_env_subprocess("metrics", a.limit, root)]
        prog(1, "env clean (lw-clean venv, OCR text residue)")
        notes.append(_run_env_subprocess("clean", a.limit, root))
        prog(2, "env base (numpy G0/G1/G2)")
        res = prove_golden(("base",), limit=a.limit, root=root)
        agg, full = _merge_partials(res["agg"], root, notes)
        write_proofs(_proofs_path(root), agg, registry_digest(full), res["slugs"],
                     extra={"env_runs": notes})
        prog(3, "written ops/runtime/gate_proofs.json", status="done")
        print(proof_table(agg))
        for n in notes:
            print("  env " + n)
        return 0 if summary(agg)["green"] else 1

    if a.env == "clean":
        res = _prove_clean_held(a.limit, root)
    else:
        res = prove_golden((a.env,), limit=a.limit, root=root)
    board = res["board"]
    agg = [r for r in res["agg"] if r.get("env", "base") == a.env or r["state"] == VALIDATION]
    out = Path(a.out) if a.out else _partial_path(a.env, root)
    write_proofs(out, agg, registry_digest(board), res["slugs"])
    print(proof_table(agg))
    return 0 if summary(agg)["green"] else 1


if __name__ == "__main__":
    sys.exit(main())
