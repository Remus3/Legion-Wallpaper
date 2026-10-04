"""The inbox responder on lw_watch.run_source (ingest P0-2 retrofit): the new arms.

The existing suites (test_inbox_responder*.py, test_inbox_*.py) pin baseline,
advance-after-AUTO and the payload shapes; these add what the primitive brings:
a missing inbox is a FETCH FAILURE, not a quiet inbox, and five in a row leave
exactly one alert line in the run log.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

import lw_inbox_responder as responder  # noqa: E402


def _argv(tmp_path, inbox):
    return ["--once", "--inbox", str(inbox), "--state", str(tmp_path / "seen.json"),
            "--runlog", str(tmp_path / "runs.jsonl")]


def _quiet(monkeypatch, tmp_path):
    monkeypatch.setattr(responder, "HALT_PATH", tmp_path / "never-HALT")
    monkeypatch.setattr(responder, "_publish", lambda *a, **k: None)


def test_a_missing_inbox_is_a_fetch_failure_not_a_quiet_inbox(tmp_path, monkeypatch, capsys):
    _quiet(monkeypatch, tmp_path)
    (tmp_path / "seen.json").write_text(json.dumps({"seen": []}), encoding="utf-8")
    assert responder.main(_argv(tmp_path, tmp_path / "gone")) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["fetch_failed"] and out["consecutive_failures"] == 1


def test_five_missing_inbox_ticks_log_exactly_one_alert(tmp_path, monkeypatch, capsys):
    _quiet(monkeypatch, tmp_path)
    (tmp_path / "seen.json").write_text(json.dumps({"seen": []}), encoding="utf-8")
    for _ in range(7):
        responder.main(_argv(tmp_path, tmp_path / "gone"))
    capsys.readouterr()
    rows = [json.loads(x) for x in (tmp_path / "runs.jsonl").read_text(
        encoding="utf-8").splitlines()]
    alerts = [r for r in rows if r["event"] == "source_alert"]
    assert len(alerts) == 1 and alerts[0]["consecutive_failures"] == 5
    inbox = tmp_path / "back"
    inbox.mkdir()
    responder.main(_argv(tmp_path, inbox))
    capsys.readouterr()
    assert "fetch_failures" not in json.loads((tmp_path / "seen.json").read_text(
        encoding="utf-8"))


def test_a_cold_start_on_a_missing_inbox_does_not_baseline_it(tmp_path, monkeypatch, capsys):
    _quiet(monkeypatch, tmp_path)
    responder.main(_argv(tmp_path, tmp_path / "gone"))
    inbox = tmp_path / "gone"
    inbox.mkdir()
    (inbox / "2026-10-04-0001-from-RC-note.md").write_text("n", encoding="utf-8")
    monkeypatch.setattr(responder, "spawn", lambda *a, **k: (_ for _ in ()).throw(
        AssertionError("spawned on a baseline tick")))
    responder.main(_argv(tmp_path, inbox))
    out = json.loads(capsys.readouterr().out.split("\n}\n")[-2] + "\n}")
    assert out["cold_start"] is True and out["baselined"] == 1


def test_a_corrupt_seen_file_is_reported_never_rewritten_and_spawns_nothing(
        tmp_path, monkeypatch, capsys):
    _quiet(monkeypatch, tmp_path)
    (tmp_path / "seen.json").write_text("{torn", encoding="utf-8")
    inbox = tmp_path / "inbox"
    inbox.mkdir()
    (inbox / "2026-10-04-0001-from-RC-note.md").write_text("n", encoding="utf-8")
    monkeypatch.setattr(responder, "spawn", lambda *a, **k: (_ for _ in ()).throw(
        AssertionError("spawned over a corrupt seen-file")))
    assert responder.main(_argv(tmp_path, inbox)) == 0
    out = json.loads(capsys.readouterr().out)
    assert "state_corrupt" in out
    assert (tmp_path / "seen.json").read_text(encoding="utf-8") == "{torn"
