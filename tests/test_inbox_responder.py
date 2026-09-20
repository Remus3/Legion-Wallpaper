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

import ast
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import lw_inbox_responder as responder  # noqa: E402

# Captured BEFORE any fixture can redirect it, so the arm pinning the real
# default still reads the real default even while every other arm runs against
# an injected one.
REAL_HALT_PATH = responder.HALT_PATH


@pytest.fixture(autouse=True)
def _the_live_run_log_is_never_touched():
    """A test that writes `ops/runtime/inbox_responder/runs.jsonl` fabricates
    responder history in the operator's real tree.

    MEASURED, not hypothetical: the cycle arms below drove `main()` without a
    `--runlog`, and the first suite run after the log landed appended 13 records
    of invented cold starts to the live file. Injecting the path at each call
    site fixes those arms; this fixture is what keeps the NEXT one honest, and
    it guards by MTIME rather than by patching the constant, so the arm pinning
    the real default still reads the real default.
    """
    real = responder.RUNLOG_PATH
    before = real.stat().st_mtime_ns if real.exists() else None
    yield
    after = real.stat().st_mtime_ns if real.exists() else None
    assert after == before, f"an arm wrote the live run log at {real}"


@pytest.fixture(autouse=True)
def _the_live_kill_switch_is_never_read(monkeypatch, tmp_path):
    """An arm that falls through to the default `--halt` reads the OPERATOR'S
    kill switch, so the suite's colour depends on machine state.

    MEASURED 2026-09-11: the operator disarmed both headless lanes at a session
    wrap, and four arms here went red - not because anything regressed, but
    because a real HALT file existed and `main()` obeyed it. That is the test's
    defect, not the operator's. Sibling rule already in this file for the run
    log: inject the path rather than inherit it.

    The subprocess arms cannot be reached by monkeypatch, so `_cli` sets the
    module attribute inside the child before `main()` runs - passing `--halt`
    there would no longer suppress the default anyway, which is the point of the
    2026-09-20 fix. `REAL_HALT_PATH` keeps the default-pinning arm honest.
    """
    monkeypatch.setattr(responder, "HALT_PATH", tmp_path / "never-created-HALT")


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
    """`example` is deliberate: it is in `PLACEHOLDER_ACCOUNTS`, so this fixture
    does not itself trip `tests/test_no_account_paths.py` on a PUBLIC repo. The
    filter under test exempts no account name - only a `<...>` placeholder - so
    the arm still measures what it says it does."""
    hits = responder.filter_reply(r"the fix is in C:\Users\example\AppData\Local")
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
    assert "Register-ScheduledTask" in cmd and "LW-InboxResponder" in cmd
    assert "lw_inbox_responder.py" in cmd and "--once" in cmd


def test_the_script_path_is_quoted_inside_the_argument_string():
    """THE DEFECT THIS ARM EXISTS FOR. The first shipped spelling was a
    `schtasks` line using cmd's `\\"` escape, run from PowerShell, which strips
    the backslashes: schtasks saw `/TR` end at the first inner quote and read the
    rest as its own options - `ERROR: Invalid argument/option - '--once /F'`, in
    the operator's hands. The repo root contains a space, so an unquoted script
    path is not a style question."""
    cmd = responder.register_command()
    script = str(responder.ROOT / "tools" / "lw_inbox_responder.py")
    assert f"'\"{script}\" --once'" in cmd, cmd
    assert "\\\"" not in cmd, "cmd.exe escaping in the PowerShell form is the bug"


def test_the_cmd_form_uses_cmds_own_escaping_and_not_powershells():
    """MIRROR: the fallback is for a shell where `\\"` IS the escape."""
    cmd = responder.register_command("cmd")
    assert cmd.startswith("schtasks ")
    assert '\\"' in cmd and "Register-ScheduledTask" not in cmd


def test_the_register_command_spells_no_account_name_in_source():
    """It resolves the interpreter at runtime through `lw_paths`. A literal would
    publish the account name, and this repo is PUBLIC."""
    source = (ROOT / "tools" / "lw_inbox_responder.py").read_text(encoding="utf-8")
    assert "lw_paths.system_python()" in source
    assert "Users\\" not in source


@pytest.mark.skipif(shutil.which("powershell") is None and shutil.which("pwsh") is None,
                    reason="no PowerShell on this machine, so the emitted command "
                           "cannot be parse-checked here - could not check, which is "
                           "not the same as checked and found clean")
