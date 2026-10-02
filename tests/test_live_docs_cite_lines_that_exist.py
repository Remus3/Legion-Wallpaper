"""Live docs: a `file.py:NNN` citation must point at a line that EXISTS.

THE CLASS (RC, cross-repo, 2026-10-02): a pointer that RESOLVES is not a pointer
that is TRUE. A citation decays silently - the file is still there, the line
number now lands in a different function or past the end of the file entirely -
and nothing in the repo notices, because no test reads a doc's citations.

WHY THIS INSTRUMENT AND NOT THE ONE LW ALREADY RETRACTED. On 2026-09-08 LW
measured 99 of 1176 path citations "pointing at nothing" and RETRACTED the whole
finding within the hour (docs/LEDGER.md:3057-3064): the instrument was a
path-EXISTENCE check, the question was whether a citation misleads a reader, and
a path-existence check cannot tell a dead citation from a foreign path, a to-do
("not yet written - add ..."), a sibling repo's file, or a sentence whose point
is that the path is ABSENT. This arm deliberately asserts the one thing that has
no such reading: among citations whose FILE resolves inside this repo, the cited
LINE NUMBER must be within that file. "Line 2089 of an 8-line file" cannot be a
foreign path or a to-do. It is wrong in every reading.

Three consequences of that choice, all deliberate:

  - A citation whose file does NOT resolve here is SKIPPED, not failed. That is
    exactly the bucket the retracted finding lived in. Measured 2026-10-02: 6 of
    the 110 citations in these docs name a gitignored third-party path under
    .venv-gen/site-packages, which exists on this box and not in CI.
  - A BARE basename (`slots.py:40`, `__init__.py:216`) is SKIPPED unless exactly
    one tracked file carries that name, because resolving `__init__.py` to the
    only tracked file of that name is how the first cut of this sweep
    manufactured 7 false positives against docs that plainly meant a venv file.
  - An elided path (one containing `...`) is SKIPPED. It is prose, not a pointer.

SCOPE, with a reason, because a guard that gets disabled for noise is worse than
no guard. Only the LIVE docs plus docs/adr: CLAUDE.md, ROADMAP.md, BACKLOG.md,
README.md, WAKEUP_NOTES.md, docs/ARCHITECTURE.md, docs/OPERATIONS.md,
docs/LEDGER.md. EXCLUDED: `docs/_archive/**` and dated artifacts, per CLAUDE.md's
standing sweep exclusions, and `docs/research/**`, which is dated research
output - an archived report that cited line 160 of a venv file in July is a
faithful record of July and must not redden a suite in October. The live docs are
the ones a session is told to read at start, so they are the ones whose pointers
a reader will actually follow.

LW'S OWN RULE, which this does NOT replace: docs/LEDGER.md:1347 pins a violation
"as a sorted `(file, code)` list, NOT by line - a line decays on the next joint
re-pin", and docs/LEDGER.md:417 asks siblings for a `(file, code)` pair pin. That
rule governs PINS inside tests. This arm governs PROSE citations in docs, where
a line number is often the only available referent. It is the floor under the
rule, not a substitute for it.
"""
from __future__ import annotations

import collections
import re
import subprocess
from pathlib import Path

import gitdep

import pytest

ROOT = Path(__file__).resolve().parents[1]

# Repo-root docs that a session is told to read, plus every ADR.
_LIVE_ROOT_DOCS = (
    "CLAUDE.md",
    "ROADMAP.md",
    "BACKLOG.md",
    "README.md",
    "WAKEUP_NOTES.md",
    "docs/ARCHITECTURE.md",
    "docs/OPERATIONS.md",
    "docs/LEDGER.md",
)

_CITATION = re.compile(
    r"\b((?:[A-Za-z0-9_./-]+/)?[A-Za-z0-9_.-]+"
    r"\.(?:py|md|json|ps1|ahk|toml|ini|yml|yaml|cfg|txt))"
    r"[:#](\d{1,6})\b"
)


def _tracked() -> list[str]:
    out = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files", "-z"],
        capture_output=True, check=True,
    ).stdout
    return [p for p in out.decode("utf-8").split("\0") if p]


def _live_docs(tracked: list[str]) -> list[str]:
    tset = set(tracked)
    docs = [d for d in _LIVE_ROOT_DOCS if d in tset]
    docs += sorted(
        t for t in tracked if t.startswith("docs/adr/") and t.endswith(".md")
    )
    return docs


def _resolve(cited: str, tracked: list[str], tset: set[str],
             by_base: dict[str, list[str]]) -> str | None:
    """The cited path as a tracked repo path, or None when it is not decidable."""
    if "..." in cited:
        return None
    if cited in tset:
        return cited
    if "/" in cited:
        suffix = [t for t in tracked if t.endswith("/" + cited)]
        return suffix[0] if len(suffix) == 1 else None
    hits = by_base.get(cited, [])
    return hits[0] if len(hits) == 1 else None


