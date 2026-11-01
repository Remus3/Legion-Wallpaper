"""Before/after slider page for one item in the human QA queue (LW-QA-SLIDER).

MAIN W44 UI/UX round (2026-10-31), after upscayl's compare view: the operator
judges stage N against stage N-1 by dragging one divider across a single box,
with the gate metrics beside it instead of in a manifest.

  stage N    `<slug>_<stage>needauth.*`  the submitted candidate
  stage N-1  `<slug>_<stage>initial.*`   that stage's input milestone

Both images are drawn in ONE box sized to the candidate's aspect, so the
browser resamples the baseline to the candidate's display scale (common scale
for the eye; the gate's own FR common scale is printed beside it). Metrics are
the newest `audit` carrying a `gate` key in the slug's manifest; an item with
none says so on the page rather than showing an empty panel.

Read-only: reads ops/runtime/pipeline_state.json and the slug folder, writes
ONE html file (default ops/runtime/review/qa_slider.html, gitignored), touches
no pixels and no pipeline state. Image srcs are file:// URIs, so the page opens
straight off disk.

  python tools/lw_qa_slider.py                 # first NEEDAUTH item
  python tools/lw_qa_slider.py --slug <slug>   # a named one
  python tools/lw_qa_slider.py --list          # the queue
"""
from __future__ import annotations

import argparse
import html
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "ops" / "runtime" / "pipeline_state.json"
IMAGES = ROOT / "images"
OUT = ROOT / "ops" / "runtime" / "review" / "qa_slider.html"
STAGES = ("first", "clean", "final", "last")
IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".webp", ".bmp")


def queue(state: dict) -> list:
    """Slugs waiting on the operator (substate NEEDAUTH), sorted."""
    images = state.get("images") or {}
    return sorted(s for s, v in images.items()
                  if isinstance(v, dict) and v.get("substate") == "NEEDAUTH")


def _milestone(folder: Path, slug: str, stage: str, phase: str):
    for ext in IMAGE_EXTS:
        path = folder / f"{slug}_{stage}{phase}{ext}"
        if path.is_file():
            return path
    return None


def pair(folder: Path, slug: str):
    """(stage, before, after) for the slug's pending candidate, else None."""
    for stage in STAGES:
        after = _milestone(folder, slug, stage, "needauth")
        if after is None:
            continue
        before = _milestone(folder, slug, stage, "initial")
        if before is not None:
            return stage, before, after
    return None


def gate_metrics(manifest: dict):
    """The newest transition audit that names a gate, else None."""
    for t in reversed(manifest.get("transitions") or []):
        audit = t.get("audit") if isinstance(t, dict) else None
        if isinstance(audit, dict) and audit.get("gate"):
            return audit
    return None


def _fmt(value) -> str:
    if isinstance(value, float):
        return f"{value:.4f}"
    if isinstance(value, (list, tuple)) and len(value) == 2:
        return f"{value[0]}x{value[1]}"
    return str(value)


def _metric_rows(audit) -> str:
    if not audit:
        return '<p class="note">no gate audit recorded for this item</p>'
    rows = [("gate", audit.get("gate")), ("verdict", audit.get("verdict"))]
    rows += sorted((audit.get("metrics") or {}).items())
    fr = audit.get("fr_all") or {}
    if fr.get("common_scale"):
        rows.append(("FR common scale", fr["common_scale"]))
    reasons = audit.get("reasons")
    if reasons:
        rows.append(("reasons", "; ".join(str(r) for r in reasons)))
    body = "".join(f"<tr><th scope=\"row\">{html.escape(str(k))}</th>"
                   f"<td>{html.escape(_fmt(v))}</td></tr>" for k, v in rows)
    return f"<table><caption>Gate metrics</caption>{body}</table>"


