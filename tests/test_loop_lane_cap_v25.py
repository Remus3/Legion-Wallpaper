"""FLEET-KIT v25 LANE-CAP guard (MAIN ORDER 2026-10-27-2136, section 5 items 2-4).

The loop controller's per-tree lane cap and its executor slot count follow the
machine config (fleet_lanes.load_config(), FLEET_LANES_CONFIG / ~/.fleet/
lanes.json) instead of a hard-coded 3, and the driver checks
fleet_lanes.should_yield("LW") at each cycle boundary - ending the lane after
its current cycle, never killing or terminating a worker.

Hermetic: the controller is imported against a throwaway config under tmp, and
the machine config is a tmp file named by FLEET_LANES_CONFIG (missing file =
the kit defaults, width 3 / cap 3).
"""
from __future__ import annotations

import ast
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
CONTROLLER = ROOT / "ops" / "loop" / "loop_controller.py"
CONFIGS = sorted((ROOT / "ops" / "loop").glob("config*.json"))
PROD_CFG = json.loads((ROOT / "ops" / "loop" / "config.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def lc(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("lc_v25")
    cfgp = tmp / "cfg.json"
    cfgp.write_text(json.dumps({
        "repo_root": str(tmp), "control_dir": str(tmp / "control"),
        "cycle_deadline_sec": 5400, "ceiling_usd": 1.0, "max_cycles": 1,
    }), encoding="utf-8")
    argv = sys.argv
    sys.argv = [str(CONTROLLER), str(cfgp)]
    try:
        spec = importlib.util.spec_from_file_location("lw_loop_controller_v25", CONTROLLER)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = mod
        spec.loader.exec_module(mod)
    finally:
        sys.argv = argv
    return mod


def _machine(monkeypatch, tmp_path, doc=None):
    p = tmp_path / "lanes.json"
    if doc is not None:
        p.write_text(json.dumps(doc), encoding="ascii", newline="\n")
    monkeypatch.setenv("FLEET_LANES_CONFIG", str(p))
    return p


def test_the_cap_and_slot_count_read_the_machine_config_not_a_hard_coded_three(
        lc, monkeypatch, tmp_path):
    _machine(monkeypatch, tmp_path, {"governor_width": 5, "lane_cap_max": 5})
    assert lc.lane_settings(PROD_CFG)[1] == 5
    assert lc.executor_slot_count(PROD_CFG) == 5
    assert lc.lane_cap_request(PROD_CFG) is None  # run_lane(cap=None) = live cap


def test_with_the_machine_config_missing_both_read_the_kit_default_three(
        lc, monkeypatch, tmp_path):
    _machine(monkeypatch, tmp_path)  # named file does not exist
    assert lc.lane_settings(PROD_CFG)[1] == 3
    assert lc.executor_slot_count(PROD_CFG) == 3


def test_a_tree_value_below_the_machine_keeps_and_above_clamps(lc, monkeypatch, tmp_path):
    _machine(monkeypatch, tmp_path, {"governor_width": 5, "lane_cap_max": 5})
    assert lc.lane_settings({"lane_cap": 2})[1] == 2
    assert lc.executor_slot_count({"max_concurrent_lanes": 2}) == 2
    assert lc.lane_settings({"lane_cap": 9})[1] == 5
    assert lc.executor_slot_count({"max_concurrent_lanes": 9}) == 5


def test_no_loop_config_or_controller_default_pins_three(lc):
    for cfg in CONFIGS:
        data = json.loads(cfg.read_text(encoding="utf-8"))
        assert "max_concurrent_lanes" not in data, cfg.name
        assert data.get("lane_cap") is None, cfg.name
    src = CONTROLLER.read_text(encoding="utf-8")
    assert 'CFG.get("max_concurrent_lanes", 3)' not in src
    assert "held_slot(executor_slot_count(CFG)" in src


def test_should_yield_true_ends_the_lane_and_never_kills_a_worker(lc, monkeypatch):
    calls = []

    def boom(*a, **k):
        calls.append(a)
        raise AssertionError("a worker was signalled")

    monkeypatch.setattr(os, "kill", boom)
    monkeypatch.setattr(subprocess.Popen, "kill", boom)
    monkeypatch.setattr(subprocess.Popen, "terminate", boom)
    monkeypatch.setattr(subprocess.Popen, "send_signal", boom)
    seen = []

    def yes(code, root=None):
        seen.append((code, root))
        return True

    assert lc.cycle_boundary_yield(2, should_yield=yes) is True
    assert seen == [("LW", lc.headless_env.governor_root())]
    assert lc.cycle_boundary_yield(1, should_yield=yes) is False  # no cycle ran yet
    assert lc.cycle_boundary_yield(3, should_yield=lambda c, root=None: False) is False

    def broken(code, root=None):
        raise OSError("unreadable governor")

    assert lc.cycle_boundary_yield(3, should_yield=broken) is False  # advisory
    assert calls == []


def test_the_driver_checks_should_yield_each_cycle_and_only_returns(lc):
    tree = ast.parse(CONTROLLER.read_text(encoding="utf-8"))
    run = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "_run_lane")
    loop = next(n for n in ast.walk(run) if isinstance(n, ast.For))
    branch = next(n for n in loop.body if isinstance(n, ast.If)
                  and "cycle_boundary_yield" in ast.unparse(n.test))
    body = "\n".join(ast.unparse(s) for s in branch.body)
    assert isinstance(branch.body[-1], ast.Return), body
    called = [ast.unparse(c.func).lower() for s in branch.body for c in ast.walk(s)
              if isinstance(c, ast.Call)]
    for word in ("kill", "terminate", "send_signal", "exit", "stop"):
        assert not any(word in f for f in called), called
    assert all(isinstance(s, (ast.Expr, ast.Return)) for s in branch.body), body
    # the executor slot is recorded under the tree CODE, so should_yield counts it
    src = ast.unparse(run)
    assert "repo=LANE_CODE" in src
