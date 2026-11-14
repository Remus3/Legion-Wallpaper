"""MAIN ORDER 2026-11-14-0935 item 2: a timed-out ORDER run names its last step.

6 of 24 order rows ended at the 30 minute limit with no trace. On a kit line
with error "timeout" the responder reads progress/responder-run.json from the
fleet root and puts its step and pct into the disposition (which is the
run-log ledger line's reason).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import lw_inbox_responder as responder  # noqa: E402


def _write_progress(root: Path, doc: dict) -> None:
    p = root / "ops" / "loop" / "control" / "progress" / "responder-run.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(doc), encoding="utf-8")


def test_child_progress_names_step_and_pct(tmp_path):
    _write_progress(tmp_path, {"task": "responder-run", "pct": 40, "step": "ACT-0935",
                               "status": "running"})
    text = responder.child_progress(tmp_path)
    assert "ACT-0935" in text and "40" in text


def test_child_progress_without_a_file_says_so(tmp_path):
    assert "no progress file" in responder.child_progress(tmp_path)


def test_child_progress_unreadable_file_never_raises(tmp_path):
    p = tmp_path / "ops" / "loop" / "control" / "progress" / "responder-run.json"
    p.parent.mkdir(parents=True)
    p.write_text("{not json", encoding="utf-8")
    assert "unreadable" in responder.child_progress(tmp_path)


def test_a_timed_out_run_names_the_last_progress_step(monkeypatch, tmp_path):
    _write_progress(tmp_path, {"task": "responder-run", "pct": 65, "step": "REPLY-0935",
                               "status": "running"})
    monkeypatch.setattr(responder.lw_headless_env, "FLEET_ROOT", tmp_path)
    monkeypatch.setattr(responder, "main_provenance", lambda p: "")
    monkeypatch.setattr(responder, "kit_adoption", lambda p, prov: None)

    def fake_spawn(prompt, **kw):
        return {"rc": None, "error": "timeout"}

    monkeypatch.setattr(responder.lw_headless_env, "spawn", fake_spawn)
    out = responder.spawn(Path("moon_sync_inbox/2026-11-14-from-MAIN-ORDER-to-LW-x.md"))
    assert out.verdict == responder.AUTO
    assert "timed out" in out.reason
    assert "REPLY-0935" in out.reason and "65" in out.reason


def test_a_finished_run_does_not_read_progress(monkeypatch, tmp_path):
    _write_progress(tmp_path, {"task": "responder-run", "pct": 65, "step": "REPLY-0935"})
    monkeypatch.setattr(responder.lw_headless_env, "FLEET_ROOT", tmp_path)
    monkeypatch.setattr(responder, "main_provenance", lambda p: "")
    monkeypatch.setattr(responder, "kit_adoption", lambda p, prov: None)
    monkeypatch.setattr(responder.lw_headless_env, "spawn",
                        lambda prompt, **kw: {"rc": 0, "model": "m", "effort": "e",
                                              "duration_s": 3})
    out = responder.spawn(Path("moon_sync_inbox/2026-11-14-from-MAIN-ORDER-to-LW-x.md"))
    assert "REPLY-0935" not in out.reason


