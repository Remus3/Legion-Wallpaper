"""Machine-checkable "Reverse if" conditions for tools/lw_promise_watch.py.

Each probe answers ONE question with an exit code: 0 = the reversal condition
is TRUE now, 1 = false, 2 = cannot tell (input missing, fetch failed, parse
failed) - never a quiet 1 when it could not look.

  python tools/lw_promise_probes.py <probe-name>
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CI_PYTHON_PIN = "3.14"
# sha256[:16] of docs/RESTORATION_PLAN.md section 10 (privacy / shareability
# boundary) as of 2026-10-04 - ADR-005's reversal condition is that it changes.
SECTION10_SHA16 = "330b3d9cef5bb833"
REPO_API = "https://api.github.com/repos/Remus3/Legion-Wallpaper"
WIKI_API = "https://wiki.leagueoflegends.com/en-us/api.php?action=query&meta=siteinfo&format=json"
FLEET_KIT_VERSION = 14


class Undecided(Exception):
    pass


def _read(rel):
    p = ROOT / rel
    if not p.is_file():
        raise Undecided(f"{rel} missing")
    return p.read_text(encoding="utf-8")


def adr_superseded(n):
    """An ADR other than ADR-n says it supersedes ADR-n."""
    d = ROOT / "docs" / "adr"
    if not d.is_dir():
        raise Undecided("docs/adr missing")
    pat = re.compile(rf"supersed\w*\s+ADR-0*{n}\b", re.I)
    for p in d.glob("ADR-*.md"):
        if p.name.startswith(f"ADR-{n:03d}"):
            continue
        if pat.search(p.read_text(encoding="utf-8")):
            return True
    return False


def ci_python_pin_moved():
    pins = set(re.findall(r'python-version:\s*"([^"]+)"', _read(".github/workflows/ci.yml")))
    if not pins:
        raise Undecided("no python-version pin found")
    return pins != {CI_PYTHON_PIN}


def ci_paths_filter_added():
    for line in _read(".github/workflows/ci.yml").splitlines():
        code = line.split("#", 1)[0]
        if re.match(r"^\s*paths(-ignore)?\s*:", code):
            return True
    return False


def privacy_boundary_changed():
    text = _read("docs/RESTORATION_PLAN.md")
    m = re.search(r"^## 10\..*?(?=^## |\Z)", text, re.S | re.M)
    if not m:
        raise Undecided("section 10 not found")
    return hashlib.sha256(m.group(0).encode("utf-8")).hexdigest()[:16] != SECTION10_SHA16


def _fetch(url, timeout=20):
    import urllib.error
    import urllib.request
    req = urllib.request.Request(url, headers={"User-Agent": "lw-promise-watch/1"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read(200000)
    except urllib.error.HTTPError as exc:
        return exc.code, b""
    except (OSError, ValueError) as exc:
        raise Undecided(f"fetch failed ({exc.__class__.__name__})") from None


def repo_not_public():
    status, body = _fetch(REPO_API)
    if status == 404:
        return True  # unauthenticated 404 = private (or gone): reverse-worthy either way
    if status != 200:
        raise Undecided(f"github api status {status}")
    try:
        return bool(json.loads(body).get("private"))
    except ValueError:
        raise Undecided("github api body not JSON") from None


def wiki_api_stopped_answering():
    status, body = _fetch(WIKI_API)
    if status >= 500 or status in (401, 403, 404, 410):
        return True
    try:
        return "query" not in json.loads(body)
    except ValueError:
        return True  # it answered, but not as the Action API


def fleet_kit_moved():
    """A newer FLEET-KIT note reached the inbox, or the vendored kit moved."""
    try:
        man = json.loads(_read("ops/fleet_kit/MANIFEST.json"))
    except ValueError:
        raise Undecided("fleet kit manifest unreadable") from None
    if int(man.get("version", 0)) != FLEET_KIT_VERSION:
        return True
    inbox = ROOT / "moon_sync_inbox"
    if not inbox.is_dir():
        raise Undecided("sync inbox missing")
    # NEWER than the vendored kit only: the inbox keeps every older FLEET-KIT
    # note for good, and "any other version" would fire on that history forever.
    pat = re.compile(r"FLEET-KIT-v(\d{1,3})\b")
    for p in inbox.glob("*"):
        if p.is_file() and p.stat().st_size < 2_000_000:
            try:
                text = p.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            if any(int(v) > FLEET_KIT_VERSION for v in pat.findall(text)):
                return True
    return False


PROBES = {
    "adr001_superseded": lambda: adr_superseded(1),
    "adr003_superseded": lambda: adr_superseded(3),
    "adr007_superseded": lambda: adr_superseded(7),
    "ci_python_pin_moved": ci_python_pin_moved,
    "ci_paths_filter_added": ci_paths_filter_added,
    "privacy_boundary_changed": privacy_boundary_changed,
    "repo_not_public": repo_not_public,
    "wiki_api_stopped_answering": wiki_api_stopped_answering,
    "fleet_kit_moved": fleet_kit_moved,
}


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 1 or argv[0] not in PROBES:
        print(f"usage: lw_promise_probes.py <{'|'.join(sorted(PROBES))}>")
        return 2
    try:
        true = PROBES[argv[0]]()
    except Undecided as exc:
        print(f"{argv[0]}: undecided - {exc}")
        return 2
    print(f"{argv[0]}: {'TRUE' if true else 'false'}")
    return 0 if true else 1


if __name__ == "__main__":
    sys.exit(main())
