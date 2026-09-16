"""Generate the pipeline state diagram FROM the pipeline code.

Why this exists rather than an external diagram tool
----------------------------------------------------
The operator queued `tt-a1i/archify` on 2026-09-15 to render LW's structure as
a checked diagram instead of prose. The job is real; the instrument was wrong
for this tree, and the scope answer is recorded in `ROADMAP.md` and in the
header of the generated `docs/PIPELINE_DIAGRAM.md`. The short version: its
documented install is machine-wide (a cross-tree effect, which is a sync-inbox
matter and never unilateral), its output is self-contained HTML that GitHub
does not render inline - so the diagram would be invisible exactly where
ARCHITECTURE.md is read - and a repo-local install means vendoring ~157 MB into
a PUBLIC tree. Mermaid needs none of that and GitHub renders it natively.

What actually makes a diagram worth having is not the renderer. It is that the
diagram cannot quietly disagree with the code. So every state and every edge
here is DERIVED from `lw_pipeline.py`'s own constants - rename a folder there
and this output changes with it - and `tests/test_pipeline_diagram.py` fails
if the tracked file is stale or if `lw_pipeline.py` grows a transition verb
this generator neither draws nor declares in-place.

Usage:
  python tools/lw_diagram.py            # print to stdout
  python tools/lw_diagram.py --write    # rewrite docs/PIPELINE_DIAGRAM.md
  python tools/lw_diagram.py --check    # exit 1 if the tracked file is stale
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import lw_pipeline  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
DOC = REPO / "docs" / "PIPELINE_DIAGRAM.md"

# Verbs lw_pipeline logs that do NOT change which stage folder an image sits
# in. Each stays off the diagram on purpose, with its reason, so the coverage
# arm in tests/test_pipeline_diagram.py stays a real assertion rather than a
# list that grows whenever it is inconvenient.
IN_PLACE_OPS = {
    "SAVE_WORKING",       # writes a working file inside the same scratch folder
    "SUBMIT",             # moves into the _needauth queue WITHIN the scratch
    "ANNOTATE",           # metadata only - metrics, source URL, vision audit
    "GC_DONE",            # deletes a superseded Done folder; no image advances
    "REMOVE",             # operator teardown of a slug, outside the ladder
    "DELIVER_PICTURES",   # optional copy OUT to Pictures; the slug does not move
}

# Stage-folder node ids, in ladder order. Label is the real folder name.
_ORIGINALS = "ORIGINALS"
_BACKUP = "BACKUP"


def _scratch_id(stage: str) -> str:
    return f"{stage.upper()}_SCRATCH"


def _done_id(stage: str) -> str:
    # The last stage's Done folder is "8.End Review" - name the node for what
    # the folder IS, not for the stage that fills it.
    return "END_REVIEW" if stage == lw_pipeline.STAGES[-1] else f"{stage.upper()}_DONE"


def build_states() -> dict[str, str]:
    """Node id -> the real folder name it stands for."""
    states = {_ORIGINALS: lw_pipeline.ORIGINALS}
    for stage in lw_pipeline.STAGES:
        states[_scratch_id(stage)] = lw_pipeline.SCRATCH_DIR[stage]
        states[_done_id(stage)] = lw_pipeline.DONE_DIR[stage]
    states[_BACKUP] = lw_pipeline.BACKUP
    return states


def build_edges() -> list[tuple[str, str, str]]:
    """(op, src node id, dst node id) for every folder-CHANGING transition.

    Each edge mirrors a real `ctx.log(...)` call site in lw_pipeline.py.
    """
    stages = lw_pipeline.STAGES
    last = stages[-1]
    edges: list[tuple[str, str, str]] = [
        ("INTAKE", _ORIGINALS, _scratch_id(stages[0])),
    ]
    for stage in stages:
        edges.append((lw_pipeline.APPROVE_OP[stage], _scratch_id(stage), _done_id(stage)))
    for prev, nxt in zip(stages, stages[1:], strict=False):
        edges.append((lw_pipeline.START_OP[nxt], _done_id(prev), _scratch_id(nxt)))
    # A rejected submission stays in its own scratch folder and is re-worked.
    for stage in stages:
        edges.append(("REJECT", _scratch_id(stage), _scratch_id(stage)))
    # End Review is the only place a REJECT demotes across a folder boundary.
    edges.append(("REJECT", _done_id(last), _scratch_id(last)))
    edges.append(("FINALIZE", _done_id(last), _BACKUP))
    # reopen --to <stage> pulls a slug back to any EARLIER scratch folder.
    for stage in stages:
        for earlier in stages[: stages.index(stage) + 1]:
            src = _done_id(stage)
            dst = _scratch_id(earlier)
            if (("REOPEN", src, dst)) not in edges:
                edges.append(("REOPEN", src, dst))
    return edges


def _mermaid() -> str:
    states = build_states()
    lines = ["stateDiagram-v2"]
    for node, folder in states.items():
        lines.append(f'    {node} : {folder}')
    lines.append("    [*] --> ORIGINALS")
    drawn: set[tuple[str, str, str]] = set()
    for op, src, dst in build_edges():
        if (op, src, dst) in drawn:
            continue
        drawn.add((op, src, dst))
        lines.append(f"    {src} --> {dst} : {op}")
    lines.append(f"    {_BACKUP} --> [*]")
    return "\n".join(lines)


def render_document() -> str:
    states = build_states()
    edges = build_edges()
    reopen = sorted({(s, d) for op, s, d in edges if op == "REOPEN"})
    body = [
        "# Pipeline state diagram (generated)",
        "",
        "**Generated by `tools/lw_diagram.py` from `tools/lw_pipeline.py`'s own",
        "constants. Do not hand-edit** - `tests/test_pipeline_diagram.py` compares",
        "this file byte-for-byte against a fresh generation, and fails if",
        "`lw_pipeline.py` grows a transition verb this diagram does not draw.",
        "Regenerate with:",
        "",
        "```",
        "python tools/lw_diagram.py --write",
        "```",
        "",
        "Every node is a real folder under `images\\` (ADR-003) and every edge is a",
        "transition `lw_pipeline.py` actually logs to `PIPELINE_LOG.md`. The prose",
        "map in `docs/ARCHITECTURE.md` stays the reference for what each folder",
        "HOLDS; this is the reference for how an image MOVES.",
        "",
        "## The ladder",
        "",
        "```mermaid",
        _mermaid(),
        "```",
        "",
        "## States",
        "",
        "| node | folder |",
        "| --- | --- |",
    ]
    for node, folder in states.items():
        body.append(f"| `{node}` | `{folder}` |")
    body += [
        "",
        "## Edges",
        "",
        "| op | from | to |",
        "| --- | --- | --- |",
    ]
    seen: set[tuple[str, str, str]] = set()
    for op, src, dst in edges:
        if (op, src, dst) in seen:
            continue
        seen.add((op, src, dst))
        body.append(f"| `{op}` | `{states[src]}` | `{states[dst]}` |")
    body += [
        "",
        "## What the diagram deliberately does not draw",
        "",
        "In-place verbs. These are logged to `PIPELINE_LOG.md` and change the",
        "contents of a folder, not which folder an image is in, so drawing them",
        "would add self-loops to every node and say nothing:",
        "",
    ]
    for op in sorted(IN_PLACE_OPS):
        body.append(f"- `{op}`")
    body += [
        "",
        f"`REOPEN` is drawn ({len(reopen)} edges): `reopen --to <stage>` pulls a",
        "slug back to any earlier scratch folder, which is how a finished image",
        "is re-processed. It is the only backward path other than the End Review",
        "demotion.",
        "",
        "## Why this is mermaid and not an external diagram tool",
        "",
        "The operator queued `tt-a1i/archify` (MIT) on 2026-09-15 for exactly this",
        "job. The scope answer, recorded in `ROADMAP.md`: the job is real, that",
        "instrument is wrong HERE. Its documented install is machine-wide, which",
        "reaches four sibling trees and is therefore a sync-inbox matter rather",
        "than a unilateral one; its output is self-contained HTML, which GitHub",
        "does not render inline, so the diagram would be invisible on the page",
        "where it would be read; and a repo-local install means vendoring about",
        "157 MB into a PUBLIC tree. Mermaid costs no install, stays 7-bit ASCII,",
        "renders natively on GitHub, and - the part that actually matters - can",
        "be generated from the code so it cannot drift.",
        "",
    ]
    return "\n".join(body)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--write", action="store_true", help="rewrite the tracked doc")
    ap.add_argument("--check", action="store_true", help="exit 1 if the doc is stale")
    args = ap.parse_args(argv)
    fresh = render_document()
    if args.write:
        tmp = DOC.with_suffix(".md.tmp")
        tmp.write_bytes(fresh.encode("utf-8"))
        tmp.replace(DOC)
        print(f"wrote {DOC}")
        return 0
    if args.check:
        current = DOC.read_bytes().decode("utf-8") if DOC.is_file() else ""
        if current != fresh:
            print("STALE: docs/PIPELINE_DIAGRAM.md differs from a fresh generation")
            return 1
        print("OK: docs/PIPELINE_DIAGRAM.md is current")
        return 0
    print(fresh)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
