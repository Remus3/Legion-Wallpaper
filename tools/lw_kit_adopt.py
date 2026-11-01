"""Deterministic FLEET-KIT adoption steps (RRF-2.3b, MAIN 2246 REPO-REVIEW 2.3).

# arch: kit adoption without a model - verify, copy, re-embed

WHY THIS EXISTS. A FLEET-KIT-vN ORDER used to be adopted end to end by a
headless model run (LEDGER 293: one such child died mid-suite with 21 files
drafted and nothing committed). Most of the work needs no judgment: check the
delivered bundle against its own MANIFEST.json, copy it into ops/fleet_kit/
byte for byte, and splice FLEET-COMMON.md between the CLAUDE.md markers. This
module does those steps; a model is kept only for the residual (tree-specific
wiring the ORDER describes in prose).

SLICE 1: verify_bundle, copy_bundle, embed_block. SLICE 2: adopt() + the CLI
chain them with fleet_headless.conformance() (loaded from the COPIED kit, so
its KIT_VERSION is the new one) and the kit tests:

    python tools/lw_kit_adopt.py adopt <bundle dir> [--root R] [--no-tests]
    python tools/lw_kit_adopt.py check [--root R]
    python tools/lw_kit_adopt.py closeout --owner ID --order TEXT [--push]

Stages, in order, each stopping the chain: verify (bundle vs its manifest),
version (no downgrade), embed (CLAUDE.md markers checked BEFORE any write),
copy, conformance, tests. Output is one JSON object {ok, stage, problems,
residual}; exit 0 ok, 1 not ok, 2 usage. Red kit tests after a clean copy are
the residual (tree-specific wiring, e.g. the version pin) - the only part
left for a model. The responder hands only that residual to its child at
sonnet/medium (tools/lw_inbox_responder.py kit_adoption, RRF-2.3b slice 3).

Pure stdlib, no machine paths: every function takes its directories as
arguments, so tests run on tmp_path and never touch the live kit.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

# Must equal fleet_headless.BEGIN / END (pinned by tests/test_lw_kit_adopt.py):
# conformance() hashes exactly text[i + len(BEGIN):j].
BEGIN, END = "<!-- FLEET-COMMON BEGIN -->\n", "<!-- FLEET-COMMON END -->"
MANIFEST = "MANIFEST.json"
COMMON = "FLEET-COMMON.md"


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _manifest(bundle):
    try:
        man = json.loads((Path(bundle) / MANIFEST).read_text(encoding="ascii"))
    except (OSError, ValueError):
        return None
    if not isinstance(man, dict) or not isinstance(man.get("files"), dict):
        return None
    return man


def verify_bundle(bundle):
    """Problems with a kit bundle directory against its own MANIFEST.json; [] = clean.

    Checks every listed file exists with the listed sha256, that no unlisted
    file rides along, and that common_block_sha256 is the hash of
    FLEET-COMMON.md (the block conformance() later compares CLAUDE.md to)."""
    bundle = Path(bundle)
    man = _manifest(bundle)
    if man is None:
        return ["bundle manifest missing or unreadable"]
    files = man["files"]
    problems = []
    for name, want in sorted(files.items()):
        f = bundle / name
        if Path(name).name != name:
            problems.append(f"bundle manifest name is not a plain file: {name}")
        elif not f.is_file():
            problems.append(f"bundle file missing: {name}")
        elif _sha256(f) != want:
            problems.append(f"bundle file hash mismatch: {name}")
    for f in sorted(bundle.iterdir()):
        if f.is_file() and f.name != MANIFEST and f.name not in files:
            problems.append(f"bundle file not in manifest: {f.name}")
    if COMMON not in files:
        # Without this, a bundle lacking both FLEET-COMMON.md and
        # common_block_sha256 passed (None == None).
        problems.append(f"bundle manifest does not list {COMMON}")
    elif files[COMMON] != man.get("common_block_sha256"):
        problems.append(f"common_block_sha256 != sha256({COMMON})")
    return problems


def _atomic_copy(src, dest):
    tmp = dest.with_name(dest.name + ".tmp")
    tmp.write_bytes(Path(src).read_bytes())
    tmp.replace(dest)


def copy_bundle(bundle, dest):
    """Copy a verified bundle into dest (ops/fleet_kit/); [] = copied and re-verified.

    Refuses before writing anything when the bundle does not verify. The
    manifest goes last, so an interrupted copy leaves the old manifest and
    conformance() fails loudly instead of passing on a half-new kit."""
    problems = verify_bundle(bundle)
    if problems:
        return problems
    bundle, dest = Path(bundle), Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    for name in sorted(_manifest(bundle)["files"]):
        _atomic_copy(bundle / name, dest / name)
    _atomic_copy(bundle / MANIFEST, dest / MANIFEST)
    return [f"after copy: {p}" for p in _verify_listed(dest)]


def _verify_listed(dest):
    """verify_bundle minus the unlisted-file check: dest may hold local extras."""
    return [p for p in verify_bundle(dest) if not p.startswith("bundle file not in manifest")]


def embed_block(text, block):
    """CLAUDE.md text with block spliced between the FLEET-COMMON markers.

    Raises ValueError unless each marker appears exactly once, BEGIN first."""
    if text.count(BEGIN) != 1 or text.count(END) != 1:
        raise ValueError("CLAUDE.md must carry each FLEET-COMMON marker exactly once")
    i, j = text.find(BEGIN), text.find(END)
    if j < i:
        raise ValueError("FLEET-COMMON END marker precedes BEGIN")
    return text[:i + len(BEGIN)] + block + text[j:]


# ---------------------------------------------------------------- slice 2: chain + CLI

REPO = Path(__file__).resolve().parents[1]
KIT_REL = Path("ops") / "fleet_kit"
_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0) if sys.platform == "win32" else 0


def load_conformance(root):
    """fleet_headless.conformance from root's vendored kit, loaded fresh by
    file path (never a cached import), so a just-copied kit checks itself."""
    path = Path(root) / KIT_REL / "fleet_headless.py"
    spec = importlib.util.spec_from_file_location("_lw_kit_adopt_fleet_headless", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.conformance


def kit_test_files(root):
    """The tests that pin kit behavior: tests/test_fleet_kit_*.py + this module's."""
    tests = Path(root) / "tests"
    files = sorted(tests.glob("test_fleet_kit_*.py"))
    own = tests / "test_lw_kit_adopt.py"
    return files + ([own] if own.is_file() else [])


