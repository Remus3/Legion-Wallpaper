"""Arms for `tools/lw_write_tracer.py`, the shareable write-attribution plugin.

END TO END, IN A REAL SUBPROCESS, NOT BY POKING INTERNALS. The thing being
shipped is a pytest plugin, and a plugin that works when its functions are
called by hand but not when pytest loads it is the failure mode that matters.
Every arm below generates a throwaway suite in `tmp_path` and runs a real
`pytest -p lw_write_tracer` over it.

THE BLIND SPOT IS PINNED BY AN ARM, NOT BY A SENTENCE. RC replied that its
suite shells out more than most and asked that the subprocess limit not be
buried, so `test_a_subprocess_write_is_NOT_caught` asserts the gap exists. If
someone later closes it, that arm fails and tells them to update the claim -
which a docstring cannot do.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TRACER = ROOT / "tools" / "lw_write_tracer.py"


def _run(tmp_path: Path, body: str, watch: Path | None = None,
         env_extra: dict | None = None) -> dict:
    """Generate a one-file suite, run it under the tracer, return the report."""
    (tmp_path / "test_generated.py").write_text(body, encoding="utf-8")
    live = watch if watch is not None else tmp_path / "live"
    live.mkdir(parents=True, exist_ok=True)
    out = tmp_path / "trace.json"
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", str(tmp_path / "test_generated.py"),
         "-q", "-p", "no:cacheprovider", "-p", "lw_write_tracer",
         "--trace-roots", str(live), "--trace-out", str(out)],
        cwd=str(tmp_path), capture_output=True, text=True,
        env={**_env(), "PYTHONPATH": str(ROOT / "tools"), **(env_extra or {})},
        timeout=300)
    assert out.exists(), f"no report written.\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
    return json.loads(out.read_text(encoding="utf-8"))


def _env() -> dict:
    import os
    return {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}


def test_an_append_is_counted_in_bytes_and_attributed_to_its_test(tmp_path):
    """MIRROR ARM. The tracer must actually fire, or every arm below is vacuous."""
    report = _run(tmp_path, '''
from pathlib import Path
LIVE = Path(__file__).parent / "live"

def test_writes():
    with open(LIVE / "day.log", "a", encoding="utf-8") as fh:
        fh.write("hello")
''')
    key = str(tmp_path / "live" / "day.log")
    assert report["wrote_bytes"][key] == 5
    assert report["written_by"][key] == ["test_generated.py::test_writes"]


def test_an_atomic_replace_is_caught_under_the_TARGET_name(tmp_path):
    """The route an open() wrapper alone cannot see: the only open it observes
    is the TMP name, and this repo's own rule makes tmp-then-replace the
    preferred way to write state - so the naive wrapper is blind to exactly the
    writes that matter most."""
    report = _run(tmp_path, '''
import os
from pathlib import Path
LIVE = Path(__file__).parent / "live"

def test_replaces():
    tmp = Path(__file__).parent / "scratch.tmp"
    tmp.write_text("payload", encoding="utf-8")
    os.replace(tmp, LIVE / "state.json")
''')
    assert str(tmp_path / "live" / "state.json") in report["written_by"]
    assert str(tmp_path / "scratch.tmp") not in report["written_by"], \
        "the tmp file is outside the watched root and must not be reported"


def test_an_open_that_never_writes_is_reported_separately(tmp_path):
    """Opening a log for append is not writing to it. A logging FileHandler
    opens on construction and may never emit, and reporting that as a write
    would overstate the defect - so it lands in its own bucket."""
    report = _run(tmp_path, '''
from pathlib import Path
LIVE = Path(__file__).parent / "live"

def test_opens_only():
    open(LIVE / "quiet.log", "a", encoding="utf-8").close()
''')
    key = str(tmp_path / "live" / "quiet.log")
    assert key in report["opened_for_write_only"]
    assert key not in report["wrote_bytes"]


def test_a_read_is_not_reported(tmp_path):
    """Non-vacuity in the other direction: a tracer that flagged reads would
    report every repo as guilty."""
    live = tmp_path / "live"
    live.mkdir()
    (live / "seed.txt").write_text("x", encoding="utf-8")
    report = _run(tmp_path, '''
from pathlib import Path
LIVE = Path(__file__).parent / "live"

def test_reads():
    assert (LIVE / "seed.txt").read_text(encoding="utf-8") == "x"
''')
    assert report["written_by"] == {}
    assert report["opened_for_write_only"] == {}


def test_a_write_outside_the_watched_root_is_ignored(tmp_path):
    """The report is about LIVE paths. A suite writing its own tmp dir is doing
    the right thing and must not appear."""
    report = _run(tmp_path, '''
from pathlib import Path

def test_writes_elsewhere():
    (Path(__file__).parent / "elsewhere.txt").write_text("x", encoding="utf-8")
''')
    assert report["wrote_bytes"] == {}
    assert report["written_by"] == {}


def test_a_subprocess_write_is_NOT_caught(tmp_path):
    """THE STATED LIMIT, PINNED. RC asked that this not be buried in prose,
    since its suite shells out more than most - so the gap is an assertion. If
    someone closes it, this arm fails and forces the claim to be updated, which
    is more than a docstring can do."""
    report = _run(tmp_path, '''
import subprocess, sys
from pathlib import Path
LIVE = Path(__file__).parent / "live"

def test_child_writes():
    subprocess.run([sys.executable, "-c",
                    "from pathlib import Path;"
                    f"Path(r'{LIVE / 'child.log'}').write_text('x', encoding='utf-8')"],
                   check=True)
    assert (LIVE / "child.log").exists(), "the child really did write"
''')
    assert str(tmp_path / "live" / "child.log") not in report["written_by"], \
        "subprocess writes are now caught - update the documented limit"
    assert "subprocess" in json.dumps(report["limits"]).lower(), \
        "the report must carry its own limits, so a reader cannot miss them"


def test_a_snapshot_and_RESTORE_is_reported_as_a_write_though_state_is_UNCHANGED(tmp_path):
    """THE SECOND STATED LIMIT, PINNED. This tracer answers 'did bytes move',
    never 'did state change', and the gap is not academic: on 2026-09-11 LW
    filed a finding against a sibling's suite on exactly this shape, and the
    sibling measured both records BYTE-IDENTICAL across the run - the bytes
    were the guard's RESTORE putting the operator's mail state back. A repair
    is indistinguishable here from the damage. So the arm asserts BOTH halves
    at once: the tracer names the restoring test, AND the record it names is
    unchanged on disk."""
    import hashlib

    live = tmp_path / "live"
    live.mkdir(parents=True, exist_ok=True)
    record = live / "inbox_seen.json"
    record.write_bytes(b'{"seen": ["a", "b"]}')
    before = hashlib.sha256(record.read_bytes()).hexdigest()

    report = _run(tmp_path, '''
from pathlib import Path
LIVE = Path(__file__).parent / "live"
RECORD = LIVE / "inbox_seen.json"

def test_guarded():
    snapshot = RECORD.read_bytes()
    try:
        RECORD.write_bytes(b'{"seen": ["a", "b", "c"]}')
    finally:
        RECORD.write_bytes(snapshot)
''', watch=live)

    after = hashlib.sha256(record.read_bytes()).hexdigest()
    assert after == before, "the generated guard must leave the record byte-identical"
    key = str(record)
    assert report["written_by"].get(key) == ["test_generated.py::test_guarded"],         "the tracer must still report the restoring test as a writer - that is the trap"
    assert report["wrote_bytes"][key] > 0, "and it reports real bytes for the repair"
    assert "bytes_not_state" in report["limits"],         "the report must carry this caveat itself, where a reader cannot miss it"


def test_the_report_names_every_test_that_touched_a_path(tmp_path):
    """One path, several culprits - the question an operator actually asks."""
    report = _run(tmp_path, '''
from pathlib import Path
LIVE = Path(__file__).parent / "live"

def _touch():
    with open(LIVE / "shared.log", "a", encoding="utf-8") as fh:
        fh.write("x")

def test_one(): _touch()
def test_two(): _touch()
''')
    key = str(tmp_path / "live" / "shared.log")
    assert report["written_by"][key] == ["test_generated.py::test_one",
                                         "test_generated.py::test_two"]
    assert report["wrote_bytes"][key] == 2


def test_the_builtins_are_restored_when_the_run_ends(tmp_path):
    """The plugin patches process-global names. Leaving them patched would make
    every later plugin and every later test observe a wrapped `open`."""
    report = _run(tmp_path, '''
import builtins, os
from pathlib import Path
LIVE = Path(__file__).parent / "live"

def test_marker():
    (LIVE / "x.log").write_text("x", encoding="utf-8")
    assert builtins.open.__name__ != "open" or True
''')
    assert report["restored"] is True


def test_a_pathlib_write_is_caught(tmp_path):
    """THE HOLE THE FIRST VERSION HAD. `builtins.open is io.open` is true, but
    `pathlib` calls `io.open(...)` by attribute lookup on the module, so a
    tracer that patches only `builtins` misses every `Path.write_text`,
    `Path.write_bytes` and `Path.open` - which is how most of this codebase
    writes. Mutation-proven: dropping the `io.open` patch makes this arm fail
    and leaves every other arm green."""
    report = _run(tmp_path, '''
from pathlib import Path
LIVE = Path(__file__).parent / "live"

def test_pathlib_write():
    (LIVE / "via_pathlib.json").write_text("{}", encoding="utf-8")
''')
    key = str(tmp_path / "live" / "via_pathlib.json")
    assert report["wrote_bytes"][key] == 2
    assert report["written_by"][key] == ["test_generated.py::test_pathlib_write"]


# --------------------------------------------------------------------------
# The self-check, adopted from LL's 2026-09-11 note
# --------------------------------------------------------------------------

def test_every_run_plants_a_control_and_reports_whether_it_was_PROVED(tmp_path):
    """LL's point 1, and the highest-value thing they named: an instrument that
    prints a zero with no self-check attached is reporting an absence of
    evidence dressed as evidence of absence. Their probe printed 188 findings
    beside "positive control UNPROVEN" and that admission is the only reason
    the number was worth anything.

    So every run plants a specimen through each patched route and says whether
    it came back."""
    report = _run(tmp_path, '''
def test_nothing():
    pass
''')
    control = report["control"]
    assert control["proved"] is True
    assert set(control["routes"]) == {"open", "io_open", "replace"}
    assert all(control["routes"].values()), control["routes"]


def test_the_control_specimens_are_scrubbed_from_the_findings(tmp_path):
    """A control that leaves its own specimens in the report would manufacture
    a finding in every tree it ran against - the over-reporting failure LL
    warns about, introduced by the very thing meant to prevent it."""
    report = _run(tmp_path, '''
def test_nothing():
    pass
''')
    assert report["wrote_bytes"] == {}
    assert report["written_by"] == {}
    for key in list(report["wrote_bytes"]) + list(report["written_by"]):
        assert "lw_tracer_control" not in key


def test_the_control_carries_a_NEGATIVE_specimen_too(tmp_path):
    """LL's point 2: a control made only of positive specimens proves the
    instrument can SEE and proves nothing about whether it INVENTS. A write
    outside every watched root is planted on each run, and the control fails if
    the tracer reports it."""
    report = _run(tmp_path, '''
def test_nothing():
    pass
''')
    assert report["control"]["negative_clean"] is True


def test_an_unproved_control_is_reported_rather_than_hidden(tmp_path):
    """The shape that matters when it goes wrong. Forcing the control to fail
    must produce `proved: false` in a report that still WRITES - a self-check
    that suppressed the report would leave the operator with nothing at all."""
    report = _run(tmp_path, '''
def test_nothing():
    pass
''', env_extra={"LW_TRACE_BREAK_CONTROL": "io_open"})
    assert report["control"]["proved"] is False
    assert report["control"]["routes"]["io_open"] is False
    assert report["control"]["routes"]["open"] is True, \
        "only the named route breaks - the rest must still prove"
