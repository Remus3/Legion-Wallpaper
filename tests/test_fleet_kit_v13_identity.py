"""FLEET-KIT v13 NO AI OR BOT ATTRIBUTION (FLEET-COMMON 17; MAIN's staged v13
bundle 2026-10-08-2128, GH-HYGIENE ruling 2026-10-08).

conformance() pins the vendored bytes; these arms pin how LW WIRES them:
  * the tracked .githooks/commit-msg calls `fleet_identity.py commit-msg "$1"`
    and never fails a commit on it (fail open, but loud on stderr); the tracked .githooks/pre-push
    calls `fleet_identity.py pre-push "$@"` and refuses on it (`|| exit 1`);
    both match the regex MAIN's drift sweep (f) uses;
  * install_git_hooks.py --check (drift_guard) requires both, so a hook edit
    that drops either goes red;
  * the tracked .claude/settings.json sets none of the v13 tree_forbidden
    attribution keys (they live in the account settings only).

Hermetic: tracked bytes and pure functions; no git config is read or written.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import install_git_hooks as igh  # noqa: E402

HOOKS = ROOT / ".githooks"
# MAIN tools/fleet_kit.py identity_hook_problems(): the drift sweep's needle.
_DRIFT = r"fleet_identity\.py[\"']?\s+{}"


def _hook(name):
    return (HOOKS / name).read_text(encoding="utf-8")


def test_commit_msg_hook_strips_attribution_and_never_rejects():
    body = _hook("commit-msg")
    assert re.search(_DRIFT.format("commit-msg"), body)
    line = next(ln for ln in body.splitlines() if "fleet_identity.py" in ln)
    # Fail open but loud: an `if ! ...; then echo >&2; fi` guard, never
    # `|| true` (drift_guard bans silent suppression) and never `|| exit`.
    assert line.strip().startswith("if ! ") and line.strip().endswith('commit-msg "$1"; then'), line
    assert "ops/fleet_kit/fleet_identity.py" in line
    assert "|| true" not in body


def test_commit_msg_hook_passes_drift_guard():
    import drift_guard
    assert drift_guard.scan_hook_script(_hook("commit-msg"), "commit-msg") == []
    assert drift_guard.scan_hook_script(_hook("pre-push"), "pre-push") == []


def test_commit_msg_hook_strips_before_the_message_gates_read_it():
    body = _hook("commit-msg")
    assert body.index("fleet_identity.py") < body.index("precommit_msg_check.py")


def test_pre_push_hook_refuses_on_an_identity_violation():
    body = _hook("pre-push")
    assert body.startswith("#!/bin/sh\n")
    assert re.search(_DRIFT.format("pre-push"), body)
    line = next(ln for ln in body.splitlines() if "fleet_identity.py" in ln)
    assert line.strip().endswith('pre-push "$@" || exit 1'), line
    assert "ops/fleet_kit/fleet_identity.py" in line


def test_hook_installer_requires_both_identity_hooks():
    need = igh.IDENTITY_REQUIRED
    assert set(need) == {"commit-msg", "pre-push"}
    for name, needle in need.items():
        assert needle in _hook(name), name


def test_tracked_settings_set_no_tree_forbidden_display_key():
    spec = json.loads((ROOT / "ops" / "fleet_kit" / "cli_display.json").read_text(encoding="utf-8"))
    forbidden = set(spec["tree_forbidden"])
    assert {"attribution", "includeCoAuthoredBy"} <= forbidden
    for f in (ROOT / ".claude" / "settings.json",):
        keys = set(json.loads(f.read_text(encoding="utf-8")))
        assert not keys & forbidden, (f.name, keys & forbidden)


def test_identity_log_is_gitignored_by_an_explicit_line():
    lines = (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
    assert "ops/loop/control/identity.jsonl" in lines