def run_kit_tests(root, files):
    """(returncode, last output lines) of pytest over files, run in root."""
    cmd = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
           *[str(f) for f in files]]
    try:
        p = subprocess.run(cmd, cwd=str(root), capture_output=True, text=True,
                           timeout=900, creationflags=_NO_WINDOW)
    except (OSError, subprocess.SubprocessError) as exc:
        return 99, f"kit tests did not run: {type(exc).__name__}"
    out = (p.stdout or "") + (p.stderr or "")
    return p.returncode, "\n".join(out.strip().splitlines()[-20:])


def _version(man):
    v = (man or {}).get("version")
    return v if isinstance(v, int) else None


def _atomic_write_bytes(dest, data):
    tmp = dest.with_name(dest.name + ".tmp")
    tmp.write_bytes(data)
    tmp.replace(dest)


def _result(ok, stage, problems=(), residual=()):
    return {"ok": ok, "stage": stage, "problems": list(problems), "residual": list(residual)}


def adopt(bundle, root, run_tests=None, conformance_fn=None):
    """Adopt a delivered kit bundle into root: verify, version, embed-check,
    copy, re-embed CLAUDE.md, conformance, kit tests. Returns _result(...).

    Nothing is written unless verify, version and the CLAUDE.md marker check
    all pass. run_tests=False skips the kit tests; True / None runs run_kit_tests;
    a callable is called instead."""
    bundle, root = Path(bundle), Path(root)
    problems = verify_bundle(bundle)
    if problems:
        return _result(False, "verify", problems)
    new = _version(_manifest(bundle))
    kit = root / KIT_REL
    old = _version(_manifest(kit))
    if new is None:
        return _result(False, "version", ["bundle manifest version is not an integer"])
    if old is not None and new < old:
        return _result(False, "version", [f"bundle v{new} is older than the vendored kit v{old}"])
    claude = root / "CLAUDE.md"
    try:
        text = claude.read_bytes().decode("ascii")
        block = (bundle / COMMON).read_bytes().decode("ascii")
        embedded = embed_block(text, block)
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        return _result(False, "embed", [f"CLAUDE.md: {exc}"])
    problems = copy_bundle(bundle, kit)
    if problems:
        return _result(False, "copy", problems)
    if embedded != text:
        _atomic_write_bytes(claude, embedded.encode("ascii"))
    missing = []
    if old is not None and new != old:
        missing = bump_pins(root, old, new)[1]
    try:
        problems = (conformance_fn or load_conformance(root))(root)
    except Exception as exc:  # noqa: BLE001 - a broken new kit is a reported stage, not a crash
        problems = [f"conformance did not run: {type(exc).__name__}: {exc}"]
    if problems:
        return _result(False, "conformance", problems)
    if run_tests is False:
        return _result(True, "done")
    runner = run_tests if callable(run_tests) else run_kit_tests  # True / None -> default
    rc, tail = runner(root, kit_test_files(root))
    if rc != 0:
        pins = [f"pin not moved: {rel}" for rel in missing]
        return _result(False, "tests", [f"kit tests rc={rc}"],
                       [*pins, f"kit tests rc={rc}: {tail}"])
    return _result(True, "done")


