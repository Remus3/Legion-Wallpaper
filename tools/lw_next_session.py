"""Resolve and write the LW next-session hand-off file, namespace guarded.

The hand-off lands in the REPO ROOT and is tracked in git (moved off the
Desktop 2026-09-06, operator-directed via RC's cross-repo note). The Desktop
was untracked, unversioned and unreviewable: nothing could notice a hand-off
going stale, and no diff showed what the last session actually handed over.
The Desktop keeps a SHORTCUT to the repo file, so operator access is unchanged.

The `LW-` prefix stays on the filename even though it is now redundant in-repo.
The Desktop shortcuts are still a shared surface and need distinguishable
names, and the prefix is also what stops a doctored intent document from
naming an arbitrary write target.

Contract:
  * default target is `<repo root>/LW-NEXT-SESSION.txt`;
  * an optional on-disk intent document may name a DIFFERENT file, but only a
    bare filename in the repo root that starts with `LW-`;
  * every other value - absolute path, drive letter, `..` segment, any path
    separator, empty/blank, non-string, malformed or missing document - falls
    back to the default instead of being honoured.

A cross-repo write must be a deliberate act, never a fallback. Rejections are
returned as a reason string rather than raised: a stale intent document must
not be able to fail an operator's `/done`, only to be ignored.

Pure stdlib, so it runs on the CI interpreter. Coverage:
tests/test_lw_next_session_guard.py.

The CONTENT is gated too, and before the write rather than after the commit:
`write_handoff` runs `precommit_gate.scan_handoff_text` over the string and
refuses on non-ASCII, a banned glyph, a 32-hex literal, a user-profile path or
a secret-shaped literal. Same function object as the commit-time gate, so the
rule has one reading. This file is TRACKED in a PUBLIC repo and is the
highest-variance artifact in the tree - written fresh every session, never
reviewed before it is written - and a tracked hand-off that is wrong costs a
history rewrite where a Desktop one cost a single edit. Coverage:
tests/test_handoff_write_gate.py. NOT gated with a per-session exemption list:
an exemption list that grows once per session is a gate disarmed one word at a
time.

CLI:
    python tools/lw_next_session.py --path            # print the resolved target
    python tools/lw_next_session.py --write FILE      # write FILE's content
    ... | python tools/lw_next_session.py --write -   # write stdin
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# The hand-off content rules live with the commit-time gate, and this module
# calls that exact function object. Two agreeing copies would be a second
# reading of one rule, which is the defect this consolidates - see
# tests/test_handoff_write_gate.py, which asserts the IDENTITY, not the
# behaviour.
try:
    from precommit_gate import scan_handoff_text
except ImportError:  # running with tools/ off sys.path
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from precommit_gate import scan_handoff_text

ROOT = Path(__file__).resolve().parent.parent

DEFAULT_NAME = "LW-NEXT-SESSION.txt"
REQUIRED_PREFIX = "LW-"

# Optional. Absent is the normal case - the default is not a fallback for
# failure so much as the standing answer.
INTENT_PATH = ROOT / "ops" / "runtime" / "next_session_intent.json"
INTENT_KEY = "filename"

_SEPARATORS = ("/", "\\")


class HandoffRefused(ValueError):
    """The hand-off carries content that must not reach a tracked public file.

    Subclasses ValueError deliberately: the pre-existing contract was a
    ValueError on non-ASCII and the `--write` CLI catches that, so growing the
    rule set must not change what callers catch.
    """


def choose_filename(value):
    """Validate an intent filename. Returns (filename, reason).

    reason is "" when `value` was accepted; otherwise it explains the rejection
    and the returned filename is DEFAULT_NAME.
    """
    if not isinstance(value, str) or isinstance(value, bool):
        return DEFAULT_NAME, f"intent filename is not a string ({type(value).__name__})"
    name = value.strip()
    if not name:
        return DEFAULT_NAME, "intent filename is empty"
    if any(sep in name for sep in _SEPARATORS):
        return DEFAULT_NAME, f"intent filename {name!r} contains a path separator"
    # A drive letter cannot appear in a bare filename; ":" also catches NTFS
    # alternate data streams.
    if ":" in name:
        return DEFAULT_NAME, f"intent filename {name!r} contains a drive letter or stream"
    if name in (".", "..") or ".." in name:
        return DEFAULT_NAME, f"intent filename {name!r} contains a parent-directory segment"
    if Path(name).is_absolute():
        return DEFAULT_NAME, f"intent filename {name!r} is absolute"
    if not name.startswith(REQUIRED_PREFIX):
        return DEFAULT_NAME, (
            f"intent filename {name!r} is not prefixed {REQUIRED_PREFIX!r} - "
            "it could target a sibling repo's hand-off")
    if name == REQUIRED_PREFIX:
        return DEFAULT_NAME, "intent filename is the bare prefix with no name"
    return name, ""


def choose_filename_from_intent(intent_path=None):
    """Read the intent document and validate what it names. Returns (name, reason)."""
    path = Path(intent_path) if intent_path is not None else INTENT_PATH
    if not path.is_file():
        return DEFAULT_NAME, f"no intent document at {path}"
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return DEFAULT_NAME, f"intent document unreadable ({exc.__class__.__name__})"
    if not isinstance(doc, dict):
        return DEFAULT_NAME, "intent document is not a JSON object"
    if INTENT_KEY not in doc:
        return DEFAULT_NAME, f"intent document has no {INTENT_KEY!r} key"
    return choose_filename(doc[INTENT_KEY])


def resolve_target(root=None, intent_path=None):
    """The full path the hand-off will be written to."""
    base = Path(root) if root is not None else ROOT
    name, _reason = choose_filename_from_intent(intent_path)
    return base / name


def write_handoff(text, root=None, intent_path=None):
    """Atomically write `text` to the resolved target. Returns the path written.

    Raises HandoffRefused (a ValueError) when the content breaks a hand-off
    rule - non-ASCII, a banned glyph, a 32-hex literal, a user-profile path or
    a secret-shaped literal. The gate runs BEFORE anything reaches disk: this
    file is TRACKED in a PUBLIC repo, so a bad hand-off caught at commit time
    is already one push from world-readable and a bad one caught later costs a
    history rewrite. Refusing while it is still a string in memory is the only
    point at which the session can simply fix it.

    On refusal NOTHING is written - no target, no `.tmp`, and any existing
    hand-off is left exactly as it was.
    """
    if not isinstance(text, str):
        raise TypeError("hand-off content must be a string")
    violations = scan_handoff_text(text)
    if violations:
        raise HandoffRefused(
            "hand-off REFUSED before writing - "
            f"{len(violations)} rule violation(s):\n" + "\n".join(violations))
    target = resolve_target(root=root, intent_path=intent_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_name(target.name + ".tmp")
    tmp.write_text(text, encoding="ascii", newline="\n")
    tmp.replace(target)
    return target


def main(argv=None):
    ap = argparse.ArgumentParser(description="LW next-session hand-off writer")
    ap.add_argument("--path", action="store_true",
                    help="print the resolved target and exit")
    ap.add_argument("--write", metavar="FILE",
                    help="write FILE's content ('-' for stdin)")
    args = ap.parse_args(argv)

    name, reason = choose_filename_from_intent()
    if reason and "no intent document" not in reason:
        print(f"intent ignored: {reason}", file=sys.stderr)

    if args.path or not args.write:
        print(resolve_target())
        return 0

    text = sys.stdin.read() if args.write == "-" else Path(args.write).read_text(encoding="utf-8")
    try:
        written = write_handoff(text)
    except ValueError as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 2
    print(written)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
