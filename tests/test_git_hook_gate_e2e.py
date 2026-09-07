"""End-to-end proof that LW's tracked git hooks actually REFUSE a bad commit.

PORTED from Riot Commander's tests/test_git_hook_gate_e2e.py (delivered verbatim
to moon_sync_inbox/from-RC-verbatim/ on 2026-09-07). RC's paraphrases of this
probe in the note channel are superseded by the real file; this is that file
adapted to LW's two hooks and tool paths, not a fifth rewrite of the idea.

WHY THIS EXISTS
---------------
RC measured 2026-07-26 that all five of its tracked hooks were committed mode
100644. Git refuses to execute a non-executable hook and says NOTHING about it,
so on every Linux clone - CI included - the entire gate was absent while every
check reported green. Lanternlight's two tracked hooks were measured the same
way on 2026-09-06. CLAUDE.md draws the conclusion this file implements: never
treat a hook's PRESENCE as proof it fires; the only valid test is end-to-end -
stage a banned glyph, attempt a REAL commit, assert HEAD unchanged.

Every cheaper assertion available was true at some point while the gate was
still not firing: the hook file exists, core.hooksPath is set, the index mode
is 100755, the hook runs on every commit (LW's own 2026-07-03 to 2026-07-26
window, where pre-commit invoked precommit_gate.py with NO args and the gate
self-gated to a silent no-op).

THE POSITIVE CONTROL IS NOT OPTIONAL
------------------------------------
A refusal test alone is worthless: a commit that fails because the fixture
forgot to copy a script the hook invokes looks exactly like a commit that failed
because the gate worked. Without the positive control, a gate that refuses
EVERYTHING passes both refusal tests, and that catastrophically broken version
is the one that looks safest. So the clean-ASCII case must be asserted to
COMMIT, and it additionally asserts a side effect only the commit-msg hook can
produce (the Claude co-author trailer is stripped), so an unwired fixture cannot
pass by silently doing nothing at all.

The two negatives are separate on purpose: staged CONTENT goes through
pre-commit and the MESSAGE goes through commit-msg, so one passing says nothing
about the other. The message half was a real measured miss: git's order is
pre-commit -> prepare the message -> commit-msg, so .git/COMMIT_EDITMSG does not
exist yet when pre-commit runs.

WHY A TEMPORARY REPO
--------------------
The commits under test are real, and this repo is not a place to make throwaway
commits - least of all commits that must be REFUSED. The fixture is a standalone
`git init` in a temp dir with the REAL hook bodies and the REAL scripts they
invoke copied in.

LW_REQUIRE_HOOK_GATE=1 turns "this clone never armed the gate" from a SKIP into
a FAILURE. A skipped test is a green tick, which is how RC's five hooks sat at
mode 100644 for weeks while CI stayed green. CI sets it (see
.github/workflows/ci.yml and tests/test_ci_gate_arming.py).

Banned glyphs are built with chr() so this file stays 7-bit ASCII and does not
trip the very gate it tests.
"""
from __future__ import annotations

import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

REPO = pathlib.Path(__file__).resolve().parent.parent
HOOKS = REPO / ".githooks"
INSTALLER = REPO / "tools" / "install_git_hooks.py"

# Written with chr(), never as a literal: this file is itself scanned by the
# repo's ASCII hygiene guards and by the gate under test.
EM_DASH = chr(0x2014)

_HAVE_GIT = shutil.which("git") is not None

# Set by CI. Turns every environment-conditional skip below into a failure, so
# an unconfigured or git-less runner cannot report green by skipping.
_REQUIRE = os.environ.get("LW_REQUIRE_HOOK_GATE") == "1"

# LW tracks exactly two hooks. Both are commit-time and both are installed in
# the fixture; there is no post-commit / post-checkout / pre-push to exclude.
_FIXTURE_HOOKS = ("pre-commit", "commit-msg")

