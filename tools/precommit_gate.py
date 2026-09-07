#!/usr/bin/env python3
"""PreToolUse gate on `git commit`: block NET-NEW ruff errors + banned glyphs.

Wired in .claude/settings.json under PreToolUse matcher Bash(git commit:*).
Reads the Claude Code hook payload on stdin (tool_name / tool_input.command).

Self-gates: if the command is not a `git commit`, exits 0 before touching git
(so it is a no-op on every other Bash call - zero overhead off the commit path).

On a commit it inspects ONLY staged content of staged files (diff-filter ACM):
  1. ruff check (no --fix) on staged .py, keeping findings whose row lands in an
     ADDED line range of that file (net-new only - pre-existing repo debt in an
     untouched region never blocks, so an unattended headless run cannot wedge
     on unrelated errors).
  2. banned-glyph byte scan (U+2014/2013/201C/201D/2018/2019) on ADDED (+) lines
     only, plus the commit-message text in the command string itself.

Exit 2 (block) with a terse stderr report on any violation; exit 0 otherwise.
Mirrors tools/edit_lint_check.py's banned set + frozen-skip; that hook is
edit-time + advisory, this one is commit-time + blocking on net-new only.

Also owns the HAND-OFF rule set (scan_handoff_text): ASCII, banned glyphs,
32-hex literals, user-profile paths, secret-shaped literals. That one function
is called from BOTH enforcement points - tools/lw_next_session.write_handoff
before anything reaches disk, and _staged_violations over the staged blob - so
the rule has a single reading. `--scan-files FILE...` runs it from a shell.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys

# Hooks run under windowless pythonw.exe; a console-subsystem child (git /
# `py` launcher + ruff) would otherwise get a fresh console allocated - an
# on-screen + taskbar flash. CREATE_NO_WINDOW suppresses it (Windows-only;
# 0 elsewhere).
_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)

# Anchor for the Legion Wallpaper repo - final fallback when the root cannot
# be resolved from the command or the hook's CWD.
_LW_ROOT = r"C:\Legion Wallpaper"

_BANNED = {
    chr(0x2014): "em-dash",
    chr(0x2013): "en-dash",
    chr(0x201C): "smart-dquote-open",
    chr(0x201D): "smart-dquote-close",
    chr(0x2018): "smart-quote-open",
    chr(0x2019): "smart-quote-close",
    # U+2026 joined the set 2026-09-06: the CI hygiene guard had banned it
    # since bring-up while this gate did not, so an ellipsis committed clean
    # and reddened CI on the same commit. Converged on the stricter reading -
    # CLAUDE.md says stay 7-bit ASCII. Pinned by
    # tests/test_glyph_rule_has_one_reading.py.
    chr(0x2026): "ellipsis",
    chr(0x00A0): "non-breaking-space",
}
_FROZEN_SKIP = ("logs/", "docs/_archive/", ".pyc", ".git/", "__pycache__/")
_HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")

# Operator policy 2026-06-03: never emit the Claude co-author trailer.
# Matches any casing of the trailer key, and only when the value names Claude or
# anthropic.com - a human co-author trailer is legitimate and must survive.
_CLAUDE_TRAILER = re.compile(r"^\s*co-authored-by:.*(claude|anthropic)", re.IGNORECASE)

# ---------------------------------------------------------------------------
# The HAND-OFF content rule set - ONE reading, TWO enforcement points.
#
# `LW-NEXT-SESSION.txt` is tracked in a PUBLIC repo and is the
# highest-variance artifact in the tree: written fresh every session, never
# reviewed before it is written, quoting freely from whatever that session
# touched. A Desktop file that is wrong costs one edit; a tracked one costs a
# history rewrite (Clockspeed's finding, 2026-09-06), and LW rewrote its whole
# history twice that week.
#
# So the same function gates the WRITE (tools/lw_next_session.write_handoff,
# before anything reaches disk) and the COMMIT (_staged_violations below, over
# the whole staged blob). Deliberately one function object rather than two
# agreeing copies: this repo already carries three separate declarations of the
# banned-glyph rule, and they agree only by inspection.
#
# NOT solved with a per-session exemption list. An exemption list that grows
# once per session is a gate disarmed one word at a time.
# ---------------------------------------------------------------------------

# The hand-off filename contract mirrors tools/lw_next_session.py: a bare
# filename in the REPO ROOT starting with `LW-`. Pinned by
# tests/test_handoff_write_gate.py so a rename cannot unhook the commit half.
HANDOFF_BASENAME = "LW-NEXT-SESSION.txt"
_HANDOFF_NAME = re.compile(r"LW-[A-Za-z0-9._-]*\.txt")

# 32+ hex is the floor deliberately: a git short sha (7-12) and a `sha12=`
# pipeline-log field must survive, a sha256/sha1 digest or a hex token must not.
_HEX32 = re.compile(r"(?<![0-9A-Za-z])[0-9a-fA-F]{32,}(?![0-9A-Za-z])")

# Path SHAPES only. An account name on its own is not matched: hard-coding the
# operator's username into a public repo to detect it would be the disclosure
# this gate exists to prevent.
_USER_PROFILE = re.compile(
    r"[A-Za-z]:[\\/]{1,2}Users[\\/]{1,2}[A-Za-z0-9._~-]+"
    r"|/(?:home|Users)/[A-Za-z0-9._~-]+"
    r"|%USERPROFILE%|\$env:USERPROFILE|~/\.[A-Za-z0-9._-]+",
    re.IGNORECASE,
)

_SECRET = re.compile(
    r"sk-[A-Za-z0-9_-]{16,}"
    r"|gh[pousr]_[A-Za-z0-9]{20,}"
    r"|github_pat_[A-Za-z0-9_]{20,}"
    r"|AIza[A-Za-z0-9_-]{20,}"
    r"|AKIA[A-Z0-9]{12,}"
    r"|xox[abposr]-[A-Za-z0-9-]{10,}"
    r"|-----BEGIN [A-Z ]*PRIVATE KEY-----"
    r"|(?:api[_-]?key|secret|token|password|passwd|passphrase)\s*[:=]\s*\S{8,}"
    r"|bearer\s+[A-Za-z0-9._~+/-]{16,}",
    re.IGNORECASE,
)


def is_handoff_path(path: str) -> bool:
    """True for a repo-ROOT hand-off file, matching lw_next_session's contract."""
    p = path.replace("\\", "/")
    return "/" not in p and bool(_HANDOFF_NAME.fullmatch(p))


