"""FLEET-KIT v12 race guards (MAIN 2031 ORDER section 3; FLEET-COMMON 16).

conformance() pins the vendored bytes; it does not see how LW WIRES them.
These arms do:
  * the tracked .claude/settings.json runs fleet_claims.py `hook` (PreToolUse,
    the ordered matcher) and `release-hook` (SubagentStop), each EXACTLY the
    anchored command MAIN ordered, timeout 10, interpreter `python` (a deny is
    a JSON decision on stdout; pythonw discards stdout);
  * the claims / lock runtime files are gitignored by an explicit line;
  * tests/conftest.py installs fleet_test_guard with LW's runtime-root env vars;
  * LW's own commit / push / whole-suite callers go through the gitlock and
    the suite gate (tools/lw_race_guards.py), re-entry inside a held slot runs
    direct (a nested gate on a 1-slot machine would wait on itself);
  * /done names both helpers.

Hermetic: tracked bytes and pure functions; nothing takes a real slot or lock.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import lw_race_guards as rg  # noqa: E402

SETTINGS = ROOT / ".claude" / "settings.json"
CLAIMS_HOOK = 'python "$CLAUDE_PROJECT_DIR/ops/fleet_kit/fleet_claims.py" hook'
RELEASE_HOOK = 'python "$CLAUDE_PROJECT_DIR/ops/fleet_kit/fleet_claims.py" release-hook'
MATCHER = "Edit|Write|NotebookEdit|MultiEdit|Bash|PowerShell"
_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0) if sys.platform == "win32" else 0


def _hooks(event):
    entries = json.loads(SETTINGS.read_text(encoding="utf-8"))["hooks"].get(event, [])
    return [(e.get("matcher"), h) for e in entries for h in e["hooks"]
            if "fleet_claims.py" in h["command"]]


def test_claims_pretooluse_hook_is_wired_once_exactly():
    hits = _hooks("PreToolUse")
    assert len(hits) == 1, hits
    matcher, hook = hits[0]
    assert matcher == MATCHER
    assert hook["timeout"] == 10
    assert hook["command"] in (CLAIMS_HOOK, CLAIMS_HOOK + " || true"), hook["command"]


def test_claims_release_hook_is_wired_on_subagentstop_exactly():
    hits = _hooks("SubagentStop")
    assert len(hits) == 1, hits
    _, hook = hits[0]
    assert hook["timeout"] == 10
    assert hook["command"] in (RELEASE_HOOK, RELEASE_HOOK + " || true"), hook["command"]


def test_subagent_first_entry_is_kept():
    pre = json.loads(SETTINGS.read_text(encoding="utf-8"))["hooks"]["PreToolUse"]
    assert any("fleet_subagent_first.py" in h["command"] for e in pre for h in e["hooks"])


def test_race_guard_runtime_files_are_gitignored_by_an_explicit_line():
    lines = (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
    for rel in ("ops/loop/control/claims/", "ops/loop/control/locks/",
                "ops/loop/control/claims.jsonl", "ops/loop/control/claims.mode",
                "ops/loop/control/gitlock.jsonl"):
        assert rel in lines, rel
        probe = rel + "x.json" if rel.endswith("/") else rel
        r = subprocess.run(["git", "-C", str(ROOT), "check-ignore", "-v", "--no-index", probe],
                           capture_output=True, text=True, creationflags=_NO_WINDOW)
        pattern = r.stdout.split("\t")[0].split(":", 2)[-1] if r.stdout else ""
        assert r.returncode == 0 and pattern, f"{probe} is not gitignored: {r.stdout!r}"


def test_conftest_installs_the_test_guard_with_lw_runtime_roots():
    text = (ROOT / "tests" / "conftest.py").read_text(encoding="utf-8")
    assert "fleet_test_guard.install(" in text
    assert "env_roots=lw_race_guards.ENV_ROOTS" in text


def test_env_roots_cover_every_runtime_root_env_var_lw_reads():
    assert set(rg.ENV_ROOTS) >= {"LW_OPS_TASKS_ROOT", "LW_RUNLOG_ROOT", "LW_GOVERNOR_ROOT",
                                 "LW_BRIDGE_JOURNAL", "LW_CLAIMED_GREEN_REPORT_DIR"}


def test_gate_argv_wraps_the_suite_in_the_kit_gate_with_an_owner():
    cmd = [sys.executable, "-m", "pytest", "tests/", "-q"]
    out = rg.gate_argv(cmd, "lw-x", env={})
    assert out[1].replace("\\", "/").endswith("ops/fleet_kit/fleet_suite_gate.py")
    assert out[2:6] == ["run", "--owner", "lw-x", "--"]
    assert out[6:] == cmd


def test_gate_argv_runs_direct_inside_a_held_slot():
    cmd = [sys.executable, "-m", "pytest", "tests/", "-q"]
    assert rg.gate_argv(cmd, "lw-x", env={"FLEET_SUITE_SLOT": "0"}) == cmd


def test_gate_shell_prefixes_a_shell_command():
    out = rg.gate_shell('"py" -m pytest tests/ -q', "lw-x", env={})
    assert "fleet_suite_gate.py" in out and out.endswith('-- "py" -m pytest tests/ -q')
    assert rg.gate_shell("x", "lw-x", env={"FLEET_SUITE_SLOT": "1"}) == "x"


def test_owner_prefers_the_env_owner():
    assert rg.owner("done_gate", env={"FLEET_CLAIM_OWNER": "s.a"}) == "s.a"
    assert rg.owner("done_gate", env={}).startswith("lw-done_gate-")


def test_done_gate_suite_check_goes_through_the_gate():
    import done_gate
    suites = [c for c in done_gate.default_checks(env={}) if "pytest" in c]
    assert len(suites) == 1
    assert any(str(a).replace("\\", "/").endswith("fleet_suite_gate.py") for a in suites[0])


def test_pytest_guard_and_false_red_probe_route_the_suite_through_the_gate():
    for rel in ("tools/pytest_guard.py", "tools/lw_false_red_probe.py", "tools/truth_gate.py"):
        text = (ROOT / rel).read_text(encoding="utf-8")
        assert "lw_race_guards" in text and ("gate_argv(" in text or "gate_shell(" in text), rel


def test_ci_watchdog_push_runs_under_the_git_lock():
    text = (ROOT / "tools" / "ci_watchdog.py").read_text(encoding="utf-8")
    i = text.index('["git", "push", "-u", "origin", branch]')
    assert "git_lock(" in text[max(0, i - 300):i]


def test_git_lock_is_the_kit_context_manager():
    assert rg.git_lock is rg.gitlock_module().git_lock


def test_done_command_names_both_helpers():
    text = (ROOT / ".claude" / "commands" / "done.md").read_text(encoding="utf-8")
    assert "fleet_gitlock.py run --owner" in text
    assert "fleet_suite_gate.py run --owner" in text


def test_child_rule_names_both_helpers_with_the_owner_rule():
    assert "fleet_gitlock.py run --owner" in rg.CHILD_RULE
    assert "fleet_suite_gate.py run --owner" in rg.CHILD_RULE


def test_the_responder_child_prompt_carries_the_race_guard_rule():
    import lw_inbox_responder as responder
    prompt = responder.spawn_prompt(Path("moon_sync_inbox/x-from-MAIN-ORDER-y.md"))
    assert rg.CHILD_RULE in prompt


def test_the_loop_executor_sdk_prompt_carries_the_race_guard_rule():
    import importlib.util
    spec = importlib.util.spec_from_file_location("lw_executor_rg_probe",
                                                  ROOT / "ops" / "loop" / "executor.py")
    ex = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = ex
    spec.loader.exec_module(ex)
    assert rg.CHILD_RULE in ex.sdk_prompt(1, "b", "fixed")
