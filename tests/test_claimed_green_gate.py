"""Characterization tests for the Stop-hook claimed-green gate (P1).

The gate answers one question at the moment Claude says it is done: was a
"tests pass" claim backed by a run that actually happened in this session?

Contract under test, from the official hook docs (docs/MCP_LIFT_DIVE_2026-08-01
section 3, Item B):
  - input arrives as JSON on stdin with `stop_hook_active`,
    `last_assistant_message` and `transcript_path`
  - a finding is exit 0 with ONE line of {"hookSpecificOutput": {"hookEventName":
    "Stop", "additionalContext": <one line>}} - shown as "Stop hook feedback",
    not a "Stop hook error" dump (MAIN ORDER 2026-10-07 2237); the full reason
    goes to a report file the line names
  - `stop_hook_active` is COOPERATIVE - the harness does not cap the loop, so an
    always-block hook wedges the session forever. This is the single most
    important test in the file.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

GATE = Path(__file__).resolve().parents[1] / "tools" / "claimed_green_gate.py"
REPORT_ENV = "LW_CLAIMED_GREEN_REPORT_DIR"


@pytest.fixture(autouse=True)
def report_dir(monkeypatch):
    """Every fired gate writes its report here, never into the live ops/runtime.

    mkdtemp, not tmp_path: the feedback line carries the full report path and
    must stay <= 160 chars, and pytest's tmp_path alone can approach that.
    """
    path = Path(tempfile.mkdtemp(prefix="cgg"))
    monkeypatch.setenv(REPORT_ENV, str(path))
    yield path
    shutil.rmtree(path, ignore_errors=True)


def _line(**kw) -> str:
    return json.dumps(kw)


def _assistant_bash(command: str, stdout: str = "", code: int = 0) -> str:
    """One assistant turn issuing a Bash tool call, as Claude Code records it."""
    return _line(
        type="assistant",
        message={
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "name": "Bash",
                    "input": {"command": command},
                }
            ],
        },
        toolUseResult={"stdout": stdout, "code": code},
    )


def _paired_bash(
    command: str,
    stdout: str = "",
    tool_id: str = "toolu_01",
    interrupted: str = "False",
) -> list:
    """The REAL Claude Code shape, measured against a live 1.4 MB transcript.

    The result does NOT sit on the assistant entry - it arrives on a LATER user
    entry, joined by `tool_use_id`, with the payload at entry-level
    `toolUseResult`. Bash results carry NO `code` field at all: just stdout,
    stderr and `interrupted`, and `interrupted` is the STRING "False", not a
    bool. Synthetic same-entry fixtures hid all three of these.
    """
    return [
        _line(
            type="assistant",
            message={
                "role": "assistant",
                "content": [
                    {
                        "type": "tool_use",
                        "id": tool_id,
                        "name": "Bash",
                        "input": {"command": command},
                    }
                ],
            },
        ),
        _line(
            type="user",
            message={
                "role": "user",
                "content": [{"type": "tool_result", "tool_use_id": tool_id}],
            },
            toolUseResult={
                "stdout": stdout,
                "stderr": "",
                "interrupted": interrupted,
                "isImage": False,
            },
        ),
    ]


def _user_text(text: str) -> str:
    return _line(type="user", message={"role": "user", "content": text})


def _transcript(tmp_path: Path, *lines: str) -> Path:
    path = tmp_path / "transcript.jsonl"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def run_gate(payload: dict) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(GATE)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
    )


def decision_of(proc: subprocess.CompletedProcess) -> dict:
    """{} when clean; else {"decision": "block", "reason", "line", "report"}.

    Every fired path is held to the feedback shape here, so each existing block
    test also proves it: one stdout line, exit 0, no stderr, no top-level
    decision/reason, and a report file that carries the full reason.
    """
    if not proc.stdout.strip():
        return {}
    assert proc.returncode == 0
    assert proc.stderr == ""
    lines = proc.stdout.strip().splitlines()
    assert len(lines) == 1, proc.stdout
    out = json.loads(lines[0])
    assert set(out) == {"hookSpecificOutput"}, out
    spec = out["hookSpecificOutput"]
    assert spec["hookEventName"] == "Stop"
    line = spec["additionalContext"]
    assert "\n" not in line and len(line) <= 160, line
    assert line.startswith("claimed_green_gate: ")
    report = Path(os.environ[REPORT_ENV]) / "last_finding.txt"
    assert str(report) in line, line
    reason = report.read_text(encoding="ascii")
    return {"decision": "block", "reason": line + "\n" + reason,
            "line": line, "report": reason}


PASSING = "1537 passed, 16 skipped in 42.10s"
FAILING = "1 failed, 1536 passed in 41.88s"


# --- the loop guard: this is the one that must never regress ----------------


def test_stop_hook_active_always_allows(tmp_path):
    """An always-block Stop hook loops forever. stop_hook_active breaks it."""
    transcript = _transcript(tmp_path, _user_text("go"))
    proc = run_gate(
        {
            "hook_event_name": "Stop",
            "stop_hook_active": True,
            "last_assistant_message": "All tests pass, suite is green.",
            "transcript_path": str(transcript),
        }
    )
    assert proc.returncode == 0
    assert decision_of(proc) == {}


# --- claim detection --------------------------------------------------------


def test_no_claim_allows(tmp_path):
    transcript = _transcript(tmp_path, _user_text("go"))
    proc = run_gate(
        {
            "stop_hook_active": False,
            "last_assistant_message": "Wrote the docs. Nothing else to report.",
            "transcript_path": str(transcript),
        }
    )
    assert proc.returncode == 0
    assert decision_of(proc) == {}


@pytest.mark.parametrize(
    "claim",
    [
        "All tests pass.",
        "Suite is green.",
        "1537 passed, 16 skipped.",
        "CI is green on that commit.",
        "The full suite passes now.",
    ],
)
def test_green_claims_are_recognized(tmp_path, claim):
    transcript = _transcript(tmp_path, _user_text("go"))
    proc = run_gate(
        {
            "stop_hook_active": False,
            "last_assistant_message": claim,
            "transcript_path": str(transcript),
        }
    )
    assert decision_of(proc).get("decision") == "block", claim


# A green phrase governed by a conditional in the SAME clause is a plan, not a
# claim. Live false positive 2026-10-07: a checklist line "Merge Dependabot PR
# #1 once its CI is green" blocked a Stop. The sibling patterns (tests pass,
# suite green, all green, green on <sha>) share the same root cause.
@pytest.mark.parametrize(
    "text",
    [
        "Merge Dependabot PR #1 once its CI is green",
        "Merge it when CI is green.",
        "Hold the push until CI is green.",
        "Tag the release after CI is green.",
        "Merge only if CI is green.",
        "Next: wait for CI green, then merge.",
        "Ship it once the tests pass.",
        "Restart when the full suite is green.",
        "Close the lane once all green.",
        "Deploy when it is green on 58ff889.",
    ],
)
def test_conditional_green_phrasing_is_not_a_claim(tmp_path, text):
    transcript = _transcript(tmp_path, _user_text("go"))
    proc = run_gate(
        {
            "stop_hook_active": False,
            "last_assistant_message": text,
            "transcript_path": str(transcript),
        }
    )
    assert decision_of(proc) == {}, text


@pytest.mark.parametrize(
    "text",
    [
        "CI is green.",
        "CI green on abc1234.",
        "CI is green; merge PR #1 once Dependabot rebases.",
        "Merge PR #1 once its CI is green. CI is green on abc1234.",
        "After the push, CI is green.",
        "Once more: all tests pass.",
    ],
)
def test_real_claim_beside_a_conditional_still_blocks(tmp_path, text):
    transcript = _transcript(tmp_path, _user_text("go"))
    proc = run_gate(
        {
            "stop_hook_active": False,
            "last_assistant_message": text,
            "transcript_path": str(transcript),
        }
    )
    assert decision_of(proc).get("decision") == "block", text


# --- detector: claim-no-run -------------------------------------------------


def test_claim_with_no_run_blocks(tmp_path):
    transcript = _transcript(
        tmp_path,
        _user_text("fix it"),
        _assistant_bash("git status --short"),
    )
    proc = run_gate(
        {
            "stop_hook_active": False,
            "last_assistant_message": "Done - all tests pass.",
            "transcript_path": str(transcript),
        }
    )
    assert proc.returncode == 0
    decision = decision_of(proc)
    assert decision["decision"] == "block"
    assert "claim-no-run" in decision["reason"]


def test_fired_gate_is_one_feedback_line_and_the_report_holds_the_reason(
        tmp_path, report_dir):
    """MAIN ORDER 2026-10-07 2237: the pane gets one feedback line, not a dump."""
    transcript = _transcript(tmp_path, _user_text("fix it"))
    proc = run_gate({"stop_hook_active": False,
                     "last_assistant_message": "Done - all tests pass.",
                     "transcript_path": str(transcript)})
    decision = decision_of(proc)
    report = report_dir / "last_finding.txt"
    assert decision["line"] == f"claimed_green_gate: claim-no-run x1 - read {report}"
    # the full reason is in the report, and ONLY there
    assert "python -m pytest -q" in decision["report"]
    assert "python -m pytest -q" not in decision["line"]
    assert '"decision"' not in proc.stdout and '"reason"' not in proc.stdout


def test_clean_path_prints_nothing_and_writes_no_report(tmp_path, report_dir):
    transcript = _transcript(tmp_path, _user_text("go"))
    proc = run_gate({"stop_hook_active": False,
                     "last_assistant_message": "Wrote the docs.",
                     "transcript_path": str(transcript)})
    assert (proc.returncode, proc.stdout, proc.stderr) == (0, "", "")
    assert not (report_dir / "last_finding.txt").exists()


def test_claim_with_passing_run_allows(tmp_path):
    transcript = _transcript(
        tmp_path,
        _user_text("fix it"),
        _assistant_bash("python -m pytest -q", stdout=PASSING, code=0),
    )
    proc = run_gate(
        {
            "stop_hook_active": False,
            "last_assistant_message": "Done - 1537 passed, 16 skipped.",
            "transcript_path": str(transcript),
        }
    )
    assert decision_of(proc) == {}


def test_run_in_a_subagent_counts(tmp_path):
    """A suite run by a subagent is still a run - do not accuse on sidechains."""
    transcript = _transcript(
        tmp_path,
        _line(
            type="assistant",
            isSidechain=True,
            message={
                "role": "assistant",
                "content": [
                    {
                        "type": "tool_use",
                        "name": "Bash",
                        "input": {"command": "pytest tests/ -q"},
                    }
                ],
            },
            toolUseResult={"stdout": PASSING, "code": 0},
        ),
    )
    proc = run_gate(
        {
            "stop_hook_active": False,
            "last_assistant_message": "Suite is green.",
            "transcript_path": str(transcript),
        }
    )
    assert decision_of(proc) == {}


# --- GATE-SUBAGENT-FP (LEDGER 289): subagent runs live in SEPARATE files ------
# Measured on disk 2026-10-10: the main transcript is <project>/<sid>.jsonl and
# each subagent writes <project>/<sid>/subagents/agent-<id>.jsonl, every line
# isSidechain=true. The main file carries none of the subagent's tool calls, so
# a gate that reads only transcript_path cannot see a subagent's pytest run.


def _session(tmp_path: Path, main_lines, subagents: dict) -> Path:
    sid = "0f0f0f0f-1111-2222-3333-444444444444"
    main = tmp_path / f"{sid}.jsonl"
    main.write_text("\n".join(main_lines) + "\n", encoding="utf-8")
    sub_dir = tmp_path / sid / "subagents"
    sub_dir.mkdir(parents=True)
    for agent_id, lines in subagents.items():
        (sub_dir / f"agent-{agent_id}.jsonl").write_text(
            "\n".join(lines) + "\n", encoding="utf-8")
        (sub_dir / f"agent-{agent_id}.meta.json").write_text(
            '{"agentType": "general-purpose"}', encoding="utf-8")
    return main


def _sidechain_bash(command: str, stdout: str, tool_id: str, ts: str,
                    is_error: bool = False) -> list:
    """The measured subagent shape: no entry-level toolUseResult, output on
    the tool_result part as `content` with `is_error`."""
    return [
        _line(type="assistant", isSidechain=True, timestamp=ts,
              message={"role": "assistant", "content": [
                  {"type": "tool_use", "id": tool_id, "name": "Bash",
                   "input": {"command": command}}]}),
        _line(type="user", isSidechain=True, timestamp=ts,
              message={"role": "user", "content": [
                  {"type": "tool_result", "tool_use_id": tool_id,
                   "content": stdout, "is_error": is_error}]}),
    ]


def test_run_only_in_a_subagent_file_counts(tmp_path):
    """The session-68 false positive: only a subagent ran the suite."""
    main = _session(
        tmp_path,
        [_user_text("fix it"), _assistant_bash("git status --short")],
        {"a1b2c3": _sidechain_bash("python -m pytest -q", PASSING,
                                   "toolu_s1", "2026-10-10T10:00:00.000Z")},
    )
    proc = run_gate({"stop_hook_active": False,
                     "last_assistant_message": "Done - 1537 passed, 16 skipped.",
                     "transcript_path": str(main)})
    assert decision_of(proc) == {}


def test_red_run_only_in_a_subagent_file_still_blocks(tmp_path):
    """Seeing subagent runs must not blind the gate: a red one is still red."""
    main = _session(
        tmp_path,
        [_user_text("fix it")],
        {"a1b2c3": _sidechain_bash("python -m pytest -q", FAILING, "toolu_s1",
                                   "2026-10-10T10:00:00.000Z", is_error=True)},
    )
    proc = run_gate({"stop_hook_active": False,
                     "last_assistant_message": "All tests pass now.",
                     "transcript_path": str(main)})
    assert "claim-vs-fail" in decision_of(proc)["reason"]


def test_main_and_subagent_runs_are_ordered_by_timestamp(tmp_path):
    """A main-thread red run AFTER a subagent's green one is the last word."""
    red = _paired_bash("python -m pytest -q", stdout=FAILING, tool_id="toolu_m1")
    red = [json.dumps(dict(json.loads(x), timestamp="2026-10-10T11:00:00.000Z"))
           for x in red]
    main = _session(
        tmp_path,
        [_user_text("fix it"), *red],
        {"a1b2c3": _sidechain_bash("python -m pytest -q", PASSING, "toolu_s1",
                                   "2026-10-10T10:00:00.000Z")},
    )
    proc = run_gate({"stop_hook_active": False,
                     "last_assistant_message": "All tests pass now.",
                     "transcript_path": str(main)})
    assert "claim-vs-fail" in decision_of(proc)["reason"]


