"""Legion Wallpaper - model weight pins: assert the bytes, do not merely record them.

The gap this closes: `lw_upscale.first_pass` RECORDS `model_sha256` into every
audit, and nothing ever asserted it equals the weight the pipeline was
calibrated on. A swapped, re-downloaded or corrupted weight file would drift
the frozen golden (pv 6d43a6d4, ADR-004) while the provenance record still
looked perfect. Recorded is not pinned.

The manifest is `config/model_pins.json` (basename -> {sha256, bytes, role,
why}). `tools/models/` is gitignored - weights are never tracked - so the
manifest is the only tracked statement of which bytes the calibration holds
for.

FOUR states, never two. Collapsing them is how a guard turns into a lie:
  MATCH     present, sha256 equals the pin. Verified.
  MISMATCH  present, sha256 differs. HARD FAILURE - the whole point.
  ABSENT    not on disk. NOT a failure: CI runs on Linux with no weights and a
            fresh clone has none either. Reported as a skip, and `ok` is False
            so absent can never read as verified.
  UNPINNED  on disk but not in the manifest. NOT a failure (the V1 DAT2
            fallback is unpinned today), but reported distinctly so an
            unpinned model is never mistaken for a verified one.

Environment:
  LW_MODEL_PINS                 override the manifest path (tests, and a
                                staged manifest during a deliberate swap).
  LW_ALLOW_MODEL_PIN_MISMATCH   escape hatch: downgrade a MISMATCH refusal to a
                                warning, for a deliberate model change before
                                the manifest is updated. Named in the refusal
                                message so the operator does not have to read
                                this file to find it.

Import contract: stdlib ONLY. This module is imported by `tools/lw_upscale.py`,
which runs under `.venv-upscale` and is contractually limited to PIL + numpy +
stdlib, and by `tools/drift_guard.py` under system python.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path

# --------------------------------------------------------------------------
# Constants
# --------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PINS_PATH = REPO_ROOT / "config" / "model_pins.json"

PINS_ENV = "LW_MODEL_PINS"
OVERRIDE_ENV = "LW_ALLOW_MODEL_PIN_MISMATCH"

STATE_MATCH = "match"
STATE_MISMATCH = "mismatch"
STATE_ABSENT = "absent"
STATE_UNPINNED = "unpinned"

# 1 MiB chunks - stream, never read a 140 MB weight into memory.
_CHUNK = 1 << 20


class ModelPinMismatch(RuntimeError):
    """A pinned weight is present on disk and its bytes are not the pinned bytes."""


@dataclass(frozen=True)
class PinResult:
    """One verification verdict. `state` is the truth; `ok`/`failed` are views.

    `ok` is True ONLY for MATCH. Absent and unpinned are deliberately not ok -
    that is what stops "no weights here" from reading as "weights verified".
    `failed` is True ONLY for MISMATCH, and only when not overridden.
    """

    state: str
    path: str
    basename: str
    expected_sha256: str | None = None
    actual_sha256: str | None = None
    expected_bytes: int | None = None
    actual_bytes: int | None = None
    overridden: bool = False

    @property
    def ok(self) -> bool:
        return self.state == STATE_MATCH

    @property
    def failed(self) -> bool:
        return self.state == STATE_MISMATCH and not self.overridden

    def describe(self) -> str:
        """One human line. Used verbatim in the refusal, so it names everything."""
        if self.state == STATE_MATCH:
            return f"{self.basename}: sha256 matches the pin ({self.expected_sha256})"
        if self.state == STATE_ABSENT:
            return f"{self.basename}: pinned but not on disk at {self.path} (skipped, not verified)"
        if self.state == STATE_UNPINNED:
            return f"{self.basename}: not pinned in {pins_path()} (not verified)"
        return (
            f"{self.basename}: PINNED WEIGHT MISMATCH at {self.path}\n"
            f"  expected sha256 {self.expected_sha256} ({self.expected_bytes} bytes)\n"
            f"  actual   sha256 {self.actual_sha256} ({self.actual_bytes} bytes)\n"
            f"  The pipeline calibration (ADR-004 golden pv 6d43a6d4) is pinned to the\n"
            f"  expected bytes. Re-fetch the weight, or - for a DELIBERATE model change -\n"
            f"  update config/model_pins.json, or set {OVERRIDE_ENV}=1 for this run."
        )


# --------------------------------------------------------------------------
# Loading
# --------------------------------------------------------------------------


def pins_path() -> str:
    """The manifest path in force: LW_MODEL_PINS if set, else config/model_pins.json."""
    return os.environ.get(PINS_ENV) or str(DEFAULT_PINS_PATH)


def load_manifest(pins_path_override: str | None = None) -> dict:
    """Return the whole manifest document. Raises on a missing/invalid manifest.

    A manifest that cannot be parsed is NOT treated as "no pins": an unparsed
    config presents exactly like one with no entries, which is how a guard goes
    silently dead (the same failure mode CLAUDE.md records for
    .claude/settings.json).
    """
    path = pins_path_override or pins_path()
    with open(path, encoding="utf-8") as fh:
        doc = json.load(fh)
    if not isinstance(doc, dict) or not isinstance(doc.get("models"), dict):
        raise ValueError(f"model pin manifest is malformed (no models map): {path}")
    return doc


def load_pins(pins_path_override: str | None = None) -> dict:
    """Return {basename: entry} from the manifest."""
    return load_manifest(pins_path_override)["models"]


def model_root(pins_path_override: str | None = None, root: str | None = None) -> Path:
    """Absolute directory the manifest's `model_root` points at."""
    doc = load_manifest(pins_path_override)
    base = Path(root) if root else REPO_ROOT
    return base / doc.get("model_root", "tools/models")


