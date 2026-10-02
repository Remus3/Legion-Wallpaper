"""No NEW occurrence of a pinned identity may enter this repository's history.

Sibling of `tests/test_no_secret_literals.py`, `tests/test_no_account_paths.py`
and `tests/test_no_split_identity.py`, and the correction to all three on ONE
axis: every one of them is a WORKING-TREE guard. Each builds its corpus from
`git ls-files` and reads the bytes from disk, so each answers "what does the
tracked tree carry RIGHT NOW". None of them can see a blob that is no longer
checked out. Verified before this file was written, against the live source:
`test_no_secret_literals` takes its corpus at :153-159 and reads from disk at
:194; `test_no_account_paths` does the same at :122-129 and :151;
`test_no_split_identity` at :93-100 and :109. That is not a defect in them - it
is their stated scope - but it leaves a whole class unattended on a PUBLIC repo,
because git keeps every blob it was ever handed.

THE MEASURED FINDING THIS GUARDS, re-measured here on 2026-10-02 rather than
taken from a report. A full scan of the object database - 4,772 objects, 2,338
blobs, 137.1 MiB, 3.49s, including the objects no ref reaches - found:

  * NO credential, API key, token or private key anywhere in history, beyond
    the fixtures that are planted on purpose and say so.
  * The operator's personal email address alive in FIVE distinct history blobs,
    whose trees belong to THREE commits, all three ancestors of origin/main:
    1bf2363 (2026-09-08), d327642 (2026-09-07) and e685573 (2026-09-07) - the
    last of these being the commit that RECORDED the purge. Carrier paths are
    `WAKEUP_NOTES.md`, `docs/LEDGER.md` and
    `docs/_archive/2026-09-07-sha-rewrite-map.md`. This is the exact shape the
    `feedback-documenting-a-leak-republishes-it` memory describes: the write-up
    of a purge is where the purged value comes back.
  * Commit METADATA is clean. One distinct identity across author and committer
    on every ref, and it is the GitHub noreply address, so the 2026-09-07
    rewrite worked on its targets. What survived is inside the DOCUMENTS.
  * NOT in HEAD. The tracked tree is clean, which is why the three sweeps above
    all report green and are right to.

A SECOND REPORTED RESIDUAL WAS CHECKED AND IS NOT ONE. A hand-off report named
an account-name-shaped segment under a `C:\\Users\\...` fixture as a
low-severity leak. Measured: the value behind that digest is the string
`someaccount`, eleven characters, which is a SYNTHETIC fixture planted by
`tests/test_handoff_write_gate.py` and `tests/test_inbox_responder.py` to prove
their redaction gates fire. It is not this machine's login - that account name
is thirteen characters and hashes to a different digest. Nothing is pinned for
it, deliberately: pinning a deliberate fake would make the guard fire on the
fixtures that prove the OTHER guards work, and a guard that fights its siblings
gets deleted. Recorded in `docs/IDENTITY_IN_HISTORY_2026-10-02.md`.

THE OPERATOR'S DECISION, 2026-10-02: do NOT rewrite history a fourth time. The
reasons are recorded in that doc. This file is the forward half of that
decision, and it is the only half there is.

================================ SCOPE =================================

Three scopes, deliberately separated, because they do not cost the same and are
not available in the same places. Measured on this box, this tree:

  ENTRY GATE      551 tracked files, 7.9 MiB, under 0.1s. Every tracked path
                  read from DISK, plus every blob STAGED in the index that
                  differs from HEAD. This is the set a commit would hand to
                  git, so it is where a NEW occurrence is stopped. Always runs.
  HISTORY DELTA   every blob reachable from a local ref but NOT from the
                  recorded baseline commit. 0.016s at the baseline, and it
                  grows with the distance from it. Any pin hit in a blob that
                  is not in `KNOWN_CARRIERS` fails. Runs wherever real history
                  is present.
  FULL CENSUS     the whole object database, 3.49s and 137.1 MiB of I/O, which
                  is what produced the finding above. OPT-IN via
                  `LW_IDENTITY_CENSUS=1`. It is not in the default suite for
                  two reasons: 3.5s and 137 MiB on every single pytest run buys
                  a re-derivation of a recorded constant, and in CI it would be
                  structurally VACUOUS (see below) - a green that means nothing
                  in the place it matters most is worse than an absent arm.

WHAT THIS GUARD CANNOT SEE. Stated as a list rather than implied, because an
overclaiming guard is worse than a narrow one.

  1. ANY BLOB THAT PREDATES THE BASELINE, other than the ones enumerated in
     `KNOWN_CARRIERS`. The delta arm is a fail-on-NEW gate by construction. The
     pre-baseline population was measured once, by the census, and recorded; the
     census is how that record is re-checked, and it is opt-in.
  2. ANYTHING IN A SHALLOW CLONE BEYOND HEAD AND THE INDEX. `ci.yml` uses
     `actions/checkout@v6` with no `fetch-depth`, and that action's default is a
     single-commit shallow clone, so in CI there IS no history to walk. The two
     history arms detect that and SKIP with a reason that says so. The ENTRY
     GATE is the CI-effective arm, and it is effective there: it reads the
     checked-out tree, which is present at any depth.
  3. OBJECTS THAT EXIST ONLY ON THE REMOTE. GitHub keeps unreachable objects
     after a force-push (CLAUDE.md records this), and no local test can reach
     them. This is a reason the remediation was declined, not a gap this guard
     could close.
  4. A PINNED VALUE SPLIT ACROSS SEPARATORS. The shapes here are CONTIGUOUS
     token classes. `tests/test_no_split_identity.py` is the split-proof half,
     over the tracked tree, pinning a normalised fragment. Neither half
     subsumes the other and this file does not duplicate it.
  5. A VALUE THAT IS NOT PINNED. This is a pin list, not a classifier. It
     answers "has THIS value come back", which is the question the finding
     poses. `test_no_secret_literals` is the shape-family classifier.

WHY THE PINS ARE DIGESTS AND THE FIXTURES ARE FAKE. Standing rule, learned the
expensive way: a guard that spells out the value it forbids publishes it, and a
guard that plants the real value as a fixture makes its own test file the last
tracked copy. So each pinned value is a `(length, sha256-of-lowercase)` pair and
appears nowhere as text, the positive controls are invented addresses on the
reserved `.invalid` TLD, and `test_this_file_quotes_no_real_address` grades that
property on this file's own bytes.

The mechanism is CLASS regex first, digest second: find every token of a shape
(an address, a dotted token), lowercase it, and compare its digest to the pins.
The regex describes a class and never an instance, so it reveals nothing, and
the length pre-filter means only candidates that COULD match are ever hashed -
which is what keeps the entry gate under a tenth of a second over 7.9 MiB.
"""
from __future__ import annotations

