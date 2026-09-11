"""Arms for `tools/lw_false_red_probe.py`.

The probe's whole value is that the stripped environment really cannot resolve
git. A stripper that quietly kept the git directory would report "0 false-RED
sites" and be believed - the false-GREEN failure mode of a false-RED probe.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import lw_false_red_probe as probe  # noqa: E402


def test_a_directory_holding_git_exe_is_stripped(tmp_path):
    holds = tmp_path / "holds"
    holds.mkdir()
    (holds / "git.exe").write_text("", encoding="utf-8")
    clean = tmp_path / "clean"
    clean.mkdir()
    out = probe.path_without_git({"PATH": os.pathsep.join([str(holds), str(clean)])})
    assert str(holds) not in out.split(os.pathsep)
    assert str(clean) in out.split(os.pathsep), "MIRROR: it must keep everything else"


def test_an_empty_path_entry_is_dropped_rather_than_kept_as_cwd(tmp_path):
    out = probe.path_without_git({"PATH": os.pathsep.join([str(tmp_path), "", "  "])})
    assert out.split(os.pathsep) == [str(tmp_path)]


def test_a_missing_path_variable_does_not_raise():
    assert probe.path_without_git({}) == ""
