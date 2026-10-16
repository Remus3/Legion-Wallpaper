"""CONFIG-SLUG: every ops/loop/config*.json `transcript_dir` names the LIVE
Claude project slug for this repo.

The checkout moved from drive C to drive E; the transcript
store keys a project by its path with every non-alphanumeric character
turned into a hyphen, so live sessions write under `E--Legion-Wallpaper`.
The configs still named `C--Legion-Wallpaper`, a directory no session writes
to any more, so `loop_controller.transcript_dir()` (ops/loop/loop_controller.py
`transcript_dir`, read by `session_files` and the launch-time session pin)
metered a dead store.

The slug is asserted as a literal, not derived from the checkout root: CI runs
from `/home/runner/work/...` and a worktree from `.claude/worktrees/...`, and
neither is the path the operator's sessions are keyed by.
"""
import json
import os
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CONFIGS = sorted((ROOT / "ops" / "loop").glob("config*.json"))
LIVE_SLUG = "E--Legion-Wallpaper"
EXPECTED = "~/.claude/projects/" + LIVE_SLUG

# An absolute path of any kind (drive letter, UNC, POSIX root) or an account
# home spelled out would name the account in a PUBLIC repo.
_ABSOLUTE = re.compile(r"^(?:[A-Za-z]:[\\/]|[\\/])")
_ACCOUNT_HOME = re.compile(r"(?i)[\\/]users[\\/]|[\\/]home[\\/]")


def test_configs_exist():
    names = {p.name for p in CONFIGS}
    assert {"config.json", "config.gate.json", "config.dry.json",
            "config.p5.json"} <= names


@pytest.mark.parametrize("cfg", CONFIGS, ids=lambda p: p.name)
def test_transcript_dir_names_the_live_e_slug(cfg):
    doc = json.loads(cfg.read_text(encoding="utf-8"))
    if "transcript_dir" not in doc:
        pytest.skip(f"{cfg.name} carries no transcript_dir")
    td = doc["transcript_dir"]
    assert td == EXPECTED, f"{cfg.name}: transcript_dir={td!r}"
    assert Path(td.replace("\\", "/")).name == LIVE_SLUG
    assert "C--" not in td


@pytest.mark.parametrize("cfg", CONFIGS, ids=lambda p: p.name)
def test_transcript_dir_names_no_account_path(cfg):
    doc = json.loads(cfg.read_text(encoding="utf-8"))
    td = doc.get("transcript_dir")
    if td is None:
        pytest.skip(f"{cfg.name} carries no transcript_dir")
    assert not _ABSOLUTE.match(td), f"{cfg.name}: absolute path {td!r}"
    assert not _ACCOUNT_HOME.search(td), f"{cfg.name}: account home in {td!r}"
    assert td.startswith("~/"), f"{cfg.name}: expected a ~-relative path"


def test_transcript_dir_expands_under_the_current_home(monkeypatch, tmp_path):
    """The consumer expands `~` (loop_controller.transcript_dir); the expanded
    path lands under whatever home the running account has."""
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.setenv("HOME", str(tmp_path))
    got = Path(os.path.expandvars(EXPECTED)).expanduser()
    assert got == tmp_path / ".claude" / "projects" / LIVE_SLUG
