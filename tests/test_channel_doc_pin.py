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

    # Guard the guard: an empty candidate set would pass vacuously.
    assert candidates, (
        "no repo-relative path spans extracted from the doc - the extraction "
        "broke, so the assertion below would be vacuous")

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


# ---- 7. the filename-variant table, the grammar's test-vector source --------

def _variant_table_rows() -> list[list[str]]:
    """Rows of the `### Filename grammar table` section, header dropped."""
    text = _text()
    start = text.find("### Filename grammar table")
    if start < 0:
        return []
    body = text[start:]
    rows: list[list[str]] = []
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
            continue  # the separator row
        rows.append(cells)
    return rows[1:] if rows else []  # drop the header row


def test_the_filename_variant_table_is_present_and_parses():
    """This table is where the grammar's test vectors come from.

    Each row pairs a synthetic example filename with the SHAPE it belongs to,
    so a tree building a grammar arm reads its cases out of here rather than
    inventing them. If the table stops parsing, that source is gone silently.
    """
    rows = _variant_table_rows()
    assert rows, (
        "the `### Filename grammar table` section is missing or its rows no "
        "longer parse")

    examples = []
    shapes = []
    for cells in rows:
        assert len(cells) >= 2, f"under-wide table row: {cells}"
        example = cells[0].strip("`")
        shape = cells[-1]
        assert example.startswith("2026-") or example.startswith("from-"), (
            f"table row 0 is not a filename example: {cells}")
        assert shape, f"table row carries no shape: {cells}"
        examples.append(example)
        shapes.append(shape)

    assert len(set(examples)) >= 2, (
        f"the table records fewer than two distinct examples: {examples}")
    assert len(set(shapes)) >= 2, (
        f"the table records fewer than two distinct shapes: {shapes}")

    # Guard the guard: two rows that were both PRIMARY would be two rows and no
    # vectors. The table earns its keep only by carrying the accepted shape AND
    # at least one shape a responder refuses - the two answers any grammar arm
    # has to be able to produce.
    distinct = set(shapes)
    assert "PRIMARY" in distinct, f"no PRIMARY row: {sorted(distinct)}"
    variants = {s for s in distinct if s.startswith("Variant ")}
    assert variants, f"the table records no refused variant: {sorted(distinct)}"


if __name__ == "__main__":  # pragma: no cover - measurement aid
    raise SystemExit(pytest.main([__file__, "-v"]))
