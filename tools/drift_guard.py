"""Per-session drift guard for Legion Wallpaper. Cheap invariant checks at /done.

Exit 0 = clean, 1 = at least one breach. Adapted from the machine-wide ritual doc
(DONE_RITUAL_OPTIMIZED.md, 2026-07-26). Every check exists because the drift it
catches actually happened on a project on this box and later cost a dedicated
cleanup session.

LW-specific deviations from the reference implementation, each measured:
- MIRROR_PAIRS (tools/*.md <-> .claude/commands/*.md) is a NO-OP here: the two
  dirs share zero basenames. Replaced by LW's real duplicated-invariant risk -
  every .claude/commands/*.md must carry the SUBAGENT-FIRST block (CLAUDE.md).
- Untracked-authored is still checked but points at .claude/commands, which LW
  tracks in git (unlike RC, where it was gitignored and silently unversioned).
- Version-anchor stays wired but dormant: LW has no shipped version string yet.
"""
from __future__ import annotations

import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

# CREATE_NO_WINDOW: 0 on non-Windows so the module still imports/tests in CI.
# Under a pythonw.exe parent (every hook + scheduled task here) a console child
# allocates its OWN window and flashes over the desktop.
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)

# ---- CONFIG - the only per-project section -------------------------------
# CLAUDE.md budget is real and CI-enforced (CLAUDE.md: "CI size-budgeted < 60KB").
# ROADMAP.md is advisory here - LW states no hard budget for it.
DOC_BUDGETS = {"CLAUDE.md": 61440}
DOC_BUDGETS_ADVISORY = {"ROADMAP.md": 81920}
COMMANDS_DIR = ".claude/commands"
COMMANDS_MARKER = "SUBAGENT-FIRST"
MEMORY_DIR = pathlib.Path(
    r"C:\Users\Administrator\.claude\projects\C--LegionWallpaper\memory"
)
MEMORY_INDEX = "MEMORY.md"
MEMORY_UNINDEXED_OK = ()
DOC_GLOBS = ["docs/**/*.md", "*.md"]
DOC_EXCLUDE = ("_archive", "node_modules", ".git", "worktrees", ".venv")
# --------------------------------------------------------------------------

problems: list[str] = []
notes: list[str] = []


def warn(msg: str) -> None:
    problems.append(msg)


def _authored_docs() -> list[pathlib.Path]:
    out: list[pathlib.Path] = []
    for g in DOC_GLOBS:
        for p in ROOT.glob(g):
            if p.is_file() and not any(x in p.as_posix() for x in DOC_EXCLUDE):
                out.append(p)
    return out


def check_doc_budgets() -> None:
    for name, budget in DOC_BUDGETS.items():
        p = ROOT / name
        if not p.exists():
            warn(f"DOC BUDGET: {name} missing")
            continue
        n = p.stat().st_size
        pct = 100 * n / budget
        if n > budget:
            warn(f"DOC BUDGET: {name} is {n} bytes, OVER its {budget} budget")
        elif pct >= 90:
            warn(f"DOC BUDGET: {name} at {pct:.0f}% of budget - relocate soon")
        else:
            notes.append(f"{name} {pct:.0f}% of {budget} budget")
    for name, budget in DOC_BUDGETS_ADVISORY.items():
        p = ROOT / name
        if p.exists():
            notes.append(f"{name} {100 * p.stat().st_size / budget:.0f}% (advisory)")


def check_command_marker() -> None:
    """LW invariant: every command doc carries the SUBAGENT-FIRST block."""
    d = ROOT / COMMANDS_DIR
    if not d.is_dir():
        notes.append(f"{COMMANDS_DIR} absent - marker check skipped")
        return
    files = sorted(d.glob("*.md"))
    missing = [f.name for f in files
               if COMMANDS_MARKER.lower() not in
               f.read_text(encoding="utf-8", errors="replace").lower()]
    if missing:
        warn(f"COMMAND MARKER: {len(missing)} missing {COMMANDS_MARKER}: {missing[:6]}")
    else:
        notes.append(f"{len(files)} command docs carry {COMMANDS_MARKER}")


