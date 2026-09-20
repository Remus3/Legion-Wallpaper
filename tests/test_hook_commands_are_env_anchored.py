"""A hook command must reference its script through `$CLAUDE_PROJECT_DIR`, never
through a literal absolute path to THIS checkout.

THE DEFECT, measured on 2026-09-20. All eleven hook commands in
`.claude/settings.json` named their script by the literal path
`C:\\Legion Wallpaper\\tools\\<script>.py`, with zero uses of
`$CLAUDE_PROJECT_DIR` anywhere in the repo. The interpreter had already been
de-accountised to the bare name `pythonw` (LEDGER 166,
`tests/test_hook_interpreter_resolves.py` keeps that honest) - but the SCRIPT
half stayed pinned to one directory on one machine.

WHY THAT IS A FALSE GREEN AND NOT MERELY UNTIDY. A clone under another name, a
rename of the folder, or a linked worktree all keep running the ORIGINAL tree's
tooling. The hook fires, exits 0, and gated NOTHING in the checkout actually
being edited. Every symptom is identical to a healthy run, which is the same
silence class this repo has already been bitten by twice: `core.hooksPath`
pointing at `.githooks` made any hook written into `.git/hooks` dead, and
`precommit_gate.py` invoked with no args self-gated to a silent no-op for three
weeks. Presence is not proof a guard fires. `.githooks/` got this right from the
start - both hooks resolve `ROOT="$(git rev-parse --show-toplevel)"` - so the
Claude-side wiring was the only half still pinned.

EXPANSION IS MEASURED, NOT ASSUMED. Swapping a working literal for a variable
the harness does not expand would DISARM every hook, which is strictly worse
than the defect. So it was proven by observation before the edit, on CLI 2.1.251,
with two headless `claude -p` probe sessions in throwaway project directories:
the harness substitutes `$CLAUDE_PROJECT_DIR` into the command STRING (the
script ran, and reported its own resolved `sys.argv[0]`) and also exports
`CLAUDE_PROJECT_DIR` into the hook process environment. The second probe used a
project directory whose name CONTAINS A SPACE and a `pythonw` interpreter,
because LW's root does - the expansion survives the quoting.

WHAT THIS ASSERTS, AND WHAT IT LEAVES TO ITS SIBLING.
`tests/test_tracked_settings_is_safe.py` already asserts that the tracked file
parses and that every declared script exists BY BASENAME. Basename matching is
deliberately loose there - it has to be, because it runs on Linux CI where a
Windows absolute path is not a path - and it is exactly loose enough to accept
`$CLAUDE_PROJECT_DIR/wrong/place/pytest_guard.py`. Once the commands are
env-anchored the path becomes repo-relative and therefore checkable on any OS,
so the arm below resolves the FULL path under the repo root. The JSON-validity
arm is parametrized over both settings files: `settings.json` overlaps its
sibling by one assertion on purpose, because `settings.local.json` - the
gitignored file that TAKES PRECEDENCE on this box - was covered by nothing at
all, and an invalid JSON settings file is silently unparsed, presenting exactly
as "no hooks configured" (CLAUDE.md records that confound producing a false
conclusion in two arms of a past probe).

NO ACCOUNT NAME, AND NO REPO NAME EITHER. The detector asks a structural
question - is this `.py` token an absolute path - rather than matching
`C:\\Legion Wallpaper`. Matching the literal would go green the moment the
folder were renamed, which is the very scenario this file exists for, and
`tests/test_no_account_paths.py` is the precedent for resolving the repo root
from `__file__` instead of naming a machine.
"""
from __future__ import annotations

import json
import re
from pathlib import Path, PurePosixPath, PureWindowsPath

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SETTINGS = REPO_ROOT / ".claude" / "settings.json"
LOCAL_SETTINGS = REPO_ROOT / ".claude" / "settings.local.json"

ANCHOR = "$CLAUDE_PROJECT_DIR"