def test_no_run_anywhere_still_blocks_with_a_subagents_dir(tmp_path):
    main = _session(
        tmp_path,
        [_user_text("fix it")],
        {"a1b2c3": _sidechain_bash("git log -1", "abc", "toolu_s1",
                                   "2026-10-10T10:00:00.000Z")},
    )
    proc = run_gate({"stop_hook_active": False,
                     "last_assistant_message": "Done - all tests pass.",
                     "transcript_path": str(main)})
    assert "claim-no-run" in decision_of(proc)["reason"]


# --- detector: claim-vs-fail ------------------------------------------------


def test_claim_after_failing_run_blocks(tmp_path):
    transcript = _transcript(
        tmp_path,
        _assistant_bash("python -m pytest -q", stdout=FAILING, code=1),
    )
    proc = run_gate(
        {
            "stop_hook_active": False,
            "last_assistant_message": "All tests pass now.",
            "transcript_path": str(transcript),
        }
    )
    decision = decision_of(proc)
    assert decision["decision"] == "block"
    assert "claim-vs-fail" in decision["reason"]


def test_failing_then_passing_run_allows(tmp_path):
    """The LAST run is what the claim is about - a red-then-green fix is normal."""
    transcript = _transcript(
        tmp_path,
        _assistant_bash("python -m pytest -q", stdout=FAILING, code=1),
        _assistant_bash("python -m pytest -q", stdout=PASSING, code=0),
    )
    proc = run_gate(
        {
            "stop_hook_active": False,
            "last_assistant_message": "All tests pass now.",
            "transcript_path": str(transcript),
        }
    )
    assert decision_of(proc) == {}


