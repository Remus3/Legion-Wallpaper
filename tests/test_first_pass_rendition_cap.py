"""MAIN ORDER 2026-11-14-0935 item 1: cap unapproved renditions on the desktop.

Picks naming a _firstneedauth file ran 19-22 percent of desktop picks. The
first-pass driver keeps only the RENDITION_CAP newest _firstneedauth copies in
the pictures folder and MOVES (never deletes) the rest to a holding folder the
rotation does not scan (it lists files directly under the folder only).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import lw_first_pass as fp  # noqa: E402


def _make(folder: Path, name: str, mtime: int) -> Path:
    p = folder / name
    p.write_bytes(name.encode("ascii"))
    os.utime(p, (mtime, mtime))
    return p


def test_keeps_the_ten_newest_and_moves_the_rest(tmp_path):
    pics = tmp_path / "Pictures"
    pics.mkdir()
    for i in range(14):
        _make(pics, f"s{i:02d}_firstneedauth.png", 1_000_000 + i)
    _make(pics, "approved_wallpaper.png", 10)
    res = fp.cap_needauth_renditions(pics, keep=10)
    kept = sorted(p.name for p in pics.glob("*_firstneedauth.*"))
    assert kept == [f"s{i:02d}_firstneedauth.png" for i in range(4, 14)]
    hold = pics / fp.RENDITION_HOLD_DIR
    assert sorted(p.name for p in hold.iterdir()) == [
        f"s{i:02d}_firstneedauth.png" for i in range(4)]
    assert (pics / "approved_wallpaper.png").is_file()
    assert res == {"found": 14, "kept": 10, "moved": 4, "hold": str(hold)}


def test_moved_bytes_are_intact_and_nothing_is_deleted(tmp_path):
    pics = tmp_path / "Pictures"
    pics.mkdir()
    for i in range(3):
        _make(pics, f"a{i}_firstneedauth.png", 100 + i)
    fp.cap_needauth_renditions(pics, keep=1)
    hold = pics / fp.RENDITION_HOLD_DIR
    assert (hold / "a0_firstneedauth.png").read_bytes() == b"a0_firstneedauth.png"
    assert len(list(pics.rglob("*_firstneedauth.png"))) == 3


def test_under_the_cap_moves_nothing_and_creates_no_hold(tmp_path):
    pics = tmp_path / "Pictures"
    pics.mkdir()
    for i in range(5):
        _make(pics, f"b{i}_firstneedauth.png", 100 + i)
    res = fp.cap_needauth_renditions(pics, keep=10)
    assert res["moved"] == 0 and not (pics / fp.RENDITION_HOLD_DIR).exists()


def test_a_name_clash_in_the_hold_is_never_overwritten(tmp_path):
    pics = tmp_path / "Pictures"
    hold = pics / fp.RENDITION_HOLD_DIR
    hold.mkdir(parents=True)
    (hold / "c0_firstneedauth.png").write_bytes(b"older")
    _make(pics, "c0_firstneedauth.png", 100)
    _make(pics, "c1_firstneedauth.png", 200)
    res = fp.cap_needauth_renditions(pics, keep=1)
    assert (hold / "c0_firstneedauth.png").read_bytes() == b"older"
    assert (pics / "c0_firstneedauth.png").is_file()
    assert res["moved"] == 0 and res.get("clashes") == 1


def test_dry_run_moves_nothing(tmp_path):
    pics = tmp_path / "Pictures"
    pics.mkdir()
    for i in range(4):
        _make(pics, f"d{i}_firstneedauth.png", 100 + i)
    res = fp.cap_needauth_renditions(pics, keep=2, dry_run=True)
    assert res["moved"] == 2
    assert len(list(pics.glob("*_firstneedauth.png"))) == 4


def test_missing_folder_is_a_no_op(tmp_path):
    res = fp.cap_needauth_renditions(tmp_path / "nope", keep=10)
    assert res["found"] == 0 and res["moved"] == 0


def test_cli_cap_renditions_logs_the_count(tmp_path, monkeypatch, capsys):
    pics = tmp_path / "Pictures"
    pics.mkdir()
    for i in range(12):
        _make(pics, f"e{i:02d}_firstneedauth.png", 100 + i)
    logged = []
    monkeypatch.setattr(fp, "_log", logged.append)
    assert fp.main(["--cap-renditions", "--pictures", str(pics)]) == 0
    assert len(list(pics.glob("*_firstneedauth.png"))) == fp.RENDITION_CAP
    assert any("moved=2" in line for line in logged)
    assert "moved=2" in capsys.readouterr().out
