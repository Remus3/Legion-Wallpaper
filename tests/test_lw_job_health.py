"""Arms for tools/lw_runlog.py + tools/lw_job_health.py (ingest P0-4).

Hermetic: injected clock, fixture run logs, injected schtasks runner.
Named tests from the directive: exit 2 when the log is missing; a partial that
never recovers ages into UNHEALTHY; a single failed query retried then
succeeding is OK; overnight gaps in a fixed daily schedule do not false-alarm.
Plus: a HALT file reads "halted", never unhealthy; the health script takes no
action (observation only).
"""
from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

import lw_job_health as jh  # noqa: E402
import lw_runlog  # noqa: E402

T0 = dt.datetime(2026, 10, 1, 12, 0, tzinfo=dt.UTC)

XML_PT5M = """<?xml version="1.0" encoding="UTF-16"?>
<Task><Triggers><TimeTrigger><Repetition><Interval>PT5M</Interval></Repetition>
<StartBoundary>2026-09-11T00:16:56</StartBoundary></TimeTrigger></Triggers>
<Settings><Enabled>true</Enabled></Settings></Task>"""

XML_DAILY = """<Task><Triggers><CalendarTrigger><StartBoundary>2026-08-01T04:17:00</StartBoundary>
<ScheduleByDay><DaysInterval>1</DaysInterval></ScheduleByDay></CalendarTrigger></Triggers></Task>"""

XML_WEEKLY = """<Task><Triggers><CalendarTrigger><ScheduleByWeek><WeeksInterval>1</WeeksInterval>
</ScheduleByWeek></CalendarTrigger></Triggers></Task>"""

XML_DISABLED = XML_PT5M.replace("<Enabled>true</Enabled>", "<Enabled>false</Enabled>")


def _log(root: Path, task: str, rows):
    p = root / f"{task}.jsonl"
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as fh:
        for minutes, status in rows:
            t = T0 + dt.timedelta(minutes=minutes)
            fh.write(json.dumps({"task": task, "started": t.isoformat(),
                                 "ended": t.isoformat(), "status": status,
                                 "detail": "", "pid": 1}) + "\n")


def _query(xml_by_task, fail_first=0):
    calls = {}

    def run(task):
        calls[task] = calls.get(task, 0) + 1
        if calls[task] <= fail_first:
            return 1, "", "ERROR: The RPC server is unavailable.\nmore"
        return 0, xml_by_task.get(task, XML_PT5M), ""
    run.calls = calls
    return run


def _judge(tmp_path, task, now_min, xml=XML_PT5M, fail_first=0, halt=None):
    q = _query({task: xml}, fail_first=fail_first)
    spec = jh.JobSpec(task, halt_file=halt)
    return jh.judge(spec, runlog_dir=tmp_path, now=T0 + dt.timedelta(minutes=now_min),
                    query=q), q


# -- the writer ---------------------------------------------------------------

def test_record_appends_one_line_with_the_contract_fields(tmp_path):
    lw_runlog.record("LW-X", "2026-10-01T12:00:00Z", "ok", "fine", root=tmp_path, pid=7)
    rows = [json.loads(x) for x in (tmp_path / "LW-X.jsonl").read_text(
        encoding="utf-8").splitlines()]
    assert len(rows) == 1
    assert set(rows[0]) == {"task", "started", "ended", "status", "detail", "pid"}
    assert rows[0]["status"] == "ok" and rows[0]["pid"] == 7


def test_record_refuses_an_unknown_status(tmp_path):
    lw_runlog.record("LW-X", "s", "green", "", root=tmp_path)
    row = json.loads((tmp_path / "LW-X.jsonl").read_text(encoding="utf-8"))
    assert row["status"] == "failed" and "unknown status" in row["detail"]


def test_record_never_raises(tmp_path):
    blocker = tmp_path / "file"
    blocker.write_text("x", encoding="ascii")
    assert lw_runlog.record("LW-X", "s", "ok", "", root=blocker / "sub") is False


def test_record_rotates_past_the_cap(tmp_path, monkeypatch):
    monkeypatch.setattr(lw_runlog, "MAX_BYTES", 400)
    for _ in range(10):
        lw_runlog.record("LW-X", "s", "ok", "x" * 20, root=tmp_path)
    assert (tmp_path / "LW-X.jsonl.1").exists()
    assert (tmp_path / "LW-X.jsonl").stat().st_size <= 400


