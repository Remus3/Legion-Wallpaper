"""Tests for tools/lw_model_pins.py and its wiring into tools/lw_upscale.py.

The gap these close: lw_upscale RECORDED `model_sha256` into every audit and
nothing ever ASSERTED it. A swapped, re-downloaded or corrupted weight file
would drift the frozen golden (pv 6d43a6d4) while the provenance record still
looked perfect. Recorded is not pinned.

HERMETIC BY CONSTRUCTION. Not one test here reads the real 140 MB weight, and
none needs `tools/models/` to exist - CI runs on Linux with no weights at all.
Every case builds temp files with known content and points the verifier at a
temp manifest via the LW_MODEL_PINS env override. The single test that reads a
tracked repo file (config/model_pins.json) reads SOURCE, not machine state.

Two of these exist specifically because a guard nobody has watched fail asserts
nothing:
  - test_upscale_refuses_a_mismatched_weight_before_inference kills the arm:
    delete or invert the check in upscale_spandrel and it fails.
  - test_*_clears_when_the_weight_is_corrected proves the refusal GOES AWAY,
    not merely that it appears.
"""

import hashlib
import json
import os
import sys

import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, REPO_ROOT)
# tools/ on sys.path too, so `lw_model_pins` is the SAME module object
# lw_upscale binds by path. Two module objects would give two distinct
# ModelPinMismatch classes and `pytest.raises` matches by identity.
sys.path.insert(0, os.path.join(REPO_ROOT, "tools"))

import lw_model_pins  # noqa: E402

from tools import lw_upscale  # noqa: E402

# The ADR-004 primary first-pass upscaler. Values from the ADR text itself, so
# this test fails if the manifest and the decision record ever disagree.
ADR004_BASENAME = "4x_IllustrationJaNai_V3detail_DAT2_28k_bf16.safetensors"
ADR004_SHA256 = "eb9faf6a37de81406765e0c99e76ad7dafe67e4877f32e186085ac277a0e6181"
ADR004_BYTES = 139793020

GOOD = b"the-pinned-weight-bytes" * 64
BAD_SAME_SIZE = b"the-drifted-weight-byte" * 64      # same length, different content
BAD_OTHER_SIZE = b"short"


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _manifest(tmp_path, basename, data, model_root="models"):
    """Write a temp manifest pinning `basename` to sha256/len of `data`.

    Returns the manifest path. The model file itself is NOT written here - the
    caller decides whether it is present, matching or drifted, because that is
    exactly the axis under test.
    """
    doc = {
        "schema": 1,
        "model_root": model_root,
        "models": {
            basename: {
                "sha256": _sha(data),
                "bytes": len(data),
                "role": "test fixture",
                "why": "hermetic fixture, not a real weight",
            }
        },
    }
    path = tmp_path / "model_pins.json"
    path.write_text(json.dumps(doc, indent=2), encoding="ascii")
    return path


# ---------------------------------------------------------------------------
# The tracked manifest agrees with ADR-004
# ---------------------------------------------------------------------------


def test_repo_manifest_pins_the_adr004_model():
    """config/model_pins.json pins the V3 detail DAT2 weight ADR-004 promoted."""
    pins = lw_model_pins.load_pins()
    assert ADR004_BASENAME in pins, sorted(pins)
    entry = pins[ADR004_BASENAME]
    assert entry["sha256"] == ADR004_SHA256
    assert entry["bytes"] == ADR004_BYTES
    assert "ADR-004" in entry["why"]


def test_repo_manifest_is_extensible():
    """The manifest is a map, not a single hardcoded entry - more can be pinned."""
    doc = json.loads(
        open(os.path.join(REPO_ROOT, "config", "model_pins.json"), encoding="ascii").read()
    )
    assert isinstance(doc.get("models"), dict)
    assert isinstance(doc.get("model_root"), str) and doc["model_root"]
    assert doc.get("schema") == 1


# ---------------------------------------------------------------------------
# Three states, never two: match / mismatch / absent (+ unpinned, distinct)
# ---------------------------------------------------------------------------


