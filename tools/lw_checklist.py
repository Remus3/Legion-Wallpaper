# arch: session checklist (FLEET-COMMON item 13) - thin adapter over ops/fleet_kit/fleet_checklist.py (kit v7)
"""LW's binding of the kit's session checklist (FLEET-KIT v7, MAIN 0215).

FLEET-COMMON item 13: every session kind - interactive, headless lane, loop
tick, inbox responder - prints `Session <n> checklist` at start, reprints only
the remaining tasks after every 4 completions, and runs /done unprompted when
none remain. A headless fire also writes the remaining list into its item-12
progress file as "checklist".

  session-start   SessionStart hook: the block from the hand-off. n is the
                  hand-off's `SESSION: <n>` line (tools/lw_next_session.py
                  writes n+1 at every /done); the tasks are its `CHECKLIST:`
                  section (`  - <ID>: <task>`), else its Task line. Exit 0
                  always: a hook must never block a session start.
  progress        one item-12 progress write with the item-13d checklist,
                  for a spawned child (child_rule() tells it how).

Fire(...) is the in-process helper for the loop controller (one fire per
cycle, progress/lane-<i>.json in the MAIN checkout) and the inbox responder
(one fire per tick that has notes to run). It never raises: a progress write
that fails is a lost status line, never a failed fire.

The kit module is bound by path (ops/fleet_kit is not a package) and the
progress write is the kit's own fleet_headless.write_progress.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KIT_DIR = ROOT / "ops" / "fleet_kit"
HANDOFF_NAME = "LW-NEXT-SESSION.txt"

_SESSION = re.compile(r"^SESSION:\s*(\d+)\s*$", re.M)
_SECTION = re.compile(r"^[A-Z][A-Za-z -]*:")
_ITEM = re.compile(r"^\s+-\s+([A-Za-z0-9][A-Za-z0-9._-]{0,15}):\s+(.+?)\s*$")
_TASK = re.compile(r"^Task:\s*(.+?)\s*$", re.M)

HOOK_RULE = (
    "FLEET-COMMON item 13: print the block above as your first chat output, "
    "adding or dropping tasks to match what this session will actually do "
    "(the operator's ask first). Reprint REMAINING tasks only after every 4 "
    "completions, new ones marked +. When none remain, run /done unprompted.")


def _bind(name: str, filename: str):
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, KIT_DIR / filename)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def kit_checklist():
    """The vendored kit's fleet_checklist.py."""
    return _bind("fleet_kit_checklist", "fleet_checklist.py")


def kit_headless():
    """The vendored kit's fleet_headless.py - the SAME module object
    tools/lw_headless_env.py binds (it registers it as `fleet_headless`)."""
    return _bind("fleet_headless", "fleet_headless.py")


# ---------------------------------------------------------------- hand-off

def handoff_session(text: str) -> int | None:
    m = _SESSION.search(text or "")
    return int(m.group(1)) if m else None


def handoff_items(text: str) -> list[tuple[str, str]]:
    """(id, task) rows from the CHECKLIST: section; else the Task line as T1."""
    lines = (text or "").splitlines()
    items: list[tuple[str, str]] = []
    inside = False
    for ln in lines:
        if ln.startswith("CHECKLIST:"):
            inside = True
            continue
        if inside:
            if _SECTION.match(ln):
                break
            m = _ITEM.match(ln)
            if m:
                items.append((m.group(1), m.group(2)[: kit_checklist().TASK_MAX]))
    if items:
        return items
    m = _TASK.search(text or "")
    if m:
        return [("T1", m.group(1)[: kit_checklist().TASK_MAX])]
    return []


def session_start_block(text: str) -> str:
    kc = kit_checklist()
    n = handoff_session(text)
    rows = []
    for id_, task in handoff_items(text):
        try:
            rows.append(kc.item(id_, task))
        except ValueError:
            continue
    if n is None:
        body = kc.render(0, rows).splitlines()
        body[0] = "Session ? checklist"
        return "\n".join(body)
    return kc.Checklist(n, rows).start()


# ---------------------------------------------------------------- headless fire

