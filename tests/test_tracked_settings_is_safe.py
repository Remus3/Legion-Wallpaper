"""The TRACKED `.claude/settings.json` must carry repo behaviour and nothing else.

This repo is PUBLIC (Apache-2.0 since 2026-08-01) and, unlike RC, it TRACKS
`.claude/` on purpose: the hook wiring is the gate, and an untracked gate is
unreviewable - a missing script target becomes a silent no-op that no diff ever
shows. That decision is right and this guard exists to keep it affordable.

MEASURED 2026-09-06: the tracked file also carried `bypassPermissions`,
`dangerouslySkipPermissions`, `defaultMode: bypassPermissions`,
`skipDangerousModePermissionPrompt` and a `permissions.allow` of `[".*"]`.

SEVERITY, stated precisely rather than dramatically (corrected 2026-09-06 by a
cross-repo note after the first framing overstated it): Claude Code gates this
ABOVE the settings file - an unfamiliar folder is untrusted, and an untrusted
workspace makes headless silently DISCARD `permissions.allow` (that half is
MEASURED and is in CLAUDE.md; that the same gate covers `bypassPermissions` and
`defaultMode` is the operator's report, not a measurement here). So a cloner
was not being silently handed a bypass. What remains is a category error and
noise - which is enough, because the load-bearing argument never depended on
the disclosure risk. The operator confirmed the bypass posture is MACHINE-WIDE
across all five projects on this box, which is exactly the test for what it is:
a fact about the OPERATOR'S ENVIRONMENT, not about this repository. Uniform
across five trees means it is not repo configuration, so it belongs in the
gitignored `.claude/settings.local.json` (which is where it now lives, and
which takes precedence, so this box behaves identically).

Ruling and reasoning arrived through the cross-repo channel on 2026-09-06 and
LW is the public repo it matters most for. The keys are listed by name below
rather than by heuristic: a heuristic that tries to guess "is this preference
or behaviour" would be argued with, and the argument is the failure mode.

`tools/drift_guard.py::scan_settings` already flags a wildcard allow list and
an allow-with-empty-deny, but it scans whatever file it is given. This asserts
the tracked file in THIS repo, which is the one that gets published.
"""
from __future__ import annotations

import json
from pathlib import Path, PureWindowsPath

ROOT = Path(__file__).resolve().parent.parent
TRACKED = ROOT / ".claude" / "settings.json"

# Operator environment / posture. None of these is a fact about the repository,
# and the first four disable permission prompts for anyone who clones it.
BANNED_KEYS = (
    "bypassPermissions",
    "dangerouslySkipPermissions",
    "defaultMode",
    "skipDangerousModePermissionPrompt",
    "permissions",
    "model",
    "effortLevel",
    "theme",
    "statusLine",
    "enabledPlugins",
    "autoUpdates",
    "spinnerTipsEnabled",
    "agentPushNotifEnabled",
    "prefersReducedMotion",
)

# What the tracked file is FOR. Asserted so a future "cleanup" that empties it
# cannot pass this guard by deleting the thing it protects.
REQUIRED_KEYS = ("env", "hooks")


def _tracked() -> dict:
    raw = TRACKED.read_text(encoding="utf-8")
    # Validity first: an unparsed settings file registers NO hooks and warns
    # about nothing, so it presents exactly like hooks that do not fire. A
    # single backslash before a drive letter is not a valid JSON escape - that
    # is a measured failure on this box, not a hypothetical (CLAUDE.md).
    return json.loads(raw)


def test_the_tracked_settings_file_parses():
    assert isinstance(_tracked(), dict)


def test_no_operator_posture_or_preference_keys_are_published():
    present = [k for k in BANNED_KEYS if k in _tracked()]
    assert not present, (
        f"{present} are in the TRACKED .claude/settings.json. These describe "
        "the operator's environment, not this repository - the bypass posture "
        "is identical across all five projects on this box, which is what "
        "makes it environment. Move them to .claude/settings.local.json, "
        "which is gitignored and takes precedence, so this box is unaffected. "
        "The first four are permission posture, which the app gates on "
        "workspace trust anyway - a category error rather than a hazard, "
        "and it belongs in the local file for the same reason either way.")


def test_the_hook_wiring_is_still_tracked():
    """The reason LW tracks this file at all, unlike RC which ignores it."""
    doc = _tracked()
    for key in REQUIRED_KEYS:
        assert key in doc, (
            f"the tracked settings file no longer declares `{key}` - the hook "
            "wiring being versioned and reviewable is the entire reason this "
            "file is tracked in the first place")
    events = doc["hooks"]
    assert isinstance(events, dict) and events, "hooks block is empty"
    # Every declared hook must name a command; an event with no command is the
    # "declared but wired to nothing" shape this channel has hit twice.
    for event, entries in events.items():
        for entry in entries:
            for hook in entry.get("hooks", []):
                assert hook.get("command"), f"{event}: a hook entry has no command"


def test_every_declared_hook_script_exists():
    """A declared hook whose script is missing is a gate that silently is not there.

    RC shipped exactly this: a SessionStart hook naming a script that did not
    exist, dead with no warning, and invisible because the declaring file was
    untracked. Tracking the file is only half the fix; this is the other half.

    Matched on BASENAME against the repo tree, never on the absolute path in the
    command: the commands carry Windows paths and CI runs on Linux, where
    a Windows absolute path is not a path at all, so `is_file()` is False for
    every hook and this guard would fail on a perfectly healthy tree.
    PureWindowsPath is what makes the basename come out right off-Windows.
    """
    present = {p.name for p in ROOT.rglob("*.py") if "__pycache__" not in p.parts}
    missing = []
    for event, entries in _tracked()["hooks"].items():
        for entry in entries:
            for hook in entry.get("hooks", []):
                for token in hook.get("command", "").split('"'):
                    if token.lower().endswith(".py"):
                        name = PureWindowsPath(token).name
                        if name not in present:
                            missing.append((event, name))
    assert not missing, f"hook script(s) declared but absent from the tree: {missing}"