def check(root, conformance_fn=None):
    """conformance() of root as it stands, as a _result; writes nothing."""
    try:
        problems = (conformance_fn or load_conformance(root))(root)
    except Exception as exc:  # noqa: BLE001
        problems = [f"conformance did not run: {type(exc).__name__}: {exc}"]
    return _result(not problems, "done" if not problems else "conformance", problems)


# The tree's own KIT_VERSION pins (LEDGER 357 hand-edited these four). {v} is the version.
VERSION_PINS = (
    ("tests/test_fleet_kit_conformance.py", "    assert _kit().KIT_VERSION == {v}"),
    ("tests/test_headless_env.py", "    assert he.kit.KIT_VERSION == {v}"),
    ("tests/test_promise_probe_fleet_kit.py",
     '    assert pp.FLEET_KIT_VERSION == man["version"] == {v}'),
    ("tools/lw_promise_probes.py", "FLEET_KIT_VERSION = {v}"),
)


def bump_pins(root, old, new):
    """Move each KIT_VERSION pin line old -> new, atomically. Returns (changed,
    missing): a pin that is not where this table says is reported, never guessed."""
    changed, missing = [], []
    for rel, line in VERSION_PINS:
        path = Path(root) / rel
        try:
            data = path.read_bytes().decode("ascii")
        except (OSError, UnicodeDecodeError):
            missing.append(rel)
            continue
        have, want = line.format(v=old), line.format(v=new)
        if have not in data:
            missing.append(rel)
            continue
        _atomic_write_bytes(path, data.replace(have, want, 1).encode("ascii"))
        changed.append(rel)
    return changed, missing


def commit_message(version, order):
    """The adoption commit's message: ASCII, no trailer (FLEET-COMMON 17)."""
    return f"chore(kit): adopt fleet kit v{version} ({order})\n"


def _run_step(root):
    def run(argv):
        return subprocess.run(argv, cwd=str(root), creationflags=_NO_WINDOW,
                              capture_output=True, check=False).returncode
    return run


