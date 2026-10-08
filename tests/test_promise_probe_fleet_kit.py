"""The fleet-kit promise probe fires only on a kit NEWER than the vendored one.

ops/promises.json `fleet-kit` runs `lw_promise_probes.py fleet_kit_moved`. The
inbox keeps every older FLEET-KIT note (v2..v7) forever, so a probe that fires
on "any version other than mine" fires on the history and never clears.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _probes():
    spec = importlib.util.spec_from_file_location(
        "lw_promise_probes_under_test", ROOT / "tools" / "lw_promise_probes.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _tree(tmp_path, version, notes):
    kit = tmp_path / "ops" / "fleet_kit"
    kit.mkdir(parents=True)
    (kit / "MANIFEST.json").write_text(json.dumps({"version": version}), encoding="utf-8")
    inbox = tmp_path / "moon_sync_inbox"
    inbox.mkdir()
    for i, text in enumerate(notes):
        (inbox / f"n{i}.md").write_text(text, encoding="utf-8")
    return tmp_path


def test_the_probe_pins_the_vendored_version():
    pp = _probes()
    man = json.loads((ROOT / "ops" / "fleet_kit" / "MANIFEST.json").read_text(encoding="utf-8"))
    assert pp.FLEET_KIT_VERSION == man["version"] == 9


def test_older_kit_notes_in_the_inbox_do_not_fire(tmp_path, monkeypatch):
    pp = _probes()
    monkeypatch.setattr(pp, "ROOT", _tree(tmp_path, pp.FLEET_KIT_VERSION, [
        "FLEET-KIT-v4 order", "FLEET-KIT-v5 plan", "FLEET-KIT-v6 lanes", "FLEET-KIT-v7 checklist", "FLEET-KIT-v8 now"]))
    assert pp.fleet_kit_moved() is False


def test_a_newer_kit_note_fires_and_clears_once_vendored(tmp_path, monkeypatch):
    pp = _probes()
    newer = pp.FLEET_KIT_VERSION + 1
    root = _tree(tmp_path, pp.FLEET_KIT_VERSION, [f"ORDER FLEET-KIT-v{newer} ships"])
    monkeypatch.setattr(pp, "ROOT", root)
    assert pp.fleet_kit_moved() is True
    # Two-digit versions are newer too.
    (root / "moon_sync_inbox" / "n0.md").write_text("FLEET-KIT-v12", encoding="utf-8")
    assert pp.fleet_kit_moved() is True
    # Clears: the note is gone (or vendored and the pin moved) - no fire.
    (root / "moon_sync_inbox" / "n0.md").write_text("FLEET-KIT-v3", encoding="utf-8")
    assert pp.fleet_kit_moved() is False


def test_a_moved_manifest_fires(tmp_path, monkeypatch):
    pp = _probes()
    monkeypatch.setattr(pp, "ROOT", _tree(tmp_path, pp.FLEET_KIT_VERSION + 1, []))
    assert pp.fleet_kit_moved() is True
