"""C-SLUG-SIBLINGS: one resolver for this repo's Claude project slug.

CONFIG-SLUG (b14ce18) moved ops/loop/config*.json `transcript_dir` to the live
`E--Legion-Wallpaper` store, but five tool sites still hardcoded the dead
`C--Legion-Wallpaper` slug (claimed_green_gate PROJECT_SESSIONS, drift_guard
MEMORY_DIR, lw_agent_mirror PROJECT_SESSIONS, lw_rundash TRANSCRIPT_DIR,
lw_transcript_union DEFAULT_CANON_KEY). They now all read
`lw_paths.project_slug()` / `lw_paths.claude_project_sessions()`, which take the
slug from the loop config's `transcript_dir` (the one place it is written) and
fall back to deriving it from the MAIN checkout root.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import lw_paths  # noqa: E402

LIVE_SLUG = "E--Legion-Wallpaper"
SITES = ("claimed_green_gate.py", "drift_guard.py", "lw_agent_mirror.py",
         "lw_rundash.py", "lw_transcript_union.py")


def test_slug_encodes_every_non_alnum_char_as_a_hyphen():
    assert lw_paths.slug_for("E:\\Legion Wallpaper") == LIVE_SLUG
    assert lw_paths.slug_for("E:/Legion Wallpaper") == LIVE_SLUG
    assert lw_paths.slug_for("/home/runner/work/a b") == "-home-runner-work-a-b"


def test_project_slug_matches_the_loop_config():
    doc = json.loads((ROOT / "ops" / "loop" / "config.json").read_text(encoding="utf-8"))
    assert Path(doc["transcript_dir"]).name == LIVE_SLUG
    assert lw_paths.project_slug() == LIVE_SLUG


def test_project_slug_falls_back_to_the_main_checkout(tmp_path):
    main = tmp_path / "My Tree"
    (main / ".git" / "worktrees" / "w1").mkdir(parents=True)
    wt = main / ".claude" / "worktrees" / "w1"
    wt.mkdir(parents=True)
    (wt / ".git").write_text("gitdir: " + str(main / ".git" / "worktrees" / "w1") + "\n",
                             encoding="utf-8")
    assert lw_paths.main_checkout_root(wt) == main
    assert lw_paths.main_checkout_root(main) == main
    # No loop config under this root -> derived from the main checkout.
    assert lw_paths.project_slug(wt) == lw_paths.slug_for(main)


def test_claude_project_sessions_is_the_slug_dir():
    assert lw_paths.claude_project_sessions() == lw_paths.claude_project_dir(LIVE_SLUG)


def test_every_site_routes_through_the_resolver():
    import claimed_green_gate
    import drift_guard
    import lw_agent_mirror
    import lw_transcript_union
    from tools import lw_rundash

    want = lw_paths.claude_project_sessions()
    assert claimed_green_gate.PROJECT_SESSIONS == want
    assert drift_guard.MEMORY_DIR == want / "memory"
    assert lw_agent_mirror.PROJECT_SESSIONS == want
    assert lw_rundash.TRANSCRIPT_DIR == want
    assert lw_transcript_union.DEFAULT_CANON_KEY == LIVE_SLUG


def test_no_site_quotes_the_dead_c_slug():
    lit = re.compile(r"""["']C--Legion-Wallpaper["']""")
    for name in SITES:
        text = (ROOT / "tools" / name).read_text(encoding="utf-8")
        assert not lit.search(text), name