_CSS = """
body{font:16px/1.5 system-ui,sans-serif;margin:0;padding:16px;background:#111;color:#eee}
h1{font-size:20px;margin:0 0 4px;overflow-wrap:anywhere}
p.sub{margin:0 0 16px;color:#bbb}
main{display:flex;gap:24px;align-items:flex-start;flex-wrap:wrap}
.cmp{position:relative;flex:1 1 640px;max-width:1280px;aspect-ratio:16/9;background:#000}
.cmp img{position:absolute;inset:0;width:100%;height:100%;object-fit:contain}
#after{clip-path:inset(0 0 0 50%)}
.lbl{position:absolute;top:8px;padding:2px 8px;background:#000c;font-size:14px}
.lbl.l{left:8px}.lbl.r{right:8px}
#bar{position:absolute;top:0;bottom:0;left:50%;width:2px;background:#fc6;pointer-events:none}
input[type=range]{width:100%;min-height:44px;margin:8px 0 0}
aside{flex:0 1 320px}
table{border-collapse:collapse;width:100%}
caption{text-align:left;font-weight:600;padding-bottom:8px}
th,td{padding:6px 8px;border-bottom:1px solid #333;text-align:left;font-size:14px}
td{font-variant-numeric:tabular-nums;overflow-wrap:anywhere}
.note{color:#fc6}
"""

_JS = """
var s=document.getElementById('split'),a=document.getElementById('after'),b=document.getElementById('bar');
function u(){a.style.clipPath='inset(0 0 0 '+s.value+'%)';b.style.left=s.value+'%';
s.setAttribute('aria-valuetext',(100-s.value)+' percent candidate shown');}
s.addEventListener('input',u);u();
"""


def build_page(slug, stage, before: Path, after: Path, audit) -> str:
    """The whole page as an ASCII string."""
    name = html.escape(slug)
    b_uri = html.escape(Path(before).resolve().as_uri(), quote=True)
    a_uri = html.escape(Path(after).resolve().as_uri(), quote=True)
    stage_e = html.escape(stage)
    page = (
        "<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\">"
        "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
        f"<title>QA slider - {name}</title><style>{_CSS}</style></head><body>"
        f"<header><h1>{name}</h1>"
        f"<p class=\"sub\">Stage {stage_e}: input (N-1, left) against the submitted "
        "candidate (N, right), drawn in one box at the candidate's scale. "
        "Drag the slider to move the divider.</p></header>"
        "<main><section aria-label=\"before and after\" style=\"flex:1 1 640px\">"
        "<div class=\"cmp\">"
        f"<img id=\"before\" src=\"{b_uri}\" alt=\"{stage_e} input (N-1)\">"
        f"<img id=\"after\" src=\"{a_uri}\" alt=\"{stage_e} candidate (N)\">"
        f"<span class=\"lbl l\">N-1 {stage_e}initial</span>"
        f"<span class=\"lbl r\">N {stage_e}needauth</span><span id=\"bar\"></span></div>"
        "<label for=\"split\">Divider position (percent from left)</label>"
        "<input id=\"split\" type=\"range\" min=\"0\" max=\"100\" value=\"50\">"
        f"</section><aside>{_metric_rows(audit)}</aside></main>"
        f"<script>{_JS}</script></body></html>\n"
    )
    return page.encode("ascii", "xmlcharrefreplace").decode("ascii")


def _load_json(path: Path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--slug", default=None, help="queued slug (default: first)")
    ap.add_argument("--list", action="store_true", help="print the queue")
    ap.add_argument("--state", default=str(STATE))
    ap.add_argument("--images", default=str(IMAGES))
    ap.add_argument("--out", default=str(OUT))
    args = ap.parse_args(argv)

    state = _load_json(Path(args.state))
    if not isinstance(state, dict):
        print("qa-slider: pipeline state unreadable - run lw_pipeline scan",
              file=sys.stderr)
        return 2
    pending = queue(state)
    if args.list:
        for slug in pending:
            print(slug)
        return 0
    if not pending:
        print("qa-slider: the QA queue is empty - nothing to compare")
        return 1
    slug = args.slug or pending[0]
    entry = (state.get("images") or {}).get(slug)
    if slug not in pending or not isinstance(entry, dict):
        print(f"qa-slider: {slug} is not in the QA queue", file=sys.stderr)
        return 2
    folder = Path(args.images) / str(entry.get("stage_folder") or "") / slug
    found = pair(folder, slug)
    if found is None:
        print(f"qa-slider: {slug} has no initial + needauth pair on disk",
              file=sys.stderr)
        return 2
    stage, before, after = found
    manifest = _load_json(folder / "manifest.json") or {}
    page = build_page(slug, stage, before, after, gate_metrics(manifest))
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_name(out.name + ".tmp")
    tmp.write_bytes(page.encode("ascii"))
    tmp.replace(out)
    print(f"qa-slider: {slug} ({stage}) -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