def test_interrupted_run_is_not_a_failure(tmp_path):
    """Exit 124/137/143 is an interrupted run, not a red suite - do not accuse."""
    transcript = _transcript(
        tmp_path,
        _assistant_bash("python -m pytest -q", stdout="", code=143),
        _assistant_bash("python -m pytest -q", stdout=PASSING, code=0),
    )
    proc = run_gate(
        {
            "stop_hook_active": False,
            "last_assistant_message": "Suite green.",
            "transcript_path": str(transcript),
        }
    )
    assert decision_of(proc) == {}


# --- detector: no-verify ----------------------------------------------------


def test_commit_after_hook_rejection_blocks(tmp_path):
    transcript = _transcript(
        tmp_path,
        _assistant_bash(
            "git commit -m x",
            stdout="precommit_gate BLOCKED commit - net-new violations",
            code=1,
        ),
        _assistant_bash("git commit --no-verify -m x", stdout="[main abc123]", code=0),
    )
    proc = run_gate(
        {
            "stop_hook_active": False,
            "last_assistant_message": "Committed and pushed.",
            "transcript_path": str(transcript),
        }
    )
    decision = decision_of(proc)
    assert decision["decision"] == "block"
    assert "no-verify" in decision["reason"]


def test_no_verify_without_a_prior_rejection_is_not_blocked(tmp_path):
    """No hook rejection before it - suspicious at most, and not this gate's call."""
    transcript = _transcript(
        tmp_path,
        _assistant_bash("git commit --no-verify -m x", stdout="[main abc123]", code=0),
    )
    proc = run_gate(
        {
            "stop_hook_active": False,
            "last_assistant_message": "Committed.",
            "transcript_path": str(transcript),
        }
    )
    assert decision_of(proc) == {}


