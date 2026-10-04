"""The CI watchdog on lw_watch.run_source (ingest P0-2 retrofit 2/2): the new arms.

A failing sha is a watched item: retired only by a merged fix or a give-up; an
`unavailable` CI read is a fetch failure, and five in a row write ONE alert.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load():
    spec = importlib.util.spec_from_file_location("lw_ci_watchdog_watch_t",
                                                  ROOT / "tools" / "ci_watchdog.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


cw = _load()
RED = {"status": "failure", "sha": "b" * 40, "runs": [{"name": "ci"}]}


class _TG:
    status = RED

    @classmethod
    def check_ci(cls, _ref):
        return cls.status


def _wire(monkeypatch, tmp_path, results):
    monkeypatch.setattr(cw, "STATE_DIR", tmp_path / "logs")
    monkeypatch.setattr(cw, "_bind_truth_gate", lambda: _TG)
    calls = []

    def _fix(sha, runs, attempt, tg, **kw):
        calls.append(attempt)
        return results.pop(0)
    monkeypatch.setattr(cw, "do_fix_pass", _fix)
    return calls


def _pass(tmp_path, dry_run=False):
    return cw.one_pass(model=None, dry_run=dry_run, max_attempts=2, fix_timeout=1,
                       state_dir=tmp_path)


def test_the_first_pass_on_a_red_main_fixes_it(monkeypatch, tmp_path):
    _TG.status = RED
    calls = _wire(monkeypatch, tmp_path, [True])
    assert _pass(tmp_path) == 0 and calls == [1]


def test_a_merged_fix_retires_the_sha(monkeypatch, tmp_path):
    _TG.status = RED
    calls = _wire(monkeypatch, tmp_path, [True])
    _pass(tmp_path)
    _pass(tmp_path)                      # same red sha still reported
    assert calls == [1]


def test_a_failed_fix_keeps_the_sha_until_the_budget_gives_up(monkeypatch, tmp_path):
    _TG.status = RED
    calls = _wire(monkeypatch, tmp_path, [False, False])
    assert _pass(tmp_path) == 1
    assert _pass(tmp_path) == 1
    assert _pass(tmp_path) == 0          # give-up: retired, nothing attempted
    assert _pass(tmp_path) == 0
    assert calls == [1, 2]


def test_five_unavailable_reads_write_exactly_one_alert(monkeypatch, tmp_path):
    _TG.status = {"status": "unavailable", "detail": "gh auth expired", "sha": "HEAD"}
    calls = _wire(monkeypatch, tmp_path, [])
    for _ in range(7):
        assert _pass(tmp_path) == 0
    lines = (tmp_path / cw.ALERTS_FILE).read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1 and json.loads(lines[0])["consecutive_failures"] == 5
    assert calls == []
    _TG.status = {"status": "success", "sha": "c" * 40}
    _pass(tmp_path)
    rec = json.loads((tmp_path / cw.WATCH_FILE).read_text(encoding="utf-8"))
    assert rec["sources"][cw.WATCH_SOURCE]["failures"] == 0


def test_a_dry_run_writes_no_watch_state(monkeypatch, tmp_path):
    _TG.status = RED
    _wire(monkeypatch, tmp_path, [True])
    _pass(tmp_path, dry_run=True)
    _TG.status = {"status": "unavailable", "detail": "x", "sha": "HEAD"}
    _pass(tmp_path, dry_run=True)        # a failure counter would be a write
    assert not (tmp_path / cw.WATCH_FILE).exists()
