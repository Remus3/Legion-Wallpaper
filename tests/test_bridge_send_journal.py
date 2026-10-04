"""AHK bridge: single-paste delivery + attempt/result send journal (ingest P1-6).

Controller side (Python, fake sender): every gemini.ready hand-off writes an
ATTEMPT line before the send and a RESULT line after it, sharing an id, and
stores length + sha256 of the text, never the text. An attempt without a
result is a sender that died mid-send. Bridge side (static arms over the .ahk):
non-slash lines go as ONE clipboard paste with save/restore and a SEPARATE
Enter, and the target's process is checked before anything is sent.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location(
    "lw_loop_executor_journal_t", ROOT / "ops" / "loop" / "executor.py")
executor = importlib.util.module_from_spec(_spec)
sys.modules["lw_loop_executor_journal_t"] = executor
_spec.loader.exec_module(executor)

AHK = (ROOT / "ops" / "loop" / "claude_gui_bridge.ahk").read_text(encoding="utf-8")

NASTY = 'line "one" with \\back\\slashes and $dollar\nline two\n' + "\n".join(
    f"row {i}: 'q' \"qq\" \\ $x `tick`" for i in range(40))


def _journal_rows(path: Path) -> list[dict]:
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines()]


def test_attempt_then_result_share_an_id_and_store_hash_not_text(tmp_path):
    j = executor.SendJournal(tmp_path / "sends.jsonl")
    jid = j.attempt(NASTY, target="ahk")
    j.result(jid, ok=True, detail="consumed")
    rows = _journal_rows(tmp_path / "sends.jsonl")
    assert [r["kind"] for r in rows] == ["attempt", "result"]
    assert rows[0]["id"] == rows[1]["id"] == jid
    assert rows[0]["len"] == len(NASTY)
    assert rows[0]["sha256"] == hashlib.sha256(NASTY.encode("utf-8")).hexdigest()
    raw = (tmp_path / "sends.jsonl").read_text(encoding="utf-8")
    assert "row 7" not in raw and "dollar" not in raw


def test_the_journal_never_raises(tmp_path):
    blocker = tmp_path / "f"
    blocker.write_text("x", encoding="ascii")
    j = executor.SendJournal(blocker / "sub" / "sends.jsonl")
    jid = j.attempt("x")
    j.result(jid, ok=False)                    # no exception


class _Rec:
    def __init__(self):
        self.order: list[str] = []


def _ahk(tmp_path, rec, *, consumed=True):
    journal = executor.SendJournal(tmp_path / "sends.jsonl")
    real_attempt, real_result = journal.attempt, journal.result

    def attempt(text, **k):
        rec.order.append("attempt")
        return real_attempt(text, **k)

    def result(jid, **k):
        rec.order.append("result")
        return real_result(jid, **k)
    journal.attempt, journal.result = attempt, result

    def stop(msg):
        rec.order.append("stop")
        raise SystemExit(1)

    (tmp_path / "claude.done").write_text("{}", encoding="utf-8")
    return executor.build(
        {"cycle_deadline_sec": 5, "channel": "ahk"}, tmp_path,
        log=lambda m: None, stop=stop,
        awrite=lambda p, t: rec.order.append("send"),
        wait_for=lambda p, d: True,
        wait_gone=lambda p, d: consumed,
        rjson=lambda *a, **k: {}, stall_action=lambda n: "stop",
        stall_recovery_directive=lambda c: "recover",
        journal=journal), journal


def test_the_executor_journals_attempt_before_send_and_result_after(tmp_path):
    rec = _Rec()
    ex, _j = _ahk(tmp_path, rec)
    ex.run(3, NASTY, "fixed")
    assert rec.order == ["attempt", "send", "result"]
    rows = _journal_rows(tmp_path / "sends.jsonl")
    assert rows[1]["ok"] is True
    payload = executor.directive_payload(3, NASTY, "fixed", True)
    assert rows[0]["sha256"] == hashlib.sha256(payload.encode("utf-8")).hexdigest()


def test_an_unconsumed_send_is_journalled_as_failed_before_the_stop(tmp_path):
    rec = _Rec()
    ex, _j = _ahk(tmp_path, rec, consumed=False)
    with pytest.raises(SystemExit):
        ex.run(3, "body", "fixed")
    assert rec.order == ["attempt", "send", "result", "stop"]
    rows = _journal_rows(tmp_path / "sends.jsonl")
    assert rows[1]["ok"] is False and "not consumed" in rows[1]["detail"]


def test_the_default_journal_is_redirected_in_the_suite():
    live = ROOT / "ops" / "runtime" / "bridge" / "sends.jsonl"
    assert executor.default_journal_path().resolve() != live.resolve()


# -- the bridge (static: the .ahk is never run by the suite) -------------------

def test_the_bridge_pastes_non_slash_lines_as_one_block():
    assert "ClipboardAll()" in AHK, "the operator's clipboard must be saved"
    assert "A_Clipboard := saved" in AHK, "and restored"
    assert 'Send("^v")' in AHK
    # a plain line is never typed with SendText any more
    assert "SendText(lineText)" not in AHK


def test_the_clipboard_is_restored_after_the_paste_not_only_on_failure():
    paste = AHK.index('Send("^v")')
    end = AHK.index("}", paste)
    assert "A_Clipboard := saved" in AHK[paste:end]


def test_the_target_is_checked_before_activation_and_again_once_focused():
    loop = AHK[AHK.index('LogMsg("ahk bridge start (LW)")'):]
    activate = loop.index("WinActivate(win)")
    assert "TargetOk(win)" in loop[:activate]
    assert 'TargetOk("A")' in loop[activate:loop.index('SendText("/")')]


def test_enter_is_sent_separately_after_the_paste():
    paste = AHK.index('Send("^v")')
    enter = AHK.index('Send("{Enter}")', paste)
    between = AHK[paste:enter]
    assert "Sleep" in between


def test_the_bridge_checks_the_target_process_before_sending():
    check = AHK.index("WinGetProcessName")
    first_send = min(AHK.index('Send("^v")'), AHK.index('SendText("/")'))
    assert check < first_send
    assert '"claude.exe"' in AHK and "REFUSE" in AHK
