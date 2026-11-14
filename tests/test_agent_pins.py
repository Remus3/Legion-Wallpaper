"""MAIN ORDER 2026-11-14-0935 item 4: every sub-agent file pins model and effort.

An unpinned .claude/agents/*.md inherits the parent's model and effort (the
interactive default is xhigh). The model is an ALIAS, never a dated id.
"""
from __future__ import annotations

import re
from pathlib import Path

AGENTS = Path(__file__).resolve().parent.parent / ".claude" / "agents"
MODELS = {"opus", "sonnet", "haiku", "inherit"}
EFFORTS = {"low", "medium", "high", "xhigh", "max"}


def _front(path: Path) -> dict:
    text = path.read_text(encoding="ascii")
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    assert m, f"{path.name}: no frontmatter"
    return dict(ln.split(":", 1) for ln in m.group(1).splitlines() if ":" in ln)


def test_every_agent_file_pins_a_model_alias_and_an_effort():
    files = sorted(AGENTS.glob("*.md"))
    assert files
    for f in files:
        fm = {k.strip(): v.strip() for k, v in _front(f).items()}
        assert fm.get("model") in MODELS, f"{f.name}: model {fm.get('model')!r}"
        assert fm.get("effort") in EFFORTS, f"{f.name}: effort {fm.get('effort')!r}"


def test_the_verifier_runs_at_sonnet_medium():
    fm = {k.strip(): v.strip() for k, v in _front(AGENTS / "verifier.md").items()}
    assert (fm["model"], fm["effort"]) == ("sonnet", "medium")
