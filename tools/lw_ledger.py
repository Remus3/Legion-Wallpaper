"""The item ledger across its files: docs/LEDGER.md plus docs/ledger/YYYY-MM.md.

# arch: keeps the newest ledger entries in docs/LEDGER.md, older ones per month

WHY (MAIN 2026-11-01-1223 item 5). docs/LEDGER.md reached 1,102,356 B. It keeps
the newest KEEP entries; older entries live per month under docs/ledger/, with
an index in docs/ledger/README.md. A rotation is a MOVE: entry bytes are compared
before and after, and any difference raises before a file is written.

    python tools/lw_ledger.py rotate [--keep 20] [--root R]
    python tools/lw_ledger.py check [--root R]

Anything that needs "does item N exist" or "every entry" calls read_all(); an
item's number never changes when it moves.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER_REL = Path("docs") / "LEDGER.md"
MONTHS_DIRNAME = "ledger"
INDEX_NAME = "README.md"
KEEP = 20
ENTRY = re.compile(r"(?m)^(\d+)\. ")
DATE = re.compile(r"(\d{4}-\d{2})-\d{2}")
MONTH_FILE = re.compile(r"^\d{4}-\d{2}\.md$")


class LedgerMoveError(RuntimeError):
    """A rotation would have lost or changed an entry; nothing was written."""


def month_files(ledger: Path) -> list[Path]:
    """The month files beside `ledger`, newest month first. The index is not one."""
    folder = Path(ledger).parent / MONTHS_DIRNAME
    if not folder.is_dir():
        return []
    return sorted((p for p in folder.iterdir() if MONTH_FILE.match(p.name)), reverse=True)


def read_all(ledger: Path) -> str:
    """Every entry's text, newest first: `ledger` then its month files. A missing
    `ledger` raises OSError, which is how callers already read an absent file."""
    ledger = Path(ledger)
    parts = [ledger.read_text(encoding="utf-8", errors="replace")]
    parts += [p.read_text(encoding="utf-8", errors="replace") for p in month_files(ledger)]
    return "\n".join(parts)


def split_entries(text: str) -> tuple[str, list[tuple[int, str]]]:
    """(the text before the first entry, [(number, entry bytes as text), ...])."""
    marks = list(ENTRY.finditer(text))
    if not marks:
        return text, []
    ends = [m.start() for m in marks[1:]] + [len(text)]
    return text[:marks[0].start()], [(int(m.group(1)), text[m.start():e])
                                     for m, e in zip(marks, ends, strict=True)]


def month_of(entry: str, fallback: str) -> str:
    """The YYYY-MM of an entry's lead date, else the entry before it's month."""
    m = DATE.search(entry.split("\n", 1)[0])
    return m.group(1) if m else fallback


def digest_multiset(entries: list[tuple[int, str]]) -> list[str]:
    """Sorted hashes of each entry, trailing whitespace ignored, number included."""
    return sorted(hashlib.sha256(e.rstrip().encode("utf-8")).hexdigest() for _n, e in entries)


def all_entries(ledger: Path) -> list[tuple[int, str]]:
    out = split_entries(Path(ledger).read_bytes().decode("utf-8"))[1]
    for p in month_files(ledger):
        out += split_entries(p.read_bytes().decode("utf-8"))[1]
    return out


def _month_head(month: str) -> str:
    return (f"# Ledger {month}\n\nEntries moved verbatim from docs/LEDGER.md, newest first. "
            "Append-only: never edit an entry.\n\n")


def _write(path: Path, text: str) -> None:
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_bytes(text.encode("utf-8"))
    tmp.replace(path)


def _index(ledger: Path) -> str:
    lines = ["# Ledger index", "",
             "Newest entries: docs/LEDGER.md. Older ones, by the month of their lead date:", ""]
    for p in month_files(ledger):
        nums = [n for n, _e in split_entries(p.read_bytes().decode("utf-8"))[1]]
        lines.append(f"- {p.stem}: {len(nums)} entries, items {min(nums)} to {max(nums)} "
                     f"({p.name})")
    return "\n".join(lines) + "\n"


def rotate(ledger: Path, keep: int = KEEP) -> dict:
    """Move every entry past the newest `keep` into its month file; rewrite the index.

    Everything is composed and proven in memory first. Raises LedgerMoveError
    without writing if the entry multiset would change."""
    ledger = Path(ledger)
    before = all_entries(ledger)
    head, entries = split_entries(ledger.read_bytes().decode("utf-8"))
    stay, move = entries[:keep], entries[keep:]
    folder = ledger.parent / MONTHS_DIRNAME
    groups: dict[str, list[str]] = {}
    fallback = "0000-00"
    for _n, entry in reversed(move):            # oldest first, so a fallback is earlier
        fallback = month_of(entry, fallback)
        groups.setdefault(fallback, []).insert(0, entry)
    out: dict[Path, str] = {}
    for month, moved in groups.items():
        path = folder / f"{month}.md"
        old = path.read_bytes().decode("utf-8") if path.exists() else ""
        old_head, old_entries = split_entries(old)
        body = "".join(e if e.endswith("\n") else e + "\n" for e in moved)
        out[path] = (old_head or _month_head(month)) + body + "".join(e for _n, e in old_entries)
    new_ledger = head + "".join(e for _n, e in stay)
    after = split_entries(new_ledger)[1]
    untouched = [p for p in month_files(ledger) if p not in out]
    for p in untouched:
        after += split_entries(p.read_bytes().decode("utf-8"))[1]
    for text in out.values():
        after += split_entries(text)[1]
    if digest_multiset(before) != digest_multiset(after):
        raise LedgerMoveError(f"entries before {len(before)}, after {len(after)}: not written")
    folder.mkdir(parents=True, exist_ok=True)
    for path, text in out.items():
        _write(path, text)
    _write(ledger, new_ledger)
    if month_files(ledger):
        _write(folder / INDEX_NAME, _index(ledger))
    final = all_entries(ledger)
    if digest_multiset(before) != digest_multiset(final):
        raise LedgerMoveError(f"read-back: before {len(before)}, after {len(final)}")
    return {"before": len(before), "after": len(final), "moved": len(move),
            "kept": len(stay), "months": len(groups)}


def check(ledger: Path) -> list[str]:
    """Problems with the split as it stands: an entry filed twice, or an index
    that does not match its month files."""
    ledger = Path(ledger)
    problems = []
    nums = [n for n, _e in all_entries(ledger)]
    dupes = sorted({n for n in nums if nums.count(n) > 1}) if len(set(nums)) != len(nums) else []
    if dupes:
        problems.append(f"item numbers filed more than once: {dupes[:20]}")
    index = ledger.parent / MONTHS_DIRNAME / INDEX_NAME
    if month_files(ledger) and (not index.exists()
                                or index.read_bytes().decode("utf-8") != _index(ledger)):
        problems.append(f"{INDEX_NAME} does not match the month files: run rotate")
    return problems


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("cmd", choices=["rotate", "check"])
    ap.add_argument("--keep", type=int, default=KEEP)
    ap.add_argument("--root", type=Path, default=ROOT)
    args = ap.parse_args(argv)
    ledger = args.root / LEDGER_REL
    if args.cmd == "rotate":
        print(json.dumps(rotate(ledger, args.keep)))
        return 0
    problems = check(ledger)
    print(json.dumps({"problems": problems, "entries": len(all_entries(ledger))}))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