def test_git_push_dash_n_is_not_a_commit_bypass(tmp_path):
    """`git push -n` is a dry run. Segment the command, do not substring-match."""
    transcript = _transcript(
        tmp_path,
        _assistant_bash("git commit -m x", stdout="pre-commit hook failed", code=1),
        _assistant_bash("git push -n origin main", stdout="", code=0),
    )
    proc = run_gate(
        {
            "stop_hook_active": False,
            "last_assistant_message": "Pushed.",
            "transcript_path": str(transcript),
        }
    )
    assert decision_of(proc) == {}


@pytest.mark.parametrize("command", [
    # The live false positive, 2026-10-03: `grep -n` in the SAME chain as a
    # file-scoped commit read as `git commit -n`.
    'git commit -q -F m.txt -- LW-NEXT-SESSION.txt && grep -n "X" LW-NEXT-SESSION.txt',
    'grep -n "X" f && git commit -q -F m.txt -- f',
    'git commit -m x; sed -n 1,5p f',
    'git commit -m x | head -n 3',
    'python w.py\ngrep -n x f && git commit -m y',
])
def test_a_dash_n_owned_by_another_command_is_not_a_bypass(tmp_path, command):
    transcript = _transcript(
        tmp_path,
        _assistant_bash("git commit -m x", stdout="pre-commit hook failed", code=1),
        _assistant_bash(command, stdout="[main abc123]", code=0),
    )
    proc = run_gate({"stop_hook_active": False, "last_assistant_message": "Committed.",
                     "transcript_path": str(transcript)})
    assert decision_of(proc) == {}


