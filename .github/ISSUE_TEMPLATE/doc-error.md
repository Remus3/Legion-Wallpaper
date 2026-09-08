---
name: Factual error in the docs
about: A doc that contradicts the code, a stale command, a path or SHA that does not resolve
title: ''
labels: ''
assignees: ''
---

<!--
Read CONTRIBUTING.md first. This is for a doc that is WRONG, not for a doc you
would have written differently.
-->

## Where

`path/to/file.md:LINE`

## What it says

Quote the line.

## What is actually true

Cite the ground truth: `file:line` in the code, a command and its output, or a
decision in `docs/adr/`.

<!--
Three notes on citing SHAs, because this repo makes it easy to get wrong:
history has been rewritten three times (2026-08-01, 2026-09-06, 2026-09-07), so
a SHA cited in a doc written before 2026-09-07 may not resolve today. The maps
in docs/_archive/ walk it forward, oldest first. Say which map you used.
-->
