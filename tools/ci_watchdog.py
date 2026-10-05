#!/usr/bin/env python
"""LW-CIWatchdog - unattended red-main CI auto-fixer.

One pass per invocation, then exit. The scheduled task (`LW-CIWatchdog`, at
startup + every 2 minutes) is the loop; this file deliberately is not, so a
wedged pass dies with its process instead of living forever.

Shape of a pass:

    HALT? -> lock -> check_ci(main) -> settled failure? -> isolated worktree
    -> headless `claude -p` fixes it there -> push branch -> open PR
    -> the PR's OWN CI must go green on its OWN head sha -> merge -> clean up

This tool can push and merge. Three rails, all tested in
`tests/test_ci_watchdog.py`:

  1. HALT is checked FIRST and answers everything. A kill switch that only works
     when the tool is otherwise healthy is not a kill switch.
     Kill: create `ops\\runtime\\ci_watchdog\\HALT`, or
     `Disable-ScheduledTask LW-CIWatchdog`.
  2. Ambiguity NEVER means act. `queued` / `pending` / `unavailable` /
     `not-evaluated` all WAIT; only a settled `failure` triggers a fix. That
     distinction is exactly what f1 item 12 built into `truth_gate.check_ci`,
     and this tool reuses that function rather than re-deriving it - an
     abbreviated sha reaching `gh run list` returns [] and would otherwise read
     as "nothing owed".
  3. The merge self-gates on the FIX BRANCH's own green CI AT ITS OWN HEAD SHA.
     A stale success from an earlier push to the same branch is the trap that
     turns one red main into two.

Per-sha attempt budget (default 2). A transient Anthropic condition (credit /
rate limit / overloaded) does NOT burn an attempt - same class the weekly-hygiene
wrapper already handles, and one bad afternoon must not exhaust the budget on a
repo that was never broken.

Every subprocess sets CREATE_NO_WINDOW: a console flashing on the operator's
desktop is a recurring real defect here, and this thing runs every 2 minutes.

Exit codes: 0 pass completed (including "nothing to do"), 1 pass failed, 2 usage.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATE_DIR = ROOT / "ops" / "runtime" / "ci_watchdog"
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)

HALT_FILE = "HALT"
LOCK_FILE = "lock.json"
STATE_FILE = "state.json"
# A fix pass (worktree + model + suite) runs far longer than the 2-minute
# trigger, so overlapping invocations are the DEFAULT, not an edge case. The
# stale window is generous enough that a slow-but-live pass is never stolen.
LOCK_STALE_S = 3600.0
MAX_ATTEMPTS = 2
BASE_BRANCH = "main"
# Poll budget for the fix branch's own CI. 40 * 30s = 20 minutes, comfortably
# past a normal run, and a timeout leaves the PR OPEN for the operator rather
# than merging it unverified.
PR_CI_POLLS = 40
PR_CI_INTERVAL_S = 30.0

_TRANSIENT = re.compile(
    r"credit balance is too low|rate[ _-]?limit|overloaded|too many requests"
    r"|status(?: code)? (?:429|529)|insufficient (?:credit|quota)",
    re.IGNORECASE)


def _bind_truth_gate():
    """Bind tools/truth_gate.py BY PATH - tools/ is not importable as a package."""
    spec = importlib.util.spec_from_file_location(
        "lw_ci_watchdog_truth_gate", ROOT / "tools" / "truth_gate.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _bind_headless_env():
    """Bind tools/lw_headless_env.py BY PATH, reusing an already-loaded copy.

    LW's binding of MAIN's fleet kit (kit v3): every headless claude this tool
    starts goes through the kit's gate and accounting, and a refusal means NO
    fix attempt - never a plain `claude` in its place. `kit.spawn` itself cannot
    carry this run: it runs with `cwd` = the tree whose ops/loop/control holds
    the budget and status files, and the fix must run in a throwaway worktree;
    it also returns no stderr, which the transient check reads.
    """
    if "lw_headless_env" in sys.modules:
        return sys.modules["lw_headless_env"]
    spec = importlib.util.spec_from_file_location(
        "lw_headless_env", ROOT / "tools" / "lw_headless_env.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


# ==========================================================================
# Pure decision logic - no network, no worktree, no model
# ==========================================================================
def halted(state_dir):
    """The HALT file's contents, or a generic reason if it is empty.

    An empty file still halts: `type nul > HALT` is the likeliest way an
    operator creates one under stress, and reading that as "no halt" would
    disarm the kill switch at exactly the moment it is being used.
    """
    p = Path(state_dir) / HALT_FILE
    if not p.is_file():
        return None
    try:
        body = p.read_text(encoding="utf-8", errors="replace").strip()
    except OSError:
        body = ""
    return body or "HALT file present"


def decide(ci, state, *, max_attempts=MAX_ATTEMPTS, halt=None):
    """What this pass should do. Returns {"action", "reason", "sha"}.

    Actions: halt | idle | wait | fix | give-up. Anything not understood WAITS -
    acting on an unrecognised status is how an auto-fixer starts inventing work.
    """
    if halt:
        return {"action": "halt", "reason": halt, "sha": None}
    status = (ci or {}).get("status")
    sha = (ci or {}).get("sha")
    if status in ("success", "not-evaluated"):
        return {"action": "idle", "reason": f"CI {status}", "sha": sha}
    if status != "failure":
        return {"action": "wait",
                "reason": f"CI {status!r} is not settled - not acting", "sha": sha}
    # The budget is PER SHA: a different failure deserves its own attempts, or
    # one exhausted sha wedges the watchdog forever.
    attempts = int(state.get("attempts", 0)) if state.get("sha") == sha else 0
    if attempts >= max_attempts:
        return {"action": "give-up",
                "reason": f"{attempts} attempts already spent on {sha[:8] if sha else '?'} "
                          f"(max {max_attempts}) - leaving it for the operator",
                "sha": sha}
    return {"action": "fix", "reason": f"CI failure on {sha[:8] if sha else '?'}",
            "sha": sha}


def bump_attempt(state, sha):
    """Attempt counter for `sha`. Pure - returns a new dict."""
    if state.get("sha") == sha:
        return {"sha": sha, "attempts": int(state.get("attempts", 0)) + 1}
    return {"sha": sha, "attempts": 1}


def branch_name(sha, attempt):
    return f"ci-fix/{(sha or 'unknown')[:8]}-{attempt}"


def merge_allowed(pr_ci, head_sha):
    """Merge only on the fix branch's OWN success at the head being merged.

    The sha equality is the load-bearing half. A success left over from an
    earlier push to the same branch is a real green for a commit nobody is
    merging, and taking it would put an unverified fix on main.
    """
    if not isinstance(pr_ci, dict):
        return False
    return pr_ci.get("status") == "success" and pr_ci.get("sha") == head_sha


def is_transient(text):
    """A vendor-side condition that is not a repo fault, so it must not burn an
    attempt. Same class the weekly-hygiene wrapper already detects."""
    return bool(_TRANSIENT.search(text or ""))


# ==========================================================================
# Single instance
# ==========================================================================
def acquire(state_dir, pid=None, now=None):
    """Take the pass lock. False when a live pass already holds it.

    A corrupt or unreadable lock file is treated as FREE: a wedged watchdog that
    cannot be restarted is worse than a rare double pass, and the worktree
    branch names carry the attempt number so a collision is visible.
    """
    d = Path(state_dir)
    d.mkdir(parents=True, exist_ok=True)
    pid = os.getpid() if pid is None else pid
    now = time.time() if now is None else now
    lock = d / LOCK_FILE
    if lock.is_file():
        try:
            rec = json.loads(lock.read_text(encoding="utf-8"))
            if now - float(rec.get("ts", 0)) < LOCK_STALE_S:
                return False
        except (OSError, ValueError, TypeError):
            pass
    _awrite(lock, json.dumps({"pid": pid, "ts": now}))
    return True


def release(state_dir):
    (Path(state_dir) / LOCK_FILE).unlink(missing_ok=True)


def _awrite(path, text):
    """Atomic write, per the project hard rule - consumers may poll mid-write."""
    path = Path(path)
    tmp = Path(str(path) + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def read_state(state_dir):
    try:
        return json.loads((Path(state_dir) / STATE_FILE).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def write_state(state_dir, state):
    _awrite(Path(state_dir) / STATE_FILE, json.dumps(state, indent=2))


# ==========================================================================
# IO
# ==========================================================================
def log(msg):
    line = f"{time.strftime('%Y-%m-%dT%H:%M:%S')} [ci_watchdog] {msg}"
    print(line, flush=True)
    try:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        with open(STATE_DIR / "watchdog.log", "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        pass


def run(argv, cwd=None, timeout=600, stdin=None, env=None):
    return subprocess.run(argv, cwd=str(cwd or ROOT), input=stdin,
                          capture_output=True, text=True, encoding="utf-8",
                          errors="replace", timeout=timeout,
                          creationflags=NO_WINDOW, env=env)


FIX_PROMPT = """\
This is an UNATTENDED scheduled run. No operator is watching the chat.

