"""gemini-removal: the director + auditor roles behind a backend seam.

Gemini was never a config flag in LW - it was structurally the DIRECTOR (it
AUTHORS each cycle's directive) and the AUDITOR (it scores the cycle's diff).
Removing it therefore means replacing what authors the directive, not switching
a backend behind a key that already exists.

These tests pin the reversible half: a `*_backend` seam whose default is
`claude`, with the Gemini call path left intact and reachable as the rollback.
The rollback is two config keys, exactly as `channel` is one for the executor.

Nothing here spawns a real model call - `oracle()` is exercised against injected
fakes, because the point of the seam is that the dispatch is testable without a
vendor.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


def _load_controller():
    spec = importlib.util.spec_from_file_location(
        "lw_loop_controller_under_test", ROOT / "ops" / "loop" / "loop_controller.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


lc = _load_controller()


# ---- the seam itself -------------------------------------------------------

def test_backend_defaults_to_claude_when_unconfigured():
    """The DEFAULT is the whole point: an un-keyed config must not reach Gemini."""
    assert lc.oracle_backend({}, "director") == "claude"
    assert lc.oracle_backend({}, "auditor") == "claude"


def test_per_role_key_wins_over_the_shared_key():
    cfg = {"oracle_backend": "claude", "auditor_backend": "gemini"}
    assert lc.oracle_backend(cfg, "director") == "claude"
    assert lc.oracle_backend(cfg, "auditor") == "gemini"


def test_shared_key_sets_both_roles():
    cfg = {"oracle_backend": "gemini"}
    assert lc.oracle_backend(cfg, "director") == "gemini"
    assert lc.oracle_backend(cfg, "auditor") == "gemini"


def test_backend_is_case_and_whitespace_tolerant():
    assert lc.oracle_backend({"director_backend": " Gemini "}, "director") == "gemini"


def test_unknown_backend_falls_back_to_claude_rather_than_crashing():
    """An unattended run must not die on a typo, and must not silently bill the
    vendor being removed. Unknown -> claude, the safe default."""
    assert lc.oracle_backend({"director_backend": "grok"}, "director") == "claude"


# ---- the live config is flipped -------------------------------------------

def test_shipped_config_routes_both_roles_to_claude():
    import json
    cfg = json.loads((ROOT / "ops" / "loop" / "config.json").read_text(encoding="utf-8"))
    assert lc.oracle_backend(cfg, "director") == "claude"
    assert lc.oracle_backend(cfg, "auditor") == "claude"


# ---- the claude oracle: ONE kit.spawn per try (kit v4) ---------------------

def _kit_seams(seen: dict, *, url="http://127.0.0.1:4999/x", result="answer"):
    """kit.spawn's external edges, injected: URL, connect, runner, exe."""
    import json as _json

    def _run(argv, **kw):
        seen.setdefault("calls", []).append((argv, kw))

        class _R:
            returncode = 0
            stdout = _json.dumps({"result": result, "usage": {}})
            stderr = ""
        return _R()

    return {"url_source": lambda: url,
            "connect": lambda *a, **k: type("C", (), {"close": lambda self: None})(),
            "run": _run, "exe_source": lambda: "claude.exe"}


def _seam_spawn(monkeypatch, seams):
    import functools
    he = lc.headless_env
    monkeypatch.setattr(he, "spawn", functools.partial(he.spawn, **seams))


def test_claude_oracle_is_read_only(monkeypatch):
    """The director and auditor READ the tree and emit text. They must never get
    the executor's bypassPermissions - that channel exists to let the executor
    COMMIT, and an adjudicator that can write is not an adjudicator."""
    seen = {}
    _seam_spawn(monkeypatch, _kit_seams(seen))
    monkeypatch.setattr(lc, "CFG", {"repo_root": "C:\\Legion Wallpaper"})
    assert lc.claude_oracle("body", "Audit.") == "answer"
    (argv, _kw), = seen["calls"]
    assert "bypassPermissions" not in argv
    assert argv[argv.index("--permission-mode") + 1] == "plan"
    assert argv[argv.index("--add-dir") + 1] == "C:\\Legion Wallpaper"


def test_claude_oracle_puts_body_and_instruction_on_stdin_with_the_exact_model(monkeypatch):
    seen = {}
    _seam_spawn(monkeypatch, _kit_seams(seen))
    monkeypatch.setattr(lc, "CFG", {"oracle_model": "claude-opus-5"})
    lc.claude_oracle("the body", "Output ONLY the directive.")
    (argv, kw), = seen["calls"]
    assert argv[argv.index("--model") + 1] == "claude-opus-5"
    assert "the body" in kw["input"] and "Output ONLY the directive." in kw["input"]
    assert not any("Output ONLY the directive." in a for a in argv), "never in argv"


# ---- dispatch --------------------------------------------------------------

