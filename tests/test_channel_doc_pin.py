r"""LW's pin on the vendored cross-repo channel doc, `docs/CHANNEL.md`.

The doc is byte-identical in every participating repository at the same
relative path, and section 9 makes the pin a JOINT act: a byte change without a
CHANNEL_VERSION bump, or a bump without a re-pin, is red by construction
because this file binds the two together.

Two deliberate choices, both taken from the doc's own section 9:

  * the digest is over LF-NORMALISED bytes, never raw bytes, because not every
    participating tree pins markdown to LF in its attributes file and a
    raw-byte pin would go red in a tree whose working copy checks out CRLF even
    though all five git blobs are identical;
  * the zero-CR arm is nevertheless VALID in this tree, and only in a tree that
    took that step: LW's `.gitattributes` carries `*.md text eol=lf`, which the
    doc names as the precondition for arming it.

This file imports STDLIB AND PYTEST ONLY, on purpose. The doc is the shared
artifact of five trees; a pin that reached into LW's own tooling would grade
the vendored bytes against a local module that no other tree carries, and a
change to that module could turn the pin red or green without a byte of the doc
moving. The date regex in the heading arm is written out inline here for the
same reason - LW's arm is the plain regex, not a sweep module's opinion.
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DOC_REL = "docs/CHANNEL.md"
DOC = ROOT / "docs" / "CHANNEL.md"

# Pinned over the LF-normalised bytes. Moving either constant without the other
# is the red-by-construction case section 9 describes.
PINNED_SHA256 = "899f6eb957cc26ee25993d83d65d8ca291841fe4eec24a48f729c2dc005f4c6b"
PINNED_CHANNEL_VERSION = 1

# Repo-relative path shapes the doc may name. A span only counts as a path
# claim if it carries a separator AND either sits under a known top-level
# directory or ends in a file extension - a bare note filename, a `pid:` label
# or a `%LOCALAPPDATA%\...` machine path is not a repo-relative claim.
KNOWN_TOP_DIRS = (
    "docs/", "tools/", "tests/", "ops/", "images/", "data/",
    ".claude/", ".githooks/",
)

# ISO date and ISO date-time, written out inline rather than imported.
DATE_IN_TEXT = re.compile(r"\d{4}-\d{2}-\d{2}(?:T\d{2}:\d{2}(?::\d{2})?)?")

# A `path.ext:123` citation of any kind. The doc states its own reason for
# refusing these: the directory those notes live in is gitignored, so a line
# cite into it resolves in no tree at all.
FILE_LINE_CITE = re.compile(
    r"[A-Za-z0-9_./\\-]+\.(?:py|md|ps1|json|toml|txt|yml|yaml|ahk):\d+")


def _raw() -> bytes:
    return DOC.read_bytes()


def _lf_bytes() -> bytes:
    return _raw().replace(b"\r\n", b"\n")


def _text() -> str:
    return _lf_bytes().decode("ascii")


def _backtick_spans(text: str) -> list[str]:
    return re.findall(r"`([^`\n]+)`", text)


def _looks_like_repo_path(span: str) -> bool:
    if "/" not in span:
        return False
    if "<" in span or ">" in span or "%" in span:
        return False
    if span.startswith(KNOWN_TOP_DIRS):
        return True
    return bool(re.search(r"\.[A-Za-z0-9]{1,5}$", span))


# ---- 1. the file is where every tree agrees it is ---------------------------

def test_the_channel_doc_exists_at_the_agreed_relative_path():
    """Section 9 pins the PATH as well as the bytes: `docs/CHANNEL.md`.

    Derived from the repo root, never from an absolute path, so the arm means
    the same thing in a worktree and on another box.
    """
    assert DOC.is_file(), (
        f"the vendored channel doc is missing at {DOC_REL} (looked under "
        f"{ROOT})")


# ---- 2. the joint pin -------------------------------------------------------

def test_the_lf_normalised_digest_matches_the_pinned_value():
    """The digest all five trees hash from their OWN disk."""
    got = hashlib.sha256(_lf_bytes()).hexdigest()
    assert got == PINNED_SHA256, (
        "the channel doc's LF-normalised digest moved.\n"
        f"  pinned: {PINNED_SHA256}\n"
        f"  on disk: {got}\n"
        "A byte change is a five-tree re-pin round, not a local edit - see "
        "section 9 of the doc.")


# ---- 3. the zero-CR arm, valid because .gitattributes earns it --------------

def test_the_working_copy_carries_no_carriage_returns():
    """Armed only because LW's `.gitattributes` carries `*.md text eol=lf`.

    A tree without that rule would see its working copy check out CRLF and this
    arm would be red on bytes that are nevertheless identical in git - which is
    exactly why the DIGEST above normalises and this arm is a separate, local,
    opt-in claim.
    """
    n_cr = _raw().count(b"\r")
    assert n_cr == 0, (
        f"{n_cr} CR bytes in {DOC_REL}: the working copy checked out CRLF, so "
        "LW's `*.md text eol=lf` attribute is not in force")


# ---- 4. the version, bound to the digest above ------------------------------

def test_the_declared_channel_version_parses_and_matches_the_pin():
    """The bump half of the binding. The doc declares its own version."""
    m = re.search(r"^CHANNEL_VERSION:\s*(\d+)\s*$", _text(), re.MULTILINE)
    assert m is not None, (
        "no `CHANNEL_VERSION: <int>` line in the doc - the version half of the "
        "pin cannot be read, so a bump could land unnoticed")
    got = int(m.group(1))
    assert got == PINNED_CHANNEL_VERSION, (
        f"CHANNEL_VERSION is {got}, pinned at {PINNED_CHANNEL_VERSION}. A bump "
        "and a re-pin travel together.")


# ---- 5. no dated headings ---------------------------------------------------

def test_no_heading_carries_a_date():
    """A dated heading rots: the doc outlives the date and reads stale.

    Measured dates in the BODY are fine and the doc carries several (section 7
    cites a measurement date on purpose). It is the structural headings that
    must stay evergreen.
    """
    offenders = []
    for n, line in enumerate(_text().split("\n"), start=1):
        if not line.startswith("#"):
            continue
        hit = DATE_IN_TEXT.search(line)
        if hit:
            offenders.append(f"  line {n}: {line.strip()!r} (matched "
                             f"{hit.group(0)!r})")
    assert not offenders, (
        "heading lines carry dates:\n" + "\n".join(offenders))


# ---- 6. every path it names resolves, and it cites no file:line -------------

def test_every_repo_relative_path_the_doc_names_resolves_on_disk():
    """MEASURED, not assumed - and the scope is stated rather than silent.

    The doc is authored by another tree, so it can name paths that exist there
    and not here. Running the extraction over the vendored bytes gives exactly
    ONE span that looks like a repo-relative path claim: `docs/CHANNEL.md`,
    the doc's own agreed location, which resolves in LW. Every other backtick
    span is a bare note filename (no separator, and those notes live in a
    gitignored inbox by design), a grammar placeholder with `<...>`, a
    `%LOCALAPPDATA%` machine path, or a label such as `pid:` - none of which is
    a claim about a file in THIS repository, so none is asserted on.

    The one path the doc names WITHOUT a separator and which does NOT resolve
    in LW is `CROSS_REPO_CONVERGENCE_CHARTER.md` (section 9's provenance line
    calls it tracked; in LW it exists only as a note inside the gitignored
    inbox). It is out of scope here not to dodge it but because a bare
    filename is not a repo-relative path claim - the doc's own rule 12 is that
    provenance is cited by BARE filename precisely because a path into the
    inbox resolves in no tree.
    """
    text = _text()
    spans = _backtick_spans(text)
    candidates = sorted({s for s in spans if _looks_like_repo_path(s)})

    # Guard the guard, REPAIRED 2026-09-16 on CS's finding (note
    # 1c0be827c496). The old guard was `assert candidates` - non-empty. It was
    # satisfied by a SELF-REFERENCE: the only span the extraction yields is
    # `docs/CHANNEL.md`, the doc's own agreed location, which resolves because
    # the test just read it. A guard whose only witness is the file under test
    # cannot fire, so it asserted nothing. Measured before the repair:
    # candidates == ["docs/CHANNEL.md"], count 1.
    #
    # Pinning the resolved set - CS's first option - says out loud what this
    # arm actually covers, and turns a silent broadening or breakage of the
    # extraction into a red test instead of a guard that keeps passing.
    assert candidates == [SELF_PATH], (
        f"the extracted candidate set moved: {candidates} (pinned: "
        f"[{SELF_PATH!r}]). Either the extraction broke - in which case the "
        "assertion below is vacuous - or the doc now names a repo-relative "
        "path it did not before, which needs reading before this pin moves.")

    missing = [c for c in candidates if not (ROOT / c).exists()]
    assert not missing, (
        "the doc names repo-relative paths that do not resolve in LW: "
        f"{missing} (extracted candidates: {candidates})")

    # The other half of the same claim: a `file.py:123` cite decays on the next
    # edit of the file it names and cannot be re-grounded.
    hits = FILE_LINE_CITE.findall(text)
    assert not hits, (
        f"the doc carries file:line citations {hits} - a line cite rots on the "
        "next edit of the file it names")


# The doc's own agreed location - the single repo-relative path it names.
# Arm 6 pins its extracted candidate set to exactly this (see that arm).
SELF_PATH = "docs/CHANNEL.md"

# The grammar table, pinned cell by cell. This is the vector source every
# porting tree reads its grammar cases out of, so a moved cell changes what
# four other trees test. Generated from the doc and then frozen; re-pin only
# together with the digest, never to make a red test go green.
EXPECTED_TABLE = [
    ['`2026-09-15-0930-from-RC-FYI-example-topic.md`', 'ADMIT', 'routes', 'any entry', 'no responder', 'no responder', 'PRIMARY'],
    ['`2026-09-15-from-RC-FYI-example-topic.md`', 'REFUSE', 'routes', 'any entry', 'no responder', 'no responder', 'Variant A'],
    ['`from-RC-2026-09-15-0930-FYI-example-topic.md`', 'REFUSE', 'zero destinations', 'any entry', 'no responder', 'no responder', 'Variant B'],
    ['`2026-09-15-0930-from-RC-FYI-example-topic.txt`', 'REFUSE', 'routes', 'any entry', 'no responder', 'no responder', 'Variant C'],
]


# ---- 7. the filename-variant table, the grammar's test-vector source --------

def _variant_table_rows() -> tuple[list[list[str]], list[list[str]]]:
    """(data rows with the header dropped, separator rows seen)."""
    text = _text()
    start = text.find("### Filename grammar table")
    if start < 0:
        return [], []
    body = text[start:]
    rows: list[list[str]] = []
    separators: list[list[str]] = []
    seen_pipe = False
    for line in body.split("\n"):
        stripped = line.strip()
        if not stripped.startswith("|"):
            if seen_pipe and rows:
                break  # the table ended
            continue
        seen_pipe = True
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if all(set(c) <= set("-: ") for c in cells):
            separators.append(cells)
            continue  # the separator row
        rows.append(cells)
    # Dropping rows[0] as "the header" is only correct if a separator was
    # actually seen. Delete the separator and the header silently becomes the
    # dropped row, the four data rows shift up, and a cell-for-cell pin still
    # matches - which is exactly how this parser passed CS's separator-deletion
    # mutation while CS's own arm caught it (measured 2026-09-16). Returning
    # the separators lets the arm assert the table is still a table.
    return (rows[1:] if rows else []), separators


def test_the_filename_variant_table_is_present_and_parses():
    """This table is where the grammar's test vectors come from.

    Each row pairs a synthetic example filename with the SHAPE it belongs to,
    so a tree building a grammar arm reads its cases out of here rather than
    inventing them. If the table stops parsing, that source is gone silently.
    """
    rows, separators = _variant_table_rows()
    assert len(separators) == 1, (
        f"the grammar table has {len(separators)} separator rows, expected 1 - "
        "without exactly one, dropping rows[0] as the header is not sound and "
        "the cell pin below can match a table that shifted up")
    assert rows, (
        "the `### Filename grammar table` section is missing or its rows no "
        "longer parse")

    # REPAIRED 2026-09-16 on CS's finding (note 1c0be827c496). The old arm
    # graded the example prefix and the distinctness of shapes, and nothing
    # else. Measured by replaying CS's six mutations against it: it caught 2 of
    # 6. It passed a SWAP of two variant rows' example names, a flip of the
    # PRIMARY row's verdict from ADMIT to REFUSE, a blanking of all four
    # responder columns, and - unlike CS's own arm, which caught this one - the
    # deletion of the separator row. An arm whose stated job is to pin the
    # grammar's test-vector source has to grade the vectors.
    #
    # The row COUNT is asserted BEFORE the content compare, so a table that
    # lost a row fails on the count rather than on a confusing per-cell diff.
    assert len(rows) == len(EXPECTED_TABLE), (
        f"the grammar table has {len(rows)} rows, pinned at "
        f"{len(EXPECTED_TABLE)}: {rows}")
    assert rows == EXPECTED_TABLE, (
        "the grammar table's cells moved. This table is the vector source a "
        "grammar arm reads its cases out of, so a changed cell changes what "
        "every porting tree tests. Diff it against the pin and move the pin "
        "deliberately, together with the digest, or not at all.")

    # The shape claims the pin implies, kept as named assertions so the reason
    # the table earns its keep survives a future re-pin: it has to carry the
    # accepted shape AND at least one shape a responder refuses - the two
    # answers any grammar arm must be able to produce.
    shapes = [cells[-1] for cells in rows]
    examples = [cells[0].strip("`") for cells in rows]
    assert len(set(examples)) == len(examples), (
        f"the table records a duplicate example: {examples}")
    for example in examples:
        assert example.startswith("2026-") or example.startswith("from-"), (
            f"table row 0 is not a filename example: {example}")
    distinct = set(shapes)
    assert "PRIMARY" in distinct, f"no PRIMARY row: {sorted(distinct)}"
    variants = {s for s in distinct if s.startswith("Variant ")}
    assert variants, f"the table records no refused variant: {sorted(distinct)}"


if __name__ == "__main__":  # pragma: no cover - measurement aid
    raise SystemExit(pytest.main([__file__, "-v"]))
