"""drift_guard: pinned model weights still hash to the bytes the manifest pins.

THE GAP. `tools/lw_upscale.py` RECORDS `model_sha256` into the audit of every
upscale run, and until 2026-09-08 nothing ever ASSERTED it. A re-fetched,
swapped or truncated weight would drift the frozen golden (pv 6d43a6d4) while
the provenance record still looked perfect, because recording a hash proves
only that a hash was taken - not that it was the right one. `lw_model_pins`
carries the assertion and its own tests; this file covers the drift_guard ARM
that runs it every session, which is a separate thing that can be wired wrong.

The states that matter are not two but four, and the one that bites is ABSENT:
CI and a fresh clone have no weights (`tools/models/` is gitignored), so absent
must report as absent and must NEVER read as verified. A guard that silently
passes when it could not look is the failure this repo already records for
`.claude/settings.json`, where an unparsed config presented exactly like one
with no hooks.

HERMETIC. Every test builds its own manifest and its own fake weight files in
tmp_path and points the check at them. Nothing here reads the real 140 MB
weight or this machine's `tools/models/`, so the file behaves the same on CI
Linux as on the Legion box.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

import drift_guard as DG  # noqa: E402
import lw_model_pins  # noqa: E402


def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _manifest(tmp_path: Path, model_root: Path, entries: dict) -> str:
    """Write a throwaway pins manifest and return its path."""
    doc = {"schema": 1, "model_root": str(model_root), "models": entries}
    p = tmp_path / "pins.json"
    p.write_text(json.dumps(doc), encoding="utf-8")
    return str(p)


def _weight(model_root: Path, name: str, body: bytes) -> Path:
    model_root.mkdir(parents=True, exist_ok=True)
    p = model_root / name
    p.write_bytes(body)
    return p


def _run(pins_path: str) -> tuple[list[str], list[str]]:
    """Run the arm in isolation and return (problems, notes) it produced."""
    DG.problems.clear()
    DG.notes.clear()
    DG.check_model_pins(pins_path=pins_path)
    return list(DG.problems), list(DG.notes)


def _fixture(tmp_path: Path, body: bytes, pinned: bytes | None = None):
    """A manifest pinning `pinned` (default: the bytes actually written)."""
    root = tmp_path / "models"
    _weight(root, "w.safetensors", body)
    target = body if pinned is None else pinned
    entry = {"sha256": _sha(target), "bytes": len(target), "role": "test"}
    return _manifest(tmp_path, root, {"w.safetensors": entry}), root


def test_a_matching_weight_is_a_note_and_never_a_breach(tmp_path):
    pins, _ = _fixture(tmp_path, b"the pinned bytes")
    problems, notes = _run(pins)
    assert problems == []
    assert any("verified" in n for n in notes), notes


def test_a_mismatched_weight_is_a_breach(tmp_path):
    # Same byte COUNT, different content: proves the arm is not size-only.
    pins, _ = _fixture(tmp_path, b"the WRONG bytes!", pinned=b"the pinned byte")
    root = tmp_path / "models"
    _weight(root, "w.safetensors", b"the WRONG bytes")
    problems, _ = _run(pins)
    assert len(problems) == 1, problems
    assert "MODEL PIN MISMATCH" in problems[0]


def test_the_breach_names_both_shas_so_it_is_actionable(tmp_path):
    # Equal length on purpose: a size mismatch short-circuits the hash by
    # design, so only equal-size drift proves the message carries a real sha.
    good, bad = b"pinned-bytes!", b"drifted-bytes"
    root = tmp_path / "models"
    _weight(root, "w.safetensors", bad)
    pins = _manifest(
        tmp_path, root,
        {"w.safetensors": {"sha256": _sha(good), "bytes": len(good), "role": "t"}},
    )
    problems, _ = _run(pins)
    assert _sha(good) in problems[0], "expected sha must be named"
    assert _sha(bad) in problems[0], "actual sha must be named, not just 'differs'"


def test_an_absent_weight_is_a_note_and_never_reads_as_verified(tmp_path):
    root = tmp_path / "models"
    root.mkdir()
    pins = _manifest(
        tmp_path, root,
        {"gone.safetensors": {"sha256": _sha(b"x"), "bytes": 1, "role": "t"}},
    )
    problems, notes = _run(pins)
    assert problems == [], "absent is CI and a fresh clone, not drift"
    assert any("absent" in n for n in notes), notes
    assert not any("weight(s) verified" in n for n in notes), (
        "absent must never be reported as verified - that is the silent-pass trap"
    )


def test_an_unreadable_manifest_is_itself_a_breach(tmp_path):
    p = tmp_path / "broken.json"
    p.write_text("{not json", encoding="utf-8")
    problems, _ = _run(str(p))
    assert len(problems) == 1
    assert "manifest unreadable" in problems[0]


def test_a_missing_manifest_is_a_breach_not_a_silent_pass(tmp_path):
    problems, _ = _run(str(tmp_path / "does-not-exist.json"))
    assert len(problems) == 1, "a manifest that is not there cannot verify anything"


def test_the_breach_clears_when_the_weight_is_corrected(tmp_path):
    """Appears is not goes-away: a report you cannot clear is a defect."""
    good = b"the pinned bytes"
    root = tmp_path / "models"
    _weight(root, "w.safetensors", b"drifted")
    pins = _manifest(
        tmp_path, root,
        {"w.safetensors": {"sha256": _sha(good), "bytes": len(good), "role": "t"}},
    )
    problems, _ = _run(pins)
    assert len(problems) == 1, "must fire first, or clearing proves nothing"

    _weight(root, "w.safetensors", good)  # operator re-fetches the real weight
    problems, notes = _run(pins)
    assert problems == [], "the same check must go green on the corrected file"
    assert any("verified" in n for n in notes)


def test_the_run_scoped_hatch_does_NOT_silence_the_session_gate(tmp_path, monkeypatch):
    """Deliberate design call, not an oversight.

    LW_ALLOW_MODEL_PIN_MISMATCH authorises ONE inference run to proceed on a
    weight that is not the pinned one. It does not make the repo's recorded
    calibration true again. drift_guard reports STATE, so it stays red until
    the manifest is updated to say which bytes the pipeline is now calibrated
    on - the fix is a manifest edit, not an env var. A gate that any env var
    can silence is a gate that dies quietly, which is the whole failure mode
    this repo's hook-verification rule exists to prevent.
    """
    good = b"the pinned bytes"
    root = tmp_path / "models"
    _weight(root, "w.safetensors", b"deliberately different")
    pins = _manifest(
        tmp_path, root,
        {"w.safetensors": {"sha256": _sha(good), "bytes": len(good), "role": "t"}},
    )
    problems, _ = _run(pins)
    assert len(problems) == 1, "no hatch armed = breach"

    monkeypatch.setenv(lw_model_pins.OVERRIDE_ENV, "1")
    problems, _ = _run(pins)
    assert len(problems) == 1, (
        "the session gate must still report a drifted weight - the hatch lets a "
        "RUN proceed, it does not make the manifest correct"
    )


def test_updating_the_manifest_is_what_clears_it(tmp_path):
    """The documented remedy actually works - otherwise the gate is a dead end."""
    actual = b"the new weight bytes"
    root = tmp_path / "models"
    _weight(root, "w.safetensors", actual)
    stale = _manifest(
        tmp_path, root,
        {"w.safetensors": {"sha256": _sha(b"old"), "bytes": 3, "role": "t"}},
    )
    assert len(_run(stale)[0]) == 1

    fresh = _manifest(
        tmp_path, root,
        {"w.safetensors": {"sha256": _sha(actual), "bytes": len(actual), "role": "t"}},
    )
    assert _run(fresh)[0] == [], "re-pinning the manifest must clear the breach"


def test_main_actually_calls_the_arm(monkeypatch):
    """Mutation guard: a check that main() never calls asserts nothing."""
    called = []
    monkeypatch.setattr(DG, "check_model_pins", lambda *a, **k: called.append(1))
    for name in [n for n in dir(DG) if n.startswith("check_") and n != "check_model_pins"]:
        monkeypatch.setattr(DG, name, lambda *a, **k: None)
    DG.problems.clear()
    DG.notes.clear()
    DG.main()
    assert called == [1], "check_model_pins is not wired into main()"


def test_the_arm_is_not_size_only(tmp_path):
    """Kills the mutant that compares st_size and skips the hash on a match."""
    good, bad = b"AAAAAAAA", b"BBBBBBBB"
    assert len(good) == len(bad)
    root = tmp_path / "models"
    _weight(root, "w.safetensors", bad)
    pins = _manifest(
        tmp_path, root,
        {"w.safetensors": {"sha256": _sha(good), "bytes": len(good), "role": "t"}},
    )
    problems, _ = _run(pins)
    assert len(problems) == 1, (
        "equal size with different content must still breach - a size-only "
        "check would pass here and that is exactly the drift being guarded"
    )
