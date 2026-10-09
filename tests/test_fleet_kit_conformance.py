"""FLEET-KIT conformance: MAIN's vendored kit and the embedded FLEET-COMMON block.

MAIN 0955 section 2 step 2 (kit v3 MAIN 1016, kit v4 MAIN 1204, kit v6 MAIN 2237,
kit v7 MAIN 0215, kit v8 MAIN 0310, kit v9 MAIN 2354, kit v10 MAIN 0839, kit v11 MAIN 1840,
kit v12 MAIN 2031): every tree runs
`assert fleet_headless.conformance(<repo root>) == []` on every run of its suite,
so a local edit to a vendored kit file under ops/fleet_kit/, or to the
FLEET-COMMON block between the markers in CLAUDE.md, fails CI here.

Hermetic: the kit is pure stdlib and reads only tracked bytes under the repo
root; nothing here touches the registry, the network or a machine path, so the
same assertion holds on the Linux CI runner.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KIT = ROOT / "ops" / "fleet_kit" / "fleet_headless.py"


def _kit():
    spec = importlib.util.spec_from_file_location("fleet_headless", KIT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_fleet_kit_conformance():
    assert _kit().conformance(ROOT) == []


def test_fleet_kit_version_is_the_one_main_shipped():
    """v12 per MAIN 2031 (v11 MAIN 1840); a new version lands only as a MAIN FLEET-KIT-vN note."""
    assert _kit().KIT_VERSION == 12
