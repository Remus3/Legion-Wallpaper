"""FLEET-KIT v6 lanes on the loop controller (MAIN 2237 sections 3 + 4a).

The per-repo single-controller guard (control/RUNNING.lock, one run per repo)
is lifted onto the kit's fleet_lanes: up to 3 lanes per repo, each in its OWN
git worktree (<parent>/lw-worktrees/lane-<i>), each with its own control dir,
and the controller's slots.hold(3) around the executor call stays that lane's
ONE governor slot. An old-layout RUNNING.lock that names a live controller
still refuses a start - the two lock layouts must never run side by side.

Hermetic: every arm builds its own throwaway git repo under tmp_path and points
the controller at it (repo_root + control_dir), so no lane lock, worktree or
control file is ever written in a real checkout.
"""
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def _git(cwd: Path, *args: str) -> str:
    env = {k: v for k, v in os.environ.items() if not k.upper().startswith("GIT_")}
    r = subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True,
                       timeout=60, env=env, creationflags=NO_WINDOW)
    assert r.returncode == 0, r.stderr
    return r.stdout.strip()


def tmp_repo(tmp_path: Path) -> Path:
    """A one-commit git repo at tmp_path/repo - the fake LW main tree."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "lanes@example.invalid")
    _git(repo, "config", "user.name", "lanes")
    _git(repo, "config", "core.autocrlf", "false")
    (repo / "README.txt").write_text("lane test\n", encoding="ascii", newline="\n")
    _git(repo, "add", "README.txt")
    _git(repo, "commit", "-q", "-m", "init")
    return repo


def _lc():
    spec = importlib.util.spec_from_file_location(
        "lw_loop_controller_lanes_under_test", ROOT / "ops" / "loop" / "loop_controller.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


lc = _lc()
lanes = lc.fleet_lanes


def _cfg(tmp_path: Path, repo: Path, **extra) -> Path:
    ctl = tmp_path / "control"
    ctl.mkdir(exist_ok=True)
    cfg = json.loads((ROOT / "ops" / "loop" / "config.dry.json").read_text(encoding="utf-8"))
    cfg.update({"repo_root": str(repo), "control_dir": str(ctl), "max_cycles": 1,
                "cycle_deadline_sec": 3, "poll_sec": 1, "fixed_directive": "noop",
                "session_jsonl": ""})
    cfg.update(extra)
    p = tmp_path / "cfg.json"
    p.write_text(json.dumps(cfg), encoding="utf-8")
    return p


def _launch(cfgp: Path) -> subprocess.Popen:
    return subprocess.Popen(
        [sys.executable, str(ROOT / "ops" / "loop" / "loop_controller.py"), str(cfgp)],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
        creationflags=NO_WINDOW)


def _wait_for(path: Path, proc: subprocess.Popen, tries: int = 300) -> bool:
    for _ in range(tries):
        if path.is_file():
            return True
        if proc.poll() is not None:
            return False
        time.sleep(0.1)
    return False


# ---- the binding --------------------------------------------------------------

def test_the_lane_module_is_the_vendored_kit_and_shared_with_fleet_headless():
    assert Path(lanes.__file__).resolve() == (ROOT / "ops" / "fleet_kit" /
                                              "fleet_lanes.py").resolve()
    # fleet_headless._lanes() binds the same file under the same name, so
    # spawn(governor=...) and this controller share ONE module object.
    assert sys.modules[f"fleet_kit_lanes_v{lc.headless_env.kit.KIT_VERSION}"] is lanes


def test_lane_settings_default_to_the_kit_cap_of_three():
    name, cap = lc.lane_settings({})
    assert (name, cap) == ("loop", 3)
    assert lc.lane_settings({"lane": "refs", "lane_cap": 2}) == ("refs", 2)


@pytest.mark.parametrize("bad", [0, 4, "x"])
def test_lane_settings_refuse_a_cap_outside_the_kit_range(bad):
    with pytest.raises(ValueError):
        lc.lane_settings({"lane_cap": bad})


@pytest.mark.parametrize("bad", ["", "../up", "a b", "x" * 65])
def test_lane_settings_refuse_a_name_that_is_not_a_safe_directory_name(bad):
    with pytest.raises(ValueError):
        lc.lane_settings({"lane": bad})


def test_the_production_config_declares_cap_three():
    cfg = json.loads((ROOT / "ops" / "loop" / "config.json").read_text(encoding="utf-8"))
    assert lc.lane_settings(cfg)[1] == 3


def test_each_lane_gets_its_own_control_dir_by_name(tmp_path: Path):
    a = lc.lane_control_dir(tmp_path, "loop")
    b = lc.lane_control_dir(tmp_path, "refs")
    assert a != b
    assert a.parent == b.parent == tmp_path / "lane-runs"


def test_the_executor_runs_in_the_lane_worktree_not_the_main_tree(tmp_path: Path):
    cfg = {"repo_root": "C:\\main", "channel": "sdk"}
    out = lc.lane_cfg(cfg, {"worktree": str(tmp_path / "lw-worktrees" / "lane-1")})
    assert out["repo_root"] == str(tmp_path / "lw-worktrees" / "lane-1")
    assert cfg["repo_root"] == "C:\\main", "the caller's config must not be mutated"


# ---- the old layout must never coexist with a v6 lane -----------------------------

def test_a_live_old_layout_lock_inside_the_window_is_live(tmp_path: Path):
    (tmp_path / "RUNNING.lock").write_text(
        json.dumps({"pid": os.getpid(), "run_id": "held", "ts": time.time()}),
        encoding="utf-8")
    assert lc.old_layout_holder(tmp_path, me=os.getpid() + 1) is not None


def test_a_dead_or_expired_old_layout_lock_is_not_live(tmp_path: Path):
    lock = tmp_path / "RUNNING.lock"
    lock.write_text(json.dumps({"pid": 999999999, "ts": time.time()}), encoding="utf-8")
    assert lc.old_layout_holder(tmp_path, me=os.getpid()) is None
    lock.write_text(json.dumps({"pid": os.getpid(),
                                "ts": time.time() - 4 * lc.slots.DEFAULT_STALE_AFTER}),
                    encoding="utf-8")
    assert lc.old_layout_holder(tmp_path, me=os.getpid() + 1) is None
    assert lock.exists(), "an old-layout lock is read, never deleted"


def test_no_old_layout_lock_is_not_live(tmp_path: Path):
    assert lc.old_layout_holder(tmp_path, me=os.getpid()) is None


# ---- end to end: the controller claims a lane + a worktree, hermetically --------

def test_a_run_claims_lane_zero_and_its_own_worktree(tmp_path: Path):
    repo = tmp_repo(tmp_path)
    proc = _launch(_cfg(tmp_path, repo))
    try:
        ready = tmp_path / "control" / "lane-runs" / "loop" / "run_id.txt"
        assert _wait_for(ready, proc), "the controller never reached its lane"
        rec = json.loads((repo / "ops" / "loop" / "control" / "lanes" / "0.lock")
                         .read_text(encoding="utf-8"))
        assert rec["pid"] == proc.pid
        assert rec["lane"] == "loop" and rec["repo"] == "LW" and rec["index"] == 0
        wt = tmp_path / "lw-worktrees" / "lane-0"
        assert Path(rec["worktree"]) == wt
        assert (wt / ".git").is_file(), "lane 0 must be a linked git worktree"
        assert (wt / "README.txt").is_file()
        assert not (tmp_path / "control" / "RUNNING.lock").exists(), \
            "the v6 layout writes no old-layout lock"
    finally:
        proc.kill()
        proc.wait(timeout=30)


def test_a_second_lane_with_another_name_runs_beside_the_first(tmp_path: Path):
    repo = tmp_repo(tmp_path)
    # Lane 0 held by THIS (live) process under the name "loop".
    held = lanes.try_acquire_lane(repo, "LW", "loop", "held", 3)
    assert held["ok"] and held["index"] == 0
    try:
        proc = _launch(_cfg(tmp_path, repo, lane="refs"))
        try:
            ready = tmp_path / "control" / "lane-runs" / "refs" / "run_id.txt"
            assert _wait_for(ready, proc), "a second lane must be allowed under cap 3"
            rec = json.loads((repo / "ops" / "loop" / "control" / "lanes" / "1.lock")
                             .read_text(encoding="utf-8"))
            assert rec["pid"] == proc.pid and rec["lane"] == "refs"
            assert (tmp_path / "lw-worktrees" / "lane-1" / ".git").is_file()
        finally:
            proc.kill()
            proc.wait(timeout=30)
    finally:
        lanes.release_lane(held)


def test_a_lane_name_already_running_is_refused(tmp_path: Path):
    repo = tmp_repo(tmp_path)
    held = lanes.try_acquire_lane(repo, "LW", "loop", "held", 3)
    try:
        r = subprocess.run([sys.executable, str(ROOT / "ops" / "loop" / "loop_controller.py"),
                            str(_cfg(tmp_path, repo))], capture_output=True, text=True,
                           timeout=120, creationflags=NO_WINDOW)
        assert r.returncode == 2
        assert "lane_held" in (r.stderr + r.stdout)
        assert not (tmp_path / "lw-worktrees").exists(), "a refusal creates no worktree"
    finally:
        lanes.release_lane(held)


def test_a_full_repo_is_refused_at_the_configured_cap(tmp_path: Path):
    repo = tmp_repo(tmp_path)
    held = lanes.try_acquire_lane(repo, "LW", "other", "held", 1)
    try:
        r = subprocess.run([sys.executable, str(ROOT / "ops" / "loop" / "loop_controller.py"),
                            str(_cfg(tmp_path, repo, lane_cap=1))], capture_output=True,
                           text=True, timeout=120, creationflags=NO_WINDOW)
        assert r.returncode == 2
        assert "lanes_full" in (r.stderr + r.stdout)
    finally:
        lanes.release_lane(held)


def test_a_live_old_layout_lock_refuses_the_v6_start(tmp_path: Path):
    repo = tmp_repo(tmp_path)
    cfgp = _cfg(tmp_path, repo)
    (tmp_path / "control" / "RUNNING.lock").write_text(
        json.dumps({"pid": os.getpid(), "run_id": "old", "ts": time.time()}),
        encoding="utf-8")
    r = subprocess.run([sys.executable, str(ROOT / "ops" / "loop" / "loop_controller.py"),
                        str(cfgp)], capture_output=True, text=True, timeout=120,
                       creationflags=NO_WINDOW)
    assert r.returncode == 2
    assert "already running" in (r.stderr + r.stdout)
    assert not (repo / "ops" / "loop" / "control" / "lanes" / "0.lock").exists(), \
        "an old-layout lock and a v6 lane lock must never coexist"


def test_the_lane_is_released_when_the_run_ends(tmp_path: Path):
    """max_cycles 0: the run claims, runs no cycle, stops - and frees the lane."""
    repo = tmp_repo(tmp_path)
    r = subprocess.run([sys.executable, str(ROOT / "ops" / "loop" / "loop_controller.py"),
                        str(_cfg(tmp_path, repo, max_cycles=0))], capture_output=True,
                       text=True, timeout=120, creationflags=NO_WINDOW)
    assert r.returncode == 0, r.stdout + r.stderr
    assert not (repo / "ops" / "loop" / "control" / "lanes" / "0.lock").exists()
    stop = tmp_path / "control" / "lane-runs" / "loop" / "STOP"
    assert stop.is_file(), "stop() writes the LANE's STOP, not the shared one"
    assert not (tmp_path / "control" / "STOP").exists()


# ---- one governor slot per executor call, taken at the call -----------------------

def test_the_executor_call_holds_exactly_one_slot_keyed_to_the_main_tree():
    import ast
    src = (ROOT / "ops" / "loop" / "loop_controller.py").read_text(encoding="utf-8")
    assert src.count("with held_slot(") == 1
    assert "repo=str(MAIN_ROOT)" in src, "the slot's repo key stays the main tree"
    governed = [n.lineno for n in ast.walk(ast.parse(src)) if isinstance(n, ast.Call)
                and any(k.arg == "governor" for k in n.keywords)]
    assert governed == [], "never both slots.hold and spawn(governor=...)"


# ---- FLEET-KIT v7 item 13 d: every loop fire writes its checklist ---------------

def test_the_checklist_module_is_lws_binding_of_the_kit():
    assert Path(lc.lw_checklist.__file__).resolve() == (ROOT / "tools" /
                                                        "lw_checklist.py").resolve()


def test_a_cycle_fire_writes_lane_i_progress_in_the_main_checkout(tmp_path, monkeypatch):
    monkeypatch.setattr(lc, "MAIN_ROOT", tmp_path / "main")
    monkeypatch.setattr(lc, "LANE_INDEX", 2)
    logged = []
    monkeypatch.setattr(lc, "log", logged.append)
    fire = lc.cycle_fire(5)
    fire.start()
    doc = json.loads((tmp_path / "main" / "ops" / "loop" / "control" / "progress" /
                      "lane-2.json").read_text(encoding="utf-8"))
    assert doc["task"] == "lane-2" and doc["status"] == "running"
    assert [r["id"] for r in doc["checklist"]] == [i for i, _t in lc.CYCLE_ITEMS]
    assert logged[0].splitlines()[0] == "Session 5 checklist"


def test_a_run_writes_its_lane_checklist_in_the_main_tree_not_the_worktree(tmp_path: Path):
    repo = tmp_repo(tmp_path)
    proc = _launch(_cfg(tmp_path, repo))
    try:
        prog = repo / "ops" / "loop" / "control" / "progress" / "lane-0.json"
        assert _wait_for(prog, proc), "the cycle fire never wrote progress/lane-0.json"
        doc = json.loads(prog.read_text(encoding="utf-8"))
        assert doc["task"] == "lane-0"
        assert isinstance(doc["checklist"], list)
        wt_prog = tmp_path / "lw-worktrees" / "lane-0" / "ops" / "loop" / "control" / \
            "progress" / "lane-0.json"
        assert not wt_prog.exists(), "never inside the lane worktree"
    finally:
        proc.kill()
        proc.wait(timeout=30)
