"""No tracked CODE file may hardcode LW's own root as `C:\\Legion Wallpaper`.

THE RULE. On 2026-10-08 the repo moved from C: to E: and C: became a junction.
The C: path inventory (LW responder ANSWER to MAIN 2155) found 34 tracked code
and config rows that spelled LW's root out as a drive-letter literal, so every
one of them silently depended on that junction. The root is now derived - from
`__file__` (`Path(__file__).resolve().parents[1]`), from `tools/lw_paths.py`
(`repo_root()`), from `$PSScriptRoot` in PowerShell, or from `A_ScriptDir` in
AutoHotkey - and this guard keeps a new literal from creeping back in.

SCOPE. Tracked files with a code / config extension (.py .ps1 .psm1 .json
.toml .cmd .bat .ahk). Prose (.md) is out of scope: the ledger and history
legitimately record where the tree used to live.

THE ALLOWLIST is per file and every entry says why. Three kinds only:
history / dated artifacts (never rewritten), tests whose fixtures USE the
literal as a string under test, and one comment that records the old literal.
"""
from __future__ import annotations

import re
import subprocess
from functools import lru_cache
from pathlib import Path

import gitdep

REPO_ROOT = Path(__file__).resolve().parent.parent

CODE_SUFFIXES = (".py", ".ps1", ".psm1", ".json", ".toml", ".cmd", ".bat", ".ahk")

# `C:\Legion Wallpaper`, `C:/Legion Wallpaper`, the JSON/Python-escaped
# `C:\\Legion Wallpaper`, and the pre-2026-09-06 `C:\LegionWallpaper`.
LW_ROOT_LITERAL = re.compile(r"[cC]:(?:\\\\|\\|/)+Legion ?Wallpaper", re.IGNORECASE)

# Path prefix (directory, ends in "/") or exact file -> reason.
ALLOWLIST: dict[str, str] = {
    "scratchpad/": "dated one-off artifacts, history, never rewritten",
    "docs/_archive/": "immutable history (CLAUDE.md sweep exclusion)",
    "tests/test_no_hardcoded_c_paths.py": "this guard: the fixture arm below",
    "tests/test_director_prompt_budget.py": "fixture: asserts the literal is ABSENT",
    "tests/test_drift_guard_agent_config.py": "fixture: a ~/.claude.json projects key",
    "tests/test_drift_guard_sibling_root.py": "comment: the 2026-09-06 rename story",
    "tests/test_hook_commands_are_env_anchored.py": "fixture: a pinned hook command under test",
    "tests/test_loop_module_root_resolution.py": "fixture: a drive path on POSIX",
    "tests/test_lw_first_pass.py": "fixture: a source path string under test",
    "tests/test_no_account_paths.py": "fixture: a non-account path under test",
    "tests/test_done_gate.py": "fixture: a pushed command string under test",
    "tests/test_guard_scripts_resolve_this_checkout.py": "fixture: planted pinned roots",
    "tests/test_handoff_write_gate.py": "fixture: a non-profile path under test",
    "tests/test_lw_agent_mirror.py": "fixture: a worktreePath record",
    "tests/test_lw_rundash_state.py": "fixture: `git worktree list` output",
    "tests/test_no_invalid_escape_sequences.py": "docstring: the escape-bug example",
    "tests/test_oracle_backend.py": "fixture: a cfg repo_root passed through argv",
    "tests/test_slice_orchestrator_claims.py": "fixture: an absolute claim path",
    "ops/loop/loop_controller.py": "comment: records the old hardcoded fallback",
    "tools/claimed_green_gate.py": "docstring: the shlex backslash example",
    "tools/drift_guard.py": "docstrings: the 2026-09-06 rename + slug encoding",
    "tools/lw_transcript_union.py": "docstring: the pre-rename cwd it repairs",
}


def _allowed(rel: str) -> bool:
    return any(rel == k or (k.endswith("/") and rel.startswith(k)) for k in ALLOWLIST)


def find_literals(text: str) -> list[int]:
    """1-based line numbers carrying an LW-root drive literal."""
    return [i for i, line in enumerate(text.splitlines(), 1)
            if LW_ROOT_LITERAL.search(line)]


@lru_cache(maxsize=1)
def _tracked_code_files() -> tuple[str, ...]:
    out = subprocess.run(["git", "ls-files", "-z"], cwd=REPO_ROOT,
                         capture_output=True, check=True).stdout
    names = [n for n in out.decode("utf-8", "replace").split("\0") if n]
    return tuple(n for n in names if n.lower().endswith(CODE_SUFFIXES))


def test_detector_fires_on_every_spelling():
    bs = "\\"
    for s in ("C:" + bs + "Legion Wallpaper",
              "c:/legion wallpaper/images",
              '"C:' + bs + bs + 'Legion Wallpaper' + bs + bs + 'ops"',
              "C:" + bs + "LegionWallpaper"):
        assert find_literals("x = " + s) == [1], s
    assert find_literals("ROOT = Path(__file__).resolve().parents[1]") == []
    assert find_literals("E:" + bs + "Legion Wallpaper") == []


def test_allowlist_entries_exist():
    for k in ALLOWLIST:
        assert (REPO_ROOT / k.rstrip("/")).exists(), f"stale allowlist entry {k}"


@gitdep.requires_git
def test_no_tracked_code_file_hardcodes_lw_root():
    hits = []
    for rel in _tracked_code_files():
        if _allowed(rel):
            continue
        p = REPO_ROOT / rel
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        hits += [f"{rel}:{n}" for n in find_literals(text)]
    assert not hits, (
        "hardcoded LW root literal(s) - derive it from __file__ / "
        "tools/lw_paths.repo_root() / $PSScriptRoot / A_ScriptDir instead:\n  "
        + "\n  ".join(hits))