import hashlib
import os
import re
import subprocess
from functools import lru_cache
from pathlib import Path
from typing import NamedTuple

import gitdep

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


class Pin(NamedTuple):
    """A forbidden value, pinned. `label` is what a hit REPORTS, since the value
    cannot be. `length` is the length of the lowercased value and exists only so
    the scan can reject a candidate without hashing it; it reconstructs nothing,
    the same bargain `tools/split_scan.py` already struck and documented.
    """

    label: str
    length: int
    digest: str


def digest_of(value: str) -> str:
    """sha256 of the lowercased value. The one definition, so pins and scans agree."""
    return hashlib.sha256(value.lower().encode("utf-8")).hexdigest()


def pin(label: str, value: str) -> Pin:
    """Build a pin from a value. Used for the FAKE probe values only."""
    lowered = value.lower()
    if not lowered:
        raise ValueError(f"{label}: empty value")
    return Pin(label, len(lowered), digest_of(lowered))


# THE REAL PINS. Hard-coded digests, no value anywhere. Both are views of the
# one finding above: the whole address as it appears contiguously, and its local
# part on its own, which is what a line break at the `@` leaves behind.
PINNED: tuple[Pin, ...] = (
    Pin("operator-address", 22,
        "6c69aeec06d41b08765d41ee353e46de2597de37bc60bebeb38898c2affd0d5e"),
    Pin("operator-address-local-part", 12,
        "4d3cb93c7b82d7c4fe8de1d3aba6e658bd55caca7b4b8c0cbc352f978b182ce8"),
)