def _last_ci_conclusion(root):
    done = subprocess.run(
        ["gh", "run", "list", "--branch", "main", "--workflow", "ci", "--limit", "1",
         "--json", "conclusion", "--jq", ".[0].conclusion"],
        cwd=str(root), creationflags=_NO_WINDOW, capture_output=True, text=True, check=False)
    return done.stdout.strip() if done.returncode == 0 else ""


def closeout(root, version, owner, order, *, runner=None, push=False, ci_conclusion=None):
    """The fixed steps after adopt(): stage, ONE gated suite, gitlock commit, optional
    push on a green previous run. A rollout run stops here and runs NO /done.

    WHY (MAIN 2026-11-01-1223 item 3, measured). The v27 rollout run took 1647.4 s:
    about 480 s for the adoption with its 128 s suite, then a nested /done whose
    second suite, on a docs-only commit, queued 683 s behind the other trees' nightly
    adoptions and held 179 s. The hand-off belongs to the next session's /done."""
    root = Path(root)
    run = runner or _run_step(root)
    gitlock = [sys.executable, "ops/fleet_kit/fleet_gitlock.py", "run", "--owner", owner, "--"]
    paths = [KIT_REL.as_posix(), "CLAUDE.md", *[rel for rel, _ in VERSION_PINS]]
    if run(["git", "add", "--", *paths]) != 0:
        return _result(False, "add", ["git add failed"])
    suite = [sys.executable, "ops/fleet_kit/fleet_suite_gate.py", "run", "--owner", owner, "--",
             sys.executable, "tools/lw_suite.py", "-q"]
    rc = run(suite)
    if rc != 0:
        return _result(False, "suite", [f"suite rc={rc}"])
    fd, name = tempfile.mkstemp(prefix="lw_kit_adopt_", suffix=".txt")
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(commit_message(version, order).encode("ascii"))
        rc = run([*gitlock, "git", "commit", "-F", name])
    finally:
        Path(name).unlink(missing_ok=True)
    if rc != 0:
        return _result(False, "commit", [f"commit rc={rc}"])
    if push:
        verdict = (ci_conclusion or _last_ci_conclusion)(root)
        if verdict != "success":
            return _result(False, "ci", [f"previous push reads {verdict or 'unknown'}, not pushed"])
        rc = run([*gitlock, "git", "push", "origin", "main"])
        if rc != 0:
            return _result(False, "push", [f"push rc={rc}"])
    return _result(True, "done")


USAGE = ("usage: lw_kit_adopt.py adopt <bundle> [--root R] [--no-tests]\n"
         "       lw_kit_adopt.py check [--root R]\n"
         "       lw_kit_adopt.py closeout --owner ID --order TEXT [--root R] [--push]")


def main(argv=None):
    import argparse

    argv = sys.argv[1:] if argv is None else list(argv)
    ap = argparse.ArgumentParser(prog="lw_kit_adopt.py", usage=USAGE)
    sub = ap.add_subparsers(dest="cmd")
    a = sub.add_parser("adopt")
    a.add_argument("bundle")
    a.add_argument("--root", default=str(REPO))
    a.add_argument("--no-tests", action="store_true")
    c = sub.add_parser("check")
    c.add_argument("--root", default=str(REPO))
    z = sub.add_parser("closeout")
    z.add_argument("--root", default=str(REPO))
    z.add_argument("--owner", required=True)
    z.add_argument("--order", required=True)
    z.add_argument("--push", action="store_true")
    try:
        args = ap.parse_args(argv)
    except SystemExit:
        return 2
    if args.cmd == "adopt":
        res = adopt(args.bundle, args.root,
                    run_tests=False if args.no_tests else run_kit_tests)
    elif args.cmd == "check":
        res = check(args.root)
    elif args.cmd == "closeout":
        res = closeout(args.root, _version(_manifest(Path(args.root) / KIT_REL)),
                       args.owner, args.order, push=args.push)
    else:
        print(USAGE, file=sys.stderr)
        return 2
    print(json.dumps(res, indent=1))
    return 0 if res["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