# `C:\...`, `C:/...`, `\\server\share\...` and the POSIX `/...`. Structural, so a
# rename of this folder cannot quietly disarm it.
_ABSOLUTE = re.compile(r"^(?:[A-Za-z]:[\\/]|\\\\|/)")


def _settings_files() -> list[Path]:
    """The settings files that EXIST. The local one is gitignored, so CI has none."""
    return [p for p in (SETTINGS, LOCAL_SETTINGS) if p.is_file()]


def hook_commands(doc: dict) -> list[tuple[str, str, str]]:
    """`(event, matcher, command)` for every hook declared in `doc`.

    The matcher is carried so a failure names the trigger a reader has to look
    for, not just the script.
    """
    rows: list[tuple[str, str, str]] = []
    for event, entries in (doc.get("hooks") or {}).items():
        for entry in entries:
            matcher = entry.get("matcher", "<any>")
            for hook in entry.get("hooks", []):
                rows.append((event, matcher, hook.get("command", "")))
    return rows


def script_tokens(command: str) -> list[str]:
    """Every `.py` token in a command string. Pure, so the arms can drive it.

    A QUOTED chunk is one token even when it contains spaces; only an unquoted
    chunk is split on whitespace. That distinction is the whole correctness of
    this function and it is not theoretical: the first revision split every
    chunk on whitespace, so `"C:\\Legion Wallpaper\\tools\\x.py"` arrived as
    `C:\\Legion` plus `Wallpaper\\tools\\x.py` - the second half ends in `.py`,
    is NOT absolute, and the sweep went green on the very literals it was
    written to catch. The planted arms below are what reported it.

    A trailing flag such as `--inbox-only` never ends in `.py` and drops out by
    itself.
    """
    tokens: list[str] = []
    for index, chunk in enumerate(command.split('"')):
        # Odd indices are the insides of double quotes.
        candidates = [chunk] if index % 2 else chunk.split()
        for token in candidates:
            token = token.strip()
            if token.lower().endswith(".py"):
                tokens.append(token)
    return tokens


def unanchored(command: str) -> list[str]:
    """Script tokens that are absolute rather than `$CLAUDE_PROJECT_DIR`-relative."""
    return [t for t in script_tokens(command)
            if not t.startswith(ANCHOR) and _ABSOLUTE.match(t)]


def repo_relative(token: str) -> str | None:
    """`tools/x.py` for an anchored token, else None. Accepts either separator."""
    if not token.startswith(ANCHOR):
        return None
    tail = token[len(ANCHOR):].lstrip("\\/")
    return PurePosixPath(PureWindowsPath(tail).as_posix()).as_posix()


@pytest.mark.parametrize("path", [pytest.param(p, id=p.name) for p in _settings_files()])
def test_the_settings_file_parses(path: Path):
    """An unparsed settings file registers NO hooks and warns about nothing.

    Its own arm because it is the documented silent-disarm case: it presents
    exactly like a config with no hooks at all. A single backslash before a
    drive letter is not a valid JSON escape, which is the measured way this
    file has been broken on this box before.
    """
    assert isinstance(json.loads(path.read_text(encoding="utf-8")), dict)


def test_the_inventory_is_not_empty():
    """Guard the guard: an empty command list would pass every arm below."""
    rows = hook_commands(json.loads(SETTINGS.read_text(encoding="utf-8")))
    assert len(rows) >= 11, f"only {len(rows)} hook commands found in {SETTINGS}"


