"""lw_paths.tools_dir(): the shared machine tools root (lw-clean venv + YOLO
weights, realesrgan, mockd), derived instead of spelled `C:\\Tools`.

WHY (LEDGER 287, DEHARDCODE-REST). The tools root did NOT move with the repo on
the 2026-10-08 C: -> E: move - it lives on the system drive. Five tracked code
sites each carried their own `C:\\Tools` literal; they now read one resolver:
`LW_TOOLS_DIR` when set, else `%SystemDrive%\\Tools`.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "tools"))

import lw_paths  # noqa: E402  (path shim above)


def test_tools_dir_honours_override(monkeypatch, tmp_path):
    monkeypatch.setenv("LW_TOOLS_DIR", str(tmp_path))
    assert lw_paths.tools_dir() == tmp_path


def test_tools_dir_defaults_to_system_drive(monkeypatch):
    monkeypatch.delenv("LW_TOOLS_DIR", raising=False)
    monkeypatch.setenv("SystemDrive", "Q:")
    assert str(lw_paths.tools_dir()).replace("/", "\\") == "Q:\\Tools"


def test_tools_dir_without_system_drive_is_c(monkeypatch):
    monkeypatch.delenv("LW_TOOLS_DIR", raising=False)
    monkeypatch.delenv("SystemDrive", raising=False)
    assert str(lw_paths.tools_dir()).replace("/", "\\") == "C:\\Tools"


def _child(expr: str, env_extra: dict[str, str]) -> str:
    """Evaluate `expr` in a fresh interpreter (module constants bind at import)."""
    env = dict(os.environ, **env_extra)
    code = f"import sys; sys.path.insert(0, r'{REPO_ROOT / 'tools'}'); {expr}"
    out = subprocess.run([sys.executable, "-c", code], env=env, cwd=REPO_ROOT,
                         capture_output=True, text=True, check=True,
                         creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    return out.stdout.strip()


def test_every_tools_site_follows_the_override(tmp_path):
    root = str(tmp_path / "T")
    env = {"LW_TOOLS_DIR": root}
    got = _child(
        "import lw_clean_lane, lw_clean_pass, lw_upscale; "
        "print(lw_clean_lane.VENV_PY); print(lw_clean_pass.CLEAN_VENV_PY); "
        "print(lw_clean_pass.WEIGHTS_PATH); print(lw_upscale.NCNN_EXE_DEFAULT)",
        env).splitlines()
    tail = ["lw-clean\\venv\\Scripts\\python.exe",
            "lw-clean\\venv\\Scripts\\python.exe",
            "lw-clean\\yolo11x-train28-best.pt",
            "realesrgan\\realesrgan-ncnn-vulkan.exe"]
    assert len(got) == 4, got
    for value, t in zip(got, tail, strict=True):
        norm = value.replace("/", "\\")
        assert norm.startswith(root.replace("/", "\\")), value
        assert norm.endswith(t), value


def test_upscale_inline_default_matches_resolver():
    env = {k: v for k, v in os.environ.items() if k != "LW_TOOLS_DIR"}
    code = (f"import sys; sys.path.insert(0, r'{REPO_ROOT / 'tools'}'); "
            "import lw_paths, lw_upscale; "
            "print(lw_paths.tools_dir()); print(lw_upscale._TOOLS_DIR)")
    out = subprocess.run([sys.executable, "-c", code], env=env, cwd=REPO_ROOT,
                         capture_output=True, text=True, check=True,
                         creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    a, b = out.stdout.strip().splitlines()
    assert a == b


ASSIGNED_TOOLS_LITERAL = re.compile(
    r"""=\s*r?["'][cC]:(\\\\|\\|/)+Tools""")


def test_no_tracked_py_assigns_a_c_tools_literal():
    out = subprocess.run(["git", "ls-files", "-z", "*.py"], cwd=REPO_ROOT,
                         capture_output=True, check=True).stdout
    hits = []
    for rel in (n for n in out.decode("utf-8", "replace").split("\0") if n):
        if rel.startswith(("scratchpad/", "docs/_archive/")):
            continue
        if rel == "tests/test_lw_paths_tools_dir.py":
            continue
        try:
            text = (REPO_ROOT / rel).read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        hits += [f"{rel}:{i}" for i, ln in enumerate(text.splitlines(), 1)
                 if ASSIGNED_TOOLS_LITERAL.search(ln)]
    assert not hits, "use lw_paths.tools_dir():\n  " + "\n  ".join(hits)
