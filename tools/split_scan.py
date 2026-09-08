"""Find a sensitive value in tracked text even when it has been SPLIT.

The mechanism behind `tests/test_no_split_identity.py`; the rule, the history
and the limits live in that file's docstring. Kept in `tools/` rather than
inside the test because `tests/test_no_account_paths.py` uses it too, to prove
the blindness its own contiguous regex has.

THE ONE IDEA. A whole-token search asks "do these bytes appear in order, with
nothing between them". Every separator a document is made of - a newline, an
indent, a backtick, a markdown emphasis marker, a list bullet, a comment hash -
defeats it, and none of those changes what a reader sees. So the text is reduced
to a NORMALIZED view first: lowercase, `[a-z0-9]` only. Splitting a value across
that view is impossible without putting UNRELATED characters between the halves.

Values are pinned by sha256, never spelled out: a guard that names the string it
forbids publishes it. `first` and `length` are carried alongside the digest so
the scan hashes only the windows that could match, which is what makes it linear
rather than one hash per character per fragment.
"""
from __future__ import annotations

import hashlib
import re
from typing import NamedTuple

_KEEP = re.compile(r"[^a-z0-9]+")


class Fragment(NamedTuple):
    """A pinned value. `label` is what a hit REPORTS, since the value cannot be."""

    label: str
    first: str
    length: int
    digest: str


def normalize(text: str) -> str:
    """Lowercase, `[a-z0-9]` only. Deletes every separator a split can be made of."""
    return _KEEP.sub("", text.lower())


def pin(label: str, value: str) -> Fragment:
    """Pin `value` by its NORMALIZED form. Used to build the constants below."""
    norm = normalize(value)
    if not norm:
        raise ValueError(f"{label}: nothing left after normalisation")
    return Fragment(label, norm[0], len(norm),
                    hashlib.sha256(norm.encode("ascii")).hexdigest())


def _hits_in_view(view: str, frag: Fragment) -> bool:
    """True if `frag` occurs in one normalised view. Only candidate windows hash."""
    start = view.find(frag.first)
    while start != -1:
        window = view[start:start + frag.length]
        if (len(window) == frag.length
                and hashlib.sha256(window.encode("ascii")).hexdigest() == frag.digest):
            return True
        start = view.find(frag.first, start + 1)
    return False


# The values this repository must never carry. Each one is distinctive ON ITS
# OWN, which is the rule stated in the guard's docstring: a fragment that has to
# be assembled from two halves is defeated again by the next split.
#
#   operator-surname   the identifying half of the operator's personal email
#                      address, purged from history on 2026-09-07 (LEDGER 172)
#                      and then re-published five times by the three artifacts
#                      that recorded the purge. The domain is deliberately NOT
#                      pinned: it names millions of people, so it would fire on
#                      prose and the guard would be deleted.
#   account-in-path    the machine's real Windows account name, pinned JOINED
#                      to the `Users` segment that precedes it in a home path.
#                      The bare account name is a common English word that
#                      `docs/OPERATIONS.md` and `tools/ci_watchdog.py` both use
#                      legitimately; joined to `Users` it is a home path and
#                      nothing else. `tests/test_no_account_paths.py` catches
#                      the same class contiguously, with the account segment
#                      parsed rather than pinned, so a path from ANY machine in
#                      the fleet is caught there. This pin is the split-proof
#                      half, not a replacement for it.
SENSITIVE_FRAGMENTS: tuple[Fragment, ...] = (
    Fragment("operator-surname", "b", 6,
             "6248cfe0e5baae53967acf9ea66c3f4e817154f980b46cb9cd252577e3a55ab5"),
    Fragment("account-in-path", "u", 18,
             "c2afc84abc8f49921c5a743c1af70b62b5ed260c2da25ff2a7d637b78e615f2a"),
)


def scan_fragments(
    text: str, fragments: tuple[Fragment, ...] = SENSITIVE_FRAGMENTS,
) -> list[str]:
    """Labels of every pinned fragment present in `text`, split-proof and reversed.

    Pure, so the mutation arms can drive it with a synthetic pin instead of the
    real one. Scanning the reversed view for a forward fragment is what catches
    a value written backwards, which is the shape Lanternlight actually hit.
    """
    forward = normalize(text)
    if not forward:
        return []
    backward = forward[::-1]
    hits: list[str] = []
    for frag in fragments:
        for view, sense in ((forward, "split"), (backward, "split+reversed")):
            if _hits_in_view(view, frag):
                hits.append(f"identity fragment [{frag.label}] ({sense})")
                break
    return hits