def _mask_user(text: str) -> str:
    """Show the path SHAPE without repeating the account name."""
    head, sep, _tail = text.replace("\\", "/").rpartition("/")
    return f"{head}{sep}<user>" if sep else "<user-profile>"


def scan_handoff_text(text: str, label: str = "hand-off") -> list[str]:
    """Every hand-off content rule, in one place. Returns [] when clean.

    Rules: 7-bit ASCII, the banned glyph set, 32+ hex literals, user-profile
    paths, and secret-shaped literals. Findings carry the line number and the
    rule but never the matched value for the secret class - the report goes to
    stderr and into logs, so echoing it there would just move the disclosure.
    """
    out: list[str] = []
    for i, line in enumerate(text.splitlines(), 1):
        hits = _glyph_hits(line)
        if hits:
            out.append(f"  {label}:{i}  banned glyph: {', '.join(hits)}")
        try:
            line.encode("ascii")
        except UnicodeEncodeError as exc:
            out.append(f"  {label}:{i}  non-ASCII at column {exc.start + 1}")
        m = _HEX32.search(line)
        if m:
            out.append(
                f"  {label}:{i}  32-hex literal ({len(m.group(0))} chars, "
                f"starts {m.group(0)[:6]}...)"
            )
        m = _USER_PROFILE.search(line)
        if m:
            out.append(f"  {label}:{i}  user-profile path: {_mask_user(m.group(0))}")
        if _SECRET.search(line):
            out.append(f"  {label}:{i}  secret-shaped literal (value withheld)")
    return out


