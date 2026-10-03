"""Every headless `claude` spawn in this tree runs through the local proxy.

Operator directive, confirmed in session 2026-10-02: at spawn time read the USER
environment variable `CLAUDE_HEADLESS_BASE_URL` (registry first, because a
process started before the variable was set never inherits it), hand it to the
CHILD as `ANTHROPIC_BASE_URL`, and FAIL CLOSED - unset, non-loopback, or a port
nobody answers on all REFUSE the spawn. Deleting the variable is the operator's
kill switch for every tree, so it has to stop every spawn site, which is what the
site-coverage arm at the bottom pins.

Hermetic by construction: the registry reader, the environment and the probe are
all injected. Nothing here reads the operator's real variable, and nothing here
starts `claude`.
"""
from __future__ import annotations

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


def _url(port: int, host: str = "127.0.0.1") -> str:
    return f"http://{host}:{port}/tc-acct/{SECRET}"


def _no_registry():
    """The registry could not be read at all - env is the fallback."""
    return None


@pytest.fixture()
def open_port():
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.bind(("127.0.0.1", 0))
    srv.listen(4)
    try:
        yield srv.getsockname()[1]
    finally:
        srv.close()


@pytest.fixture()
def closed_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


# ---------------------------------------------------------------------------
# Fail closed
# ---------------------------------------------------------------------------

def test_unset_is_refused():
    with pytest.raises(he.HeadlessRefused) as exc:
        he.resolve(registry_reader=_no_registry, environ={})
    assert "unset" in str(exc.value)


def test_blank_is_refused():
    with pytest.raises(he.HeadlessRefused):
        he.resolve(registry_reader=_no_registry, environ={he.VAR: "   "})


@pytest.mark.parametrize("host", ["10.1.2.3", "example.com", "127.0.0.2.example.com",
                                  "0.0.0.0"])
def test_a_non_loopback_host_is_refused(host):
    url = f"http://{host}:8080/tc-acct/{SECRET}"
    probed = []
    with pytest.raises(he.HeadlessRefused) as exc:
        he.resolve(registry_reader=_no_registry, environ={he.VAR: url},
                   probe=lambda h, p: probed.append((h, p)) or True)
    assert "loopback" in str(exc.value)
    assert probed == [], "a non-loopback URL must be refused BEFORE any connect"
    assert SECRET not in str(exc.value)


def test_a_closed_port_is_refused(closed_port):
    with pytest.raises(he.HeadlessRefused) as exc:
        he.resolve(registry_reader=_no_registry,
                   environ={he.VAR: _url(closed_port)})
    reason = str(exc.value)
    assert "connect refused" in reason
    assert f"127.0.0.1:{closed_port}" in reason
    assert SECRET not in reason and "tc-acct" not in reason


def test_an_unparseable_port_is_refused():
    with pytest.raises(he.HeadlessRefused) as exc:
        he.resolve(registry_reader=_no_registry,
                   environ={he.VAR: f"http://127.0.0.1:notaport/{SECRET}"})
    assert SECRET not in str(exc.value)


def test_a_non_http_scheme_is_refused():
    with pytest.raises(he.HeadlessRefused):
        he.resolve(registry_reader=_no_registry,
                   environ={he.VAR: f"ftp://127.0.0.1:21/{SECRET}"},
                   probe=lambda h, p: True)


# ---------------------------------------------------------------------------
# The open path
# ---------------------------------------------------------------------------

def test_an_open_port_sets_the_child_env_only(open_port):
    url = _url(open_port)
    before = dict(os.environ)
    base = {"PATH": "x", "KEEP": "1"}
    env = he.child_env(base, registry_reader=_no_registry, environ={he.VAR: url})
    assert env["ANTHROPIC_BASE_URL"] == url
    assert env["KEEP"] == "1"
    assert "ANTHROPIC_BASE_URL" not in base, "the base dict must be copied, not mutated"
    # Booleans bound FIRST: an assert over os.environ would render the whole
    # process environment into a failure (tests/test_assert_never_renders_the_environ.py).
    unchanged = dict(os.environ) == before
    assert unchanged, "os.environ must never be mutated"


