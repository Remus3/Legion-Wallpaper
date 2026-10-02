"""A digest quoted in operational config must match the file it names.

`ops/loop/config.json`'s `directive_suffix` is not prose. It is fed verbatim to
the headless loop executor (`ops/loop/loop_controller.py:927`), so a stale fact
inside it is an INSTRUCTION, and the facts most likely to decay are exactly the
ones that matter: the sha256 digests of the two shared loop files, and the
roster of which sibling repos carry them.

Both had decayed when this guard was written (2026-10-02):

  - The suffix quoted `0b112a4f...` as `winmutex.py`'s digest. That is the
    PRE-round-B value. `tests/test_loop_concurrency.py` labels it verbatim as
    "previous" and pins `df0a7a40...`, which is what is on disk. Round B landed
    in `e980e8b` on 2026-09-20, and the citation sat stale for twelve days.
  - The suffix said FOUR carriers and "CS and LL have no ops/loop/slots.py at
    all". LW had already WITHDRAWN that in writing on the cross-repo channel:
    CS carries `ops/loop/slots.py` byte-identical, the population is FIVE, and
    only LL is absent.

Why a guard rather than just the repair: an executor reading a wrong carrier
roster is being told that editing a byte-identical-by-contract file is safer
than it is, and an executor reading a stale digest cannot verify the file it is
forbidden to touch. A repair fixes the instance; this fixes the class.

Scope, stated so it cannot over-claim: this checks DIGESTS and the CARRIER
COUNT, both of which are mechanically decidable against the live tree. It does
NOT check the rest of the suffix's prose, which is operator intent and has no
machine-checkable referent.
"""

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "ops" / "loop" / "config.json"

# The shared, byte-identical-by-contract files the directive quotes.
SHARED = ("ops/loop/slots.py", "ops/loop/winmutex.py")

_HEX64 = re.compile(r"\b[0-9a-f]{64}\b")


def _suffix() -> str:
    cfg = json.loads(CONFIG.read_bytes().decode("utf-8"))
    return cfg.get("directive_suffix", "")


def _live_digests() -> dict:
    out = {}
    for rel in SHARED:
        p = ROOT / rel
        if p.is_file():
            out[rel] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


def test_the_suffix_exists_and_is_not_empty():
    """Guard the guard: an empty suffix would pass every arm below vacuously.

    This is the arm that catches the key being renamed or dropped - without it,
    deleting `directive_suffix` turns this whole module green.
    """
    s = _suffix()
    assert len(s) > 500, (
        f"directive_suffix is {len(s)} chars - too short to be the live "
        "directive, so the arms below would assert nothing"
    )


def test_the_shared_files_are_both_present():
    """Second guard-the-guard: the digest arm needs real files to compare to."""
    live = _live_digests()
    missing = [r for r in SHARED if r not in live]
    assert not missing, f"shared file(s) absent, digest arm would be vacuous: {missing}"


def test_every_digest_quoted_in_the_directive_is_a_live_shared_digest():
    """Any 64-hex token in the suffix must be a CURRENT shared-file digest.

    Deliberately strict: the suffix has no legitimate reason to quote a sha256
    that is not one of these two files' present contents. A superseded digest
    is the exact defect this guard exists for, so an unrecognised one fails
    rather than being waved through.
    """
    s = _suffix()
    quoted = set(_HEX64.findall(s))
    if not quoted:
        return  # nothing cited is not a decay; the arms above cover emptiness
    live = set(_live_digests().values())
    stale = sorted(quoted - live)
    assert not stale, (
        "directive_suffix quotes sha256 digest(s) that are not the live "
        "contents of "
        + " or ".join(SHARED)
        + " - a superseded digest in operational config is an instruction, not "
        "a note. Stale: "
        + ", ".join(d[:16] + "..." for d in stale)
    )


def test_both_shared_digests_are_actually_cited():
    """The suffix forbids editing both files, so it must identify both.

    Without this, the arm above is satisfiable by DELETING a citation - the
    shrink-the-population route that was measured live in LW today.
    """
    s = _suffix()
    live = _live_digests()
    uncited = sorted(rel for rel, d in live.items() if d not in s)
    assert not uncited, (
        "directive_suffix names the byte-identical-by-contract rule but does "
        "not cite the current digest of: " + ", ".join(uncited)
    )


def test_the_carrier_count_is_not_a_withdrawn_number():
    """FOUR carriers was withdrawn on the channel; CS carries slots.py.

    Pinned as an absence of the retracted claim rather than as the presence of
    the new one, because the roster can legitimately grow again - what must
    never come back is the specific sentence LW retracted.
    """
    s = _suffix()
    assert "FOUR carriers" not in s, (
        "directive_suffix says FOUR carriers - withdrawn 2026-10-02, the "
        "population is FIVE (CS carries ops/loop/slots.py byte-identical)"
    )
    assert "CS and LL have no" not in s, (
        "directive_suffix repeats the withdrawn claim that CS carries no "
        "ops/loop/slots.py - only LL is absent"
    )