@pytest.mark.parametrize("command", [
    "git add f && git commit -n -m x",
    "git commit --no-verify -m x && git push",
    "grep -n x f; git commit -n -m y",
    "git -C /repo commit -n -m x",
    "git -c core.hooksPath=x commit --no-verify -m x",
])
def test_a_real_bypass_inside_a_chain_still_blocks(tmp_path, command):
    transcript = _transcript(
        tmp_path,
        _assistant_bash("git commit -m x", stdout="pre-commit hook failed", code=1),
        _assistant_bash(command, stdout="[main abc123]", code=0),
    )
    proc = run_gate({"stop_hook_active": False, "last_assistant_message": "Committed.",
                     "transcript_path": str(transcript)})
    assert decision_of(proc).get("decision") == "block"


# --- never wedge the session ------------------------------------------------


@pytest.mark.parametrize("payload", [{}, {"transcript_path": "nope.jsonl"}])
def test_unreadable_input_allows(payload):
    proc = run_gate(payload)
    assert proc.returncode == 0
    assert decision_of(proc) == {}


def test_corrupt_transcript_lines_are_skipped(tmp_path):
    path = tmp_path / "transcript.jsonl"
    path.write_text(
        "not json at all\n"
        + _assistant_bash("python -m pytest -q", stdout=PASSING, code=0)
        + "\n{\n",
        encoding="utf-8",
    )
    proc = run_gate(
        {
            "stop_hook_active": False,
            "last_assistant_message": "Tests pass.",
            "transcript_path": str(path),
        }
    )
    assert proc.returncode == 0
    assert decision_of(proc) == {}


