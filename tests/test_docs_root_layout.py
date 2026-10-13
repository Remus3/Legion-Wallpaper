"""RRF-3.3 (MAIN README-AUDIT 3.3): dated one-off reports live in docs/_archive/.

MAIN's 2026-10-08 audit counted 97 files in docs/ root, 71 of them dated one-off
reports. They now sit in docs/_archive/<yyyy-mm>/ (yyyy-mm from the date in the
file name); docs/ root keeps the standing docs. STANDING lists the four dated
files that are still live work, each with the reason; it may only shrink.

Every `docs/...md` path cited by a tracked file must still resolve, so a move
never leaves a dangling pointer behind (the consumer check, made permanent).
"""
from __future__ import annotations

import re

import gitdep
import tracked_corpus

DATED = re.compile(r"^docs/[^/]*(\d{4})-(\d{2})-\d{2}[^/]*$")

# Dated by name, standing by use. Reason recorded per file.
STANDING = {
    "docs/RUNDASH_SPEC_2026-08-01.md": "live spec: cited by tools/lw_rundash*.py and 6 tests",
    "docs/REPO_REVIEW_PLAN_2026-10-08.md": "plan for the open REPO-REVIEW-DRIVER hand-off item",
    "docs/HANDCLEAN_WORKLIST_2026-09-01.md": "open hand-clean worklist cited by the hand-off",
    "docs/NEXT_SESSION_PARKED_2026-09-10.md": "parked pipeline-queue prompt kept to resume (WAKEUP_NOTES)",
}

# Cited before it exists: the output a still-open item will write.
PENDING = {
    "docs/REPO_REVIEW_FINDINGS_2026-10-08.md": "output of the REPO-REVIEW-DRIVER, not yet written",
}

_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")
_CITED = re.compile(r"\bdocs/[A-Za-z0-9_./-]+?\.md\b")


@gitdep.requires_git
def test_no_dated_one_off_report_sits_in_docs_root():
    root_dated = [f for f in tracked_corpus.tracked_files() if DATED.match(f)]
    stray = sorted(set(root_dated) - set(STANDING))
    assert not stray, f"move to docs/_archive/<yyyy-mm>/: {stray}"


@gitdep.requires_git
def test_every_standing_exception_still_exists():
    files = set(tracked_corpus.tracked_files())
    assert set(STANDING) <= files, sorted(set(STANDING) - files)


@gitdep.requires_git
def test_every_cited_docs_path_resolves():
    files = tracked_corpus.tracked_files()
    tracked = set(files)
    dangling = []
    for rel in files:
        # tests/ is skipped: its dated paths are often RULE INPUTS (a skip or
        # exemption arm fed a docs-root spelling on purpose), not citations.
        if (rel.startswith(("docs/_archive/", "tests/"))
                or not rel.endswith((".md", ".py", ".txt", ".json"))):
            continue
        try:
            text = tracked_corpus.read_text(rel, errors="replace")
        except OSError:
            continue
        for m in _CITED.finditer(text):
            path = m.group(0)
            if _DATE.search(path) and path not in tracked and path not in PENDING:
                dangling.append(f"{rel}: {path}")
    assert not dangling, "cited dated doc does not exist: " + ", ".join(dangling[:30])
