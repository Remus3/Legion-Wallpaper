"""Arms for `tools/lw_inbox_responder.py`.

TWO DIRECTIONS, DELIBERATELY. RC audited its own tree on 2026-09-08 and found
115 external-binary call sites, 39 of them carrying FALSE-RED risk, against a
2116-line guard that can only see false-GREEN - because it audits skip
CONDITIONS and an ungated `subprocess.run([...], check=True)` has no skip to
inspect. So every allow rule here has a MIRROR arm proving the action is
actually permitted, not only that its denial denies. A gate that grades nothing
satisfies a one-directional suite perfectly.

THE THIRD DISPOSITION. RSC's finding, converged with LW's own `lw_model_pins`
four-state grading: CHECKED-AND-REFUSED and COULD-NOT-CHECK are different
answers, and neither may read as AUTO. The arms assert `checked` explicitly
rather than reading the verdict alone.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import lw_inbox_responder as responder  # noqa: E402


# --------------------------------------------------------------------------
# The gate: allowed actions, both directions
# --------------------------------------------------------------------------

def test_a1_read_only_measurement_in_own_tree_is_auto():
    """MIRROR ARM. The capability must actually fire, or the gate grades nothing."""
    d = responder.classify({"kind": "measure", "tree": "own", "writes": False})
    assert d.verdict == responder.AUTO
    assert d.rule == "A1"
    assert d.checked is True


def test_a1_refuses_a_measurement_that_writes():
    d = responder.classify({"kind": "measure", "tree": "own", "writes": True})
    assert d.verdict == responder.DRAFT
    assert d.checked is True


def test_a1_refuses_a_measurement_of_someone_elses_tree():
    d = responder.classify({"kind": "measure", "tree": "sibling", "writes": False})
    assert d.verdict == responder.DRAFT


def test_a1_cannot_be_decided_without_the_writes_field():
    """COULD-NOT-CHECK is its own answer and never reads as AUTO."""
    d = responder.classify({"kind": "measure", "tree": "own"})
    assert d.verdict == responder.DRAFT
    assert d.checked is False


def test_a2_suite_run_is_auto_only_with_a_timeout_and_a_file_ceiling():
    """MIRROR ARM plus RSC 4c: a suite is arbitrary code with write authority."""
    ok = responder.classify(
        {"kind": "suite", "timeout_s": 600, "max_files": 5000, "reports": ["exit_code", "passed", "skipped"]}
    )
    assert (ok.verdict, ok.rule, ok.checked) == (responder.AUTO, "A2", True)


def test_a2_refuses_an_unbounded_suite_run():
    d = responder.classify({"kind": "suite", "reports": ["exit_code", "passed", "skipped"]})
    assert d.verdict == responder.DRAFT
    assert "timeout" in d.reason or "ceiling" in d.reason


def test_a2_refuses_a_report_without_the_skip_count():
    """CS measured a gate reporting PASS with 5 skipped. Counts, not a verdict."""
    d = responder.classify(
        {"kind": "suite", "timeout_s": 600, "max_files": 5000, "reports": ["exit_code", "passed"]}
    )
    assert d.verdict == responder.DRAFT


def test_a2_refuses_a_reported_verdict_in_place_of_counts():
    d = responder.classify(
        {"kind": "suite", "timeout_s": 600, "max_files": 5000, "reports": ["green"]}
    )
    assert d.verdict == responder.DRAFT


def test_a3_vendor_is_auto_when_two_independent_carriers_corroborate():
    """MIRROR ARM. The narrowed A3 must still have a case it accepts."""
    d = responder.classify({
        "kind": "vendor",
        "digest": "a" * 64,
        "citations": [{"carrier": "RC", "digest": "a" * 64},
                      {"carrier": "CS", "digest": "a" * 64}],
        "sender": "RSC",
    })
    assert (d.verdict, d.rule, d.checked) == (responder.AUTO, "A3", True)


def test_a3_refuses_a_digest_corroborated_only_by_its_own_sender():
    """RSC 4a and CS: one sender agreeing with itself proves transport, not authority."""
    d = responder.classify({
        "kind": "vendor",
        "digest": "a" * 64,
        "citations": [{"carrier": "RSC", "digest": "a" * 64},
                      {"carrier": "RSC", "digest": "a" * 64}],
        "sender": "RSC",
    })
    assert d.verdict == responder.DRAFT
    assert d.checked is True


def test_a3_does_not_count_the_sender_towards_its_own_corroboration():
    """The mutant this arm exists to kill SURVIVED the first pass.

    Two citations both from the sender were already refused by the count alone,
    so letting the sender count as a carrier changed no result and the rule read
    as tested when it was not. Sender plus ONE other carrier is the case that
    separates them: one independent measurement, not two.
    """
    d = responder.classify({
        "kind": "vendor",
        "digest": "a" * 64,
        "citations": [{"carrier": "RSC", "digest": "a" * 64},
                      {"carrier": "RC", "digest": "a" * 64}],
        "sender": "RSC",
    })
    assert d.verdict == responder.DRAFT
    assert d.checked is True


def test_a3_refuses_when_a_cited_carrier_disagrees_about_the_bytes():
    d = responder.classify({
        "kind": "vendor",
        "digest": "a" * 64,
        "citations": [{"carrier": "RC", "digest": "a" * 64},
                      {"carrier": "CS", "digest": "b" * 64}],
        "sender": "RSC",
    })
    assert d.verdict == responder.DRAFT


def test_a3_with_no_citations_at_all_is_could_not_check():
    d = responder.classify({"kind": "vendor", "digest": "a" * 64, "sender": "RSC"})
    assert d.verdict == responder.DRAFT
    assert d.checked is False


def test_a4_pin_move_is_auto_only_beside_an_accepted_vendor_reporting_old_and_new():
    """MIRROR ARM for RSC 4b's surviving case."""
    d = responder.classify({
        "kind": "pin_move",
        "with_accepted_vendor": True,
        "old": "a" * 64,
        "new": "b" * 64,
    })
    assert (d.verdict, d.rule, d.checked) == (responder.AUTO, "A4", True)


