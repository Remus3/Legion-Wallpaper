r"""The executor slot wait must be BOUNDED, and every hold must be MEASURED.

THE DEFECT, measured on this tree 2026-10-02.
  (a) `ops/loop/loop_controller.py` called `slots.hold(...)` around the executor
      call with NO `timeout` argument.
  (b) `ops/loop/slots.py` stamps `"ts": time.time()` into the lock payload at
      hold() ENTRY (:220), before the acquire/backoff loop starts (:224).
  (c) `timeout=None` leaves `deadline = None` (:221), so the loop's only raise
      site (:230) is unreachable and the wait never ends.
  (d) `slots.is_stale` ages a lock from exactly that payload `ts` (:105).
Together those four mean the age of a held lock had NO UPPER BOUND by
construction: a run that waited a long time for a contended slot acquired a
lock whose stamp was already old, because `ts` records when the WAIT started,
not when the lock was ACQUIRED. A long-waiting run could therefore hold a lock
that was already past any staleness threshold the moment it got it, and another
repo would reap it out from under a live executor call.

WHY THE FIX IS AT THE CALL SITE. `ops/loop/slots.py` is byte-identical-by-
contract across every sibling repo that vendors it, pinned by sha256 in
tests/test_loop_concurrency.py. The bound and the instrumentation both live in
LW-owned code; slots.py is not touched.

THE OWED CORPUS. LW has owed the channel a hold()-duration corpus. The whole
point of the analysis above is that WAIT and HOLD are different quantities:
conflating them is what let a 5401s figure read as a maximum when it was a
floor over the holds that happened to be short. So the corpus records them
separately, and it records a LEAKED hold in a way a reader cannot silently
drop - pairing acquire/release lines and dropping the unpaired ones is the
sibling defect that produced that floor.

HERMETIC. Every arm here injects its own clock, slot root and corpus path. No
machine state, no absolute Legion paths, no ~/.claude.json, and nothing
Windows-only (CI is ubuntu-latest).
"""
from __future__ import annotations

import ast
import contextlib
import importlib.util
import json
import os
import subprocess
import sys
import textwrap
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
CONTROLLER = ROOT / "ops" / "loop" / "loop_controller.py"

_SEQ = [0]


def _load_controller(tmp: Path):
    """Import loop_controller against a THROWAWAY config rooted in tmp.

    The module does a CTL.mkdir at import time and derives ROOT (and therefore
    the corpus path) from the config, so pointing both at tmp is what keeps
    these arms off the real tree.
    """
    tmp.mkdir(parents=True, exist_ok=True)
    cfgp = tmp / "cfg.json"
    cfgp.write_text(json.dumps({
        "repo_root": str(tmp),
        "control_dir": str(tmp / "control"),
        "cycle_deadline_sec": 5400,
        "max_concurrent_lanes": 3,
        "ceiling_usd": 1.0,
        "max_cycles": 1,
    }), encoding="utf-8")
    _SEQ[0] += 1
    name = f"lw_loop_controller_bounded_{_SEQ[0]}"
    argv = sys.argv
    sys.argv = [str(CONTROLLER), str(cfgp)]
    try:
        spec = importlib.util.spec_from_file_location(name, CONTROLLER)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    finally:
        sys.argv = argv
    return mod


def _hold_call(src: str):
    """The Call node for the slot hold that wraps the executor call."""
    tree = ast.parse(src)
    found = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        f = node.func
        if isinstance(f, ast.Name) and f.id == "held_slot":
            found.append(node)
        elif isinstance(f, ast.Attribute) and f.attr == "hold" and \
                isinstance(f.value, ast.Name) and f.value.id == "slots":
            found.append(node)
    return found


def _lines(path: Path) -> list[dict]:
    return [json.loads(ln) for ln in
            path.read_text(encoding="utf-8").splitlines() if ln.strip()]