def test_operator_waiver_allows(tmp_path):
    """If the operator said not to run them, a green claim is not an accusation."""
    transcript = _transcript(tmp_path, _user_text("skip the tests, just commit it"))
    proc = run_gate(
        {
            "stop_hook_active": False,
            "last_assistant_message": "Committed. Tests pass as of the last run.",
            "transcript_path": str(transcript),
        }
    )
    assert decision_of(proc) == {}


# --- the REAL transcript shape ---------------------------------------------
# These are the regression tests for the bug the synthetic fixtures above hid:
# a live probe found 46 commands and 2 pytest runs, and classified BOTH as
# "unknown" because the result never joined back to the call.


def test_real_shape_passing_run_allows(tmp_path):
    transcript = _transcript(
        tmp_path, *_paired_bash("python -m pytest -q", stdout=PASSING)
    )
    proc = run_gate(
        {
            "stop_hook_active": False,
            "last_assistant_message": "Done - 1537 passed, 16 skipped.",
            "transcript_path": str(transcript),
        }
    )
    assert decision_of(proc) == {}, "the run is right there in the transcript"


def test_real_shape_failing_run_blocks(tmp_path):
    transcript = _transcript(
        tmp_path, *_paired_bash("python -m pytest -q", stdout=FAILING)
    )
    proc = run_gate(
        {
            "stop_hook_active": False,
            "last_assistant_message": "All tests pass.",
            "transcript_path": str(transcript),
        }
    )
    assert decision_of(proc)["decision"] == "block"
    assert "claim-vs-fail" in decision_of(proc)["reason"]


def test_real_shape_interrupted_string_is_not_a_failure(tmp_path):
    """`interrupted` arrives as the STRING "True" - truthiness alone is a trap."""
    lines = _paired_bash("python -m pytest -q", stdout="", tool_id="a", interrupted="True")
    lines += _paired_bash("python -m pytest -q", stdout=PASSING, tool_id="b")
    transcript = _transcript(tmp_path, *lines)
    proc = run_gate(
        {
            "stop_hook_active": False,
            "last_assistant_message": "Suite green.",
            "transcript_path": str(transcript),
        }
    )
    assert decision_of(proc) == {}


def test_real_shape_no_code_field_and_no_output_is_unknown_not_pass(tmp_path):
    """No code, no counts - that is not evidence of green, so the claim is bare."""
    transcript = _transcript(
        tmp_path, *_paired_bash("python -m pytest -q", stdout="")
    )
    proc = run_gate(
        {
            "stop_hook_active": False,
            "last_assistant_message": "All tests pass.",
            "transcript_path": str(transcript),
        }
    )
    decision = decision_of(proc)
    assert decision.get("decision") == "block"
    assert "no-counts" in decision["reason"]


def test_real_shape_no_verify_after_rejection_blocks(tmp_path):
    lines = _paired_bash(
        "git commit -m x",
        stdout="precommit_gate BLOCKED commit - net-new violations",
        tool_id="a",
    )
    lines += _paired_bash("git commit --no-verify -m x", stdout="[main abc]", tool_id="b")
    transcript = _transcript(tmp_path, *lines)
    proc = run_gate(
        {
            "stop_hook_active": False,
            "last_assistant_message": "Committed.",
            "transcript_path": str(transcript),
        }
    )
    assert "no-verify" in decision_of(proc)["reason"]


def test_block_reason_is_ascii_and_actionable(tmp_path):
    transcript = _transcript(tmp_path, _user_text("go"))
    proc = run_gate(
        {
            "stop_hook_active": False,
            "last_assistant_message": "All tests pass.",
            "transcript_path": str(transcript),
        }
    )
    reason = decision_of(proc)["reason"]
    reason.encode("ascii")
    assert "pytest" in reason