def _is_commit(command: str) -> bool:
    s = command.strip()
    # tolerate leading env assignments, `&&`/`;` chains, PowerShell `{` blocks,
    # and global flags with quoted args (git -C "C:\path" commit).
    return bool(re.search(
        r"(^|[;&|{(]\s*)git\s+(?:(?:-\S+|\"[^\"]*\"|'[^']*')\s+)*commit\b", s
    ))


def _skippable(path: str) -> bool:
    p = path.replace("\\", "/")
    return any(s in p for s in _FROZEN_SKIP)


def _git(args: list[str], root: str | None) -> str:
    try:
        out = subprocess.run(
            ["git", *args], cwd=root or None, capture_output=True, text=True,
            timeout=20, creationflags=_NO_WINDOW,
        )
        return out.stdout
    except (OSError, subprocess.SubprocessError):
        return ""


_DASH_C = re.compile(r"git\s+-C\s+(\"([^\"]+)\"|'([^']+)'|(\S+))")


def _root_from_command(command: str) -> str | None:
    """Repo dir from `git -C <path> ... commit`, preferring the segment that
    carries the commit (worktree agents commit via -C into their own tree -
    resolving the hook's CWD would gate the WRONG repo's staged diff)."""
    root = None
    for m in _DASH_C.finditer(command):
        path = m.group(2) or m.group(3) or m.group(4)
        tail = command[m.end():]
        if re.match(r"\s+(?:(?:-\S+|\"[^\"]*\"|'[^']*')\s+)*commit\b", tail):
            return path
        root = root or path
    return root


def _staged_added(root: str) -> dict[str, dict]:
    """Return {path: {"ranges": [(start,end)...], "lines": [(lineno,text)...]}}."""
    diff = _git(["diff", "--cached", "--unified=0", "--no-color"], root)
    files: dict[str, dict] = {}
    cur: str | None = None
    lineno = 0
    for ln in diff.splitlines():
        if ln.startswith("+++ "):
            p = ln[4:].strip()
            cur = None if p == "/dev/null" else p[2:] if p.startswith("b/") else p
            if cur and not _skippable(cur):
                files.setdefault(cur, {"ranges": [], "lines": []})
            else:
                cur = None
            continue
        if ln.startswith("@@"):
            m = _HUNK.match(ln)
            if m and cur:
                start = int(m.group(1))
                count = int(m.group(2)) if m.group(2) else 1
                lineno = start
                if count:
                    files[cur]["ranges"].append((start, start + count - 1))
            continue
        if cur and ln.startswith("+") and not ln.startswith("+++"):
            files[cur]["lines"].append((lineno, ln[1:]))
            lineno += 1
    return files


def _glyph_hits(text: str) -> list[str]:
    return sorted({name for ch, name in _BANNED.items() if ch in text})


def _compile_errors(pyfiles: list[str], root: str) -> list[str]:
    """py_compile each staged .py; a syntax error crashes silently under
    pythonw.exe at runtime (CLAUDE.md hard rule), so block it at commit."""
    import py_compile

    out: list[str] = []
    for rel in pyfiles:
        path = os.path.join(root, rel)
        try:
            py_compile.compile(path, doraise=True)
        except py_compile.PyCompileError as exc:
            out.append(f"  {rel}  py_compile: {exc.msg.splitlines()[0][:160]}")
        except OSError:
            pass
    return out