CI is RED on {base} at {sha}. Failing runs: {runs}

Your job is ONLY to make CI green again. Specifically:

1. Read the failing run's logs (`gh run view <id> --log-failed`) and find the
   ACTUAL cause. Do not guess from the test name.
2. Fix the cause, not the symptom. If the fix belongs to a family of similar
   cases, grep for the siblings and fix them too.
3. Run the full suite locally and confirm it passes before committing.
4. Commit on the CURRENT branch (you are already on a fix branch in an isolated
   worktree - do NOT switch branches, do NOT touch main).

HARD BOUNDARIES:
- Do NOT push, do NOT open a PR, do NOT merge. The watchdog does all three, and
  it self-gates the merge on this branch's own green CI.
- Do NOT change test expectations to make a test pass unless the expectation is
  provably the bug. Say so explicitly in the commit message if you do.
- Do NOT widen scope. A CI fix is not a refactor.
- Follow CLAUDE.md: 7-bit ASCII only, no em-dashes, no Co-Authored-By trailer.
- If you cannot find a real cause, make NO commit and say why. An empty pass is
  a fine outcome; a speculative commit on main is not.
"""


def _fix_in_worktree(wt, sha, runs, model, timeout, kit_seams=None):
    """Run headless claude inside the worktree. Returns (ok, transient, output).

    ONE call to `kit.spawn` through `lw_headless_env.spawn` (kit v7): the child
    runs in the worktree (`cwd=wt`), its stderr comes back for the transient
    check (`return_stderr`), a code-writing fix runs at effort `high`, and the
    kit owns everything else - proxy gate, `claude_exe` (never from cwd), lean
    project-only flags, the budget counted under its lock, status, usage line,
    and the process-tree kill on a timeout. `bare` stays False and the kit is
    told LW's floors live in hooks. `kit_seams` reaches kit.spawn's
    url_source / connect / run / exe_source - the test seam.
    """
    he = _bind_headless_env()
    prompt = FIX_PROMPT.format(base=BASE_BRANCH, sha=sha, runs=runs)
    # FLEET-COMMON item 13 d (kit v7): the fix run keeps its own checklist.
    # A fix run is its own fire: run count 1.
    prompt = f"{prompt}\n{_bind_checklist().child_rule(FIX_NOTE, 1)}\n"
    try:
        line = he.spawn(prompt, note=FIX_NOTE, writes_code=True, model=model or None,
                        effort=FIX_EFFORT, cwd=wt, return_stderr=True, timeout=timeout,
                        governor=FIX_GOVERNOR, governor_timeout=FIX_SLOT_WAIT_S,
                        extra=("--permission-mode", "bypassPermissions",
                               "--add-dir", str(wt)),
                        **(kit_seams or {}))
    except he.HeadlessRefused as exc:
        # The gate passed a moment ago, so this is the budget or a lock filling
        # in between, or no governor slot freed within FIX_SLOT_WAIT_S: not a
        # repo fault, refunded like a transient.
        return False, True, f"headless spawn refused: {exc}"
    except OSError as exc:
        return False, False, f"could not start claude ({type(exc).__name__})"
    if line.get("error") == "timeout":
        return False, False, "timeout"
    out = str(line.get("result") or "") + str(line.get("stderr") or "")
    rc = line.get("rc")
    if rc != 0 and is_transient(out):
        return False, True, out[-2000:]
    return rc == 0, False, out[-2000:]


# A CI fix writes code: kit v4 effort `high` (the kit's pick would be medium).
FIX_EFFORT = "high"

# The kit's `note` for this run: names it in the usage log and picks its effort.
FIX_NOTE = "ci-watchdog-fix"

# FLEET-KIT v6 RULING (MAIN 2237 section 2), carried by v7: a run that writes
# code takes ONE machine-wide governor slot, taken AT the call by kit.spawn
# (governor=), never around git. A slot not won within FIX_SLOT_WAIT_S refuses
# before anything starts (kit.Refused -> transient, refunded).
FIX_GOVERNOR = "queued"
FIX_SLOT_WAIT_S = 600


def _head_of(wt):
    r = run(["git", "rev-parse", "HEAD"], cwd=wt, timeout=30)
    return r.stdout.strip() if r.returncode == 0 else ""


def _cleanup_worktree(wt, branch, *, keep):
    if keep:
        log(f"worktree kept for inspection: {wt} ({branch})")
        return
    run(["git", "worktree", "remove", "--force", str(wt)], timeout=120)
    run(["git", "branch", "-D", branch], timeout=60)


def headless_gate(**seams):
    """(child_env, None) when the proxy gate passes, else (None, reason).

    A PRE-flight only: the spawn itself runs the kit's gate again. This one
    exists so a refusal creates no worktree and a dry run reports it.

    Runs BEFORE the worktree exists and before the dry-run return, so a refusal
    creates nothing and a dry run reports it too. The reason never carries the
    URL; it is logged here and to the shared daily log.
    """
    he = _bind_headless_env()
    try:
        env = he.child_env(**seams)
        if not he.can_start():
            raise he.HeadlessRefused("run budget exhausted")
        return env, None
    except he.HeadlessRefused as exc:
        log(f"headless spawn refused: {exc} - no fix attempted, no fallback")
        he.log_refusal("ci_watchdog", str(exc))
        return None, str(exc)


def do_fix_pass(sha, runs, attempt, tg, *, model, dry_run, fix_timeout, env_seams=None):
    """One fix attempt: worktree -> model -> push -> PR -> self-gate -> merge.

    Returns "refused" when the headless proxy gate refuses: nothing was
    attempted, so the caller refunds the attempt exactly as for a transient.
    """
    _env, refused = headless_gate(**(env_seams or {}))
    if refused is not None:
        return "refused"
    branch = branch_name(sha, attempt)
    wt = ROOT / "worktrees" / branch.replace("/", "_")
    if dry_run:
        log(f"DRY RUN: would create {wt} on {branch} and attempt a fix")
        return True

    r = run(["git", "worktree", "add", "-b", branch, str(wt), BASE_BRANCH],
            timeout=300)
    if r.returncode != 0:
        log(f"worktree add failed: {r.stderr.strip()[:300]}")
        return False
    keep = False
    try:
        before = _head_of(wt)
        ok, transient, out = _fix_in_worktree(wt, sha, runs, model, fix_timeout,
                                              kit_seams=env_seams)
        if transient:
            # Vendor-side, not a repo fault. Reported by the caller as a
            # non-attempt so one bad afternoon cannot exhaust the budget.
            log("transient API condition - not burning an attempt")
            return "transient"
        after = _head_of(wt)
        if after == before:
            log(f"no commit made (claude ok={ok}) - nothing to push. tail: {out[-300:]}")
            return False
        r = run(["git", "push", "-u", "origin", branch], cwd=wt, timeout=300)
        if r.returncode != 0:
            log(f"push failed: {r.stderr.strip()[:300]}")
            return False
        r = run(["gh", "pr", "create", "--base", BASE_BRANCH, "--head", branch,
                 "--title", f"ci: auto-fix red {BASE_BRANCH} at {sha[:8]}",
                 "--body", f"Automated by LW-CIWatchdog for the CI failure on "
                           f"{sha}.\n\nMerge is self-gated on this branch's own "
                           f"green CI at its own head sha."],
                cwd=wt, timeout=180)
        if r.returncode != 0:
            log(f"pr create failed: {r.stderr.strip()[:300]}")
            keep = True
            return False
        log(f"PR opened for {branch} @ {after[:8]}; waiting on its own CI")
        for _ in range(PR_CI_POLLS):
            pr_ci = tg.check_ci(after)
            if merge_allowed(pr_ci, after):
                m = run(["gh", "pr", "merge", branch, "--squash", "--delete-branch"],
                        cwd=wt, timeout=300)
                if m.returncode == 0:
                    log(f"merged {branch} - {BASE_BRANCH} should be green")
                    return True
                log(f"merge failed: {m.stderr.strip()[:300]}")
                keep = True
                return False
            if pr_ci.get("status") == "failure":
                log(f"fix branch's OWN CI is red - refusing to merge {branch}")
                keep = True
                return False
            time.sleep(PR_CI_INTERVAL_S)
        log(f"fix branch CI never settled - PR left OPEN for the operator ({branch})")
        keep = True
        return False
    finally:
        _cleanup_worktree(wt, branch, keep=keep)


TASK_RUNLOG_NAME = "LW-CIWatchdog"


def _bind_runlog():
    if "lw_runlog" in sys.modules:
        return sys.modules["lw_runlog"]
    spec = importlib.util.spec_from_file_location("lw_runlog", ROOT / "tools" / "lw_runlog.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def one_pass(*, model, dry_run, max_attempts, fix_timeout, state_dir=STATE_DIR):
    """One pass, plus ONE run record (ingest P0-4) unless it is a dry run."""
    rl = _bind_runlog()
    started = rl.utc_now()
    status = {"status": "failed", "detail": "pass raised"}
    try:
        return _one_pass(status, model=model, dry_run=dry_run, max_attempts=max_attempts,
                         fix_timeout=fix_timeout, state_dir=state_dir)
    finally:
        if not dry_run:
            rl.record(TASK_RUNLOG_NAME, started, status["status"], status["detail"])


def _one_pass(status, *, model, dry_run, max_attempts, fix_timeout, state_dir):
    reason = halted(state_dir)
    if reason:
        log(f"HALT: {reason}")
        status.update(status="halted", detail=str(reason)[:120])
        return 0
    if not acquire(state_dir):
        log("another pass holds the lock - exiting")
        status.update(status="skipped", detail="another pass holds the lock")
        return 0
    try:
        rc = _watched_pass(state_dir, model=model, dry_run=dry_run,
                           max_attempts=max_attempts, fix_timeout=fix_timeout, status=status)
        if rc != 0:
            status.update(status="failed", detail=status.get("detail") or f"rc {rc}")
        return rc
    finally:
        release(state_dir)


# The watch over "is main red" (ingest P0-2 retrofit 2/2). A failing sha is an
# item; it is DELIVERED - stops being offered - only when a fix pass merged or
# the per-sha budget gave up (left for the operator, logged once). An
# `unavailable` CI read is a FETCH FAILURE, never "nothing owed": five in a row
# (ten minutes at PT2M) append exactly one line to ALERTS_FILE, and the counter
# resets on the next good read. baseline=False: this source is a STATE ("main
# is red now"), not an event feed - the red already on main when the watch was
# first created is the work, not history.
WATCH_FILE = "watch.json"
ALERTS_FILE = "alerts.jsonl"
WATCH_SOURCE = "ci-main"
ALERT_AFTER = 5


def _bind_checklist():
    """tools/lw_checklist.py (FLEET-COMMON item 13, kit v7), bound by path."""
    if "lw_checklist" in sys.modules:
        return sys.modules["lw_checklist"]
    spec = importlib.util.spec_from_file_location("lw_checklist",
                                                  ROOT / "tools" / "lw_checklist.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _bind_watch():
    if "lw_watch" in sys.modules:
        return sys.modules["lw_watch"]
    spec = importlib.util.spec_from_file_location("lw_watch", ROOT / "tools" / "lw_watch.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _watched_pass(state_dir, *, model, dry_run, max_attempts, fix_timeout, status=None):
    lw_watch = _bind_watch()
    tg = _bind_truth_gate()
    ctx = {"rc": 0}

    def fetch():
        ci = tg.check_ci("HEAD")
        ctx["ci"] = ci
        if (ci or {}).get("status") == "unavailable":
            log(f"wait: CI 'unavailable' is not settled - not acting "
                f"({str((ci or {}).get('detail') or '')[:120]})")
            raise lw_watch.FetchFailed("CI status unavailable")
        d = decide(ci, read_state(state_dir), max_attempts=max_attempts)
        ctx["d"] = d
        log(f"{d['action']}: {d['reason']}")
        return [d["sha"]] if d["action"] in ("fix", "give-up") and d["sha"] else []

    def deliver(items):
        d = ctx["d"]
        if d["action"] == "give-up":
            return {"delivered": True}       # handled: left for the operator
        state = bump_attempt(read_state(state_dir), d["sha"])
        write_state(state_dir, state)
        runs = ", ".join(x.get("name", "?") for x in (ctx["ci"].get("runs") or []))
        result = do_fix_pass(d["sha"], runs, state["attempts"], tg,
                             model=model, dry_run=dry_run, fix_timeout=fix_timeout)
        if result in ("transient", "refused"):
            # Refund: the repo was never the problem. A refused proxy gate
            # attempted nothing at all, so it must not burn the budget either -
            # but it is NOT a completed pass, so it exits 1 where a transient
            # (which did run and will self-resolve) exits 0.
            write_state(state_dir, {"sha": d["sha"],
                                    "attempts": max(0, state["attempts"] - 1)})
            ctx["rc"] = 1 if result == "refused" else 0
            return {"delivered": False}
        ctx["rc"] = 0 if result else 1
        # A dry run proves nothing was fixed, so it never retires the sha.
        return {"delivered": bool(result) and not dry_run}

    def alert(source, count, detail):
        line = json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "source": source,
                           "consecutive_failures": count, "detail": detail})
        log(f"ALERT: {source} unreadable {count} passes in a row - {detail}")
        try:
            with open(Path(state_dir) / ALERTS_FILE, "a", encoding="utf-8") as f:
                f.write(line + "\n")
        except OSError:
            return False, "alerts file unwritable"
        return True, "alerts file"

    res = lw_watch.run_source(lw_watch.WatchState(Path(state_dir) / WATCH_FILE), WATCH_SOURCE,
                              fetch, deliver, alert, alert_after=ALERT_AFTER,
                              describe=lambda sha: sha[:8], baseline=False,
                              persist=not dry_run)
    if res.get("detail") and res["outcome"] != "fetch-failed":
        log(f"watch: {res['outcome']} - {res['detail']}")
    if status is not None:
        if res["outcome"] == "fetch-failed":
            status.update(status="partial", detail="CI status unavailable")
        else:
            d = ctx.get("d") or {}
            status.update(status="ok", detail=f"{d.get('action', '?')}: {d.get('reason', '')}"[:200])
    return ctx["rc"]


# ==========================================================================
# Self-registration (the LW convention: a task is installed by its own tool)
# ==========================================================================
TASK_NAME = "LW-CIWatchdog"
TASK_XML = ROOT / "ops" / "runtime" / "lw_ci_watchdog_task.xml"


def task_xml(python_exe, script, *, every_minutes=2):
    """Task Scheduler XML for a boot trigger that REPEATS.

    `schtasks /Create` cannot express this: `/RI` is rejected outright for
    `/SC ONSTART` (and for ONLOGON - the same wall `lw_wallpaper_rotate` hit).
    So the trigger goes through XML, exactly as that tool does.

    A BootTrigger's Repetition only starts when the trigger FIRES, so a
    boot-only task registers Ready and sits idle until the next reboot. The
    TimeTrigger below arms the repeat from install time, which is the same
    correction `docs/OPERATIONS.md` records for any LW-* task wanting a repeat.

    EXACTLY ONE of the two repeats. Giving both a Repetition runs two
    independent schedules at once and halves the real interval - measured on
    LW-Wallpaper 2026-08-13 (1.54 min per tick against a configured 3), same
    defect, same generator shape. The BootTrigger is a one-shot kick.
    """
    start = time.strftime("%Y-%m-%dT%H:%M:%S")
    return f"""<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Description>LW CI watchdog - red-main auto-fixer. Kill switch: create