def check_memory_index() -> None:
    if not MEMORY_DIR.is_dir():
        warn(f"MEMORY: {MEMORY_DIR} not found")
        return
    idx = MEMORY_DIR / MEMORY_INDEX
    if not idx.exists():
        warn(f"MEMORY: no {MEMORY_INDEX}")
        return
    text = idx.read_text(encoding="utf-8", errors="replace")
    files = {p.stem for p in MEMORY_DIR.glob("*.md") if p.name != MEMORY_INDEX}
    linked = set(re.findall(r"\]\(([A-Za-z0-9_.\-]+)\.md\)", text))
    dead = sorted(linked - files)
    if dead:
        warn(f"MEMORY: {len(dead)} dead index link(s): {dead[:5]}")
    unindexed = sorted(
        f for f in (files - linked)
        if not (MEMORY_UNINDEXED_OK and f.startswith(MEMORY_UNINDEXED_OK))
    )
    if unindexed:
        warn(f"MEMORY: {len(unindexed)} unindexed: {unindexed[:6]}")
    if not dead and not unindexed:
        notes.append(f"memory index clean ({len(files)} files)")


def check_version_anchors(old_version: str | None) -> None:
    """After a version bump, no authored doc may still name the OLD version."""
    if not old_version:
        return
    hits = []
    for p in list(_authored_docs()) + list(ROOT.glob("docs/**/*.html")):
        try:
            if old_version in p.read_text(encoding="utf-8", errors="replace"):
                hits.append(p.relative_to(ROOT).as_posix())
        except OSError:
            continue
    hits = [h for h in hits
            if not re.search(r"CHANGELOG|HISTORY|LEDGER|_archive|WAKEUP", h, re.I)]
    if hits:
        warn(f"VERSION ANCHOR: {old_version} still present in {hits}")


def check_counted_claims() -> None:
    """A doc saying 'the N most recent' above a list of a different length."""
    words = {"three": 3, "five": 5, "ten": 10, "twelve": 12,
             "fifteen": 15, "twenty": 20}
    for p in _authored_docs():
        text = p.read_text(encoding="utf-8", errors="replace")
        m = re.search(r"[Tt]he (\w+) most recent", text)
        if not m:
            continue
        claimed = words.get(m.group(1).lower())
        if claimed is None:
            continue
        actual = len(re.findall(r"^- \d+\.\d+\.\d+ ->", text[m.end():], re.M))
        if actual and actual != claimed:
            warn(f"COUNT CLAIM: {p.relative_to(ROOT).as_posix()} says "
                 f"'{m.group(1)} most recent' but lists {actual}")


def check_untracked_authored() -> None:
    """Authored command docs git is not tracking - LW tracks .claude/ on purpose."""
    d = ROOT / COMMANDS_DIR
    if not d.is_dir():
        return
    bad = []
    for f in sorted(d.glob("*.md")):
        rel = f.relative_to(ROOT).as_posix()
        r = subprocess.run(
            ["git", "-C", str(ROOT), "ls-files", "--error-unmatch", rel],
            capture_output=True, text=True, creationflags=NO_WINDOW,
        )
        if r.returncode != 0:
            bad.append(rel)
    if bad:
        warn(f"UNTRACKED: {len(bad)} authored command doc(s) not in git: {bad[:5]}")


def check_cited_shas() -> None:
    """SHAs cited in staged docs must resolve (worktree-slice SHAs often do not)."""
    r = subprocess.run(
        ["git", "-C", str(ROOT), "diff", "--cached", "-U0"],
        capture_output=True, text=True, creationflags=NO_WINDOW,
    )
    added = [ln for ln in r.stdout.splitlines() if ln.startswith("+")]
    shas = set(re.findall(r"\b([0-9a-f]{7,8})\b", "\n".join(added)))
    for sha in sorted(shas)[:40]:
        ok = subprocess.run(
            ["git", "-C", str(ROOT), "cat-file", "-e", f"{sha}^{{commit}}"],
            capture_output=True, creationflags=NO_WINDOW,
        )
        if ok.returncode != 0:
            notes.append(f"cited SHA {sha} does not resolve (worktree slice?)")


SHARED_LOOP_FILES = ("ops/loop/slots.py", "ops/loop/winmutex.py")
SIBLING_REPO = pathlib.Path(r"C:\Riot Commander")