def _staged_violations(root: str) -> list[str]:
    """Every check that reads STAGED CONTENT (shared by both entry points)."""
    staged = _staged_added(root)
    violations: list[str] = []

    # 1. banned glyphs on added lines
    for path, info in staged.items():
        for lineno, text in info["lines"]:
            hits = _glyph_hits(text)
            if hits:
                violations.append(f"  {path}:{lineno}  banned glyph: {', '.join(hits)}")

    # 1b. the hand-off artifact, WHOLE staged blob through the shared engine.
    # Added lines are not enough here: the hand-off is rewritten wholesale, and
    # a secret that survives from a previous session in an untouched line is
    # exactly as public. This is the commit-time half of the WRITE-time gate in
    # tools/lw_next_session.write_handoff - one function, two enforcement
    # points, so the rule has one reading.
    for path in staged:
        if is_handoff_path(path):
            blob = _git(["show", f":{path}"], root)
            violations.extend(scan_handoff_text(blob, label=path))

    # 2. net-new ruff errors + py_compile on staged .py
    pyfiles = [
        p for p in staged if p.endswith(".py") and os.path.isfile(os.path.join(root, p))
    ]
    violations.extend(_compile_errors(pyfiles, root))
    if pyfiles:
        # Use the `py` launcher (not sys.executable): under the hook the running
        # interpreter is a bare pythoncore build with no ruff installed; the
        # launcher resolves the project Python that has ruff (mirrors edit_lint_check.py).
        # Bare-repo guard: if the launcher / ruff is unavailable in this young
        # repo, skip the ruff pass instead of crashing the hook (the glyph and
        # py_compile gates above still apply).
        findings: list = []
        try:
            proc = subprocess.run(
                ["py", "-m", "ruff", "check", "--output-format=json", *pyfiles],
                cwd=root,
                capture_output=True,
                text=True,
                timeout=60,
                creationflags=_NO_WINDOW,
            )
            findings = json.loads(proc.stdout) if proc.stdout.strip() else []
        except (OSError, subprocess.SubprocessError, ValueError):
            findings = []
        for f in findings:
            fn = (f.get("filename") or "").replace("\\", "/")
            rel = fn[len(root.replace("\\", "/")) + 1 :] if fn.startswith(root.replace("\\", "/")) else fn
            row = ((f.get("location") or {}).get("row")) or 0
            ranges = staged.get(rel, staged.get(fn, {})).get("ranges", [])
            if any(a <= row <= b for a, b in ranges):
                violations.append(
                    f"  {rel}:{row}  ruff {f.get('code', '?')}: {f.get('message', '')}"
                )
    return violations


def _report(violations: list[str], what: str) -> int:
    sys.stderr.write(
        f"precommit_gate BLOCKED commit - {what}:\n"
        + "\n".join(violations)
        + "\n\nFix the staged lines (ruff check --fix / strip the glyph) and re-commit.\n"
    )
    return 2


def _git_hook_mode() -> int:
    """Entry point for .git/hooks/pre-commit - see tools/install_git_hooks.py.

    THIS is the authoritative gate. The PreToolUse copy below is only the fast
    in-session signal: RC measured 2026-07-26 that a nested
    `claude -p --permission-mode bypassPermissions` commits without PreToolUse
    hooks firing at all, while git hooks ran normally. A git hook is the only
    placement that survives every channel (AHK, SDK, a human, CI).
    """
    root = _git(["rev-parse", "--show-toplevel"], os.getcwd()).strip() or os.getcwd()
    violations = _staged_violations(root)
    if violations:
        return _report(violations, "net-new violations in staged files")
    return 0


