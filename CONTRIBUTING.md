# Contributing

Read this before opening anything. It is short and it is honest about what this
repository is.

## What this repo is

A personal project, built in the open, shaped entirely around one machine, one
corpus and one operator. It is published as a **reference to read and borrow
from**, not as a product to install or a codebase seeking maintainers. The
roadmap is driven by `ROADMAP.md` alone.

You cannot run the pipeline end to end without the corpus, and the corpus is not
here and never will be: the images are third-party illustrations, `images/**` is
gitignored, and the restored output stays private (`README.md`, and
`docs/RESTORATION_PLAN.md` section 10).

## What is welcome

- **A factual error.** A doc that contradicts the code, a stale command, a
  cited path or SHA that does not resolve, a broken link. Cite `file:line`.
- **A defect in the published machinery** with a reproduction: the gate ladder,
  the pipeline state machine, the git hooks, the drift guard, the loop
  executor. Say what you ran and what you saw.
- **A security or privacy problem.** Do not open a public issue for these -
  `SECURITY.md` has the channel.

## What is not

- **Feature requests and roadmap suggestions.** The roadmap is set by the
  operator's own use, and an unbacked "you should add X" will be closed.
- **Pull requests, by default.** They are not being solicited. An unsolicited PR
  will most likely be closed unread, and one that arrives without the checks
  below will certainly be. If you have a fix worth landing, open an issue first
  and say so; the maintainer will tell you whether a PR is wanted.
- **Anything involving the image corpus** - copies, links, scrapes, requests.

## If a PR is invited, it has to clear the same gates the maintainer does

These are enforced by hooks and by CI, not by review goodwill. See `CLAUDE.md`
for the full operating contract.

- **TDD, RED first.** The failing test comes before the implementation, and the
  RED is observed, not assumed. A behaviour change with no test does not land.
- **The full suite is green.** `python -m pytest tests/ -q` from the repo root.
- **Lint is clean.** `python -m ruff check .`. The lint pins are deliberate:
  `target-version` tracks the minimum supported Python and must never be raised
  above the CI pin, and `exclude` must stay top-level in `ruff.toml` (under
  `[lint]` it is silently inert).
- **7-bit ASCII in authored content.** No em dashes, no en dashes, no smart
  quotes, anywhere: code, comments, docstrings, Markdown, commit messages. Use
  a spaced hyphen for a clause break. This is not a style preference - a UTF-8
  em dash inside a double-quoted PowerShell string decodes to a smart quote that
  terminates the string and cascades into a parse failure.
- **No personal data, ever.** No account home paths (`tests/test_no_account_paths.py`),
  no credential literals (`tests/test_no_secret_literals.py`), and no personal
  identity even split across lines (`tests/test_no_split_identity.py`). This
  repo is public; a commit here is one push from world-readable.
- **No `Co-Authored-By: Claude` trailer.** Stripped by `.githooks/commit-msg`.
- **Install the hooks before you commit:** `python tools/install_git_hooks.py`,
  then prove they fire with `python tools/install_git_hooks.py --check`.
  Presence of a hook file is not proof it runs - `core.hooksPath` points at the
  tracked `.githooks`, so anything written into `.git/hooks` is dead.

## Requirements

Windows plus Python 3.14. The GPU-backed upscaling and inpainting environments
are provisioned outside the repo and are not part of the default suite; the
cv-lane tests run off `requirements-cv.txt`.
