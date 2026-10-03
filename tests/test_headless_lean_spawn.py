"""Every headless `claude` spawn this tree makes carries the lean flags.

MAIN 0912 (2026-10-03, digest-verified a59494ae): 58k input tokens per call is
SETUP, not work, and it is re-sent on every model call of a run. Measured from
LW's own checkout through the proxy, one trivial prompt:

    no flags (the responder as it ran)                   58,510
    --strict-mcp-config --setting-sources project,local  53,143
    --strict-mcp-config --setting-sources project        47,026

`project,local` (MAIN's suggestion) keeps the gitignored local scope, which in
this tree re-enables three plugins and pins the `rc-main` alias the proxy
answers with 404. It carries no hook and no deny rule, so dropping it costs no
floor. `--bare` is NOT used: it skips every hook, and LW's floors live in hooks
(PreToolUse precommit_gate, Stop claimed_green_gate).

The flag set lives ONCE, in `lw_headless_env.LEAN_ARGS`. The last arm here
ENUMERATES the spawn sites rather than trusting this list of four.
"""
from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

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

_PROXY_UP = {"registry_reader": lambda: None,
             "environ": {"CLAUDE_HEADLESS_BASE_URL": "http://127.0.0.1:4999/x"},
             "probe": lambda _h, _p: True}


def _carries_lean(argv: list) -> bool:
    lean = list(lw_headless_env.LEAN_ARGS)
    return any(argv[i:i + len(lean)] == lean for i in range(len(argv)))


def test_the_lean_set_drops_mcp_and_the_user_and_local_scopes():
    lean = list(lw_headless_env.LEAN_ARGS)
    assert "--strict-mcp-config" in lean
    assert lean[lean.index("--setting-sources") + 1] == "project"
    # A floor is not traded for tokens: --bare skips every hook.
    assert "--bare" not in lean


# --------------------------------------------------------------------------
# The four spawn paths
# --------------------------------------------------------------------------

def test_the_responder_spawn_is_lean():
    assert _carries_lean(responder.spawn_argv(Path("moon_sync_inbox/note.md")))


def test_the_loop_executor_spawn_is_lean():
    ex = executor.SdkExecutor({"claude_cmd": "claude", "repo_root": "."}, None,
                              log=print, stop=None, awrite=None)
    assert _carries_lean(ex.build_argv(1))


def test_the_loop_executor_passes_only_the_mcp_config_it_is_given():
    """--strict-mcp-config with no --mcp-config means NO servers. A loop that
    needs a browser names its config; nothing else is loaded."""
    bare = executor.SdkExecutor({"claude_cmd": "claude"}, None,
                                log=print, stop=None, awrite=None).build_argv(1)
    assert "--mcp-config" not in bare
    named = executor.SdkExecutor({"claude_cmd": "claude", "executor_mcp_config": "m.json"},
                                 None, log=print, stop=None, awrite=None).build_argv(1)
    assert named[named.index("--mcp-config") + 1] == "m.json"


def test_the_oracle_spawn_is_lean_and_keeps_no_transcript():
    """Read-only, plain text, nobody reads it back: no session to persist."""
    argv = lc.claude_oracle_argv("Audit.", {"claude_cmd": "claude"})
    assert _carries_lean(argv)
    assert "--no-session-persistence" in argv


def test_the_ci_watchdog_spawn_is_lean(monkeypatch, tmp_path):
    seen = {}

    def _fake_run(argv, **_kwargs):
        seen["argv"] = argv

        class _R:
            returncode = 0
            stdout = ""
            stderr = ""

        return _R()

    monkeypatch.setattr(cw.shutil, "which", lambda name, path=None: r"C:\fake\claude.CMD")
    monkeypatch.setattr(cw, "run", _fake_run)
    cw._fix_in_worktree(tmp_path, "a" * 40, "1", "claude-sonnet-5", 60, {"PATH": ""})
    assert _carries_lean(seen["argv"])


# Each spawn site, found by what it IS (a `claude` argv carrying the print flag)
# rather than by name - so a fifth site added later is caught here, not missed.
_PRINT_FLAG = re.compile(r"""["']-p["']""")
_CLAUDE = re.compile(r"""["']claude(?:\.cmd)?["']""", re.IGNORECASE)