def check_shared_loop_files() -> None:
    """slots.py + winmutex.py must be BYTE-IDENTICAL in LW and RC.

    They coordinate the two repos' concurrent runs with each other through
    C:\\ProgramData\\lw-loop and the OS mutex namespace, so a divergence is not a
    merge conflict anyone notices - it is a silent concurrency bug (two loops
    each believing they hold the only slot). A NOTE while RC has not adopted
    them yet; a BREACH the moment both copies exist and differ.
    """
    import hashlib

    for rel in SHARED_LOOP_FILES:
        mine, theirs = ROOT / rel, SIBLING_REPO / rel
        if not mine.is_file():
            continue
        if not theirs.is_file():
            notes.append(f"{rel} not yet ported to RC (shared-file contract pending)")
            continue
        h1 = hashlib.sha256(mine.read_bytes()).hexdigest()
        h2 = hashlib.sha256(theirs.read_bytes()).hexdigest()
        if h1 != h2:
            problems.append(
                f"{rel} DIVERGED from RC ({h1[:8]} vs {h2[:8]}) - the two loops "
                f"coordinate through it; a divergence is a silent concurrency bug")


def check_git_hooks() -> None:
    """The authoritative glyph/ruff gate lives in .git/hooks, which git does NOT
    track - so without this check it silently un-installs itself on a fresh clone.
    That matters more than it sounds: RC measured that a headless
    `claude -p --permission-mode bypassPermissions` run bypasses the Claude
    PreToolUse gate entirely, leaving the git hook as the only backstop.
    """
    installer = ROOT / "tools" / "install_git_hooks.py"
    if not installer.is_file():
        return
    r = subprocess.run(
        [sys.executable, str(installer), "--check", "--repo", str(ROOT)],
        capture_output=True, text=True, creationflags=NO_WINDOW,
    )
    if r.returncode != 0:
        problems.append((r.stderr or r.stdout).strip().splitlines()[0][:160]
                        if (r.stderr or r.stdout).strip() else "git-hook gate drift")


# --------------------------------------------------------------------------
# Agent-config checks. Surface adapted from ECC/AgentShield's published scan
# list (settings, hooks, agents, secrets), reduced to what maps to a failure
# THIS box actually had. Both of the first two are written up in CLAUDE.md and
# neither had a check afterwards, which is why they could recur silently.
# --------------------------------------------------------------------------
SETTINGS_REL = ".claude/settings.json"
CLAUDE_HOME_JSON = pathlib.Path.home() / ".claude.json"
HOOK_SCRIPT_GLOBS = ("tools/*guard*.py", ".githooks/*")


def scan_settings(raw: str) -> list[str]:
    """Issues in a `.claude/settings.json` body. Empty list = clean.

    Validity is checked FIRST and short-circuits, because an unparsed config
    presents exactly as a config with no hooks - the false "hooks do not fire"
    reading recorded in CLAUDE.md. A single backslash before a drive letter is
    not a valid JSON escape, and nothing warns you.
    """
    import json as _json
    try:
        d = _json.loads(raw)
    except ValueError as exc:
        return [f"{SETTINGS_REL}: invalid JSON, silently unparsed ({exc})"]
    out: list[str] = []
    perm = d.get("permissions") or {}
    allow = perm.get("allow") or []
    deny = perm.get("deny") or []
    wild = [a for a in allow
            if str(a).strip() in ("*", "Bash", "Bash(*)") or str(a).endswith("(*)")]
    if wild:
        out.append(f"{SETTINGS_REL}: wildcard allow entries {wild[:4]}")
    if allow and not deny:
        out.append(f"{SETTINGS_REL}: {len(allow)} allow rule(s) and an empty deny list")
    return out


