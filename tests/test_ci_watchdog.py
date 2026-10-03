"""LW-CIWatchdog: the red-main auto-fixer's decision logic.

The task fires at startup and every 2 minutes, unattended, with permission to
push and merge. That authority is why almost all of the logic here is PURE and
tested in isolation: the parts that decide WHETHER to act must be readable and
provable without a GitHub API, a worktree, or a model call.

Three rails the tests exist to hold:

  1. HALT is checked first and answers everything. A kill switch that only works
     when the tool is otherwise healthy is not a kill switch.
  2. Ambiguity NEVER means act. `queued`, `pending`, `unavailable` and
     `not-evaluated` all wait. Only a settled `failure` triggers a fix - the same
     distinction f1 item 12 had to build into `check_ci`, for the same reason.
  3. The merge self-gates on the FIX BRANCH'S OWN green CI at its own head sha.
     Merging a ci-fix on anything else - the base's status, a stale run, a
     pending one - is how an auto-fixer turns one red main into two.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _load():
    spec = importlib.util.spec_from_file_location(
        "lw_ci_watchdog_under_test", ROOT / "tools" / "ci_watchdog.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


cw = _load()

RED = {"status": "failure", "sha": "a" * 40, "runs": [{"name": "ci"}]}
GREEN = {"status": "success", "sha": "a" * 40}


# ---- 1. the kill switch ----------------------------------------------------

def test_halt_file_stops_everything(tmp_path: Path):
    (tmp_path / "HALT").write_text("operator", encoding="utf-8")
    assert cw.halted(tmp_path) == "operator"


def test_an_empty_halt_file_still_halts(tmp_path: Path):
    """`type nul > HALT` is the likeliest way an operator creates it under
    stress. An empty file must not read as 'no halt'."""
    (tmp_path / "HALT").write_text("", encoding="utf-8")
    assert cw.halted(tmp_path) == "HALT file present"


def test_no_halt_file_means_no_halt(tmp_path: Path):
    assert cw.halted(tmp_path) is None


def test_halt_beats_a_red_main(tmp_path: Path):
    (tmp_path / "HALT").write_text("stop", encoding="utf-8")
    assert cw.decide(RED, {}, halt=cw.halted(tmp_path))["action"] == "halt"


# ---- 2. ambiguity never means act -----------------------------------------

def test_a_settled_failure_is_the_only_trigger():
    assert cw.decide(RED, {})["action"] == "fix"


def test_green_is_idle():
    assert cw.decide(GREEN, {})["action"] == "idle"


def test_not_evaluated_is_idle_not_a_fix():
    """paths-ignore covered every changed file, so no run was ever coming.
    Nothing is broken and nothing is owed."""
    d = cw.decide({"status": "not-evaluated", "sha": "b" * 40}, {})
    assert d["action"] == "idle"


def test_every_unsettled_status_waits():
    for status in ("queued", "pending", "unavailable"):
        d = cw.decide({"status": status, "sha": "b" * 40}, {})
        assert d["action"] == "wait", status


def test_an_unknown_status_waits_rather_than_acting():
    """Fail closed on a status string nobody anticipated."""
    assert cw.decide({"status": "banana", "sha": "b" * 40}, {})["action"] == "wait"


# ---- 3. attempt budget -----------------------------------------------------

def test_a_second_attempt_on_the_same_sha_is_allowed():
    state = {"sha": "a" * 40, "attempts": 1}
    assert cw.decide(RED, state, max_attempts=2)["action"] == "fix"


def test_the_budget_is_exhausted_and_it_gives_up_loudly():
    state = {"sha": "a" * 40, "attempts": 2}
    d = cw.decide(RED, state, max_attempts=2)
    assert d["action"] == "give-up"
    assert "2" in d["reason"]


def test_a_new_red_sha_resets_the_budget():
    """The budget is per-sha. A different failure deserves its own attempts, or
    one exhausted sha would wedge the watchdog forever."""
    state = {"sha": "a" * 40, "attempts": 9}
    assert cw.decide({"status": "failure", "sha": "c" * 40}, state,
                     max_attempts=2)["action"] == "fix"


def test_bump_attempt_counts_within_a_sha_and_resets_across_them():
    s = cw.bump_attempt({}, "a" * 40)
    assert s == {"sha": "a" * 40, "attempts": 1}
    s = cw.bump_attempt(s, "a" * 40)
    assert s["attempts"] == 2
    s = cw.bump_attempt(s, "d" * 40)
    assert s["attempts"] == 1


def test_bump_attempt_does_not_mutate_its_input():
    src = {"sha": "a" * 40, "attempts": 1}
    cw.bump_attempt(src, "a" * 40)
    assert src["attempts"] == 1


# ---- 4. the merge self-gate ------------------------------------------------

def test_merge_needs_the_fix_branchs_own_green_ci():
    assert cw.merge_allowed({"status": "success", "sha": "f" * 40},
                            "f" * 40) is True


def test_merge_is_refused_when_the_green_is_for_another_sha():
    """A stale success from an earlier push on the same branch is the trap. The
    status must belong to the head being merged."""
    assert cw.merge_allowed({"status": "success", "sha": "0" * 40},
                            "f" * 40) is False


def test_merge_is_refused_on_anything_but_success():
    for status in ("failure", "pending", "queued", "unavailable",
                   "not-evaluated"):
        assert cw.merge_allowed({"status": status, "sha": "f" * 40},
                                "f" * 40) is False, status


def test_merge_is_refused_on_a_missing_status():
    assert cw.merge_allowed(None, "f" * 40) is False
    assert cw.merge_allowed({}, "f" * 40) is False


# ---- 5. naming + transient classification ----------------------------------

def test_branch_name_is_unique_per_sha_and_attempt():
    a = cw.branch_name("abcdef1234567890" + "0" * 24, 1)
    b = cw.branch_name("abcdef1234567890" + "0" * 24, 2)
    assert a != b
    assert a.startswith("ci-fix/")
    assert "abcdef12" in a


def test_branch_name_never_contains_a_path_separator_or_space():
    n = cw.branch_name("a" * 40, 1)
    assert " " not in n and "\\" not in n
    assert n.count("/") == 1


def test_a_transient_api_condition_is_not_a_repo_fault():
    """Same class the weekly-hygiene wrapper already handles: a credit or rate
    limit must not burn an attempt, or one bad afternoon exhausts the budget on
    a repo that was never broken."""
    for txt in ["credit balance is too low", "429 Too Many Requests",
                "API Error: overloaded", "rate_limit_error"]:
        assert cw.is_transient(txt) is True, txt


def test_an_ordinary_failure_is_not_transient():
    assert cw.is_transient("AssertionError: 3 tests failed") is False
    assert cw.is_transient("") is False


# ---- 6. single instance ----------------------------------------------------

def test_a_fresh_lock_blocks_a_second_run(tmp_path: Path):
    """The task fires every 2 minutes and a fix pass takes longer than that, so
    overlapping runs are the DEFAULT, not an edge case."""
    assert cw.acquire(tmp_path, pid=111, now=1000.0) is True
    assert cw.acquire(tmp_path, pid=222, now=1030.0) is False


def test_a_stale_lock_is_reclaimed(tmp_path: Path):
    assert cw.acquire(tmp_path, pid=111, now=1000.0) is True
    assert cw.acquire(tmp_path, pid=222, now=1000.0 + cw.LOCK_STALE_S + 1) is True


def test_release_lets_the_next_run_in(tmp_path: Path):
    assert cw.acquire(tmp_path, pid=111, now=1000.0) is True
    cw.release(tmp_path)
    assert cw.acquire(tmp_path, pid=222, now=1001.0) is True


def test_a_corrupt_lock_file_does_not_wedge_the_watchdog(tmp_path: Path):
    (tmp_path / "lock.json").write_text("{not json", encoding="utf-8")
    assert cw.acquire(tmp_path, pid=111, now=1000.0) is True


# ---- 7. task schedule ------------------------------------------------------

def test_task_xml_has_exactly_one_repeating_trigger():
    """Two repeating triggers run two independent schedules at once.

    Measured on LW-Wallpaper 2026-08-13: a BootTrigger/LogonTrigger repeat
    PLUS a TimeTrigger repeat halved the real interval (1.54 min against a
    configured 3). The TimeTrigger owns the cadence; the boot trigger is a
    one-shot kick so the task survives a reboot without a second schedule.
    """
    xml = cw.task_xml("py.exe", "watchdog.py", every_minutes=2)

    assert "<BootTrigger>" in xml, "must still start after a reboot"
    assert "<TimeTrigger>" in xml, "must arm the repeat from install time"
    assert xml.count("<Repetition>") == 1
    assert xml.count("<Interval>PT2M</Interval>") == 1
    boot = xml.split("<BootTrigger>")[1].split("</BootTrigger>")[0]
    assert "<Repetition>" not in boot, "the boot trigger must not repeat"


# ---- 8. the fleet kit's gate (kit v3; operator directive 2026-10-02) ------

_UNSET = {"url_source": lambda: None}


def _isolate_logs(monkeypatch, tmp_path: Path):
    """Keep the gate's two log writes out of the live runtime + logs trees."""
    monkeypatch.setattr(cw, "STATE_DIR", tmp_path / "state")
    he = cw._bind_headless_env()
    monkeypatch.setattr(he, "LOG_DIR", tmp_path / "logs")