def test_cli_takes_data_as_arguments_not_stdin(tmp_path):
    assert lw_runlog.main(["--root", str(tmp_path), "--task", "LW-W", "--started",
                           "2026-10-01T00:00:00Z", "--status", "partial", "--detail",
                           "one source dead"]) == 0
    row = json.loads((tmp_path / "LW-W.jsonl").read_text(encoding="utf-8"))
    assert row["status"] == "partial" and row["detail"] == "one source dead"


# -- the judge ----------------------------------------------------------------

def test_a_missing_log_is_unknown_exit_2(tmp_path):
    v, _q = _judge(tmp_path, "LW-A", 10)
    assert v["state"] == jh.UNKNOWN and "no run log" in v["reason"]
    assert jh.exit_code([v]) == 2


def test_a_fresh_ok_job_is_healthy(tmp_path):
    _log(tmp_path, "LW-A", [(m, "ok") for m in range(0, 60, 5)])
    v, _q = _judge(tmp_path, "LW-A", 57)
    assert v["state"] == jh.OK, v
    assert jh.exit_code([v]) == 0


def test_a_partial_that_never_recovers_ages_into_unhealthy(tmp_path):
    rows = [(m, "ok") for m in range(0, 30, 5)] + [(m, "partial") for m in range(30, 300, 5)]
    _log(tmp_path, "LW-A", rows)
    early, _ = _judge(tmp_path, "LW-A", 32)
    assert early["state"] == jh.OK                     # one partial is not an alarm
    late, _ = _judge(tmp_path, "LW-A", 297)
    assert late["state"] == jh.UNHEALTHY and "partial" in late["reason"]
    assert jh.exit_code([late]) == 1


def test_consecutive_failures_are_unhealthy_at_once(tmp_path):
    # the last ok is still inside the staleness threshold - only the streak fires
    _log(tmp_path, "LW-A", [(m, "ok") for m in range(0, 60, 5)]
         + [(56, "failed"), (57, "failed"), (58, "failed")])
    v, _ = _judge(tmp_path, "LW-A", 59)
    assert v["state"] == jh.UNHEALTHY and "last 3 runs failed" in v["reason"]


def test_a_stale_job_is_unhealthy(tmp_path):
    _log(tmp_path, "LW-A", [(m, "ok") for m in range(0, 60, 5)])
    v, _ = _judge(tmp_path, "LW-A", 55 + 60)
    assert v["state"] == jh.UNHEALTHY and "no ok run" in v["reason"]


def test_threshold_follows_the_observed_cadence_not_the_declared_one(tmp_path):
    # declared PT5M, but the scheduler really lands a success every ~3h
    _log(tmp_path, "LW-A", [(m, "ok") for m in range(0, 180 * 8, 180)])
    v, _ = _judge(tmp_path, "LW-A", 180 * 7 + 200)
    assert v["state"] == jh.OK, v
    assert v["threshold_s"] >= 180 * 60 * 1.5


def test_a_failed_query_retried_then_succeeding_is_ok(tmp_path):
    _log(tmp_path, "LW-A", [(m, "ok") for m in range(0, 60, 5)])
    v, q = _judge(tmp_path, "LW-A", 57, fail_first=2)
    assert v["state"] == jh.OK and v["declared_s"] == 300
    assert q.calls["LW-A"] == 3


def test_a_query_that_never_succeeds_keeps_its_first_error_line(tmp_path):
    _log(tmp_path, "LW-A", [(m, "ok") for m in range(0, 60, 5)])
    v, q = _judge(tmp_path, "LW-A", 57, fail_first=99)
    assert v["declared_s"] is None
    assert v["query_error"] == "ERROR: The RPC server is unavailable."
    assert q.calls["LW-A"] == jh.QUERY_TRIES


def test_overnight_gaps_in_a_fixed_daily_schedule_do_not_false_alarm(tmp_path):
    # a daily job at 04:17 that once ran late, once early - 20h..28h gaps
    day = 24 * 60
    rows = [(0, "ok"), (day + 240, "ok"), (2 * day + 100, "ok"), (3 * day, "ok"),
            (4 * day + 60, "ok")]
    _log(tmp_path, "LW-D", rows)
    v, _ = _judge(tmp_path, "LW-D", 5 * day + 200, xml=XML_DAILY)
    assert v["state"] == jh.OK, v


def test_weekly_declared_interval_is_parsed(tmp_path):
    assert jh.declared_interval_s(XML_WEEKLY) == 7 * 86400
    assert jh.declared_interval_s(XML_DAILY) == 86400
    assert jh.declared_interval_s(XML_PT5M) == 300
    assert jh.declared_interval_s("<Task/>") is None


