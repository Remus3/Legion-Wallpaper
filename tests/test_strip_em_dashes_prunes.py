"""strip_em_dashes' filesystem fallback must PRUNE, not post-filter.

THE DEFECT, measured on the authoring box 2026-09-19 during the machine
stray-work sweep. `_tracked_files()` prefers `git ls-files -z`, which walks
nothing and excludes everything gitignored for free. Its FALLBACK read:

    return [p for p in ROOT.rglob("*") if p.is_file()]

with the skip predicate applied afterwards, in the consuming loop. `rglob("*")`
materialises the whole tree before one path is excluded: 199,691 entries and
1.40 s warm on this repo, because it descends `.venv-gen` (41,563 files),
`.venv-metrics` (45,712), `.venv-upscale` (22,584), `.venv-poc` (6,564) and
`Claude/` (47,109 - Claude Desktop app data, not project content).

A post-filter is not a prune. The old code returned the RIGHT file list, so a
test that only checks the returned list passes against both the defect and the
fix. That is why the binding arm here records which directories `os.walk`
actually descended into: it is the only assertion the defect can fail.

The second half of the defect: the module docstring says the walk fallback
"relies on [the exclusions] entirely", but `_SKIP_DIR_PARTS` never carried
`.venv-*`. Under git, gitignore hid the venvs; without git, the fallback would
have decoded 116,423 virtualenv files looking for em-dashes. The exclusion set
was only ever complete in the mode that did not need it.

WHEN THE FALLBACK FIRES: when `git ls-files -z` raises or returns empty - an
unborn repo, a half-written clone, a held index lock, a corrupt tree. The
slowest path was bolted to the worst moment.

HERMETIC: every arm builds its own throwaway tree in tmp_path and walks THAT.
Nothing here reads this machine's repo, so it passes identically in CI.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

import strip_em_dashes as sed  # noqa: E402

EM = chr(0x2014)


def _build(root: Path) -> None:
    """A tree holding one offender in every place the walker must not go."""
    body = f"a {EM} b\n"
    (root / "good.md").write_text(body, encoding="utf-8")
    for rel in (
        "Claude/Cache/deep/bad.md",          # app data, root-anchored skip
        ".venv-gen/lib/site-packages/bad.md",  # gitignored virtualenv
        ".venv-metrics/lib/bad.md",
        "__pycache__/bad.md",
        "docs/_archive/bad.md",              # immutable history
        "logs/bad.md",                       # append-only
        "sub/nested/ok.md",                  # must be FOUND
    ):
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(body, encoding="utf-8")


def test_walk_returns_only_files_outside_the_exclusions(tmp_path):
    """The file list itself. Necessary, and NOT sufficient - see the next arm."""
    _build(tmp_path)
    found = {p.relative_to(tmp_path).as_posix() for p in sed._walk_files(tmp_path)}
    assert found == {"good.md", "sub/nested/ok.md"}


def test_walk_never_descends_into_an_excluded_directory(tmp_path):
    """THE BINDING ARM. A post-filter returns the same list but still descends.

    Records every directory os.walk yields. Under the old
    `rglob("*")`-then-filter shape this fails on the first excluded child,
    because rglob has no way to be told not to go in.
    """
    _build(tmp_path)
    visited: list[str] = []
    real_walk = os.walk

    def recording_walk(top, *a, **kw):
        for dirpath, dirnames, filenames in real_walk(top, *a, **kw):
            visited.append(Path(dirpath).relative_to(tmp_path).as_posix())
            yield dirpath, dirnames, filenames

    sed.os.walk = recording_walk
    try:
        sed._walk_files(tmp_path)
    finally:
        sed.os.walk = real_walk

    forbidden = ("Claude", ".venv-gen", ".venv-metrics", "__pycache__",
                 "_archive", "logs")
    descended = [d for d in visited
                 if any(part in forbidden for part in Path(d).parts)]
    assert descended == [], f"walk descended into excluded trees: {descended}"
    assert "sub/nested" in visited, "the walk must still reach real content"


def test_root_anchored_skip_stays_root_anchored(tmp_path):
    """`Claude` is excluded at the ROOT only - a nested one is project content.

    _SKIP_ROOT_DIRS exists because the app-data directory sits at the repo
    root; widening it to every depth would silently drop a real `docs/Claude/`
    page. Narrow first, widen only on evidence.
    """
    (tmp_path / "docs" / "Claude").mkdir(parents=True)
    (tmp_path / "docs" / "Claude" / "page.md").write_text(
        f"a {EM} b\n", encoding="utf-8")
    (tmp_path / "Claude").mkdir()
    (tmp_path / "Claude" / "app.md").write_text(f"a {EM} b\n", encoding="utf-8")

    found = {p.relative_to(tmp_path).as_posix() for p in sed._walk_files(tmp_path)}
    assert found == {"docs/Claude/page.md"}


def test_binary_and_log_extensions_still_drop_at_file_level(tmp_path):
    """Pruning is for DIRECTORIES; the per-file carve-outs must survive it."""
    for rel in ("a.png", "b.jsonl", "c.log", "d.log.3", "keep.md"):
        (tmp_path / rel).write_text("x\n", encoding="utf-8")
    found = {p.relative_to(tmp_path).as_posix() for p in sed._walk_files(tmp_path)}
    assert found == {"keep.md"}


def test_fallback_is_wired_to_the_pruned_walker(tmp_path, monkeypatch):
    """_tracked_files() must REACH _walk_files when git is unusable.

    Without this the prune is dead code: the defect was never in the walker,
    it was in what the fallback called.
    """
    called: list[Path] = []

    def fake_walk_files(root):
        called.append(Path(root))
        return []

    def boom(*a, **kw):
        raise OSError("git is unusable")

    monkeypatch.setattr(sed, "_walk_files", fake_walk_files)
    monkeypatch.setattr(sed.subprocess, "run", boom)
    sed._tracked_files()
    assert called == [sed.ROOT]