def test_the_emitted_powershell_actually_parses():
    """Parses it, never runs it. Registering the task is D5."""
    exe = shutil.which("powershell") or shutil.which("pwsh")
    probe = (
        "$errs=$null;"
        "$null=[System.Management.Automation.Language.Parser]::ParseInput("
        "$env:LW_REG_CMD,[ref]$null,[ref]$errs);"
        "if($errs.Count -eq 0){'OK'}else{$errs|%{$_.Message}}"
    )
    env = dict(os.environ, LW_REG_CMD=responder.register_command())
    out = subprocess.run([exe, "-NoProfile", "-NonInteractive", "-Command", probe],
                         capture_output=True, text=True, env=env).stdout
    assert out.strip() == "OK", out


# --------------------------------------------------------------------------
# "This module may PRINT the registration and must never RUN it" - asserted
# over the syntax tree and over behaviour, never over lines.
#
# THE DEFECT THIS SECTION REPLACES, measured 2026-09-20. The shipped arm was a
# LINE-scoped scan: it collected source lines containing `subprocess.run(` and
# friends and asserted none of them said `schtasks`. A plain multi-line call
#
#     subprocess.run(
#         ["schtasks", "/Create", ...],
#     )
#
# puts the launcher and its arguments on different lines, so the scan collected
# the first and read `schtasks` on the second - and passed. No adversary is
# needed for that; it is how a formatter writes a long call. A guard a newline
# defeats is not a guard, so the instrument changed rather than the wording.
# --------------------------------------------------------------------------

_SPAWN_MODULES = ("subprocess", "os")
_SUBPROCESS_SPAWNS = frozenset({"run", "Popen", "call", "check_call",
                                "check_output", "getoutput", "getstatusoutput"})


def _is_spawn(module: str, attr: str) -> bool:
    """Does `module.attr` start a process?

    `os` is matched by PREFIX on purpose: the family is `spawnl`, `spawnle`,
    `spawnlp`, `spawnv`, `spawnve`, `spawnvp`, `execv`, `execve`, `execl`,
    `posix_spawn` and more, and enumerating it by hand is how the next spelling
    gets missed.
    """
    if module == "subprocess":
        return attr in _SUBPROCESS_SPAWNS
    return (attr in {"system", "popen", "startfile"}
            or attr.startswith(("spawn", "exec", "posix_spawn")))


def _spawn_sites(source: str) -> list[tuple[int, str]]:
    """Every process-launch site in `source`, as (lineno, the whole call text).

    AST, not lines. It resolves `import subprocess as sp`, `from os import
    system`, and a `getattr(subprocess, "run")` indirection, and because the
    text it returns is `ast.unparse` of the enclosing CALL, a line break inside
    the argument list cannot hide an argument from the caller's assertion.

    A `getattr` on a spawn module whose attribute is not a literal is reported
    too: an opaque lookup is exactly the shape a launcher hides in, and the
    module has no legitimate use for one.
    """
    tree = ast.parse(source)
    parents = {child: parent for parent in ast.walk(tree)
               for child in ast.iter_child_nodes(parent)}

    aliases: dict[str, str] = {}
    from_imports: dict[str, tuple[str, str]] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                if a.name in _SPAWN_MODULES:
                    aliases[a.asname or a.name] = a.name
        elif isinstance(node, ast.ImportFrom) and node.module in _SPAWN_MODULES:
            for a in node.names:
                from_imports[a.asname or a.name] = (node.module, a.name)

    hits: list[ast.AST] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
            module = aliases.get(node.value.id)
            if module and _is_spawn(module, node.attr):
                hits.append(node)
        elif isinstance(node, ast.Name) and node.id in from_imports:
            if _is_spawn(*from_imports[node.id]):
                hits.append(node)
        elif (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
              and node.func.id == "getattr" and node.args
              and isinstance(node.args[0], ast.Name)
              and node.args[0].id in aliases):
            attr = node.args[1] if len(node.args) > 1 else None
            if isinstance(attr, ast.Constant) and isinstance(attr.value, str):
                if _is_spawn(aliases[node.args[0].id], attr.value):
                    hits.append(node)
            else:
                hits.append(node)

    sites: set[tuple[int, str]] = set()
    for hit in hits:
        chosen = hit if isinstance(hit, ast.Call) else None
        node = hit
        while node in parents:
            node = parents[node]
            if isinstance(node, ast.stmt):
                break
            if isinstance(node, ast.Call):
                chosen = node
        sites.add((hit.lineno, ast.unparse(chosen if chosen is not None else node)))
    return sorted(sites)