def test_a4_standalone_pin_move_is_refused():
    """CS: a pin that updates itself to whatever arrived is not a pin."""
    d = responder.classify({"kind": "pin_move", "with_accepted_vendor": False,
                            "old": "a" * 64, "new": "b" * 64})
    assert d.verdict == responder.DRAFT


def test_a4_refuses_a_pin_move_that_does_not_report_the_old_value():
    d = responder.classify({"kind": "pin_move", "with_accepted_vendor": True, "new": "b" * 64})
    assert d.verdict == responder.DRAFT


def test_a5_reply_is_auto_into_the_repos_the_note_names():
    """MIRROR ARM. Without A5 the responder is inert by D8 - RSC 4d."""
    d = responder.classify(
        {"kind": "reply", "targets": ["RC", "CS"], "overwrites": False},
        note={"names": ["RC", "CS", "LL"]},
    )
    assert (d.verdict, d.rule, d.checked) == (responder.AUTO, "A5", True)


def test_a5_refuses_a_reply_into_a_repo_the_note_never_named():
    d = responder.classify(
        {"kind": "reply", "targets": ["RC", "LL"], "overwrites": False},
        note={"names": ["RC"]},
    )
    assert d.verdict == responder.DRAFT


def test_a5_refuses_an_overwrite_of_an_existing_note():
    d = responder.classify(
        {"kind": "reply", "targets": ["RC"], "overwrites": True},
        note={"names": ["RC"]},
    )
    assert d.verdict == responder.DRAFT


# --------------------------------------------------------------------------
# The deny set
# --------------------------------------------------------------------------

@pytest.mark.parametrize("kind,rule", [
    ("history_rewrite", "D1"),
    ("push", "D2"),
    ("visibility", "D2"),
    ("policy", "D3"),
    ("delete", "D4"),
    ("scheduled_task", "D5"),
    ("hook", "D5"),
    ("service", "D5"),
    ("frozen_file", "D6"),
])
def test_every_deny_kind_lands_on_its_own_rule(kind, rule):
    d = responder.classify({"kind": kind})
    assert d.verdict == responder.DRAFT
    assert d.rule == rule