# CLASS shapes. Each describes a family of tokens and never one instance, so
# neither reveals anything about what is pinned.
#
#   address        a local part, an at-sign, a dotted domain: the contiguous
#                  form. Written out in words rather than as a sample, because
#                  the arm at the bottom of this file grades this source for
#                  address-shaped tokens and a sample would trip it - which is
#                  how that arm was first seen to bind.
#   dotted-token   `word.word`. Enormously common in this tree (`lw_facts.py`,
#                  `docs.md`, `obj.attr`), which is exactly why it is safe to
#                  use: it says nothing. The length pre-filter means almost none
#                  of those matches is ever hashed.
SHAPES: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("address", re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,24}")),
    ("dotted-token", re.compile(r"[A-Za-z][A-Za-z0-9_\-]{1,40}\.[A-Za-z][A-Za-z0-9_\-]{1,40}")),
)

# The recorded pre-baseline population, BY BLOB SHA. A blob sha is not secret
# and it is what makes the finding checkable by anyone: `git cat-file blob <sha>`
# resolves it, and `git cat-file -e <sha>` proves it is still there. Enumerated
# rather than counted so the census can assert set equality instead of a total,
# which is the difference between grading the population and grading its size.
KNOWN_CARRIERS: dict[str, str] = {
    "100427ca360ae449797c4f0f3289d8d8cd81402b": "docs/LEDGER.md",
    "150d6d32e19fbd3397fb9aecb2e9d1594814bd7d": "docs/LEDGER.md",
    "611053d509d91183461f2fe2c252d685acb25b91": "WAKEUP_NOTES.md",
    "a1f888295cc66f831a3a7ad6e75a5412073d6cc2": "WAKEUP_NOTES.md",
    "b9992ac6744de4c9ec3053eb2fe645698cfd7f96":
        "docs/_archive/2026-09-07-sha-rewrite-map.md",
}

# The commit the DELTA arm measures from: `origin/main` as it stood when this
# guard was written. Everything at or before it was measured by the census and
# is recorded above; everything after it is this guard's business. Moving this
# forward is legitimate, and the arm below refuses to let it be moved to a
# commit that does not exist, which is what a fourth history rewrite would do.
BASELINE_COMMIT = "6dbe5e9be79d0e726432dc6d324a25a12ad5e3b9"

CENSUS_ENV = "LW_IDENTITY_CENSUS"


# --------------------------------------------------------------------------- #
# the scanner
# --------------------------------------------------------------------------- #
def scan(text: str, pins: tuple[Pin, ...] = PINNED) -> list[str]:
    """Labels of every pinned value present in `text`. Pure, so arms can drive it."""
    if not text or not pins:
        return []
    lengths = {p.length for p in pins}
    by_digest = {p.digest: p.label for p in pins}
    hits: list[str] = []
    seen: set[str] = set()
    for shape, pattern in SHAPES:
        for match in pattern.finditer(text):
            token = match.group(0)
            if len(token) not in lengths:
                continue
            label = by_digest.get(digest_of(token))
            if label is not None and label not in seen:
                seen.add(label)
                # The LABEL is the whole report. Not one character of the value
                # reaches a log, per the standing rule that documenting a leak
                # republishes it.
                hits.append(f"pinned identity [{label}] in {shape} form")
    return hits


def scan_bytes(blob: bytes, pins: tuple[Pin, ...] = PINNED) -> list[str]:
    """`scan`, for raw object bytes. latin-1 is byte-preserving over the whole
    octet range, so a binary blob decodes without raising and without shifting
    any ASCII offset - the pinned values are ASCII, so nothing can be missed."""
    return scan(blob.decode("latin-1"), pins)


# --------------------------------------------------------------------------- #
# git
# --------------------------------------------------------------------------- #
def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=REPO_ROOT, capture_output=True, text=True,
        check=True, creationflags=NO_WINDOW,
    ).stdout


def _git_bytes(*args: str) -> bytes:
    return subprocess.run(
        ["git", *args], cwd=REPO_ROOT, capture_output=True,
        check=True, creationflags=NO_WINDOW,
    ).stdout


@lru_cache(maxsize=1)
def _tracked_files() -> tuple[str, ...]:
    """Every tracked path, asked of GIT rather than of the disk."""
    return tuple(sorted(p for p in _git("ls-files", "-z").split("\0") if p))


@lru_cache(maxsize=1)
def _staged_paths() -> tuple[str, ...]:
    """Paths whose INDEX content differs from HEAD, i.e. what a commit would add.

    Normally empty. It is here because the entry gate's whole claim is about
    what would ENTER, and a value can be staged without being on disk - `git add
    -p` of a hunk, or a staged file deleted afterwards.
    """
    out = _git("diff-index", "--cached", "--name-only", "-z",
               "--diff-filter=ACMR", "HEAD")
    return tuple(sorted(p for p in out.split("\0") if p))