def _the_line_scoped_scan_this_replaced(source: str) -> list[str]:
    """The SHIPPED instrument, kept verbatim as the fossil the arm below pins.

    NOT a guard. It exists so the defeat is a measurement in the suite rather
    than a claim in a commit message.
    """
    return [ln for ln in source.splitlines()
            if ("subprocess.run(" in ln or "subprocess.Popen(" in ln
                or "os.system(" in ln or "os.startfile(" in ln)]


# Every one of these launches `schtasks`. Each is a shape the line-scoped scan
# could not see; the first needs no adversary at all.
_EVASIONS = {
    "a plain multi-line call": (
        "import subprocess\n"
        "subprocess.run(\n"
        '    ["schtasks", "/Create", "/TN", "LW-InboxResponder"],\n'
        ")\n"
    ),
    "an aliased import": (
        "import subprocess as sp\n"
        'sp.run(["schtasks", "/Create"])\n'
    ),
    "a from-import": (
        "from subprocess import run\n"
        'run(["schtasks", "/Create"])\n'
    ),
    "a getattr indirection": (
        "import subprocess\n"
        'getattr(subprocess, "run")(["schtasks", "/Create"])\n'
    ),
    "os.system": (
        "import os\n"
        'os.system("schtasks /Create /TN LW-InboxResponder")\n'
    ),
    "os.popen": (
        "import os\n"
        'os.popen("schtasks /Query").read()\n'
    ),
    "os.spawnl": (
        "import os\n"
        'os.spawnl(os.P_NOWAIT, "schtasks.exe", "schtasks", "/Create")\n'
    ),
}


@pytest.mark.parametrize("shape", sorted(_EVASIONS))
def test_the_launch_detector_sees_every_shape_a_line_scan_missed(shape):
    """The spec for the instrument. Each fixture DOES register the task."""
    sites = _spawn_sites(_EVASIONS[shape])
    assert sites, f"{shape}: the detector found no launch site at all"
    assert any("schtasks" in text for _ln, text in sites), \
        f"{shape}: the detector found {sites} but cannot see the schtasks argument"


def test_a_line_break_alone_defeated_the_scan_this_replaced():
    """WHY the instrument changed, as a measurement rather than an assertion.

    The evasion here is a formatter's output, not an attack: the launcher on
    one line and its argument list on the next.
    """
    evasion = _EVASIONS["a plain multi-line call"]
    collected = _the_line_scoped_scan_this_replaced(evasion)
    assert collected, "the fossil scan did not even find the launcher line"
    assert not any("schtasks" in ln for ln in collected), \
        "this fixture no longer demonstrates the defeat it was written for"
    assert any("schtasks" in text for _ln, text in _spawn_sites(evasion))


def test_the_launch_detector_does_not_flag_printing_the_command():
    """MIRROR. A detector that flags every mention of `schtasks` grades nothing:
    this module's whole job is to PRINT that command."""
    assert _spawn_sites('import subprocess\nprint("schtasks /Create")\n') == []


def test_no_process_launch_in_this_module_mentions_schtasks():
    """The one step that waits for the operator, asserted rather than intended.

    Registering `LW-InboxResponder` is D5 in RC's own deny set, so the module
    may PRINT the command and must never be able to run it. Asserted over the
    launch sites rather than over prose, which is where the two differ.
    """
    source = (ROOT / "tools" / "lw_inbox_responder.py").read_text(encoding="utf-8")
    sites = _spawn_sites(source)
    assert any("Popen" in text for _ln, text in sites), \
        f"no launch site found - the arm would pass vacuously (saw {sites})"
    for lineno, text in sites:
        low = text.lower()
        assert "schtasks" not in low, f"line {lineno}: {text}"
        assert "register-scheduledtask" not in low, f"line {lineno}: {text}"


def _launcher_tripwires(monkeypatch) -> list[str]:
    """Replace every process launcher this module could reach with a tripwire."""
    invoked: list[str] = []

    def _trip(name):
        def _fn(*_a, **_k):
            invoked.append(name)
            raise AssertionError(f"{name} was invoked")
        return _fn

    for attr in sorted(_SUBPROCESS_SPAWNS):
        monkeypatch.setattr(subprocess, attr, _trip(f"subprocess.{attr}"),
                            raising=False)
    for attr in ("system", "popen", "startfile", "execv", "spawnl", "spawnv",
                 "posix_spawn"):
        monkeypatch.setattr(os, attr, _trip(f"os.{attr}"), raising=False)
    return invoked


