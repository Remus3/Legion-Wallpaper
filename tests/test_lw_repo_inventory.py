"""tools/lw_repo_inventory.py - on-disk file census for the repo review.

The REPO-REVIEW ORDER (MAIN 2246 s8) accepts only when the reviewed file
count equals the on-disk count (tracked + untracked + ignored, .git
internals excluded). These tests pin the walk and the status split on a
throwaway git repo so the census cannot silently skip a class.
"""
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import lw_repo_inventory as inv  # noqa: E402


def _git(root, *args):
    subprocess.run(["git", *args], cwd=root, check=True, capture_output=True,
                   creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))


def _mkrepo(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    _git(root, "init", "-q")
    (root / ".gitignore").write_text("ignored/\n*.log\n", encoding="ascii")
    (root / "a.py").write_text("x = 1\n", encoding="ascii")
    (root / "sub").mkdir()
    (root / "sub" / "b.md").write_text("b\n", encoding="ascii")
    _git(root, "add", ".gitignore", "a.py", "sub/b.md")
    (root / "new.txt").write_text("u\n", encoding="ascii")          # untracked
    (root / "ignored").mkdir()
    (root / "ignored" / "w.bin").write_bytes(b"\x00" * 10)        # ignored
    (root / "sub" / "run.log").write_text("l\n", encoding="ascii")  # ignored
    return root


def test_walk_excludes_git_internals_only(tmp_path):
    root = _mkrepo(tmp_path)
    files = inv.walk(root)
    assert ".git/HEAD" not in files
    assert not any(f.startswith(".git/") for f in files)
    assert sorted(files) == sorted([
        ".gitignore", "a.py", "sub/b.md", "new.txt", "ignored/w.bin", "sub/run.log"])


def test_status_split_covers_every_file_once(tmp_path):
    root = _mkrepo(tmp_path)
    census = inv.census(root)
    assert census["total"] == 6
    assert census["by_status"] == {"tracked": 3, "untracked": 1, "ignored": 2}
    assert sum(census["by_status"].values()) == census["total"]
    assert sum(c["count"] for c in census["classes"]) == census["total"]


def test_classes_group_by_top_folder_extension_status(tmp_path):
    root = _mkrepo(tmp_path)
    classes = {(c["top"], c["ext"], c["status"]): c["count"]
               for c in inv.census(root)["classes"]}
    assert classes[("ignored", ".bin", "ignored")] == 1
    assert classes[("sub", ".log", "ignored")] == 1
    assert classes[("sub", ".md", "tracked")] == 1
    assert classes[("(root)", ".py", "tracked")] == 1


def test_by_top_counts(tmp_path):
    root = _mkrepo(tmp_path)
    by_top = inv.census(root)["by_top"]
    assert by_top == {"(root)": 3, "sub": 2, "ignored": 1}