def entry_sweep() -> tuple[int, list[str]]:
    """`(items_scanned, offenders)` over the tree on disk plus the staged index."""
    scanned = 0
    offenders: list[str] = []
    for rel in _tracked_files():
        try:
            text = (REPO_ROOT / rel).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        scanned += 1
        for hit in scan(text):
            offenders.append(f"{rel} (working tree): {hit}")
    for rel in _staged_paths():
        try:
            blob = _git_bytes("show", f":{rel}")
        except subprocess.CalledProcessError:
            continue
        scanned += 1
        for hit in scan_bytes(blob):
            offenders.append(f"{rel} (staged): {hit}")
    return scanned, offenders


def _is_shallow() -> bool:
    return _git("rev-parse", "--is-shallow-repository").strip() == "true"


def _commit_exists(rev: str) -> bool:
    return subprocess.run(
        ["git", "cat-file", "-e", f"{rev}^{{commit}}"], cwd=REPO_ROOT,
        capture_output=True, creationflags=NO_WINDOW,
    ).returncode == 0


def delta_blobs(since: str) -> dict[str, str]:
    """`{blob sha: path}` for every blob reachable from a ref but not from `since`.

    Driveable with any revision, which is what lets the arm below prove the
    enumerator BINDS on a day when the live delta is legitimately empty.
    """
    out = _git("rev-list", "--objects", "--all", "--not", since)
    named: dict[str, str] = {}
    for line in out.splitlines():
        sha, _, path = line.partition(" ")
        if len(sha) == 40 and path:
            named[sha] = path
    if not named:
        return {}
    # ONE `--batch-check` for the whole set. A `cat-file -t` per object was the
    # first cut, and the mutation run that widened the baseline to the root
    # commit measured it at 125s for 2.3k objects - several hundred process
    # spawns is a cost the delta arm would start paying as it drifts from the
    # baseline, which is exactly when it must stay cheap enough to keep.
    probe = subprocess.run(
        ["git", "cat-file", "--batch-check"], cwd=REPO_ROOT,
        input="\n".join(named) + "\n", capture_output=True, text=True,
        check=True, creationflags=NO_WINDOW,
    ).stdout
    found: dict[str, str] = {}
    for line in probe.splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[1] == "blob" and parts[0] in named:
            found[parts[0]] = named[parts[0]]
    return found


def delta_sweep(since: str = BASELINE_COMMIT) -> tuple[int, list[str]]:
    """`(blobs_scanned, offenders)` over the blobs new since `since`."""
    scanned = 0
    offenders: list[str] = []
    for sha, path in sorted(delta_blobs(since).items()):
        if sha in KNOWN_CARRIERS:
            continue
        try:
            blob = _git_bytes("cat-file", "blob", sha)
        except subprocess.CalledProcessError:
            continue
        scanned += 1
        for hit in scan_bytes(blob):
            offenders.append(f"{sha} ({path}): {hit}")
    return scanned, offenders


def census() -> tuple[int, dict[str, list[str]]]:
    """`(blobs_scanned, {blob sha: labels})` over the WHOLE object database.

    Streams `git cat-file --batch-all-objects`, so it reaches objects no ref
    points at - which is where 20 of the blobs in the 2026-10-02 scan lived.
    """
    proc = subprocess.Popen(
        ["git", "cat-file", "--batch-all-objects", "--batch", "--buffer"],
        cwd=REPO_ROOT, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
        creationflags=NO_WINDOW,
    )
    assert proc.stdout is not None
    stream = proc.stdout
    scanned = 0
    found: dict[str, list[str]] = {}
    try:
        while True:
            header = stream.readline()
            if not header:
                break
            parts = header.split()
            if len(parts) < 3:
                continue
            sha, kind, size = parts[0].decode(), parts[1].decode(), int(parts[2])
            body = stream.read(size)
            stream.read(1)
            if kind != "blob":
                continue
            scanned += 1
            hits = scan_bytes(body)
            if hits:
                found[sha] = hits
    finally:
        stream.close()
        proc.wait()
    return scanned, found