def scan_hook_script(text: str, name: str) -> list[str]:
    """Issues in a hook script body. A hook is a GATE; these make it fail open.

    Silent suppression is the one with precedent: `.githooks/pre-commit` invoked
    the gate with no args for weeks, and with no args the gate self-gates to a
    no-op - it ran on every commit and gated nothing.
    """
    out: list[str] = []
    if "2>/dev/null" in text or "2>$null" in text or "|| true" in text:
        out.append(f"{name}: suppresses its own errors (gate can fail open)")
    if re.search(r"\brequests\b|urllib\.request|\bcurl\b|\bwget\b|Invoke-WebRequest",
                 text):
        out.append(f"{name}: makes network calls from a hook")
    if re.search(r"shell\s*=\s*True", text):
        out.append(f"{name}: shell=True")
    return out


def collide_path_keys(projects: dict) -> list[tuple]:
    """Project keys in ~/.claude.json that name ONE directory but disagree.

    The keys are path-separator- and case-sensitive, so `C:/x` and `C:\\x` are
    two entries for one project. Only DISAGREEING duplicates are returned:
    agreeing ones are untidy but harmless, and reporting them would bury the
    case that actually breaks a run - a headless session landing on the
    spelling whose trust is False discards `permissions.allow` in silence.
    """
    norm: dict[str, list[str]] = {}
    for k in projects:
        n = str(k).replace("/", "\\").rstrip("\\").lower()
        norm.setdefault(n, []).append(k)
    out = []
    for n, keys in sorted(norm.items()):
        if len(keys) < 2:
            continue
        trusts = [(projects[k] or {}).get("hasTrustDialogAccepted") for k in keys]
        if len(set(trusts)) > 1:
            out.append((n, keys, trusts))
    return out


def check_agent_config() -> None:
    p = ROOT / SETTINGS_REL
    if p.is_file():
        for issue in scan_settings(p.read_text(encoding="utf-8", errors="replace")):
            # Invalid JSON is a BREACH: it disarms every hook without a word.
            # Permission-shape findings are NOTES - this box deliberately runs
            # bypassPermissions, so they are advice, not drift.
            if "invalid JSON" in issue:
                warn(issue)
            else:
                notes.append(issue)
    me = pathlib.Path(__file__).resolve()
    for g in HOOK_SCRIPT_GLOBS:
        for f in sorted(ROOT.glob(g)):
            # A scanner must not scan the file that DEFINES its patterns: every
            # detection string appears there literally, so it would report
            # itself for all three findings and bury the real ones.
            if not f.is_file() or f.resolve() == me:
                continue
            for issue in scan_hook_script(
                    f.read_text(encoding="utf-8", errors="replace"), f.name):
                warn(issue)


def check_claude_path_keys(projects: dict | None = None) -> None:
    """Cross-project: one bad spelling here silently disarms a headless run.

    `projects` is injectable so this is testable without a real ~/.claude.json.
    Reading the operator's live file made the first version of the test pass
    locally and fail in CI, where the file does not exist - a machine-dependent
    test, which is the failure this repo's verification discipline exists to
    catch.
    """
    import json as _json
    if projects is None:
        if not CLAUDE_HOME_JSON.is_file():
            return
        try:
            d = _json.loads(
                CLAUDE_HOME_JSON.read_text(encoding="utf-8", errors="replace"))
        except ValueError:
            warn("~/.claude.json: invalid JSON")
            return
        projects = d.get("projects") or {}
    mine = str(ROOT).replace("/", "\\").rstrip("\\").lower()
    for n, keys, trusts in collide_path_keys(projects):
        msg = (f"~/.claude.json: {n} has {len(keys)} spellings with DISAGREEING "
               f"trust {trusts} - a headless run on the False one drops permissions")
        # A breach only when it is THIS project: another repo's key is worth
        # surfacing but must not wedge LW's /done behind a fix nobody here owns.
        if n == mine:
            warn(msg)
        else:
            notes.append(msg)


def main() -> int:
    old_version = sys.argv[1] if len(sys.argv) > 1 else None
    check_doc_budgets()
    check_command_marker()
    check_memory_index()
    check_version_anchors(old_version)
    check_counted_claims()
    check_untracked_authored()
    check_cited_shas()
    check_git_hooks()
    check_shared_loop_files()
    check_agent_config()
    check_claude_path_keys()

    for n in notes:
        print(f"  note   : {n}")
    for p in problems:
        print(f"  BREACH : {p}")
    print(f"drift_guard: {len(problems)} breach(es), {len(notes)} note(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
