"""TRIPWIRE: the fleet_watch swap is DEFERRED until the kit can carry LW's watch.

MAIN's v6 order 4b asked LW to swap tools/lw_watch.py for the kit's
fleet_watch.py; the v7 order keeps LW's five watcher extensions on MAIN's record
(not in v7). ADJUDICATED 2026-10-05 (LEDGER 273): defer. A straight swap would
re-spawn an hour-long code-writing responder run whenever a tick mixes an AUTO
and an UNAVAILABLE note (kit delivery is all-or-nothing), swallow the CI
watchdog's first red sha (the kit always baselines), write state on dry runs,
and raise WatchStateCorrupt on both live state files.

This test is GREEN while the vendored kit lacks the extensions, and goes RED the
day a kit fleet_watch.run_source gains them - the signal to re-open the swap
(migrate the two state files, read each caller back live, delete lw_watch.py).
"""
from __future__ import annotations

import importlib.util
import inspect
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXTENSIONS = ("baseline", "persist", "prune", "confirm_arg")


def _kit_watch():
    spec = importlib.util.spec_from_file_location(
        "fleet_watch_tripwire", ROOT / "ops" / "fleet_kit" / "fleet_watch.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_lw_still_carries_its_own_watcher_with_the_extensions():
    lw = (ROOT / "tools" / "lw_watch.py").read_text(encoding="utf-8")
    for name in EXTENSIONS:
        assert f"{name}:" in lw or f"{name}=" in lw, name


def test_the_kit_watcher_still_lacks_the_extensions_else_reopen_the_swap():
    params = inspect.signature(_kit_watch().run_source).parameters
    gained = [n for n in EXTENSIONS if n in params]
    assert gained == [], (
        f"kit fleet_watch.run_source gained {gained}: re-open the deferred swap "
        f"(LEDGER 273) - migrate the responder and CI-watchdog state files, read "
        f"each caller back live, then retire tools/lw_watch.py")