def test_states_are_four_distinct_values():
    """Absent must never read as verified, and unpinned must never read as absent."""
    states = {
        lw_model_pins.STATE_MATCH,
        lw_model_pins.STATE_MISMATCH,
        lw_model_pins.STATE_ABSENT,
        lw_model_pins.STATE_UNPINNED,
    }
    assert len(states) == 4


def test_verify_path_present_and_matching(tmp_path):
    pins_file = _manifest(tmp_path, "w.safetensors", GOOD)
    weight = tmp_path / "w.safetensors"
    weight.write_bytes(GOOD)

    res = lw_model_pins.verify_path(str(weight), pins_path=str(pins_file))
    assert res.state == lw_model_pins.STATE_MATCH
    assert res.ok is True
    assert res.failed is False
    assert res.actual_sha256 == _sha(GOOD)


def test_verify_path_present_and_mismatched_same_size(tmp_path):
    """Same byte count, different content - the size pre-filter cannot catch it."""
    pins_file = _manifest(tmp_path, "w.safetensors", GOOD)
    weight = tmp_path / "w.safetensors"
    weight.write_bytes(BAD_SAME_SIZE)
    assert len(BAD_SAME_SIZE) == len(GOOD)

    res = lw_model_pins.verify_path(str(weight), pins_path=str(pins_file))
    assert res.state == lw_model_pins.STATE_MISMATCH
    assert res.failed is True
    assert res.ok is False
    assert res.actual_sha256 == _sha(BAD_SAME_SIZE)
    assert res.expected_sha256 == _sha(GOOD)


def test_verify_path_size_mismatch_skips_the_hash(tmp_path):
    """Cheap pre-filter: a wrong size is a mismatch without hashing the file."""
    pins_file = _manifest(tmp_path, "w.safetensors", GOOD)
    weight = tmp_path / "w.safetensors"
    weight.write_bytes(BAD_OTHER_SIZE)

    res = lw_model_pins.verify_path(str(weight), pins_path=str(pins_file))
    assert res.state == lw_model_pins.STATE_MISMATCH
    assert res.actual_sha256 is None          # not hashed - that is the point
    assert res.actual_bytes == len(BAD_OTHER_SIZE)
    assert res.expected_bytes == len(GOOD)

    forced = lw_model_pins.verify_path(
        str(weight), pins_path=str(pins_file), hash_on_size_mismatch=True
    )
    assert forced.actual_sha256 == _sha(BAD_OTHER_SIZE)


def test_verify_path_absent_is_not_a_failure(tmp_path):
    """CI and fresh clones have no weights. Absent is a skip, never a pass."""
    pins_file = _manifest(tmp_path, "w.safetensors", GOOD)
    res = lw_model_pins.verify_path(
        str(tmp_path / "w.safetensors"), pins_path=str(pins_file)
    )
    assert res.state == lw_model_pins.STATE_ABSENT
    assert res.failed is False
    assert res.ok is False                     # absent must NOT read as verified


def test_verify_path_unpinned_is_distinct(tmp_path):
    """An unpinned model is not a failure and is not the same as absent."""
    pins_file = _manifest(tmp_path, "w.safetensors", GOOD)
    other = tmp_path / "someone_elses.safetensors"
    other.write_bytes(b"whatever")

    res = lw_model_pins.verify_path(str(other), pins_path=str(pins_file))
    assert res.state == lw_model_pins.STATE_UNPINNED
    assert res.failed is False
    assert res.ok is False


def test_verify_pins_absent_model_root_reports_skips_not_passes(tmp_path):
    """verify_pins over a model_root with nothing in it: skipped, not verified."""
    pins_file = _manifest(tmp_path, "w.safetensors", GOOD, model_root="models")
    (tmp_path / "models").mkdir()

    rep = lw_model_pins.verify_pins(pins_path=str(pins_file), root=str(tmp_path))
    assert rep["failed"] == []
    assert rep["verified"] == []
    assert rep["absent"] == ["w.safetensors"]
    assert rep["ok"] is True


