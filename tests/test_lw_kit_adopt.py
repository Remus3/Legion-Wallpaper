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


def test_verify_bundle_requires_the_common_block_file(tmp_path):
    """A bundle without FLEET-COMMON.md (and no common_block_sha256) must not
    verify clean: embed_block would have nothing to splice."""
    b = _bundle(tmp_path, files={"fleet_x.py": "X = 1\n"})
    man = json.loads((b / "MANIFEST.json").read_text(encoding="ascii"))
    man.pop("common_block_sha256")
    (b / "MANIFEST.json").write_text(json.dumps(man), encoding="ascii")
    assert "bundle manifest does not list FLEET-COMMON.md" in ka.verify_bundle(b)


# ---------------------------------------------------------------- slice 2: the CLI


def _live_root(tmp_path):
    """A throwaway repo root holding a byte copy of the live kit + CLAUDE.md."""
    import shutil

    root = tmp_path / "repo"
    kit = root / "ops" / "fleet_kit"
    kit.mkdir(parents=True)
    for f in (ROOT / "ops" / "fleet_kit").iterdir():
        if f.is_file():
            shutil.copyfile(f, kit / f.name)
    shutil.copyfile(ROOT / "CLAUDE.md", root / "CLAUDE.md")
    return root


def _live_bundle(tmp_path):
    """The live kit as a delivered bundle (only the manifest-listed files)."""
    import shutil

    b = tmp_path / "bundle"
    b.mkdir()
    kit = ROOT / "ops" / "fleet_kit"
    man = json.loads((kit / "MANIFEST.json").read_text(encoding="ascii"))
    for name in list(man["files"]) + ["MANIFEST.json"]:
        shutil.copyfile(kit / name, b / name)
    return b


def _ok_tests(calls):
    def run(root, files):
        calls.append((root, list(files)))
        return 0, "5 passed"
    return run


def test_adopt_live_kit_into_a_copy_is_clean_and_runs_the_kit_tests(tmp_path):
    root, calls = _live_root(tmp_path), []
    (root / "tests").mkdir()
    for name in ("test_fleet_kit_conformance.py", "test_lw_kit_adopt.py", "test_other.py"):
        (root / "tests" / name).write_bytes(b"")
    res = ka.adopt(_live_bundle(tmp_path), root, run_tests=_ok_tests(calls))
    assert res["ok"] is True and res["stage"] == "done" and res["problems"] == []
    assert "test_other.py" not in [Path(f).name for f in calls[0][1]]
    assert len(calls) == 1 and calls[0][0] == root
    names = [Path(f).name for f in calls[0][1]]
    assert "test_fleet_kit_conformance.py" in names and "test_lw_kit_adopt.py" in names


def test_adopt_new_common_block_is_embedded_and_conformance_is_the_new_kits(tmp_path):
    """A bundle with a changed FLEET-COMMON.md lands in CLAUDE.md, and the
    conformance check is loaded from the COPIED kit (its KIT_VERSION)."""
    root, b = _live_root(tmp_path), _live_bundle(tmp_path)
    new_block = (b / "FLEET-COMMON.md").read_text(encoding="ascii") + "18. NEW RULE.\n"
    (b / "FLEET-COMMON.md").write_bytes(new_block.encode("ascii"))
    man = json.loads((b / "MANIFEST.json").read_text(encoding="ascii"))
    man["files"]["FLEET-COMMON.md"] = man["common_block_sha256"] = _sha(new_block)
    (b / "MANIFEST.json").write_text(json.dumps(man), encoding="ascii")
    res = ka.adopt(b, root, run_tests=_ok_tests([]))
    assert res["problems"] == [] and res["ok"] is True
    text = (root / "CLAUDE.md").read_bytes().decode("ascii")
    assert "18. NEW RULE.\n" + ka.END in text
    assert "\r\n" not in text and not list(root.glob("*.tmp"))