def test_child_env_defaults_to_a_copy_of_os_environ(open_port):
    env = he.child_env(registry_reader=_no_registry, environ={he.VAR: _url(open_port)})
    is_copy = env is not os.environ
    same_path = env.get("PATH") == os.environ.get("PATH")
    parent_untouched = os.environ.get("ANTHROPIC_BASE_URL") != env.get("ANTHROPIC_BASE_URL")
    assert is_copy and same_path and parent_untouched


@pytest.mark.parametrize("host", ["localhost", "LOCALHOST"])
def test_localhost_is_loopback(host):
    seen = []
    url = he.resolve(registry_reader=_no_registry,
                     environ={he.VAR: f"http://{host}:4567/x"},
                     probe=lambda h, p: seen.append((h, p)) or True)
    assert url.endswith(":4567/x")
    assert seen == [("localhost", 4567)]


def test_ipv6_loopback_is_accepted():
    seen = []
    he.resolve(registry_reader=_no_registry, environ={he.VAR: "http://[::1]:4567/"},
               probe=lambda h, p: seen.append((h, p)) or True)
    assert seen == [("::1", 4567)]


def test_a_missing_port_takes_the_scheme_default():
    seen = []
    he.resolve(registry_reader=_no_registry, environ={he.VAR: "http://127.0.0.1/"},
               probe=lambda h, p: seen.append(p) or True)
    assert seen == [80]


# ---------------------------------------------------------------------------
# Registry before env - and the kill switch beats a stale inherited env
# ---------------------------------------------------------------------------

def test_the_registry_is_read_before_the_environment():
    got = he.read_base_url(registry_reader=lambda: "http://127.0.0.1:1111/reg",
                           environ={he.VAR: "http://127.0.0.1:2222/env"})
    assert got == "http://127.0.0.1:1111/reg"


def test_an_unreadable_registry_falls_back_to_the_environment():
    got = he.read_base_url(registry_reader=_no_registry,
                           environ={he.VAR: "http://127.0.0.1:2222/env"})
    assert got == "http://127.0.0.1:2222/env"


def test_a_deleted_registry_value_beats_a_stale_inherited_env():
    """THE KILL SWITCH. A process started while the variable existed still
    carries it in its own environment after the operator deletes it. If the env
    fallback answered here, deleting the variable would stop nothing that was
    already running - so a READABLE registry with no value means unset."""
    got = he.read_base_url(registry_reader=lambda: "",
                           environ={he.VAR: "http://127.0.0.1:2222/stale"})
    assert got is None
    with pytest.raises(he.HeadlessRefused):
        he.resolve(registry_reader=lambda: "",
                   environ={he.VAR: "http://127.0.0.1:2222/stale"},
                   probe=lambda h, p: True)


def test_the_default_registry_reader_is_inert_off_windows():
    assert he._registry_value(os_name="posix") is None


# ---------------------------------------------------------------------------
# Logging never carries the URL
# ---------------------------------------------------------------------------

def test_log_refusal_writes_one_line_without_the_url(tmp_path, closed_port):
    try:
        he.resolve(registry_reader=_no_registry, environ={he.VAR: _url(closed_port)})
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

def test_cli_exec_refusal_exits_78_and_runs_nothing(tmp_path, capsys, monkeypatch):
    ran = []
    monkeypatch.setattr(he.subprocess, "run", lambda *a, **k: ran.append(a))
    rc = he.main(["exec", "--", "claude", "-p", "hi"], log_dir=tmp_path,
                 registry_reader=_no_registry, environ={})
    assert rc == he.REFUSED_EXIT == 78
    assert ran == []
    assert "unset" in capsys.readouterr().err
    assert list(tmp_path.glob("*.log")), "the refusal must be logged"


def test_cli_check_reports_refused(capsys):
    rc = he.main(["check"], registry_reader=_no_registry, environ={})
    assert rc == 78
    assert capsys.readouterr().out.startswith("REFUSED")


def test_cli_check_reports_ok_host_port_only(open_port, capsys):
    rc = he.main(["check"], registry_reader=_no_registry,
                 environ={he.VAR: _url(open_port)})
    out = capsys.readouterr().out
    assert rc == 0
    assert out.strip() == f"OK 127.0.0.1:{open_port}"
    assert SECRET not in out


