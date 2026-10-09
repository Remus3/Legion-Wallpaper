"""Every headless `claude` spawn in this tree runs through MAIN's fleet kit.

Operator order via MAIN (kit v3, 2026-10-03): every headless `claude` this tree
starts goes through `fleet_headless.spawn`, and LW's own proxy-env, probe,
budget, skip, status and console code is deleted. `tools/lw_headless_env.py` is
now a thin binding of the vendored kit: `kit.spawn` where it fits, the kit's
PRIMITIVES (base_url, check_url, probe, child_env, claude_exe, RunBudget,
write_status, usage_line) where it does not. These arms pin the binding, the
fail-closed gate as the kit now answers it, the accounting, the CLI, and the
site coverage over every launcher in tools/ and ops/.

Hermetic by construction: the URL source, the connector, the runner and the
executable are all injected, and `conftest.py` points `FLEET_ROOT` at a tmp dir
for every arm. Nothing here reads the operator's real variable, and nothing here
starts `claude`.
"""
from __future__ import annotations

import json
import os
import re
import socket
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import lw_headless_env as he  # noqa: E402

# A fake path segment standing in for whatever account routing the real URL
# carries. The arms assert it never reaches a reason or a log line.
SECRET = "fake-id"
_URL = f"http://127.0.0.1:4999/tc-acct/{SECRET}"


def _url(port: int, host: str = "127.0.0.1") -> str:
    return f"http://{host}:{port}/tc-acct/{SECRET}"


class _Conn:
    def close(self):
        pass


def _up(*_a, **_k):
    return _Conn()


def _down(*_a, **_k):
    raise ConnectionRefusedError("refused")


@pytest.fixture()
def closed_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


@pytest.fixture()
def open_port():
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.bind(("127.0.0.1", 0))
    srv.listen(4)
    try:
        yield srv.getsockname()[1]
    finally:
        srv.close()


# ---------------------------------------------------------------------------
# The binding: the vendored kit, by path, one module object
# ---------------------------------------------------------------------------

def test_the_kit_is_bound_from_the_vendored_copy():
    assert Path(he.kit.__file__).resolve() == (ROOT / "ops" / "fleet_kit" /
                                               "fleet_headless.py").resolve()
    assert sys.modules["fleet_headless"] is he.kit
    assert he.kit.KIT_VERSION == 14


def test_the_refusal_class_is_the_kits():
    assert he.HeadlessRefused is he.kit.Refused
    assert he.VAR == he.kit.VAR == "CLAUDE_HEADLESS_BASE_URL"
    assert he.CODE == "LW"


def test_the_lean_flags_are_read_off_the_kits_argv_builder():
    argv = he.kit.build_argv("x", "p", "m", "e", setting_sources=he.SETTING_SOURCES)
    assert tuple(argv[-len(he.LEAN_ARGS):]) == he.LEAN_ARGS
    assert he.LEAN_ARGS[he.LEAN_ARGS.index("--setting-sources") + 1] == "project"
    assert "--strict-mcp-config" in he.LEAN_ARGS
    assert "--bare" not in he.LEAN_ARGS, "LW's floors live in hooks"


def test_rebinding_reuses_the_loaded_kit():
    assert he._bind_kit() is he.kit


# ---------------------------------------------------------------------------
# Fail closed - the kit's answers
# ---------------------------------------------------------------------------

def test_unset_is_refused():
    with pytest.raises(he.HeadlessRefused) as exc:
        he.resolve(lambda: None, _up)
    assert "unset" in str(exc.value)


@pytest.mark.parametrize("host", ["10.1.2.3", "example.com", "127.0.0.2.example.com",
                                  "0.0.0.0"])
def test_a_non_loopback_host_is_refused_before_any_connect(host):
    probed = []
    with pytest.raises(he.HeadlessRefused) as exc:
        he.resolve(lambda: f"http://{host}:8080/tc-acct/{SECRET}",
                   lambda *a, **k: probed.append(a) or _Conn())
    assert "loopback" in str(exc.value)
    assert probed == []
    assert SECRET not in str(exc.value)


def test_a_closed_port_is_refused(closed_port):
    with pytest.raises(he.HeadlessRefused) as exc:
        he.resolve(lambda: _url(closed_port))
    reason = str(exc.value)
    assert "unreachable" in reason
    assert SECRET not in reason and "tc-acct" not in reason


