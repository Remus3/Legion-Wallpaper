"""RRF-2.3b residual (MAIN REPO-REVIEW 2.3, LEDGER 299/305): a FLEET-KIT-vN
FIX / ORDER from MAIN is adopted by the PARENT responder through
tools/lw_kit_adopt.adopt (verify, copy, re-embed, conformance, kit tests - no
model), and the child is handed ONLY the residual (tree-specific wiring, the
suite, the commit and the answer) at sonnet / medium.

Why: the v17 child (2026-10-11 05:09) ran opus and timed out at 1800 s with
the copy done and nothing committed - the deterministic half had been paid
for at model rates."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import lw_inbox_responder as R  # noqa: E402

NOTE = "2026-10-10-1312-from-MAIN-FIX-to-ALL-SIX-FLEET-KIT-v17-shell-edits-ONE-ANSWER.md"
BUNDLE = "2026-10-10-1312-from-MAIN-FLEET-KIT-v17"
MATCH = "MAIN PROVENANCE (computed by the parent responder): MATCH - sha256 x"


def _note(tmp_path, name=NOTE, bundle=BUNDLE):
    note = tmp_path / name
    note.write_text("x\n", encoding="ascii")
    if bundle:
        (tmp_path / bundle).mkdir()
    return note


# ------------------------------------------------------------- the bundle


def test_the_bundle_is_the_sibling_dir_with_the_same_stamp_and_version(tmp_path):
    note = _note(tmp_path)
    assert R.kit_bundle(note) == tmp_path / BUNDLE


def test_no_bundle_dir_means_no_bundle(tmp_path):
    assert R.kit_bundle(_note(tmp_path, bundle=None)) is None


def test_a_bundle_of_another_version_is_not_this_notes(tmp_path):
    note = _note(tmp_path, bundle="2026-10-10-1312-from-MAIN-FLEET-KIT-v16")
    assert R.kit_bundle(note) is None


def test_a_kit_note_not_from_main_has_no_bundle(tmp_path):
    name = "2026-10-10-1312-from-RC-FIX-to-ALL-FLEET-KIT-v17-x.md"
    note = _note(tmp_path, name=name, bundle="2026-10-10-1312-from-RC-FLEET-KIT-v17")
    assert R.kit_bundle(note) is None


def test_a_main_note_that_is_not_a_kit_note_has_no_bundle(tmp_path):
    note = _note(tmp_path, name="2026-10-10-1312-from-MAIN-ORDER-to-LW-other.md")
    assert R.kit_bundle(note) is None


# ------------------------------------------------------------- the adoption


def test_nothing_is_adopted_without_a_main_match(tmp_path):
    calls = []
    note = _note(tmp_path)
    for prov in ("", "MAIN PROVENANCE (computed by the parent responder): MISMATCH - x",
                 "MAIN PROVENANCE (computed by the parent responder): UNAVAILABLE - x",
                 "MAIN PROVENANCE (computed by the parent responder): UNCOMMITTED - x"):
        out = R.kit_adoption(note, prov, adopt=lambda *a, **k: calls.append(a),
                             bundle_ok=lambda b: True)
        assert out is None
    assert calls == []


def test_an_unverified_bundle_is_reported_and_never_copied(tmp_path):
    calls = []
    out = R.kit_adoption(_note(tmp_path), MATCH, adopt=lambda *a, **k: calls.append(a),
                         bundle_ok=lambda b: False)
    assert calls == []
    assert out["ok"] is False and out["stage"] == "provenance"


def test_a_verified_bundle_is_adopted_into_this_repo_with_the_kit_tests(tmp_path):
    seen = {}

    def _adopt(bundle, root, run_tests=None):
        seen.update(bundle=bundle, root=root, run_tests=run_tests)
        return {"ok": True, "stage": "done", "problems": [], "residual": []}

    out = R.kit_adoption(_note(tmp_path), MATCH, adopt=_adopt, bundle_ok=lambda b: True)
    assert out["ok"] is True
    assert seen == {"bundle": tmp_path / BUNDLE, "root": R.ROOT, "run_tests": True}


def test_an_adopt_crash_is_a_reported_stage_not_a_dead_tick(tmp_path):
    def _boom(*_a, **_k):
        raise RuntimeError("disk")

    out = R.kit_adoption(_note(tmp_path), MATCH, adopt=_boom, bundle_ok=lambda b: True)
    assert out["ok"] is False and out["stage"] == "adopt" and "disk" in out["problems"][0]


def test_the_bundle_check_reads_every_file_against_mains_committed_outbox(tmp_path,
                                                                         monkeypatch):
    bundle = tmp_path / BUNDLE
    bundle.mkdir()
    for name in ("MANIFEST.json", "fleet_headless.py"):
        (bundle / name).write_bytes(b"x")
    asked = []
    monkeypatch.setattr(R, "main_outbox", lambda: tmp_path / "outbox")
    monkeypatch.setattr(R.lw_headless_env.kit, "verify_main",
                        lambda path, outbox, rel=None: asked.append(rel) or rel != f"{BUNDLE}/fleet_headless.py")
    assert R.bundle_verified(bundle) is False
    assert sorted(asked) == [f"{BUNDLE}/MANIFEST.json", f"{BUNDLE}/fleet_headless.py"]


def test_an_empty_bundle_is_not_verified(tmp_path, monkeypatch):
    (tmp_path / BUNDLE).mkdir()
    monkeypatch.setattr(R, "main_outbox", lambda: tmp_path / "outbox")
    monkeypatch.setattr(R.lw_headless_env.kit, "verify_main", lambda *a, **k: True)
    assert R.bundle_verified(tmp_path / BUNDLE) is False


# ------------------------------------------------------------- the hand-off


class _Conn:
    def close(self):
        pass


def _seams(seen):
    def _run(argv, **kw):
        seen["argv"], seen["kw"] = argv, kw

        class _R:
            returncode = 0
            stdout = json.dumps({"result": "ok", "usage": {}})
            stderr = ""
        return _R()

    return {"url_source": lambda: "http://127.0.0.1:4999/tc-acct/fake-id",
            "connect": lambda *a, **k: _Conn(), "run": _run,
            "exe_source": lambda: "fake-claude.exe"}


def _spawn(monkeypatch, tmp_path, adoption):
    monkeypatch.setattr(R, "main_provenance", lambda p: MATCH)
    monkeypatch.setattr(R, "kit_adoption", lambda p, prov: adoption)
    seen = {}
    out = R.spawn(_note(tmp_path), kit_seams=_seams(seen))
    argv = seen["argv"]
    return out, argv[argv.index("--model") + 1], argv[argv.index("--effort") + 1], \
        seen["kw"]["input"]


def test_a_residual_goes_to_the_child_at_sonnet_medium(monkeypatch, tmp_path):
    adoption = {"ok": False, "stage": "tests", "problems": ["kit tests rc=1"],
                "residual": ["kit tests rc=1: assert 15 == 17"]}
    out, model, effort, prompt = _spawn(monkeypatch, tmp_path, adoption)
    assert (model, effort) == (R.RESIDUAL_MODEL, R.RESIDUAL_EFFORT) == ("sonnet", "medium")
    assert "KIT ADOPTION (done by the parent responder)" in prompt
    assert "assert 15 == 17" in prompt
    assert "stage tests" in out.reason


def test_a_clean_adoption_still_hands_only_the_residual(monkeypatch, tmp_path):
    adoption = {"ok": True, "stage": "done", "problems": [], "residual": []}
    _, model, effort, prompt = _spawn(monkeypatch, tmp_path, adoption)
    assert (model, effort) == ("sonnet", "medium")
    assert "do NOT copy the bundle again" in prompt


def test_an_adoption_that_stopped_early_keeps_the_full_code_run(monkeypatch, tmp_path):
    adoption = {"ok": False, "stage": "verify", "problems": ["bundle file missing: x"],
                "residual": []}
    _, model, effort, prompt = _spawn(monkeypatch, tmp_path, adoption)
    assert (model, effort) == ("opus", R.CODE_EFFORT)
    assert "bundle file missing: x" in prompt


def test_a_note_with_no_adoption_is_unchanged(monkeypatch, tmp_path):
    _, model, effort, prompt = _spawn(monkeypatch, tmp_path, None)
    assert (model, effort) == ("opus", R.CODE_EFFORT)
    assert "KIT ADOPTION" not in prompt


def test_a_dry_run_never_adopts(monkeypatch, tmp_path):
    def _never(*_a, **_k):
        raise AssertionError("dry run adopted")

    monkeypatch.setattr(R, "main_provenance", lambda p: MATCH)
    monkeypatch.setattr(R, "kit_adoption", _never)
    out = R.spawn(_note(tmp_path), dry_run=True, kit_seams=_seams({}))
    assert out.verdict == R.AUTO
