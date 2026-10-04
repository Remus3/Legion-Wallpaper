"""Failure catalogues: every tool's skill doc ends with real failures (P2-8).

Each major tool's command doc carries a "## Failure catalogue" table:
symptom | cause | how it was caught | fix | LEDGER. Every row traces to a real
failure, so every row cites at least one LEDGER item, and every cited item
must exist in docs/LEDGER.md. drift_guard runs `check()`.

The catalogue lives in the tool's own doc, never in CLAUDE.md (CI size budget).
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "docs" / "LEDGER.md"
HEADING = "## Failure catalogue"
COLUMNS = ["symptom", "cause", "how it was caught", "fix", "ledger"]
MIN_ROWS = 5

# tool -> the doc that carries its catalogue
CATALOGUES = {
    "cleaning lane": ROOT / ".claude" / "commands" / "cleaning-pass.md",
    "first pass": ROOT / ".claude" / "commands" / "first-pass.md",
    "source recovery": ROOT / ".claude" / "commands" / "intake.md",
}


def ledger_ids(ledger=LEDGER):
    try:
        text = Path(ledger).read_text(encoding="utf-8")
    except OSError:
        return set()
    return {int(m.group(1)) for m in re.finditer(r"(?m)^(\d+)\. ", text)}


def parse_table(text):
    """Rows of the first table under HEADING, or None when absent."""
    i = text.find(HEADING)
    if i < 0:
        return None
    rows = []
    started = False
    for line in text[i:].splitlines()[1:]:
        if line.startswith("## "):
            break
        if line.startswith("|"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if not started:
                started = True
                header = [c.lower() for c in cells]
                if header != COLUMNS:
                    return {"header": header, "rows": []}
                continue
            if set("".join(cells)) <= set("-: "):
                continue
            rows.append(cells)
        elif started and line.strip() == "":
            if rows:
                break
    return {"header": COLUMNS, "rows": rows}


def check(catalogues=None, ledger=LEDGER):
    """Problems ([] when every catalogue is present, well formed, cites real items)."""
    catalogues = CATALOGUES if catalogues is None else catalogues
    ids = ledger_ids(ledger)
    problems = []
    for tool, path in catalogues.items():
        try:
            text = Path(path).read_text(encoding="utf-8")
        except OSError:
            problems.append(f"{tool}: catalogue doc missing ({Path(path).name})")
            continue
        table = parse_table(text)
        if table is None:
            problems.append(f"{tool}: no '{HEADING}' section in {Path(path).name}")
            continue
        if table["header"] != COLUMNS:
            problems.append(f"{tool}: catalogue columns must be {COLUMNS}")
            continue
        if len(table["rows"]) < MIN_ROWS:
            problems.append(f"{tool}: {len(table['rows'])} rows (< {MIN_ROWS})")
        for n, cells in enumerate(table["rows"], 1):
            if len(cells) != len(COLUMNS) or not all(cells):
                problems.append(f"{tool}: row {n} has an empty or missing cell")
                continue
            cited = [int(x) for x in re.findall(r"\d+", cells[-1])]
            if not cited or not cells[-1].upper().startswith("LEDGER"):
                problems.append(f"{tool}: row {n} cites no LEDGER item")
            for c in cited:
                if c not in ids:
                    problems.append(f"{tool}: row {n} cites LEDGER {c}, which does not exist")
    return problems


if __name__ == "__main__":
    import sys
    found = check()
    for p in found:
        print("  " + p)
    print(f"failure catalogues: {'OK' if not found else 'BREACH'}")
    sys.exit(1 if found else 0)