def test_verify_pins_flags_a_drifted_weight(tmp_path):
    pins_file = _manifest(tmp_path, "w.safetensors", GOOD, model_root="models")
    (tmp_path / "models").mkdir()
    (tmp_path / "models" / "w.safetensors").write_bytes(BAD_SAME_SIZE)

    rep = lw_model_pins.verify_pins(pins_path=str(pins_file), root=str(tmp_path))
    assert rep["failed"] == ["w.safetensors"]
    assert rep["ok"] is False

    # ... and CLEARS once the weight is corrected.
    (tmp_path / "models" / "w.safetensors").write_bytes(GOOD)
    rep2 = lw_model_pins.verify_pins(pins_path=str(pins_file), root=str(tmp_path))
    assert rep2["failed"] == []
    assert rep2["verified"] == ["w.safetensors"]
    assert rep2["ok"] is True


# ---------------------------------------------------------------------------
# assert_pinned: the refusal, its message, and the escape hatch
# ---------------------------------------------------------------------------


def test_assert_pinned_raises_and_names_both_shas_and_the_hatch(tmp_path, monkeypatch):
    pins_file = _manifest(tmp_path, "w.safetensors", GOOD)
    weight = tmp_path / "w.safetensors"
    weight.write_bytes(BAD_SAME_SIZE)
    monkeypatch.delenv(lw_model_pins.OVERRIDE_ENV, raising=False)

    with pytest.raises(lw_model_pins.ModelPinMismatch) as exc:
        lw_model_pins.assert_pinned(str(weight), pins_path=str(pins_file))

    msg = str(exc.value)
    assert _sha(GOOD) in msg                   # expected
    assert _sha(BAD_SAME_SIZE) in msg          # actual
    assert lw_model_pins.OVERRIDE_ENV in msg   # the way out, named in the refusal


def test_assert_pinned_names_the_actual_sha_even_on_a_size_mismatch(tmp_path):
    """The fast path skips the hash; the FATAL path still names a real sha."""
    pins_file = _manifest(tmp_path, "w.safetensors", GOOD)
    weight = tmp_path / "w.safetensors"
    weight.write_bytes(BAD_OTHER_SIZE)

    with pytest.raises(lw_model_pins.ModelPinMismatch) as exc:
        lw_model_pins.assert_pinned(str(weight), pins_path=str(pins_file))
    assert _sha(BAD_OTHER_SIZE) in str(exc.value)


def test_assert_pinned_clears_when_the_weight_is_corrected(tmp_path):
    """Appears is not goes-away: prove the refusal LIFTS on a corrected file."""
    pins_file = _manifest(tmp_path, "w.safetensors", GOOD)
    weight = tmp_path / "w.safetensors"

    weight.write_bytes(BAD_SAME_SIZE)
    with pytest.raises(lw_model_pins.ModelPinMismatch):
        lw_model_pins.assert_pinned(str(weight), pins_path=str(pins_file))

    weight.write_bytes(GOOD)
    res = lw_model_pins.assert_pinned(str(weight), pins_path=str(pins_file))
    assert res.state == lw_model_pins.STATE_MATCH


def test_assert_pinned_allows_absent_and_unpinned(tmp_path):
    pins_file = _manifest(tmp_path, "w.safetensors", GOOD)
    absent = lw_model_pins.assert_pinned(
        str(tmp_path / "w.safetensors"), pins_path=str(pins_file)
    )
    assert absent.state == lw_model_pins.STATE_ABSENT

    other = tmp_path / "unpinned.safetensors"
    other.write_bytes(b"x")
    unpinned = lw_model_pins.assert_pinned(str(other), pins_path=str(pins_file))
    assert unpinned.state == lw_model_pins.STATE_UNPINNED


def test_escape_hatch_downgrades_the_refusal(tmp_path, monkeypatch):
    """A deliberate model change is possible without editing code."""
    pins_file = _manifest(tmp_path, "w.safetensors", GOOD)
    weight = tmp_path / "w.safetensors"
    weight.write_bytes(BAD_SAME_SIZE)

    monkeypatch.setenv(lw_model_pins.OVERRIDE_ENV, "1")
    res = lw_model_pins.assert_pinned(str(weight), pins_path=str(pins_file))
    assert res.state == lw_model_pins.STATE_MISMATCH
    assert res.overridden is True