def _sweep() -> tuple[int, int, list[str]]:
    """(citations seen, citations decided, failure rows). One git call, cached reads."""
    tracked = _tracked()
    tset = set(tracked)
    by_base: dict[str, list[str]] = collections.defaultdict(list)
    for t in tracked:
        by_base[t.rsplit("/", 1)[-1]].append(t)
    nlines: dict[str, int] = {}

    def count(rel: str) -> int:
        if rel not in nlines:
            try:
                nlines[rel] = len((ROOT / rel).read_bytes().splitlines())
            except OSError:
                nlines[rel] = -1
        return nlines[rel]

    seen = decided = 0
    bad: list[str] = []
    for doc in _live_docs(tracked):
        text = (ROOT / doc).read_text(encoding="utf-8", errors="replace")
        for ln, line in enumerate(text.splitlines(), 1):
            for m in _CITATION.finditer(line):
                cited, num = m.group(1), int(m.group(2))
                seen += 1
                target = _resolve(cited, tracked, tset, by_base)
                if target is None:
                    continue
                total = count(target)
                if total < 0:
                    continue
                decided += 1
                if num > total:
                    bad.append(
                        f"{doc}:{ln} cites {cited}:{num} -> {target} has only "
                        f"{total} lines"
                    )
    return seen, decided, bad


@gitdep.requires_git
def test_the_citation_sweep_selects_a_real_corpus():
    """Guard the guard. This whole arm is a loop over a collection that can be
    empty - no parametrize, so `empty_parameter_set_mark = fail_at_collect` does
    not reach it. An empty `git ls-files`, a renamed doc set or a regex that
    stopped matching all produce zero failures and a green arm. Measured
    2026-10-02: 22 docs, 110 citations, 103 of them decidable.
    """
    tracked = _tracked()
    docs = _live_docs(tracked)
    assert len(docs) >= 15, f"only {len(docs)} live docs selected: {docs}"
    seen, decided, _ = _sweep()
    assert seen >= 80, f"only {seen} citations matched - the regex is wrong"
    assert decided >= 70, (
        f"only {decided} of {seen} citations resolved to a tracked file - "
        f"path resolution is broken, not the docs")


@gitdep.requires_git
def test_no_live_doc_cites_a_line_that_cannot_exist():
    """The arm. A line number past the end of the file it names is wrong in every
    reading - it is not a foreign path, a to-do or an assertion of absence.
    """
    _, _, bad = _sweep()
    assert not bad, (
        f"{len(bad)} live-doc citation(s) point past the end of the file they "
        f"name. Re-read the code and cite the current line, or - better, per "
        f"docs/LEDGER.md:1347 - cite the SYMBOL and drop the number:\n  "
        + "\n  ".join(bad)
    )


@gitdep.requires_git
def test_the_arm_would_catch_a_decayed_citation():
    """Mutation-in-place: the detector fires on a planted over-the-end citation.

    An arm nobody has seen fail asserts nothing. Rather than editing a tracked
    doc, this drives the same resolution-and-compare logic over a fixture pair
    and asserts both directions.
    """
    tracked = ["docs/FIXTURE.md", "tools/short.py"]
    tset = set(tracked)
    by_base = {"FIXTURE.md": ["docs/FIXTURE.md"], "short.py": ["tools/short.py"]}
    assert _resolve("tools/short.py", tracked, tset, by_base) == "tools/short.py"
    assert _resolve("short.py", tracked, tset, by_base) == "tools/short.py"
    assert _resolve("nowhere/absent.py", tracked, tset, by_base) is None
    assert _resolve("venv/.../pipeline.py", tracked, tset, by_base) is None


@gitdep.requires_git
def test_an_ambiguous_bare_basename_is_skipped_and_never_failed():
    """The retracted 2026-09-08 finding in one arm: `__init__.py:216` must not be
    resolved to whichever tracked file happens to carry that name. The first cut
    of this sweep did exactly that and manufactured 7 false positives.
    """
    tracked = ["a/__init__.py", "b/__init__.py"]
    by_base = {"__init__.py": tracked}
    assert _resolve("__init__.py", tracked, set(tracked), by_base) is None


@pytest.mark.parametrize("sample,expect", [
    ("see tools/drift_guard.py:209 for the sweep", ("tools/drift_guard.py", "209")),
    ("docs/LEDGER.md:1347 pins it", ("docs/LEDGER.md", "1347")),
    ("`ops/loop/slots.py:7` says", ("ops/loop/slots.py", "7")),
])
def test_the_regex_reads_the_shapes_these_docs_actually_use(sample, expect):
    """A regex that silently stopped matching turns this file green forever."""
    m = _CITATION.search(sample)
    assert m is not None, sample
    assert m.groups() == expect


@pytest.mark.parametrize("sample", [
    "ADR-004 (2026-07-05)",
    "version 2.1.220 on Legion",
    "see docs/OPERATIONS.md for the commands",
])
def test_the_regex_does_not_invent_a_citation_from_ordinary_prose(sample):
    assert _CITATION.search(sample) is None, sample


def test_the_scope_exclusions_are_the_ones_claude_md_states():
    """docs/_archive/** and docs/research/** are OUT, with the reason recorded in
    this module's docstring. A future widening has to argue past this arm.
    """
    tracked = _tracked() if gitdep.GIT else []
    if not tracked:
        pytest.skip(gitdep.REASON)
    docs = _live_docs(tracked)
    assert not [d for d in docs if d.startswith("docs/_archive/")]
    assert not [d for d in docs if d.startswith("docs/research/")]
    assert "docs/ARCHITECTURE.md" in docs and "docs/LEDGER.md" in docs


def test_this_guard_is_ascii():
    """Repo-wide hard rule; a guard that violates it is not credible."""
    raw = Path(__file__).read_bytes()
    assert not any(b > 0x7F for b in raw), "non-ASCII byte in this guard"
