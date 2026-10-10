"""Deterministic FLEET-KIT adoption steps (RRF-2.3b, MAIN 2246 REPO-REVIEW 2.3).

# arch: kit adoption without a model - verify, copy, re-embed

WHY THIS EXISTS. A FLEET-KIT-vN ORDER used to be adopted end to end by a
headless model run (LEDGER 293: one such child died mid-suite with 21 files
drafted and nothing committed). Most of the work needs no judgment: check the
delivered bundle against its own MANIFEST.json, copy it into ops/fleet_kit/
byte for byte, and splice FLEET-COMMON.md between the CLAUDE.md markers. This
module does those steps; a model is kept only for the residual (tree-specific
wiring the ORDER describes in prose).

SLICE 1 (this file): verify_bundle, copy_bundle, embed_block. Still to come in
RRF-2.3b: a CLI that chains them with fleet_headless.conformance() and the kit
tests, and the responder hand-off of the residual at sonnet/medium.

Pure stdlib, no machine paths: every function takes its directories as
arguments, so tests run on tmp_path and never touch the live kit.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

# Must equal fleet_headless.BEGIN / END (pinned by tests/test_lw_kit_adopt.py):
# conformance() hashes exactly text[i + len(BEGIN):j].
BEGIN, END = "<!-- FLEET-COMMON BEGIN -->\n", "<!-- FLEET-COMMON END -->"
MANIFEST = "MANIFEST.json"
COMMON = "FLEET-COMMON.md"


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _manifest(bundle):
    try:
        man = json.loads((Path(bundle) / MANIFEST).read_text(encoding="ascii"))
    except (OSError, ValueError):
        return None
    if not isinstance(man, dict) or not isinstance(man.get("files"), dict):
        return None
    return man


def verify_bundle(bundle):
    """Problems with a kit bundle directory against its own MANIFEST.json; [] = clean.

    Checks every listed file exists with the listed sha256, that no unlisted
    file rides along, and that common_block_sha256 is the hash of
    FLEET-COMMON.md (the block conformance() later compares CLAUDE.md to)."""
    bundle = Path(bundle)
    man = _manifest(bundle)
    if man is None:
        return ["bundle manifest missing or unreadable"]
    files = man["files"]
    problems = []
    for name, want in sorted(files.items()):
        f = bundle / name
        if Path(name).name != name:
            problems.append(f"bundle manifest name is not a plain file: {name}")
        elif not f.is_file():
            problems.append(f"bundle file missing: {name}")
        elif _sha256(f) != want:
            problems.append(f"bundle file hash mismatch: {name}")
    for f in sorted(bundle.iterdir()):
        if f.is_file() and f.name != MANIFEST and f.name not in files:
            problems.append(f"bundle file not in manifest: {f.name}")
    if files.get(COMMON) != man.get("common_block_sha256"):
        problems.append(f"common_block_sha256 != sha256({COMMON})")
    return problems


def _atomic_copy(src, dest):
    tmp = dest.with_name(dest.name + ".tmp")
    tmp.write_bytes(Path(src).read_bytes())
    tmp.replace(dest)


def copy_bundle(bundle, dest):
    """Copy a verified bundle into dest (ops/fleet_kit/); [] = copied and re-verified.

    Refuses before writing anything when the bundle does not verify. The
    manifest goes last, so an interrupted copy leaves the old manifest and
    conformance() fails loudly instead of passing on a half-new kit."""
    problems = verify_bundle(bundle)
    if problems:
        return problems
    bundle, dest = Path(bundle), Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    for name in sorted(_manifest(bundle)["files"]):
        _atomic_copy(bundle / name, dest / name)
    _atomic_copy(bundle / MANIFEST, dest / MANIFEST)
    return [f"after copy: {p}" for p in _verify_listed(dest)]


def _verify_listed(dest):
    """verify_bundle minus the unlisted-file check: dest may hold local extras."""
    return [p for p in verify_bundle(dest) if not p.startswith("bundle file not in manifest")]


def embed_block(text, block):
    """CLAUDE.md text with block spliced between the FLEET-COMMON markers.

    Raises ValueError unless each marker appears exactly once, BEGIN first."""
    if text.count(BEGIN) != 1 or text.count(END) != 1:
        raise ValueError("CLAUDE.md must carry each FLEET-COMMON marker exactly once")
    i, j = text.find(BEGIN), text.find(END)
    if j < i:
        raise ValueError("FLEET-COMMON END marker precedes BEGIN")
    return text[:i + len(BEGIN)] + block + text[j:]
