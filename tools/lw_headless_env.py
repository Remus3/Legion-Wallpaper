"""LW's binding of MAIN's fleet kit - the ONE path a headless `claude` starts by.

# arch: headless-claude spawn gate - thin adapter over ops/fleet_kit/fleet_headless.py (kit v4), fail closed

MAIN order (kit v3, 2026-10-03; kit v4 the same day): every headless `claude` this tree starts goes
through `fleet_headless.spawn(...)`, and LW's own proxy-env, probe, budget,
skip, status and console code is deleted - one path, the kit's. The kit lives
at `ops/fleet_kit/` byte-pinned by its MANIFEST; it is NEVER edited here (see
`tests/test_fleet_kit_conformance.py`). `ops/` is not a package, so the kit is
bound BY PATH and an already-loaded copy is reused, exactly as the loop binds
this module.

WHAT THIS MODULE STILL CARRIES, AND WHY. Since kit v4 `kit.spawn` takes cwd,
stdin, return_stderr, session id / resume, an exact model, effort high, the
setting sources, a streamed log and a halt file, and kills the process tree on
a timeout - so the CI watchdog's worktree fix and the loop oracle run through
`spawn` below. Two LW paths still cannot: the loop executor needs the FULL
result event (structured_output, session_id, is_error) while spawn returns only
its `result` text, and a live-console .ps1 run is hours long on this process's
stdio. For those this module gives the kit's PRIMITIVES, never a copy of them:

  * `child_env` / `resolve` - `kit.base_url` (registry first; a readable
    registry WITHOUT the value is the kill switch), `kit.check_url` (plain
    http, loopback, explicit port), `kit.probe`, `kit.child_env`.
  * `start_run` / `end_run` - the kit's own pre- and post-launch accounting,
    in kit.spawn's order: `RunBudget.start()` under the kit's lock (cap reached
    writes the "limit" status; an unreadable budget file or a busy lock writes
    "refused" - both raise, fail closed), "running" status, then one
    `usage_line` appended to the kit's usage log and the "idle" status.
  * `LEAN_ARGS` - read off `kit.build_argv` with LW's `SETTING_SOURCES`, so the
    non-bare flag set exists once, in the kit.

`bare` is False on every LW path and `floors_in_hooks=True` is passed on every
`spawn`: LW's floors live in hooks (`.claude/settings.json` PreToolUse
`precommit_gate.py`, `text_first_guard.py`), `--bare` skips every hook, and the
kit then refuses `--bare` outright.

`SETTING_SOURCES` is `project` alone (kit v4 parameter): LW measured it at
47,026 input tokens against 53,143 for `project,local`, and this tree's local
scope re-enables three plugins and pins a model alias the proxy answers 404.

`FLEET_ROOT` is where the kit's status, budget and usage files live
(`ops/loop/control/`, gitignored). Tests redirect it; production never does.

CLI:
    python tools/lw_headless_env.py check
        OK <host>:<port> and exit 0, or REFUSED <reason> and exit 78.
    python tools/lw_headless_env.py spawn --note N --prompt-file F [--writes-code]
                                          [--timeout S] [-- extra...]
        kit.spawn, synchronous. Prints the usage line (with `result`) as JSON
        and exits with the child's code; 78 on refusal, 124 on timeout.
    python tools/lw_headless_env.py exec -- <argv...>
        For a run kit.spawn cannot carry (live console, hours long). The kit's
        gate and accounting around argv, run with this process's stdio. A bare
        `claude` argv[0] resolves through `kit.claude_exe`.
"""
from __future__ import annotations

import argparse
import datetime as dt
import importlib.util
import json
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KIT_PATH = ROOT / "ops" / "fleet_kit" / "fleet_headless.py"
LOG_DIR = ROOT / "logs"
CODE = "LW"
REFUSED_EXIT = 78  # EX_CONFIG
TIMEOUT_EXIT = 124

# Where the kit's status / budget / usage files live. A module attribute so the
# suite can point it at a tmp dir; nothing in production reassigns it.
FLEET_ROOT = ROOT


def _bind_kit():
    """The vendored kit, bound by path; an already-loaded copy is reused."""
    mod = sys.modules.get("fleet_headless")
    if mod is not None:
        return mod
    spec = importlib.util.spec_from_file_location("fleet_headless", KIT_PATH)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