# FAKE pins for the positive controls. Invented addresses on the reserved
# `.invalid` TLD (RFC 2606), so these name nobody and resolve nowhere. The rule
# under test is the CLASS, so a fixture naming nobody proves exactly as much -
# and an earlier LW guard that planted the real value made its own test file the
# last tracked copy of it.
PROBE_PINS: tuple[Pin, ...] = (
    pin("probe-address", "zqx.probeuser@nowhere.invalid"),
    pin("probe-local-part", "zqx.probeuser"),
)


# --------------------------------------------------------------------------- #
# arms: the entry gate
# --------------------------------------------------------------------------- #
@gitdep.requires_git
def test_the_entry_corpus_is_not_empty():
    """GUARD THE GUARD. A sweep over nothing passes vacuously and looks identical
    to a sweep that found nothing, which is the defect class measured LIVE in
    this repo today in `tools/drift_guard.py`. The corpus is asserted, not
    assumed, and the number is a floor well under the 551 measured so it does
    not become a maintenance chore.
    """
    scanned, _ = entry_sweep()
    assert scanned > 300, (
        f"only {scanned} items in the entry corpus - the sweep is measuring "
        "almost nothing, so its clean result means almost nothing")


@gitdep.requires_git
def test_no_entering_content_carries_a_pinned_identity():
    scanned, offenders = entry_sweep()
    assert not offenders, (
        f"{len(offenders)} pinned identity hit(s) in the {scanned} items that "
        "would enter this repository:\n  " + "\n  ".join(offenders)
        + "\nRemove it. Describe the value in prose instead of quoting it: the "
        "three artifacts that RECORDED the 2026-09-07 purge each re-published "
        "the address they were documenting. This repo is PUBLIC, and a commit "
        "here is one push from world-readable and then unpurgeable.")


@pytest.mark.parametrize("planted", [
    "contact: zqx.probeuser@nowhere.invalid for details",
    "ZQX.ProbeUser@Nowhere.Invalid",
    "the local part on its own is zqx.probeuser here",
    "mailto:zqx.probeuser@nowhere.invalid",
    "| author | zqx.probeuser@nowhere.invalid |",
    "git config user.email zqx.probeuser@nowhere.invalid",
])
def test_a_planted_fake_identity_is_caught(planted):
    """Every detector arm proven to FIRE before the clean results are trusted.

    A clean sweep and an unarmed sweep are indistinguishable from their output.
    Both shape families and the lowercasing are driven here.
    """
    assert scan(planted, PROBE_PINS), f"the sweep missed a planted fake: {planted!r}"


@pytest.mark.parametrize("planted", [
    b"contact: zqx.probeuser@nowhere.invalid\n",
    b"\x00\x01\x02 zqx.probeuser@nowhere.invalid \xff\xfe",
])
def test_a_planted_fake_is_caught_in_raw_bytes(planted):
    """The history arms see BYTES, including from blobs git calls binary."""
    assert scan_bytes(planted, PROBE_PINS), f"missed in bytes: {planted!r}"


@pytest.mark.parametrize("innocent", [
    "zqx.probeusers@nowhere.invalid",   # one character longer
    "zqx.probeuse@nowhere.invalid",     # one character shorter
    "probeuser.zqx@nowhere.invalid",    # the halves transposed
    "zqx-probeuser@nowhere.invalid",    # a different separator
    "see tools/lw_facts.py and docs/LEDGER.md for the record",
    "noreply@users.noreply.github.com",
    "7991173+Remus3@users.noreply.github.com",
    "",
])
def test_an_unrelated_neighbour_survives(innocent):
    """The noreply identity this repo commits under must stay legal, and so must
    every dotted token in the tree, or the guard gets deleted and the property
    stops being checked."""
    assert not scan(innocent, PROBE_PINS), f"false positive on: {innocent!r}"


# --------------------------------------------------------------------------- #
# arms: the history delta
# --------------------------------------------------------------------------- #
def _require_real_history() -> None:
    """THREE dispositions, never two. `gitdep` covers the fourth (git absent).

    A shallow clone is a true SKIP: there is no history to walk, and reporting
    green over it would be the vacuity this file exists to avoid. A baseline
    that does not resolve in a repository that is NOT shallow is a FAILURE: it
    means the recorded constant is stale, which is what a fourth history rewrite
    would do, and a stale baseline silently narrows the delta to nothing.
    """
    if _is_shallow():
        pytest.skip(
            "this is a shallow clone, so there is no history to walk. "
            "ci.yml uses actions/checkout@v6 with no fetch-depth, whose default "
            "is a single commit. The entry gate above is the arm that binds here")
    assert _commit_exists(BASELINE_COMMIT), (
        f"BASELINE_COMMIT {BASELINE_COMMIT[:9]} does not resolve in a "
        "repository that is not shallow. Either history was rewritten again - "
        "in which case re-run the census and re-record both the baseline and "
        "KNOWN_CARRIERS - or this clone is missing refs. Until it resolves the "
        "delta arm would silently measure NOTHING.")


