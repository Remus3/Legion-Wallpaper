"""SUBMIT records who submitted (2026-10-04, LEDGER 268 defect 4).

Before: `cmd_submit` had no actor and logged `actor=operator` for every submit,
including the 287 unattended 2026-08-22 dispose submits. The CLI default is
now `unattributed` (honest: the pipeline cannot know who typed the command),
and every tool caller passes `tool:<name>`.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import lw_pipeline as lw  # noqa: E402

STAGE_FOLDERS = [
    "0.Originals", "1.First Pass Scratch", "2.First Pass Done",
    "3.Cleaning Scratch", "4.Cleaning Done", "5.Final Scratch",
    "6.Final Done", "7.Last Scratch", "8.End Review", "9.Image Backup",
]


@pytest.fixture()
def root(tmp_path: Path) -> Path:
    r = tmp_path / "images"
    for name in STAGE_FOLDERS + ["reference_pictures"]:
        (r / name).mkdir(parents=True)
    return r


@pytest.fixture(autouse=True)
def _fast_gate(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(lw, "PROBE_SECONDS", 0.0)


def run(root: Path, *args: str) -> int:
    return lw.main(["--root", str(root), *args])


def _ready_to_submit(root: Path, tmp: Path) -> Path:
    p = root / "0.Originals" / "ahri.png"
    p.write_bytes(b"orig-ahri")
    old = p.stat().st_mtime - 120
    os.utime(p, (old, old))
    assert run(root, "intake", "--all") == 0
    src = tmp / "edit.png"
    src.write_bytes(b"edited")
    assert run(root, "save-working", "ahri", "--from", str(src)) == 0
    return root / "1.First Pass Scratch" / "ahri"


def _submit_log_line(root: Path) -> str:
    log = (root.parent / "PIPELINE_LOG.md").read_text(encoding="ascii")
    lines = [ln for ln in log.splitlines() if " | SUBMIT | " in ln]
    assert len(lines) == 1, lines
    return lines[0]


def _submit_transition(folder: Path) -> dict:
    man = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
    subs = [t for t in man["transitions"] if t["op"] == "SUBMIT"]
    assert len(subs) == 1
    return subs[0]


def test_submit_records_the_passed_actor(root, tmp_path):
    folder = _ready_to_submit(root, tmp_path)
    assert run(root, "submit", "ahri", "--actor", "tool:lw_first_pass") == 0
    assert "| actor=tool:lw_first_pass |" in _submit_log_line(root)
    assert _submit_transition(folder)["actor"] == "tool:lw_first_pass"


def test_submit_default_actor_is_not_a_claim_of_operator(root, tmp_path):
    folder = _ready_to_submit(root, tmp_path)
    assert run(root, "submit", "ahri") == 0
    assert "| actor=unattributed |" in _submit_log_line(root)
    assert _submit_transition(folder)["actor"] == "unattributed"


def test_operator_can_still_say_so(root, tmp_path):
    _ready_to_submit(root, tmp_path)
    assert run(root, "submit", "ahri", "--actor", "operator") == 0
    assert "| actor=operator |" in _submit_log_line(root)


# ---- every tool caller names itself ------------------------------------

def _actor_of(argv):
    assert "--actor" in argv, argv
    return argv[argv.index("--actor") + 1]


def test_clean_pass_submit_cmd_names_the_tool():
    import lw_clean_pass as lcp
    assert _actor_of(lcp.build_submit_cmd("s")) == "tool:lw_clean_pass"
    save, sub = lcp.build_cleanscan_cmds("s", "i.png")
    assert _actor_of(sub) == "tool:lw_clean_pass"
    _, sub2 = lcp.build_cleanscan_cmds("s", "i.png", actor="tool:x")
    assert _actor_of(sub2) == "tool:x"


def test_iopaint_submit_cmd_names_the_tool():
    import lw_clean_iopaint as lci
    assert _actor_of(lci.build_submit_cmd("s")) == "tool:lw_clean_iopaint"


def test_dispose_clean_scan_submit_names_dispose(monkeypatch):
    import lw_clean_dispose as disp
    monkeypatch.setattr(disp, "cleanscan_source", lambda slug: "init.png")
    rec = disp.drive("slug-a", "clean", "img.png", dry_run=True)
    subs = [s["argv"] for s in rec["steps"] if s["argv"][2] == "submit"]
    assert len(subs) == 1
    assert _actor_of(subs[0]) == "tool:lw_clean_dispose"


def test_first_pass_submit_names_the_tool(monkeypatch):
    import lw_first_pass as lfp
    seen = []

    class _P:
        returncode = 0
        stdout = ""
        stderr = ""

    monkeypatch.setattr(lfp, "_pipeline", lambda *a: seen.append(a) or _P())
    lfp.pipeline_submit("s")
    assert _actor_of(list(seen[0])) == "tool:lw_first_pass"
