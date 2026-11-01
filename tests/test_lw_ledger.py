"""The ledger split (MAIN 2026-11-01-1223 item 5): a rotation is a move, never a loss."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import lw_failure_catalogue  # noqa: E402
import lw_gate_board  # noqa: E402
import lw_ledger as ll  # noqa: E402
import repo_insights  # noqa: E402

HEAD = "# Ledger\n\nPreamble with 1. not an entry mid line.\n\n---\n\n"


def _entry(n: int, date: str) -> str:
    return f"{n}. DONE **{date} - item {n}.** Body\n   more body for {n}.\n\n"


def _tree(tmp_path: Path, rows: list[tuple[int, str]]) -> Path:
    ledger = tmp_path / "docs" / "LEDGER.md"
    ledger.parent.mkdir(parents=True)
    ledger.write_bytes((HEAD + "".join(_entry(n, d) for n, d in rows)).encode("ascii"))
    return ledger


ROWS = [(6, "2026-11-01"), (5, "2026-10-30"), (4, "2026-10-02"), (3, "2026-09-30"),
        (2, "2026-09-01"), (1, "2026-08-31")]


def test_rotate_moves_each_old_entry_to_its_month_and_keeps_the_newest(tmp_path):
    ledger = _tree(tmp_path, ROWS)
    res = ll.rotate(ledger, keep=2)
    assert res == {"before": 6, "after": 6, "moved": 4, "kept": 2, "months": 3}
    assert ledger.read_text(encoding="ascii") == HEAD + _entry(6, "2026-11-01") + _entry(5, "2026-10-30")
    folder = ledger.parent / "ledger"
    assert sorted(p.name for p in folder.iterdir()) == [
        "2026-08.md", "2026-09.md", "2026-10.md", "README.md"]
    assert _entry(3, "2026-09-30") + _entry(2, "2026-09-01") in (folder / "2026-09.md").read_text(
        encoding="ascii"), "newest first inside a month"


def test_rotate_keeps_every_entry_byte(tmp_path):
    ledger = _tree(tmp_path, ROWS)
    before = ll.digest_multiset(ll.all_entries(ledger))
    ll.rotate(ledger, keep=1)
    assert ll.digest_multiset(ll.all_entries(ledger)) == before


def test_a_second_rotation_prepends_into_an_existing_month(tmp_path):
    ledger = _tree(tmp_path, ROWS)
    ll.rotate(ledger, keep=2)
    res = ll.rotate(ledger, keep=1)
    assert res["moved"] == 1
    text = (ledger.parent / "ledger" / "2026-10.md").read_text(encoding="ascii")
    assert text.index("5. DONE") < text.index("4. DONE")
    assert text.count("# Ledger 2026-10") == 1
    assert ll.check(ledger) == []


def test_a_rotation_that_would_lose_an_entry_writes_nothing(tmp_path, monkeypatch):
    ledger = _tree(tmp_path, ROWS)
    original = ledger.read_bytes()
    real = ll.digest_multiset
    calls = []

    def _lossy(entries):
        calls.append(1)
        return real(entries) + (["lost"] if len(calls) == 1 else [])

    monkeypatch.setattr(ll, "digest_multiset", _lossy)
    with pytest.raises(ll.LedgerMoveError):
        ll.rotate(ledger, keep=2)
    assert ledger.read_bytes() == original
    assert not (ledger.parent / "ledger").exists()


def test_an_undated_entry_files_with_the_entry_before_it(tmp_path):
    ledger = tmp_path / "docs" / "LEDGER.md"
    ledger.parent.mkdir(parents=True)
    ledger.write_bytes((HEAD + _entry(3, "2026-10-01") + "2. DONE **no date here.** x\n\n"
                        + _entry(1, "2026-09-01")).encode("ascii"))
    ll.rotate(ledger, keep=1)
    assert "2. DONE" in (ledger.parent / "ledger" / "2026-09.md").read_text(encoding="ascii")


def test_check_reports_a_duplicate_and_a_stale_index(tmp_path):
    ledger = _tree(tmp_path, ROWS)
    ll.rotate(ledger, keep=2)
    assert ll.check(ledger) == []
    month = ledger.parent / "ledger" / "2026-10.md"
    month.write_bytes(month.read_bytes() + _entry(6, "2026-10-01").encode("ascii"))
    assert len(ll.check(ledger)) == 2


def test_the_readers_still_see_a_moved_item(tmp_path, monkeypatch):
    ledger = _tree(tmp_path, ROWS)
    ll.rotate(ledger, keep=2)
    assert 1 in lw_failure_catalogue.ledger_ids(ledger)
    assert 1 in lw_gate_board._ledger_ids(ledger)
    monkeypatch.setattr(repo_insights, "ROOT", tmp_path)
    got = repo_insights.parse_ledger("2026-08-01")
    assert got["latest_item"] == 6
    assert {n for n, _d, _t in got["items_in_window"]} == {1, 2, 3, 4, 5, 6}


def test_the_live_split_is_consistent():
    ledger = ROOT / "docs" / "LEDGER.md"
    assert ll.check(ledger) == []
    nums = [n for n, _e in ll.all_entries(ledger)]
    assert max(nums) >= 358 and len(nums) == len(set(nums))
    assert len(ll.split_entries(ledger.read_bytes().decode("utf-8"))[1]) < 60, "run rotate"