def test_an_unrecognised_action_is_denied_by_default():
    d = responder.classify({"kind": "rm_minus_rf_the_universe"})
    assert (d.verdict, d.rule) == (responder.DRAFT, "D8")


def test_a_note_marking_an_action_operator_gated_beats_every_allow_rule():
    """D7 outranks A1: the sender's own gate is not ours to overrule."""
    d = responder.classify(
        {"kind": "measure", "tree": "own", "writes": False},
        note={"operator_gated": True},
    )
    assert (d.verdict, d.rule) == (responder.DRAFT, "D7")


def test_registering_the_responder_task_is_itself_denied():
    """THE TRAP in RC's own list: LW-InboxResponder registration is D5."""
    d = responder.classify({"kind": "scheduled_task", "name": "LW-InboxResponder"})
    assert (d.verdict, d.rule) == (responder.DRAFT, "D5")


# --------------------------------------------------------------------------
# The output filter - RSC 4d: the reply is the unbounded surface
# --------------------------------------------------------------------------

def test_the_output_filter_refuses_a_reply_carrying_an_account_path():
    hits = responder.filter_reply(r"the fix is in C:\Users\someaccount\AppData\Local")
    assert hits
    assert any("account path" in h for h in hits)


def test_the_output_filter_refuses_a_raw_api_error_string():
    hits = responder.filter_reply("failed: 429 rate_limit_error from the API")
    assert hits


def test_the_output_filter_passes_an_ordinary_measured_reply():
    """MIRROR ARM. A filter that rejects everything is not a filter."""
    assert responder.filter_reply("suite exit 0, 2813 passed, 18 skipped") == []


def test_the_output_filter_catches_a_pinned_identity_split_across_a_separator():
    """Reuses tools/split_scan.py rather than re-deriving a second matcher."""
    import split_scan

    probe = split_scan.pin("probe", "zqxsplitprobe")
    assert responder.filter_reply("zqx split probe", fragments=(probe,))


# --------------------------------------------------------------------------
# New-note detection, and the report-never-acknowledge boundary
# --------------------------------------------------------------------------

def test_new_notes_are_keyed_by_content_so_an_in_place_edit_re_fires(tmp_path):
    inbox = tmp_path / "moon_sync_inbox"
    inbox.mkdir()
    note = inbox / "2026-09-10-0000-from-RC-hello.md"
    note.write_text("first", encoding="utf-8")
    state = tmp_path / "seen.json"

    first = responder.new_notes(inbox, state)
    assert [n.name for n in first] == [note.name]
    responder.record_seen(inbox, state, first)
    assert responder.new_notes(inbox, state) == []

    note.write_text("corrected in place", encoding="utf-8")
    assert [n.name for n in responder.new_notes(inbox, state)] == [note.name]


def test_a_withdrawn_note_that_comes_back_is_new_again(tmp_path):
    """The state prunes to what is LIVE, so it cannot grow without bound and a
    re-filed note is not silently swallowed by a key from its first arrival.
    `lw_facts` prunes for the same reason - this channel has withdrawn notes."""
    inbox = tmp_path / "moon_sync_inbox"
    inbox.mkdir()
    note = inbox / "2026-09-10-0002-from-LL-withdrawn.md"
    note.write_text("body", encoding="utf-8")
    state = tmp_path / "seen.json"
    responder.record_seen(inbox, state, responder.new_notes(inbox, state))
    assert responder.new_notes(inbox, state) == []

    note.unlink()
    responder.record_seen(inbox, state, [])
    assert json.loads(state.read_text(encoding="utf-8"))["seen"] == []

    note.write_text("body", encoding="utf-8")
    assert [n.name for n in responder.new_notes(inbox, state)] == [note.name]


def test_draft_prefixed_notes_are_not_picked_up(tmp_path):
    inbox = tmp_path / "moon_sync_inbox"
    inbox.mkdir()
    (inbox / "_draft.md").write_text("wip", encoding="utf-8")
    assert responder.new_notes(inbox, tmp_path / "seen.json") == []