def _fake_hold(slot_dir: Path, stamp: float):
    """A stand-in for slots.hold that writes a payload with a CHOSEN stamp."""
    @contextlib.contextmanager
    def fake(max_slots, **kw):
        slot_dir.mkdir(parents=True, exist_ok=True)
        p = slot_dir / "0.lock"
        p.write_text(json.dumps({"pid": os.getpid(), "ts": stamp}),
                     encoding="utf-8")
        try:
            yield p
        finally:
            with contextlib.suppress(OSError):
                p.unlink()
    return fake


def _scripted_clock(values):
    vals = list(values)

    def clock():
        return vals.pop(0) if vals else 0.0
    return clock


# ---- 1. the bound exists, and it is DERIVED -------------------------------

def test_the_call_site_passes_a_timeout_at_all(tmp_path: Path):
    """The whole defect in one assertion: no timeout kwarg, no bound."""
    calls = _hold_call(CONTROLLER.read_text(encoding="utf-8"))
    assert calls, "could not find the executor slot hold in loop_controller.py"
    for c in calls:
        kw = {k.arg for k in c.keywords if k.arg}
        assert "timeout" in kw, (
            "the executor slot hold passes no timeout, so slots.hold leaves "
            "deadline=None and the wait is unbounded by construction")


def test_the_timeout_is_derived_and_not_a_literal(tmp_path: Path):
    """A hard-coded number would be a second magic constant to drift from the
    cycle deadline. The value must come from a call, not a Constant."""
    calls = _hold_call(CONTROLLER.read_text(encoding="utf-8"))
    for c in calls:
        tv = next(k.value for k in c.keywords if k.arg == "timeout")
        assert not isinstance(tv, ast.Constant), (
            "a literal timeout is a magic number that will drift from "
            "cycle_deadline_sec; derive it from config instead")


def test_the_bound_is_one_cycle_deadline(tmp_path: Path):
    """Asserts the DERIVATION over injected configs, never a literal."""
    ctrl = _load_controller(tmp_path)
    assert ctrl.slot_wait_timeout({"cycle_deadline_sec": 1234}) == 1234.0
    assert ctrl.slot_wait_timeout({"cycle_deadline_sec": 60}) == 60.0
    # and an explicit override wins, so a tighter bound is configurable
    assert ctrl.slot_wait_timeout(
        {"cycle_deadline_sec": 5400, "slot_wait_timeout_sec": 90}) == 90.0


def test_the_bound_keeps_a_held_lock_out_of_its_own_reap_window(tmp_path: Path):
    """THE REASON for the number, machine-checked.

    wait <= deadline and hold <= deadline puts a hard ceiling of 2x
    cycle_deadline_sec on a lock's age at release. slots.DEFAULT_STALE_AFTER is
    3x 5400s, so a lock this loop holds can never age into its own reap window
    mid-hold. If that inequality ever stops holding, the bound stops meaning
    what its comment says.
    """
    ctrl = _load_controller(tmp_path)
    # ctrl.slots, NOT a second import of slots.py: a freshly loaded copy is a
    # DIFFERENT module object with a DIFFERENT SlotTimeout class, so an arm
    # written against it would assert about a class production never raises.
    slots = ctrl.slots
    real = json.loads((ROOT / "ops" / "loop" / "config.json").read_text(encoding="utf-8"))
    deadline = float(real["cycle_deadline_sec"])
    bound = ctrl.slot_wait_timeout(real)
    assert bound + deadline < slots.DEFAULT_STALE_AFTER, (
        f"wait bound {bound}s + hold {deadline}s is not under the "
        f"{slots.DEFAULT_STALE_AFTER}s stale window")


def test_the_wrapper_refuses_an_unbounded_hold(tmp_path: Path):
    """Structural: the unbounded wait cannot be reintroduced THROUGH the
    wrapper, whatever a future caller passes."""
    ctrl = _load_controller(tmp_path)
    for bad in (None, 0, -1):
        with pytest.raises(ValueError):
            with ctrl.held_slot(1, timeout=bad, root=tmp_path / "slots",
                                corpus=tmp_path / "c.jsonl"):
                pass


# ---- 2. a SlotTimeout is raised, and HANDLED ------------------------------

