"""No tracked file may carry a real account or organisation UUID.

MAIN's 2026-10-08 README-AUDIT (finding 3.1) found a class the two neighbouring
guards miss: the owner account UUID and organisation UUID copied out of a Claude
config / transcript into a tracked doc. `tests/test_no_account_paths.py` parses
Windows home paths and `tests/test_no_split_identity.py` pins known values by
digest; neither one reads a UUID that FOLLOWS an account or org key.

THE RULE. A UUID that follows an `accountUuid` / `account_uuid` / `account-id`
or an `org` / `organization` / `organisation` uuid-or-id key is flagged, in any
tracked file, with NO dated-file or archive exemption: the history rewrite of
2026-10-09 (LEDGER 292) scrubbed every copy, so there is nothing left to excuse.
The all-zero UUID is the one placeholder spelling allowed, plus the angle-bracket
placeholders `<account-uuid>` / `<org-uuid>` (which are not UUIDs at all).

WHY KEYED, NOT EVERY UUID. Session ids, run ids and fixture ids are UUIDs too,
they identify no account, and this repo cites them on purpose. The key is what
makes a UUID an account identity.
"""
from __future__ import annotations

import re
import subprocess
from functools import lru_cache
from pathlib import Path

import gitdep

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

_UUID = r"[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}"
ACCOUNT_UUID = re.compile(
    r"(?i)(?:account[_-]?(?:uuid|id)|org(?:ani[sz]ation)?[_-]?(?:uuid|id))"
    r"[\"'`]?\s*[:=]\s*[\"'`]?(?P<uuid>" + _UUID + r")"
)
_ZERO = "00000000-0000-0000-0000-000000000000"

SELF_EXEMPT = {"tests/test_no_account_uuid.py"}


def scan_text(text: str) -> list[str]:
    """Offending keyed UUIDs in `text` (the value is never echoed)."""
    hits = []
    for m in ACCOUNT_UUID.finditer(text):
        if m.group("uuid") == _ZERO:
            continue
        hits.append(f"keyed account/org uuid at offset {m.start()}")
    return hits


@lru_cache(maxsize=1)
def _tracked_files() -> tuple[str, ...]:
    out = subprocess.run(
        ["git", "ls-files", "-z"], cwd=REPO_ROOT,
        capture_output=True, text=True, check=True,
    ).stdout
    return tuple(sorted(p for p in out.split("\0") if p))


def sweep() -> tuple[int, list[str]]:
    scanned, offenders = 0, []
    for rel in _tracked_files():
        if rel in SELF_EXEMPT:
            continue
        try:
            text = (REPO_ROOT / rel).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        scanned += 1
        offenders += [f"{rel}: {h}" for h in scan_text(text)]
    return scanned, offenders


@gitdep.requires_git
def test_the_sweep_selects_a_real_corpus():
    scanned, _ = sweep()
    assert scanned > 200, f"only {scanned} tracked files scanned"


@gitdep.requires_git
def test_no_tracked_file_carries_an_account_uuid():
    _, offenders = sweep()
    assert not offenders, (
        f"{len(offenders)} keyed account/org UUID(s):\n  " + "\n  ".join(offenders)
        + "\nWrite <account-uuid> / <org-uuid> instead. This repo is PUBLIC.")


@pytest.mark.parametrize("planted", [
    '"ownerAccountUuid":"12345678-9abc-4def-8123-456789abcdef"',
    '"ownerOrganizationUuid": "abcdef01-2345-4678-9abc-def012345678"',
    "account_uuid = 'deadbeef-0000-4000-8000-00000000beef'",
    "organization_id: 0f0f0f0f-1111-4222-8333-444455556666",
    "orgId=11111111-2222-4333-8444-555566667777",
])
def test_a_planted_account_uuid_is_caught(planted):
    assert scan_text(planted), f"missed a planted keyed uuid: {planted}"


@pytest.mark.parametrize("innocent", [
    '"ownerAccountUuid":"00000000-0000-0000-0000-000000000000"',
    '"ownerAccountUuid":"<account-uuid>"',
    '"ownerOrganizationUuid":"<org-uuid>"',
    '"sessionId":"12345678-9abc-4def-8123-456789abcdef"',
    "run_id 12345678-9abc-4def-8123-456789abcdef",
])
def test_a_legitimate_neighbour_survives(innocent):
    assert not scan_text(innocent), f"false positive on: {innocent}"


def test_the_self_exemption_is_load_bearing():
    text = (REPO_ROOT / "tests/test_no_account_uuid.py").read_text(encoding="utf-8")
    assert scan_text(text)


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
