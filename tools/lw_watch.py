"""Watcher primitive: baseline first, advance only after delivery, alert once on rot.

# arch: shared "wake on new item" core for scheduled watchers (responder, CI watchdog)

WHY (ingest directive P0-2). The inbox responder ("what did I already answer")
and the CI watchdog ("settled failure already handled") each re-implemented a
part of this, and a SILENT source - an expired token, a moved endpoint, a
missing directory - looked identical to a QUIET one. One run of `run_source`:

  (a) the FIRST run for a source records what exists and sends nothing, so
      history is never replayed as news (`baseline=False` for a STATE-shaped
      source such as "is main red right now", where the current value is not
      history - the caller says so explicitly);
  (b) the seen-set advances ONLY for items the deliver step confirmed - a
      closed target, a failed or raising send re-offers the same items next
      run. `confirm(ids)` persists at once, for a deliver that handles items
      one at a time and may die mid-batch;
  (c) `watch_lock` - a lock DIRECTORY plus a pid file - stops overlapping
      runs; a lock whose pid is dead is taken over. Liveness is the process
      table (OpenProcess), never an mtime;
  (d) consecutive fetch failures are counted per source; at `alert_after` in
      a row exactly ONE alert is sent (a failed alert send is retried next
      run), and the counter resets on the next successful fetch;
  (e) nothing is sent and nothing is written when nothing changed.

Outcomes: baseline | nothing-new | delivered | deliver-failed | fetch-failed.

`deliver(items, confirm)` is injected (a fleet-kit spawn, a sync-inbox note,
a task-engine notification) and returns a structured result: True (all),
a list of ids, or {"delivered": [...]}; anything else - False, None, a raise -
delivers nothing. `fetch()` returns the source's CURRENT item ids; a raise or
None is a fetch failure, never an empty source.

State: `WatchState(path)` - {"sources": {name: {"seen", "failures",
"alerted"}}}, atomic tmp+replace, seen pruned to the live source and bounded by
`max_seen`. `FlatSeenState(path)` - the inbox responder's legacy single-source
{"seen": [...]} file, kept byte-compatible (counters ride as extra keys).
Coverage: tests/test_lw_watch.py.
"""
from __future__ import annotations

import contextlib
import json
import os
import time
from pathlib import Path

MAX_SEEN = 5000
ALERT_AFTER = 5


class FetchFailed(RuntimeError):
    """A fetch that could not observe the source (distinct from an empty one)."""


class LockBusy(RuntimeError):
    """A live process holds the lock."""


# ---------------------------------------------------------------------------
# Lock (c)
# ---------------------------------------------------------------------------

def pid_alive(pid: int) -> bool:
    """True when `pid` names a running process. Never judged by a file's mtime."""
    if not isinstance(pid, int) or pid <= 0:
        return False
    if os.name == "nt":
        import ctypes
        from ctypes import wintypes
        k32 = ctypes.WinDLL("kernel32", use_last_error=True)
        k32.OpenProcess.restype = wintypes.HANDLE
        k32.OpenProcess.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
        handle = k32.OpenProcess(0x1000, False, pid)  # QUERY_LIMITED_INFORMATION
        if not handle:
            # ERROR_ACCESS_DENIED (5): it exists but belongs to someone else.
            return ctypes.get_last_error() == 5
        try:
            code = wintypes.DWORD()
            if not k32.GetExitCodeProcess(handle, ctypes.byref(code)):
                return True
            return code.value == 259  # STILL_ACTIVE
        finally:
            k32.CloseHandle(handle)
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


@contextlib.contextmanager
def watch_lock(lock_dir: Path, *, wait_s: float = 0.0, pid: int | None = None,
               alive=pid_alive):
    """Hold `lock_dir` (a directory + `pid` file) for the body.

    mkdir is the atomic step. A lock whose recorded pid is dead - or whose pid
    file is unreadable - is taken over; a live pid blocks, raising LockBusy
    once `wait_s` has passed.
    """
    lock_dir = Path(lock_dir)
    lock_dir.parent.mkdir(parents=True, exist_ok=True)
    me = os.getpid() if pid is None else pid
    deadline = time.monotonic() + wait_s
    while True:
        try:
            lock_dir.mkdir()
            break
        except FileExistsError:
            holder = _read_pid(lock_dir)
            if holder is None or not alive(holder):
                _break_lock(lock_dir)
                continue
            if time.monotonic() >= deadline:
                raise LockBusy(f"lock held by live pid {holder}") from None
            time.sleep(0.05)
    try:
        (lock_dir / "pid").write_text(str(me), encoding="ascii")
        yield
    finally:
        _break_lock(lock_dir)


def _read_pid(lock_dir: Path) -> int | None:
    for _ in range(2):
        try:
            return int((lock_dir / "pid").read_text(encoding="ascii").strip())
        except (OSError, ValueError):
            # mkdir landed but the pid file is not written yet: give it a moment.
            time.sleep(0.05)
    return None


def _break_lock(lock_dir: Path) -> None:
    with contextlib.suppress(OSError):
        (lock_dir / "pid").unlink()
    with contextlib.suppress(OSError):
        lock_dir.rmdir()


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------

def _atomic_json(path: Path, doc: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(doc, indent=2), encoding="utf-8")
    tmp.replace(path)


def _read_json(path: Path) -> dict | None:
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return doc if isinstance(doc, dict) else None


