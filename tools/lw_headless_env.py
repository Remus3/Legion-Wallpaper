"""Route every headless `claude` spawn through the local proxy - or refuse it.

# arch: headless-claude spawn gate - CLAUDE_HEADLESS_BASE_URL -> child ANTHROPIC_BASE_URL, fail closed

Operator directive, confirmed in session 2026-10-02. Every HEADLESS `claude`
this tree starts must run through a local proxy:

  * READ at spawn time, from the USER environment STORE (HKCU\\Environment)
    first. A process started before the variable was set never inherits it, so
    `os.environ` alone would read "unset" in exactly the long-lived schedulers
    that spawn the most. `os.environ` is the fallback only when the registry
    cannot be read at all (off Windows, or an unreadable key).
  * A READABLE registry with NO value means UNSET, even if this process still
    carries an inherited copy in its own environment. Deleting the variable is
    the operator's kill switch for every tree; letting a stale inherited copy
    answer would leave every already-running scheduler spawning after the
    switch was thrown.
  * SET it as `ANTHROPIC_BASE_URL` in the CHILD's env only - a copy. This module
    never writes the user or machine environment and never mutates `os.environ`.
  * FAIL CLOSED. Unset or empty, a non-http(s) scheme, a host that is not
    loopback (127.0.0.1, localhost, ::1), or a port nobody answers on within
    2 s: REFUSE and say why. There is no fallback to a plain spawn, and a
    refusal is never retried another way.
  * NEVER log the URL. It can carry account routing in its path. A reason names
    only "unset", host:port, or "connect refused" - and `log_refusal` scrubs
    anything URL-shaped as a backstop.

CLI:
    python tools/lw_headless_env.py check
        OK <host>:<port> and exit 0, or REFUSED <reason> and exit 78.
    python tools/lw_headless_env.py exec -- <argv...>
        Resolve, run argv with the child env (CREATE_NO_WINDOW, inherited
        stdio) and return its exit code. On refusal: reason to stderr, one log
        line under logs/, exit 78 (EX_CONFIG).
"""
from __future__ import annotations

import argparse
import datetime as dt
import os
import re
import shutil
import socket
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlsplit

VAR = "CLAUDE_HEADLESS_BASE_URL"
CHILD_VAR = "ANTHROPIC_BASE_URL"
LOOPBACK = frozenset({"127.0.0.1", "localhost", "::1"})
CONNECT_TIMEOUT_S = 2.0
REFUSED_EXIT = 78  # EX_CONFIG

ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = ROOT / "logs"

# 0 off Windows so the module still imports and tests on a CI runner.
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)

_URLISH = re.compile(r"[A-Za-z][A-Za-z0-9+.-]*://\S*")


class HeadlessRefused(RuntimeError):
    """A headless spawn was refused. The message never contains the URL."""


# ---------------------------------------------------------------------------
# Reading the variable
# ---------------------------------------------------------------------------

def _registry_value(os_name: str | None = None) -> str | None:
    """HKCU\\Environment's value: the string, "" if absent, None if unreadable.

    Guarded by `os.name` BEFORE `winreg` is touched, so this imports and runs
    on a Linux runner (where it answers None and the env fallback applies).
    """
    if (os_name or os.name) != "nt":
        return None
    try:
        import winreg
    except ImportError:
        return None
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as key:
            value, kind = winreg.QueryValueEx(key, VAR)
    except FileNotFoundError:
        return ""
    except OSError:
        return None
    value = str(value or "")
    if kind == getattr(winreg, "REG_EXPAND_SZ", -1):
        value = winreg.ExpandEnvironmentStrings(value)
    return value


def read_base_url(registry_reader=None, environ=None) -> str | None:
    """The configured base URL, or None when it is unset.

    Registry first. A readable registry is AUTHORITATIVE, including when it says
    the value is absent - see the module docstring for why a stale inherited
    copy must not answer for a deleted variable.
    """
    reader = registry_reader if registry_reader is not None else _registry_value
    env = os.environ if environ is None else environ
    reg = reader()
    if reg is not None:
        return reg.strip() or None
    return (env.get(VAR) or "").strip() or None


def _tcp_probe(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=CONNECT_TIMEOUT_S):
            return True
    except OSError:
        return False