kit = _bind_kit()
VAR = kit.VAR
HeadlessRefused = kit.Refused


# LW's setting scope for every headless child (see the module docstring).
SETTING_SOURCES = "project"


def _lean_args() -> tuple:
    """The kit's non-bare flags, read off its own argv builder."""
    argv = kit.build_argv("<exe>", "<prompt>", "<model>", "<effort>",
                          setting_sources=SETTING_SOURCES)
    return tuple(argv[argv.index("<effort>") + 1:])


LEAN_ARGS = _lean_args()

# The same expression the kit uses for its own spawn. Only the `exec` path
# below launches anything itself; every other caller hands this to Popen/run.
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0) if sys.platform == "win32" else 0

_URLISH = re.compile(r"[A-Za-z][A-Za-z0-9+.-]*://\S*")


# ---------------------------------------------------------------------------
# The gate - kit primitives only
# ---------------------------------------------------------------------------

def resolve(url_source=None, connect=None) -> str:
    """The proxy URL a headless child must use, or kit.Refused. Never echoes it."""
    url = (url_source or kit.base_url)()
    host, port = kit.check_url(url)
    if connect is None:
        kit.probe(host, port)
    else:
        kit.probe(host, port, connect=connect)
    return url


def child_env(base: dict | None = None, *, bare: bool = False, url_source=None,
              connect=None) -> dict:
    """The kit's child env (credentials stripped, proxy URL set), a COPY of base."""
    return kit.child_env(resolve(url_source, connect), bare=bare, parent=base)


def describe(url_source=None, connect=None) -> str:
    """host:port of the resolved target - the only form that may be printed."""
    host, port = kit.check_url(resolve(url_source, connect))
    return f"[{host}]:{port}" if ":" in host else f"{host}:{port}"


def claude_exe(which=None) -> str:
    """kit.claude_exe - the real binary behind the npm shim when it exists."""
    return kit.claude_exe() if which is None else kit.claude_exe(which=which)


def spawn(prompt: str, *, note: str = "", writes_code: bool = False, bare: bool = False,
          rules_file=None, timeout: float = 3600, extra=(), **params) -> dict:
    """kit.spawn for LW: FLEET_ROOT, code LW, floors in hooks, project scope.

    Raises kit.Refused before any launch. `params` reaches kit.spawn's v4
    options (cwd, stdin, return_stderr, persist, session_id, resume, model,
    effort, log_path, halt_file) and its test seams (url_source, connect, run,
    exe_source). A timeout does NOT raise: the kit kills the process tree and
    returns a line with rc None and error "timeout".
    """
    params.setdefault("setting_sources", SETTING_SOURCES)
    return kit.spawn(FLEET_ROOT, CODE, prompt, note=note, writes_code=writes_code,
                     bare=bare, rules_file=rules_file, timeout=timeout,
                     extra=tuple(extra), floors_in_hooks=True, **params)


# ---------------------------------------------------------------------------
# Accounting for the paths kit.spawn cannot carry - kit.spawn's own sequence
# ---------------------------------------------------------------------------

def budget():
    return kit.RunBudget(Path(FLEET_ROOT) / kit.BUDGET_REL)


def can_start() -> bool:
    """The kit's rolling-window check, without recording a start."""
    return budget().can_start()


def start_run() -> float:
    """Count one start under the kit's lock, then status "running".

    kit.spawn's own order: `RunBudget.start()` False = cap reached (status
    "limit"); Refused = unreadable budget file or busy lock (status "refused").
    Both raise HeadlessRefused - fail closed, nothing is launched.
    """
    b = budget()
    try:
        counted = b.start()
    except HeadlessRefused:
        kit.write_status(FLEET_ROOT, CODE, "refused", "Refused", None, b)
        raise
    if not counted:
        kit.write_status(FLEET_ROOT, CODE, "limit", "Turn Limit Reached", None, b)
        raise HeadlessRefused(f"run budget exhausted ({b.used()}/{b.cap})")
    started = time.time()
    kit.write_status(FLEET_ROOT, CODE, "running", "Running Session", started, b)
    return started