def test_a_full_bucket_raises_slot_timeout_rather_than_waiting(tmp_path: Path):
    """Runs the REAL slots.hold against a tmp bucket, so this proves the bound
    binds end to end and not just that a kwarg is spelled."""
    ctrl = _load_controller(tmp_path)
    slots = ctrl.slots
    root = tmp_path / "slots"
    root.mkdir()
    # one slot, held by a pid that is unambiguously alive and NOT stale
    (root / "0.lock").write_text(json.dumps(
        {"pid": os.getpid(), "repo": "other", "ts": time.time()}), encoding="utf-8")
    t0 = time.monotonic()
    with pytest.raises(slots.SlotTimeout):
        with ctrl.held_slot(1, timeout=0.25, backoff=0.01, jitter=0.0,
                            root=root, corpus=tmp_path / "c.jsonl"):
            raise AssertionError("the body must not run")
    assert time.monotonic() - t0 < 30, "the wait did not respect the bound"


def test_a_slot_timeout_is_handled_at_the_call_site_and_the_cycle_continues():
    """A SlotTimeout must not propagate out of the cycle.

    AST, not prose: the hold has to sit inside a try whose handler names
    slots.SlotTimeout, and that handler must CONTINUE rather than re-raise or
    exit. A crash loop here would be worse than the unbounded wait being fixed.
    """
    tree = ast.parse(CONTROLLER.read_text(encoding="utf-8"))
    guarded = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Try):
            continue
        if not _hold_call(ast.unparse(ast.Module(body=node.body, type_ignores=[]))):
            continue
        for h in node.handlers:
            names = {n.attr if isinstance(n, ast.Attribute) else getattr(n, "id", "")
                     for n in ast.walk(h.type)} if h.type else set()
            if "SlotTimeout" not in names:
                continue
            body = ast.unparse(ast.Module(body=h.body, type_ignores=[]))
            assert any(isinstance(n, ast.Continue) for n in ast.walk(h)), (
                "the SlotTimeout handler must skip the cycle and go on to the "
                f"next one, not fall through:\n{body}")
            assert not any(isinstance(n, ast.Raise) for n in ast.walk(h)), (
                "re-raising turns slot contention into a dead run")
            guarded.append(h)
    assert guarded, (
        "the executor slot hold is not wrapped in an except slots.SlotTimeout "
        "handler, so a bounded wait merely converts an unbounded hang into a "
        "crash")


def test_the_handled_timeout_still_reaches_the_director():
    """A failed cycle has to tell the next director call that it failed - the
    doctrine pinned by tests/test_failed_cycle_reaches_the_director.py. A
    silently skipped cycle is a cycle the director cannot see."""
    src = CONTROLLER.read_text(encoding="utf-8")
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if not isinstance(node, ast.Try):
            continue
        for h in node.handlers:
            names = {n.attr if isinstance(n, ast.Attribute) else getattr(n, "id", "")
                     for n in ast.walk(h.type)} if h.type else set()
            if "SlotTimeout" not in names:
                continue
            body = ast.unparse(ast.Module(body=h.body, type_ignores=[]))
            assert "failure_raw" in body and "last_done" in body, (
                "the slot-timeout handler must hand the failure forward as "
                f"last_done so the director sees it:\n{body}")
            return
    raise AssertionError("no SlotTimeout handler found")


# ---- 3. the corpus: wait and hold recorded SEPARATELY ---------------------

