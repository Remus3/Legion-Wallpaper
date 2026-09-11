"""Is a git BINARY resolvable on this machine? One question, asked once per file.

WHY THIS EXISTS. On 2026-09-10 LW ran RC's reproduction on its own tree: with
git stripped off PATH, 43 arms went RED for a tool that was simply not
installed. Not one was a defect in the thing under test. RSC found the same root
cause 13 times in 4 test files, and LW had already hit it in production code
(`tools/lw_model_pins.py`, where ABSENT must never read as verified).

THREE DISPOSITIONS, NOT TWO:

    git ran and the guard found nothing      skip, with a reason that is TRUE
    git ran and the guard found a breach     FAIL
    git is not installed at all              skip, with a reason that is TRUE

Conflating the third with the second is how a CORRECT guard installs a FALSE
RED, and a red suite a reader cannot act on trains them to ignore red.

WHAT THIS IS NOT. It is not a sweep, not a matcher and not a shared repair.
It answers ONE factual question - can this machine resolve a git executable -
and every call site still decides for itself what that answer means there. Some
sites skip a whole module (every arm in it drives a real repository); some skip
one arm; `tools/` production code does not use this at all. Widening one matcher
to cover 43 sites is the move RSC's charter names as the wrong response after
the second defeat, and it would relocate the conflation rather than close it.

WHAT IT DELIBERATELY DOES NOT COVER. A git that IS installed and then fails is
still a FAIL, and must stay one. This only knows about absence. If a call site
needs "no repository here", that is a different question with a different answer
and belongs at that site.

The mirror direction is graded behaviourally, not by reading conditions:
`tests/test_git_absence_is_a_skip.py` runs a representative node per repaired
file twice - once with git stripped, once with git present - and asserts SKIP
then RUN. A marker that always skips satisfies the first half perfectly.
"""
from __future__ import annotations

import shutil

import pytest

GIT = shutil.which("git")

REASON = (
    "git is not installed on this machine, so this arm COULD NOT CHECK rather "
    "than having checked and found nothing - a missing tool is a true skip, "
    "never a failure of the thing under test"
)

# Module- or function-level marker. `pytestmark = gitdep.requires_git` when every
# arm in the file drives a real repository; on the single arm otherwise.
requires_git = pytest.mark.skipif(GIT is None, reason=REASON)


def skip_if_git_missing() -> None:
    """Imperative form, for a fixture or a mid-test branch.

    A fixture is where the two big files needed it: they shell out during SETUP,
    so a missing git produced an ERROR rather than a FAILED, and collection
    succeeded either way.
    """
    if GIT is None:
        pytest.skip(REASON)