def _target(url: str) -> tuple[str, int]:
    """(host, port) from the URL, or HeadlessRefused. Never echoes the URL."""
    try:
        parts = urlsplit(url)
    except ValueError:
        raise HeadlessRefused(f"{VAR} is not a parseable URL") from None
    scheme = (parts.scheme or "").lower()
    if scheme not in ("http", "https"):
        raise HeadlessRefused(f"{VAR} scheme is not http or https")
    host = (parts.hostname or "").lower()
    if host not in LOOPBACK:
        raise HeadlessRefused(f"{VAR} host is not loopback")
    try:
        port = parts.port
    except ValueError:
        raise HeadlessRefused(f"{VAR} port is not a valid number") from None
    if port is None:
        port = 443 if scheme == "https" else 80
    return host, port


def resolve(registry_reader=None, environ=None, probe=None) -> str:
    """The URL a headless child must use. Raises HeadlessRefused otherwise."""
    url = read_base_url(registry_reader=registry_reader, environ=environ)
    if not url:
        raise HeadlessRefused(f"{VAR} unset")
    host, port = _target(url)
    if not (probe or _tcp_probe)(host, port):
        raise HeadlessRefused(f"connect refused {host}:{port}")
    return url


def child_env(base: dict | None = None, **seams) -> dict:
    """A COPY of `base` (default os.environ) with ANTHROPIC_BASE_URL set."""
    url = resolve(**seams)
    env = dict(os.environ if base is None else base)
    env[CHILD_VAR] = url
    return env


def describe(**seams) -> str:
    """host:port of the resolved target - the only form that may be printed."""
    host, port = _target(resolve(**seams))
    return f"[{host}]:{port}" if ":" in host else f"{host}:{port}"


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

def log_refusal(caller: str, reason: str, log_dir: Path | None = None) -> None:
    """Append ONE line to logs/YYYY-MM-DD.log. Never raises.

    Append rather than tmp-replace: this is the shared append-only daily log,
    and a whole-file rewrite is the one operation that could lose lines another
    writer already landed.
    """
    safe = _URLISH.sub("[url]", f"{caller}: headless spawn refused: {reason}")
    now = dt.datetime.now()
    line = f"{now:%Y-%m-%d %H:%M:%S} lw_headless_env {safe}\n"
    target_dir = Path(log_dir) if log_dir is not None else LOG_DIR
    try:
        target_dir.mkdir(parents=True, exist_ok=True)
        with open(target_dir / f"{now:%Y-%m-%d}.log", "a", encoding="utf-8") as fh:
            fh.write(line)
    except OSError:
        pass


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _std(stream):
    """`stream` if it has a real OS handle to hand down, else None."""
    try:
        stream.flush()
        stream.fileno()
    except (AttributeError, OSError, ValueError):
        return None
    return stream


def _exec(argv: list[str], env: dict) -> int:
    """Run argv with the gated env and this process's stdio, return its code.

    The std handles are passed EXPLICITLY. CREATE_NO_WINDOW gives the child a
    console of its own that nobody can see, so leaving inheritance implicit
    sent the child's output there - measured 2026-10-02: a child printing 42
    under `exec ... | cat` produced nothing at all. Explicit handles make the
    child write to whatever this process writes to (a pipe, a file, a console).
    """
    exe = shutil.which(argv[0], path=env.get("PATH")) or argv[0]
    try:
        return subprocess.run([exe, *argv[1:]], env=env, creationflags=NO_WINDOW,
                              stdin=_std(sys.stdin), stdout=_std(sys.stdout),
                              stderr=_std(sys.stderr)).returncode
    except OSError as exc:
        print(f"lw_headless_env: could not start {argv[0]}: {type(exc).__name__}",
              file=sys.stderr)
        return 127


def main(argv: list[str] | None = None, *, log_dir: Path | None = None, **seams) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check", help="print OK host:port or REFUSED reason")
    ex = sub.add_parser("exec", help="run argv through the proxy, or refuse")
    ex.add_argument("argv", nargs=argparse.REMAINDER)
    args = ap.parse_args(argv)

    if args.cmd == "check":
        try:
            print(f"OK {describe(**seams)}")
        except HeadlessRefused as exc:
            print(f"REFUSED {exc}")
            return REFUSED_EXIT
        return 0

    child = list(args.argv)
    if child and child[0] == "--":
        child = child[1:]
    if not child:
        print("lw_headless_env exec: no command given after --", file=sys.stderr)
        return 2
    try:
        env = child_env(**seams)
    except HeadlessRefused as exc:
        print(f"lw_headless_env: REFUSED {exc}", file=sys.stderr)
        log_refusal(f"exec {Path(child[0]).name}", str(exc), log_dir=log_dir)
        return REFUSED_EXIT
    return _exec(child, env)


if __name__ == "__main__":
    raise SystemExit(main())
