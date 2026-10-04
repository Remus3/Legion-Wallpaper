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
  (c) `watch_lock` - a lock DIRECTORY holding the pid, created by renaming a
      temp dir that already holds it onto the lock path - stops overlapping
      runs; a dead or pid-less holder is renamed aside and the take retried;
      release only while the lock still holds our pid. Liveness is the
      process table (OpenProcess + GetExitCodeProcess), never an mtime and
      never os.kill(pid, 0) on Windows;
  (d) consecutive fetch failures are counted per source; at `alert_after` in
      a row exactly ONE alert is sent (a failed alert send is retried next
      run), and the counter resets on the next successful fetch;
  (e) nothing is sent and nothing is written when nothing changed.

Outcomes: baseline | nothing-new | delivered | deliver-failed | fetch-failed.

CONTRACT = MAIN 0020 section 4 (operator order via MAIN, sha256 MATCH), so the
v5 swap to the kit's fleet_watch is a changed import:
run_source(state, source, fetch, deliver, alert=None, alert_after=5,
describe=None) -> {source, outcome, new, detail}. `deliver(items)` is injected
(a fleet-kit spawn, a sync-inbox note, a task-engine notification); ONLY a dict
whose "delivered" is exactly True advances state. LW EXTENSIONS, keyword-only
and offered to the kit as tests: "delivered" as a list of ids (per-item
partial delivery), `confirm_arg=True` (deliver(items, confirm) - confirm(ids)
persists at once, for a sender whose items take an hour each), `baseline=False`
(state-shaped sources), `persist=False` (dry runs), `prune`. `fetch()` returns
the source's CURRENT item ids; a raise or None is a fetch failure, never an
empty source. A corrupt state file RAISES WatchStateCorrupt and is never
rewritten.

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
def watch_lock(lock_dir: Path, *, pid: int | None = None, pid_alive=pid_alive,
               wait_s: float = 0.0, alive=None):
    """Hold `lock_dir` (a DIRECTORY holding a `pid` file) for the body.

    MAIN 0020 section 4 contract: the lock is created atomically - a temp dir
    that already holds our pid is RENAMED onto the lock path, so no observer
    ever sees a pid-less lock of ours; a dead or pid-less holder is taken over
    by renaming it ASIDE and retrying; the lock is released only while it
    still holds our pid. A live holder blocks (LockBusy once `wait_s` passed).
    `alive` is the pre-0020 name of `pid_alive`, kept for callers.
    """
    check = alive if alive is not None else pid_alive
    lock_dir = Path(lock_dir)
    lock_dir.parent.mkdir(parents=True, exist_ok=True)
    me = os.getpid() if pid is None else pid
    deadline = time.monotonic() + wait_s
    while True:
        tmp = lock_dir.with_name(f"{lock_dir.name}.{me}.{time.monotonic_ns()}.tmp")
        tmp.mkdir()
        (tmp / "pid").write_text(str(me), encoding="ascii")
        try:
            tmp.rename(lock_dir)
            break
        except OSError:
            _remove_dir(tmp)
            if not lock_dir.exists():
                continue
            holder = _read_pid(lock_dir)
            if holder is None or not check(holder):
                aside = lock_dir.with_name(f"{lock_dir.name}.stale.{time.monotonic_ns()}")
                with contextlib.suppress(OSError):
                    lock_dir.rename(aside)
                    _remove_dir(aside)
                continue
            if time.monotonic() >= deadline:
                raise LockBusy(f"lock held by live pid {holder}") from None
            time.sleep(0.05)
    try:
        yield
    finally:
        if _read_pid(lock_dir) == me:
            _remove_dir(lock_dir)


def _read_pid(lock_dir: Path) -> int | None:
    try:
        return int((lock_dir / "pid").read_text(encoding="ascii").strip())
    except (OSError, ValueError):
        return None


def _remove_dir(d: Path) -> None:
    with contextlib.suppress(OSError):
        (d / "pid").unlink()
    with contextlib.suppress(OSError):
        d.rmdir()


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------

def _atomic_json(path: Path, doc: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(doc, indent=2), encoding="utf-8")
    tmp.replace(path)


class WatchStateCorrupt(RuntimeError):
    """The state file exists but is not a JSON object. Raised, never rewritten
    (MAIN 0020 section 4): silently restarting from empty would replay every
    item as news, or - worse - re-baseline over a real backlog."""


def _read_json(path: Path) -> dict | None:
    """The state document; None only when the file is ABSENT."""
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return None
    except OSError as exc:
        raise WatchStateCorrupt(f"{path.name} unreadable ({type(exc).__name__})") from None
    try:
        doc = json.loads(text)
    except ValueError:
        raise WatchStateCorrupt(f"{path.name} is not JSON") from None
    if not isinstance(doc, dict):
        raise WatchStateCorrupt(f"{path.name} is not a JSON object")
    return doc


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
        doc = _read_json(self.path)
        if doc is None:
            return None
        # Present-but-empty (ingest P2-5): `{}` is not a baseline this class
        # ever writes, and reading it as "seen nothing" would make the whole
        # inbox new. Only a real list counts.
        if not isinstance(doc.get("seen"), list):
            raise WatchStateCorrupt(f"{self.path.name} has no seen list")
        return {"seen": list(doc["seen"]),
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
    """MAIN 0020: only a dict whose "delivered" is exactly True advances (all
    items). LW extension, offered to the kit as a test: "delivered" as a LIST
    of ids advances exactly those (per-item partial delivery). Anything else -
    a bare True, a list, False, None - advances nothing."""
    if not isinstance(result, dict):
        return []
    got = result.get("delivered")
    if got is True:
        return list(items)
    if isinstance(got, list):
        wanted = set(items)
        return [i for i in got if i in wanted]
    return []


def run_source(state, source: str, fetch, deliver, alert=None,
               alert_after: int = ALERT_AFTER, describe=None, *, baseline: bool = True,
               persist: bool = True, prune: bool = True, confirm_arg: bool = False) -> dict:
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
        # An unbaselined record may still carry failure counters: mark it
        # recovered so the reset below is written.
        rec = {"seen": [], "failures": int((rec or {}).get("failures") or 0),
               "alerted": bool((rec or {}).get("alerted"))}

    seen_list = list(rec.get("seen") or [])
    seen = set(seen_list)
    new = [i for i in dict.fromkeys(items) if i not in seen]
    out["new"] = [describe(i) for i in new] if describe is not None else list(new)
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
        result = deliver(list(new), confirm) if confirm_arg else deliver(list(new))
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
