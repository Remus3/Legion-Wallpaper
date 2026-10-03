"""LW's live inbox-responder status, the file the lane widget reads (MAIN 0915).

# arch: responder status publisher - one gitignored JSON per tree, schema 1

WHY. The operator asked for each tree's inbox responder to show as a live
service on the lane widget's ALL tab ("Sync: Idle [4m/5m][110/120]"). The
widget is a read-only observer of bounded, named paths, so every tree publishes
ONE file at the SAME relative path, `ops/loop/control/inbox_status.json`, and
the widget never writes it. MAIN 0915 fixed the schema; this module is LW's
writer for it and nothing else.

WHAT THE PARENT CAN SEE, AND WHAT IT CANNOT. `LW-InboxResponder` is a
five-minute tick that launches DETACHED children and exits. So:
  * "Running Session" is a PID probe at each tick over the children it
    launched, with a start-time guard: a child counts only while a process with
    its PID still exists AND was created within `START_SLACK_S` of the tick that
    launched it. A reused PID was created later, so it fails the guard.
  * A session's end is OBSERVED at the next tick, so every duration here has a
    one-tick granularity. "Idle" starts at the tick that saw the last child gone,
    which is an upper bound on when the run ended, never a guess inside it.
  * The finer names MAIN allows ("Running a Command", "Appending Ledger") need a
    streamed child; LW's children run with stdout at DEVNULL, so this module
    reports only the basic set and never refines.

LW's mapping onto MAIN's six states:
  halted   "Halted"              the kill switch file exists (outranks all)
  running  "Running Session"     a launched child is still alive
  running  "Checking Inbox"      transient, published at tick start only
  limit    "Turn Limit Reached"  the rolling-window budget is spent
  refused  "Backing Off"         this tick's spawns were all refused or could
                                 not launch; the notes stay unseen for a retry
  idle     "Idle"                otherwise
LW has no backoff timer, so it never publishes "backoff".

ETA = the median of the last 10 COMPLETED instances of the same task name, null
under 3. A completed instance is a contiguous run of one durable task. The
transient "Checking Inbox" never interrupts the durable task, so an idle period
spanning many ticks stays one instance and keeps its start.

Both files are gitignored per-host runtime: the published document under
`ops/loop/control/` and the writer's own memory (children, last task, duration
history) under `ops/runtime/inbox_responder/`. Writes are atomic (tmp + replace)
because the widget polls mid-write.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

STATUS_PATH = ROOT / "ops" / "loop" / "control" / "inbox_status.json"
STATE_PATH = ROOT / "ops" / "runtime" / "inbox_responder" / "status_state.json"

SCHEMA = 1
CODE = "LW"
TASKS = ("Idle", "Checking Inbox", "Waiting for Slot", "Running Session",
         "Delivering Notes", "Committing", "Backing Off", "Halted",
         "Turn Limit Reached")
TRANSIENT = "Checking Inbox"
RUNS_CAP = 120
WINDOW_S = 86400
ETA_SAMPLES = 10
ETA_MIN = 3
# Tick start to `Popen` for up to three spawns, proxy check included, is
# seconds; two minutes is generous and still far below any PID-reuse cycle.
START_SLACK_S = 120.0


def local_iso(moment: dt.datetime) -> str:
    """ISO-8601 in local time WITH its offset, to the second."""
    return moment.astimezone().replace(microsecond=0).isoformat()


def eta_s(durations: list[float]) -> int | None:
    """Median of the last ten completed durations; None under three. Never a guess."""
    recent = list(durations)[-ETA_SAMPLES:]
    if len(recent) < ETA_MIN:
        return None
    return int(round(statistics.median(recent)))


def _windows_alive(pid: int, spawned: float) -> bool:
    import ctypes
    from ctypes import wintypes

    k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    k32.OpenProcess.restype = wintypes.HANDLE
    k32.OpenProcess.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
    k32.GetExitCodeProcess.argtypes = (wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD))
    k32.GetProcessTimes.argtypes = (wintypes.HANDLE,) + (ctypes.POINTER(wintypes.FILETIME),) * 4
    k32.CloseHandle.argtypes = (wintypes.HANDLE,)
    query_limited, still_active = 0x1000, 259
    handle = k32.OpenProcess(query_limited, False, pid)
    if not handle:
        return False
    try:
        code = wintypes.DWORD()
        if not k32.GetExitCodeProcess(handle, ctypes.byref(code)) or code.value != still_active:
            return False
        times = [wintypes.FILETIME() for _ in range(4)]
        if not k32.GetProcessTimes(handle, *(ctypes.byref(t) for t in times)):
            return False
        ticks = (times[0].dwHighDateTime << 32) | times[0].dwLowDateTime
        created = ticks / 1e7 - 11644473600.0  # FILETIME epoch 1601 -> Unix
        return abs(created - spawned) <= START_SLACK_S
    finally:
        k32.CloseHandle(handle)


def pid_alive(pid: int, spawned: float) -> bool:
    """Is the child launched at `spawned` (Unix seconds) still running as `pid`?

    Windows: the process exists, has not exited, and was created within
    `START_SLACK_S` of `spawned` (the start-time guard against a reused PID).
    POSIX has no portable creation time, so there it is existence only - the
    responder is a Windows scheduled task and the POSIX branch serves CI.
    NEVER `os.kill` on Windows: there it terminates the process.
    """
    if pid <= 0:
        return False
    if os.name == "nt":
        return _windows_alive(pid, spawned)
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False
    return True


def write_atomic(path: Path, doc: dict) -> None:
    """tmp + replace, LF only, so a poller never reads half a document."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_bytes((json.dumps(doc, indent=2) + "\n").encode("ascii"))
    tmp.replace(path)


