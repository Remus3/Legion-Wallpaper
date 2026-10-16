r"""drift_guard: telling a RENAMED sibling repo apart from an ABSENT one.

Reported by RC 2026-09-06 (RC e752e4edc). RC's cross-repo guards held
LW_ROOT = C:\LegionWallpaper; LW's rename to "C:\Legion Wallpaper" turned both
of them from checking into SKIPPING, and RC's suite stayed green for about
three hours with nothing being compared. LW has the identical structure aimed
at C:\<RC>, which is why this exists here too.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

import drift_guard as DG  # noqa: E402


# ---- a renamed sibling must go RED, not quiet ------------------------------
#
# RC's cross-repo guards held LW_ROOT = C:\LegionWallpaper. The 2026-09-06
# rename to "C:\Legion Wallpaper" turned both of them from checking into
# SKIPPING, and RC's suite stayed green for ~3 hours with nothing comparing
# anything. The bytes happened to agree, so nothing broke - which is the
# uncomfortable part, not the reassuring one.
#
# LW has the identical structure pointed at C:\<RC>. The fix is not
# "stop hardcoding": it is that a sibling which EXISTS UNDER ANOTHER SPELLING
# must be distinguishable from one that is genuinely absent, because only the
# first is a bug and only the second deserves a skip.


def test_a_present_sibling_resolves(tmp_path):
    (tmp_path / "Sibling Tree" / ".git").mkdir(parents=True)
    path, status = DG.resolve_sibling_root(tmp_path / "Sibling Tree")
    assert status == "present" and path.name == "Sibling Tree"


def test_a_worktree_style_git_file_counts_as_a_repo(tmp_path):
    """A linked worktree carries `.git` as a FILE; it is still a live checkout."""
    (tmp_path / "Sibling Tree").mkdir()
    (tmp_path / "Sibling Tree" / ".git").write_text("gitdir: x\n", encoding="ascii")
    _path, status = DG.resolve_sibling_root(tmp_path / "Sibling Tree")
    assert status == "present"


# ---- a HALF-MOVED sibling must go RED, not compare stale bytes -------------
#
# Measured 2026-10-08 (LEDGER 283/286): RC's C: -> E: move ran in two steps, and
# for a while E:\<RC> existed WITHOUT .git while the live repo was
# still on the other drive. A bare `is_dir()` called that copy "present", so the
# slots.py / winmutex.py byte-identity check would have compared against a
# stale copy and stayed green - matching only because the bytes happened to
# agree. A directory with no .git is not the sibling REPO.


def test_a_directory_without_git_is_a_half_move_not_present(tmp_path):
    (tmp_path / "Sibling Tree").mkdir()
    path, status = DG.resolve_sibling_root(tmp_path / "Sibling Tree")
    assert status == "no-git", "a copy without .git must never read as present"
    assert path is not None and path.name == "Sibling Tree"


def test_the_configured_sibling_is_derived_not_a_drive_literal():
    """drift_guard's sibling is found beside this checkout by its pinned name
    key (tools/sibling_names.py, RRF-3.2), so no spelling is configured."""
    import sibling_names

    assert DG.SIBLING_REPO == sibling_names.sibling_dir("RC")


def test_no_tracked_code_hardcodes_the_rc_root_as_a_drive_literal():
    """The RC twin of tests/test_no_hardcoded_c_paths.py: no drive literal in
    front of any pinned RC display name (tools/sibling_names.py, RRF-3.2)."""
    import re

    import sibling_names as sn
    import tracked_corpus

    drive = re.compile(r"[A-Za-z]:[\\/]+$")
    suffixes = (".py", ".ps1", ".psm1", ".json", ".toml", ".cmd", ".bat", ".ahk")
    hits = []
    for rel in (n for n in tracked_corpus.tracked_files() if n.lower().endswith(suffixes)):
        try:
            text = tracked_corpus.read_text(rel, errors="replace")
        except OSError:
            continue
        hits += [f"{rel}:{text.count(chr(10), 0, s) + 1}"
                 for s, _e, code in sn.finditer(text)
                 if code == "RC" and drive.search(text[max(0, s - 8):s])]
    assert not hits, f"RC root drive literal(s) - use drift_guard.SIBLING_REPO: {hits}"


def test_a_renamed_sibling_is_reported_as_renamed_not_absent(tmp_path):
    """The whole point: this case used to be indistinguishable from absent."""
    (tmp_path / "Sibling-Tree").mkdir()
    path, status = DG.resolve_sibling_root(tmp_path / "Sibling Tree")
    assert status == "renamed", "a renamed sibling must never read as absent"
    assert path.name == "Sibling-Tree", "and must name where it actually is"


def test_a_space_to_nospace_rename_is_caught(tmp_path):
    """The exact shape of the 2026-09-06 LW rename, from the other side."""
    (tmp_path / "SiblingTree").mkdir()
    _path, status = DG.resolve_sibling_root(tmp_path / "Sibling Tree")
    assert status == "renamed"


def test_a_genuinely_absent_sibling_is_absent(tmp_path):
    """A CI runner has no sibling tree at all. That still deserves a skip."""
    path, status = DG.resolve_sibling_root(tmp_path / "Sibling Tree")
    assert status == "absent" and path is None


def test_an_unrelated_neighbour_is_not_mistaken_for_a_rename(tmp_path):
    (tmp_path / "Other Tree").mkdir()
    _path, status = DG.resolve_sibling_root(tmp_path / "Sibling Tree")
    assert status == "absent", "only a name-equivalent directory is a rename"
