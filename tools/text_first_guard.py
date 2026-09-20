#!/usr/bin/env python3
"""PreToolUse text-first backstop (R1-R3, CLAUDE.md "Execution Efficiency").

Denies vision / desktop tools that READ TEXT OR STATE off the screen when a
text path always exists in LW: file content -> Read / Grep; runtime state ->
Read ops/runtime/health.json (service/API endpoints TBD - product not yet
defined).

Scope is deliberately NARROW so the guard never wedges a sanctioned visual
ritual: ONLY the pure screen-text / clipboard readers are denied. Pixel
screenshots, preview_* DOM checks, and clicks / typing are all ALLOWED
(legit per R3 - the UI-audit ritual). The escape-hatch file
ops/runtime/allow_visual.flag, when present, allows everything (rare case
where no text path exists).

PreToolUse JSON contract: permissionDecision "deny" feeds the reason back to
the model and blocks the call, so the model retries with the text tool. The
guard never raises - a crashing guard must not block tools.
"""
import json
import os
import sys
from pathlib import Path

# Pure screen-text / clipboard readers that ALWAYS have a text alternative.
_DENY = {
    "mcp__Windows-MCP__Scrape",
    "mcp__computer-use__read_clipboard",
}

_FLAG_REL = ("ops", "runtime", "allow_visual.flag")


def flag_path() -> Path:
    """The escape hatch, in the checkout this guard is RUNNING IN.

    This was a bare literal until 2026-09-20, which meant a clone, a rename or a
    linked worktree consulted the ORIGINAL tree's flag: an override dropped in
    the tree being edited did nothing, and one left behind in the original tree
    silently granted a bypass everywhere else. Same false-GREEN family as the
    hook commands that named their script by absolute path
    (tests/test_hook_commands_are_env_anchored.py).

    `CLAUDE_PROJECT_DIR` first, because the harness exports it into every hook
    process and it is the authoritative answer to "which project is this"
    (measured on CLI 2.1.251). Otherwise the repo root is derived from this
    file's own location - `tools/` sits directly under it - which is what keeps
    the guard correct when it is run by hand or from a test.
    """
    env_root = os.environ.get("CLAUDE_PROJECT_DIR")
    root = Path(env_root) if env_root else Path(__file__).resolve().parent.parent
    return root.joinpath(*_FLAG_REL)

_REASON = (
    "Text-first (CLAUDE.md R1-R2): do not read text/state off the screen. "
    "File content -> Read/Grep. Runtime state -> Read ops/runtime/health.json "
    "(service/API endpoints TBD - product not yet defined). "
    "Override only when no text path exists: create ops/runtime/allow_visual.flag."
)


def main() -> int:
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
        tool = payload.get("tool_name", "")
        if tool in _DENY and not flag_path().exists():
            out = {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": _REASON,
                }
            }
            sys.stdout.write(json.dumps(out))
    except (ValueError, TypeError, OSError):
        # Never block on guard failure.
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