def test_no_hook_command_embeds_an_absolute_script_path():
    """The defect itself. A literal path runs the ORIGINAL tree from a clone."""
    offenders = []
    for path in _settings_files():
        doc = json.loads(path.read_text(encoding="utf-8"))
        for event, matcher, command in hook_commands(doc):
            for token in unanchored(command):
                offenders.append(f"{path.name} {event}[{matcher}]: {token}")
    assert not offenders, (
        f"{len(offenders)} hook command(s) name a script by absolute path:\n  "
        + "\n  ".join(offenders)
        + f"\nAnchor it instead: \"{ANCHOR}/tools/<script>.py\". A literal path "
        "makes a clone, a rename or a linked worktree run the ORIGINAL tree's "
        "tooling - the hook fires, exits 0, and gates nothing in the checkout "
        "being edited. Expansion is proven on CLI 2.1.251, including a project "
        "root containing a space.")


def test_every_anchored_script_exists_under_the_repo_root():
    """A hook pointing at a moved script is the same false green in a new costume.

    Stronger than the sibling's basename check on purpose: an anchored path is
    repo-relative, so the FULL path can be resolved - and `$CLAUDE_PROJECT_DIR/
    wrong/place/pytest_guard.py` is exactly what a basename match accepts.
    """
    missing = []
    anchored = 0
    for path in _settings_files():
        doc = json.loads(path.read_text(encoding="utf-8"))
        for event, matcher, command in hook_commands(doc):
            for token in script_tokens(command):
                rel = repo_relative(token)
                if rel is None:
                    continue
                anchored += 1
                if not (REPO_ROOT / rel).is_file():
                    missing.append(f"{path.name} {event}[{matcher}]: {rel}")
    assert not missing, f"anchored hook script(s) absent from this checkout: {missing}"
    assert anchored >= 11, (
        f"only {anchored} anchored script path(s) resolved, so this arm checked "
        "almost nothing - the commands are probably not anchored yet")


# ---------------------------------------------------------------------------
# Detector arms. A sweep that has never been seen to FIRE asserts nothing, and a
# clean result is indistinguishable from an unarmed one.
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("planted", [
    r'pythonw "C:\Legion Wallpaper\tools\precommit_gate.py"',
    'pythonw "C:/Legion Wallpaper/tools/precommit_gate.py"',
    # A RENAMED clone. Matching the repo name would miss this one, which is the
    # scenario the whole file is about.
    r'pythonw "D:\Legion Wallpaper Copy\tools\lw_facts.py" --inbox-only',
    "python /home/runner/work/Legion-Wallpaper/tools/pytest_guard.py",
    r'pythonw "\\legion\share\Legion Wallpaper\tools\lw_facts.py"',
])
def test_a_planted_absolute_script_path_is_caught(planted):
    assert unanchored(planted), f"the detector missed a planted literal: {planted}"


@pytest.mark.parametrize("innocent", [
    'pythonw "$CLAUDE_PROJECT_DIR/tools/precommit_gate.py"',
    'pythonw "$CLAUDE_PROJECT_DIR/tools/lw_facts.py" --inbox-only',
    r'pythonw "$CLAUDE_PROJECT_DIR\tools\install_git_hooks.py" --check',
    # A relative path is not this guard's business: it is resolved against the
    # hook's cwd, which is a different question with a different answer.
    "python tools/pytest_guard.py",
    # No script at all.
    "echo hello",
])
def test_a_legitimate_neighbour_survives(innocent):
    assert not unanchored(innocent), f"false positive on: {innocent}"


@pytest.mark.parametrize(("token", "expected"), [
    ("$CLAUDE_PROJECT_DIR/tools/lw_facts.py", "tools/lw_facts.py"),
    (r"$CLAUDE_PROJECT_DIR\tools\lw_facts.py", "tools/lw_facts.py"),
    ("$CLAUDE_PROJECT_DIR/tools/lw_facts.py".replace("/tools", "//tools"), "tools/lw_facts.py"),
])
def test_the_anchor_is_stripped_the_same_way_on_either_separator(token, expected):
    """CI is Linux and the authored file is Windows, so both separators arrive."""
    assert repo_relative(token) == expected


def test_an_unanchored_token_has_no_repo_relative_form():
    assert repo_relative(r"C:\Legion Wallpaper\tools\lw_facts.py") is None


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