def test_pins_env_override_selects_the_manifest(tmp_path, monkeypatch):
    """LW_MODEL_PINS points the loader at another manifest (used by these tests)."""
    pins_file = _manifest(tmp_path, "w.safetensors", GOOD)
    monkeypatch.setenv(lw_model_pins.PINS_ENV, str(pins_file))
    pins = lw_model_pins.load_pins()
    assert list(pins) == ["w.safetensors"]


# ---------------------------------------------------------------------------
# THE ARM: lw_upscale refuses a drifted weight BEFORE any inference
# ---------------------------------------------------------------------------


def _drifted_weight(tmp_path, monkeypatch, content):
    pins_file = _manifest(tmp_path, "w.safetensors", GOOD)
    weight = tmp_path / "w.safetensors"
    weight.write_bytes(content)
    monkeypatch.setenv(lw_model_pins.PINS_ENV, str(pins_file))
    monkeypatch.delenv(lw_model_pins.OVERRIDE_ENV, raising=False)
    return str(weight)


def test_upscale_refuses_a_mismatched_weight_before_inference(tmp_path, monkeypatch):
    """MUTATION GUARD. Remove or invert the check in upscale_spandrel and this
    test fails: with the check gone the call dies on the torch import or on the
    missing source file instead, never with ModelPinMismatch."""
    weight = _drifted_weight(tmp_path, monkeypatch, BAD_SAME_SIZE)

    with pytest.raises(lw_model_pins.ModelPinMismatch):
        lw_upscale.upscale_spandrel(str(tmp_path / "no_such_source.png"), weight)


def test_upscale_pin_check_fires_before_the_source_is_even_opened(tmp_path, monkeypatch):
    """The refusal must precede inference, so a nonexistent source is irrelevant."""
    weight = _drifted_weight(tmp_path, monkeypatch, BAD_OTHER_SIZE)
    with pytest.raises(lw_model_pins.ModelPinMismatch):
        lw_upscale.upscale_spandrel("/definitely/not/a/real/source.png", weight)


def test_upscale_refusal_clears_when_the_weight_is_corrected(tmp_path, monkeypatch):
    """Appears is not goes-away, at the wiring level too."""
    weight = _drifted_weight(tmp_path, monkeypatch, BAD_SAME_SIZE)
    with pytest.raises(lw_model_pins.ModelPinMismatch):
        lw_upscale.upscale_spandrel(str(tmp_path / "no_such_source.png"), weight)

    open(weight, "wb").write(GOOD)
    # The pin now passes, so the call proceeds and fails on something else
    # (no torch in CI, or no source image). Anything BUT ModelPinMismatch.
    with pytest.raises(Exception) as exc:  # noqa: B017 - the type is the assertion
        lw_upscale.upscale_spandrel(str(tmp_path / "no_such_source.png"), weight)
    assert not isinstance(exc.value, lw_model_pins.ModelPinMismatch)


def test_upscale_escape_hatch_lets_a_deliberate_swap_through(tmp_path, monkeypatch):
    weight = _drifted_weight(tmp_path, monkeypatch, BAD_SAME_SIZE)
    monkeypatch.setenv(lw_model_pins.OVERRIDE_ENV, "1")
    with pytest.raises(Exception) as exc:  # noqa: B017 - the type is the assertion
        lw_upscale.upscale_spandrel(str(tmp_path / "no_such_source.png"), weight)
    assert not isinstance(exc.value, lw_model_pins.ModelPinMismatch)


def test_upscale_does_not_refuse_an_unpinned_model(tmp_path, monkeypatch):
    """The V1 DAT2 fallback is unpinned today; it must still run."""
    pins_file = _manifest(tmp_path, "w.safetensors", GOOD)
    other = tmp_path / "some_other_model.pth"
    other.write_bytes(b"unpinned bytes")
    monkeypatch.setenv(lw_model_pins.PINS_ENV, str(pins_file))

    with pytest.raises(Exception) as exc:  # noqa: B017 - the type is the assertion
        lw_upscale.upscale_spandrel(str(tmp_path / "no_such_source.png"), str(other))
    assert not isinstance(exc.value, lw_model_pins.ModelPinMismatch)
