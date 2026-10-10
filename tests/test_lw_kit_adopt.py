"""RRF-2.3b slice 1: deterministic kit adoption - verify, copy, re-embed.

`tools/lw_kit_adopt.py` replaces the model-driven part of a FLEET-KIT-vN
adoption that needs no judgment: check a delivered bundle against its own
MANIFEST.json, copy it into ops/fleet_kit/ only when every hash matches, and
splice FLEET-COMMON.md between the CLAUDE.md markers. Every test runs on
tmp_path fixtures; nothing reads or writes the live kit.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import lw_kit_adopt as ka  # noqa: E402

BLOCK = "\n## FLEET COMMON\n\nrule one\n"


def _sha(text):
    return hashlib.sha256(text.encode("ascii")).hexdigest()


def _bundle(tmp_path, files=None, version=99):
    files = files or {"FLEET-COMMON.md": BLOCK, "fleet_x.py": "X = 1\n"}
    b = tmp_path / "bundle"
    b.mkdir()
    for name, text in files.items():
        (b / name).write_bytes(text.encode("ascii"))
    man = {"version": version, "common_block_sha256": _sha(files.get("FLEET-COMMON.md", "")),
           "files": {n: _sha(t) for n, t in files.items()}}
    (b / "MANIFEST.json").write_text(json.dumps(man), encoding="ascii")
    return b


def test_verify_bundle_clean_is_empty(tmp_path):
    assert ka.verify_bundle(_bundle(tmp_path)) == []


def test_verify_bundle_reports_edited_missing_and_unlisted(tmp_path):
    b = _bundle(tmp_path)
    (b / "fleet_x.py").write_bytes(b"X = 2\n")
    (b / "FLEET-COMMON.md").unlink()
    (b / "stray.py").write_bytes(b"")
    problems = ka.verify_bundle(b)
    assert "bundle file hash mismatch: fleet_x.py" in problems
    assert "bundle file missing: FLEET-COMMON.md" in problems
    assert "bundle file not in manifest: stray.py" in problems


def test_verify_bundle_unreadable_manifest(tmp_path):
    b = tmp_path / "bundle"
    b.mkdir()
    assert ka.verify_bundle(b) == ["bundle manifest missing or unreadable"]


def test_verify_bundle_block_hash_must_match_common_file(tmp_path):
    b = _bundle(tmp_path)
    man = json.loads((b / "MANIFEST.json").read_text(encoding="ascii"))
    man["common_block_sha256"] = "0" * 64
    (b / "MANIFEST.json").write_text(json.dumps(man), encoding="ascii")
    assert "common_block_sha256 != sha256(FLEET-COMMON.md)" in ka.verify_bundle(b)


def test_copy_bundle_refuses_a_bad_bundle_and_writes_nothing(tmp_path):
    b = _bundle(tmp_path)
    (b / "fleet_x.py").write_bytes(b"tampered\n")
    dest = tmp_path / "kit"
    dest.mkdir()
    (dest / "fleet_x.py").write_bytes(b"old\n")
    problems = ka.copy_bundle(b, dest)
    assert problems and problems[0].startswith("bundle file hash mismatch")
    assert (dest / "fleet_x.py").read_bytes() == b"old\n"
    assert not (dest / "MANIFEST.json").exists()


def test_copy_bundle_copies_every_file_and_manifest_byte_exact(tmp_path):
    b = _bundle(tmp_path)
    dest = tmp_path / "kit"
    dest.mkdir()
    (dest / "fleet_x.py").write_bytes(b"old\n")
    assert ka.copy_bundle(b, dest) == []
    for name in ("FLEET-COMMON.md", "fleet_x.py", "MANIFEST.json"):
        assert (dest / name).read_bytes() == (b / name).read_bytes()
    assert not list(dest.glob("*.tmp"))
    assert ka.verify_bundle(dest) == []


def test_embed_block_splices_between_markers_only():
    text = ("# head\n\n" + ka.BEGIN + "old block\n" + ka.END + "\n# tail\n")
    out = ka.embed_block(text, BLOCK)
    assert out == "# head\n\n" + ka.BEGIN + BLOCK + ka.END + "\n# tail\n"
    i, j = out.find(ka.BEGIN), out.find(ka.END)
    assert _sha(out[i + len(ka.BEGIN):j]) == _sha(BLOCK)


def test_embed_block_refuses_missing_or_duplicate_markers():
    import pytest

    with pytest.raises(ValueError):
        ka.embed_block("no markers\n", BLOCK)
    with pytest.raises(ValueError):
        ka.embed_block(ka.BEGIN + ka.BEGIN + "x\n" + ka.END + "\n", BLOCK)


def test_markers_match_the_vendored_kit():
    """The splice must produce exactly what fleet_headless.conformance() hashes."""
    src = (ROOT / "ops" / "fleet_kit" / "fleet_headless.py").read_text(encoding="ascii")
    assert 'BEGIN, END = "<!-- FLEET-COMMON BEGIN -->\\n", "<!-- FLEET-COMMON END -->"' in src
    assert (ka.BEGIN, ka.END) == ("<!-- FLEET-COMMON BEGIN -->\n", "<!-- FLEET-COMMON END -->")


def test_embed_into_live_claude_md_is_identity():
    """Re-embedding the vendored FLEET-COMMON.md into CLAUDE.md changes nothing."""
    text = (ROOT / "CLAUDE.md").read_bytes().decode("ascii")
    block = (ROOT / "ops" / "fleet_kit" / "FLEET-COMMON.md").read_bytes().decode("ascii")
    assert ka.embed_block(text, block) == text