@pytest.mark.parametrize("url", [f"ftp://127.0.0.1:21/{SECRET}",
                                 f"https://127.0.0.1:443/{SECRET}",
                                 "http://127.0.0.1/no-port",
                                 f"http://user@127.0.0.1:80/{SECRET}"])
def test_the_kit_refuses_what_is_not_plain_http_to_an_explicit_loopback_port(url):
    """Kit v3 is stricter than LW's old gate: https and a defaulted port are
    refused now. Behaviour moved to the kit on purpose - one path, the kit's."""
    with pytest.raises(he.HeadlessRefused) as exc:
        he.resolve(lambda: url, _up)
    assert SECRET not in str(exc.value)


@pytest.mark.parametrize("host", ["localhost", "127.0.0.1"])
def test_a_loopback_url_passes(host):
    seen = []
    url = he.resolve(lambda: f"http://{host}:4567/x",
                     lambda addr, timeout=0: seen.append(addr) or _Conn())
    assert url.endswith(":4567/x")
    assert seen == [(host, 4567)]


def test_the_registry_wins_and_its_absence_is_the_kill_switch():
    """THE KILL SWITCH, as the kit implements it: a READABLE registry with no
    value answers None even while a stale inherited copy sits in the env."""
    stale = {he.VAR: "http://127.0.0.1:2222/stale"}
    assert he.kit.base_url(registry=lambda: (True, None), environ=stale) is None
    assert he.kit.base_url(registry=lambda: (True, "http://127.0.0.1:1/r"),
                           environ=stale) == "http://127.0.0.1:1/r"
    assert he.kit.base_url(registry=lambda: (False, None),
                           environ=stale) == stale[he.VAR]


# ---------------------------------------------------------------------------
# The child env - the kit's, a copy
# ---------------------------------------------------------------------------

def test_the_child_env_is_the_kits_and_a_copy():
    before = dict(os.environ)
    base = {"PATH": "x", "KEEP": "1", "CLAUDE_CODE_USE_BEDROCK": "1"}
    # The credential names come from the kit, so no name-to-literal pair is
    # written here (tests/test_no_secret_literals.py scans tracked files).
    base.update(dict.fromkeys(he.kit.STRIP_EXACT, "placeholder"))
    env = he.child_env(base, url_source=lambda: _URL, connect=_up)
    assert env["ANTHROPIC_BASE_URL"] == _URL
    assert env["KEEP"] == "1"
    assert not set(he.kit.STRIP_EXACT) & set(env)
    assert "CLAUDE_CODE_USE_BEDROCK" not in env
    assert "ANTHROPIC_BASE_URL" not in base, "the base dict must be copied"
    unchanged = dict(os.environ) == before
    assert unchanged, "os.environ must never be mutated"


def test_a_refused_gate_builds_no_env():
    with pytest.raises(he.HeadlessRefused):
        he.child_env({}, url_source=lambda: _URL, connect=_down)


# ---------------------------------------------------------------------------
# kit.spawn through the adapter: FLEET_ROOT, code LW, bare False
# ---------------------------------------------------------------------------

def _fake_run(seen):
    def run(argv, **kw):
        seen["argv"], seen["kw"] = argv, kw

        class _R:
            returncode = 0
            stdout = json.dumps({"result": "done", "usage": {"input_tokens": 5}})
            stderr = ""
        return _R()
    return run


def test_spawn_is_kit_spawn_at_fleet_root_with_lw_code():
    seen = {}
    line = he.spawn("hello", note="2026-10-03-from-RC-ACK-x.md", url_source=lambda: _URL,
                    connect=_up, run=_fake_run(seen), exe_source=lambda: "claude.exe")
    assert line["code"] == "LW" and line["result"] == "done"
    assert line["bare"] is False
    assert seen["kw"]["cwd"] == str(he.FLEET_ROOT)
    assert seen["kw"]["env"]["ANTHROPIC_BASE_URL"] == _URL
    status = json.loads((Path(he.FLEET_ROOT) / he.kit.STATUS_REL).read_text(encoding="ascii"))
    assert status["code"] == "LW" and status["state"] == "idle"
    assert he.budget().used() == 1