def test_every_headless_claude_spawn_site_in_the_tree_uses_the_lean_set():
    sites = []
    for base in ("tools", "ops"):
        for path in sorted((ROOT / base).rglob("*.py")):
            rel = path.relative_to(ROOT).as_posix()
            if rel.startswith(("tools/dwpose_onnx/", "ops/runtime/")):
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            if _PRINT_FLAG.search(text) and _CLAUDE.search(text):
                sites.append((rel, "LEAN_ARGS" in text))
    print("spawn sites:", sites)
    # The four known today. Fewer means the instrument went blind.
    assert len(sites) >= 4, sites
    assert all(lean for _rel, lean in sites), sites


# --------------------------------------------------------------------------
# Responder routing: model and effort by the note's kind (MAIN 0912 C + D)
# --------------------------------------------------------------------------

def _route(name: str) -> tuple[str, str]:
    return responder.route(Path("moon_sync_inbox") / name)


def test_a_reply_only_kind_runs_on_sonnet():
    assert _route("2026-10-03-1015-from-SS-ANSWER-x.md") == ("sonnet", "medium")


def test_an_acknowledgement_kind_runs_at_low_effort():
    for kind in ("ACK", "INFORMATION", "FYI"):
        assert _route(f"2026-10-03-1015-from-RC-{kind}-x.md") == ("sonnet", "low"), kind


def test_a_code_writing_kind_keeps_opus():
    for kind in ("ORDER", "RULING", "FIX", "CORRECTION", "REVIEW", "ACTION"):
        assert _route(f"2026-10-03-0912-from-MAIN-{kind}-ALL-x.md") == ("opus", "high"), kind


def test_an_unknown_or_unparseable_kind_keeps_opus():
    """The DOWNGRADE is the tight set. A kind nobody listed - 'OUR', 'WE', a
    bare name - keeps the model the responder always ran, so a code order
    phrased oddly is never answered by the cheaper one."""
    assert _route("2026-10-03-1015-from-CS-OUR-position.md")[0] == "opus"
    assert _route("note.md")[0] == "opus"


def test_the_spawn_argv_carries_the_routed_model_and_effort():
    argv = responder.spawn_argv(Path("moon_sync_inbox/2026-10-03-1015-from-SS-ANSWER-x.md"))
    assert argv[argv.index("--model") + 1] == "sonnet"
    assert argv[argv.index("--effort") + 1] == "medium"


# --------------------------------------------------------------------------
# Usage per run (MAIN 0912 E)
# --------------------------------------------------------------------------

def test_the_responder_asks_for_the_json_receipt():
    argv = responder.spawn_argv(Path("moon_sync_inbox/note.md"))
    assert argv[argv.index("--output-format") + 1] == "json"


def test_the_spawn_writes_each_runs_receipt_to_its_own_usage_file(monkeypatch, tmp_path):
    seen = {}

    def _fake_popen(argv, **kwargs):
        seen["stdout"] = kwargs["stdout"]

        class _P:
            pid = 4242

        return _P()

    monkeypatch.setattr(responder, "USAGE_DIR", tmp_path / "usage")
    monkeypatch.setattr(responder.shutil, "which", lambda _name: r"C:\fake\claude.exe")
    monkeypatch.setattr(responder.subprocess, "Popen", _fake_popen)
    out = responder.spawn(Path("moon_sync_inbox/2026-10-03-1015-from-SS-ANSWER-x.md"),
                          env_seams=_PROXY_UP)
    assert out.verdict == responder.AUTO
    written = Path(seen["stdout"].name)
    assert written.parent == tmp_path / "usage"
    assert written.name.endswith("from-SS-ANSWER-x.json")
    # The parent hands the handle down and lets go of its own copy.
    assert seen["stdout"].closed


def test_an_unwritable_usage_dir_still_spawns(monkeypatch, tmp_path):
    """The receipt is an observation; it must never become the failure."""
    blocker = tmp_path / "usage"
    blocker.write_text("a file where the directory should be", encoding="utf-8")
    seen = {}

    def _fake_popen(argv, **kwargs):
        seen["stdout"] = kwargs["stdout"]

        class _P:
            pid = 4242

        return _P()

    monkeypatch.setattr(responder, "USAGE_DIR", blocker)
    monkeypatch.setattr(responder.shutil, "which", lambda _name: r"C:\fake\claude.exe")
    monkeypatch.setattr(responder.subprocess, "Popen", _fake_popen)
    out = responder.spawn(Path("moon_sync_inbox/note.md"), env_seams=_PROXY_UP)
    assert out.verdict == responder.AUTO
    assert seen["stdout"] is responder.subprocess.DEVNULL
