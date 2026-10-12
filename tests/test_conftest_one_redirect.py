"""RRF-2.6 (MAIN REPO-REVIEW 2.6): tests/conftest.py carried six autouse
fixtures that each pulled tmp_path for one redirect apiece (fleet files,
operator tasks, run logs, governor slots, bridge journal). LW now has ONE
autouse redirect fixture; the kit's _fleet_runtime_roots is the other
tmp_path user. Pinned so a seventh one-var fixture goes red instead of
quietly re-adding per-test setup cost."""
from __future__ import annotations

import ast
import os
from pathlib import Path

import lw_headless_env as he

CONFTEST = Path(__file__).resolve().parent / "conftest.py"
REDIRECTS = {
    "LW_OPS_TASKS_ROOT": "operator_tasks",
    "LW_RUNLOG_ROOT": "runlog",
    "LW_GOVERNOR_ROOT": "governor/slots",
    "LW_BRIDGE_JOURNAL": "bridge/sends.jsonl",
}


def _autouse_tmp_path_fixtures() -> list[str]:
    tree = ast.parse(CONFTEST.read_text(encoding="ascii"))
    out = []
    for node in tree.body:
        if not isinstance(node, ast.FunctionDef):
            continue
        autouse = any(isinstance(d, ast.Call) and any(
            k.arg == "autouse" and getattr(k.value, "value", False) is True
            for k in d.keywords) for d in node.decorator_list)
        uses_tmp = "tmp_path" in ast.unparse(node)
        if autouse and uses_tmp:
            out.append(node.name)
    return out


def test_conftest_has_one_lw_autouse_tmp_path_fixture():
    assert _autouse_tmp_path_fixtures() == ["_lw_live_state_redirect"]


def test_every_redirect_points_under_this_tests_tmp_path(tmp_path):
    for var, sub in REDIRECTS.items():
        assert Path(os.environ[var]) == tmp_path / sub, var
    assert Path(he.FLEET_ROOT) == tmp_path / "fleet_root"
    assert Path(he.LOG_DIR) == tmp_path / "logs"
