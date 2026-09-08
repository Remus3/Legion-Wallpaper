# Security Policy

## Scope

This repository publishes a process, not a service. There is no deployment, no
server, no user data and no released package: the code runs on one operator's
Windows workstation. So the realistic report classes are narrower than the usual
template implies, and they are the ones this project actually cares about.

**In scope**

- A **secret, credential or token** committed anywhere in the tree or reachable
  in history. Live keys are meant to live in machine-level environment variables
  and in gitignored `API-Key-*.txt` files at the repo root; anything else is a
  defect.
- **Personal or machine-identifying data** in a tracked file: an account home
  path, a personal email address, a machine layout. Including one that is
  **split across lines** or written in reverse - that is a real failure mode
  here, not a hypothetical (`tests/test_no_split_identity.py`).
- A **guard that does not guard**: a hook, gate or sweep that reports clean on
  input it is supposed to reject. A guard nobody has seen fail asserts nothing,
  so a demonstrated false green is a genuine finding.
- Code in this repo that would **execute untrusted input** or write outside its
  intended tree.

**Out of scope**

- The image corpus. It is third-party illustration, it is not tracked here, and
  it is not a security surface.
- Dependency advisories with no exploit path through this code.
- Anything requiring an attacker to already have an interactive session on the
  operator's workstation.

## Reporting

**Do not open a public issue for anything in scope above.** A public issue about
a leaked value republishes the value, which is the exact mistake this project
has already made once and now guards against.

Use GitHub's private vulnerability reporting on this repository:
**Security -> Advisories -> Report a vulnerability**. That channel needs no
email address, which is deliberate - the maintainer publishes none.

If that form is not available to you, open the smallest possible public issue
that says a private channel is needed and contains **no detail and no value**,
and wait to be contacted.

## What to expect

One maintainer, best effort, no SLA. Expect an acknowledgement within a few
days. A confirmed leak is fixed forward and a guard is added in the same change
so it cannot silently return: history rewriting is deliberately not the default
remedy here, because a force-push does not purge server-side unreachable
objects and the rewrite invalidates every SHA already cited in the docs.

## Supported versions

`main` only. There are no releases and no backports.