class Fire:
    """One headless fire's checklist: logged at start and after every task,
    written into progress/<task>.json (remaining tasks only)."""

    def __init__(self, root, task: str, run_n: int, items, log=None, kit=None):
        self.root = Path(root)
        self.task = task
        self.kit = kit
        self.log = log or (lambda _text: None)
        kc = kit_checklist()
        self.cl = kc.Checklist(int(run_n), [kc.item(i, t) for i, t in items])
        self.total = max(1, len(self.cl.remaining()))
        self.step = "start"

    def _write(self, status: str, step: str | None = None, eta_s: int = 0):
        if step:
            self.step = step
        left = len(self.cl.remaining())
        pct = 100 if status == "done" else int(100 * (self.total - left) / self.total)
        try:
            (self.kit or kit_headless()).write_progress(
                self.root, self.task, pct, self.step, int(eta_s), status,
                checklist=self.cl.rows())
        except (OSError, ValueError):
            pass

    def _say(self, text):
        if not text:
            return
        try:
            self.log(text)
        except Exception:  # noqa: BLE001 - a log sink never breaks a fire
            pass

    def start(self):
        self._say(self.cl.start())
        self._write("running", "start")

    def running(self, id_: str, state: str, eta_s: int | None = None):
        try:
            self.cl.set_state(id_, state, eta_s)
        except (KeyError, ValueError):
            return
        self._write("running", f"{id_} {state}", eta_s or 0)

    def complete(self, id_: str):
        try:
            update = self.cl.complete(id_)
        except KeyError:
            return
        self._say(update)
        self._write("running", f"{id_} done")

    def close(self, status: str = "done", step: str | None = None):
        if status == "done":
            for r in self.cl.remaining():
                self.cl.complete(r["id"])
        self._write(status, step or status)


def child_rule(task: str, run_n: int) -> str:
    """The prompt line a spawned headless child gets (FLEET-COMMON item 13 d)."""
    return (
        f"FLEET-COMMON item 13: first print `Session {int(run_n)} checklist`, one "
        f"line per task you will do (`- <ID>: <task>`), last line `/done`; reprint "
        f"REMAINING tasks only after every 4 completions. At start and after every "
        f"task write it with `python tools/lw_checklist.py progress --task {task} "
        f"--pct <0-100> --step <ID> --eta <seconds> --status running|done|failed "
        f"--checklist '<json list of remaining {{id, task, state, eta_s}}>'`.")


# ---------------------------------------------------------------- CLI

def _out(text: str) -> None:
    data = (text + "\n").encode("utf-8")
    try:
        sys.stdout.buffer.write(data)
        sys.stdout.flush()
    except (AttributeError, OSError, ValueError):
        pass


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="LW session checklist (FLEET-COMMON item 13)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    ss = sub.add_parser("session-start")
    ss.add_argument("--root", type=Path, default=ROOT)
    pg = sub.add_parser("progress")
    pg.add_argument("--root", type=Path, default=ROOT)
    pg.add_argument("--task", required=True)
    pg.add_argument("--pct", type=int, required=True)
    pg.add_argument("--step", required=True)
    pg.add_argument("--eta", type=int, required=True)
    pg.add_argument("--status", choices=("running", "done", "failed"), required=True)
    pg.add_argument("--checklist", required=True)
    args = ap.parse_args(argv)

    if args.cmd == "session-start":
        try:
            text = (args.root / HANDOFF_NAME).read_text(encoding="utf-8", errors="replace")
        except OSError:
            text = ""
        try:
            block = session_start_block(text)
        except Exception as exc:  # noqa: BLE001 - a hook never blocks a session
            block = f"Session ? checklist\n(checklist unavailable: {type(exc).__name__})"
        _out("# Session checklist\n\n" + block + "\n\n" + HOOK_RULE)
        return 0

    try:
        rows = json.loads(args.checklist)
        kit_headless().write_progress(args.root, args.task, args.pct, args.step,
                                      args.eta, args.status, checklist=rows)
    except (ValueError, TypeError, OSError) as exc:
        print(f"lw_checklist progress: refused - {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
