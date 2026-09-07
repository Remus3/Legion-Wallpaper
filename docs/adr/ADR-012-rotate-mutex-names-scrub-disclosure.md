# ADR-012: Mutex names rotated to opaque strings; capability and defect prose scrubbed

**Date:** 2026-09-07
**Status:** Accepted

## Context

LW has been a public repository since 2026-08-01 (ADR-referenced in CLAUDE.md
Settled, LEDGER 88), and `ops/loop/winmutex.py` and `ops/loop/slots.py` are
tracked. A sibling repo raised the disclosure while preparing its own flip to
public, believing it would be the first to publish those files. It would not
have been: LW verified live that
`raw.githubusercontent.com/Remus3/Legion-Wallpaper/main/ops/loop/winmutex.py`
returns HTTP 200 anonymously, so both mutex names and the surrounding prose had
already been world-readable for five weeks.

What was published was more than two strings. The header named the external
vendor, stated that it runs on a single metered account, and described - in
detail - a failover path that misreads a quota error as genuine exhaustion and
stickily swaps the backend for the rest of a run. The same paragraph was
mirrored in `ops/loop/loop_controller.py` and
`docs/specs/2026-07-26-f1-sdk-executor-channel.md`. That is a capability sketch
plus an unfixed behavioural defect, in a repo whose licence covers the process
and whose audience is strangers.

Alternatives weighed:

- **Accept and change nothing.** Defensible on secrecy grounds - the bytes are
  already out and LW's git history keeps them permanently, since a force-push
  does not purge GitHub-side unreachable objects (measured 2026-08-01). It buys
  nothing forward, though, and leaves the squattable strings live.
- **Trim the prose only** (a sibling's preference). Correct as far as it goes,
  and it fixes real drift - the header asserted an acquirer that one sibling
  had retired - but it leaves the exact `Global\` names published, and those
  are the part a local process can squat to starve every loop on the box.
- **Rotate the names only.** Closes the squat vector but keeps the defect
  description, which is the part that is actually about how the system fails.

## Decision

Do both, in one round with every loop stopped: rotate `GEMINI_MUTEX` and
`GPU_MUTEX` to opaque, non-descriptive strings, and remove the vendor,
metering, and failover-defect prose from `winmutex.py`, `loop_controller.py`
and the f1 spec. The SYMBOL names stay - they are the cross-repo API and
renaming them is a wider change than this decision covers.

## Consequences

**Good:** The published strings no longer name a vendor, a resource or a
project, and no longer document how the failover misbehaves. The retired names
are dead, so every historical mention of them in append-only records
(`docs/LEDGER.md`, `docs/history_notes.md`, dated artifacts under
`docs/_archive/` and `docs/CONCURRENCY_MEASURED_2026-08-01.md`) is now inert and
was deliberately left unedited rather than rewritten - the redaction is recorded
here instead of applied silently to history.

**Trade-off:** `winmutex.py` is BYTE-IDENTICAL-by-contract across the sibling
repos, so this is a joint re-pin round, and unlike the two previous re-pins it
is not docstring-only: the name VALUES move. Between the first tree landing the
new names and the last, two loops can hold DIFFERENT names and both believe
they are exclusive - the exact mutual exclusion the file exists to provide,
silently absent. That is why it was done with every loop stopped (verified at
authoring time: zero `loop_controller` processes, empty slots bucket) and why no
loop may start until every sibling has pinned the same bytes. The prose that was
removed also carried real rationale; the ADR now holds it instead of the file.

**Watch for:** the symbol names `GEMINI_MUTEX` / `GPU_MUTEX` still name the
vendor and the resource in a public file - a second round could rename them, at
the cost of touching every call site in three repos. And the underlying failover
defect is still unfixed: it is now undocumented in public rather than resolved,
which is a disclosure decision and not an engineering one.
