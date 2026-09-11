"""Reproduce RC's false-RED probe on LW: run the suite with git OFF PATH.

RC found 39 of its 115 external-binary call sites carry false-RED risk, and
that a guard auditing skip CONDITIONS is structurally blind to an ungated
`subprocess.run([...], check=True)`. RC reproduced rather than static-reading:
with git off PATH, 121 of 139 tests in one file ERROR through a session
fixture. LW has 102 call sites and 9 `shutil.which` guards, so the same probe
is the right one here.

Method: strip every PATH entry that contains a `git.exe` / `git` executable,
assert the child cannot resolve git, then run the full suite in that env.
Writes both runs' output so the DELTA is what gets reported, not the absolute
count - a test that fails with git present is not this probe's finding.
"""
from __future__ import annotations

import json
import os
import pathlib
import shutil
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "ops" / "runtime" / "false_red_probe"
NO_WINDOW = 0x08000000


def path_without_git(env: dict[str, str]) -> str:
    kept = []
    for entry in env.get("PATH", "").split(os.pathsep):
        if not entry.strip():
            continue
        d = pathlib.Path(entry)
        try:
            has_git = (d / "git.exe").exists() or (d / "git").is_file()
        except OSError:
            has_git = False
        if not has_git:
            kept.append(entry)
    return os.pathsep.join(kept)


def run_suite(env: dict[str, str], tag: str) -> dict:
    log = OUT / f"suite_{tag}.txt"
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/", "-q", "--no-header", "-p", "no:cacheprovider"],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        errors="replace",
        creationflags=NO_WINDOW,
    )
    log.write_text(proc.stdout + "\n--- stderr ---\n" + proc.stderr, encoding="utf-8")
    tail = [ln for ln in proc.stdout.splitlines() if ln.strip()][-3:]
    return {"tag": tag, "returncode": proc.returncode, "tail": tail, "log": str(log)}


def failing_ids(tag: str) -> set[str]:
    txt = (OUT / f"suite_{tag}.txt").read_text(encoding="utf-8", errors="replace")
    ids = set()
    for line in txt.splitlines():
        s = line.strip()
        if s.startswith(("FAILED ", "ERROR ")):
            ids.add(s.split(" ", 1)[1].split(" - ")[0])
    return ids


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    base = dict(os.environ)
    stripped = dict(base)
    stripped["PATH"] = path_without_git(base)

    resolved = subprocess.run(
        [sys.executable, "-c", "import shutil,json;print(json.dumps(shutil.which('git')))"],
        env=stripped,
        capture_output=True,
        text=True,
        creationflags=NO_WINDOW,
    ).stdout.strip()
    if json.loads(resolved) is not None:
        print(f"ABORT: git still resolvable in the stripped env: {resolved}")
        return 2
    print("git is NOT resolvable in the stripped env - probe is valid")

    with_git = run_suite(base, "with_git")
    print("with_git:", with_git["returncode"], with_git["tail"])
    without = run_suite(stripped, "no_git")
    print("no_git:", without["returncode"], without["tail"])

    base_bad = failing_ids("with_git")
    no_git_bad = failing_ids("no_git")
    new = sorted(no_git_bad - base_bad)
    report = {
        "with_git": with_git,
        "no_git": without,
        "failing_with_git": len(base_bad),
        "failing_no_git": len(no_git_bad),
        "new_failures_caused_by_missing_git": new,
        "new_failure_count": len(new),
    }
    (OUT / "probe_no_git.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"NEW failures attributable to missing git: {len(new)}")
    for item in new[:40]:
        print("  ", item)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