def test_printing_the_registration_command_invokes_no_launcher(monkeypatch, capsys):
    """BEHAVIOURAL arm, which proves the property the AST arm only reads.

    Every launcher reachable from the module raises if touched, and the
    registration path still completes - so the command is emitted as text, by a
    code path that provably did not run it.
    """
    invoked = _launcher_tripwires(monkeypatch)
    assert responder.main(["--print-register-command"]) == 0
    out = capsys.readouterr().out
    assert "schtasks" in out and "Register-ScheduledTask" in out
    assert invoked == []


def test_a_halted_cycle_invokes_no_launcher(tmp_path, monkeypatch, capsys):
    """The same tripwires over the halted path: HALT stops the spawn itself,
    not merely the bookkeeping around it."""
    inbox = tmp_path / "moon_sync_inbox"
    _fill(inbox, 2)
    halt = tmp_path / "HALT"
    halt.write_text("operator stopped the trial", encoding="utf-8")
    invoked = _launcher_tripwires(monkeypatch)
    assert responder.main(["--once", "--runlog", str(tmp_path / "runs.jsonl"),
                           "--inbox", str(inbox),
                           "--state", str(tmp_path / "seen.json"),
                           "--halt", str(halt)]) == 0
    assert json.loads(capsys.readouterr().out)["halted"]
    assert invoked == []


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

    assert responder.main(["--once", "--runlog", str(tmp_path / "runs.jsonl"),
                    "--inbox", str(inbox), "--state", str(state)]) == 0
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
    responder.main(["--once", "--runlog", str(tmp_path / "runs.jsonl"),
                    "--inbox", str(inbox), "--state", str(state)])
    capsys.readouterr()

    (inbox / "2026-09-10-9999-from-CS-fresh.md").write_text("fresh", encoding="utf-8")
    assert responder.main(["--once", "--runlog", str(tmp_path / "runs.jsonl"),
                    "--inbox", str(inbox), "--state", str(state)]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["new_notes"] == 1
    assert [s["note"] for s in payload["spawned"]] == ["2026-09-10-9999-from-CS-fresh.md"]


def test_a_burst_is_capped_and_the_remainder_is_deferred_not_dropped(tmp_path, capsys, monkeypatch):
    inbox = tmp_path / "moon_sync_inbox"
    _fill(inbox, 1)
    state = tmp_path / "seen.json"
    monkeypatch.setattr(responder, "spawn", lambda *_a, **_k: responder._auto("spawn", "fake"))
    responder.main(["--once", "--runlog", str(tmp_path / "runs.jsonl"),
                    "--inbox", str(inbox), "--state", str(state)])
    capsys.readouterr()

    for i in range(5):
        (inbox / f"2026-09-10-8{i:03d}-from-LL-burst.md").write_text(f"b{i}", encoding="utf-8")
    responder.main(["--once", "--runlog", str(tmp_path / "runs.jsonl"),
                    "--inbox", str(inbox), "--state", str(state)])
    payload = json.loads(capsys.readouterr().out)
    assert len(payload["spawned"]) == responder.MAX_SPAWNS_PER_CYCLE
    assert payload["deferred"] == 5 - responder.MAX_SPAWNS_PER_CYCLE
    assert len(responder.new_notes(inbox, state)) == 5 - responder.MAX_SPAWNS_PER_CYCLE


# --------------------------------------------------------------------------
# The kill switch. Added when the task was ARMED on 2026-09-11 - arming
# something that spawns unattended agents without a mid-flight stop is the gap,
# and disabling the scheduled task is slower than dropping a file.
# --------------------------------------------------------------------------

def test_a_halt_file_stops_a_cycle_before_anything_is_spawned(tmp_path, capsys, monkeypatch):
    inbox = tmp_path / "moon_sync_inbox"
    _fill(inbox, 2)
    state = tmp_path / "seen.json"
    halt = tmp_path / "HALT"
    halt.write_text("operator stopped the trial", encoding="utf-8")
    monkeypatch.setattr(responder, "spawn",
                        lambda *_a, **_k: pytest.fail("HALT did not stop the spawn"))

    rc = responder.main(["--once", "--runlog", str(tmp_path / "runs.jsonl"),
                    "--inbox", str(inbox), "--state", str(state),
                         "--halt", str(halt)])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["halted"] == "operator stopped the trial"
    assert payload["spawned"] == []


def test_an_empty_halt_file_still_halts(tmp_path, capsys):
    """`type nul > HALT` is how an operator makes one under stress, and reading
    that as "no halt" would disarm the switch exactly when it is being used."""
    inbox = tmp_path / "moon_sync_inbox"
    _fill(inbox, 1)
    halt = tmp_path / "HALT"
    halt.write_text("", encoding="utf-8")
    responder.main(["--once", "--runlog", str(tmp_path / "runs.jsonl"),
                    "--inbox", str(inbox), "--state", str(tmp_path / "s.json"),
                    "--halt", str(halt)])
    assert json.loads(capsys.readouterr().out)["halted"]


def test_halt_beats_the_cold_start_baseline_too(tmp_path, capsys):
    """HALT is checked FIRST and answers everything. A kill switch that only
    works on the paths you remembered is not a kill switch."""
    inbox = tmp_path / "moon_sync_inbox"
    _fill(inbox, 3)
    state = tmp_path / "seen.json"
    halt = tmp_path / "HALT"
    halt.write_text("stop", encoding="utf-8")
    responder.main(["--once", "--runlog", str(tmp_path / "runs.jsonl"),
                    "--inbox", str(inbox), "--state", str(state),
                    "--halt", str(halt)])
    assert json.loads(capsys.readouterr().out)["halted"]
    assert not state.exists(), "a halted cycle still wrote the baseline"


def test_without_a_halt_file_the_cycle_runs(tmp_path, capsys, monkeypatch):
    """MIRROR. A switch stuck ON stops everything and would pass the arms above."""
    inbox = tmp_path / "moon_sync_inbox"
    _fill(inbox, 1)
    state = tmp_path / "seen.json"
    responder.main(["--once", "--runlog", str(tmp_path / "runs.jsonl"),
                    "--inbox", str(inbox), "--state", str(state),
                    "--halt", str(tmp_path / "absent-HALT")])
    payload = json.loads(capsys.readouterr().out)
    assert "halted" not in payload
    assert payload["cold_start"] is True

    monkeypatch.setattr(responder, "spawn", lambda *_a, **_k: responder._auto("spawn", "fake"))
    (inbox / "2026-09-11-0001-from-RC-new.md").write_text("new", encoding="utf-8")
    responder.main(["--once", "--runlog", str(tmp_path / "runs.jsonl"),
                    "--inbox", str(inbox), "--state", str(state),
                    "--halt", str(tmp_path / "absent-HALT")])
    assert len(json.loads(capsys.readouterr().out)["spawned"]) == 1


def test_the_default_halt_path_is_under_runtime_state():
    assert REAL_HALT_PATH.name == "HALT"
    assert REAL_HALT_PATH.parent.parent.name == "runtime"


# --------------------------------------------------------------------------
# THE OVERRIDE MAY ADD A GATE AND MAY NEVER REMOVE ONE.
#
# DEFECT MEASURED 2026-09-20. `--halt` took `HALT_PATH` as its argparse
# DEFAULT, so `--halt <a path that does not exist>` did not add a second switch
# - it REPLACED the only one. A probe run with that argument proceeded while the
# operator's HALT file sat untouched on disk; the control run with no argument
# halted. So the published claim - this responder cannot run while HALT exists -
# held only for a caller that did not pass the flag, which is the one caller a
# kill switch does not have to defend against. LW told the whole channel its
# refusal to pair rested on that gate, and a posture is only as strong as it.
# --------------------------------------------------------------------------

def test_no_command_line_argument_can_run_a_cycle_while_the_default_halt_exists(
        tmp_path, capsys, monkeypatch):
    """THE DEFECT, pinned. State is pre-seeded so the cold-start branch cannot
    absorb the bypass: without the fix this reaches `spawn`."""
    default_halt = tmp_path / "default" / "HALT"
    default_halt.parent.mkdir(parents=True)
    default_halt.write_text("operator stopped the trial", encoding="utf-8")
    monkeypatch.setattr(responder, "HALT_PATH", default_halt)

    inbox = tmp_path / "moon_sync_inbox"
    _fill(inbox, 2)
    state = tmp_path / "seen.json"
    state.write_text(json.dumps({"seen": []}), encoding="utf-8")
    monkeypatch.setattr(responder, "spawn", lambda *_a, **_k: pytest.fail(
        "an argument relocated the kill switch and the cycle spawned"))

    rc = responder.main(["--once", "--runlog", str(tmp_path / "runs.jsonl"),
                         "--inbox", str(inbox), "--state", str(state),
                         "--halt", str(tmp_path / "absent-HALT")])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["halted"] == "operator stopped the trial"
    assert payload["spawned"] == []


def test_the_default_kill_switch_is_consulted_with_no_override_and_with_one(
        tmp_path, monkeypatch):
    """The seam is the MODULE attribute, which no command line can reach."""
    default_halt = tmp_path / "HALT"
    default_halt.write_text("operator stopped the trial", encoding="utf-8")
    monkeypatch.setattr(responder, "HALT_PATH", default_halt)
    assert responder.halt_reason() == "operator stopped the trial"
    assert responder.halt_reason(tmp_path / "absent") == "operator stopped the trial"


def test_an_override_can_still_add_a_second_gate(tmp_path, monkeypatch):
    """MIRROR. Add-only must still ADD: an override with the default absent is
    the shape every other arm in this section runs on."""
    monkeypatch.setattr(responder, "HALT_PATH", tmp_path / "absent-HALT")
    extra = tmp_path / "extra-HALT"
    extra.write_text("second gate", encoding="utf-8")
    assert responder.halt_reason(extra) == "second gate"
    assert responder.halt_reason(tmp_path / "also-absent") is None


def test_no_argparse_option_defaults_to_the_kill_switch_path():
    """The mechanism of the defect, not only its effect: an option whose default
    IS the switch is an option that replaces it."""
    parser = responder.build_parser()
    defaults = {a.dest: a.default for a in parser._actions}
    assert "halt" in defaults, "the flag is gone - update this arm deliberately"
    assert defaults["halt"] is None, (
        f"--halt defaults to {defaults['halt']!r}; a default of the real switch "
        "is what made an override a replacement")


def _cli(args: list[str], *, halt_path: Path) -> subprocess.CompletedProcess:
    """Drive the CLI in a child process with the DEFAULT switch INJECTED.

    The injection is a module attribute set before `main()` is reached, never an
    argument - which is the whole point of the fix. Before it, this helper
    passed `--halt` and so tested the bypass; a subprocess arm that inherited
    the real default instead would make the suite's colour depend on whether
    the operator currently has the lane disarmed (measured 2026-09-11, four arms
    red for exactly that reason).
    """
    driver = (
        "import sys\n"
        f"sys.path.insert(0, {str(ROOT / 'tools')!r})\n"
        "from pathlib import Path\n"
        "import lw_inbox_responder as r\n"
        f"r.HALT_PATH = Path({str(halt_path)!r})\n"
        "raise SystemExit(r.main(sys.argv[1:]))\n"
    )
    return subprocess.run([sys.executable, "-c", driver, *args],
                          capture_output=True, text=True, cwd=str(ROOT),
                          creationflags=responder.NO_WINDOW)


def test_cli_once_dry_run_reports_json_and_changes_no_state(tmp_path):
    inbox = tmp_path / "moon_sync_inbox"
    inbox.mkdir()
    (inbox / "2026-09-10-0001-from-RC-x.md").write_text("hello", encoding="utf-8")
    state = tmp_path / "seen.json"
    proc = _cli(["--once", "--dry-run", "--inbox", str(inbox), "--state", str(state)],
                halt_path=tmp_path / "never-created-HALT")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["dry_run"] is True
    assert payload["spawned"] == []
    assert not state.exists(), "a dry run recorded state"


def test_cli_once_halts_when_the_default_switch_exists_and_an_override_is_absent(tmp_path):
    """END TO END over a real command line, which is where the defect lived.
    `--halt` naming a path that does not exist must not answer for the default."""
    inbox = tmp_path / "moon_sync_inbox"
    _fill(inbox, 1)
    default_halt = tmp_path / "default" / "HALT"
    default_halt.parent.mkdir(parents=True)
    default_halt.write_text("operator stopped the trial", encoding="utf-8")
    state = tmp_path / "seen.json"
    proc = _cli(["--once", "--dry-run", "--inbox", str(inbox), "--state", str(state),
                 "--halt", str(tmp_path / "absent-HALT")],
                halt_path=default_halt)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert json.loads(proc.stdout)["halted"] == "operator stopped the trial"
    assert not state.exists()