# Scripts the two hooks invoke via "$ROOT/...". Copied to the same relative path
# so each script's own parent.parent ROOT resolves to the fixture, not to LW.
_SUPPORT_SCRIPTS = (
    "tools/precommit_gate.py",
    "tools/precommit_msg_check.py",
)

# Tools a hook may reference that the fixture does NOT copy. Both are absent
# from LW today and both are invoked inside an `if [ -f ... ]` guard, so they
# no-op in a fixture that lacks them. Any OTHER tool appearing in a hook body
# means the hook grew a dependency this fixture does not satisfy - fail loudly
# rather than let the positive control turn red for an unexplained reason.
_KNOWN_GUARDED_TOOLS = ("gen_archmap.py", "gen_state_schema.py")

_ROOT_TOOL_REF = re.compile(r"\$ROOT/(tools/[A-Za-z0-9_]+\.py)")


def _skip_or_fail(case: unittest.TestCase, why: str) -> None:
    """Skip, unless CI has armed LW_REQUIRE_HOOK_GATE - then this is a failure."""
    if _REQUIRE:
        case.fail(f"LW_REQUIRE_HOOK_GATE=1 and {why}")
    case.skipTest(why)


def _assert_hook_bodies_still_carry_the_gate() -> None:
    """Read the gate out of the REAL hooks rather than trusting a retyped copy.

    If someone deletes the gate invocation upstream, this fails loudly instead
    of the fixture silently testing a hand-written stand-in that still works.
    """
    pre = (HOOKS / "pre-commit").read_text(encoding="utf-8")
    msg = (HOOKS / "commit-msg").read_text(encoding="utf-8")
    if "precommit_gate.py" not in pre or "--git-hook" not in pre:
        raise AssertionError(
            ".githooks/pre-commit no longer invokes precommit_gate.py --git-hook "
            "- with no args the gate self-gates to a SILENT no-op (measured "
            "2026-07-03 to 2026-07-26)")
    if "precommit_gate.py" not in msg or "--message-file" not in msg:
        raise AssertionError(
            ".githooks/commit-msg no longer invokes precommit_gate.py "
            "--message-file - the commit MESSAGE half of the gate is gone")
    if "precommit_msg_check.py" not in msg:
        raise AssertionError(
            ".githooks/commit-msg no longer invokes precommit_msg_check.py")
    referenced = set()
    for body in (pre, msg):
        referenced |= {m.group(1) for m in _ROOT_TOOL_REF.finditer(body)}
    unexpected = sorted(
        r for r in referenced
        if r not in _SUPPORT_SCRIPTS
        and pathlib.PurePosixPath(r).name not in _KNOWN_GUARDED_TOOLS
    )
    if unexpected:
        raise AssertionError(
            f"hook(s) now invoke {unexpected}, which this fixture neither copies "
            "nor knows to be guarded by an `if [ -f ]` test. Add it to "
            "_SUPPORT_SCRIPTS (if the fixture must run it) or to "
            "_KNOWN_GUARDED_TOOLS (if it no-ops when absent)")


class TrackedHookModeTests(unittest.TestCase):
    """The exact regression that made every RC hook inert on Linux.

    File modes ARE carried by a clone, unlike core.hooksPath, so this is a
    property of the repository itself. Asserted by name: a 100644 hook produces
    no error message anywhere, so the only way it ever surfaces is an assertion
    that says the word.
    """

    def test_every_tracked_hook_is_executable_in_the_index(self) -> None:
        if not _HAVE_GIT:
            _skip_or_fail(self, "git is not on PATH")
        out = subprocess.run(
            ["git", "-C", str(REPO), "ls-files", "-s", ".githooks/"],
            capture_output=True, text=True, errors="replace",
        )
        self.assertEqual(out.returncode, 0, out.stderr)
        rows = [ln for ln in out.stdout.splitlines() if ln.strip()]
        self.assertGreaterEqual(
            len(rows), len(_FIXTURE_HOOKS),
            f"expected at least {len(_FIXTURE_HOOKS)} tracked hooks, saw {rows}")
        bad = [ln for ln in rows if not ln.startswith("100755 ")]
        self.assertEqual(
            bad, [],
            "git silently refuses to run a non-executable hook: " + str(bad))