def test_wait_and_hold_are_recorded_separately(tmp_path: Path):
    """Deterministic by injection - no sleeping, no racing the clock.

    stamp=100 (what slots wrote at hold() ENTRY), acquire=107, release=130.
    So wait=7, hold=23, age_at_release=30. The arm fails if any two of those
    are conflated.
    """
    ctrl = _load_controller(tmp_path)
    corpus = tmp_path / "corpus.jsonl"
    with ctrl.held_slot(1, run_id="r1", cycle=4, timeout=600,
                        corpus=corpus, hold=_fake_hold(tmp_path / "s", 100.0),
                        clock=_scripted_clock([99.0, 107.0, 130.0])):
        pass
    recs = _lines(corpus)
    assert [r["event"] for r in recs] == ["acquired", "released"]
    acq, rel = recs
    assert acq["wait_sec"] == 7.0, "wait is stamp-to-acquire"
    assert acq["hold_sec"] is None, "a hold duration is not known at acquire"
    assert rel["hold_sec"] == 23.0, "hold is acquire-to-release"
    assert rel["wait_sec"] == 7.0, "the wait must still be readable, separately"
    assert rel["age_at_release_sec"] == 30.0, (
        "age at release is release minus the PAYLOAD stamp - the quantity the "
        "unbounded wait was corrupting")
    assert rel["hold_sec"] != rel["age_at_release_sec"], (
        "conflating hold with age is exactly the error that made a floor read "
        "as a maximum")


def test_the_corpus_is_jsonl_and_append_only(tmp_path: Path):
    ctrl = _load_controller(tmp_path)
    corpus = tmp_path / "corpus.jsonl"
    for cycle in (1, 2):
        with ctrl.held_slot(1, run_id="r", cycle=cycle, timeout=600,
                            corpus=corpus, hold=_fake_hold(tmp_path / "s", 10.0),
                            clock=_scripted_clock([10.0, 11.0, 12.0])):
            pass
    raw = corpus.read_text(encoding="utf-8")
    assert raw.count("\n") == 4, "two records per acquisition, one per line"
    assert len(_lines(corpus)) == 4, "every line must parse on its own"
    assert [r["cycle"] for r in _lines(corpus)] == [1, 1, 2, 2], (
        "a later cycle must not overwrite an earlier one")


def test_the_corpus_lands_under_ops_runtime_by_default(tmp_path: Path):
    """Durable and gitignored: ops/runtime/ is ignored wholesale."""
    ctrl = _load_controller(tmp_path)
    assert ctrl.SLOT_CORPUS.parent == Path(tmp_path) / "ops" / "runtime", (
        f"corpus must sit under ops/runtime, got {ctrl.SLOT_CORPUS}")
    assert ctrl.SLOT_CORPUS.suffix == ".jsonl"


def test_a_real_slots_hold_is_measured_too(tmp_path: Path):
    """Integration against the REAL slots.hold, with no timing assertions - the
    injected arms above own the arithmetic, this one owns the wiring."""
    ctrl = _load_controller(tmp_path)
    corpus = tmp_path / "corpus.jsonl"
    with ctrl.held_slot(2, run_id="real", cycle=9, timeout=30,
                        root=tmp_path / "slots", corpus=corpus) as slot:
        assert slot.exists(), "the real slots.hold yields a live lockfile"
    recs = _lines(corpus)
    assert [r["event"] for r in recs] == ["acquired", "released"]
    assert recs[0]["stamp_source"] == "payload", (
        "the wait must be measured from the stamp slots itself wrote, not from "
        "our own guess at when we started waiting")
    assert recs[1]["hold_sec"] >= 0.0


# ---- 4. a LEAK is distinguishable from a short hold ----------------------

