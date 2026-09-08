<!--
Read CONTRIBUTING.md first. Pull requests are not solicited on this repository -
open an issue and ask before spending time on one. If a PR was invited, the
boxes below are the gates the maintainer runs on every commit; they are enforced
by hooks and CI, not by review goodwill.
-->

## What this changes, and why

One paragraph. Say what was WRONG, not what you added.

## Premise check

What did you verify against ground truth before writing code, and how? Cite
`file:line`, a command and its output, or a decision in `docs/adr/`. A premise
taken from a doc without re-probing it is how this repo gets bugs.

## Evidence

- [ ] **RED first** - the failing test was written and OBSERVED failing before
      the implementation existed. Paste the failure.
- [ ] **Full suite green** - `python -m pytest tests/ -q`, last line pasted
      below, from a run made AFTER the final edit.
- [ ] **Lint clean** - `python -m ruff check .`
- [ ] Sibling cases checked. If this is one of a family (other modes, other
      variants, duplicate code paths), say which siblings you grepped for and
      which are covered by a test.
- [ ] If this fixes data corruption, already-corrupted rows are backfilled, not
      only future ones prevented.

```
paste the suite line and the RED evidence here
```

## Hygiene

- [ ] 7-bit ASCII only in authored content. No em dashes, en dashes or smart
      quotes, anywhere - including this description and the commit messages.
- [ ] No account home paths, credential literals, or personal identity in any
      tracked file, contiguous or split across lines.
- [ ] No `Co-Authored-By: Claude` trailer in any commit message.
- [ ] Git hooks installed and PROVEN to fire:
      `python tools/install_git_hooks.py --check`
- [ ] No image bytes, and nothing from the corpus, added to the tree.