def load_state(path: Path | None = None) -> dict:
    """The writer's memory. Absent or unparseable starts fresh - it holds only
    durations and children, so losing it costs ETAs, never a wrong state."""
    try:
        state = json.loads((STATE_PATH if path is None else path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return state if isinstance(state, dict) else {}


def _window(spawn_times, now: dt.datetime, window_s: int) -> list[dt.datetime] | None:
    if spawn_times is None:
        return None
    cutoff = now - dt.timedelta(seconds=window_s)
    return sorted(t for t in spawn_times if t >= cutoff)


def _document(*, state: str, task: str, started: dt.datetime, eta: int | None,
              now: dt.datetime, next_tick: dt.datetime | None, counted, cap: int,
              window_s: int) -> dict:
    return {
        "schema": SCHEMA,
        "code": CODE,
        "updated": local_iso(now),
        "state": state,
        "task": task,
        "task_started": local_iso(started),
        "task_eta_s": eta,
        "next_tick": local_iso(next_tick) if next_tick else None,
        # None, not 0, when the run log could not be read: could-not-count is
        # not zero, the same rule the budget gate runs on.
        "runs_in_window": None if counted is None else len(counted),
        "runs_cap": cap,
        "window_s": window_s,
        "cap_frees_at": (local_iso(counted[0] + dt.timedelta(seconds=window_s))
                         if counted else None),
    }


def resolve(*, halted: bool, running: bool, runs: int | None, cap: int,
            refused: bool) -> tuple[str, str]:
    """MAIN's (state, task) for one tick. Order is the precedence."""
    if halted:
        return "halted", "Halted"
    if running:
        return "running", "Running Session"
    if runs is not None and runs >= cap:
        return "limit", "Turn Limit Reached"
    if refused:
        return "refused", "Backing Off"
    return "idle", "Idle"


def record(*, now: dt.datetime, next_tick: dt.datetime | None, halted: bool,
           refused: bool, spawn_times, new_children=(), probe=None,
           cap: int = RUNS_CAP, window_s: int = WINDOW_S) -> dict:
    """End-of-tick publish. Returns the document written.

    `spawn_times` is every AUTO spawn the run log holds plus this tick's, or
    None when the log could not be read. `new_children` is (pid, launched-at
    Unix seconds) for this tick's AUTO spawns. `probe` defaults to `pid_alive`,
    looked up at call time so a test can inject it.
    """
    probe = pid_alive if probe is None else probe
    prev = load_state()
    history = {k: list(v) for k, v in (prev.get("history") or {}).items()
               if isinstance(v, list)}
    children = [list(c) for c in prev.get("children") or [] if isinstance(c, list) and len(c) == 2]
    children += [[int(pid), float(at)] for pid, at in new_children]
    children = [c for c in children if probe(int(c[0]), float(c[1]))]

    checking = prev.get("checking_since")
    if checking:
        history.setdefault(TRANSIENT, []).append(
            max(0.0, (now - dt.datetime.fromisoformat(checking)).total_seconds()))

    counted = _window(spawn_times, now, window_s)
    state, task = resolve(halted=halted, running=bool(children),
                          runs=None if counted is None else len(counted),
                          cap=cap, refused=refused)
    started = now
    if prev.get("task") == task and prev.get("task_started"):
        started = dt.datetime.fromisoformat(prev["task_started"])
    elif prev.get("task") and prev.get("task_started"):
        done = (now - dt.datetime.fromisoformat(prev["task_started"])).total_seconds()
        history.setdefault(prev["task"], []).append(max(0.0, done))
    history = {k: v[-ETA_SAMPLES:] for k, v in history.items()}

    doc = _document(state=state, task=task, started=started, eta=eta_s(history.get(task, [])),
                    now=now, next_tick=next_tick, counted=counted, cap=cap, window_s=window_s)
    write_atomic(STATE_PATH, {"task": task, "task_started": started.isoformat(),
                              "children": children, "history": history})
    write_atomic(STATUS_PATH, doc)
    return doc


def announce(task: str, *, now: dt.datetime, spawn_times, next_tick: dt.datetime | None,
             cap: int = RUNS_CAP, window_s: int = WINDOW_S) -> dict:
    """Publish a TRANSIENT task (tick start) without ending the durable one."""
    prev = load_state()
    history = prev.get("history") or {}
    doc = _document(state="running", task=task, started=now,
                    eta=eta_s(history.get(task, [])), now=now, next_tick=next_tick,
                    counted=_window(spawn_times, now, window_s), cap=cap, window_s=window_s)
    write_atomic(STATE_PATH, {**prev, "checking_since": now.isoformat()})
    write_atomic(STATUS_PATH, doc)
    return doc