def test_a_leaked_hold_is_not_silently_dropped(tmp_path: Path):
    """The sibling defect, reproduced and excluded.

    A corpus with one completed hold and one leaked hold is exactly what a
    killed holder leaves on disk. A reader that PAIRS acquire/release lines and
    drops the unpaired ones sees 1 hold and reports a maximum that is really a
    floor over the short ones. read_slot_corpus must see 2.
    """
    ctrl = _load_controller(tmp_path)
    corpus = tmp_path / "corpus.jsonl"
    ctrl.corpus_append({"event": "acquired", "state": "open", "hold_id": "A",
                        "cycle": 1, "run_id": "r", "wait_sec": 1.0,
                        "hold_sec": None, "ts_acquire": 100.0}, path=corpus)
    ctrl.corpus_append({"event": "released", "state": "closed", "hold_id": "A",
                        "cycle": 1, "run_id": "r", "wait_sec": 1.0,
                        "hold_sec": 2.0, "age_at_release_sec": 3.0,
                        "ts_acquire": 100.0, "ts_release": 102.0}, path=corpus)
    ctrl.corpus_append({"event": "acquired", "state": "open", "hold_id": "B",
                        "cycle": 2, "run_id": "r", "wait_sec": 5.0,
                        "hold_sec": None, "ts_acquire": 200.0}, path=corpus)

    naive = len([r for r in _lines(corpus) if r["event"] == "released"])
    got = ctrl.read_slot_corpus(corpus, now=260.0)
    assert naive == 1, "the naive pairing reader really does drop the leak"
    assert len(got) == 2, (
        f"read_slot_corpus dropped a leaked hold (saw {len(got)}), which is the "
        f"defect that turned a sibling's corpus into a floor")
    by_id = {r["hold_id"]: r for r in got}
    assert by_id["A"]["leaked"] is False
    assert by_id["A"]["hold_sec"] == 2.0
    assert by_id["B"]["leaked"] is True, "an acquire with no release is a LEAK"
    assert by_id["B"]["hold_sec"] is None, (
        "a leaked hold has no known duration - reporting one would invent a "
        "measurement, and reporting zero would shrink the maximum")
    assert by_id["B"]["hold_floor_sec"] == 60.0, (
        "a leak is a CENSORED observation and must carry its lower bound")
    assert by_id["B"]["wait_sec"] == 5.0, (
        "the wait IS known for a leak - it was recorded at acquire")


def test_a_killed_holder_really_leaves_the_acquired_record(tmp_path: Path):
    """End to end, with a genuinely dead process rather than a crafted file.

    os._exit inside the block skips every finally, which is what a taskkill or
    an OOM does. The acquired record must already be on disk by then or a leak
    leaves no trace at all.
    """
    script = tmp_path / "kill_mid_hold.py"
    script.write_text(textwrap.dedent(f"""
        import importlib.util, json, os, sys
        tmp = {str(tmp_path)!r}
        cfg = os.path.join(tmp, "subcfg.json")
        with open(cfg, "w", encoding="utf-8") as fh:
            json.dump({{"repo_root": tmp,
                       "control_dir": os.path.join(tmp, "subctl"),
                       "cycle_deadline_sec": 5400, "ceiling_usd": 1.0,
                       "max_cycles": 1}}, fh)
        sys.argv = [{str(CONTROLLER)!r}, cfg]
        spec = importlib.util.spec_from_file_location("c", {str(CONTROLLER)!r})
        mod = importlib.util.module_from_spec(spec)
        sys.modules["c"] = mod
        spec.loader.exec_module(mod)
        with mod.held_slot(2, run_id="killed", cycle=3, timeout=30,
                           root=os.path.join(tmp, "subslots"),
                           corpus=os.path.join(tmp, "sub.jsonl")):
            os._exit(9)
    """), encoding="utf-8")
    r = subprocess.run([sys.executable, str(script)], capture_output=True,
                       text=True, timeout=180)
    assert r.returncode == 9, f"the child did not die inside the hold: {r.stderr[-2000:]}"
    ctrl = _load_controller(tmp_path / "reader")
    got = ctrl.read_slot_corpus(tmp_path / "sub.jsonl")
    assert len(got) == 1, "the acquisition left no record at all"
    assert got[0]["leaked"] is True, "a killed holder must read as leaked"
    assert got[0]["hold_sec"] is None


def test_the_reader_tolerates_a_torn_or_foreign_line(tmp_path: Path):
    ctrl = _load_controller(tmp_path)
    corpus = tmp_path / "corpus.jsonl"
    corpus.write_text('{"event": "acquired", "hold_id": "A", "wait_sec": 1.0, '
                      '"hold_sec": null, "ts_acquire": 1.0}\n'
                      '{"event": "acq\n'
                      'not json at all\n', encoding="utf-8")
    got = ctrl.read_slot_corpus(corpus, now=2.0)
    assert len(got) == 1 and got[0]["leaked"] is True


# ---- 5. instrumentation must never break the run ------------------------

