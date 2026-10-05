"""FLEET-COMMON item 13 a (FLEET-KIT v7): the session counter lives in the
hand-off as `SESSION: <n>`, and /done writes n+1. /done writes the hand-off
through tools/lw_next_session.py --write, so the tool stamps the line: the
author never counts by hand and a block that forgets the line still gets it.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import lw_next_session as ns  # noqa: E402

BLOCK = "NEXT SESSION\n------------\nTask: x\nContext: y\n"


def test_the_counter_is_previous_plus_one_under_the_header():
    out = ns.stamp_session(BLOCK, "NEXT SESSION\n------------\nSESSION: 63\nTask: old\n")
    assert out.splitlines()[:3] == ["NEXT SESSION", "------------", "SESSION: 64"]
    assert out.count("SESSION:") == 1


def test_an_authored_session_line_is_replaced_not_duplicated():
    out = ns.stamp_session("NEXT SESSION\n------------\nSESSION: 5\nTask: x\n",
                           "SESSION: 63\n")
    assert out.count("SESSION:") == 1 and "SESSION: 64" in out


def test_no_previous_counter_starts_at_one():
    assert "SESSION: 1" in ns.stamp_session(BLOCK, "")
    assert "SESSION: 1" in ns.stamp_session(BLOCK, None)


def test_a_block_without_the_header_gets_the_line_on_top():
    assert ns.stamp_session("Task: x\n", "SESSION: 2\n").splitlines()[0] == "SESSION: 3"


def test_main_write_stamps_the_counter(tmp_path, monkeypatch):
    target = tmp_path / "LW-NEXT-SESSION.txt"
    target.write_text("NEXT SESSION\n------------\nSESSION: 9\nTask: a\n", encoding="ascii")
    src = tmp_path / "block.txt"
    src.write_text(BLOCK, encoding="ascii")
    monkeypatch.setattr(ns, "resolve_target", lambda *a, **k: target)
    monkeypatch.setattr(ns, "compose_handoff", lambda text, engine=None: text)
    monkeypatch.setattr(ns, "write_handoff",
                        lambda text, **k: (target.write_text(text, encoding="ascii"), target)[1])
    assert ns.main(["--write", str(src)]) == 0
    assert "SESSION: 10" in target.read_text(encoding="ascii")


def test_the_live_handoff_carries_a_counter():
    text = (ROOT / "LW-NEXT-SESSION.txt").read_text(encoding="ascii")
    assert ns.SESSION_LINE.search(text), "the hand-off must carry SESSION: <n>"
