"""Calibration profiles as data with evidence (directive P2-7).

Numbers that depend on the machine (GPU tile sizes, VRAM headroom) live in
config/profiles/*.json, matched by environment properties, and EVERY value
carries an evidence string saying when and how it was measured. A value
without evidence fails here; a profile that matches nothing falls back to the
code default and says so.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

import lw_profiles as P  # noqa: E402


def _write(tmp_path, name, data):
    d = tmp_path / "profiles"
    d.mkdir(exist_ok=True)
    (d / name).write_text(json.dumps(data), encoding="ascii")
    return d


GOOD = {"kind": "gpu", "name": "rtx5070-12g",
        "match": {"gpu_name_contains": "RTX 5070", "vram_mib_min": 11000},
        "values": {"upscale_tile": {"value": 512, "evidence": "measured 2026-10-04: peak 3.1 GB"}},
        "procedure": "python tools/lw_profiles.py calibrate-gpu"}


def test_every_tracked_profile_value_carries_evidence():
    profiles = P.load_all(P.PROFILES_DIR)
    assert profiles, "no tracked profiles - the evidence rule would pass vacuously"
    for prof in profiles:
        assert prof.get("procedure"), prof["name"]
        for key, v in prof["values"].items():
            assert str(v.get("evidence", "")).strip(), f"{prof['name']}.{key} has no evidence"
            assert "value" in v


def test_value_without_evidence_is_refused(tmp_path):
    bad = json.loads(json.dumps(GOOD))
    bad["values"]["upscale_tile"]["evidence"] = ""
    d = _write(tmp_path, "bad.json", bad)
    with pytest.raises(P.ProfileError):
        P.load_all(d)


def test_match_picks_the_profile_for_this_environment(tmp_path):
    d = _write(tmp_path, "a.json", GOOD)
    env = {"gpu_name": "NVIDIA GeForce RTX 5070", "vram_mib": 12227}
    v, src = P.value("gpu", "upscale_tile", default=256, env=env, profiles_dir=d)
    assert v == 512 and src == "rtx5070-12g"


def test_no_match_falls_back_to_the_default_and_says_so(tmp_path):
    d = _write(tmp_path, "a.json", GOOD)
    env = {"gpu_name": "NVIDIA GeForce RTX 3060", "vram_mib": 12288}
    v, src = P.value("gpu", "upscale_tile", default=256, env=env, profiles_dir=d)
    assert v == 256 and src == "default"


def test_unknown_environment_never_matches(tmp_path):
    d = _write(tmp_path, "a.json", GOOD)
    v, src = P.value("gpu", "upscale_tile", default=256, env={}, profiles_dir=d)
    assert src == "default"


def test_unknown_match_key_is_refused(tmp_path):
    bad = json.loads(json.dumps(GOOD))
    bad["match"]["moon_phase"] = "full"
    d = _write(tmp_path, "bad.json", bad)
    with pytest.raises(P.ProfileError):
        P.load_all(d)


def test_tracked_gpu_profile_agrees_with_the_code_default():
    """The profile RECORDS the calibrated current value; changing the tile
    changes output bytes and needs a golden regress first, so the profile and
    the code default must agree until that happens."""
    import lw_upscale
    prof = next(p for p in P.load_all(P.PROFILES_DIR) if p["kind"] == "gpu")
    assert prof["values"]["upscale_tile"]["value"] == lw_upscale.DEFAULT_TILE
    assert prof["values"]["upscale_overlap"]["value"] == lw_upscale.DEFAULT_OVERLAP


def test_environment_probe_never_raises(monkeypatch):
    def boom(*a, **k):
        raise OSError("no nvidia-smi")
    monkeypatch.setattr(P.subprocess, "run", boom)
    P._ENV_CACHE.clear()
    assert P.environment() == {}
    P._ENV_CACHE.clear()


def test_a_catch_all_profile_still_never_matches_an_unprobed_machine(tmp_path):
    anyp = json.loads(json.dumps(GOOD))
    anyp["match"] = {}
    d = _write(tmp_path, "any.json", anyp)
    assert P.value("gpu", "upscale_tile", default=256, env={}, profiles_dir=d) == (256, "default")
    assert P.value("gpu", "upscale_tile", default=256, env={"gpu_name": "x", "vram_mib": 1},
                   profiles_dir=d) == (512, "rtx5070-12g")