def test_a_halt_file_reads_halted_not_unhealthy(tmp_path):
    _log(tmp_path, "LW-A", [(0, "ok")])
    halt = tmp_path / "HALT"
    halt.write_text("", encoding="ascii")
    v, _ = _judge(tmp_path, "LW-A", 10_000, halt=halt)
    assert v["state"] == jh.HALTED
    assert jh.exit_code([v]) == 0


def test_a_disabled_task_reads_halted(tmp_path):
    _log(tmp_path, "LW-A", [(0, "ok")])
    v, _ = _judge(tmp_path, "LW-A", 10_000, xml=XML_DISABLED)
    assert v["state"] == jh.HALTED and "disabled" in v["reason"]


def test_skipped_runs_neither_count_as_ok_nor_alarm(tmp_path):
    _log(tmp_path, "LW-A", [(m, "ok") for m in range(0, 30, 5)]
         + [(m, "skipped") for m in range(30, 40, 5)])
    v, _ = _judge(tmp_path, "LW-A", 37)
    assert v["state"] == jh.OK


def test_a_skip_after_a_partial_does_not_hide_it(tmp_path):
    _log(tmp_path, "LW-A", [(m, "ok") for m in range(0, 30, 5)] + [(30, "partial")]
         + [(m, "skipped") for m in range(35, 120, 5)])
    v, _ = _judge(tmp_path, "LW-A", 117)
    assert v["state"] == jh.UNHEALTHY


def test_a_torn_last_line_is_ignored_not_fatal(tmp_path):
    _log(tmp_path, "LW-A", [(m, "ok") for m in range(0, 60, 5)])
    with (tmp_path / "LW-A.jsonl").open("a", encoding="utf-8") as fh:
        fh.write('{"task": "LW-A", "sta')
    v, _ = _judge(tmp_path, "LW-A", 57)
    assert v["state"] == jh.OK


def test_exit_code_precedence():
    assert jh.exit_code([{"state": jh.OK}, {"state": jh.UNKNOWN},
                         {"state": jh.UNHEALTHY}]) == 1
    assert jh.exit_code([{"state": jh.OK}, {"state": jh.UNKNOWN}]) == 2
    assert jh.exit_code([{"state": jh.OK}, {"state": jh.HALTED}]) == 0


def test_main_writes_job_health_json_and_takes_no_action(tmp_path, monkeypatch):
    _log(tmp_path / "runlog", "LW-A", [(m, "ok") for m in range(0, 60, 5)])
    out = tmp_path / "job_health.json"
    monkeypatch.setattr(jh, "JOBS", (jh.JobSpec("LW-A"), jh.JobSpec("LW-B")))
    q = _query({})
    rc = jh.main(["--runlog-dir", str(tmp_path / "runlog"), "--out", str(out)],
                 now=T0 + dt.timedelta(minutes=57), query=q)
    assert rc == 2                                  # LW-B has no log
    doc = json.loads(out.read_text(encoding="utf-8"))
    assert [j["task"] for j in doc["jobs"]] == ["LW-A", "LW-B"]
    assert doc["exit"] == 2
    assert sorted(p.name for p in (tmp_path / "runlog").iterdir()) == ["LW-A.jsonl"]


def test_the_four_lw_tasks_are_registered():
    assert {j.task for j in jh.JOBS} == {"LW-InboxResponder", "LW-CIWatchdog",
                                         "LW-Wallpaper", "LW-WeeklyHygiene"}


def test_under_five_gaps_uses_the_declared_floor_only(tmp_path):
    # MAIN 0020 section 5. Four 3-hour gaps would lift the threshold to 4.5h;
    # with under five gaps only the declared PT5M x 2 = 10 min floor applies.
    _log(tmp_path, "LW-A", [(m, "ok") for m in range(0, 180 * 5, 180)])
    v, _ = _judge(tmp_path, "LW-A", 180 * 4 + 30)
    assert v["state"] == jh.UNHEALTHY and v["threshold_s"] == 600


def test_halted_is_a_recordable_status(tmp_path):
    assert "halted" in lw_runlog.STATUSES
    lw_runlog.record("LW-X", "s", "halted", "HALT", root=tmp_path)
    assert json.loads((tmp_path / "LW-X.jsonl").read_text(encoding="utf-8"))["status"] == "halted"
