"""Each LW scheduled job appends ONE run record per run (ingest P0-4).

The record is the status the job says about its own run - not its exit code -
and it is what tools/lw_job_health.py judges. conftest points LW_RUNLOG_ROOT
at a per-test dir, so these arms read the record each job wrote.
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import lw_inbox_responder as responder  # noqa: E402
import lw_wallpaper_rotate as rot  # noqa: E402


def _rows(task: str) -> list[dict]:
    p = Path(os.environ["LW_RUNLOG_ROOT"]) / f"{task}.jsonl"
    if not p.exists():
        return []
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines()]


# -- responder ----------------------------------------------------------------

def _resp(monkeypatch, tmp_path, *, inbox=True):
    monkeypatch.setattr(responder, "HALT_PATH", tmp_path / "never-HALT")
    monkeypatch.setattr(responder, "_publish", lambda *a, **k: None)
    box = tmp_path / "inbox"
    if inbox:
        box.mkdir(exist_ok=True)
    (tmp_path / "seen.json").write_text(json.dumps({"seen": []}), encoding="utf-8")
    return ["--once", "--inbox", str(box), "--state", str(tmp_path / "seen.json"),
            "--runlog", str(tmp_path / "runs.jsonl")]


def test_an_idle_responder_tick_records_ok(tmp_path, monkeypatch, capsys):
    responder.main(_resp(monkeypatch, tmp_path))
    rows = _rows("LW-InboxResponder")
    assert [r["status"] for r in rows] == ["ok"]


def test_a_responder_tick_with_an_unreadable_inbox_records_partial(tmp_path, monkeypatch, capsys):
    responder.main(_resp(monkeypatch, tmp_path, inbox=False))
    assert [r["status"] for r in _rows("LW-InboxResponder")] == ["partial"]


def test_a_refused_spawn_records_partial_though_the_tick_exits_0(tmp_path, monkeypatch, capsys):
    argv = _resp(monkeypatch, tmp_path)
    (tmp_path / "inbox" / "2026-10-04-0001-from-RC-note.md").write_text("n", encoding="utf-8")
    monkeypatch.setattr(responder, "spawn", lambda *a, **k: responder.Disposition(
        responder.UNAVAILABLE, "spawn", "headless spawn refused: x", True))
    assert responder.main(argv) == 0
    rows = _rows("LW-InboxResponder")
    assert rows[-1]["status"] == "partial" and "not run" in rows[-1]["detail"]


def test_a_halted_responder_records_skipped(tmp_path, monkeypatch, capsys):
    argv = _resp(monkeypatch, tmp_path)
    halt = tmp_path / "HALT"
    halt.write_text("", encoding="ascii")
    monkeypatch.setattr(responder, "HALT_PATH", halt)
    responder.main(argv)
    assert [r["status"] for r in _rows("LW-InboxResponder")] == ["halted"]


def test_a_dry_run_responder_records_nothing(tmp_path, monkeypatch, capsys):
    responder.main(_resp(monkeypatch, tmp_path) + ["--dry-run"])
    assert _rows("LW-InboxResponder") == []


# -- CI watchdog --------------------------------------------------------------

def _cw():
    spec = importlib.util.spec_from_file_location("lw_ci_watchdog_runlog_t",
                                                  ROOT / "tools" / "ci_watchdog.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


cw = _cw()


def _cw_pass(monkeypatch, tmp_path, ci, fix=True, dry_run=False):
    monkeypatch.setattr(cw, "STATE_DIR", tmp_path / "logs")

    class _TG:
        @staticmethod
        def check_ci(_ref):
            return ci
    monkeypatch.setattr(cw, "_bind_truth_gate", lambda: _TG)
    monkeypatch.setattr(cw, "do_fix_pass", lambda *a, **k: fix)
    return cw.one_pass(model=None, dry_run=dry_run, max_attempts=2, fix_timeout=1,
                       state_dir=tmp_path)


RED = {"status": "failure", "sha": "d" * 40, "runs": []}


def test_a_green_watchdog_pass_records_ok(tmp_path, monkeypatch):
    _cw_pass(monkeypatch, tmp_path, {"status": "success", "sha": "e" * 40})
    rows = _rows("LW-CIWatchdog")
    assert [r["status"] for r in rows] == ["ok"] and "idle" in rows[0]["detail"]


def test_an_unavailable_ci_read_records_partial(tmp_path, monkeypatch):
    _cw_pass(monkeypatch, tmp_path, {"status": "unavailable", "sha": "HEAD"})
    assert [r["status"] for r in _rows("LW-CIWatchdog")] == ["partial"]


def test_a_refused_fix_records_failed(tmp_path, monkeypatch):
    assert _cw_pass(monkeypatch, tmp_path, RED, fix="refused") == 1
    assert [r["status"] for r in _rows("LW-CIWatchdog")] == ["failed"]


def test_a_halted_watchdog_records_skipped(tmp_path, monkeypatch):
    (tmp_path / "HALT").write_text("", encoding="ascii")
    _cw_pass(monkeypatch, tmp_path, RED)
    assert [r["status"] for r in _rows("LW-CIWatchdog")] == ["halted"]


def test_a_dry_run_watchdog_records_nothing(tmp_path, monkeypatch):
    _cw_pass(monkeypatch, tmp_path, RED, dry_run=True)
    assert _rows("LW-CIWatchdog") == []


# -- wallpaper ----------------------------------------------------------------

def _wall_cfg(tmp_path) -> Path:
    src = tmp_path / "Pictures"
    src.mkdir()
    (src / "a.png").write_bytes(b"x")
    cfg = {"source_dir": str(src), "interval_minutes": 3,
           "state_path": str(tmp_path / "deck.json"), "extensions": [".png"]}
    p = tmp_path / "cfg.json"
    p.write_text(json.dumps(cfg), encoding="utf-8")
    return p


def test_a_wallpaper_tick_that_sets_an_image_records_ok(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(rot, "LOG_DIR", tmp_path / "logs")
    monkeypatch.setattr(rot, "set_wallpaper", lambda p: True)
    assert rot.main(["tick", "--config", str(_wall_cfg(tmp_path))]) == 0
    assert [r["status"] for r in _rows("LW-Wallpaper")] == ["ok"]


def test_a_wallpaper_tick_that_fails_to_set_records_failed(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(rot, "LOG_DIR", tmp_path / "logs")
    monkeypatch.setattr(rot, "set_wallpaper", lambda p: False)
    rot.main(["tick", "--config", str(_wall_cfg(tmp_path))])
    assert [r["status"] for r in _rows("LW-Wallpaper")] == ["failed"]


def test_a_dry_run_wallpaper_tick_records_nothing(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(rot, "LOG_DIR", tmp_path / "logs")
    rot.main(["tick", "--dry-run", "--config", str(_wall_cfg(tmp_path))])
    assert _rows("LW-Wallpaper") == []


# -- weekly hygiene (PowerShell) ---------------------------------------------

def test_every_hygiene_exit_path_records_a_status_first():
    """Static arm over the .ps1: each `exit` is preceded by a Write-RunRecord,
    and the data rides as arguments (no stdin pipe into python)."""
    lines = (ROOT / "tools" / "weekly_hygiene_run.ps1").read_text(encoding="utf-8").splitlines()
    exits = [i for i, ln in enumerate(lines) if ln.strip().startswith("exit")]
    assert exits
    for i in exits:
        window = "\n".join(lines[max(0, i - 2):i + 1])
        assert "Write-RunRecord" in window, f"exit at line {i + 1} records nothing"
    body = "\n".join(lines)
    assert "lw_runlog.py" in body and "--status $Status" in body
    assert "| & $py" not in body and "| python" not in body
