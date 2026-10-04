"""P0-1 integration arms: the hand-off renders its operator asks FROM the task
engine, and the inbox responder's scheduled tick runs `verify_pending()`.

Acceptance from the ingest directive: a planted task whose check is "file P
exists" stays open until the file appears, then closes on the next scheduled
pass; the hand-off file's operator-ask block is generated from the engine.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

import lw_inbox_responder as responder  # noqa: E402
import lw_next_session  # noqa: E402
import lw_ops_tasks as ot  # noqa: E402


def _plant(flag: Path) -> str:
    eng = ot.default_engine()
    return eng.request("physical", "planted", reason="drop the planted flag",
                       steps=["create the flag file"],
                       verify_argv=[sys.executable, "-c",
                                    f"import os,sys; sys.exit(0 if os.path.exists({str(flag)!r}) else 1)"])


@pytest.fixture
def quiet_responder(monkeypatch, tmp_path):
    monkeypatch.setattr(responder, "HALT_PATH", tmp_path / "never-HALT")
    monkeypatch.setattr(responder, "_append_runlog", lambda *a, **k: None)
    monkeypatch.setattr(responder, "_publish", lambda *a, **k: None)
    inbox = tmp_path / "inbox"
    inbox.mkdir()
    state = tmp_path / "seen.json"
    state.write_text(json.dumps({"seen": []}), encoding="utf-8")
    return ["--once", "--inbox", str(inbox), "--state", str(state),
            "--runlog", str(tmp_path / "runs.jsonl")]


def test_the_responder_tick_closes_a_planted_task_once_its_file_appears(
        tmp_path, quiet_responder, capsys):
    flag = tmp_path / "planted.flag"
    tid = _plant(flag)
    assert responder.main(quiet_responder) == 0
    first = json.loads(capsys.readouterr().out)
    assert first["operator_tasks"]["open"] == [tid]
    assert [t.id for t in ot.default_engine().pending()] == [tid]
    flag.write_text("x", encoding="ascii")
    assert responder.main(quiet_responder) == 0
    second = json.loads(capsys.readouterr().out)
    assert second["operator_tasks"]["closed"] == [tid]
    assert ot.default_engine().pending() == []


def test_a_halted_tick_runs_no_check(tmp_path, quiet_responder, monkeypatch, capsys):
    flag = tmp_path / "planted.flag"
    flag.write_text("x", encoding="ascii")
    tid = _plant(flag)
    halt = tmp_path / "HALT"
    halt.write_text("stop", encoding="utf-8")
    monkeypatch.setattr(responder, "HALT_PATH", halt)
    responder.main(quiet_responder)
    capsys.readouterr()
    assert [t.id for t in ot.default_engine().pending()] == [tid]


def test_a_dry_run_tick_runs_no_check(tmp_path, quiet_responder, capsys):
    flag = tmp_path / "planted.flag"
    flag.write_text("x", encoding="ascii")
    tid = _plant(flag)
    responder.main(quiet_responder + ["--dry-run"])
    capsys.readouterr()
    assert [t.id for t in ot.default_engine().pending()] == [tid]


def test_an_unreadable_task_log_never_fails_the_tick(tmp_path, quiet_responder, capsys):
    root = ot.default_root()
    root.mkdir(parents=True, exist_ok=True)
    (root / "events.jsonl").write_text("{broken\n", encoding="utf-8")
    assert responder.main(quiet_responder) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["operator_tasks_error"] == "TamperedLog"


def test_the_handoff_cli_renders_operator_asks_from_the_engine(tmp_path, monkeypatch, capsys):
    tid = _plant(tmp_path / "never")
    src = tmp_path / "in.txt"
    src.write_text("NEXT SESSION\n------------\nTask: x\n", encoding="ascii")
    written = {}

    def _capture(text, **_kw):
        written["text"] = text
        return tmp_path / "LW-NEXT-SESSION.txt"

    monkeypatch.setattr(lw_next_session, "write_handoff", _capture)
    assert lw_next_session.main(["--write", str(src)]) == 0
    capsys.readouterr()
    text = written["text"]
    assert text.startswith("NEXT SESSION\n")
    assert ot.ASKS_BEGIN in text and tid in text and "drop the planted flag" in text


def test_a_hand_written_asks_block_is_replaced_not_kept(tmp_path, monkeypatch, capsys):
    src = tmp_path / "in.txt"
    src.write_text("NEXT SESSION\n" + ot.ASKS_BEGIN + "\n  - typed by hand\n" + ot.ASKS_END
                   + "\n", encoding="ascii")
    written = {}
    monkeypatch.setattr(lw_next_session, "write_handoff",
                        lambda text, **_k: written.setdefault("text", text) and src)
    lw_next_session.main(["--write", str(src)])
    capsys.readouterr()
    assert "typed by hand" not in written["text"]
    assert "none open" in written["text"]


def test_compose_handoff_is_the_function_main_uses():
    assert lw_next_session.compose_handoff("x\n").startswith("x\n" + ot.ASKS_BEGIN)