def test_oracle_routes_to_gemini_when_the_backend_says_so(monkeypatch):
    seen = {}
    monkeypatch.setattr(lc, "CFG", {"director_backend": "gemini"})
    monkeypatch.setattr(lc, "gemini", lambda b, i: (seen.update(gemini=(b, i)), "G")[1])
    monkeypatch.setattr(lc, "claude_oracle", lambda b, i: (seen.update(claude=(b, i)), "C")[1])
    assert lc.oracle("body", "inst", role="director") == "G"
    assert "claude" not in seen


def test_oracle_routes_to_claude_by_default(monkeypatch):
    seen = {}
    monkeypatch.setattr(lc, "CFG", {})
    monkeypatch.setattr(lc, "gemini", lambda b, i: (seen.update(gemini=1), "G")[1])
    monkeypatch.setattr(lc, "claude_oracle", lambda b, i: (seen.update(claude=1), "C")[1])
    assert lc.oracle("body", "inst", role="director") == "C"
    assert "gemini" not in seen


def test_claude_path_never_accrues_gemini_spend(monkeypatch):
    """ceiling_usd is a REAL rail for a metered vendor. Once the claude backend is
    the default it must stay at zero, or the loop stops itself on a phantom bill."""
    monkeypatch.setattr(lc, "CFG", {})
    monkeypatch.setattr(lc, "GEMINI_USD", 0.0)
    monkeypatch.setattr(lc, "claude_oracle", lambda b, i: "ok")
    lc.oracle("body", "inst", role="auditor")
    assert lc.GEMINI_USD == 0.0


def test_director_and_auditor_go_through_the_oracle_seam():
    """Regression guard: the two roles must not call gemini() directly again."""
    src = (ROOT / "ops" / "loop" / "loop_controller.py").read_text(encoding="utf-8")
    body = src[src.index("def director("):src.index("# ---- budget meter")]
    assert "gemini(" not in body, "director/auditor must dispatch via oracle()"
    assert "oracle(" in body


# ---- the rollback path stays reachable ------------------------------------

def test_gemini_backend_is_not_deleted():
    """The removal is reversible ON PURPOSE: flip two keys and the vendor is back.
    A big-bang deletion is the version that cannot be undone at 3am."""
    assert callable(getattr(lc, "gemini", None))
    assert callable(getattr(lc, "_gemini_call", None))


def test_gemini_mutex_still_exists_for_the_cross_repo_contract():
    """ops/loop/winmutex.py is byte-identical-by-contract with Riot Commander and
    GEMINI_MUTEX still has a live consumer there. Deleting it needs a three-way
    re-pin, not a sweep."""
    assert lc.winmutex.GEMINI_MUTEX == "Global\\MX-7C41A9E2"


def test_oracle_role_must_be_known():
    with pytest.raises(ValueError):
        lc.oracle("body", "inst", role="nonsense")


# ---- the headless proxy gate (operator directive 2026-10-02) ----------------

def test_a_refused_proxy_fails_the_claude_oracle_call_without_spawning(monkeypatch, tmp_path):
    """Refusal = this call fails with the None sentinel. No retry, no subprocess,
    and never a plain `claude` in its place."""
    he = lc.headless_env
    logged, ran = [], []
    seen = {}
    _seam_spawn(monkeypatch, _kit_seams(seen, url=None))
    monkeypatch.setenv(he.LOG_DIR_ENV, str(tmp_path))
    monkeypatch.setattr(lc, "log", logged.append)
    monkeypatch.setattr(lc, "CFG", {})
    monkeypatch.setattr(lc.time, "sleep", lambda *_a: ran.append("sleep"))
    assert lc.claude_oracle("body", "inst") is None
    assert seen == {} and ran == [], \
        "a refused gate must not spawn, and must not back off into a retry"
    assert any("headless spawn refused" in m for m in logged)
    assert list(tmp_path.glob("*.log"))


def test_the_claude_oracle_hands_the_child_the_gated_env(monkeypatch):
    seen = {}
    _seam_spawn(monkeypatch, _kit_seams(seen))
    monkeypatch.setattr(lc, "CFG", {})
    assert lc.claude_oracle("body", "inst") == "answer"
    (_argv, kw), = seen["calls"]
    assert kw["env"]["ANTHROPIC_BASE_URL"] == "http://127.0.0.1:4999/x"


def test_each_oracle_try_is_accounted_by_the_fleet_kit(monkeypatch):
    """Each try is ONE kit.spawn (kit v4 stdin=True): one budget start and one
    usage line, from the kit itself."""
    import json as _json
    from pathlib import Path as _Path
    he = lc.headless_env
    _seam_spawn(monkeypatch, _kit_seams({}))
    monkeypatch.setattr(lc, "CFG", {"oracle_model": "claude-m1"})
    assert lc.claude_oracle("body", "inst") == "answer"
    assert he.budget().used() == 1
    line = _json.loads((_Path(he.FLEET_ROOT) / he.kit.USAGE_REL)
                       .read_text(encoding="ascii").splitlines()[-1])
    assert (line["note"], line["model"], line["rc"]) == ("loop-oracle", "claude-m1", 0)