def test_cli_exec_hands_the_child_the_base_url(open_port, tmp_path):
    url = _url(open_port)
    probe = ("import os, sys; "
             f"sys.exit(0 if os.environ.get('ANTHROPIC_BASE_URL') == {url!r} else 3)")
    rc = he.main(["exec", "--", sys.executable, "-c", probe], log_dir=tmp_path,
                 registry_reader=_no_registry, environ={he.VAR: url})
    assert rc == 0


def test_exec_hands_the_child_this_process_stdio():
    """REGRESSION, measured 2026-10-02. CREATE_NO_WINDOW gives the child a hidden
    console of its own, so with IMPLICIT inheritance its output went there and a
    caller capturing it (weekly_hygiene_run.ps1 tees it to a log and greps it
    for transient errors) got nothing. Run in a subprocess so the stdio really
    is a pipe, as it is under PowerShell."""
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


def test_cli_exec_without_argv_is_a_usage_error(capsys):
    assert he.main(["exec", "--"], registry_reader=_no_registry, environ={}) == 2


# ---------------------------------------------------------------------------
# SITE COVERAGE - every headless claude launcher goes through this module
# ---------------------------------------------------------------------------

_PY_SPAWN = re.compile(
    r"""["']claude(?:\.cmd|\.exe)?["']\s*,\s*["']-p["']"""
    r"""|which\(\s*["']claude""")
_PS_SPAWN = re.compile(
    r"""(?i)&\s*claude\b|\bclaude(?:\.exe|\.cmd)?\s+-p\b|\$ClaudeExe\b""")
_SKIP_DIRS = {"__pycache__", "runtime", "models", "dwpose_onnx"}


def _launches_claude(path: Path, text: str) -> bool:
    if path.suffix == ".py":
        return bool(_PY_SPAWN.search(text))
    code = [ln for ln in text.splitlines() if not ln.lstrip().startswith("#")]
    return any(_PS_SPAWN.search(ln) for ln in code)


def _spawn_files() -> list[Path]:
    found = []
    for base in (ROOT / "tools", ROOT / "ops"):
        for path in base.rglob("*"):
            if path.suffix not in (".py", ".ps1") or not path.is_file():
                continue
            if _SKIP_DIRS & set(path.relative_to(ROOT).parts):
                continue
            if path.name == "lw_headless_env.py":
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
    """POSITIVE CONTROL. A scan that finds nothing makes the arm below pass
    vacuously, so the known launchers must all be detected."""
    found = {p.relative_to(ROOT).as_posix() for p in _spawn_files()}
    missing = KNOWN_SITES - found
    assert not missing, f"the detector no longer sees {sorted(missing)}"


@pytest.mark.parametrize("text,suffix,expect", [
    ('argv = ["claude", "-p", prompt]', ".py", True),
    ("exe = shutil.which('claude')", ".py", True),
    ('"""a headless `claude -p` run"""', ".py", False),
    ("$out = & claude -p $prompt", ".ps1", True),
    ("# spawns `claude -p` with nobody watching", ".ps1", False),
    ("Start-Process -FilePath $ClaudeExe", ".ps1", True),
    ('$x = gemini -p "hi"', ".ps1", False),
])
def test_the_site_detector_shapes(text, suffix, expect):
    assert _launches_claude(Path("x" + suffix), text) is expect


def _code_lines(text: str) -> list[str]:
    return [ln for ln in text.splitlines() if not ln.lstrip().startswith("#")]


@pytest.mark.parametrize("path", _spawn_files(), ids=lambda p: p.name)
def test_every_headless_claude_launcher_goes_through_the_proxy_gate(path):
    """A mention in a comment does not count: the gate must be CALLED in code."""
    rel = path.relative_to(ROOT).as_posix()
    text = path.read_text(encoding="utf-8", errors="replace")
    code = _code_lines(text)
    assert "lw_headless_env" in text, (
        f"{rel} launches claude headless without tools/lw_headless_env.py - "
        "deleting CLAUDE_HEADLESS_BASE_URL would not stop it")
    if path.suffix == ".py":
        assert any("child_env(" in ln for ln in code), \
            f"{rel} names the gate but never calls child_env()"
    else:
        assert any("lw_headless_env.py" in ln for ln in code), \
            f"{rel} names the gate only in a comment"
        assert any(("$HeadlessEnv" in ln or "lw_headless_env" in ln)
                   and re.search(r"\bexec\b", ln) for ln in code), \
            f"{rel} never runs the gate's exec"
