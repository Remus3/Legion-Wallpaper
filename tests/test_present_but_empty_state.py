"""Present-but-empty is its own case (ingest P2-5).

A fresh install lands on "file present and empty" - neither the absent nor the
populated fixture a suite usually has. For every reader of LW runtime state
touched by the ingest work, three fixtures: ABSENT, PRESENT-BUT-EMPTY (valid
and empty), POPULATED; each read must succeed without raising and say what it
saw, and where the reader has a writer, a write after the empty fixture must
round-trip and the row must land.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

import lw_job_health as jh  # noqa: E402
import lw_ops_tasks as ot  # noqa: E402
import lw_runlog  # noqa: E402
import lw_watch  # noqa: E402

from tools import lw_monitor, lw_rundash_state  # noqa: E402

NOW = time.time()


def _write(path: Path, kind: str, populated: str) -> Path:
    if kind == "empty":
        path.write_text("", encoding="utf-8") if path.suffix == ".jsonl" else \
            path.write_text("{}", encoding="utf-8")
    elif kind == "populated":
        path.write_text(populated, encoding="utf-8")
    return path


PIPE = json.dumps({"generated_ts": "2026-10-04T00:00:00Z", "images": {
    "akali-coven": {"substate": "NEEDAUTH", "stage_folder": "2.First Pass Done",
                    "state": "first", "last_op_ts": "2026-10-03T00:00:00Z"}}})


@pytest.mark.parametrize("kind", ["absent", "empty", "populated"])
def test_operator_queue_reader(tmp_path, kind):
    p = _write(tmp_path / "pipeline_state.json", kind, PIPE)
    q = lw_rundash_state.read_operator_queue(p, NOW)
    assert q["present"] is (kind != "absent")
    assert q["needauth_count"] == (1 if kind == "populated" else 0)


@pytest.mark.parametrize("kind", ["absent", "empty", "populated"])
def test_monitor_pipeline_view(tmp_path, kind):
    p = _write(tmp_path / "pipeline_state.json", kind, PIPE)
    view = lw_monitor.build_pipeline_view(p, NOW, cache={})
    assert isinstance(view, dict)
    json.dumps(view)                                    # serialisable payload


@pytest.mark.parametrize("kind", ["absent", "empty", "populated"])
def test_job_health_record_reader(tmp_path, kind):
    doc = json.dumps({"generated": "2099-01-01T00:00:00+00:00",
                      "jobs": [{"task": "LW-A", "state": "OK", "reason": "r"}]})
    p = _write(tmp_path / "job_health.json", kind, doc)
    v = lw_rundash_state.read_job_health(p, NOW)
    assert v["state"] == "UNKNOWN" or kind == "populated"


@pytest.mark.parametrize("kind", ["absent", "empty", "populated"])
def test_run_log_judge(tmp_path, kind):
    row = json.dumps({"task": "LW-A", "started": "2026-10-04T00:00:00Z",
                      "ended": "2026-10-04T00:00:00Z", "status": "ok"}) + "\n"
    _write(tmp_path / "LW-A.jsonl", kind, row)
    v = jh.judge(jh.JobSpec("LW-A"), runlog_dir=tmp_path,
                 now=jh.dt.datetime(2026, 10, 4, 0, 1, tzinfo=jh.dt.UTC),
                 query=lambda t: (1, "", "down"))
    assert v["state"] == jh.UNKNOWN or kind == "populated"
    assert lw_runlog.record("LW-A", "s", "ok", "", root=tmp_path)    # write lands
    assert jh.read_runs(tmp_path / "LW-A.jsonl")[-1]["status"] == "ok"


@pytest.mark.parametrize("kind", ["absent", "empty"])
def test_task_log_reads_empty_and_a_request_lands(tmp_path, kind):
    p = _write(tmp_path / "events.jsonl", kind, "")
    eng = ot.TaskEngine(ot.JsonlTaskStore(p), sink=ot.FileSink(tmp_path / "n.jsonl"))
    assert eng.pending() == []
    assert "none open" in eng.render_asks()
    tid = eng.request("c", "s", reason="r", steps=["s"],
                      verify_argv=[sys.executable, "-c", "0"])
    assert [t.id for t in ot.TaskEngine(ot.JsonlTaskStore(p)).pending()] == [tid]


@pytest.mark.parametrize("kind", ["absent", "empty"])
def test_watch_state_empty_object_baselines_and_round_trips(tmp_path, kind):
    p = _write(tmp_path / "watch.json", kind, "")
    st = lw_watch.WatchState(p)
    assert st.get("src") is None
    res = lw_watch.run_source(st, "src", lambda: ["a"], lambda i: {"delivered": True})
    assert res["outcome"] == "baseline"
    assert lw_watch.WatchState(p).get("src")["seen"] == ["a"]


def test_flat_seen_state_without_a_seen_list_is_corrupt_not_empty(tmp_path):
    """`{}` is not a baseline the responder ever writes. Reading it as "seen
    nothing" would make every note in the inbox new - present-but-empty is
    exactly where that hides."""
    p = tmp_path / "seen.json"
    p.write_text("{}", encoding="utf-8")
    with pytest.raises(lw_watch.WatchStateCorrupt):
        lw_watch.FlatSeenState(p).get("inbox")
    p.write_text('{"seen": []}', encoding="utf-8")      # a real empty baseline
    assert lw_watch.FlatSeenState(p).get("inbox")["seen"] == []