def _message_mode(path: str) -> int:
    """Entry point for .git/hooks/commit-msg.

    Separate from pre-commit on purpose, and this is not a style choice: at
    pre-commit time .git/COMMIT_EDITMSG does not exist yet (verified), so a
    single pre-commit hook would silently LOSE the commit-message glyph check
    the PreToolUse gate performs on the `-m` text.
    """
    try:
        text = open(path, encoding="utf-8", errors="replace").read()
    except OSError:
        return 0  # nothing readable to gate - never wedge a commit on this

    # Operator policy 2026-06-03: never emit the Claude co-author trailer.
    # STRIP rather than block: the trailer is appended by the tool, not typed by
    # the operator, so blocking would wedge an unattended run over a line the
    # human never wrote. Only the Claude/Anthropic trailer is policy - a real
    # human co-author is legitimate and stays.
    kept = [ln for ln in text.splitlines() if not _CLAUDE_TRAILER.match(ln)]
    if len(kept) != len(text.splitlines()):
        # Collapse the blank run the removed trailer leaves behind.
        while len(kept) > 1 and not kept[-1].strip():
            kept.pop()
        new = "\n".join(kept) + "\n"
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(new)
        os.replace(tmp, path)
        sys.stderr.write("precommit_gate: stripped the Claude co-author trailer "
                         "(operator policy 2026-06-03)\n")
        text = new

    # git strips '#' lines before the message is stored, so a glyph there never
    # ships; scanning them would block on git's own template comments.
    body = "\n".join(ln for ln in text.splitlines() if not ln.lstrip().startswith("#"))
    hits = _glyph_hits(body)
    if hits:
        return _report([f"  commit message  banned glyph: {', '.join(hits)}"],
                       "banned glyph in the commit message")
    return 0


def _scan_files_mode(paths: list[str]) -> int:
    """Entry point for `--scan-files FILE...`: run the hand-off rule set over
    files on disk. Converges with RC's CLI of the same name so one command
    means the same thing across the sibling repos, and lets CI sweep the
    tracked hand-off through the SAME engine the hook and the writer use.

    Exit 2 on any violation, 0 when clean. An unreadable path is a violation,
    not a silent pass - a gate that cannot read its target has not checked it.
    """
    violations: list[str] = []
    for path in paths:
        try:
            text = open(path, encoding="utf-8", errors="strict").read()
        except UnicodeDecodeError:
            violations.append(f"  {path}  not decodable as UTF-8")
            continue
        except OSError as exc:
            violations.append(f"  {path}  unreadable ({exc.__class__.__name__})")
            continue
        violations.extend(scan_handoff_text(text, label=path))
    if violations:
        sys.stderr.write(
            "precommit_gate --scan-files REFUSED - hand-off rule violations:\n"
            + "\n".join(violations)
            + "\n"
        )
        return 2
    sys.stdout.write(f"scan-files: {len(paths)} file(s) clean\n")
    return 0


def main() -> int:
    argv = sys.argv[1:]
    if "--git-hook" in argv:
        return _git_hook_mode()
    if "--scan-files" in argv:
        return _scan_files_mode(argv[argv.index("--scan-files") + 1:])
    if "--message-file" in argv:
        i = argv.index("--message-file")
        return _message_mode(argv[i + 1]) if i + 1 < len(argv) else 0

    raw = sys.stdin.read() if not sys.stdin.isatty() else ""
    # PowerShell 5.1 pipes prepend a UTF-8 BOM; json.loads rejects it and the
    # raw-string fallback then never regex-matches -> silent pass. Strip it.
    raw = raw.lstrip("\ufeff").strip()
    command = ""
    try:
        command = (json.loads(raw).get("tool_input") or {}).get("command", "")
    except (ValueError, AttributeError):
        command = raw
    if not _is_commit(command):
        return 0

    root = (
        _root_from_command(command)
        or _git(["rev-parse", "--show-toplevel"], os.getcwd()).strip()
        or _LW_ROOT
    )
    violations = _staged_violations(root)

    # The -m text lives in the command string here. (In the git-hook placement
    # this check belongs to commit-msg instead - see _message_mode.)
    msg_hits = _glyph_hits(command)
    if msg_hits:
        violations.append(f"  commit message  banned glyph: {', '.join(msg_hits)}")

    if violations:
        return _report(violations, "net-new violations in staged files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
