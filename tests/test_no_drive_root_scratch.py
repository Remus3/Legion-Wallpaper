"""No drive-root scratch, temp or worktree path (MAIN ORDER 2026-11-16-2145, E-ROOT).

THE RULE. Kit-adoption and session runs left helper scripts, commit messages,
logs and a hand-off copy in ad-hoc `<drive>:\\tmp*` folders at the E: root. Every
LW scratch file now goes under ONE named root, the LW sidecar Scratch dir
(`<sidecar-drive>:\\Sidecars\\LW\\Scratch`), resolved at run time by
`tools/lw_paths.py scratch_root()` and printed by `python tools/lw_paths.py
scratch [name]`. CLAUDE.md and every headless child prompt (the race-guard
CHILD_RULE the responder and the loop executor carry, plus the CI-fix prompt)
name it.

WHAT THIS GUARDS.
  1. No tracked code, CLAUDE.md, prompt or helper script names a path whose
     parent is a drive root and whose first component reads as scratch, temp
     or worktree (`E:\\tmp_kr`, `C:/Temp`, `%SystemDrive%\\rc-worktrees`,
     `<drive>:\\lwkit_tmp`). `<drive>:\\Sidecars\\...` is not flagged: its
     first component is Sidecars.
  2. Where LW derives such a path at run time - scratch_root() and the lane
     worktree (fleet_lanes.worktree_path) - the derived path lies under
     <sidecar root>/LW when the sidecar exists, and never directly under a
     drive root otherwise.
"""
from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

import gitdep
import lw_paths
import lw_race_guards as rg
import tracked_corpus

import pytest

ROOT = Path(__file__).resolve().parent.parent

DRIVE_ROOT_SCRATCH = re.compile(
    r"(?:(?<![A-Za-z0-9_])(?:[A-Za-z]|<[A-Za-z_-]*drive>):|%SystemDrive%|\$env:SystemDrive)"
    r"(?:\\\\|\\|/)+[\w.-]*(?:tmp|temp|scratch|worktree)[\w.-]*(?![\w.-])",
    re.IGNORECASE)

# Prefix (ends in "/") or exact file -> why it may name such a path.
ALLOWLIST: dict[str, str] = {
    "tests/": "fixtures: the path string is the input under test",
    "docs/_archive/": "archived history, immutable",
    "docs/ledger/": "the ledger's older entries, verbatim per month",
    "docs/history_notes.md": "append-only history record",
    "docs/claude-md-history.md": "verbatim pre-condense CLAUDE.md text",
    "scratchpad/": "dated one-off artifacts, never rewritten",
    "ops/fleet_kit/": "MAIN's vendored kit, never edited here (ROADMAP E-ROOT-KIT)",
    "docs/specs/2026-07-26-f1-sdk-executor-channel.md": "describes RC's layout, not LW's",
}


def _allowed(rel: str) -> bool:
    return any(rel == k or (k.endswith("/") and rel.startswith(k)) for k in ALLOWLIST)


def scan_text(text: str) -> list[int]:
    """1-based line numbers naming a drive-root scratch/temp/worktree path. Pure."""
    return [i for i, line in enumerate(text.splitlines(), 1)
            if DRIVE_ROOT_SCRATCH.search(line)]


def _sweep(include_allowed: bool = False) -> tuple[int, dict[str, list[int]]]:
    scanned, hits = 0, {}
    for rel in tracked_corpus.tracked_files():
        if not include_allowed and _allowed(rel):
            continue
        try:
            raw = tracked_corpus.read_bytes(rel)
        except OSError:
            continue
        if b"\0" in raw[:8192]:
            continue
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            continue
        scanned += 1
        lines = scan_text(text)
        if lines:
            hits[rel] = lines
    return scanned, hits


@gitdep.requires_git
def test_no_tracked_file_names_a_drive_root_scratch_path():
    scanned, hits = _sweep()
    assert scanned > 200, f"only {scanned} tracked text files scanned - corpus wrong"
    rows = [f"{rel}:{n}" for rel, lines in sorted(hits.items()) for n in lines]
    assert not rows, ("drive-root scratch/temp/worktree path(s):\n  " + "\n  ".join(rows)
                      + "\nUse `python tools/lw_paths.py scratch <name>` (LW sidecar Scratch).")


@gitdep.requires_git
def test_every_allowlist_entry_is_load_bearing_or_a_standing_exemption():
    _, hits = _sweep(include_allowed=True)
    standing = {"docs/_archive/", "docs/ledger/", "docs/history_notes.md",
                "docs/claude-md-history.md", "scratchpad/", "ops/fleet_kit/"}
    dead = [k for k in ALLOWLIST if k not in standing
            and not any(rel == k or (k.endswith("/") and rel.startswith(k)) for rel in hits)]
    assert not dead, f"allowlist entries with no hits (remove them): {dead}"