# --------------------------------------------------------------------------
# Hashing
# --------------------------------------------------------------------------


def sha256_file(path: str | os.PathLike[str]) -> str:
    """Streamed sha256 of a file. Never reads the whole weight into memory."""
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(_CHUNK), b""):
            h.update(chunk)
    return h.hexdigest()


# --------------------------------------------------------------------------
# Verification
# --------------------------------------------------------------------------


def verify_path(
    path: str | os.PathLike[str],
    pins: dict | None = None,
    pins_path: str | None = None,
    hash_on_size_mismatch: bool = False,
) -> PinResult:
    """Verify ONE model file against the manifest. Never raises on a mismatch.

    Size is a cheap pre-filter: a wrong byte count already proves a mismatch,
    so the 140 MB hash is skipped and `actual_sha256` stays None. The fatal
    path (`assert_pinned`) re-runs with hash_on_size_mismatch=True so the
    refusal can still name a real actual sha.
    """
    if pins is None:
        pins = load_pins(pins_path)
    p = Path(path)
    name = p.name
    entry = pins.get(name)

    if entry is None:
        return PinResult(state=STATE_UNPINNED, path=str(p), basename=name)

    expected_sha = entry.get("sha256")
    expected_bytes = entry.get("bytes")

    if not p.exists():
        return PinResult(
            state=STATE_ABSENT,
            path=str(p),
            basename=name,
            expected_sha256=expected_sha,
            expected_bytes=expected_bytes,
        )

    actual_bytes = p.stat().st_size
    if expected_bytes is not None and actual_bytes != expected_bytes:
        actual_sha = sha256_file(p) if hash_on_size_mismatch else None
        return PinResult(
            state=STATE_MISMATCH,
            path=str(p),
            basename=name,
            expected_sha256=expected_sha,
            actual_sha256=actual_sha,
            expected_bytes=expected_bytes,
            actual_bytes=actual_bytes,
        )

    actual_sha = sha256_file(p)
    state = STATE_MATCH if actual_sha == expected_sha else STATE_MISMATCH
    return PinResult(
        state=state,
        path=str(p),
        basename=name,
        expected_sha256=expected_sha,
        actual_sha256=actual_sha,
        expected_bytes=expected_bytes,
        actual_bytes=actual_bytes,
    )


def override_active(env: dict | None = None) -> bool:
    """True when the operator has armed the deliberate-model-change escape hatch."""
    src = os.environ if env is None else env
    return str(src.get(OVERRIDE_ENV, "")).strip().lower() in {"1", "true", "yes", "on"}


def assert_pinned(
    path: str | os.PathLike[str],
    pins: dict | None = None,
    pins_path: str | None = None,
) -> PinResult:
    """Verify one model and REFUSE (ModelPinMismatch) if it is present and drifted.

    Returns the PinResult for MATCH, ABSENT and UNPINNED - none of those is a
    failure. Only a present-and-drifted pinned weight raises, and only when the
    escape hatch is not armed.
    """
    res = verify_path(path, pins=pins, pins_path=pins_path)
    if res.state != STATE_MISMATCH:
        return res

    if override_active():
        # Deliberate change: hand back the mismatch, flagged, without refusing.
        return PinResult(**{**res.__dict__, "overridden": True})

    # Fatal path only: pay for the hash so the message names a real actual sha
    # even when the size pre-filter short-circuited above.
    if res.actual_sha256 is None:
        res = verify_path(
            path, pins=pins, pins_path=pins_path, hash_on_size_mismatch=True
        )
    raise ModelPinMismatch(res.describe())


def verify_pins(pins_path: str | None = None, root: str | None = None) -> dict:
    """Verify every pinned model under the manifest's model_root.

    Returns a report with the four states kept apart:
      {"ok", "verified", "failed", "absent", "results", "model_root"}
    `ok` is False only when something is present and drifted. An empty
    model_root yields ok=True with an empty `verified` list - absent is a skip,
    and the empty `verified` is what stops that from reading as a pass.
    """
    doc = load_manifest(pins_path)
    pins = doc["models"]
    base = Path(root) if root else REPO_ROOT
    mroot = base / doc.get("model_root", "tools/models")

    results = [verify_path(mroot / name, pins=pins) for name in sorted(pins)]
    return {
        "model_root": str(mroot),
        "results": results,
        "verified": [r.basename for r in results if r.state == STATE_MATCH],
        "failed": [r.basename for r in results if r.state == STATE_MISMATCH],
        "absent": [r.basename for r in results if r.state == STATE_ABSENT],
        "ok": not any(r.state == STATE_MISMATCH for r in results),
    }


def main(argv=None) -> int:
    """CLI: print the per-model verdict. Exit 3 on a present-and-drifted weight."""
    rep = verify_pins()
    print(f"model_root: {rep['model_root']}")
    for res in rep["results"]:
        print(f"[{res.state.upper():8}] {res.describe()}")
    print(
        f"verified={len(rep['verified'])} failed={len(rep['failed'])} "
        f"absent={len(rep['absent'])}"
    )
    return 0 if rep["ok"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