class WatchState:
    """Multi-source state file. `get(source)` is None until the source baselines."""

    def __init__(self, path: Path, max_seen: int = MAX_SEEN):
        self.path = Path(path)
        self.max_seen = max_seen

    def get(self, source: str) -> dict | None:
        doc = _read_json(self.path) or {}
        rec = (doc.get("sources") or {}).get(source)
        return dict(rec) if isinstance(rec, dict) else None

    def put(self, source: str, rec: dict) -> None:
        doc = _read_json(self.path) or {}
        sources = doc.get("sources") if isinstance(doc.get("sources"), dict) else {}
        sources[source] = {**rec, "seen": list(rec["seen"])[-self.max_seen:]}
        _atomic_json(self.path, {"sources": sources})


class FlatSeenState:
    """The legacy one-source {"seen": [...]} file. Absent file = not baselined."""

    def __init__(self, path: Path, max_seen: int = MAX_SEEN):
        self.path = Path(path)
        self.max_seen = max_seen

    def get(self, source: str) -> dict | None:
        if not self.path.exists():
            return None
        doc = _read_json(self.path) or {}
        return {"seen": list(doc.get("seen") or []),
                "failures": int(doc.get("fetch_failures") or 0),
                "alerted": bool(doc.get("alerted")),
                "unbaselined": bool(doc.get("unbaselined"))}

    def put(self, source: str, rec: dict) -> None:
        doc = {"seen": sorted(rec["seen"])[-self.max_seen:]}
        if rec.get("failures"):
            doc["fetch_failures"] = rec["failures"]
        if rec.get("alerted"):
            doc["alerted"] = True
        if rec.get("unbaselined"):
            doc["unbaselined"] = True
        _atomic_json(self.path, doc)


# ---------------------------------------------------------------------------
# One run
# ---------------------------------------------------------------------------

def _delivered_ids(result, items: list[str]) -> list[str]:
    if result is True:
        return list(items)
    if isinstance(result, dict):
        result = result.get("delivered")
        if result is True:
            return list(items)
    if isinstance(result, (list, tuple, set)):
        wanted = set(items)
        return [i for i in result if i in wanted]
    return []


def run_source(state, source: str, fetch, describe, deliver, *, alert=None,
               alert_after: int = ALERT_AFTER, baseline: bool = True,
               persist: bool = True, prune: bool = True) -> dict:
    """One watcher run for `source`. Returns {"source", "outcome", ...}; never raises
    for a fetch or deliver failure (a state-file write error still propagates)."""
    rec = state.get(source)
    out = {"source": source, "new": [], "delivered": [], "detail": ""}

    def save(r):
        if persist:
            state.put(source, r)

    # -- fetch ---------------------------------------------------------------
    try:
        items = fetch()
        if items is None:
            raise FetchFailed("fetch returned None")
        items = [str(i) for i in items]
    except Exception as exc:  # noqa: BLE001 - every fetch failure is counted
        r = dict(rec) if rec is not None else {"seen": [], "failures": 0, "alerted": False,
                                                 "unbaselined": True}
        r["failures"] = int(r.get("failures") or 0) + 1
        detail = f"{type(exc).__name__}: {exc}".splitlines()[0][:200]
        if alert is not None and r["failures"] >= alert_after and not r.get("alerted"):
            try:
                ok, _adetail = alert(source, r["failures"], detail)
            except Exception:  # noqa: BLE001 - an alert sink never raises into us
                ok = False
            r["alerted"] = bool(ok)
            out["alerted"] = bool(ok)
        if rec is not None or persist:
            save(r)
        out.update(outcome="fetch-failed", failures=r["failures"], detail=detail)
        return out

    live = set(items)
    if rec is None or rec.get("unbaselined"):
        if baseline:
            save({"seen": list(dict.fromkeys(items)), "failures": 0, "alerted": False})
            out.update(outcome="baseline", baselined=len(live))
            return out
        rec = {"seen": [], "failures": 0, "alerted": False}

    seen_list = list(rec.get("seen") or [])
    seen = set(seen_list)
    new = [i for i in dict.fromkeys(items) if i not in seen]
    out["new"] = [describe(i) for i in new]
    kept = [i for i in seen_list if i in live] if prune else seen_list
    recovered = bool(rec.get("failures")) or bool(rec.get("alerted"))
    base = {"seen": kept, "failures": 0, "alerted": False}

    if not new:
        if recovered or len(kept) != len(seen_list):
            save(base)
        out["outcome"] = "nothing-new"
        return out

    confirmed: list[str] = []

    def confirm(ids):
        fresh = [i for i in ids if i in set(new) and i not in confirmed]
        if not fresh:
            return
        confirmed.extend(fresh)
        save({**base, "seen": kept + confirmed})

    try:
        result = deliver(list(new), confirm)
        err = ""
    except Exception as exc:  # noqa: BLE001 - a failed send keeps the items
        result, err = None, f"{type(exc).__name__}: {exc}".splitlines()[0][:200]
    for i in _delivered_ids(result, new):
        if i not in confirmed:
            confirmed.append(i)
    if confirmed or recovered or len(kept) != len(seen_list):
        save({**base, "seen": kept + confirmed})
    out["delivered"] = list(confirmed)
    out["pending"] = [i for i in new if i not in confirmed]
    out["outcome"] = "delivered" if confirmed else "deliver-failed"
    out["detail"] = err
    return out
