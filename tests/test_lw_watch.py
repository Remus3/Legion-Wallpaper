"""Arms for tools/lw_watch.py - the watcher primitive (ingest P0-2).

Rules under test: (a) the first run baselines and sends nothing; (b) the
seen-set advances only after confirmed delivery; (c) a pid-stamped lock dir
stops overlap, a dead-pid lock is taken over; (d) K consecutive fetch failures
send exactly one alert, reset on the next success; (e) nothing is sent when
nothing changed.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

import lw_watch as w  # noqa: E402


class Box:
    def __init__(self, items=(), fail=False):
        self.items, self.fail = list(items), fail
        self.delivered_calls, self.alerts = [], []
        self.deliver_ok = True

    def fetch(self):
        if self.fail:
            raise OSError("source down")
        return list(self.items)

    def deliver(self, items, confirm):
        self.delivered_calls.append(list(items))
        return {"delivered": True} if self.deliver_ok else {"delivered": []}

    def alert(self, source, count, detail):
        self.alerts.append((source, count, detail))
        return True, "alerted"


def _run(state, box, **kw):
    return w.run_source(state, "src", box.fetch, describe=str, confirm_arg=True,
                        deliver=box.deliver, alert=box.alert, **kw)


def test_the_first_run_baselines_and_sends_nothing(tmp_path):
    st = w.WatchState(tmp_path / "s.json")
    box = Box(["a", "b"])
    res = _run(st, box)
    assert res["outcome"] == "baseline" and box.delivered_calls == []
    box.items.append("c")
    res = _run(w.WatchState(tmp_path / "s.json"), box)
    assert res["outcome"] == "delivered" and box.delivered_calls == [["c"]]


def test_baseline_false_delivers_on_the_first_run(tmp_path):
    box = Box(["a"])
    res = _run(w.WatchState(tmp_path / "s.json"), box, baseline=False)
    assert res["outcome"] == "delivered" and box.delivered_calls == [["a"]]


def test_a_failed_delivery_keeps_the_items_for_the_next_run(tmp_path):
    st = w.WatchState(tmp_path / "s.json")
    box = Box(["a"])
    _run(st, box)
    box.items.append("b")
    box.deliver_ok = False
    assert _run(st, box)["outcome"] == "deliver-failed"
    box.deliver_ok = True
    assert _run(w.WatchState(tmp_path / "s.json"), box)["outcome"] == "delivered"
    assert box.delivered_calls == [["b"], ["b"]]
    assert _run(st, box)["outcome"] == "nothing-new"


def test_a_raising_deliver_is_a_failed_delivery_not_a_crash(tmp_path):
    st = w.WatchState(tmp_path / "s.json")
    box = Box(["a"])
    _run(st, box)
    box.items.append("b")

    def boom(items, confirm):
        raise RuntimeError("target closed")
    res = w.run_source(st, "src", box.fetch, describe=str, confirm_arg=True, deliver=boom)
    assert res["outcome"] == "deliver-failed" and "RuntimeError" in res["detail"]
    assert "b" not in st.get("src")["seen"]


def test_partial_delivery_advances_only_the_confirmed_items(tmp_path):
    st = w.WatchState(tmp_path / "s.json")
    box = Box([])
    _run(st, box)
    box.items = ["a", "b", "c"]

    def some(items, confirm):
        confirm(["a"])            # persisted at once, like a per-item spawn
        return {"delivered": ["b"]}
    res = w.run_source(st, "src", box.fetch, describe=str, confirm_arg=True, deliver=some)
    assert res["outcome"] == "delivered" and sorted(res["delivered"]) == ["a", "b"]
    assert sorted(w.WatchState(tmp_path / "s.json").get("src")["seen"]) == ["a", "b"]


def test_confirm_persists_before_deliver_returns(tmp_path):
    st = w.WatchState(tmp_path / "s.json")
    _run(st, Box([]))
    path = tmp_path / "s.json"

    on_disk = []

    def crash_after_confirm(items, confirm):
        confirm(["x"])
        on_disk.append(json.loads(path.read_text(encoding="utf-8"))["sources"]["src"]["seen"])
        raise RuntimeError("died mid-batch")
    w.run_source(st, "src", lambda: ["x", "y"], describe=str, confirm_arg=True, deliver=crash_after_confirm)
    assert on_disk == [["x"]], "confirm must persist before deliver returns"
    seen = w.WatchState(path).get("src")["seen"]
    assert "x" in seen and "y" not in seen


def test_k_failures_send_one_alert_then_none_then_reset_on_success(tmp_path):
    st = w.WatchState(tmp_path / "s.json")
    box = Box(["a"])
    _run(st, box)
    box.fail = True
    for i in range(1, 5):
        assert _run(st, box, alert_after=5)["outcome"] == "fetch-failed"
        assert box.alerts == [], f"alerted early at {i}"
    _run(st, box, alert_after=5)
    assert len(box.alerts) == 1 and box.alerts[0][1] == 5
    _run(st, box, alert_after=5)                         # K+1: no second alert
    assert len(box.alerts) == 1
    box.fail = False
    res = _run(st, box, alert_after=5)
    assert res["outcome"] == "nothing-new" and st.get("src")["failures"] == 0
    box.fail = True
    for _ in range(5):
        _run(st, box, alert_after=5)
    assert len(box.alerts) == 2                          # counter was reset


def test_a_failed_alert_send_is_retried_next_run(tmp_path):
    st = w.WatchState(tmp_path / "s.json")
    calls = []

    def flaky(source, count, detail):
        calls.append(count)
        return len(calls) > 1, "x"
    for _ in range(3):
        w.run_source(st, "src", lambda: (_ for _ in ()).throw(OSError("x")), describe=str, confirm_arg=True, deliver=lambda i, c: {"delivered": True}, alert=flaky, alert_after=2)
    assert calls == [2, 3]


def test_none_from_fetch_is_a_failure_not_an_empty_source(tmp_path):
    st = w.WatchState(tmp_path / "s.json")
    res = w.run_source(st, "src", lambda: None, describe=str, confirm_arg=True, deliver=lambda i, c: {"delivered": True})
    assert res["outcome"] == "fetch-failed"


def test_nothing_changed_sends_nothing_and_writes_nothing(tmp_path):
    path = tmp_path / "s.json"
    st = w.WatchState(path)
    box = Box(["a"])
    _run(st, box)
    before = path.stat().st_mtime_ns
    os.utime(path, ns=(before - 10**9, before - 10**9))
    stamp = path.stat().st_mtime_ns
    assert _run(st, box)["outcome"] == "nothing-new"
    assert box.delivered_calls == [] and path.stat().st_mtime_ns == stamp


def test_seen_is_pruned_to_the_live_source_and_bounded(tmp_path):
    st = w.WatchState(tmp_path / "s.json")
    box = Box(["a", "b"])
    _run(st, box)
    box.items = ["b", "c"]
    _run(st, box)
    assert st.get("src")["seen"] == ["b", "c"]          # "a" left the source
    capped = w.WatchState(tmp_path / "c.json", max_seen=3)
    box = Box(["a", "b"])
    _run(capped, box)
    box.items = ["a", "b", "c", "d", "e", "f"]
    _run(capped, box)
    assert capped.get("src")["seen"] == ["d", "e", "f"]


def test_flat_state_keeps_the_legacy_seen_shape(tmp_path):
    path = tmp_path / "seen.json"
    st = w.FlatSeenState(path)
    assert st.get("any") is None
    box = Box(["a"])
    w.run_source(st, "any", box.fetch, describe=str, confirm_arg=True, deliver=box.deliver)
    assert json.loads(path.read_text(encoding="utf-8"))["seen"] == ["a"]
    path.write_text(json.dumps({"seen": ["a"]}), encoding="utf-8")   # legacy file
    assert w.FlatSeenState(path).get("any")["seen"] == ["a"]


def test_a_never_baselined_flat_source_that_fails_still_baselines_later(tmp_path):
    path = tmp_path / "seen.json"
    box = Box(["a", "b"], fail=True)
    w.run_source(w.FlatSeenState(path), "any", box.fetch, describe=str, confirm_arg=True, deliver=box.deliver)
    box.fail = False
    res = w.run_source(w.FlatSeenState(path), "any", box.fetch, describe=str, confirm_arg=True, deliver=box.deliver)
    assert res["outcome"] == "baseline" and box.delivered_calls == []


def test_failures_before_any_success_reset_on_a_no_baseline_source(tmp_path):
    st = w.WatchState(tmp_path / "s.json")
    for _ in range(3):
        w.run_source(st, "src", lambda: None, describe=str, confirm_arg=True, deliver=lambda i, c: {"delivered": True}, baseline=False)
    assert st.get("src")["failures"] == 3
    res = w.run_source(st, "src", lambda: [], describe=str, confirm_arg=True, deliver=lambda i, c: {"delivered": True}, baseline=False)
    assert res["outcome"] == "nothing-new" and st.get("src")["failures"] == 0


def test_dry_run_persists_nothing(tmp_path):
    path = tmp_path / "s.json"
    box = Box(["a"])
    res = _run(w.WatchState(path), box, persist=False)
    assert res["outcome"] == "baseline" and not path.exists()


# -- lock -------------------------------------------------------------------

def test_a_live_pid_lock_blocks(tmp_path):
    lock = tmp_path / "lk"
    with w.watch_lock(lock), pytest.raises(w.LockBusy):
        with w.watch_lock(lock, pid=os.getpid() + 1, alive=lambda p: True):
            pass


def test_a_dead_pid_lock_is_taken_over(tmp_path):
    lock = tmp_path / "lk"
    lock.mkdir()
    (lock / "pid").write_text("999999", encoding="ascii")
    with w.watch_lock(lock, alive=lambda p: False):
        assert (lock / "pid").read_text(encoding="ascii") == str(os.getpid())
    assert not lock.exists()


def test_liveness_is_never_judged_by_mtime(tmp_path):
    lock = tmp_path / "lk"
    lock.mkdir()
    (lock / "pid").write_text(str(os.getpid()), encoding="ascii")
    old = 1_000_000_000
    os.utime(lock / "pid", (old, old))
    with pytest.raises(w.LockBusy):
        with w.watch_lock(lock, pid=os.getpid() + 1):
            pass


def test_pid_alive_reads_the_real_process_table():
    assert w.pid_alive(os.getpid()) is True
    assert w.pid_alive(0) is False


# -- MAIN 0020 section 4 contract arms ------------------------------------------

def test_main_contract_positional_order_and_single_arg_deliver(tmp_path):
    st = w.WatchState(tmp_path / "s.json")
    w.run_source(st, "src", lambda: ["a"], lambda items: {"delivered": True})
    seen = []
    res = w.run_source(st, "src", lambda: ["a", "b"],
                       lambda items: seen.append(items) or {"delivered": True})
    assert res["outcome"] == "delivered" and seen == [["b"]]
    assert {"source", "outcome", "new", "detail"} <= set(res)


def test_only_a_dict_with_delivered_exactly_true_advances(tmp_path):
    st = w.WatchState(tmp_path / "s.json")
    w.run_source(st, "src", lambda: [], lambda items: {"delivered": True})
    for verdict in (True, ["x"], {"delivered": 1}, {"delivered": "yes"}, None):
        res = w.run_source(st, "src", lambda: ["x"], lambda items, v=verdict: v)
        assert res["outcome"] == "deliver-failed", verdict
    assert w.run_source(st, "src", lambda: ["x"],
                        lambda items: {"delivered": True})["outcome"] == "delivered"


@pytest.mark.parametrize("cls", [w.WatchState, w.FlatSeenState])
@pytest.mark.parametrize("body", ["{not json", "[1, 2]"])
def test_a_corrupt_state_file_raises_and_is_never_rewritten(tmp_path, cls, body):
    path = tmp_path / "s.json"
    path.write_text(body, encoding="utf-8")
    with pytest.raises(w.WatchStateCorrupt):
        w.run_source(cls(path), "src", lambda: ["a"], lambda items: {"delivered": True})
    assert path.read_text(encoding="utf-8") == body


def test_the_lock_is_released_only_while_it_holds_our_pid(tmp_path):
    lock = tmp_path / "lk"
    with w.watch_lock(lock):
        (lock / "pid").write_text("424242", encoding="ascii")   # someone took it over
    assert lock.exists() and (lock / "pid").read_text(encoding="ascii") == "424242"


def test_a_dead_holder_is_renamed_aside_not_reused_in_place(tmp_path):
    lock = tmp_path / "lk"
    lock.mkdir()
    (lock / "pid").write_text("999999", encoding="ascii")
    (lock / "marker").write_text("old", encoding="ascii")   # rmdir in place would fail
    with w.watch_lock(lock, pid_alive=lambda p: False):
        assert not (lock / "marker").exists()
        assert (lock / "pid").read_text(encoding="ascii") == str(os.getpid())


def test_a_pidless_holder_is_taken_over(tmp_path):
    lock = tmp_path / "lk"
    lock.mkdir()
    with w.watch_lock(lock, pid_alive=lambda p: True):
        assert (lock / "pid").read_text(encoding="ascii") == str(os.getpid())