def end_run(started: float, *, note: str, model: str, effort: str, rc,
            stdout: str | None = None, bare: bool = False,
            error: str | None = None) -> dict:
    """One kit usage line appended, status back to "idle". Returns the line."""
    try:
        result = json.loads(stdout) if stdout else None
    except (ValueError, TypeError):
        result = None
    if not isinstance(result, dict):
        result = None
    line = kit.usage_line(result, CODE, note, model, effort, bare, rc,
                          time.time() - started, error)
    log = Path(FLEET_ROOT) / kit.USAGE_REL
    log.parent.mkdir(parents=True, exist_ok=True)
    with open(log, "a", encoding="ascii", newline="\n") as fh:
        fh.write(json.dumps(line) + "\n")
    kit.write_status(FLEET_ROOT, CODE, "idle", "Idle", time.time(), budget())
    return line


def _flag(argv: list, name: str) -> str:
    try:
        return str(argv[argv.index(name) + 1])
    except (ValueError, IndexError):
        return ""


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

def log_refusal(caller: str, reason: str, log_dir: Path | None = None) -> None:
    """Append ONE line to logs/YYYY-MM-DD.log. Never raises, never logs a URL.

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
    under `exec ... | cat` produced nothing at all.
    """
    try:
        return subprocess.run(argv, env=env, creationflags=NO_WINDOW,
                              stdin=_std(sys.stdin), stdout=_std(sys.stdout),
                              stderr=_std(sys.stderr)).returncode
    except OSError as exc:
        print(f"lw_headless_env: could not start {argv[0]}: {type(exc).__name__}",
              file=sys.stderr)
        return 127


def _strip_dashdash(rest: list) -> list:
    rest = list(rest)
    return rest[1:] if rest and rest[0] == "--" else rest


def main(argv: list[str] | None = None, *, log_dir: Path | None = None,
         url_source=None, connect=None, run=None, exe_source=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check", help="print OK host:port or REFUSED reason")
    sp = sub.add_parser("spawn", help="one synchronous kit.spawn run")
    sp.add_argument("--note", default="")
    sp.add_argument("--prompt-file", type=Path, required=True)
    sp.add_argument("--writes-code", action="store_true")
    sp.add_argument("--timeout", type=float, default=3600.0)
    sp.add_argument("extra", nargs=argparse.REMAINDER)
    ex = sub.add_parser("exec", help="run argv through the kit's gate, or refuse")
    ex.add_argument("argv", nargs=argparse.REMAINDER)
    args = ap.parse_args(argv)
    seams = {"url_source": url_source, "connect": connect}

    if args.cmd == "check":
        try:
            print(f"OK {describe(**seams)}")
        except HeadlessRefused as exc:
            print(f"REFUSED {exc}")
            return REFUSED_EXIT
        return 0

    if args.cmd == "spawn":
        prompt = args.prompt_file.read_text(encoding="utf-8")
        kw = {k: v for k, v in {"url_source": url_source, "connect": connect,
                                "run": run, "exe_source": exe_source}.items()
              if v is not None}
        try:
            line = spawn(prompt, note=args.note, writes_code=args.writes_code,
                         timeout=args.timeout, extra=_strip_dashdash(args.extra), **kw)
        except HeadlessRefused as exc:
            print(f"lw_headless_env: REFUSED {exc}", file=sys.stderr)
            log_refusal(f"spawn {args.note or 'note'}", str(exc), log_dir=log_dir)
            return REFUSED_EXIT
        print(json.dumps(line))
        if line.get("error") == "timeout":
            print(f"lw_headless_env: timeout after {args.timeout:.0f}s", file=sys.stderr)
            return TIMEOUT_EXIT
        rc = line.get("rc")
        return rc if isinstance(rc, int) else 1

    child = _strip_dashdash(args.argv)
    if not child:
        print("lw_headless_env exec: no command given after --", file=sys.stderr)
        return 2
    try:
        env = child_env(**seams)
        if Path(child[0]).stem.lower() == "claude" and not Path(child[0]).is_absolute():
            child[0] = (exe_source or claude_exe)()
        started = start_run()
    except HeadlessRefused as exc:
        print(f"lw_headless_env: REFUSED {exc}", file=sys.stderr)
        log_refusal(f"exec {Path(child[0]).name}", str(exc), log_dir=log_dir)
        return REFUSED_EXIT
    rc = _exec(child, env)
    try:
        end_run(started, note=f"exec {Path(child[0]).stem}", model=_flag(child, "--model"),
                effort=_flag(child, "--effort"), rc=rc)
    except OSError as exc:
        print(f"lw_headless_env: usage line not written: {type(exc).__name__}",
              file=sys.stderr)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