def test_the_responder_state_file_is_not_the_watchers_seen_file():
    """The responder must never acknowledge on the operator's behalf.

    `lw_facts` keeps `ops/runtime/sync_inbox_seen.json` for the SessionStart
    report. A responder writing that file would silence the operator's own mail
    - the report-never-acknowledge contract RC's poller docstring names.
    """
    import lw_facts

    assert responder.STATE_PATH != lw_facts._SEEN
    assert responder.STATE_PATH != lw_facts._REPORTED


# --------------------------------------------------------------------------
# The spawn: detached, headless, never the operator's window
# --------------------------------------------------------------------------

def test_the_spawn_argv_is_headless_and_carries_no_window_binding():
    argv = responder.spawn_argv(Path("moon_sync_inbox/note.md"))
    assert "-p" in argv
    joined = " ".join(argv).lower()
    assert "autohotkey" not in joined and ".ahk" not in joined
    assert "--title" not in joined


def test_the_spawn_prompt_names_the_note_and_the_deny_set():
    argv = responder.spawn_argv(Path("moon_sync_inbox/note.md"))
    prompt = argv[-1]
    assert "note.md" in prompt
    assert "D8" in prompt and "default deny" in prompt.lower()


def test_a_missing_claude_cli_reports_unavailable_and_never_success(monkeypatch):
    """FALSE-RED direction. An absent binary is COULD-NOT-RUN, not a failure
    and emphatically not a success - the same three-disposition rule the gate
    uses, applied to this module's own external-binary call site."""
    monkeypatch.setattr(responder.shutil, "which", lambda _name: None)
    outcome = responder.spawn(Path("moon_sync_inbox/note.md"))
    assert outcome.verdict == responder.UNAVAILABLE
    assert outcome.checked is False


def test_dry_run_spawns_nothing(monkeypatch):
    """MIRROR ARM for the spawn site: with the CLI present it still must not
    launch under --dry-run."""
    monkeypatch.setattr(responder.shutil, "which", lambda _name: r"C:\fake\claude.exe")

    def _boom(*_a, **_k):  # pragma: no cover - the arm is that it is not called
        raise AssertionError("dry run spawned a process")

    monkeypatch.setattr(responder.subprocess, "Popen", _boom)
    outcome = responder.spawn(Path("moon_sync_inbox/note.md"), dry_run=True)
    assert outcome.verdict == responder.AUTO
    assert outcome.checked is True


def test_the_spawn_is_detached_and_windowless(monkeypatch):
    seen = {}

    def _fake_popen(argv, **kwargs):
        seen["argv"] = argv
        seen["kwargs"] = kwargs

        class _P:
            pid = 4242

        return _P()

    monkeypatch.setattr(responder.shutil, "which", lambda _name: r"C:\fake\claude.exe")
    monkeypatch.setattr(responder.subprocess, "Popen", _fake_popen)
    outcome = responder.spawn(Path("moon_sync_inbox/note.md"))
    assert outcome.verdict == responder.AUTO
    flags = seen["kwargs"]["creationflags"]
    assert flags & responder.NO_WINDOW == responder.NO_WINDOW
    assert flags & responder.DETACHED == responder.DETACHED


# --------------------------------------------------------------------------
# Registration stays an operator act
# --------------------------------------------------------------------------

def test_the_register_command_is_printed_and_never_executed():
    cmd = responder.register_command()
    assert "schtasks" in cmd and "LW-InboxResponder" in cmd


def test_no_process_launch_in_this_module_mentions_schtasks():
    """The one step that waits for the operator, asserted rather than intended.

    Registering `LW-InboxResponder` is D5 in RC's own deny set, so the module
    may PRINT the command and must never be able to run it. Asserted over the
    launch sites rather than over prose, which is where the two differ.
    """
    source = (ROOT / "tools" / "lw_inbox_responder.py").read_text(encoding="utf-8")
    launches = [ln for ln in source.splitlines()
                if ("subprocess.run(" in ln or "subprocess.Popen(" in ln
                    or "os.system(" in ln or "os.startfile(" in ln)]
    assert launches, "no launch site found - the arm would pass vacuously"
    for line in launches:
        assert "schtasks" not in line, line


