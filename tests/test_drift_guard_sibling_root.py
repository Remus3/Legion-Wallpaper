"""drift_guard: telling a RENAMED sibling repo apart from an ABSENT one.

Reported by RC 2026-09-06 (Amberstone e752e4edc). RC's cross-repo guards held
LW_ROOT = C:\LegionWallpaper; LW's rename to "C:\Legion Wallpaper" turned both
of them from checking into SKIPPING, and RC's suite stayed green for about
three hours with nothing being compared. LW has the identical structure aimed
at C:\Riot Commander, which is why this exists here too.
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
# LW has the identical structure pointed at C:\Riot Commander. The fix is not
# "stop hardcoding": it is that a sibling which EXISTS UNDER ANOTHER SPELLING
# must be distinguishable from one that is genuinely absent, because only the
# first is a bug and only the second deserves a skip.


def test_a_present_sibling_resolves(tmp_path):
    (tmp_path / "Riot Commander").mkdir()
    path, status = DG.resolve_sibling_root(tmp_path / "Riot Commander")
    assert status == "present" and path.name == "Riot Commander"


def test_a_renamed_sibling_is_reported_as_renamed_not_absent(tmp_path):
    """The whole point: this case used to be indistinguishable from absent."""
    (tmp_path / "Riot-Commander").mkdir()
    path, status = DG.resolve_sibling_root(tmp_path / "Riot Commander")
    assert status == "renamed", "a renamed sibling must never read as absent"
    assert path.name == "Riot-Commander", "and must name where it actually is"


def test_a_space_to_nospace_rename_is_caught(tmp_path):
    """The exact shape of the 2026-09-06 LW rename, from the other side."""
    (tmp_path / "RiotCommander").mkdir()
    _path, status = DG.resolve_sibling_root(tmp_path / "Riot Commander")
    assert status == "renamed"


def test_a_genuinely_absent_sibling_is_absent(tmp_path):
    """A CI runner has no sibling tree at all. That still deserves a skip."""
    path, status = DG.resolve_sibling_root(tmp_path / "Riot Commander")
    assert status == "absent" and path is None


def test_an_unrelated_neighbour_is_not_mistaken_for_a_rename(tmp_path):
    (tmp_path / "Clockspeed").mkdir()
    _path, status = DG.resolve_sibling_root(tmp_path / "Riot Commander")
    assert status == "absent", "only a name-equivalent directory is a rename"
