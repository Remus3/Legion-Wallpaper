"""LW adapter for the fleet kit v12 race guards (FLEET-COMMON 16, MAIN 2031).

One place LW's own callers get the kit's git lock and suite gate from:

  * git_lock(dir, owner, verb) - fleet_gitlock.git_lock, for Python callers
    that commit or push (tools/ci_watchdog.py's branch push);
  * gate_argv(argv, owner) / gate_shell(cmd, owner) - wrap a WHOLE-suite
    command in `fleet_suite_gate.py run --owner <owner> -- ...` (done_gate,
    pytest_guard, lw_false_red_probe, truth_gate);
  * owner(tag) - env FLEET_CLAIM_OWNER when a hook-aware caller set it, else
    `lw-<tag>-<pid>` (a script is its own claim owner);
  * ENV_ROOTS - every env var LW code reads to locate a runtime root, declared
    to fleet_test_guard.install() in tests/conftest.py.

Re-entry: the gate exports FLEET_SUITE_SLOT to the suite it runs. A caller
that finds it set is already inside a held slot (a test driving done_gate, a
suite run by a gated script), so gate_* return the command unwrapped - on the
default 1-slot machine a nested gate would wait on its own parent until it
failed closed.

The kit files are loaded by path under the kit's own sibling keys
(fleet_kit_<name>), so this module and the kit share ONE module object.
"""
from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KIT = ROOT / "ops" / "fleet_kit"
GATE = KIT / "fleet_suite_gate.py"
GITLOCK = KIT / "fleet_gitlock.py"
SLOT_ENV = "FLEET_SUITE_SLOT"
OWNER_ENV = "FLEET_CLAIM_OWNER"

# One sentence every headless child LW spawns carries (inbox responder child,
# loop executor sdk prompt): the claims hook denies a bare commit / push /
# whole suite anyway; saying it up front saves the child a denied turn.
CHILD_RULE = (
    "RACE GUARDS (FLEET-COMMON 16): run every git commit and git push as "
    "`python ops/fleet_kit/fleet_gitlock.py run --owner <id> -- git ...` and every "
    "WHOLE test suite as `python ops/fleet_kit/fleet_suite_gate.py run --owner <id> "
    "-- python -m pytest tests -q`; <id> is your claims-hook owner id (a denial "
    "names it).")

# {env var: subpath under the test's tmp_path}. Same subpaths as the older
# per-var fixtures in tests/conftest.py, so fixture order never matters.
ENV_ROOTS = {
    "LW_OPS_TASKS_ROOT": "operator_tasks",
    "LW_RUNLOG_ROOT": "runlog",
    "LW_GOVERNOR_ROOT": "governor/slots",
    "LW_BRIDGE_JOURNAL": "bridge/sends.jsonl",
    "LW_CLAIMED_GREEN_REPORT_DIR": "claimed_green",
}


def _kit_module(name: str):
    key = "fleet_kit_" + name
    if key in sys.modules:
        return sys.modules[key]
    spec = importlib.util.spec_from_file_location(key, KIT / (name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[key] = mod
    spec.loader.exec_module(mod)
    return mod


def gitlock_module():
    return _kit_module("fleet_gitlock")


git_lock = gitlock_module().git_lock


def owner(tag: str, env: dict | None = None) -> str:
    env = os.environ if env is None else env
    return env.get(OWNER_ENV) or f"lw-{tag}-{os.getpid()}"


def _inside_slot(env: dict | None) -> bool:
    env = os.environ if env is None else env
    return bool((env.get(SLOT_ENV) or "").strip())


def gate_argv(argv: list[str], owner_id: str, env: dict | None = None,
              timeout: float | None = None) -> list[str]:
    """argv run through the suite gate, or argv itself inside a held slot."""
    if _inside_slot(env):
        return list(argv)
    opts = ["--owner", owner_id]
    if timeout is not None:
        opts += ["--timeout", str(int(timeout))]
    return [sys.executable, str(GATE), "run", *opts, "--", *argv]


def gate_shell(cmd: str, owner_id: str, env: dict | None = None) -> str:
    """Shell-string form of gate_argv, for a caller that runs a command string
    through the shell (tools/truth_gate.py's claim-named suite_cmd)."""
    if _inside_slot(env):
        return cmd
    return subprocess.list2cmdline([sys.executable, str(GATE), "run",
                                    "--owner", owner_id, "--"]) + " " + cmd
