"""FLEET-KIT v10 tree wiring (MAIN 0839 section 3 steps 2-3; FLEET-COMMON banner).

The kit's conformance() pins the vendored bytes; it does not see how a tree
WIRES the new SUBAGENT-FIRST hook. These arms do:
  * the tracked PreToolUse list runs the kit's `fleet_subagent_first.py`
    exactly once, anchored to $CLAUDE_PROJECT_DIR, with timeout 10 and the
    matcher MAIN ordered (every guarded tool, MultiEdit included);
  * the interpreter is `python`, not `pythonw`: a deny is a JSON decision on
    stdout, and pythonw discards stdout, so a pythonw hook could never deny;
  * the mode file and the decision log are gitignored (runtime state).

The mode itself (`log` until three clean interactive sessions, MAIN 0839 step
3) lives in the gitignored mode file and is read back by measurement, not here.

Hermetic: reads tracked bytes only.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SETTINGS = ROOT / ".claude" / "settings.json"
MATCHER = "Bash|PowerShell|Read|Edit|Write|Grep|Glob|NotebookEdit|MultiEdit"
SCRIPT = "$CLAUDE_PROJECT_DIR/ops/fleet_kit/fleet_subagent_first.py"
_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0) if sys.platform == "win32" else 0


def _hits():
    pre = json.loads(SETTINGS.read_text(encoding="utf-8"))["hooks"]["PreToolUse"]
    return [(entry.get("matcher"), h) for entry in pre for h in entry["hooks"]
            if "fleet_subagent_first.py" in h["command"]]


def test_subagent_first_hook_is_wired_once_with_the_ordered_matcher():
    hits = _hits()
    assert len(hits) == 1, hits
    matcher, hook = hits[0]
    assert matcher == MATCHER
    assert hook["timeout"] == 10
    assert SCRIPT in hook["command"]


ANCHORED = 'python "$CLAUDE_PROJECT_DIR/ops/fleet_kit/fleet_subagent_first.py"'


def test_subagent_first_hook_is_the_anchored_fleet_form():
    """Kit v11 ruling R3 (MAIN 1840): the command is EXACTLY the anchored form,
    optionally followed by ` || true`; the v10 cwd-relative form is drift."""
    _, hook = _hits()[0]
    assert hook["command"] in (ANCHORED, ANCHORED + " || true"), hook["command"]


def test_subagent_first_hook_runs_under_an_interpreter_that_keeps_stdout():
    _, hook = _hits()[0]
    assert hook["command"].split()[0] == "python", hook["command"]


def test_subagent_first_runtime_files_are_gitignored():
    for rel in ("ops/loop/control/subagent_first.mode", "ops/loop/control/subagent_first.jsonl"):
        r = subprocess.run(["git", "-C", str(ROOT), "check-ignore", "-v", "--no-index", rel],
                           capture_output=True, text=True, creationflags=_NO_WINDOW)
        # check-ignore can exit 0 with an EMPTY pattern column; parse the column.
        pattern = r.stdout.split("\t")[0].split(":", 2)[-1] if r.stdout else ""
        assert r.returncode == 0 and pattern, f"{rel} is not gitignored: {r.stdout!r}"


COMMANDS = sorted((ROOT / ".claude" / "commands").glob("*.md"))
DISPATCH = "ONE sub-agent"


def test_command_docs_exist():
    """Guard the guard: an empty glob would pass the two arms below vacuously."""
    assert len(COMMANDS) >= 20


def test_no_command_doc_keeps_the_inline_exception():
    """MAIN 0839: the banner drops the quick-read / one-line-fix exception."""
    keep = [p.name for p in COMMANDS if "may inline" in p.read_text(encoding="ascii")]
    assert not keep, keep


def test_every_command_doc_dispatches_to_one_sub_agent():
    """MAIN 0839 step 4: /done and every skill that runs tools go to ONE sub-agent."""
    missing = [p.name for p in COMMANDS if DISPATCH not in p.read_text(encoding="ascii")]
    assert not missing, missing