def test_spawn_takes_the_kits_triage_kwargs_without_a_duplicate_keyword():
    """Kit v11: fleet_inbox.triage_spawn_kwargs(True) carries floors_in_hooks;
    the adapter must accept it (not a duplicate-keyword TypeError) and still
    declare floors in hooks to the kit."""
    seen = {}
    import lw_inbox_responder
    kw = lw_inbox_responder.fleet_inbox.triage_spawn_kwargs(True)
    line = he.spawn("hello", url_source=lambda: _URL, connect=_up, run=_fake_run(seen),
                    exe_source=lambda: "claude.exe", **kw)
    assert line["bare"] is False
    assert "--bare" not in seen["argv"]


def test_spawn_refuses_a_caller_that_denies_floors_in_hooks():
    """LW's floors live in hooks on every path; floors_in_hooks=False would
    let --bare through the kit's door, so the adapter refuses it."""
    seen = {}
    with pytest.raises(he.HeadlessRefused):
        he.spawn("x", floors_in_hooks=False, bare=True, url_source=lambda: _URL,
                 connect=_up, run=_fake_run(seen), exe_source=lambda: "claude.exe")
    assert seen == {}


def test_spawn_refuses_before_launch_when_the_budget_is_spent():
    b = he.budget()
    for _ in range(b.cap):
        b.record()
    seen = {}
    with pytest.raises(he.HeadlessRefused):
        he.spawn("x", url_source=lambda: _URL, connect=_up, run=_fake_run(seen),
                 exe_source=lambda: "claude.exe")
    assert seen == {}


# ---------------------------------------------------------------------------
# start_run / end_run - kit.spawn's own accounting for the paths it cannot carry
# ---------------------------------------------------------------------------

def test_start_and_end_run_follow_kit_spawns_sequence():
    started = he.start_run()
    status = Path(he.FLEET_ROOT) / he.kit.STATUS_REL
    assert json.loads(status.read_text(encoding="ascii"))["state"] == "running"
    assert he.budget().used() == 1
    line = he.end_run(started, note="unit", model="opus", effort="", rc=0,
                      stdout=json.dumps({"usage": {"output_tokens": 3}}))
    assert line["output_tokens"] == 3 and line["code"] == "LW"
    assert json.loads(status.read_text(encoding="ascii"))["state"] == "idle"
    usage = (Path(he.FLEET_ROOT) / he.kit.USAGE_REL).read_text(encoding="ascii")
    assert usage.count("\n") == 1


def test_start_run_refuses_and_publishes_limit_when_spent():
    b = he.budget()
    for _ in range(b.cap):
        b.record()
    assert he.can_start() is False
    with pytest.raises(he.HeadlessRefused) as exc:
        he.start_run()
    assert "budget" in str(exc.value)
    status = json.loads((Path(he.FLEET_ROOT) / he.kit.STATUS_REL).read_text(encoding="ascii"))
    assert status["state"] == "limit"


def test_end_run_tolerates_non_json_output():
    line = he.end_run(he.start_run(), note="n", model="", effort="", rc=1, stdout="text")
    assert line["input_tokens"] is None and line["rc"] == 1


# ---------------------------------------------------------------------------
# Logging never carries the URL
# ---------------------------------------------------------------------------

def test_log_refusal_writes_one_line_without_the_url(tmp_path, closed_port):
    try:
        he.resolve(lambda: _url(closed_port))
    except he.HeadlessRefused as exc:
        reason = str(exc)
    else:  # pragma: no cover
        pytest.fail("a closed port was not refused")
    he.log_refusal("unit-test", reason, log_dir=tmp_path)
    logs = list(tmp_path.glob("*.log"))
    assert len(logs) == 1
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}\.log", logs[0].name)
    body = logs[0].read_text(encoding="utf-8")
    assert body.count("\n") == 1
    assert "unit-test" in body and "refused" in body
    assert SECRET not in body and "tc-acct" not in body


def test_log_refusal_scrubs_a_url_handed_to_it_by_mistake(tmp_path):
    he.log_refusal("unit-test", f"oops {_url(9)}", log_dir=tmp_path)
    body = next(tmp_path.glob("*.log")).read_text(encoding="utf-8")
    assert SECRET not in body and "://" not in body


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def test_cli_check_reports_refused(capsys):
    assert he.main(["check"], url_source=lambda: None) == 78
    assert capsys.readouterr().out.startswith("REFUSED")