@pytest.mark.parametrize("planted", [
    r"E:\tmp_kr\send.py",
    r"E:\lwkit_tmp\prog.py",
    r"E:\tmp\ho97.txt",
    "E:/tmp_lwdone",
    r"C:\Temp\x.png",
    r"%SystemDrive%\rc-worktrees",
    r"$env:SystemDrive\lw-scratch",
    r"<drive>:\cs-fleet9-scratch",
    r"'E:\\\\tmp_hd'",
])
def test_a_planted_drive_root_scratch_path_is_caught(planted):
    assert scan_text(planted), f"missed: {planted}"


@pytest.mark.parametrize("innocent", [
    r"<sidecar-drive>:\Sidecars\LW\Scratch\resp",
    r"E:\Sidecars\LW\Worktree\lane-0",
    r"<repo>\ops\runtime\scratch",
    "images/_gen_scratch/<batch-id>/",
    r"E:\Legion Wallpaper\tools\lw_tmp_helper.py",
    "tempfile.mkdtemp(prefix='lw_tmp_')",
    "https://example.com/tmp/x",
])
def test_a_legitimate_neighbour_survives(innocent):
    assert not scan_text(innocent), f"false positive: {innocent}"


# ---- derived paths -------------------------------------------------------

def _is_drive_root_child(p: Path) -> bool:
    return p.parent == Path(p.anchor) if p.anchor else False


def test_scratch_root_lies_under_the_lw_sidecar(tmp_path, monkeypatch):
    side = tmp_path / "Sidecars"
    (side / "LW").mkdir(parents=True)
    monkeypatch.delenv(lw_paths.SCRATCH_ENV, raising=False)
    monkeypatch.setenv("FLEET_SIDECAR_ROOT", str(side))
    got = lw_paths.scratch_root()
    assert got == side / "LW" / "Scratch"
    assert lw_paths.scratch_dir("adopt") == side / "LW" / "Scratch" / "adopt"


def test_scratch_root_without_a_sidecar_stays_in_the_repo(tmp_path, monkeypatch):
    monkeypatch.delenv(lw_paths.SCRATCH_ENV, raising=False)
    monkeypatch.setenv("FLEET_SIDECAR_ROOT", "")
    got = lw_paths.scratch_root()
    assert got == lw_paths.repo_root() / "ops" / "runtime" / "scratch"
    assert not _is_drive_root_child(got)


def test_scratch_root_env_override_wins(tmp_path, monkeypatch):
    monkeypatch.setenv(lw_paths.SCRATCH_ENV, str(tmp_path / "s"))
    assert lw_paths.scratch_root() == tmp_path / "s"


def test_scratch_dir_refuses_an_escaping_name(tmp_path, monkeypatch):
    monkeypatch.setenv(lw_paths.SCRATCH_ENV, str(tmp_path / "s"))
    for bad in ("..", "../x", "a/b", "", "C:x"):
        with pytest.raises(ValueError):
            lw_paths.scratch_dir(bad)


def test_the_scratch_env_is_a_declared_runtime_root():
    assert rg.ENV_ROOTS.get(lw_paths.SCRATCH_ENV) == "scratch"


def test_the_lane_worktree_lies_under_the_lw_sidecar(tmp_path):
    spec = importlib.util.spec_from_file_location(
        "fleet_kit_fleet_lanes", ROOT / "ops" / "fleet_kit" / "fleet_lanes.py")
    fl = sys.modules.get("fleet_kit_fleet_lanes")
    if fl is None:
        fl = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = fl
        spec.loader.exec_module(fl)
    side = tmp_path / "Sidecars"
    (side / "LW").mkdir(parents=True)
    wt = fl.worktree_path(ROOT, "LW", 0, root=side)
    assert Path(wt).is_relative_to(side / "LW"), wt


# ---- the rule is written down where runs read it --------------------------

def test_claude_md_names_the_scratch_root():
    text = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")
    assert "lw_paths.py scratch" in text
    assert r"Sidecars\LW\Scratch" in text


def test_every_child_prompt_carries_the_scratch_rule():
    assert "lw_paths.py scratch" in rg.SCRATCH_RULE
    assert rg.SCRATCH_RULE in rg.CHILD_RULE
    text = (ROOT / "tools" / "ci_watchdog.py").read_text(encoding="utf-8")
    assert "SCRATCH_RULE" in text
