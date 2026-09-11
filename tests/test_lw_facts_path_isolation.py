"""Arms for path isolation in `tools/lw_facts.py`.

MEASURED 2026-09-11, by tracing every write the suite performs in-process.
`test_main_emits_pipeline_section` patched `_ROOT`, `_HEALTH` and `_WAKEUP` and
then called `main()` - which wrote the operator's REAL
`ops/runtime/sync_inbox_reported.json`, because `_INBOX`, `_SEEN` and
`_REPORTED` are bound to the real root at IMPORT time and no `_ROOT` patch can
move them afterwards.

WHY IT MATTERS MORE THAN A STRAY FILE. That file is half of the
report-then-acknowledge split: the ack computes `seen = (seen OR reported) AND
still present`. A suite run that writes `reported` therefore marks whatever is
in the live inbox as HAVING BEEN SHOWN to the operator - and the next
`--mark-inbox-seen` acknowledges mail nobody ever saw. That is the LEDGER 162
defect exactly, re-entered through the test suite rather than through the hook.

THE FIX IS THE DERIVATION, NOT THE ARM. Patching three more names in one test
would leave the next test to rediscover this, so the paths are derived from
`_ROOT` when they are USED. Patching `_ROOT` is then sufficient, which is what
every arm in the tree already assumes.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import lw_facts  # noqa: E402


def _stat(p: Path):
    return p.stat().st_mtime_ns if p.exists() else None


def test_the_inbox_paths_follow_a_patched_root(monkeypatch, tmp_path):
    """MIRROR ARM. The derivation must actually fire."""
    monkeypatch.setattr(lw_facts, "_ROOT", tmp_path)
    assert lw_facts._inbox_path() == tmp_path / "moon_sync_inbox"
    assert lw_facts._seen_path() == tmp_path / "ops" / "runtime" / "sync_inbox_seen.json"
    assert lw_facts._reported_path() == tmp_path / "ops" / "runtime" / "sync_inbox_reported.json"


def test_main_under_a_patched_root_never_writes_the_live_reported_record(
        monkeypatch, tmp_path, capsys):
    """The defect itself: a full `main()` with `_ROOT` redirected must leave the
    operator's acknowledgement state byte-identical."""
    live = ROOT / "ops" / "runtime" / "sync_inbox_reported.json"
    before_stat = _stat(live)
    before_bytes = live.read_bytes() if live.exists() else None

    (tmp_path / "moon_sync_inbox").mkdir(parents=True)
    (tmp_path / "moon_sync_inbox" / "2026-09-11-0001-from-RC-x.md").write_text(
        "x\n", encoding="utf-8")
    monkeypatch.setattr(lw_facts, "_ROOT", tmp_path)
    monkeypatch.setattr(lw_facts, "_HEALTH", tmp_path / "ops" / "runtime" / "health.json")
    monkeypatch.setattr(lw_facts, "_WAKEUP", tmp_path / "WAKEUP_NOTES.md")

    lw_facts.main()
    capsys.readouterr()

    assert _stat(live) == before_stat, "main() wrote the live reported record"
    assert (live.read_bytes() if live.exists() else None) == before_bytes
    assert (tmp_path / "ops" / "runtime" / "sync_inbox_reported.json").exists(), \
        "and it must have written the REDIRECTED one, or the arm proves nothing"


def test_the_module_constants_still_name_the_real_paths():
    """The derivation must not quietly move the live locations."""
    assert lw_facts._INBOX == lw_facts._ROOT / "moon_sync_inbox"
    assert lw_facts._SEEN.name == "sync_inbox_seen.json"
    assert lw_facts._REPORTED.name == "sync_inbox_reported.json"


# --------------------------------------------------------------------------
# The same defect, second site
# --------------------------------------------------------------------------

def test_lw_monitor_main_can_be_told_where_to_log(monkeypatch, tmp_path):
    """`main()` called `setup_logging(MONITOR_LOG)` with no override, so every
    arm that drove it attached a handler to the operator's real
    `logs/lw_monitor.log`. Found by the same write trace; it is the milder
    sibling of the reported-record defect, since a handler that opens and never
    emits leaves no bytes - but "it happened not to write this time" is not
    isolation."""
    import lw_monitor

    live = ROOT / "logs" / "lw_monitor.log"
    before = _stat(live)
    target = tmp_path / "monitor.log"
    holder = lw_monitor.MonitorServer(
        ("127.0.0.1", 0), lw_monitor.Handler,
        state_path=tmp_path / "s.json", log_path=tmp_path / "l.md",
        page_path=tmp_path / "p.html", image_roots=[tmp_path], cache={})
    port = holder.server_address[1]
    monkeypatch.setattr(lw_monitor.webbrowser, "open", lambda url: None)
    try:
        rc = lw_monitor.main(["--port", str(port), "--open",
                              "--monitor-log", str(target)])
    finally:
        holder.server_close()

    assert rc == 0
    assert target.exists(), "the redirected log must be the one that was opened"
    assert _stat(live) == before, "main() reached the live monitor log anyway"