def test_a_corpus_io_failure_does_not_break_the_run(tmp_path: Path):
    """Injected failure: the corpus path's parent is an existing FILE, so the
    mkdir inside corpus_append cannot succeed. The hold must still complete."""
    ctrl = _load_controller(tmp_path)
    blocker = tmp_path / "blocker"
    blocker.write_text("i am a file, not a directory", encoding="utf-8")
    bad = blocker / "nested" / "corpus.jsonl"
    seen = []
    ran = []
    with ctrl.held_slot(1, run_id="io", cycle=1, timeout=600, corpus=bad,
                        log=seen.append, hold=_fake_hold(tmp_path / "s", 1.0),
                        clock=_scripted_clock([1.0, 2.0, 3.0])):
        ran.append(True)
    assert ran == [True], "an unwritable corpus must not skip the executor call"
    assert any("corpus" in m for m in seen), (
        "a failed corpus write must at least be logged, not swallowed silently")
    assert ctrl.corpus_append({"x": 1}, path=bad) is False


def test_an_unserialisable_record_does_not_break_the_run(tmp_path: Path):
    """The other half of the same promise: a bad RECORD, not a bad path."""
    ctrl = _load_controller(tmp_path)
    corpus = tmp_path / "corpus.jsonl"
    assert ctrl.corpus_append({"bad": object()}, path=corpus) is False
    assert not corpus.exists() or _lines(corpus) == []


def test_a_body_exception_still_records_the_release(tmp_path: Path):
    """A cycle that throws must not look like a leak - the finally has to run."""
    ctrl = _load_controller(tmp_path)
    corpus = tmp_path / "corpus.jsonl"
    try:
        with ctrl.held_slot(1, run_id="boom", cycle=1, timeout=600,
                            corpus=corpus, hold=_fake_hold(tmp_path / "s", 1.0),
                            clock=_scripted_clock([1.0, 2.0, 5.0])):
            raise RuntimeError("executor blew up")
    except RuntimeError:
        pass
    got = ctrl.read_slot_corpus(corpus)
    assert len(got) == 1 and got[0]["leaked"] is False, (
        "an exception in the body is not a leak; the slot WAS released")
    assert got[0]["hold_sec"] == 3.0


# ---- 6. guard the guard: prove these arms are ARMED --------------------

def test_the_corpus_writer_is_actually_exercised(tmp_path: Path):
    """The vacuity class measured live in LW today: an arm that asserts nothing
    because the thing under test never ran. Counts the writes."""
    ctrl = _load_controller(tmp_path)
    corpus = tmp_path / "corpus.jsonl"
    calls = []
    real = ctrl.corpus_append

    def spy(record, path=None, log=None):
        calls.append(record.get("event"))
        return real(record, path=path, log=log)

    ctrl.corpus_append = spy
    try:
        with ctrl.held_slot(1, run_id="spy", cycle=1, timeout=600,
                            corpus=corpus, hold=_fake_hold(tmp_path / "s", 1.0),
                            clock=_scripted_clock([1.0, 2.0, 3.0])):
            pass
    finally:
        ctrl.corpus_append = real
    assert calls == ["acquired", "released"], (
        f"the corpus writer was not exercised by the wrapper: {calls}")
    assert corpus.is_file() and corpus.stat().st_size > 0, (
        "the writer was called but nothing reached disk")


def test_this_file_skips_nothing():
    """A skipped arm asserts nothing, and a whole file of them reads green.

    No arm here is platform-bound (nothing Windows-only is called anywhere in
    this file, which is why there is no os.name guard to misplace), so a skip
    marker would be a defect rather than a degradation. CI is ubuntu-latest, so
    a Windows-only arm would go silently unexercised exactly where it matters.
    """
    src = Path(__file__).read_text(encoding="utf-8")
    # Spelled in halves on purpose: a literal here would match ITSELF and the
    # arm would read green while asserting nothing about the other arms.
    for marker in ("pytest." + "skip(", "mark." + "skip", "import" + "orskip"):
        assert marker not in src, f"{marker} would make an arm vacuous"
