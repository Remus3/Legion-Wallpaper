"""Arms for tools/lw_ops_tasks.py - the verified operator-task engine (P0-1).

Named tests from the ingest directive, in order:
  (1) same key twice -> one task, one notification
  (2) done with a failing check -> still open, event recorded
  (3) check passes -> closed
  (4) string argv refused
  (5) timeout counts as not done
  (6) editing a past event is detected and refused
  (7) a withdrawn task never re-notifies
  (8) hold mode sends nothing
Plus: open/closed is DERIVED from the log; executable allowlist; owner gate;
the hand-off block renders from the pending list and passes the hand-off gate.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

import lw_ops_tasks as ot  # noqa: E402
from precommit_gate import scan_handoff_text  # noqa: E402

PY = sys.executable


class RecordingSink:
    def __init__(self, ok=True):
        self.sent = []
        self.ok = ok

    def send(self, message):
        self.sent.append(message)
        return self.ok, "recorded"


def _exists_argv(p: Path) -> list[str]:
    return [PY, "-c", f"import os,sys; sys.exit(0 if os.path.exists({str(p)!r}) else 1)"]


def _engine(tmp_path, sink=None, **kw):
    store = ot.JsonlTaskStore(tmp_path / "events.jsonl")
    return ot.TaskEngine(store, sink=sink or RecordingSink(), **kw)


def _req(engine, verify, cap="physical", subject="plug-dac", **kw):
    return engine.request(cap, subject, reason="replug the DAC", steps=["unplug", "replug"],
                          verify_argv=verify, **kw)


# (1)
def test_same_key_twice_is_one_task_and_one_notification(tmp_path):
    sink = RecordingSink()
    eng = _engine(tmp_path, sink)
    a = _req(eng, _exists_argv(tmp_path / "flag"))
    b = _req(eng, _exists_argv(tmp_path / "flag"))
    assert a == b
    assert [t.id for t in eng.pending()] == [a]
    assert len(sink.sent) == 1
    kinds = [e["kind"] for e in eng.store.read()]
    assert kinds.count("request") == 1 and kinds.count("join") == 1


# (2)
def test_done_with_a_failing_check_stays_open_and_records_the_attempt(tmp_path):
    eng = _engine(tmp_path)
    tid = _req(eng, _exists_argv(tmp_path / "flag"))
    res = eng.done(tid)
    assert res["closed"] is False
    assert [t.id for t in eng.pending()] == [tid]
    verifies = [e for e in eng.store.read() if e["kind"] == "verify"]
    assert len(verifies) == 1 and verifies[0]["passed"] is False
    assert verifies[0]["trigger"] == "done"


# (3)
def test_a_passing_check_closes_the_task(tmp_path):
    eng = _engine(tmp_path)
    flag = tmp_path / "flag"
    tid = _req(eng, _exists_argv(flag))
    flag.write_text("x", encoding="ascii")
    assert eng.done(tid)["closed"] is True
    assert eng.pending() == []
    assert eng.task(tid).state == "closed"


# (4)
@pytest.mark.parametrize("bad", ["python -c 1", b"python", ("python", 3), [], None])
def test_a_string_or_malformed_argv_is_refused_at_the_boundary(tmp_path, bad):
    eng = _engine(tmp_path)
    with pytest.raises(ot.TaskRefused):
        _req(eng, bad)
    assert eng.store.read() == []


def test_an_executable_off_the_allowlist_is_refused(tmp_path):
    eng = _engine(tmp_path)
    with pytest.raises(ot.TaskRefused, match="allowlist"):
        _req(eng, ["curl", "http://example.invalid"])


def test_only_the_owning_tree_may_register_a_check(tmp_path):
    eng = _engine(tmp_path)
    with pytest.raises(ot.TaskRefused, match="owner"):
        _req(eng, _exists_argv(tmp_path / "f"), owner="RC")


# (5)
def test_a_timed_out_check_counts_as_not_done(tmp_path):
    eng = _engine(tmp_path, verify_timeout_s=0.5)
    tid = _req(eng, [PY, "-c", "import time; time.sleep(30)"])
    res = eng.done(tid)
    assert res["closed"] is False
    v = [e for e in eng.store.read() if e["kind"] == "verify"][-1]
    assert v["passed"] is False and v["error"] == "timeout"


def test_a_missing_or_crashing_check_counts_as_not_done(tmp_path):
    eng = _engine(tmp_path)
    tid = _req(eng, [PY, "-c", "raise SystemExit('boom')"])
    assert eng.done(tid)["closed"] is False
    r = ot.run_verify([str(tmp_path / "nope" / "python.exe"), "-c", "0"], timeout_s=5)
    assert r["passed"] is False and r["error"]


# (6)
def test_editing_a_past_event_is_detected_and_refused(tmp_path):
    eng = _engine(tmp_path)
    tid = _req(eng, _exists_argv(tmp_path / "flag"))
    eng.comment(tid, "looking at it")
    path = tmp_path / "events.jsonl"
    lines = path.read_text(encoding="utf-8").splitlines()
    first = json.loads(lines[0])
    first["reason"] = "something else"
    lines[0] = json.dumps(first, sort_keys=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    with pytest.raises(ot.TamperedLog):
        eng.store.read()
    with pytest.raises(ot.TamperedLog):
        eng.comment(tid, "more")


def test_a_deleted_middle_event_is_detected(tmp_path):
    eng = _engine(tmp_path)
    tid = _req(eng, _exists_argv(tmp_path / "flag"))
    eng.comment(tid, "a")
    eng.comment(tid, "b")
    path = tmp_path / "events.jsonl"
    lines = path.read_text(encoding="utf-8").splitlines()
    del lines[1]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    with pytest.raises(ot.TamperedLog):
        eng.store.read()


def test_a_re_hashed_forged_event_still_breaks_the_chain(tmp_path):
    eng = _engine(tmp_path)
    tid = _req(eng, _exists_argv(tmp_path / "flag"))
    eng.comment(tid, "a")
    eng.comment(tid, "b")
    path = tmp_path / "events.jsonl"
    lines = path.read_text(encoding="utf-8").splitlines()
    forged = json.loads(lines[1])
    forged["text"] = "forged"
    forged["hash"] = ot._digest(forged)      # self-consistent line
    lines[1] = json.dumps(forged, sort_keys=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    with pytest.raises(ot.TamperedLog, match="chain"):
        eng.store.read()


# (7)
def test_a_withdrawn_task_never_re_notifies(tmp_path):
    sink = RecordingSink()
    eng = _engine(tmp_path, sink)
    flag = tmp_path / "flag"
    tid = _req(eng, _exists_argv(flag))
    eng.withdraw(tid, "no longer needed")
    flag.write_text("x", encoding="ascii")
    eng.verify_pending()
    eng.comment(tid, "late comment")
    assert len(sink.sent) == 1
    assert eng.pending() == []
    assert eng.task(tid).state == "withdrawn"
    # the scheduler never ran its check again
    assert not [e for e in eng.store.read() if e["kind"] == "verify"]


# (8)
def test_hold_mode_sends_nothing(tmp_path, monkeypatch):
    out = tmp_path / "notes.jsonl"
    monkeypatch.setenv(ot.HOLD_ENV, "1")
    sink = ot.FileSink(out)
    eng = _engine(tmp_path, sink)
    _req(eng, _exists_argv(tmp_path / "flag"))
    assert not out.exists()
    note = [e for e in eng.store.read() if e["kind"] == "notify"][0]
    assert note["ok"] is False and note["detail"] == "held"


def test_a_raising_sink_never_raises_into_the_engine(tmp_path):
    class Boom:
        def send(self, message):
            raise RuntimeError("down")
    eng = _engine(tmp_path, Boom())
    tid = _req(eng, _exists_argv(tmp_path / "flag"))
    note = [e for e in eng.store.read() if e["kind"] == "notify"][0]
    assert note["ok"] is False and "RuntimeError" in note["detail"]
    assert [t.id for t in eng.pending()] == [tid]


def test_comments_never_close(tmp_path):
    eng = _engine(tmp_path)
    tid = _req(eng, _exists_argv(tmp_path / "flag"))
    eng.comment(tid, "done!")
    assert [t.id for t in eng.pending()] == [tid]


def test_state_is_derived_from_the_log_not_a_stored_flag(tmp_path):
    flag = tmp_path / "flag"
    eng = _engine(tmp_path)
    tid = _req(eng, _exists_argv(flag))
    flag.write_text("x", encoding="ascii")
    eng.verify_pending()
    again = _engine(tmp_path)          # a fresh engine over the same file
    assert again.task(tid).state == "closed"
    assert all("state" not in e for e in again.store.read())


def test_acceptance_planted_task_closes_on_the_next_scheduled_pass(tmp_path):
    flag = tmp_path / "planted.flag"
    eng = _engine(tmp_path)
    tid = _req(eng, _exists_argv(flag), subject="planted")
    first = eng.verify_pending()
    assert first["closed"] == [] and first["open"] == [tid]
    flag.write_text("x", encoding="ascii")
    second = eng.verify_pending()
    assert second["closed"] == [tid] and eng.pending() == []


def test_a_closed_key_can_be_requested_again_as_a_new_task(tmp_path):
    flag = tmp_path / "flag"
    sink = RecordingSink()
    eng = _engine(tmp_path, sink)
    a = _req(eng, _exists_argv(flag))
    flag.write_text("x", encoding="ascii")
    eng.verify_pending()
    flag.unlink()
    b = _req(eng, _exists_argv(flag))
    assert a != b and len(sink.sent) == 2


# Hand-off rendering ---------------------------------------------------------

def test_render_lists_every_pending_task_and_passes_the_handoff_gate(tmp_path):
    eng = _engine(tmp_path)
    a = _req(eng, _exists_argv(tmp_path / "f1"), subject="one")
    b = _req(eng, _exists_argv(tmp_path / "f2"), subject="two",
             handoffs=["Settings > Sound > Output"])
    block = ot.render_operator_asks(eng.pending())
    assert a in block and b in block
    assert "Settings > Sound > Output" in block
    assert block.startswith(ot.ASKS_BEGIN) and block.rstrip().endswith(ot.ASKS_END)
    assert scan_handoff_text(block) == []
    # the verify argv (which may carry a path) is never rendered
    assert str(tmp_path) not in block


def test_render_with_nothing_pending_says_none(tmp_path):
    block = ot.render_operator_asks([])
    assert "none open" in block


def test_render_withholds_a_task_whose_text_fails_the_gate(tmp_path):
    eng = _engine(tmp_path)
    tid = eng.request("password", "x", reason="token " + "ab" * 20, steps=["s"],
                      verify_argv=_exists_argv(tmp_path / "f"))
    block = ot.render_operator_asks(eng.pending())
    assert tid in block and "withheld" in block
    assert scan_handoff_text(block) == []


def test_inject_replaces_an_old_block_and_keeps_the_rest(tmp_path):
    eng = _engine(tmp_path)
    _req(eng, _exists_argv(tmp_path / "f"), subject="fresh")
    old = "NEXT SESSION\n" + ot.ASKS_BEGIN + "\n  - stale ask\n" + ot.ASKS_END + "\nTail line\n"
    out = ot.inject_operator_asks(old, eng)
    assert "stale ask" not in out and "fresh" in out
    assert out.startswith("NEXT SESSION\n") and "Tail line" in out
    assert out.count(ot.ASKS_BEGIN) == 1


def test_inject_never_fails_on_an_unreadable_log(tmp_path):
    p = tmp_path / "events.jsonl"
    p.write_text("{not json\n", encoding="utf-8")
    eng = ot.TaskEngine(ot.JsonlTaskStore(p), sink=RecordingSink())
    out = ot.inject_operator_asks("NEXT SESSION\n", eng)
    assert "UNKNOWN" in out


def test_the_default_store_is_redirected_in_the_suite():
    # conftest points the engine at a per-test root; an arm must never touch
    # ops/runtime/operator_tasks/ on the live tree.
    live = Path(ot.ROOT) / "ops" / "runtime" / "operator_tasks"
    assert ot.default_root().resolve() != live.resolve()


def test_cli_request_list_and_done_round_trip(tmp_path, capsys):
    root = tmp_path / "root"
    flag = tmp_path / "flag"
    argv_json = json.dumps(_exists_argv(flag))
    assert ot.main(["--root", str(root), "request", "--cap", "physical", "--subject", "s",
                    "--reason", "r", "--step", "do it", "--verify-json", argv_json]) == 0
    tid = json.loads(capsys.readouterr().out)["id"]
    assert ot.main(["--root", str(root), "done", tid]) == 1
    capsys.readouterr()
    flag.write_text("x", encoding="ascii")
    assert ot.main(["--root", str(root), "verify-pending"]) == 0
    assert json.loads(capsys.readouterr().out)["closed"] == [tid]


# -- MAIN 0020 section 4 contract arms ------------------------------------------

def test_the_task_id_comes_from_capability_and_subject(tmp_path):
    flag = tmp_path / "flag"
    eng = _engine(tmp_path)
    a = eng.request("oauth", "gmail read", reason="r", steps=["s"],
                    verify_argv=_exists_argv(flag))
    assert a == "oauth.gmail-read"
    flag.write_text("x", encoding="ascii")
    eng.verify_pending()
    flag.unlink()
    b = eng.request("oauth", "gmail read", reason="r", steps=["s"],
                    verify_argv=_exists_argv(flag))
    assert b == "oauth.gmail-read-2"


def test_argv0_is_resolved_on_path_never_from_the_working_directory(tmp_path, monkeypatch):
    planted = tmp_path / "git.exe"
    planted.write_bytes(b"MZ")                  # a trap in the cwd
    monkeypatch.chdir(tmp_path)
    # an empty entry and "." both MEAN the cwd to a naive search
    monkeypatch.setenv("PATH", os.pathsep.join(["", ".", str(tmp_path / "empty-dir")]))
    assert ot.resolve_executable("git.exe") is None
    assert ot.resolve_executable("git") is None
    r = ot.run_verify(["git", "--version"], timeout_s=5)
    assert r["passed"] is False and "PATH" in r["error"]
    assert ot.resolve_executable(str(planted)) == str(planted)   # absolute: as given


def test_the_allowlist_is_the_one_the_owning_tree_passes(tmp_path):
    store = ot.JsonlTaskStore(tmp_path / "events.jsonl")
    eng = ot.TaskEngine(store, sink=RecordingSink(), allowlist={"git.exe"})
    with pytest.raises(ot.TaskRefused, match="allowlist"):
        eng.request("c", "s", reason="r", steps=["s"], verify_argv=["python", "-c", "0"])
    eng.request("c", "s", reason="r", steps=["s"], verify_argv=["git.exe", "status"])


def test_the_owner_is_the_engines_own_tree(tmp_path):
    store = ot.JsonlTaskStore(tmp_path / "events.jsonl")
    eng = ot.TaskEngine(store, sink=RecordingSink(), owner="RC")
    with pytest.raises(ot.TaskRefused, match="owner"):
        eng.request("c", "s", reason="r", steps=["s"], verify_argv=_exists_argv(tmp_path),
                    owner="LW")


def test_the_writer_lock_is_an_open_handle_and_never_unlinked(tmp_path):
    lock = tmp_path / "events.jsonl.lock"
    with ot.handle_lock(lock):
        with pytest.raises(ot.LockBusy):
            with ot.handle_lock(lock, wait_s=0.2):
                pass
    assert lock.exists()
    with ot.handle_lock(lock, wait_s=0.2):      # released: free again
        pass
    assert lock.exists()


def test_render_asks_is_the_engine_method(tmp_path):
    eng = _engine(tmp_path)
    tid = _req(eng, _exists_argv(tmp_path / "f"))
    assert tid in eng.render_asks() and eng.render_asks().startswith(ot.ASKS_BEGIN)