def test_adopt_stops_at_verify_and_touches_nothing(tmp_path):
    root, b = _live_root(tmp_path), _live_bundle(tmp_path)
    before = (root / "CLAUDE.md").read_bytes()
    (b / "FLEET-COMMON.md").write_bytes(b"tampered\n")
    calls = []
    res = ka.adopt(b, root, run_tests=_ok_tests(calls))
    assert res["ok"] is False and res["stage"] == "verify"
    assert "bundle file hash mismatch: FLEET-COMMON.md" in res["problems"]
    assert (root / "CLAUDE.md").read_bytes() == before and calls == []


def test_adopt_refuses_a_downgrade(tmp_path):
    root, b = _live_root(tmp_path), _live_bundle(tmp_path)
    man = json.loads((b / "MANIFEST.json").read_text(encoding="ascii"))
    man["version"] = man["version"] - 1
    (b / "MANIFEST.json").write_text(json.dumps(man), encoding="ascii")
    res = ka.adopt(b, root, run_tests=_ok_tests([]))
    assert res["ok"] is False and res["stage"] == "version"
    kit_man = json.loads((root / "ops/fleet_kit/MANIFEST.json").read_text(encoding="ascii"))
    assert kit_man["version"] != man["version"]


def test_adopt_conformance_failure_is_reported_and_tests_not_run(tmp_path):
    root, calls = _live_root(tmp_path), []
    res = ka.adopt(_live_bundle(tmp_path), root, run_tests=_ok_tests(calls),
                   conformance_fn=lambda r: ["kit file missing or edited: x.py"])
    assert res["ok"] is False and res["stage"] == "conformance"
    assert res["problems"] == ["kit file missing or edited: x.py"] and calls == []


def test_adopt_kit_test_failure_is_the_residual(tmp_path):
    """Red kit tests after a clean copy + embed are the model's residual
    (tree-specific wiring, e.g. the version pin), not a copy failure."""
    root = _live_root(tmp_path)
    res = ka.adopt(_live_bundle(tmp_path), root,
                   run_tests=lambda r, f: (1, "FAILED tests/test_x.py::test_pin"))
    assert res["ok"] is False and res["stage"] == "tests"
    assert res["residual"] and "FAILED tests/test_x.py::test_pin" in res["residual"][0]


def test_adopt_embed_refusal_is_reported(tmp_path):
    root = _live_root(tmp_path)
    (root / "CLAUDE.md").write_bytes(b"# no markers\n")
    res = ka.adopt(_live_bundle(tmp_path), root, run_tests=_ok_tests([]))
    assert res["ok"] is False and res["stage"] == "embed"
    assert (root / "CLAUDE.md").read_bytes() == b"# no markers\n"


def test_cli_check_on_live_root_exits_zero(capsys):
    assert ka.main(["check", "--root", str(ROOT)]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["ok"] is True and out["problems"] == []


def test_cli_adopt_exit_codes_and_json(tmp_path, capsys, monkeypatch):
    root, b = _live_root(tmp_path), _live_bundle(tmp_path)
    monkeypatch.setattr(ka, "run_kit_tests", lambda r, f: (0, "ok"))
    assert ka.main(["adopt", str(b), "--root", str(root)]) == 0
    assert json.loads(capsys.readouterr().out)["stage"] == "done"
    (b / "FLEET-COMMON.md").write_bytes(b"x\n")
    assert ka.main(["adopt", str(b), "--root", str(root)]) == 1
    assert json.loads(capsys.readouterr().out)["stage"] == "verify"
    assert ka.main([]) == 2


def test_cli_no_tests_skips_the_kit_tests(tmp_path, capsys, monkeypatch):
    root, b = _live_root(tmp_path), _live_bundle(tmp_path)

    def boom(r, f):
        raise AssertionError("kit tests must not run with --no-tests")
    monkeypatch.setattr(ka, "run_kit_tests", boom)
    assert ka.main(["adopt", str(b), "--root", str(root), "--no-tests"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["ok"] is True and out["stage"] == "done"