def test_cli_check_reports_ok_host_port_only(capsys):
    assert he.main(["check"], url_source=lambda: _URL, connect=_up) == 0
    out = capsys.readouterr().out
    assert out.strip() == "OK 127.0.0.1:4999"
    assert SECRET not in out


def test_cli_exec_refusal_exits_78_and_runs_nothing(tmp_path, capsys, monkeypatch):
    ran = []
    monkeypatch.setattr(he.subprocess, "run", lambda *a, **k: ran.append(a))
    rc = he.main(["exec", "--", "claude", "-p", "hi"], log_dir=tmp_path,
                 url_source=lambda: None)
    assert rc == he.REFUSED_EXIT == 78
    assert ran == []
    assert "unset" in capsys.readouterr().err
    assert list(tmp_path.glob("*.log")), "the refusal must be logged"
    assert he.budget().used() == 0, "a refused exec spends no budget"


def test_cli_exec_hands_the_child_the_base_url_and_accounts_the_run(tmp_path):
    probe = ("import os, sys; "
             f"sys.exit(0 if os.environ.get('ANTHROPIC_BASE_URL') == {_URL!r} else 3)")
    rc = he.main(["exec", "--", sys.executable, "-c", probe], log_dir=tmp_path,
                 url_source=lambda: _URL, connect=_up)
    assert rc == 0
    assert he.budget().used() == 1
    usage = (Path(he.FLEET_ROOT) / he.kit.USAGE_REL).read_text(encoding="ascii")
    assert json.loads(usage.splitlines()[-1])["rc"] == 0


def test_cli_exec_resolves_a_bare_claude_through_the_kit(monkeypatch, tmp_path):
    seen = {}
    monkeypatch.setattr(he, "_exec", lambda argv, env: seen.setdefault("argv", argv) and 0)
    he.main(["exec", "--", "claude", "-p", "hi", "--model", "opus"], log_dir=tmp_path,
            url_source=lambda: _URL, connect=_up, exe_source=lambda: r"C:\real\claude.exe")
    assert seen["argv"][0] == r"C:\real\claude.exe"