@gitdep.requires_git
def test_the_delta_enumerator_binds_even_when_the_live_delta_is_empty():
    """GUARD THE GUARD, for the arm whose corpus is legitimately empty.

    On the day the baseline is recorded the delta is zero blobs, and a
    zero-blob sweep passes for free. Asserting non-emptiness would be wrong
    (empty is the correct steady state), so what is asserted instead is that the
    ENUMERATOR works: measured from the baseline's PARENT it must return the
    baseline commit's own blobs, which is a non-empty set with known members.
    A broken enumerator fails here instead of going quietly green forever.
    """
    _require_real_history()
    parent = f"{BASELINE_COMMIT}^"
    assert _commit_exists(parent), f"{parent} does not resolve"
    one_commit = delta_blobs(parent)
    assert one_commit, (
        "the delta enumerator returned nothing for a one-commit range, so it "
        "would return nothing for any range and the delta arm is unarmed")
    assert all(len(sha) == 40 for sha in one_commit), one_commit


@gitdep.requires_git
def test_no_blob_new_since_the_baseline_carries_a_pinned_identity():
    """The gate proper: history may not GAIN an occurrence.

    The recorded carriers are skipped by sha, not by path, so a NEW blob at one
    of those same paths is still caught.
    """
    _require_real_history()
    _, offenders = delta_sweep()
    assert not offenders, (
        f"{len(offenders)} pinned identity hit(s) in blobs new since "
        f"{BASELINE_COMMIT[:9]}:\n  " + "\n  ".join(offenders)
        + "\nThese are already in the object database. Reaching them needs a "
        "history rewrite, which the operator declined on 2026-10-02 - see "
        "docs/IDENTITY_IN_HISTORY_2026-10-02.md - so the cost of one of these "
        "is permanent. Stop it at the working tree instead.")


@gitdep.requires_git
def test_the_recorded_carriers_still_exist_and_predate_the_baseline():
    """The record is only checkable if the shas it cites resolve.

    Every carrier must (a) still be in the object database, (b) still carry a
    pin, which makes this a live re-derivation of the finding rather than a
    quote of it, and (c) be invisible to the delta arm, which is the premise
    that makes `KNOWN_CARRIERS` an acknowledgement and not an exemption.
    """
    _require_real_history()
    new_since_baseline = set(delta_blobs(BASELINE_COMMIT))
    for sha, path in sorted(KNOWN_CARRIERS.items()):
        assert len(sha) == 40 and all(c in "0123456789abcdef" for c in sha), sha
        assert subprocess.run(
            ["git", "cat-file", "-e", sha], cwd=REPO_ROOT, capture_output=True,
            creationflags=NO_WINDOW).returncode == 0, (
            f"recorded carrier {sha[:12]} ({path}) no longer resolves. If "
            "history changed, re-run the census and re-record")
        assert scan_bytes(_git_bytes("cat-file", "blob", sha)), (
            f"recorded carrier {sha[:12]} ({path}) no longer carries a pinned "
            "value, so either the record or the pins are stale")
        assert sha not in new_since_baseline, (
            f"{sha[:12]} is NEW since the baseline, so it is not a recorded "
            "pre-baseline carrier and the delta arm should be reporting it")


@gitdep.requires_git
def test_the_carriers_are_history_only_and_not_in_head():
    """The headline claim, asserted rather than asserted-in-prose: the tracked
    tree is CLEAN, which is why the three working-tree sweeps are green and
    right to be. If a carrier ever reappears in HEAD the entry gate catches it,
    and this arm says which claim in the docstring went stale."""
    _require_real_history()
    head_blobs = {
        line.split()[2] for line in _git("ls-tree", "-r", "HEAD").splitlines()
        if len(line.split()) >= 3
    }
    resident = sorted(sha for sha in KNOWN_CARRIERS if sha in head_blobs)
    assert not resident, (
        f"recorded history-only carrier(s) are LIVE in HEAD: {resident}. The "
        "docstring's 'NOT in HEAD' claim is now false and the tree needs a fix "
        "forward, not a record update")