def test_a_refused_proxy_attempts_nothing(monkeypatch, tmp_path: Path):
    """No worktree, no model, no plain-claude fallback: `run` is never called."""
    _isolate_logs(monkeypatch, tmp_path)
    calls = []
    monkeypatch.setattr(cw, "run", lambda *a, **k: calls.append(a))
    result = cw.do_fix_pass("a" * 40, "ci", 1, None, model="m", dry_run=False,
                            fix_timeout=1, env_seams=_UNSET)
    assert result == "refused"
    assert calls == []
    assert "unset" in (tmp_path / "state" / "watchdog.log").read_text(encoding="utf-8")


def test_a_dry_run_also_reports_the_refusal(monkeypatch, tmp_path: Path):
    _isolate_logs(monkeypatch, tmp_path)
    assert cw.do_fix_pass("a" * 40, "ci", 1, None, model="m", dry_run=True,
                          fix_timeout=1, env_seams=_UNSET) == "refused"


def test_a_refusal_refunds_the_attempt_and_exits_nonzero(monkeypatch, tmp_path: Path):
    _isolate_logs(monkeypatch, tmp_path)

    class _TG:
        @staticmethod
        def check_ci(_ref):
            return RED

    monkeypatch.setattr(cw, "_bind_truth_gate", lambda: _TG)
    monkeypatch.setattr(cw, "do_fix_pass", lambda *a, **k: "refused")
    rc = cw.one_pass(model="m", dry_run=False, max_attempts=2, fix_timeout=1,
                     state_dir=tmp_path)
    assert rc == 1
    assert cw.read_state(tmp_path)["attempts"] == 0, "a refusal must not burn the budget"


