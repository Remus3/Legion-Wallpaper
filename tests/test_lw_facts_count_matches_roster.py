"""lw_facts: a count must be computed from the ROWS it ships beside it.

MEASURED LIVE ON THIS BOX 2026-10-02. `python tools/lw_facts.py` printed:

    - scheduled tasks (6 LW-*):
      - LW-CIWatchdog: state=Ready
      - LW-InboxResponder: state=Disabled
      - LW-Wallpaper: state=Ready
      - LW-WeeklyHygiene: state=Ready

Six claimed, four shipped. The header counts `len(rows)` over the RAW schtasks
CSV, which emits one record per TRIGGER, while the roster iterates
`sorted(set(rows))`. So the count and the rows it sits above were computed from
two different populations, and the report gave a reader no way to tell which
number was the answer. That is the count-as-evidence class: a total that
reconciles against nothing is blind to the rows, and here it did not even
reconcile against the rows printed directly underneath it.

THE RULE THIS ENFORCES is LW's own, from memory `feedback-anchor-name-searches`:
print a sample beside every count. A count whose sample contradicts it is worse
than no sample, because it looks checked.

HERMETIC. `_task_lines` is driven with a stubbed `_run` returning a fixed CSV, so
the arms do not depend on which tasks this machine has registered.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

import lw_facts as LF  # noqa: E402

# One record per trigger, exactly as schtasks /FO CSV /NH emits it. LW-CIWatchdog
# is registered at boot AND on a PT2M repeat, so it legitimately appears twice.
_CSV_WITH_REPEAT_TRIGGERS = (
    '"\\LW-CIWatchdog","2026-10-02 09:00:00","Ready"\n'
    '"\\LW-CIWatchdog","2026-10-02 09:02:00","Ready"\n'
    '"\\LW-Wallpaper","2026-10-02 10:00:00","Ready"\n'
    '"\\LW-WeeklyHygiene","2026-10-04 04:17:00","Ready"\n'
    '"\\Microsoft\\Windows\\Defrag\\ScheduledDefrag","N/A","Ready"\n'
)


@pytest.fixture
def stub_schtasks(monkeypatch):
    def _install(csv_text: str):
        monkeypatch.setattr(LF, "_run", lambda *a, **k: csv_text)
    return _install


def _roster_names(lines: list[str]) -> list[str]:
    return [ln.strip()[2:].split(":")[0] for ln in lines[1:] if ln.strip().startswith("- ")]


def test_the_header_count_equals_the_rows_it_ships(stub_schtasks):
    """The arm. Five raw records, four distinct tasks, three of them LW-*."""
    stub_schtasks(_CSV_WITH_REPEAT_TRIGGERS)
    anomalies: list[str] = []
    lines = LF._task_lines(anomalies)
    names = _roster_names(lines)
    assert names == ["LW-CIWatchdog", "LW-Wallpaper", "LW-WeeklyHygiene"]
    assert f"({len(names)} LW-*)" in lines[0], (
        f"header count disagrees with the {len(names)} rows under it: {lines[0]}")


def test_a_repeat_trigger_is_not_counted_as_a_second_task(stub_schtasks):
    """The exact live defect: a second trigger inflated the header by one."""
    stub_schtasks(_CSV_WITH_REPEAT_TRIGGERS)
    lines = LF._task_lines([])
    assert "(3 LW-*)" in lines[0], f"repeat trigger double-counted: {lines[0]}"


def test_the_count_is_not_hardcoded_and_tracks_the_population(stub_schtasks):
    """Non-vacuity control: a different population must move the number.

    Without this, `(3 LW-*)` is satisfiable by writing 3 into the format string,
    and the arm above would still pass.
    """
    stub_schtasks('"\\LW-Only","N/A","Ready"\n')
    lines = LF._task_lines([])
    assert "(1 LW-*)" in lines[0], lines[0]
    assert _roster_names(lines) == ["LW-Only"]


def test_a_disabled_task_is_still_reported_as_an_anomaly_once(stub_schtasks):
    """Deduplicating the roster must not drop - or duplicate - the anomaly."""
    stub_schtasks(
        '"\\LW-InboxResponder","N/A","Disabled"\n'
        '"\\LW-InboxResponder","N/A","Disabled"\n'
    )
    anomalies: list[str] = []
    lines = LF._task_lines(anomalies)
    assert "(1 LW-*)" in lines[0], lines[0]
    assert anomalies == ["scheduled task LW-InboxResponder is Disabled"], anomalies


def test_no_lw_tasks_at_all_says_so_rather_than_printing_zero(stub_schtasks):
    """An empty population is reported as empty, not as a count with no rows."""
    stub_schtasks('"\\Microsoft\\Windows\\Defrag\\ScheduledDefrag","N/A","Ready"\n')
    lines = LF._task_lines([])
    assert lines == ["- scheduled tasks (LW-*): none registered yet"], lines


# ---------------------------------------------------------------------------
# the pipeline digest: the one actionable count had no roster at all
# ---------------------------------------------------------------------------
def test_the_loose_originals_count_ships_a_sample_of_the_names(tmp_path):
    """`0.Originals: N loose files awaiting intake` is the line an operator ACTS
    on, and it shipped a bare N. A reader could not tell 8 real drops from one
    stray `Thumbs.db` counted eight times by a bad filter. Name some of them.
    """
    images = tmp_path / "images"
    orig = images / LF._STAGE_FOLDERS[0]
    orig.mkdir(parents=True)
    for name in ("alpha.png", "bravo.png", "charlie.png", "delta.png"):
        (orig / name).write_bytes(b"x")
    (orig / ".gitkeep").write_bytes(b"")
    for stage in LF._STAGE_FOLDERS[1:]:
        (images / stage).mkdir(parents=True)
    lines = LF._pipeline_lines([], root=tmp_path)
    head = next(ln for ln in lines if "0.Originals" in ln)
    assert "4 loose files" in head, head
    assert "alpha.png" in head and "bravo.png" in head, (
        f"the count shipped without a single row to check it against: {head}")


def test_the_loose_sample_is_bounded_and_says_how_many_it_withheld(tmp_path):
    """A sample is a sample: it must not dump 135 filenames into the report, and
    it must say that it truncated so the reader is not misled into reading the
    sample as the roster.
    """
    images = tmp_path / "images"
    orig = images / LF._STAGE_FOLDERS[0]
    orig.mkdir(parents=True)
    for i in range(12):
        (orig / f"img{i:02d}.png").write_bytes(b"x")
    for stage in LF._STAGE_FOLDERS[1:]:
        (images / stage).mkdir(parents=True)
    head = next(ln for ln in LF._pipeline_lines([], root=tmp_path)
                if "0.Originals" in ln)
    assert "12 loose files" in head, head
    assert head.count(".png") <= 4, f"dumped the whole roster: {head}"
    assert "more" in head, f"truncated silently: {head}"
