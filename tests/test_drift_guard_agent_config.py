"""Tests for drift_guard's agent-config checks.

These exist because both failure modes ALREADY HAPPENED on this box and are
written up in CLAUDE.md, but nothing checked for them afterwards:

  * an invalid `.claude/settings.json` (single backslashes in a Windows path are
    not valid JSON escapes) is silently unparsed, which produced a false
    "hooks do not fire" conclusion in two arms of a probe;
  * `~/.claude.json` project keys are path-separator- and case-sensitive, and LW
    carried THREE keys for one directory with the forward-slash one reading
    False - so headless silently discarded `permissions.allow`.

The check surface is adapted from ECC/AgentShield's published scan list
(settings, hooks, agents, secrets), keeping only what maps to a real LW risk.

Pure functions take data, not paths, so every test runs offline with no config
on disk. Written test-first per CLAUDE.md TDD.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

import drift_guard as DG  # noqa: E402


# ---------------------------------------------------------------------------
# settings.json
# ---------------------------------------------------------------------------
def test_scan_settings_flags_invalid_json_first():
    """The documented incident: unparsed config reads as 'no hooks configured'.

    A single backslash before a drive letter is not a valid JSON escape.
    """
    bad = '{"hooks": {"PreToolUse": [{"command": "C:\\Users\\x\\py.exe"}]}}'
    issues = DG.scan_settings(bad)
    assert any("invalid json" in i.lower() for i in issues)


def test_scan_settings_accepts_a_correctly_escaped_windows_path():
    good = r'{"permissions": {"allow": [], "deny": ["Bash(rm:*)"]},' \
           r' "hooks": {"PreToolUse": []}}'
    good = good.replace('"allow": []', '"allow": ["Bash(git status:*)"]')
    issues = DG.scan_settings(good)
    assert not any("invalid json" in i.lower() for i in issues)


def test_scan_settings_flags_a_wildcard_allow():
    issues = DG.scan_settings('{"permissions": {"allow": ["Bash(*)"], "deny": ["x"]}}')
    assert any("wildcard" in i.lower() for i in issues)


def test_scan_settings_notes_an_empty_deny_list():
    issues = DG.scan_settings('{"permissions": {"allow": ["Bash(ls:*)"], "deny": []}}')
    assert any("deny" in i.lower() for i in issues)


def test_scan_settings_is_quiet_on_a_sane_config():
    ok = '{"permissions": {"allow": ["Bash(ls:*)"], "deny": ["Bash(rm:*)"]}}'
    assert DG.scan_settings(ok) == []


# ---------------------------------------------------------------------------
# hook scripts
# ---------------------------------------------------------------------------
def test_scan_hook_script_flags_silent_suppression():
    """A hook that swallows its own errors is a gate that fails open - the exact
    shape of the `precommit_gate.py` no-arg no-op already recorded in CLAUDE.md.
    """
    issues = DG.scan_hook_script("subprocess.run(cmd) 2>/dev/null || true", "h.sh")
    assert any("suppress" in i.lower() for i in issues)


def test_scan_hook_script_flags_network_and_shell_true():
    issues = DG.scan_hook_script(
        "import requests\nsubprocess.run(c, shell=True)", "h.py")
    assert any("network" in i.lower() for i in issues)
    assert any("shell=true" in i.lower() for i in issues)


def test_scan_hook_script_is_quiet_on_the_real_guards():
    """LW's actual guards must not trip this, or the check is noise."""
    text = (Path(__file__).resolve().parents[1]
            / "tools" / "text_first_guard.py").read_text(encoding="utf-8")
    assert DG.scan_hook_script(text, "text_first_guard.py") == []


# ---------------------------------------------------------------------------
# ~/.claude.json project-key collisions
# ---------------------------------------------------------------------------
def test_collide_path_keys_finds_a_trust_mismatch():
    """Two spellings of one directory disagreeing on trust is the live bug: the
    losing spelling silently discards permissions in a headless run."""
    projects = {
        r"C:\Lanternlight": {"hasTrustDialogAccepted": True},
        "C:/Lanternlight": {"hasTrustDialogAccepted": False},
    }
    out = DG.collide_path_keys(projects)
    assert len(out) == 1
    norm, keys, trusts = out[0]
    assert norm == r"c:\lanternlight"
    assert set(trusts) == {True, False}


def test_collide_path_keys_ignores_agreeing_duplicates():
    """Duplicate spellings that agree are untidy but harmless - reporting them
    would bury the one case that actually breaks a run."""
    projects = {
        r"C:\Legion-Wallpaper": {"hasTrustDialogAccepted": True},
        "C:/Legion-Wallpaper": {"hasTrustDialogAccepted": True},
        "C:/legionwallpaper": {"hasTrustDialogAccepted": True},
    }
    assert DG.collide_path_keys(projects) == []


def test_collide_path_keys_handles_trailing_separators_and_case():
    projects = {
        "C:/Monster/": {"hasTrustDialogAccepted": False},
        r"C:\monster": {"hasTrustDialogAccepted": True},
    }
    out = DG.collide_path_keys(projects)
    assert len(out) == 1 and out[0][0] == r"c:\monster"


def test_collide_path_keys_empty_input_is_clean():
    assert DG.collide_path_keys({}) == []


def test_check_agent_config_does_not_report_the_scanner_itself():
    """drift_guard defines the detection strings literally, so scanning itself
    yields all three findings and buries the real ones. Regression for exactly
    that: the first live run reported drift_guard.py three times.
    """
    DG.problems.clear()
    DG.notes.clear()
    DG.check_agent_config()
    assert not [p for p in DG.problems if "drift_guard.py" in p]


def test_other_projects_key_collisions_are_notes_not_breaches():
    """Another repo's broken key is worth surfacing but must not wedge LW's
    /done behind a fix nobody in this repo owns. Only LW's own key breaches.

    Projects are INJECTED. The first version of this test read the operator's
    real ~/.claude.json, so it passed locally and failed in CI where no such
    file exists - a machine-dependent test, and the exact failure the repo's
    verification discipline is written to prevent.
    """
    projects = {
        r"C:\Lanternlight": {"hasTrustDialogAccepted": True},
        "C:/Lanternlight": {"hasTrustDialogAccepted": False},
    }
    DG.problems.clear()
    DG.notes.clear()
    DG.check_claude_path_keys(projects)
    assert DG.problems == []
    assert any("lanternlight" in n.lower() for n in DG.notes)


def test_this_projects_key_collision_is_a_breach():
    """LW's own key IS a breach - it disarms this repo's own headless runs."""
    root = str(DG.ROOT).replace("/", "\\").rstrip("\\")
    projects = {
        root: {"hasTrustDialogAccepted": True},
        root.replace("\\", "/"): {"hasTrustDialogAccepted": False},
    }
    DG.problems.clear()
    DG.notes.clear()
    DG.check_claude_path_keys(projects)
    assert len(DG.problems) == 1 and "DISAGREEING" in DG.problems[0]
