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

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import lw_model_pins  # noqa: E402  (sibling tool, not a package)
import lw_paths  # noqa: E402  (sibling tool, not a package)

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
MEMORY_DIR = lw_paths.claude_project_dir("C--Legion-Wallpaper") / "memory"
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


# Directory prefixes whose tracked-but-ignored state is DELIBERATE, so they
# report as a note instead of a breach. Explicit prefixes only, each with the
# reason - never a blanket suppression, because the sibling-file trap below is
# live in exactly these directories.
IGNORED_TRACKED_EXEMPT = (
    # DELIBERATELY EMPTY. This arm found exactly one hit when it was written -
    # docs/_archive/**, swallowed by an unanchored `_archive/` that was meant for
    # the ROOT audit-cleanup quarantine and matched at every depth, which made
    # `git add -A` on a new file beside the tracked sha-rewrite maps exit 0 and
    # add nothing. That CAUSE was fixed (.gitignore now anchors `/_archive/` and
    # names the archive's runtime artifacts explicitly), so the exemption it
    # needed is retired rather than left behind as a standing hole. Add an entry
    # here ONLY with a comment saying why that path is ignored on purpose.
)
IGNORED_TRACKED_SAMPLE = 5


def find_tracked_but_ignored(repo: pathlib.Path | str) -> list[str]:
    """Tracked paths that the ignore rules would nonetheless ignore.

    ONE batched `check-ignore --stdin` fed from `ls-files`, not one spawn per
    file: this runs at every session start against 450+ tracked paths. Both
    sides use -z because LW's own root has a space in it and paths here do too.

    `check-ignore` exits 1 for "nothing matched", which is the CLEAN case, and
    128 for a real error; only 0 and 1 are answers. `--no-index` is what makes
    the question askable at all - without it git reports what the INDEX says
    (tracked, therefore not ignored) and the answer is always empty.
    """
    repo = str(repo)
    ls = subprocess.run(
        ["git", "-C", repo, "ls-files", "-z"],
        capture_output=True, text=True, creationflags=NO_WINDOW,
    )
    if ls.returncode != 0 or not ls.stdout:
        return []
    ci = subprocess.run(
        ["git", "-C", repo, "check-ignore", "-z", "--no-index", "--stdin"],
        input=ls.stdout, capture_output=True, text=True, creationflags=NO_WINDOW,
    )
    if ci.returncode not in (0, 1):
        return []
    return sorted(p for p in ci.stdout.split("\0") if p)


def check_tracked_but_ignored(repo: pathlib.Path | str | None = None) -> None:
    r"""An ignore rule covering a directory that already holds TRACKED files.

    THE TRAP. This .gitignore is deny-by-default with re-includes (images/**,
    tools/models/*, ops/loop/control/*). Where a rule covers a directory that
    already has tracked files, git keeps those - the index wins over .gitignore
    for a path already in it - but every NEW sibling created there is silently
    un-addable. Measured on this repo 2026-09-08:

        echo x > docs/_archive/_probe.md ; git add -A ; git status --porcelain
        -> exit 0, NO output, the file never lands.

    `git add -A` does not warn; only naming the path explicitly earns a hint,
    and nothing in the normal add-commit flow does that. The directory LOOKS
    tracked because six files in it are, so nothing on the surface says the
    seventh will vanish. Same "presence is not proof" class as the hook gate.

    SEVERITY, chosen after running it against the live repo rather than in the
    abstract. It reported six real paths, all of them deliberately tracked, so
    a flat breach would have shipped a permanently-red /done and taught the
    operator to skim past it - the way a gate dies. But a flat note would be a
    blanket suppression of a trap that is live TODAY. So: an explicit,
    individually-commented prefix in IGNORED_TRACKED_EXEMPT downgrades to a
    note that still names the directory and the fix; anything else is a BREACH,
    because an ignore rule newly swallowing a tracked path is drift that will
    eat the next file written beside it.
    """
    repo = ROOT if repo is None else repo
    hits = find_tracked_but_ignored(repo)
    if not hits:
        notes.append("no tracked path is covered by an ignore rule")
        return
    known = [h for h in hits if h.startswith(IGNORED_TRACKED_EXEMPT)]
    rogue = [h for h in hits if not h.startswith(IGNORED_TRACKED_EXEMPT)]
    if known:
        dirs = sorted({d for d in IGNORED_TRACKED_EXEMPT
                       if any(h.startswith(d) for h in known)})
        notes.append(
            f"{len(known)} tracked path(s) sit under an ignore rule by design "
            f"({', '.join(dirs)}) - a NEW sibling file there is silently "
            f"un-addable: `git add` exits 0, prints nothing, and it never "
            f"lands. Narrow the covering .gitignore rule (or re-include the "
            f"dir) before adding anything beside them."
        )
    if rogue:
        warn(
            f"IGNORED-BUT-TRACKED: {len(rogue)} tracked path(s) match an ignore "
            f"rule: {rogue[:IGNORED_TRACKED_SAMPLE]}. Git keeps these because "
            f"the index already holds them, but any NEW sibling file is "
            f"silently un-addable - `git add` exits 0, prints nothing, and the "
            f"file never lands. Run `git check-ignore -v <path>` to find the "
            f"rule, then narrow or re-include it in .gitignore - or, if the "
            f"rule is right, `git rm --cached` the paths. Deliberate cases go "
            f"in IGNORED_TRACKED_EXEMPT with a comment saying why."
        )


