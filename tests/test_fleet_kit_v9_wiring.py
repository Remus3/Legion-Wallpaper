"""FLEET-KIT v9 tree wiring (MAIN 2354 section 2 steps 2-4; FLEET-COMMON item 15).

The kit's own conformance() pins the vendored bytes and the FLEET-COMMON block;
it does not see how a tree WIRES the kit. These arms do:
  * the tracked Stop hook runs the kit's `fleet_done.py stop-hook`, anchored to
    $CLAUDE_PROJECT_DIR so it survives the drive move;
  * no tree-level display key (the kit's cli_display.json `tree_forbidden`
    list) appears anywhere in the tracked settings, top level or nested;
  * /done's last act is `fleet_done.py mark`, before the one chat line, with a
    `--status failed` path for a step that stopped it;
  * the marker and its seen-file are gitignored (runtime state, never tracked).

Hermetic: reads tracked bytes only. The gitignored settings.local.json is the
operator's machine state and is checked by measurement, not here.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KIT = ROOT / "ops" / "fleet_kit"
SETTINGS = ROOT / ".claude" / "settings.json"
DONE_MD = ROOT / ".claude" / "commands" / "done.md"
_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0) if sys.platform == "win32" else 0


def _forbidden() -> list[str]:
    return json.loads((KIT / "cli_display.json").read_text(encoding="ascii"))["tree_forbidden"]


def _keys(node) -> set[str]:
    """Every dict key at any depth."""
    found: set[str] = set()
    if isinstance(node, dict):
        for k, v in node.items():
            found.add(k)
            found |= _keys(v)
    elif isinstance(node, list):
        for v in node:
            found |= _keys(v)
    return found


def test_keys_walk_sees_a_nested_display_key():
    """Guard the guard: a key one level down must not slip past the walk."""
    assert "theme" in _keys({"permissions": {"x": [{"theme": "dark"}]}})


def test_tracked_settings_set_no_display_key_at_any_depth():
    present = sorted(set(_forbidden()) & _keys(json.loads(SETTINGS.read_text(encoding="utf-8"))))
    assert not present, f"tree-level display keys {present}: they live only in the account settings"


def test_stop_hook_runs_the_kit_done_hook_anchored_to_the_project_dir():
    stop = json.loads(SETTINGS.read_text(encoding="utf-8"))["hooks"]["Stop"]
    cmds = [h["command"] for entry in stop for h in entry["hooks"]]
    hits = [c for c in cmds if "ops/fleet_kit/fleet_done.py" in c and c.rstrip().endswith("stop-hook")]
    assert len(hits) == 1, cmds
    assert "$CLAUDE_PROJECT_DIR/ops/fleet_kit/fleet_done.py" in hits[0]


def test_done_ritual_marks_before_the_one_chat_line():
    text = DONE_MD.read_text(encoding="ascii")
    final = text[text.index("### 9."):text.index("### Safety rails")]
    mark = final.find("ops/fleet_kit/fleet_done.py mark --session")
    line = final.find("Done ritual complete, safe to clear")
    assert 0 <= mark < line, "fleet_done.py mark must be the last act before the chat line"
    assert "--status done" in final
    assert "--status failed --reason" in final


def test_done_marker_files_are_gitignored():
    for rel in ("ops/loop/control/session_done.json", "ops/loop/control/session_done.seen"):
        r = subprocess.run(["git", "-C", str(ROOT), "check-ignore", "-v", "--no-index", rel],
                           capture_output=True, text=True, creationflags=_NO_WINDOW)
        # check-ignore can exit 0 with an EMPTY pattern column; parse the column.
        pattern = r.stdout.split("\t")[0].split(":", 2)[-1] if r.stdout else ""
        assert r.returncode == 0 and pattern, f"{rel} is not gitignored: {r.stdout!r}"
