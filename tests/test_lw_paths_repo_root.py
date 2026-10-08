"""lw_paths.repo_root() / sibling_repo(): the derived replacements for the
drive-letter literals the 2026-10-08 C: -> E: move exposed."""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "tools"))

import lw_paths  # noqa: E402  (path shim above)


def test_repo_root_is_this_checkout():
    root = lw_paths.repo_root()
    assert root == REPO_ROOT
    assert (root / "tools" / "lw_paths.py").is_file()


def test_sibling_repo_sits_beside_this_checkout(monkeypatch):
    monkeypatch.delenv("LW_SIBLINGS_DIR", raising=False)
    assert lw_paths.sibling_repo("Riot Commander") == REPO_ROOT.parent / "Riot Commander"


def test_sibling_repo_honours_override(monkeypatch, tmp_path):
    monkeypatch.setenv("LW_SIBLINGS_DIR", str(tmp_path))
    assert lw_paths.sibling_repo("Resin Compute") == tmp_path / "Resin Compute"
