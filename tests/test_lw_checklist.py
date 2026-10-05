"""FLEET-COMMON item 13 (FLEET-KIT v7, MAIN 0215): the session checklist in LW.

tools/lw_checklist.py is LW's thin binding of the kit's fleet_checklist.py:
the session-start block (SessionStart hook, counter from the hand-off's
`SESSION: <n>` line, tasks from its `CHECKLIST:` section), the headless-fire
helper that writes the remaining list into an item-12 progress file, and the
`progress` CLI a spawned child uses.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import lw_checklist as lc  # noqa: E402

BOX = "☐"

HANDOFF = """NEXT SESSION
------------
SESSION: 63
Task: tally R4
CHECKLIST:
  - R4: Tally the R4 blind A/B once the operator has voted
  - R5c: Run the pre-registered DINOv2 layer-12 check
Context: x
"""


def test_the_kit_module_is_the_vendored_one():
    assert Path(lc.kit_checklist().__file__).resolve() == (
        ROOT / "ops" / "fleet_kit" / "fleet_checklist.py").resolve()
    assert lc.kit_checklist().BOX == BOX


def test_session_number_is_read_from_the_handoff():
    assert lc.handoff_session(HANDOFF) == 63
    assert lc.handoff_session("NEXT SESSION\nTask: x\n") is None


def test_items_are_read_from_the_checklist_section():
    assert lc.handoff_items(HANDOFF) == [
        ("R4", "Tally the R4 blind A/B once the operator has voted"),
        ("R5c", "Run the pre-registered DINOv2 layer-12 check")]


def test_without_a_checklist_section_the_task_line_is_the_one_item():
    items = lc.handoff_items("NEXT SESSION\nTask: tally R4 votes\nContext: y\n")
    assert items == [("T1", "tally R4 votes")]


def test_session_start_block_is_the_item_13a_shape():
    text = lc.session_start_block(HANDOFF)
    lines = text.splitlines()
    assert lines[0] == "Session 63 checklist"
    assert lines[1] == f"{BOX} R4: Tally the R4 blind A/B once the operator has voted"
    assert lines[2] == f"{BOX} R5c: Run the pre-registered DINOv2 layer-12 check"
    assert lines[3] == f"{BOX} /done"
    assert len(lines) == 4


def test_session_start_hook_prints_the_block_utf8(tmp_path):
    (tmp_path / "LW-NEXT-SESSION.txt").write_text(HANDOFF, encoding="ascii")
    r = subprocess.run([sys.executable, str(ROOT / "tools" / "lw_checklist.py"),
                        "session-start", "--root", str(tmp_path)],
                       capture_output=True, timeout=60,
                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    assert r.returncode == 0, r.stderr
    out = r.stdout.decode("utf-8")
    assert "Session 63 checklist" in out
    assert f"{BOX} /done" in out
    assert "FLEET-COMMON item 13" in out, "the hook tells the session what to do with it"


def test_session_start_hook_never_fails_a_session(tmp_path):
    r = subprocess.run([sys.executable, str(ROOT / "tools" / "lw_checklist.py"),
                        "session-start", "--root", str(tmp_path / "absent")],
                       capture_output=True, timeout=60,
                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    assert r.returncode == 0
    assert "Session ? checklist" in r.stdout.decode("utf-8")


def test_the_hook_is_registered_at_session_start():
    cfg = json.loads((ROOT / ".claude" / "settings.json").read_text(encoding="utf-8"))
    cmds = [h["command"] for grp in cfg["hooks"]["SessionStart"] for h in grp["hooks"]]
    assert any("tools/lw_checklist.py" in c and "session-start" in c for c in cmds)


# ---------------------------------------------------------------- headless fire

def _read(root, task):
    return json.loads((root / "ops" / "loop" / "control" / "progress" / f"{task}.json")
                      .read_text(encoding="utf-8"))


def test_a_fire_writes_its_checklist_at_start_and_after_every_task(tmp_path):
    logged = []
    fire = lc.Fire(tmp_path, "lane-0", 7,
                   [("D", "Get the cycle directive"), ("X", "Run the executor call")],
                   log=logged.append)
    fire.start()
    doc = _read(tmp_path, "lane-0")
    assert doc["status"] == "running" and doc["pct"] == 0
    assert [r["id"] for r in doc["checklist"]] == ["D", "X"]
    assert logged and logged[0].splitlines()[0] == "Session 7 checklist"
    fire.running("D", "director running", 90)
    assert _read(tmp_path, "lane-0")["checklist"][0]["state"] == "director running"
    fire.complete("D")
    doc = _read(tmp_path, "lane-0")
    assert [r["id"] for r in doc["checklist"]] == ["X"], "remaining tasks only"
    assert doc["pct"] == 50
    fire.complete("X")
    fire.close()
    doc = _read(tmp_path, "lane-0")
    assert doc["status"] == "done" and doc["checklist"] == [] and doc["pct"] == 100


def test_a_failed_fire_keeps_its_remaining_tasks(tmp_path):
    fire = lc.Fire(tmp_path, "inbox-responder", 3, [("N1", "Answer a note")])
    fire.start()
    fire.close("failed", "spawn raised")
    doc = _read(tmp_path, "inbox-responder")
    assert doc["status"] == "failed" and [r["id"] for r in doc["checklist"]] == ["N1"]


def test_a_fire_that_cannot_write_never_raises(tmp_path):
    blocker = tmp_path / "ops"
    blocker.write_text("a file where a directory must go", encoding="ascii")
    fire = lc.Fire(tmp_path, "lane-1", 1, [("A", "Do a thing")])
    fire.start()
    fire.complete("A")
    fire.close()


def test_the_remaining_update_is_logged_after_four_completions(tmp_path):
    logged = []
    fire = lc.Fire(tmp_path, "lane-2", 2, [(f"T{i}", f"task {i}") for i in range(6)],
                   log=logged.append)
    fire.start()
    for i in range(4):
        fire.complete(f"T{i}")
    assert logged[-1].splitlines()[0] == "Session 2 checklist - remaining"
    assert "T0" not in logged[-1] and "T4" in logged[-1]


def test_progress_cli_writes_the_item_13d_field(tmp_path):
    rows = json.dumps([{"id": "C1", "task": "Vendor kit", "state": "builder running",
                        "eta_s": 240}])
    r = subprocess.run([sys.executable, str(ROOT / "tools" / "lw_checklist.py"), "progress",
                        "--root", str(tmp_path), "--task", "responder-run", "--pct", "10",
                        "--step", "C1", "--eta", "600", "--status", "running",
                        "--checklist", rows],
                       capture_output=True, timeout=60,
                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    assert r.returncode == 0, r.stderr
    doc = _read(tmp_path, "responder-run")
    assert doc["checklist"] == [{"id": "C1", "task": "Vendor kit",
                                 "state": "builder running", "eta_s": 240}]


@pytest.mark.parametrize("bad", ["not json", json.dumps([{"id": "", "task": "x"}])])
def test_progress_cli_refuses_a_bad_checklist(tmp_path, bad):
    r = subprocess.run([sys.executable, str(ROOT / "tools" / "lw_checklist.py"), "progress",
                        "--root", str(tmp_path), "--task", "t", "--pct", "0", "--step", "s",
                        "--eta", "0", "--status", "running", "--checklist", bad],
                       capture_output=True, timeout=60,
                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    assert r.returncode == 2


def test_child_rule_names_the_task_and_the_run_count():
    rule = lc.child_rule("responder-run-12", 12)
    assert "Session 12 checklist" in rule
    assert "responder-run-12" in rule
    assert "tools/lw_checklist.py progress" in rule
    assert rule.isascii()


# ---------------------------------------------------------------- /done path

def test_done_command_carries_the_item_13_preflight_and_counter():
    text = (ROOT / ".claude" / "commands" / "done.md").read_text(encoding="ascii")
    assert "every checklist task done or carried into the hand-off" in text
    assert "SESSION: <n+1>" in text
    assert "run UNPROMPTED once no checklist task remains" in text


def test_claude_md_names_the_counter_and_the_code_paths_below_the_block():
    text = (ROOT / "CLAUDE.md").read_text(encoding="ascii")
    tail = text.split("<!-- FLEET-COMMON END -->", 1)[1]
    assert "Session checklist (FLEET-COMMON item 13" in tail
    for path in ("tools/lw_checklist.py", "LW-NEXT-SESSION.txt", "ops/loop/loop_controller.py",
                 "tools/lw_inbox_responder.py"):
        assert path in tail, path