def test_cli_print_register_command_exits_zero_without_touching_the_scheduler(tmp_path):
    proc = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "lw_inbox_responder.py"), "--print-register-command"],
        capture_output=True, text=True, cwd=str(ROOT),
    )
    assert proc.returncode == 0
    assert "schtasks" in proc.stdout
    assert "operator" in proc.stdout.lower()


def _fill(inbox: Path, n: int) -> None:
    inbox.mkdir(parents=True, exist_ok=True)
    for i in range(n):
        (inbox / f"2026-09-10-{i:04d}-from-RC-note.md").write_text(f"note {i}", encoding="utf-8")


def test_a_cold_start_baselines_the_inbox_and_spawns_nothing(tmp_path, capsys, monkeypatch):
    """Measured on the LIVE inbox before this branch existed: a first run with no
    state file reported 139 new notes and would have launched 139 sessions."""
    inbox = tmp_path / "moon_sync_inbox"
    _fill(inbox, 5)
    state = tmp_path / "seen.json"
    monkeypatch.setattr(responder, "spawn",
                        lambda *_a, **_k: pytest.fail("cold start spawned a session"))

    assert responder.main(["--once", "--inbox", str(inbox), "--state", str(state)]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["cold_start"] is True
    assert payload["baselined"] == 5
    assert state.exists()
    assert responder.new_notes(inbox, state) == []


def test_after_the_baseline_a_new_note_does_spawn(tmp_path, capsys, monkeypatch):
    """MIRROR ARM. A responder that baselines everything forever answers nothing."""
    inbox = tmp_path / "moon_sync_inbox"
    _fill(inbox, 2)
    state = tmp_path / "seen.json"
    monkeypatch.setattr(responder, "spawn", lambda *_a, **_k: responder._auto("spawn", "fake"))
    responder.main(["--once", "--inbox", str(inbox), "--state", str(state)])
    capsys.readouterr()

    (inbox / "2026-09-10-9999-from-CS-fresh.md").write_text("fresh", encoding="utf-8")
    assert responder.main(["--once", "--inbox", str(inbox), "--state", str(state)]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["new_notes"] == 1
    assert [s["note"] for s in payload["spawned"]] == ["2026-09-10-9999-from-CS-fresh.md"]


def test_a_burst_is_capped_and_the_remainder_is_deferred_not_dropped(tmp_path, capsys, monkeypatch):
    inbox = tmp_path / "moon_sync_inbox"
    _fill(inbox, 1)
    state = tmp_path / "seen.json"
    monkeypatch.setattr(responder, "spawn", lambda *_a, **_k: responder._auto("spawn", "fake"))
    responder.main(["--once", "--inbox", str(inbox), "--state", str(state)])
    capsys.readouterr()

    for i in range(5):
        (inbox / f"2026-09-10-8{i:03d}-from-LL-burst.md").write_text(f"b{i}", encoding="utf-8")
    responder.main(["--once", "--inbox", str(inbox), "--state", str(state)])
    payload = json.loads(capsys.readouterr().out)
    assert len(payload["spawned"]) == responder.MAX_SPAWNS_PER_CYCLE
    assert payload["deferred"] == 5 - responder.MAX_SPAWNS_PER_CYCLE
    assert len(responder.new_notes(inbox, state)) == 5 - responder.MAX_SPAWNS_PER_CYCLE


def test_cli_once_dry_run_reports_json_and_changes_no_state(tmp_path):
    inbox = tmp_path / "moon_sync_inbox"
    inbox.mkdir()
    (inbox / "2026-09-10-0001-from-RC-x.md").write_text("hello", encoding="utf-8")
    state = tmp_path / "seen.json"
    proc = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "lw_inbox_responder.py"),
         "--once", "--dry-run", "--inbox", str(inbox), "--state", str(state)],
        capture_output=True, text=True, cwd=str(ROOT),
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["dry_run"] is True
    assert payload["spawned"] == []
    assert not state.exists(), "a dry run recorded state"
