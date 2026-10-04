"""Isolated verification copy of LW's live runtime state (ingest P2-6).

# arch: snapshot ops/runtime/*.json into a verify root that UI/e2e runs may write; dashboards take --runtime-root

WHY. UI fixture audits and end-to-end runs exercise the dashboards against
real state, and a run that writes - or a reader bug that rewrites - must never
touch the operator's live files. Before such a run, snapshot the live state
into a dedicated verify root, point the dashboards at it with
`--runtime-root`, and let the run do what it likes there.

Rules:
  * refuse when source and target are the same directory, or when either
    contains the other's files' directory in a way that would copy a copy
    (target == source, or source inside target);
  * PROVE the copy: same file count, same newest mtime, and the same sha256
    per file - any difference is a failed snapshot (exit 1), never a warning;
  * only a verify copy is ever cleared: a target that already holds files must
    carry the MARKER this tool writes, or the snapshot refuses. The live
    source is never written. (The copy is replaceable data; anything
    irreplaceable still goes to the Recycle Bin.)

Copies the top-level `*.json` files of the source (pipeline_state.json,
slice_manifest.json, job_health.json, served_versions.json, ...), not
subdirectories.

CLI:  python tools/lw_verify_snapshot.py [--source DIR] [--target DIR]
      then: python tools/lw_rundash.py --runtime-root <target>
            python tools/lw_monitor.py --runtime-root <target>
Coverage: tests/test_lw_verify_snapshot.py.
"""
from __future__ import annotations

import argparse
import hashlib
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "ops" / "runtime"
TARGET = ROOT / "ops" / "runtime" / "verify_copy"
MARKER = ".lw_verify_copy"


class SnapshotRefused(RuntimeError):
    """The snapshot would touch something that is not a verify copy."""


def _files(d: Path) -> list[Path]:
    return sorted(p for p in d.glob("*.json") if p.is_file())


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def prove(source_files: list[Path], target: Path) -> list[str]:
    """Differences between the source files and their copies; [] = proven."""
    problems = []
    copies = _files(target)
    if len(copies) != len(source_files):
        problems.append(f"count {len(copies)} != {len(source_files)}")
    if source_files and copies:
        newest_src = max(p.stat().st_mtime for p in source_files)
        newest_dst = max(p.stat().st_mtime for p in copies)
        if abs(newest_src - newest_dst) > 0.01:
            problems.append("newest mtime differs")
    for p in source_files:
        q = target / p.name
        if not q.is_file():
            problems.append(f"missing {p.name}")
        elif _sha(q) != _sha(p):
            problems.append(f"content differs: {p.name}")
    return problems


def snapshot(source: Path = SOURCE, target: Path = TARGET) -> dict:
    source, target = Path(source).resolve(), Path(target).resolve()
    if source == target:
        raise SnapshotRefused("source and target are the same directory")
    if source.is_relative_to(target):
        raise SnapshotRefused("source lies inside the target")
    if not source.is_dir():
        raise SnapshotRefused("source directory does not exist")
    if target.exists():
        held = [p for p in target.iterdir() if p.name != MARKER]
        if held and not (target / MARKER).is_file():
            raise SnapshotRefused("target holds files and is not a verify copy (no marker)")
        for p in _files(target):           # only a marked verify copy is cleared
            p.unlink()
    target.mkdir(parents=True, exist_ok=True)
    (target / MARKER).write_text("lw verify copy - safe to clear\n", encoding="ascii")
    files = _files(source)
    for p in files:
        shutil.copy2(p, target / p.name)
    problems = prove(files, target)
    return {"source": str(source), "target": str(target), "files": len(files),
            "proven": not problems, "problems": problems}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--source", type=Path, default=SOURCE)
    ap.add_argument("--target", type=Path, default=TARGET)
    args = ap.parse_args(argv)
    try:
        res = snapshot(args.source, args.target)
    except SnapshotRefused as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 2
    print(f"{'proven' if res['proven'] else 'NOT PROVEN'}: {res['files']} file(s) -> "
          f"{Path(res['target']).name}" + ("" if res["proven"] else f" {res['problems']}"))
    return 0 if res["proven"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
