"""Every headless `claude` spawn this tree makes carries the KIT's lean flags.

MAIN 0912 (2026-10-03) measured setup, not work, as most of a headless call's
input. Since fleet kit v3 the flag set is the kit's own (`build_argv`, non-bare:
`--strict-mcp-config --setting-sources project,local`), read off the kit by
`lw_headless_env.LEAN_ARGS`, so it exists ONCE, in the kit. `--bare` is NOT
used anywhere: it skips every hook, and LW's floors live in hooks (PreToolUse
precommit_gate, text_first_guard).

SETTING SOURCES (kit v3 gap 4, closed by kit v4 `setting_sources=`): LW
measured `project` alone at 47,026 input tokens against 53,143 for
`project,local`, and in this tree the local scope re-enables three plugins and
pins the `rc-main` model alias the proxy answers with 404. Every LW path runs
`project` alone (`lw_headless_env.SETTING_SOURCES`) and still passes an
explicit --model, so no alias ever decides a run.

Model on the responder is the kit's (`pick_model(writes_code)`); effort is the
kit's `pick_effort(note)` on a reply-only run and `medium` on a code-writing run
(kit v3 gap 6, closed by kit v4 `effort=`; high until MAIN REPO-REVIEW perf 2.3). LW maps the KIND token to
writes_code.
"""
from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import lw_headless_env  # noqa: E402
import lw_inbox_responder as responder  # noqa: E402


def _load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


executor = _load("lw_executor_lean_under_test", "ops/loop/executor.py")
lc = _load("lw_loop_controller_lean_under_test", "ops/loop/loop_controller.py")
cw = _load("lw_ci_watchdog_lean_under_test", "tools/ci_watchdog.py")

_URL = "http://127.0.0.1:4999/x"


class _Conn:
    def close(self):
        pass


def _seams(seen: dict) -> dict:
    def run(argv, **kw):
        seen["argv"], seen["kw"] = argv, kw

        class _R:
            returncode = 0
            stdout = json.dumps({"result": "ok", "usage": {"input_tokens": 1}})
            stderr = ""
        return _R()

    return {"url_source": lambda: _URL, "connect": lambda *a, **k: _Conn(),
            "run": run, "exe_source": lambda: "claude.exe"}


def _carries_lean(argv: list) -> bool:
    lean = list(lw_headless_env.LEAN_ARGS)
    return any(argv[i:i + len(lean)] == lean for i in range(len(argv)))


_LIVE_HALT = responder.HALT_PATH


@pytest.fixture(autouse=True)
def _no_live_halt(monkeypatch, tmp_path):
    """RRF-T1 (REPO-REVIEW 2026-10-09): `responder.spawn` hands HALT_PATH to the
    kit as `halt_file`, read at call time. Pointed at the LIVE
    ops/runtime/inbox_responder/HALT, six tests here went red whenever the
    operator's kill switch was set. Point it at an absent tmp path instead."""
    monkeypatch.setattr(responder, "HALT_PATH", tmp_path / "inbox_responder" / "HALT")


def test_a_live_halt_never_reaches_these_tests(tmp_path):
    assert responder.HALT_PATH != _LIVE_HALT
    assert tmp_path in responder.HALT_PATH.parents
    assert not responder.HALT_PATH.exists()


def test_the_lean_set_is_the_kits_and_never_bare():
    lean = list(lw_headless_env.LEAN_ARGS)
    assert "--strict-mcp-config" in lean
    assert "--bare" not in lean


def test_the_lean_set_drops_the_local_scope():
    lean = list(lw_headless_env.LEAN_ARGS)
    assert lean[lean.index("--setting-sources") + 1] == "project"


# --------------------------------------------------------------------------
# The spawn paths
# --------------------------------------------------------------------------

def test_the_responder_spawn_is_lean_and_never_bare():
    seen = {}
    responder.spawn(Path("moon_sync_inbox/2026-10-03-from-RC-REVIEW-x.md"),
                    kit_seams=_seams(seen))
    assert _carries_lean(seen["argv"])
    assert "--bare" not in seen["argv"]
    assert seen["argv"][seen["argv"].index("--permission-mode") + 1] == "bypassPermissions"


def test_the_loop_executor_spawn_is_lean():
    ex = executor.SdkExecutor({"claude_cmd": "claude", "repo_root": "."}, None,
                              log=print, stop=None, awrite=None)
    assert _carries_lean(ex.build_argv(1))


def test_the_loop_executor_passes_only_the_mcp_config_it_is_given():
    """--strict-mcp-config with no --mcp-config means NO servers."""
    bare = executor.SdkExecutor({"claude_cmd": "claude"}, None,
                                log=print, stop=None, awrite=None).build_argv(1)
    assert "--mcp-config" not in bare
    named = executor.SdkExecutor({"claude_cmd": "claude", "executor_mcp_config": "m.json"},
                                 None, log=print, stop=None, awrite=None).build_argv(1)
    assert named[named.index("--mcp-config") + 1] == "m.json"