ops\\runtime\\ci_watchdog\\HALT or Disable-ScheduledTask {TASK_NAME}.</Description>
  </RegistrationInfo>
  <Triggers>
    <BootTrigger>
      <Enabled>true</Enabled>
    </BootTrigger>
    <TimeTrigger>
      <StartBoundary>{start}</StartBoundary>
      <Enabled>true</Enabled>
      <Repetition>
        <Interval>PT{every_minutes}M</Interval>
        <StopAtDurationEnd>false</StopAtDurationEnd>
      </Repetition>
    </TimeTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author">
      <UserId>Administrator</UserId>
      <LogonType>InteractiveToken</LogonType>
      <RunLevel>LeastPrivilege</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <StartWhenAvailable>true</StartWhenAvailable>
    <ExecutionTimeLimit>PT2H</ExecutionTimeLimit>
    <Enabled>true</Enabled>
    <Hidden>true</Hidden>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>"{python_exe}"</Command>
      <Arguments>"{script}"</Arguments>
    </Exec>
  </Actions>
</Task>
"""


def windowless_python(exe):
    """Return the pythonw.exe beside `exe`, or `exe` unchanged.

    install() used to register sys.executable verbatim. Run the installer from
    a normal python.exe - which is how anyone runs it - and the task inherits a
    CONSOLE, so every two-minute tick flashed a window and stole focus. The
    module's CREATE_NO_WINDOW care only ever covered child processes; this
    covers the parent. Falls back to the original path when the sibling is
    missing, because pointing a task at a non-existent exe fails silently on
    every trigger, forever.
    """
    p = Path(exe)
    if p.name.lower() == "pythonw.exe":
        return exe
    if p.name.lower() != "python.exe":
        return exe
    sibling = p.with_name("pythonw.exe")
    return str(sibling) if sibling.is_file() else exe


def install():
    TASK_XML.parent.mkdir(parents=True, exist_ok=True)
    xml = task_xml(windowless_python(sys.executable),
                   str(Path(__file__).resolve()))
    # UTF-16 with a BOM: schtasks /XML rejects anything else for this schema.
    tmp = Path(str(TASK_XML) + ".tmp")
    tmp.write_bytes(xml.encode("utf-16"))
    tmp.replace(TASK_XML)
    r = run(["schtasks", "/Create", "/TN", TASK_NAME, "/XML", str(TASK_XML), "/F"],
            timeout=120)
    print((r.stdout or r.stderr).strip())
    return r.returncode


def uninstall():
    r = run(["schtasks", "/Delete", "/TN", TASK_NAME, "/F"], timeout=120)
    print((r.stdout or r.stderr).strip())
    return r.returncode


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--model", default=None,
                    help="model override for the fix pass; default is the fleet "
                         "kit's pick for a code-writing run")
    ap.add_argument("--dry-run", action="store_true",
                    help="decide and log, but never create a worktree or push")
    ap.add_argument("--max-attempts", type=int, default=MAX_ATTEMPTS,
                    help="fix attempts per failing sha before giving up")
    ap.add_argument("--fix-timeout", type=float, default=3600.0,
                    help="seconds the headless fix pass may run")
    ap.add_argument("--status", action="store_true",
                    help="print the decision and exit without acting")
    ap.add_argument("--install", action="store_true",
                    help=f"register the {TASK_NAME} scheduled task")
    ap.add_argument("--uninstall", action="store_true",
                    help=f"remove the {TASK_NAME} scheduled task")
    args = ap.parse_args(argv)
    if args.install:
        return install()
    if args.uninstall:
        return uninstall()
    if args.status:
        tg = _bind_truth_gate()
        ci = tg.check_ci("HEAD")
        print(json.dumps({"ci": ci, "state": read_state(STATE_DIR),
                          "halt": halted(STATE_DIR),
                          "decision": decide(ci, read_state(STATE_DIR),
                                             max_attempts=args.max_attempts,
                                             halt=halted(STATE_DIR))}, indent=2))
        return 0
    return one_pass(model=args.model, dry_run=args.dry_run,
                    max_attempts=args.max_attempts, fix_timeout=args.fix_timeout)


if __name__ == "__main__":
    raise SystemExit(main())