def test_exec_hands_the_child_this_process_stdio():
    """REGRESSION, measured 2026-10-02: with IMPLICIT inheritance under
    CREATE_NO_WINDOW the child's output went to a hidden console."""
    import subprocess
    tools_dir = str(ROOT / "tools")
    code = (
        f"import os, sys; sys.path.insert(0, {tools_dir!r}); import lw_headless_env as he; "
        "sys.exit(he._exec([sys.executable, '-c', "
        "'import sys; print(\"OUT-MARK\"); print(\"ERR-MARK\", file=sys.stderr); "
        "print(sys.stdin.read().strip())'], dict(os.environ)))"
    )
    r = subprocess.run([sys.executable, "-c", code], input="IN-MARK",
                       capture_output=True, text=True, timeout=60,
                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    assert r.returncode == 0, r.stderr
    assert "OUT-MARK" in r.stdout and "IN-MARK" in r.stdout
    assert "ERR-MARK" in r.stderr


def test_cli_exec_without_argv_is_a_usage_error():
    assert he.main(["exec", "--"], url_source=lambda: None) == 2


def test_cli_spawn_runs_kit_spawn_with_extra_flags(tmp_path, capsys):
    prompt = tmp_path / "p.txt"
    prompt.write_text('say "hi"\nline two', encoding="utf-8")
    seen = {}
    rc = he.main(["spawn", "--note", "weekly-hygiene", "--prompt-file", str(prompt),
                  "--", "--allowedTools", "Edit,Read", "--dangerously-skip-permissions"],
                 url_source=lambda: _URL, connect=_up, run=_fake_run(seen),
                 exe_source=lambda: "claude.exe")
    assert rc == 0
    argv = seen["argv"]
    assert argv[:3] == ["claude.exe", "-p", 'say "hi"\nline two']
    assert argv[-3:] == ["--allowedTools", "Edit,Read", "--dangerously-skip-permissions"]
    assert argv[argv.index("--model") + 1] == "sonnet"
    assert json.loads(capsys.readouterr().out)["result"] == "done"


def test_cli_spawn_refusal_exits_78(tmp_path):
    prompt = tmp_path / "p.txt"
    prompt.write_text("x", encoding="utf-8")
    assert he.main(["spawn", "--prompt-file", str(prompt)], log_dir=tmp_path,
                   url_source=lambda: None) == 78


# ---------------------------------------------------------------------------
# SITE COVERAGE - every headless claude launcher goes through the kit
# ---------------------------------------------------------------------------

_PY_SPAWN = re.compile(
    r"""["']claude(?:\.cmd|\.exe)?["']\s*,\s*["']-p["']"""
    r"""|which\(\s*["']claude"""
    r"""|\b(?:lw_headless_env|headless_env|he)\.spawn\(|\bclaude_exe\(""")
_PS_SPAWN = re.compile(
    r"""(?i)&\s*claude\b|\bclaude(?:\.exe|\.cmd)?\s+-p\b|\$ClaudeExe\b|\$HeadlessEnv\s+spawn\b""")
_SKIP_DIRS = {"__pycache__", "runtime", "models", "dwpose_onnx", "fleet_kit"}
_ADAPTER = "tools/lw_headless_env.py"


def _launches_claude(path: Path, text: str) -> bool:
    code = [ln for ln in text.splitlines() if not ln.lstrip().startswith("#")]
    pattern = _PY_SPAWN if path.suffix == ".py" else _PS_SPAWN
    return any(pattern.search(ln) for ln in code)


def _spawn_files() -> list[Path]:
    found = []
    for base in (ROOT / "tools", ROOT / "ops"):
        for path in base.rglob("*"):
            if path.suffix not in (".py", ".ps1") or not path.is_file():
                continue
            if _SKIP_DIRS & set(path.relative_to(ROOT).parts):
                continue
            if path.relative_to(ROOT).as_posix() == _ADAPTER:
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            if _launches_claude(path, text):
                found.append(path)
    return sorted(found)


KNOWN_SITES = {
    "tools/lw_inbox_responder.py",
    "tools/ci_watchdog.py",
    "ops/loop/executor.py",
    "ops/loop/loop_controller.py",
    "tools/headless_run.ps1",
    "tools/weekly_hygiene_run.ps1",
}


def test_the_site_scan_finds_every_known_launcher():
    """POSITIVE CONTROL. A scan that finds nothing passes the arm below vacuously."""
    found = {p.relative_to(ROOT).as_posix() for p in _spawn_files()}
    missing = KNOWN_SITES - found
    assert not missing, f"the detector no longer sees {sorted(missing)}"


@pytest.mark.parametrize("text,suffix,expect", [
    ('argv = ["claude", "-p", prompt]', ".py", True),
    ("exe = shutil.which('claude')", ".py", True),
    ("line = lw_headless_env.spawn(prompt)", ".py", True),
    ("line = headless_env.spawn(prompt, stdin=True)", ".py", True),
    ("line = he.spawn(prompt, cwd=wt)", ".py", True),
    ("line = the.spawn(prompt)", ".py", False),
    ('"""a headless `claude -p` run"""', ".py", False),
    ("$out = & claude -p $prompt", ".ps1", True),
    ("# spawns `claude -p` with nobody watching", ".ps1", False),
    ("Start-Process -FilePath $ClaudeExe", ".ps1", True),
    ("$out = & $Python $HeadlessEnv spawn --note x", ".ps1", True),
    ('$x = gemini -p "hi"', ".ps1", False),
])
def test_the_site_detector_shapes(text, suffix, expect):
    assert _launches_claude(Path("x" + suffix), text) is expect


def _code_lines(text: str) -> list[str]:
    return [ln for ln in text.splitlines() if not ln.lstrip().startswith("#")]


@pytest.mark.parametrize("path", _spawn_files(), ids=lambda p: p.name)
def test_every_headless_claude_launcher_goes_through_the_fleet_kit(path):
    """A mention in a comment does not count: the kit's path must be CALLED."""
    rel = path.relative_to(ROOT).as_posix()
    code = _code_lines(path.read_text(encoding="utf-8", errors="replace"))
    if path.suffix == ".py":
        assert any("headless_env" in ln for ln in code), \
            f"{rel} launches claude without tools/lw_headless_env.py (the kit binding)"
        assert any(re.search(r"\.spawn\(|child_env\(", ln) for ln in code), \
            f"{rel} names the binding but never calls kit.spawn or the kit's child_env"
        assert not any(re.search(r"""which\(\s*["']claude""", ln) for ln in code), \
            f"{rel} resolves claude itself instead of kit.claude_exe"
    else:
        assert any("lw_headless_env.py" in ln for ln in code), \
            f"{rel} names the binding only in a comment"
        assert any("$HeadlessEnv" in ln and re.search(r"\b(spawn|exec)\b", ln)
                   for ln in code), f"{rel} never runs the binding's spawn or exec"


@pytest.mark.parametrize("path", _spawn_files(), ids=lambda p: p.name)
def test_no_launcher_passes_bare(path):
    """bare=False on every LW path: the floors live in hooks, --bare skips them."""
    code = _code_lines(path.read_text(encoding="utf-8", errors="replace"))
    hits = [ln for ln in code if re.search(r"""["']--bare["']|\bbare\s*=\s*True""", ln)]
    assert hits == [], f"{path.name}: {hits}"


# --------------------------------------------------------------------------
# FLEET-KIT v6 ruling (MAIN 2237 section 2), carried by v7: a run that writes
# code holds ONE governor slot at the call. `exec --governor` is that slot for
# the long operator-fired run (tools/headless_run.ps1). Root: conftest seam.
# --------------------------------------------------------------------------

def _gov_root() -> Path:
    import os
    return Path(os.environ["LW_GOVERNOR_ROOT"])


def test_cli_exec_with_governor_holds_exactly_one_slot_for_the_run(monkeypatch, tmp_path):
    seen = {}

    def _fake_exec(argv, env):
        seen["slots"] = [json.loads(p.read_text(encoding="utf-8"))
                         for p in sorted(_gov_root().glob("*.lock"))]
        return 0

    monkeypatch.setattr(he, "_exec", _fake_exec)
    rc = he.main(["exec", "--governor", "interactive", "--", sys.executable, "-c", "pass"],
                 log_dir=tmp_path, url_source=lambda: _URL, connect=_up)
    assert rc == 0
    assert len(seen["slots"]) == 1
    assert seen["slots"][0]["repo"] == "LW" and seen["slots"][0]["priority"] == "interactive"
    assert list(_gov_root().glob("*.lock")) == [], "the slot is released after the run"


def test_cli_exec_without_governor_takes_no_slot(monkeypatch, tmp_path):
    seen = {}
    monkeypatch.setattr(he, "_exec", lambda argv, env: seen.setdefault(
        "slots", list(_gov_root().glob("*.lock"))) and 0 or 0)
    assert he.main(["exec", "--", sys.executable, "-c", "pass"], log_dir=tmp_path,
                   url_source=lambda: _URL, connect=_up) == 0
    assert seen["slots"] == []


def test_cli_exec_no_free_slot_refuses_78_and_runs_nothing(monkeypatch, tmp_path):
    import os
    import time as _time
    root = _gov_root()
    root.mkdir(parents=True, exist_ok=True)
    for i in range(3):
        (root / f"{i}.lock").write_text(json.dumps(
            {"pid": os.getpid(), "repo": "OTHER", "run_id": f"r{i}", "cycle": 0,
             "ts": _time.time()}), encoding="utf-8")
    ran = []
    monkeypatch.setattr(he, "_exec", lambda argv, env: ran.append(argv) or 0)
    rc = he.main(["exec", "--governor", "queued", "--governor-timeout", "0", "--",
                  sys.executable, "-c", "pass"],
                 log_dir=tmp_path, url_source=lambda: _URL, connect=_up)
    assert rc == he.REFUSED_EXIT
    assert ran == []
    assert he.budget().used() == 0, "a refused exec spends no budget"


def test_headless_run_ps1_asks_for_one_interactive_slot():
    text = (ROOT / "tools" / "headless_run.ps1").read_text(encoding="ascii")
    assert '"exec", "--governor", "interactive"' in text


def test_every_lw_headless_child_is_exempt_from_the_subagent_first_hook():
    """Kit v10 (MAIN 0839): a headless child runs with FLEET_SUBAGENT_FIRST=off,
    so the PreToolUse hook never denies its tools once the mode moves to deny.
    A parent that inherited `deny` must not leak it into the child."""
    env = he.child_env({"PATH": "x", "FLEET_SUBAGENT_FIRST": "deny"},
                       url_source=lambda: _URL, connect=_up)
    assert env["FLEET_SUBAGENT_FIRST"] == "off"