class LiveRepoGateArmedTests(unittest.TestCase):
    """core.hooksPath is LOCAL config and is never cloned.

    So this assertion is about THIS working copy, not about the repository, and
    it is the one that must not quietly skip on a CI runner.
    """

    def test_this_clone_has_the_gate_armed(self) -> None:
        if not _HAVE_GIT:
            _skip_or_fail(self, "git is not on PATH")
        proc = subprocess.run(
            [sys.executable, str(INSTALLER), "--check"],
            capture_output=True, text=True, errors="replace", cwd=str(REPO),
        )
        if proc.returncode != 0:
            _skip_or_fail(
                self,
                "this clone has not run `python tools/install_git_hooks.py`, so "
                "the tracked .githooks gate is INERT here:\n"
                f"{proc.stdout}\n{proc.stderr}")


class HookGateEndToEndTests(unittest.TestCase):
    """Real commits into a throwaway repo wired exactly like this one."""

    def setUp(self) -> None:
        if not _HAVE_GIT:
            _skip_or_fail(self, "git is not on PATH")
        _assert_hook_bodies_still_carry_the_gate()
        self.root = pathlib.Path(tempfile.mkdtemp(prefix="lw_hook_gate_"))
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        self._build_fixture()

    # ---- fixture -------------------------------------------------------

    def _git(self, *args: str, check: bool = True) -> subprocess.CompletedProcess:
        proc = subprocess.run(
            ["git", "-C", str(self.root), *args],
            capture_output=True, text=True, errors="replace", env=self._env,
        )
        if check and proc.returncode != 0:
            self.fail(f"git {' '.join(args)} failed:\n{proc.stdout}\n{proc.stderr}")
        return proc

    def _build_fixture(self) -> None:
        # Isolate from the operator's global/system git config. An inherited
        # core.hooksPath, autocrlf or LFS filter makes the fixture measure the
        # WRONG REPO and it still looks green.
        self._env = dict(os.environ)
        self._env["GIT_CONFIG_GLOBAL"] = str(self.root / "no-global-gitconfig")
        self._env["GIT_CONFIG_SYSTEM"] = str(self.root / "no-system-gitconfig")
        # Both hooks resolve ${PYTHON:-<pinned Legion path>} and fall back to
        # `python` on PATH. Pin it to the interpreter running the test so the
        # probe depends on the GATE and not on which python a runner happens to
        # have - the pinned Legion path does not exist on the Linux runner.
        self._env["PYTHON"] = sys.executable.replace("\\", "/")

        subprocess.run(
            ["git", "init", "-q", str(self.root)],
            capture_output=True, text=True, env=self._env,
        )
        self._git("config", "user.name", "hook gate test")
        self._git("config", "user.email", "hookgate@example.invalid")
        # An unsigned-commit prompt hangs CI.
        self._git("config", "commit.gpgsign", "false")

        hooks = self.root / ".githooks"
        hooks.mkdir()
        for name in _FIXTURE_HOOKS:
            # The REAL hook body, byte for byte. A stub would test the fixture.
            dst = hooks / name
            dst.write_text((HOOKS / name).read_text(encoding="utf-8"),
                           encoding="utf-8", newline="\n")
            dst.chmod(0o755)

        for rel in _SUPPORT_SCRIPTS:
            dst = self.root / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(REPO / rel, dst)

        # Same wiring tools/install_git_hooks.py performs: a RELATIVE
        # core.hooksPath, so the pointer survives being cloned elsewhere.
        self._git("config", "core.hooksPath", ".githooks")

        # Track the hooks with the EXECUTABLE index mode, mirroring the live
        # repo so this fixture stays meaningful on the Linux runner that
        # actually matters - where 100644 is the difference between a gate and
        # nothing, and git reports NOTHING when it declines to run one.
        self._git("add", "-A")
        for name in _FIXTURE_HOOKS:
            self._git("update-index", "--chmod=+x", f".githooks/{name}")
        # Baseline with --no-verify: the fixture's own scaffolding is not what
        # is under test.
        self._git("commit", "--no-verify", "-q", "-m", "chore: fixture baseline")

    def _head(self) -> str:
        return self._git("rev-parse", "HEAD").stdout.strip()

    def _commit(self, message: str) -> subprocess.CompletedProcess:
        """Commit via -F, never -m.

        A non-ASCII MESSAGE passed through argv can be mangled by the shell or
        by console encoding before the hook ever sees it, so -m tests the
        harness rather than the gate.
        """
        msg = self.root / ".commit-message"
        msg.write_text(message + "\n", encoding="utf-8", newline="\n")
        return self._git("commit", "-F", str(msg), check=False)

    # ---- the three assertions -----------------------------------------

    def test_clean_ascii_change_commits(self) -> None:
        """POSITIVE CONTROL. Without this, a refusal proves nothing.

        A hook that dies because the fixture forgot to copy a script it invokes
        refuses every commit and looks identical to a working gate. The trailer
        assertion is the second half: stripping it is a side effect ONLY
        precommit_gate.py --message-file produces, and that runs ONLY from
        commit-msg, so an unwired fixture cannot pass by doing nothing.
        """
        (self.root / "sample_module.py").write_text(
            'print("all ascii here")\n', encoding="utf-8", newline="\n")
        self._git("add", "sample_module.py")
        before = self._head()

        proc = self._commit(
            "test: add an all-ascii fixture module\n\n"
            "Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>")

        self.assertEqual(
            proc.returncode, 0,
            f"clean ASCII commit was refused:\n{proc.stdout}\n{proc.stderr}")
        self.assertNotEqual(self._head(), before, "HEAD did not advance")
        body = self._git("log", "-1", "--format=%B").stdout
        self.assertIn("test: add an all-ascii fixture module", body)
        self.assertNotIn(
            "Co-Authored-By", body,
            "the commit-msg hook did not run: it must STRIP the Claude "
            "co-author trailer (operator policy 2026-06-03), so its absence "
            "here is the proof the hook fired on the passing path too")

    def test_em_dash_in_staged_content_is_refused(self) -> None:
        """The banned-glyph-in-FILE-CONTENT half of the gate (pre-commit)."""
        (self.root / "notes.txt").write_text(
            f"a clause{EM_DASH}and its continuation\n",
            encoding="utf-8", newline="\n")
        self._git("add", "notes.txt")
        before = self._head()

        proc = self._commit("test: stage a banned glyph")

        self.assertNotEqual(
            proc.returncode, 0,
            f"an em-dash in staged content COMMITTED:\n{proc.stdout}\n{proc.stderr}")
        self.assertEqual(self._head(), before, "HEAD advanced on a refused commit")

    def test_em_dash_in_commit_message_is_refused(self) -> None:
        """The half that CANNOT live in pre-commit, and was a real measured miss.

        Git's order is pre-commit -> prepare the message -> commit-msg, so
        .git/COMMIT_EDITMSG does not exist yet when pre-commit runs. While the
        gate was invoked only from pre-commit the content and ruff halves still
        fired - so it LOOKED healthy - while a banned glyph in a commit SUBJECT
        landed clean (measured 2026-07-26).
        """
        (self.root / "clean.txt").write_text(
            "nothing wrong with this file\n", encoding="utf-8", newline="\n")
        self._git("add", "clean.txt")
        before = self._head()

        proc = self._commit(f"test: subject with a banned{EM_DASH}glyph in it")

        self.assertNotEqual(
            proc.returncode, 0,
            f"an em-dash in the commit MESSAGE committed:\n{proc.stdout}\n{proc.stderr}")
        self.assertEqual(self._head(), before, "HEAD advanced on a refused commit")


if __name__ == "__main__":
    unittest.main()