# --------------------------------------------------------------------------- #
# arms: the census (opt-in)
# --------------------------------------------------------------------------- #
@gitdep.requires_git
@pytest.mark.skipif(
    os.environ.get(CENSUS_ENV) != "1",
    reason=f"the full-history census costs 3.5s and 137 MiB of I/O and is "
           f"structurally vacuous in a shallow CI clone; set {CENSUS_ENV}=1 to "
           f"re-derive the recorded population (it is also what `python "
           f"tests/test_no_identity_enters_history.py` runs)")
def test_the_census_agrees_with_the_record():
    """Re-derive the whole population and assert SET equality with the record.

    Equality in both directions on purpose. A carrier that appeared is the leak
    this file is about; a carrier that vanished means the record is stale and
    every citation of it is wrong. Counting would catch neither cleanly.
    """
    _require_real_history()
    scanned, found = census()
    assert scanned > 1000, f"only {scanned} blobs streamed - the census is wrong"
    assert set(found) == set(KNOWN_CARRIERS), (
        "the census disagrees with KNOWN_CARRIERS.\n"
        f"  appeared: {sorted(set(found) - set(KNOWN_CARRIERS))}\n"
        f"  vanished: {sorted(set(KNOWN_CARRIERS) - set(found))}\n"
        "An appearance is a new leak. A disappearance means the record and "
        "docs/IDENTITY_IN_HISTORY_2026-10-02.md are both stale.")


# --------------------------------------------------------------------------- #
# arms: the guard's own hygiene
# --------------------------------------------------------------------------- #
def test_the_probe_pins_are_not_the_real_pins():
    """The positive controls must not be proving the real pins by accident."""
    real = {p.digest for p in PINNED}
    assert real.isdisjoint({p.digest for p in PROBE_PINS})
    assert len({p.label for p in PINNED} & {p.label for p in PROBE_PINS}) == 0


def test_every_real_pin_is_a_digest_and_long_enough_to_stand_alone():
    """A pin short enough to occur by chance in 137 MiB is not a pin."""
    assert PINNED, "the guard is unarmed"
    labels = [p.label for p in PINNED]
    assert len(labels) == len(set(labels)), f"duplicate labels: {labels}"
    for p in PINNED:
        assert len(p.digest) == 64, f"{p.label} is not a sha256 pin"
        assert all(c in "0123456789abcdef" for c in p.digest), f"{p.label} not hex"
        assert p.length >= 10, f"{p.label} is too short to stand alone"


def test_this_file_quotes_no_real_address():
    """GRADE the no-value rule on this file's own bytes, do not merely state it.

    Every address-shaped token in this source must sit on the reserved
    `.invalid` TLD or be the repository's own public noreply commit identity.
    Anything else means a session documenting the leak republished it, which is
    the exact failure this file is built around.
    """
    source = Path(__file__).read_text(encoding="utf-8")
    allowed_suffix = (".invalid", "users.noreply.github.com")
    offenders = [
        m.group(0) for m in SHAPES[0][1].finditer(source)
        if not m.group(0).lower().endswith(allowed_suffix)
    ]
    assert not offenders, (
        f"this guard quotes {len(offenders)} real-looking address(es): "
        f"{offenders}. Pin by digest and plant fakes on .invalid")


def test_the_record_doc_exists_and_cites_every_carrier_sha():
    """A finding nobody can find again is not recorded. The doc is the place a
    future session looks, and it is only checkable if it cites the shas."""
    doc = REPO_ROOT / "docs" / "IDENTITY_IN_HISTORY_2026-10-02.md"
    assert doc.is_file(), f"{doc} is missing - the record is the other half"
    text = doc.read_text(encoding="utf-8")
    missing = [sha for sha in KNOWN_CARRIERS if sha not in text]
    assert not missing, f"the record does not cite carrier sha(s): {missing}"
    assert BASELINE_COMMIT[:9] in text, "the record does not cite the baseline"


if __name__ == "__main__":
    os.environ[CENSUS_ENV] = "1"
    raise SystemExit(pytest.main([__file__, "-q"]))