def _kit_seams(seen: dict, *, url="http://127.0.0.1:4999/x", rc=0, stderr=""):
    """kit.spawn's external edges, injected: URL, connect, runner, exe."""
    def _run(argv, **kw):
        seen["argv"], seen["kw"] = argv, kw

        class _R:
            returncode = rc
            stdout = json.dumps({"result": "fixed", "usage": {}})
        _R.stderr = stderr
        return _R()

    return {"url_source": lambda: url,
            "connect": lambda *a, **k: type("C", (), {"close": lambda self: None})(),
            "run": _run, "exe_source": lambda: r"C:\fake\npm\claude.CMD"}


def test_the_fix_spawn_goes_through_the_kits_gate():
    """kit v4: the fix run IS kit.spawn, so the proxy gate runs at the spawn
    itself - an unset proxy launches nothing and is refunded as transient."""
    seen = {}
    seams = _kit_seams(seen, url=None)
    ok, transient, out = cw._fix_in_worktree(Path("."), "a" * 40, "1", None, 60,
                                             kit_seams=seams)
    assert seen == {}
    assert (ok, transient) == (False, True) and "refused" in out


def test_the_fix_runs_in_the_worktree_at_high_effort_with_stderr(monkeypatch, tmp_path):
    """The v4 parameters this path needed: cwd, return_stderr, effort high."""
    seen = {}
    ok, transient, out = cw._fix_in_worktree(tmp_path, "a" * 40, "1", None, 60,
                                             kit_seams=_kit_seams(seen, stderr="warn"))
    assert (ok, transient) == (True, False)
    assert seen["kw"]["cwd"] == str(tmp_path)
    argv = seen["argv"]
    assert argv[argv.index("--effort") + 1] == "high"
    assert out == "fixedwarn", "the result text and the child's stderr both come back"


def test_a_transient_in_stderr_is_still_refunded(tmp_path):
    seen = {}
    ok, transient, _out = cw._fix_in_worktree(
        tmp_path, "a" * 40, "1", None, 60,
        kit_seams=_kit_seams(seen, rc=1, stderr="API Error: 529 overloaded"))
    assert (ok, transient) == (False, True)


def test_a_timed_out_fix_is_a_plain_failure(tmp_path):
    """kit v4 kills the tree and returns error "timeout"; never a raise."""
    import subprocess
    seams = _kit_seams({})
    seams["run"] = lambda argv, **kw: (_ for _ in ()).throw(
        subprocess.TimeoutExpired(argv, kw.get("timeout")))
    assert cw._fix_in_worktree(tmp_path, "a" * 40, "1", None, 60,
                               kit_seams=seams) == (False, False, "timeout")


def test_the_fix_run_launches_the_resolved_cli_not_the_bare_name(monkeypatch, tmp_path):
    """Sibling of the responder defect measured 2026-10-03: on Windows the CLI
    is `claude.CMD`, and a bare "claude" argv makes CreateProcess look for
    `claude.exe` and raise FileNotFoundError, so a red CI would have crashed
    the fix run instead of reaching the model."""
    seen = {}
    cw._fix_in_worktree(tmp_path, "a" * 40, "1", "claude-sonnet-5", 60,
                        kit_seams=_kit_seams(seen))
    assert seen["argv"][0] == r"C:\fake\npm\claude.CMD"
    assert seen["argv"][seen["argv"].index("--model") + 1] == "claude-sonnet-5"


def test_a_spent_fleet_kit_budget_attempts_nothing(monkeypatch, tmp_path: Path):
    """Kit v3: the 120-run rolling budget is checked at the gate, before any
    worktree exists, and refunds the attempt like any refusal."""
    _isolate_logs(monkeypatch, tmp_path)
    he = cw._bind_headless_env()
    b = he.budget()
    for _ in range(b.cap):
        b.record()
    calls = []
    monkeypatch.setattr(cw, "run", lambda *a, **k: calls.append(a))
    up = {"url_source": lambda: "http://127.0.0.1:4999/x",
          "connect": lambda *a, **k: type("C", (), {"close": lambda self: None})()}
    assert cw.do_fix_pass("a" * 40, "ci", 1, None, model=None, dry_run=False,
                          fix_timeout=1, env_seams=up) == "refused"
    assert calls == []