def test_the_oracle_spawn_is_lean_and_keeps_no_transcript(monkeypatch):
    import functools
    seen = {}
    monkeypatch.setattr(lc.headless_env, "spawn",
                        functools.partial(lc.headless_env.spawn, **_seams(seen)))
    monkeypatch.setattr(lc, "CFG", {})
    lc.claude_oracle("body", "Audit.")
    argv = seen["argv"]
    assert _carries_lean(argv)
    assert "--no-session-persistence" in argv


def test_the_ci_watchdog_spawn_is_the_kits_argv(monkeypatch, tmp_path):
    seen = {}
    cw._fix_in_worktree(tmp_path, "a" * 40, "1", None, 60, kit_seams=_seams(seen))
    argv = seen["argv"]
    assert _carries_lean(argv)
    assert argv[argv.index("--output-format") + 1] == "json"
    assert argv[argv.index("--model") + 1] == lw_headless_env.kit.pick_model(True)
    assert argv[argv.index("--add-dir") + 1] == str(tmp_path)
    assert lw_headless_env.budget().used() == 1, "the run is counted in the kit's budget"


# Each site that builds a claude argv ITSELF (a `-p` literal beside a claude
# name) must take the flags from the kit. Sites that call kit.spawn or the
# kit's build_argv carry them by construction.
_PRINT_FLAG = re.compile(r"""["']-p["']""")
_CLAUDE = re.compile(r"""["']claude(?:\.cmd)?["']""", re.IGNORECASE)


def test_every_hand_built_claude_argv_in_the_tree_uses_the_kits_lean_set():
    sites = []
    for base in ("tools", "ops"):
        for path in sorted((ROOT / base).rglob("*.py")):
            rel = path.relative_to(ROOT).as_posix()
            if rel.startswith(("tools/dwpose_onnx/", "ops/runtime/", "ops/fleet_kit/")):
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            if _PRINT_FLAG.search(text) and _CLAUDE.search(text):
                sites.append((rel, "LEAN_ARGS" in text or "build_argv(" in text))
    print("hand-built sites:", sites)
    # The loop executor today (the oracle moved onto kit.spawn with kit v4).
    # Fewer means the instrument went blind.
    assert len(sites) >= 1, sites
    assert all(lean for _rel, lean in sites), sites


# --------------------------------------------------------------------------
# Responder routing: the KIND token picks writes_code; the kit picks the rest
# --------------------------------------------------------------------------

def _routed(name: str) -> tuple[str, str]:
    seen = {}
    responder.spawn(Path("moon_sync_inbox") / name, kit_seams=_seams(seen))
    argv = seen["argv"]
    return argv[argv.index("--model") + 1], argv[argv.index("--effort") + 1]


def test_a_reply_only_kind_does_not_write_code():
    for kind in ("ANSWER", "ACK", "INFORMATION", "FYI"):
        assert responder.writes_code(Path(f"2026-10-03-1015-from-RC-{kind}-x.md")) is False


def test_a_reply_only_kind_runs_on_the_kits_sonnet():
    assert _routed("2026-10-03-1015-from-SS-ANSWER-x.md") == ("sonnet", "medium")


def test_an_acknowledgement_runs_at_the_kits_low_effort():
    for kind in ("ACK", "INFORMATION"):
        assert _routed(f"2026-10-03-1015-from-RC-{kind}-x.md") == ("sonnet", "low"), kind


def test_a_code_writing_kind_runs_on_the_kits_opus():
    for kind in ("ORDER", "RULING", "FIX", "CORRECTION", "REVIEW", "ACTION"):
        model, _effort = _routed(f"2026-10-03-0912-from-MAIN-{kind}-ALL-x.md")
        assert model == "opus", kind


def test_an_unknown_or_unparseable_kind_is_treated_as_code_writing():
    """The DOWNGRADE is the tight set; an odd kind never reaches the cheaper model."""
    assert responder.writes_code(Path("2026-10-03-1015-from-CS-OUR-position.md")) is True
    assert responder.writes_code(Path("note.md")) is True


def test_a_code_writing_run_uses_medium_effort():
    """MAIN REPO-REVIEW perf 2.3 (2026-10-09): high -> medium on code runs."""
    assert _routed("2026-10-03-0912-from-MAIN-ORDER-ALL-x.md") == ("opus", "medium")


# --------------------------------------------------------------------------
# Usage per run (MAIN 0912 E) - the kit's one usage line
# --------------------------------------------------------------------------

def test_the_responder_asks_for_the_json_receipt():
    seen = {}
    responder.spawn(Path("moon_sync_inbox/note.md"), kit_seams=_seams(seen))
    assert seen["argv"][seen["argv"].index("--output-format") + 1] == "json"


def test_each_responder_run_writes_one_kit_usage_line():
    responder.spawn(Path("moon_sync_inbox/2026-10-03-1015-from-SS-ANSWER-x.md"),
                    kit_seams=_seams({}))
    log = Path(lw_headless_env.FLEET_ROOT) / lw_headless_env.kit.USAGE_REL
    lines = log.read_text(encoding="ascii").splitlines()
    assert len(lines) == 1
    line = json.loads(lines[0])
    assert line["code"] == "LW" and line["note"].endswith("from-SS-ANSWER-x.md")
    assert line["input_tokens"] == 1