def check_model_pins(pins_path: str | None = None) -> None:
    """Pinned model weights on disk still hash to the bytes the manifest pins.

    lw_upscale RECORDS model_sha256 into every audit and, until 2026-09-08,
    nothing ever ASSERTED it. A re-fetched or corrupted weight would drift the
    frozen golden (pv 6d43a6d4) while the provenance record still looked
    perfect. Recorded is not pinned. ABSENT is a note, not a breach: CI and a
    fresh clone have no weights, and absent must never read as verified.
    """
    # OSError = manifest missing/unreadable, ValueError = will not parse
    # (json.JSONDecodeError subclasses it). Both are drift: an unparsed manifest
    # presents exactly like one with no pins, the .claude/settings.json trap.
    try:
        summary = lw_model_pins.verify_pins(pins_path=pins_path)
    except (OSError, ValueError) as exc:
        warn(f"MODEL PINS: manifest unreadable ({exc.__class__.__name__}: {exc})")
        return
    # DELIBERATE: the LW_ALLOW_MODEL_PIN_MISMATCH hatch is RUN-scoped and does
    # not reach here. It lets one inference run proceed on an unpinned weight;
    # it does not make the recorded calibration true. This gate reports STATE
    # and stays red until the manifest says which bytes are now calibrated.
    for r in summary["results"]:
        if r.failed:
            warn(f"MODEL PIN MISMATCH: {r.describe()}")
    if summary["absent"]:
        notes.append(
            f"{len(summary['absent'])} pinned model weight(s) absent - not "
            "verified (expected on CI and a fresh clone; weights are gitignored)"
        )
    if summary["verified"]:
        notes.append(f"{len(summary['verified'])} pinned model weight(s) verified")


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


def _name_key(name: str) -> str:
    """Fold a directory name to what survives a re-spelling."""
    return re.sub(r"[^a-z0-9]", "", name.lower())


def resolve_sibling_root(configured):
    r"""Locate a sibling repo root, telling a RENAME apart from an ABSENCE.

    Returns (path, status) with status one of:
      present  - the configured path exists
      renamed  - it does not, but a name-equivalent directory sits beside it
      absent   - nothing resembling it is there (a CI runner, legitimately)

    WHY THIS EXISTS. RC's cross-repo guards held C:\\LegionWallpaper. LW's
    2026-09-06 rename to "C:\\Legion Wallpaper" turned both of them from
    checking into SKIPPING, and RC's suite stayed green for about three hours
    with nothing being compared. The bytes happened to agree, so nothing broke -
    which is the uncomfortable part, not the reassuring one. A skip-when-absent
    guard that loses its target does not go red, it goes QUIET.

    The lesson is narrower than "stop hardcoding a sibling path": a sibling
    that exists under another spelling is a BUG and must be loud, while one
    that is genuinely missing is a runner without the tree and deserves its
    skip. Those two were indistinguishable, and now they are not. Whoever does
    the renaming is the only party positioned to notice, so a rename commit
    should sweep the SIBLING's constants too.

    Reported by RC 2026-09-06 (Amberstone e752e4edc), which fixed its own side.
    """
    configured = pathlib.Path(configured)
    if configured.is_dir():
        return configured, "present"
    parent, want = configured.parent, _name_key(configured.name)
    if not want or not parent.is_dir():
        return None, "absent"
    for entry in sorted(parent.iterdir()):
        if entry.is_dir() and _name_key(entry.name) == want:
            return entry, "renamed"
    return None, "absent"


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

    sibling, status = resolve_sibling_root(SIBLING_REPO)
    if status == "renamed":
        problems.append(
            f"sibling repo moved: {SIBLING_REPO} is now {sibling}. Until the "
            f"constant is updated this check compares NOTHING and goes quiet "
            f"rather than red - see resolve_sibling_root."
        )
        return
    if status == "absent":
        notes.append(f"sibling repo {SIBLING_REPO} not on this machine")
        return

    for rel in SHARED_LOOP_FILES:
        mine, theirs = ROOT / rel, sibling / rel
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
    check_tracked_but_ignored()
    check_model_pins()
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
