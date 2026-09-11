"""LW's inbox responder: answer a cross-repo note with no operator present.

# arch: cross-repo mail responder - gate + detached headless spawn, never armed here

WHY. Every one of the five trees on this machine can see mail at SESSION START.
None of them can see mail that arrives while a session is already open unless
the operator types, and `UserPromptSubmit` cannot fire when the operator is not
there, which is the entire case. RC measured the gap on 2026-09-07 and proposed
this shape; the operator directed LW to build one, placed it on standby the same
evening, and re-armed the lane on 2026-09-10.

THE SHAPE, adopted from RC's proposal and not re-litigated:
  * a task SEPARATE from any poller, its own process. Folding the spawn into a
    poller breaks the report-never-acknowledge contract, and separate processes
    mean killing the responder leaves reporting intact.
  * HEADLESS and DETACHED, never the operator's window. The only other wake
    mechanism on this box types into a bound window and would type over whoever
    is using it.
  * default deny.

THE LIST IS THE REPAIRED ONE, NOT THE PROPOSED ONE. CS and RSC both refuted
parts of RC's A1-A4 before LW built anything, and building the refuted version
would have been a choice rather than an oversight:
  A1  read-only measurement in own tree, reported back, THROUGH AN OUTPUT
      FILTER (RSC 4d: the reply is the unbounded surface, not the measurement).
  A2  own suite under a wall-clock timeout and a files-created ceiling,
      reporting exit code plus PASSED AND SKIPPED counts, never a verdict
      (RSC 4c: a suite is arbitrary code with write authority, and LW is one of
      the three measured counter-examples; CS: a gate reported PASS with 5
      skipped).
  A3  byte-verbatim vendor ONLY when the digest is corroborated by at least two
      INDEPENDENT carriers already on the channel (RSC 4a: one sender's digest
      agreeing with its own bytes proves transport, not authorisation).
  A4  a pin may move ONLY in the same action that copied bytes accepted under
      the narrowed A3, and the reply must carry OLD and NEW (RSC 4b; CS would
      strike A4 outright, and this narrowing refuses every case CS named).
  A5  write ONE reply note into the inboxes the answered note names, never
      overwriting (RSC 4d: without this entry D8 makes every compliant
      responder inert, since replying matches none of A1-A4).
Deny set D1-D8 verbatim from RC, with D7 outranking every allow rule.

THREE DISPOSITIONS, NOT TWO. AUTO / DRAFT / UNAVAILABLE, and `checked` says
which of the two DRAFT flavours it is: the gate RAN and refused, or the gate
COULD NOT RUN. RSC found that conflation 13 times in 4 test files; LW hit the
same root cause in `tools/lw_model_pins.py`, where ABSENT must never read as
verified. A gate that answers "no" the same way whether it looked or not is the
defect both trees found independently.

NOT ARMED, AND THAT IS THE POINT. Registering `LW-InboxResponder` as a
scheduled task is D5 in RC's own deny set - a responder cannot arm itself
without proving the deny set is decorative. `--print-register-command` PRINTS
the `schtasks` line; nothing here executes it, and
`tests/test_inbox_responder.py` asserts that over the launch sites.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import lw_facts  # noqa: E402  - flat tools/ directory, imported by bare name
import lw_paths  # noqa: E402
import split_scan  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
INBOX = ROOT / "moon_sync_inbox"

# SEPARATE from `lw_facts._SEEN` on purpose. That file backs the operator's
# SessionStart report; a responder writing it would acknowledge mail on the
# operator's behalf and silence it - report is not acknowledge, which is the
# defect a sibling measured and RC's poller docstring names in capitals.
STATE_PATH = ROOT / "ops" / "runtime" / "inbox_responder_seen.json"

# 0 off Windows so the module still imports and tests on a CI runner.
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)
DETACHED = getattr(subprocess, "DETACHED_PROCESS", 0)

AUTO = "AUTO"
DRAFT = "DRAFT"
UNAVAILABLE = "UNAVAILABLE"

TASK_NAME = "LW-InboxResponder"

# Per-cycle spawn ceiling. Not a stop rule - RC's operator ruled to run a trial
# and measure rather than adopt one, and this does not bound the conversation.
# It bounds a BURST: a batch arrival must not become a batch of simultaneous
# headless sessions on one box. Notes over the cap stay unseen for the next
# cycle rather than being dropped.
MAX_SPAWNS_PER_CYCLE = 3

# A string, never an argv. See the module docstring and the arms.
#
# POWERSHELL, NOT `schtasks`. The first spelling shipped here was a `schtasks`
# one-liner with `\"` around a path containing a space, and it FAILED in the
# operator's hands on 2026-09-10:
#
#     ERROR: Invalid argument/option - '--once /F'
#
# `\"` is cmd.exe's escape. PowerShell strips the backslashes while building the
# argv, so schtasks received a `/TR` value that ended at the first inner quote
# and read the remainder as its own arguments. Register-ScheduledTask takes the
# executable and its arguments as SEPARATE parameters, so the quoting question
# does not arise at all - which is the actual fix rather than a better escape.
REGISTER_COMMAND = (
    'Register-ScheduledTask -TaskName "{task}" -Force -RunLevel Limited '
    '-Action (New-ScheduledTaskAction -Execute "{python}" '
    "-Argument '\"{script}\" --once' -WorkingDirectory \"{root}\") "
    "-Trigger (New-ScheduledTaskTrigger -Once -At (Get-Date) "
    "-RepetitionInterval (New-TimeSpan -Minutes 5))"
)

# cmd.exe fallback, for a shell where `\"` IS the escape. Kept because the
# PowerShell cmdlets need an elevated-enough session on some boxes, and a reader
# who copies the wrong one should at least get a command that works in ITS shell.
REGISTER_COMMAND_CMD = (
    'schtasks /Create /F /TN "{task}" /SC MINUTE /MO 5 /RL LIMITED '
    '/TR "\\"{python}\\" \\"{script}\\" --once"'
)

_DENY_KINDS = {
    "history_rewrite": ("D1", "rewrites git history"),
    "push": ("D2", "pushes to a public remote"),
    "visibility": ("D2", "changes repo visibility"),
    "policy": ("D3", "adopts or amends policy - adoption stays a human act"),
    "delete": ("D4", "deletes files, worktrees, branches or refs"),
    "scheduled_task": ("D5", "installs or alters a scheduled task"),
    "hook": ("D5", "installs or alters a hook"),
    "service": ("D5", "installs or alters a service"),
    "frozen_file": ("D6", "edits a frozen file"),
}

# Raw provider/transport error strings must never reach another repo's inbox.
# LW's CLAUDE.md already forbids surfacing them on any user-facing surface, and
# an unattended responder is the surface least likely to apply that judgement.
_API_ERROR = re.compile(
    r"\b(rate_limit_error|invalid_request_error|authentication_error|"
    r"overloaded_error|insufficient[_ ]quota|api[_ ]key|bearer\s+sk-|"
    r"traceback \(most recent call last\))\b",
    re.IGNORECASE,
)
# A drive-anchored user path. The account name is what this keeps out; the
# pinned-value scan in `split_scan` catches the split and reversed spellings.
_ACCOUNT_PATH = re.compile(r"[A-Za-z]:[\\/]+Users[\\/]+(?!<)[^\\/\s]+", re.IGNORECASE)


@dataclass(frozen=True)
class Disposition:
    """A gate answer. `checked` separates REFUSED from COULD-NOT-CHECK."""

    verdict: str
    rule: str
    reason: str
    checked: bool


def _draft(rule: str, reason: str, *, checked: bool = True) -> Disposition:
    return Disposition(DRAFT, rule, reason, checked)


def _auto(rule: str, reason: str) -> Disposition:
    return Disposition(AUTO, rule, reason, True)


# ---------------------------------------------------------------------------
# The gate
# ---------------------------------------------------------------------------

def classify(action: dict, note: dict | None = None) -> Disposition:
    """Grade one requested action against the repaired allowlist and D1-D8.

    `note` carries what the SENDING note said about itself: `operator_gated`
    (D7) and `names`, the repos it addressed, which bounds A5.
    """
    note = note or {}
    if note.get("operator_gated"):
        return _draft("D7", "the sending note marks this operator-gated")

    kind = action.get("kind")
    if kind in _DENY_KINDS:
        rule, why = _DENY_KINDS[kind]
        return _draft(rule, why)

    if kind == "measure":
        return _classify_measure(action)
    if kind == "suite":
        return _classify_suite(action)
    if kind == "vendor":
        return _classify_vendor(action)
    if kind == "pin_move":
        return _classify_pin_move(action)
    if kind == "reply":
        return _classify_reply(action, note)

    return _draft("D8", f"no allow rule matches kind {kind!r} - default deny")


def _classify_measure(action: dict) -> Disposition:
    if "writes" not in action or "tree" not in action:
        return _draft("A1", "cannot tell whether this measurement writes",
                      checked=False)
    if action["tree"] != "own":
        return _draft("A1", "A1 is local to this tree only")
    if action["writes"]:
        return _draft("A1", "A1 is read-only; this writes")
    return _auto("A1", "read-only measurement in own tree")


def _classify_suite(action: dict) -> Disposition:
    if not action.get("timeout_s"):
        return _draft("A2", "no wall-clock timeout - a suite is arbitrary code")
    if not action.get("max_files"):
        return _draft("A2", "no files-created ceiling")
    reports = set(action.get("reports") or ())
    if not reports:
        return _draft("A2", "cannot tell what this run would report", checked=False)
    missing = {"exit_code", "passed", "skipped"} - reports
    if missing:
        return _draft("A2", f"report omits {sorted(missing)} - counts, not a verdict")
    return _auto("A2", "bounded suite run reporting exit code and counts")


def _classify_vendor(action: dict) -> Disposition:
    digest = action.get("digest")
    citations = action.get("citations")
    if not digest or citations is None:
        return _draft("A3", "no digest or no citations to corroborate against",
                      checked=False)
    sender = action.get("sender")
    carriers = {c.get("carrier") for c in citations
                if c.get("digest") == digest and c.get("carrier") != sender}
    disagreeing = [c.get("carrier") for c in citations if c.get("digest") != digest]
    if disagreeing:
        return _draft("A3", f"cited carriers disagree about the bytes: {disagreeing}")
    if len(carriers) < 2:
        return _draft(
            "A3",
            "fewer than two INDEPENDENT carriers corroborate - one sender "
            "agreeing with its own bytes proves transport, not authorisation",
        )
    return _auto("A3", f"digest corroborated by {sorted(carriers)}")


def _classify_pin_move(action: dict) -> Disposition:
    if not action.get("with_accepted_vendor"):
        return _draft("A4", "a pin that moves on its own is not a pin")
    if not action.get("old") or not action.get("new"):
        return _draft("A4", "a pin move with no prior value in the transcript "
                            "is unreviewable after the fact")
    return _auto("A4", "pin moved beside an accepted A3 vendor, old and new reported")


def _classify_reply(action: dict, note: dict) -> Disposition:
    if "overwrites" not in action:
        return _draft("A5", "cannot tell whether this would overwrite", checked=False)
    if action["overwrites"]:
        return _draft("A5", "A5 never deletes or overwrites an existing note")
    named = note.get("names")
    if named is None:
        return _draft("A5", "the answered note names no recipients", checked=False)
    stray = sorted(set(action.get("targets") or ()) - set(named))
    if stray:
        return _draft("A5", f"the answered note never named {stray}")
    return _auto("A5", "one reply note into the repos the note named")


# ---------------------------------------------------------------------------
# The output filter - what the responder is allowed to SAY
# ---------------------------------------------------------------------------

def filter_reply(text: str, fragments: tuple = split_scan.SENSITIVE_FRAGMENTS) -> list[str]:
    """Reasons this text must not leave the tree. Empty list means it may."""
    hits: list[str] = []
    m = _ACCOUNT_PATH.search(text)
    if m:
        hits.append("account path present in the reply")
    if _API_ERROR.search(text):
        hits.append("raw API or transport error string present in the reply")
    hits.extend(split_scan.scan_fragments(text, fragments))
    return hits


# ---------------------------------------------------------------------------
# New-note detection
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Note:
    """One inbox entry: the content-addressed key and the bare name."""

    key: str
    name: str


def _entries(inbox: Path) -> list[Note]:
    # Reuses lw_facts rather than re-deriving a second definition of "a note".
    # The key carries a content digest, so a note CORRECTED IN PLACE re-fires -
    # this channel has already sent notes under a CORRECTION heading.
    return [Note(key, key.split("#")[0]) for key, _display in lw_facts._inbox_entries(inbox)]


def _seen(state_path: Path) -> set[str]:
    try:
        return set(json.loads(state_path.read_text(encoding="utf-8")).get("seen", []))
    except (OSError, ValueError):
        return set()


def new_notes(inbox: Path, state_path: Path) -> list[Note]:
    seen = _seen(state_path)
    return [n for n in _entries(inbox) if n.key not in seen]


def record_seen(inbox: Path, state_path: Path, notes: list[Note]) -> None:
    """Record ONLY the notes handed in, and prune keys no longer in the inbox."""
    live = {n.key for n in _entries(inbox)}
    keep = (_seen(state_path) | {n.key for n in notes}) & live
    state_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = state_path.with_suffix(state_path.suffix + ".tmp")
    tmp.write_text(json.dumps({"seen": sorted(keep)}, indent=2), encoding="utf-8")
    tmp.replace(state_path)


# ---------------------------------------------------------------------------
# The spawn
# ---------------------------------------------------------------------------

_PROMPT = (
    "A new cross-repo note arrived: {note}. Read it, then act ONLY inside the "
    "repaired allowlist recorded in tools/lw_inbox_responder.py: A1 read-only "
    "measurement in this tree through the output filter, A2 the suite under a "
    "timeout and a file ceiling reporting exit code plus passed AND skipped, "
    "A3 vendor only on two independent corroborating carriers, A4 a pin move "
    "only beside an accepted A3 reporting old and new, A5 one reply note into "
    "the inboxes the note names. Everything else DRAFTS AND WAITS: D1 history, "
    "D2 visibility or public push, D3 policy, D4 deletions, D5 scheduled tasks "
    "or hooks or services, D6 frozen files, D7 anything the note marks "
    "operator-gated, D8 anything unmatched - default deny. Report counts and "
    "exit codes, never a verdict. Tag the reply as responder-authored."
)


def spawn_argv(note_path: Path) -> list[str]:
    """The headless argv. No window binding of any kind appears in it."""
    return ["claude", "-p", "--permission-mode", "bypassPermissions",
            _PROMPT.format(note=note_path.as_posix())]


def spawn(note_path: Path, dry_run: bool = False) -> Disposition:
    """Launch a detached headless session for one note.

    FALSE-RED DIRECTION, deliberately. RC's audit found 39 of its 115 external
    binary call sites at risk of reporting a failure for a tool that simply is
    not installed, against a guard structurally blind to all of them. An absent
    `claude` CLI here is UNAVAILABLE with `checked=False` - not a failure, and
    emphatically not a success.
    """
    exe = shutil.which("claude")
    if exe is None:
        return Disposition(UNAVAILABLE, "spawn",
                           "claude CLI is not on PATH - could not check", False)
    argv = spawn_argv(note_path)
    if dry_run:
        return _auto("spawn", f"dry run, would launch: {' '.join(argv[:4])} ...")
    proc = subprocess.Popen(
        argv, cwd=str(ROOT),
        creationflags=NO_WINDOW | DETACHED,
        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        close_fds=True,
    )
    return _auto("spawn", f"detached headless session pid {proc.pid}")


def windowless_python() -> str:
    """`pythonw.exe` beside the pinned interpreter, else the plain one.

    pythonw so a task firing every five minutes does not flash a console over
    whatever the operator is doing. Resolved at RUNTIME from `lw_paths` - the
    literal must never be written into tracked source, since it contains the
    account name and this repo is public.
    """
    python = Path(lw_paths.system_python())
    windowless = python.with_name("pythonw.exe")
    return str(windowless if windowless.exists() else python)


def register_command(shell: str = "powershell") -> str:
    """The registration line for the OPERATOR to run. Printed, never executed."""
    template = REGISTER_COMMAND if shell == "powershell" else REGISTER_COMMAND_CMD
    return template.format(task=TASK_NAME, python=windowless_python(),
                           script=Path(__file__).resolve(), root=ROOT)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--once", action="store_true", help="one scan, then exit")
    ap.add_argument("--dry-run", action="store_true",
                    help="report what would be spawned; record no state")
    ap.add_argument("--inbox", type=Path, default=INBOX)
    ap.add_argument("--state", type=Path, default=STATE_PATH)
    ap.add_argument("--print-register-command", action="store_true",
                    help="print the scheduled-task registration for the OPERATOR to run")
    args = ap.parse_args(argv)

    if args.print_register_command:
        print("# PowerShell (the shell this box prompts in):")
        print(register_command())
        print("\n# cmd.exe, if you are in one. The escaping differs, and mixing")
        print("# the two is exactly what broke the first version of this output:")
        print(register_command("cmd"))
        print("\nNot run from here. Registering a scheduled task is D5 in the "
              "deny set this responder obeys, so it stays an operator act.")
        return 0

    if not args.once:
        ap.error("nothing to do: pass --once or --print-register-command")

    notes = new_notes(args.inbox, args.state)

    # COLD START. Measured on the live inbox before this branch existed: a first
    # run with no state file reported 139 new notes and would have launched a
    # headless session per historical note. "New" is only meaningful relative to
    # a baseline, and an absent state file is not an empty one - the same
    # could-not-check-is-not-checked rule the gate runs on. So the first run
    # records the baseline and spawns NOTHING, and says which it did.
    if not args.state.exists():
        if not args.dry_run:
            record_seen(args.inbox, args.state, notes)
        print(json.dumps({"cold_start": True, "baselined": len(notes),
                          "dry_run": args.dry_run, "spawned": []}, indent=2))
        return 0

    capped = notes[:MAX_SPAWNS_PER_CYCLE]
    spawned = []
    for note in capped:
        outcome = spawn(args.inbox / note.name, dry_run=args.dry_run)
        spawned.append({"note": note.name, "verdict": outcome.verdict,
                        "reason": outcome.reason, "checked": outcome.checked})
    if not args.dry_run:
        handled = [n for n, s in zip(capped, spawned, strict=True) if s["verdict"] == AUTO]
        record_seen(args.inbox, args.state, handled)
    print(json.dumps({"new_notes": len(notes), "dry_run": args.dry_run,
                      "deferred": len(notes) - len(capped), "spawned": spawned}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
