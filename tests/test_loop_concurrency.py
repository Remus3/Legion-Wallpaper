"""F1 P3 concurrency governor: slots, named mutexes, single-controller lock.

These are the tests that have to be right BEFORE any live concurrent LW+RC run,
because the failure they guard against is not a crash - it is two loops quietly
double-booking a shared resource and blaming the result on something else.

slots.py and winmutex.py are byte-identical across both repos by contract, so
nothing here may assume LW paths; every test injects its own root.
"""
from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import json
import os
import re
import sys
import threading
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


def _load(name: str):
    spec = importlib.util.spec_from_file_location(
        f"lw_loop_{name}_under_test", ROOT / "ops" / "loop" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


slots = _load("slots")
winmutex = _load("winmutex")


# ---- the core invariant: never more than max_slots holders -----------------

def test_eight_threads_never_exceed_two_concurrent_holders(tmp_path: Path):
    """THE acceptance invariant. 8 contenders, 2 slots, sampled continuously."""
    live = 0
    peak = 0
    lock = threading.Lock()
    errors: list = []

    def worker(i: int):
        nonlocal live, peak
        try:
            with slots.hold(2, root=tmp_path, run_id=f"r{i}", cycle=i,
                            backoff=0.02, jitter=0.02, timeout=30):
                with lock:
                    live += 1
                    peak = max(peak, live)
                time.sleep(0.05)
                with lock:
                    live -= 1
        except Exception as e:  # noqa: BLE001 - surface, do not swallow
            errors.append(e)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=60)

    assert not errors, errors
    assert peak <= 2, f"slot governor breached: {peak} concurrent holders"
    assert peak == 2, "with 8 contenders both slots should have been used"


def test_all_slots_are_released_after_use(tmp_path: Path):
    with slots.hold(2, root=tmp_path, backoff=0.01, jitter=0.01):
        assert len(list(tmp_path.glob("*.lock"))) == 1
    assert list(tmp_path.glob("*.lock")) == [], "a slot leaked"


def test_slot_is_released_even_when_the_body_raises(tmp_path: Path):
    with pytest.raises(ValueError):
        with slots.hold(1, root=tmp_path, backoff=0.01, jitter=0.01):
            raise ValueError("boom")
    assert list(tmp_path.glob("*.lock")) == [], "an exception leaked a slot"


def test_timeout_raises_rather_than_proceeding_unslotted(tmp_path: Path):
    """A caller that cannot get a slot must fail, never run anyway."""
    with slots.hold(1, root=tmp_path, backoff=0.01, jitter=0.01):
        with pytest.raises(slots.SlotTimeout):
            with slots.hold(1, root=tmp_path, backoff=0.01, jitter=0.01, timeout=0.2):
                pytest.fail("acquired a slot that was already held")


# ---- reaping: a crashed holder must not deadlock the other repo ------------

def test_lock_held_by_a_dead_pid_is_reaped(tmp_path: Path):
    """FAIL-OPEN by design: a stale lock is reclaimed, never respected forever."""
    dead = tmp_path / "0.lock"
    dead.write_text(json.dumps({"pid": 999999999, "repo": "ghost",
                                "run_id": "x", "cycle": 1, "ts": time.time()}),
                    encoding="utf-8")
    assert slots.is_stale(dead, slots.DEFAULT_STALE_AFTER) is True
    with slots.hold(1, root=tmp_path, backoff=0.01, jitter=0.01, timeout=5) as s:
        assert s.name == "0.lock", "the dead holder's slot should be reused"


def test_lock_older_than_stale_after_is_reaped(tmp_path: Path):
    old = tmp_path / "0.lock"
    old.write_text(json.dumps({"pid": os.getpid(), "ts": time.time() - 10_000}),
                   encoding="utf-8")
    assert slots.is_stale(old, stale_after=100.0) is True


def test_live_holder_is_not_reaped(tmp_path: Path):
    """The reaper must not steal a slot from a running process."""
    mine = tmp_path / "0.lock"
    mine.write_text(json.dumps({"pid": os.getpid(), "ts": time.time()}),
                    encoding="utf-8")
    assert slots.is_stale(mine, slots.DEFAULT_STALE_AFTER) is False
    assert slots.reap(tmp_path, 1, slots.DEFAULT_STALE_AFTER) == 0


def test_corrupt_lock_cannot_wedge_the_bucket_forever(tmp_path: Path):
    bad = tmp_path / "0.lock"
    bad.write_text("{ not json", encoding="utf-8")
    os.utime(bad, (time.time() - 10_000, time.time() - 10_000))
    assert slots.is_stale(bad, stale_after=100.0) is True


def test_pid_alive_is_true_for_this_process():
    assert slots.pid_alive(os.getpid()) is True


def test_pid_alive_is_false_for_an_impossible_pid():
    assert slots.pid_alive(999999999) is False
    assert slots.pid_alive(0) is False


# ---- the payload the other repo reads --------------------------------------

def test_lock_payload_identifies_the_holder(tmp_path: Path):
    """Cross-repo debugging depends on this: which repo, which run, which cycle."""
    with slots.hold(1, root=tmp_path, repo="LW", run_id="abc123", cycle=7,
                    backoff=0.01, jitter=0.01) as s:
        rec = json.loads(s.read_text(encoding="utf-8"))
    assert rec["repo"] == "LW"
    assert rec["run_id"] == "abc123"
    assert rec["cycle"] == 7
    assert rec["pid"] == os.getpid()


# ---- one controller per repo ------------------------------------------------

def test_second_controller_in_the_same_repo_exits_nonzero(tmp_path: Path):
    """Concurrency ACROSS repos is the goal; within one repo it is corruption.

    The control_dir handshake files are not namespaced, so two controllers in
    one repo would consume each other's gemini.ready and claude.done.
    """
    import subprocess
    ctl = tmp_path / "control"
    ctl.mkdir()
    cfg = json.loads((ROOT / "ops" / "loop" / "config.dry.json").read_text(encoding="utf-8"))
    cfg.update({"control_dir": str(ctl), "max_cycles": 1, "cycle_deadline_sec": 5,
                "poll_sec": 1, "fixed_directive": "noop", "session_jsonl": ""})
    cfgp = tmp_path / "cfg.json"
    cfgp.write_text(json.dumps(cfg), encoding="utf-8")

    # A lock held by THIS process: a live pid that is not the controller's.
    (ctl / "RUNNING.lock").write_text(
        json.dumps({"pid": os.getpid(), "run_id": "held", "ts": time.time()}),
        encoding="utf-8")

    r = subprocess.run([sys.executable, str(ROOT / "ops" / "loop" / "loop_controller.py"),
                        str(cfgp)], capture_output=True, text=True, timeout=120)
    assert r.returncode != 0, "a second controller must refuse to start"
    assert "already running" in (r.stderr + r.stdout)


def test_controller_reclaims_a_lock_whose_pid_was_recycled(tmp_path: Path):
    """A live pid does not prove the ORIGINAL holder is still alive.

    Measured on the real tree 2026-08-01: control/RUNNING.lock named pid 8532
    from a run that ended 2026-07-27, and pid 8532 had since been reissued to a
    conhost.exe started that morning. Bare pid liveness said "alive", so a fresh
    launch refused to start and the loop was wedged for five days behind a lock
    whose owner had exited cleanly (STOP was present the whole time).

    The corroboration is lock AGE: the holder claims a repo for at most a cycle
    deadline, so a lock far older than the stale window cannot belong to a live
    run no matter what the pid table says.
    """
    import subprocess
    ctl = tmp_path / "control"
    ctl.mkdir()
    cfg = json.loads((ROOT / "ops" / "loop" / "config.dry.json").read_text(encoding="utf-8"))
    cfg.update({"control_dir": str(ctl), "max_cycles": 1, "cycle_deadline_sec": 3,
                "poll_sec": 1, "fixed_directive": "noop", "session_jsonl": ""})
    cfgp = tmp_path / "cfg.json"
    cfgp.write_text(json.dumps(cfg), encoding="utf-8")

    # os.getpid() is unambiguously alive - the point is that aliveness alone
    # must not be enough when the lock predates any plausible run.
    stale = _load("slots").DEFAULT_STALE_AFTER
    (ctl / "RUNNING.lock").write_text(
        json.dumps({"pid": os.getpid(), "run_id": "recycled",
                    "ts": time.time() - (stale * 4)}),
        encoding="utf-8")

    proc = subprocess.Popen(
        [sys.executable, str(ROOT / "ops" / "loop" / "loop_controller.py"), str(cfgp)],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    try:
        claimed = False
        for _ in range(150):
            if (ctl / "run_id.txt").is_file():
                claimed = True
                break
            if proc.poll() is not None:
                break
            time.sleep(0.1)
        assert claimed, "an expired lock must not wedge the repo behind a recycled pid"
        rec = json.loads((ctl / "RUNNING.lock").read_text(encoding="utf-8"))
        assert rec["pid"] == proc.pid
    finally:
        proc.kill()
        proc.wait(timeout=30)


def test_controller_still_refuses_a_live_holder_inside_the_stale_window(tmp_path: Path):
    """The sibling of the case above: age must not become a way to steal a repo.

    A genuinely running controller mid-cycle has a fresh lock, and the age
    corroboration must not weaken that refusal.
    """
    import subprocess
    ctl = tmp_path / "control"
    ctl.mkdir()
    cfg = json.loads((ROOT / "ops" / "loop" / "config.dry.json").read_text(encoding="utf-8"))
    cfg.update({"control_dir": str(ctl), "max_cycles": 1, "cycle_deadline_sec": 5,
                "poll_sec": 1, "fixed_directive": "noop", "session_jsonl": ""})
    cfgp = tmp_path / "cfg.json"
    cfgp.write_text(json.dumps(cfg), encoding="utf-8")

    stale = _load("slots").DEFAULT_STALE_AFTER
    (ctl / "RUNNING.lock").write_text(
        json.dumps({"pid": os.getpid(), "run_id": "held",
                    "ts": time.time() - (stale * 0.5)}),
        encoding="utf-8")

    r = subprocess.run([sys.executable, str(ROOT / "ops" / "loop" / "loop_controller.py"),
                        str(cfgp)], capture_output=True, text=True, timeout=120)
    assert r.returncode != 0, "a live holder inside the window still owns the repo"
    assert "already running" in (r.stderr + r.stdout)


def test_controller_reclaims_a_lock_held_by_a_dead_pid(tmp_path: Path):
    """Fail-open: a crashed controller must not lock the repo out forever."""
    import subprocess
    ctl = tmp_path / "control"
    ctl.mkdir()
    cfg = json.loads((ROOT / "ops" / "loop" / "config.dry.json").read_text(encoding="utf-8"))
    cfg.update({"control_dir": str(ctl), "max_cycles": 1, "cycle_deadline_sec": 3,
                "poll_sec": 1, "fixed_directive": "noop", "session_jsonl": ""})
    cfgp = tmp_path / "cfg.json"
    cfgp.write_text(json.dumps(cfg), encoding="utf-8")
    (ctl / "RUNNING.lock").write_text(
        json.dumps({"pid": 999999999, "run_id": "ghost", "ts": time.time()}),
        encoding="utf-8")

    # Only the CLAIM is under test, so poll for it and kill - letting the cycle
    # run to completion would add two minutes of AHK-handshake timeout per run.
    proc = subprocess.Popen(
        [sys.executable, str(ROOT / "ops" / "loop" / "loop_controller.py"), str(cfgp)],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    try:
        claimed = False
        for _ in range(150):
            if (ctl / "run_id.txt").is_file():
                claimed = True
                break
            if proc.poll() is not None:
                break
            time.sleep(0.1)
        assert claimed, "a dead holder must not block a new run from claiming the repo"
        rec = json.loads((ctl / "RUNNING.lock").read_text(encoding="utf-8"))
        assert rec["pid"] == proc.pid, "the live controller should own the lock now"
    finally:
        proc.kill()
        proc.wait(timeout=30)


# ---- named mutexes ---------------------------------------------------------

@pytest.mark.skipif(sys.platform != "win32", reason="windows mutex semantics")
def test_mutex_is_reentrant_for_the_same_thread():
    """Windows mutexes are owned per-thread; nesting must not self-deadlock."""
    with winmutex.hold("Global\\LWRC_TEST_NEST", timeout=5):
        with winmutex.hold("Global\\LWRC_TEST_NEST", timeout=5):
            pass


# winmutex.hold is a DELIBERATE no-op off Windows (winmutex.py:55-58 - "the
# loops are Windows-only"), so these two assert a primitive that does not exist
# on Linux: serialization there is vacuous, not broken. Same guard the timeout
# test already carried. The string-contract tests below stay unskipped - they
# are platform-independent and must keep running everywhere.
@pytest.mark.skipif(sys.platform != "win32", reason="windows mutex semantics")
def test_mutex_serializes_two_threads():
    live = 0
    peak = 0
    lock = threading.Lock()

    def worker():
        nonlocal live, peak
        with winmutex.hold("Global\\LWRC_TEST_SERIAL", timeout=30):
            with lock:
                live += 1
                peak = max(peak, live)
            time.sleep(0.05)
            with lock:
                live -= 1

    ts = [threading.Thread(target=worker) for _ in range(4)]
    for t in ts:
        t.start()
    for t in ts:
        t.join(timeout=60)
    assert peak == 1, f"mutex allowed {peak} concurrent holders"


# ---- f1-phase6 item 5a: pinned parity constants -----------------------------
#
# slots.py and winmutex.py are BYTE-IDENTICAL between this repo and Riot
# Commander by contract. RC's mirror test compares its copy against the LW tree
# directly, which is the stronger check - but it SKIPS when the sibling tree is
# absent, so on a CI runner (one repo checked out, no sibling) parity is
# enforced by NOBODY. These pins close that hole: each repo's CI can prove
# parity alone, against a value both sides agreed to.
#
# RE-PINNING IS A JOINT ACT. Never regenerate these from whatever the file
# happens to be locally - that turns the guard into a rubber stamp and would
# launder a unilateral drift into "agreed". Change the shared file on one side,
# hand the other side the exact bytes, re-hash BOTH trees, confirm they match,
# and only then write the new digest here and in RC's copy in the same round.
SHARED_SHA256 = {
    # unchanged since the 2026-07-26 sync
    # Re-pinned 2026-08-01 for the three-repo docstring (two repos -> three, and
    # "either repo" -> "ANY of them"). Docstring only: no code, no protocol, no
    # behaviour. Bytes authored by RC, applied here VERBATIM and re-hashed from
    # this disk rather than trusted from the note.
    # Re-pinned 2026-09-06: Red Moon is archived read-only and its working copy
    # deleted, so Resin Compute takes the vacated third slot. Docstring only,
    # same shape as the 2026-08-01 re-pin: "Red Moon" -> "Resin Compute", no
    # code, no protocol, no behaviour, and MAX_CONCURRENT_SLOTS stays 3 - the
    # bucket models one Anthropic account, and the participant count did not
    # change. Bytes authored HERE and hashed from this disk. Provisional until
    # RC copies them verbatim and RSC lands its vendored copy last; until then
    # drift_guard reports the divergence, which is the expected transient state
    # because the flip cannot be atomic. RM's copy is frozen at the previous
    # digest forever - do not chase it.
    # Previous: 5297f2d041030398a9ba240aad527b2b01a86d6e7f57a196719af8f0a91cb0a6
    # Re-pinned 2026-09-07: the hold() release-path leak (found by RSC, confirmed
    # by RC on two live ghost lanes). CODE, not docstring: release() retries a
    # bounded number of times and NEUTRALISES a lock it cannot delete, and hold()
    # no longer logs "released" when the unlink failed. Authored HERE, hashed from
    # this disk, handed to RC and RSC verbatim. PROVISIONAL until both copy it;
    # drift_guard reporting divergence until then is the expected transient.
    # Previous: 1c4f8af43ff349709c11bf3fe622e922b24cb720771c49a522b13a4d5e58c492
    # Previous: 629c3d511d2500f92d25fbe102a7a8c73644c027291f46b8796565a1e839f865
    # Re-pinned 2026-09-07: the opening paragraph no longer NAMES two sibling
    # repos. Docstring only - no code, no protocol, no behaviour, bucket still 3.
    # The old text named "Legion Wallpaper, Riot Commander and Resin Compute" one
    # sentence before forbidding exactly that ("Nothing here may reference ANY of
    # them"), which RC spotted when it took its tree public. Wording proposed by
    # RC, bytes AUTHORED BY RSC, copied here byte-level (shutil.copyfile - a
    # text-mode write turns LF into CRLF on Windows and this pin is on bytes) and
    # re-hashed from THIS disk: 9627 bytes, 0 CRLF, 0 non-ASCII. LW copied LAST -
    # RC and RSC were both measured already carrying these bytes before the copy,
    # so this round closes rather than opens the red window.
    # NOT claimed: that this now matches winmutex.py word for word. RSC measured
    # that it does not (three differences, one of them because the MECHANISM
    # differs), and shipped RC's wording unchanged anyway rather than deviate on
    # one side's private judgement.
    "slots.py": "71fa2a683f2eaa04dd61feb2bebc646b5f9086e692c5acc05a9239de49d07d1b",
    # Re-pinned 2026-09-07 (ADR-012): the two mutex NAMES are rotated to opaque
    # strings and the header prose that described the vendor and a failover
    # defect is scrubbed. This one is NOT docstring-only - the name VALUES move,
    # which is the one change in this file that can silently break mutual
    # exclusion, so it was made with every loop STOPPED (verified: zero
    # loop_controller processes, empty slots bucket) and it must be pinned in
    # every sibling BEFORE any loop starts. Bytes authored HERE, hashed from
    # this disk, handed to RC and RSC verbatim. PROVISIONAL until both copy
    # them; drift_guard reporting divergence until then is the expected
    # transient, exactly as in the 2026-09-06 re-pin.
    # ROUND B landed 2026-09-21: the comment on line 118 named a carrier CODE ("by
    # RC"), which slots.py:7 forbids outright ("Nothing here may reference ANY of
    # them"). Six bytes removed, "by RC ", keeping the provenance that is
    # load-bearing - caught ON REVIEW, and the DATE, which dates the defect to the
    # original sync. ast.dump of both parses is IDENTICAL at 9,795 chars, so no
    # behaviour moved; two-process mutual exclusion was proven in both directions
    # before the bytes were copied. Authored here, confirmed from their own disks by
    # RC and RSC. SS had not answered; the operator directed the landing rather than
    # waiting, so SS may still be carrying the old bytes - a divergence report from
    # SS is EXPECTED and is not a fault on either side.
    # previous 0b112a4f6bfa88cf5f537f8869225c1821ebfe97428b1e899979797ddd71a61e
    # previous f1b4b011112685efb88616c52752657cf896fbb0993b2d2d264e7b3edde8b4f4
    "winmutex.py": "df0a7a40c28818130dfde25144c971c06060b4645e5eb5f679fbdaf55e2e08d7",
}


@pytest.mark.parametrize("name", sorted(SHARED_SHA256))
def test_shared_module_matches_the_pinned_cross_repo_digest(name: str):
    """A drift here is not a merge conflict anyone notices - it is a silent
    concurrency bug where both loops believe they hold the only slot."""
    digest = hashlib.sha256((ROOT / "ops" / "loop" / name).read_bytes()).hexdigest()
    assert digest == SHARED_SHA256[name], (
        f"{name} no longer matches the digest agreed with Riot Commander. "
        f"If this change is intended, re-sync BOTH trees and re-pin on BOTH "
        f"sides in the same round - do not just update this constant.")


# ---- what a DIGEST cannot pin, because the digest moves legitimately -------
#
# Offered by SS (Substrate) on 2026-09-20 when it joined the bucket as a fourth
# carrier at the unchanged width of 3. Adopted here because both arms cover a
# hole LW already fell into, and a digest pin is blind to both by construction:
# on a re-pin round the digest CHANGES legitimately, in the same commit, so it
# certifies nothing about WHAT changed.
#
#   * CRLF / non-ASCII: this file is copied between trees with
#     shutil.copyfile precisely because a text-mode write turns LF into CRLF on
#     Windows. When that happens the digest arm reports "no longer matches the
#     digest agreed with Riot Commander" - true, useless, and it sends the
#     reader hunting a protocol change that did not happen. This arm names the
#     real cause.
#   * NAMES A CARRIER: the 2026-09-07 re-pin exists because the opening
#     paragraph named three sibling repos one sentence before forbidding
#     exactly that, and it was caught BY EYE when a tree went public. Eye is
#     not a guard. This is that guard.
CARRIER_NAMES = ("Legion Wallpaper", "LegionWallpaper", "Riot Commander",
                 "RiotCommander", "Resin Compute", "ResinCompute",
                 "Clockspeed", "Lanternlight", "Substrate")


# ---- the detectors, refactored into seams a FIXTURE can be pointed at -------
#
# Each of the three arms below used to read ROOT/ops/loop directly, which made
# every one of them vacuous: a pure negative assertion over bytes the arm
# fetches itself cannot tell "scanned real clean bytes" from "scanned nothing".
# Measured on this disk 2026-09-20: forcing the scanned text empty left all
# three GREEN, and so did emptying CARRIER_CODES or CARRIER_NAMES.
#
# The `root` argument is the whole point. Production passes the real directory;
# the non-vacuity arms further down write their OWN fixture and point the same
# detector at that, which is the only way to prove the detector still fires on
# a day when the real files legitimately contain ZERO violations - which is
# exactly today's state, post round B.
#
# NOT claimed: that these seams change what production checks. They do not. The
# scan logic is the same logic, lifted out of three function bodies unmodified.

LOOP = ROOT / "ops" / "loop"


def _scan_carrier_codes(root: Path, names=None, codes=None) -> list:
    """[(file, code)] for every code present as a WHOLE WORD, case-SENSITIVE."""
    names = sorted(SHARED_SHA256 if names is None else names)
    codes = CARRIER_CODES if codes is None else codes
    found = []
    for name in names:
        text = (root / name).read_text(encoding="utf-8")
        for code in codes:
            if re.search(r"\b" + code + r"\b", text):
                found.append((name, code))
    return sorted(found)


def _scan_carrier_names(root: Path, names=None, carriers=None) -> list:
    """[(file, [carrier, ...])] by case-INSENSITIVE SUBSTRING, files with hits only."""
    names = sorted(SHARED_SHA256 if names is None else names)
    carriers = CARRIER_NAMES if carriers is None else carriers
    out = []
    for name in names:
        low = (root / name).read_text(encoding="utf-8").lower()
        hits = [n for n in carriers if n.lower() in low]
        if hits:
            out.append((name, hits))
    return out


def _scan_byte_hygiene(root: Path, names=None) -> tuple:
    """(cr, high): [(file, cr count)] and [(file, [byte, ...])], hits only."""
    names = sorted(SHARED_SHA256 if names is None else names)
    cr, high = [], []
    for name in names:
        raw = (root / name).read_bytes()
        if 13 in raw:
            cr.append((name, raw.count(13)))
        bad = sorted({b for b in raw if b > 127})
        if bad:
            high.append((name, bad))
    return cr, high


@pytest.mark.parametrize("name", sorted(SHARED_SHA256))
def test_shared_module_is_lf_only_and_ascii(name: str):
    cr, high = _scan_byte_hygiene(LOOP, names=(name,))
    assert not cr, (
        f"{name} carries a CR byte: it was copied in TEXT mode, not with "
        f"shutil.copyfile. The digest arm will fail too and will blame the "
        f"protocol - the cause is the copy. Matched on ANY CR, not the "
        f"CRLF pair: RSC 1520 measured that a pair-only arm is blind to a "
        f"lone CR, and read_text would strip both under universal newlines.")
    bad = [b for _, bs in high for b in bs]
    assert not bad, f"{name} carries non-ASCII bytes {bad} - repo-wide hard rule"


@pytest.mark.parametrize("name", sorted(SHARED_SHA256))
def test_shared_module_names_no_carrier(name: str):
    """A digest cannot catch a name re-entering during a re-pin, because the
    digest is expected to move in that same commit."""
    found = [n for _, hits in _scan_carrier_names(LOOP, names=(name,)) for n in hits]
    assert not found, (
        f"{name} names {found}. This file is shared verbatim by every carrier "
        f"in the bucket and may reference none of them - the rule is stated in "
        f"the file's own docstring, and it was broken there once already.")


# RSC 1520 found the hole in the arm above BEFORE four carriers copied it, and
# it reproduces here exactly: the name arm matches full PROJECT NAMES, and the
# violation actually present in the agreed bytes is a channel CODE.
#
#     ops/loop/winmutex.py:118
#       # call would then pass green. Found by RC on review, 2026-07-26.
#
# `RC` is a carrier and slots.py:7 says "Nothing here may reference ANY of
# them", so the shared bytes DO reference a carrier and the name arm is green
# over it. Measured on this disk: 1 hit, 0 false positives, word-boundary,
# case-SENSITIVE, over both files.
#
# The obvious repair does not work and RSC measured why before landing theirs:
# a corpus-wide code matcher returns 1635 case-sensitive hits over 240 files in
# their tree, so it needs an exemption list on day one. The defect's population
# is the TWO shared files, so the arm is scoped to them.
#
# The violation is PINNED as a sorted (file, code) list rather than fixed. It is
# inert - no value, no behaviour, no byte-identity break, carried since
# 2026-07-26 - and editing a pinned shared file is a joint round, not one
# carrier's unilateral edit. Not pinned by LINE: a line number decays on the
# next joint re-pin and trains readers to bump it instead of reading it.
CARRIER_CODES = ("RC", "CS", "LW", "LL", "RSC", "SS", "RM", "DS")

# EMPTIED by round B, 2026-09-21, in the same commit as the bytes - which is exactly
# what the arm below exists to force. An empty pin is STRICTER than the one it
# replaces: any carrier code entering either shared file now reddens immediately,
# with no grandfathered entry to hide behind.
#
# WHEN THIS LIST SHRINKS, ASK WHAT ELSE WAS READING IT.
#
# Shrinking it to [] on 2026-09-21 did not just tighten the arm below, it
# DISARMED it, plus two of its neighbours, and nobody noticed for a day. While
# the pin held [("winmutex.py", "RC")] the arm was comparing against a POSITIVE
# value, so a scanner that had stopped finding anything showed up RED. With the
# pin empty, `found == []` is satisfied just as well by a scanner that scans
# nothing, and the four-cell truth table has a hole in it:
#
#     pin=RC     scanner healthy -> PASS
#     pin=RC     scanner BROKEN  -> RED    (the POSITIVE pin was the detector)
#     pin=EMPTY  scanner healthy -> PASS
#     pin=EMPTY  scanner BROKEN  -> PASS   <- the hole, measured live here
#
# Measured 2026-09-20 on this disk, before the repair: writing the scanner's
# regex non-raw so `\b` collapses to byte 0x08 and matches nothing left this
# arm GREEN. So did forcing the scanned text to "". So did CARRIER_CODES = ().
# Worst of the set: SHARED_SHA256 = {} reduced the whole four-arm block to 1
# pass and 3 SKIPS, exit 0, which is one dict literal against the entire
# cross-repo parity guard.
#
# Do NOT repair that by re-growing the pin. The pin is allowed to be empty and
# SHOULD be. The repair is below: the detectors are seams, and separate arms
# write their own fixture, prove the fixture real FROM THE FIXTURE'S OWN BYTES
# (never from a pin - a pin is the thing under test), and point the detector at
# it. Those arms hold on a day when the real bytes are clean, which is the day
# a pure negative arm silently stops meaning anything.
KNOWN_CODE_HITS = []


def test_shared_modules_carry_only_the_pinned_carrier_codes():
    """Red if a new code enters either file. Red if the RC hit is repaired
    without this pin being updated in the SAME round - which is the half a
    digest cannot give you, because the digest moves legitimately either way."""
    found = _scan_carrier_codes(LOOP)
    assert found == sorted(KNOWN_CODE_HITS), (
        f"carrier codes in the shared files changed: {sorted(found)} vs pinned "
        f"{sorted(KNOWN_CODE_HITS)}. A NEW code is a violation to remove in a "
        f"joint round. A code that DISAPPEARED means the round happened - drop "
        f"it from KNOWN_CODE_HITS in that same commit.")


# ---- is the block above ARMED? a SKIPPED parametrize is not a pass ----------
#
# Every arm over the shared files is parametrized off SHARED_SHA256, so an
# empty dict collapses three of them to zero cases. pytest reports that as
# "3 skipped", exit 0, and a green run. Measured: 1 passed + 3 skipped.
# KNOWN_CODE_HITS is deliberately NOT asserted non-empty here - it is allowed
# to be empty, and that it can be is the whole reason the arms below exist.

def test_the_shared_file_guard_block_is_armed():
    assert SHARED_SHA256, (
        "SHARED_SHA256 is empty, so every parametrized arm over the shared "
        "files has zero cases and SKIPS. pytest exits 0 and the cross-repo "
        "parity guard is gone with no red anywhere.")
    assert CARRIER_CODES, (
        "CARRIER_CODES is empty, so the code scanner has nothing to look for "
        "and reports [] over any input at all.")
    assert CARRIER_NAMES, (
        "CARRIER_NAMES is empty, so the name scanner reports [] over any "
        "input at all.")
    for name in sorted(SHARED_SHA256):
        raw = (LOOP / name).read_bytes()
        assert len(raw) > 4000, (
            f"{name} is {len(raw)} bytes. These two files are ~6-10 KB; "
            f"anything this short means the arms are scanning a stub or a "
            f"truncated copy, and a negative assertion over it proves nothing.")


# ---- non-vacuity: the detectors, proved to FIRE and proved to stay QUIET ----
#
# Design rule, from RSC and adopted verbatim by SS: a non-vacuity arm must
# prove its fixture real WITHOUT CONSULTING ANY PIN. RSC could derive fixture
# reality from the real shared files' own code content; here that is impossible,
# because post round B those files legitimately contain ZERO carrier codes. So
# each arm WRITES its own fixture and proves it real from the FIXTURE'S OWN
# bytes, read back off disk, against a sentinel spelled literally right here.
#
# Both directions, because a matcher wide enough to fire is not yet a matcher
# narrow enough to mean anything.
#
# NOT claimed: coverage of an alternation-ordering defect. There is no
# alternation in these scanners - the code scanner loops one code at a time -
# so no mutant of that shape was run and no message below mentions one.

def _plant(root: Path, name: str, raw: bytes) -> Path:
    """Write `raw` verbatim, then prove the fixture REAL from its own bytes."""
    p = root / name
    tmp = p.parent / (p.name + ".tmp")
    tmp.write_bytes(raw)
    tmp.replace(p)
    back = p.read_bytes()
    assert back == raw, (
        f"{name} did not land byte-exact, so anything measured over it is "
        f"measured over the wrong bytes.")
    assert len(back) > 60, (
        f"{name} is {len(back)} bytes. An empty or trivially short fixture is "
        f"how a non-vacuity arm becomes vacuous itself.")
    return p


_POS_CODE = (
    b"# fixture, not shared bytes. Reproduces the real 2026-07-26 violation in\n"
    b"# shape: a channel code sitting as a whole word inside a comment.\n"
    b"# call would then pass green. Found by RC on review, 2026-07-26.\n"
)
_NEG_CODE = (
    b"# fixture, not shared bytes. Every token here is a NEAR MISS and a\n"
    b"# correct scanner stays silent over all of them.\n"
    b"# glued to word characters: ARCHIVE RCS CSV LWP SSH DSL RMDIR LLVM RSCX\n"
    b"# wrong case, standalone:  rc cs lw ll rsc ss rm ds\n"
)


def test_the_carrier_code_scanner_fires_on_a_planted_code(tmp_path: Path):
    p = _plant(tmp_path, "planted.py", _POS_CODE)
    assert b"Found by RC on review" in p.read_bytes(), (
        "the sentinel is not in the fixture's own bytes, so this arm is not "
        "measuring a detection at all.")
    assert _scan_carrier_codes(tmp_path, names=("planted.py",),
                               codes=("RC",)) == [("planted.py", "RC")], (
        "the code scanner did NOT find a whole-word RC in a fixture whose own "
        "bytes contain it. The detector is broken, not the shared files. "
        "First thing to check: the word-boundary regex is built with RAW "
        "string literals - written non-raw, \\b is byte 0x08 and matches "
        "nothing, and every negative arm over the real files goes green.")
    # Separate claim, deliberately second so an empty pin cannot be what made
    # the arm above green: the tuple production actually passes still carries
    # the code.
    assert _scan_carrier_codes(tmp_path, names=("planted.py",)) == [("planted.py", "RC")], (
        "the scanner finds RC when handed a literal tuple but not when handed "
        "CARRIER_CODES, so CARRIER_CODES no longer covers it.")


def test_the_carrier_code_scanner_is_silent_over_near_misses(tmp_path: Path):
    p = _plant(tmp_path, "nearmiss.py", _NEG_CODE)
    assert b"ARCHIVE" in p.read_bytes() and b"rc cs lw" in p.read_bytes(), (
        "the near-miss tokens are not in the fixture's own bytes, so a silent "
        "scanner here proves nothing.")
    assert _scan_carrier_codes(tmp_path, names=("nearmiss.py",)) == [], (
        "the code scanner fired on near misses. Either the word boundaries "
        "were dropped, so a code glued inside ARCHIVE or CSV now counts, or "
        "the match went case-insensitive, so ordinary lowercase prose counts. "
        "Both turn the arm over the real shared files into noise.")


def test_the_carrier_name_scanner_fires_on_a_planted_name(tmp_path: Path):
    body = (b"# fixture, not shared bytes. This is the 2026-09-07 defect in\n"
            b"# shape: the shared file naming a carrier it may not reference.\n"
            b"# handed to Riot Commander verbatim, then re-pinned on both sides\n")
    p = _plant(tmp_path, "named.py", body)
    assert b"Riot Commander" in p.read_bytes(), (
        "the sentinel name is not in the fixture's own bytes.")
    assert _scan_carrier_names(tmp_path, names=("named.py",),
                               carriers=("Riot Commander",)) == [("named.py", ["Riot Commander"])], (
        "the name scanner did NOT find a carrier name present in the "
        "fixture's own bytes.")
    assert _scan_carrier_names(tmp_path, names=("named.py",)) == [("named.py", ["Riot Commander"])], (
        "the scanner finds the name from a literal tuple but not from "
        "CARRIER_NAMES, so CARRIER_NAMES no longer covers it.")


def test_the_carrier_name_scanner_is_silent_over_near_misses(tmp_path: Path):
    body = (b"# fixture, not shared bytes. Near misses only: a mutex over one\n"
            b"# slot bucket, commander of nothing, a legion of ordinary tests,\n"
            b"# compute that is not resinous, a lantern, a clock, a substratum.\n")
    p = _plant(tmp_path, "nonames.py", body)
    assert b"legion of ordinary tests" in p.read_bytes(), (
        "the near-miss tokens are not in the fixture's own bytes.")
    assert _scan_carrier_names(tmp_path, names=("nonames.py",)) == [], (
        "the name scanner fired on near misses. A single word out of a "
        "carrier name is not the carrier name, and matching on one turns the "
        "arm over the real shared files into noise.")


def test_the_byte_hygiene_scanner_fires_on_a_planted_cr_and_high_byte(tmp_path: Path):
    lone_cr = b"# fixture, not shared bytes: ONE bare CR, no LF after it ->\r"
    body = lone_cr + b"# and one byte above 127 -> \xc2\xa0 <- right there.\n"
    p = _plant(tmp_path, "dirty.py", body)
    raw = p.read_bytes()
    assert 13 in raw and b"\r\n" not in raw, (
        "the fixture does not actually carry a LONE CR, so it cannot show "
        "whether the detector is pair-only.")
    assert max(raw) > 127, "the fixture carries no byte above 127."
    # The other half of the message the production arm carries, MEASURED
    # here rather than asserted: under universal newlines read_text turns
    # that lone CR into an LF, so a detector built on read_text cannot see
    # this fixture at all. That is why the seam reads BYTES.
    assert "\r" not in p.read_text(encoding="utf-8"), (
        "read_text preserved the CR, so the note about universal newlines in the CR message below is wrong for this platform.")
    cr, high = _scan_byte_hygiene(tmp_path, names=("dirty.py",))
    assert cr == [("dirty.py", 1)], (
        "the CR detector missed a bare CR in bytes it read itself. A "
        "detector that looks for the CRLF PAIR is blind to this, and so is "
        "read_text under universal newlines.")
    assert high and high[0][0] == "dirty.py" and 194 in high[0][1], (
        "the non-ASCII detector missed a byte above 127 in bytes it read "
        "itself.")


def test_the_byte_hygiene_scanner_is_silent_over_clean_lf_ascii(tmp_path: Path):
    body = (b"# fixture, not shared bytes: LF only, 7-bit ASCII throughout.\n"
            b"# tilde ~ and DEL-adjacent 0x7e are the highest bytes present.\n")
    p = _plant(tmp_path, "clean.py", body)
    raw = p.read_bytes()
    assert 13 not in raw and max(raw) < 128, (
        "the clean fixture is not actually clean.")
    assert _scan_byte_hygiene(tmp_path, names=("clean.py",)) == ([], []), (
        "the byte-hygiene detector fired over clean LF ASCII bytes, so its "
        "silence over the real shared files means nothing.")


# ---- the shared surface no digest can pin: a VALUE, not a file --------------
#
# One slot root (C:\ProgramData\lw-loop\slots) serves both repos, but each repo
# reads its OWN config for max_concurrent_lanes. If the two disagree the
# effective machine-wide ceiling silently becomes max(lw, rc) - the governor
# stops governing and nothing fails. SHARED_SHA256 cannot cover this: the
# contract is a number living in six mutually-diverged config files across two
# trees, not a byte-identical file. Raised by RC 2026-07-27.
#
# The INTERNAL half below is the one that matters for CI, because CI checks out
# ONE tree: a cross-repo comparison can only ever skip there.

def _declared_lane_counts():
    """{config name: value} for every ops/loop config that declares the key."""
    out = {}
    for cfg in sorted((ROOT / "ops" / "loop").glob("config*.json")):
        data = json.loads(cfg.read_text(encoding="utf-8"))
        if "max_concurrent_lanes" in data:
            out[cfg.name] = data["max_concurrent_lanes"]
    return out


def test_every_config_declaring_lanes_agrees_with_the_others():
    declared = _declared_lane_counts()
    assert declared, "no config declares max_concurrent_lanes - the key was renamed or lost"
    assert len(set(declared.values())) == 1, (
        f"LW configs disagree on the machine-wide lane ceiling: {declared}. "
        f"They share one slot root, so the loosest value wins and the tighter "
        f"ones are decoration.")


def test_the_code_default_matches_what_the_configs_declare():
    """config.dry.json omits the key, so the in-code default IS the ceiling for
    any config that does not declare one. A default that drifts from the
    declared value means the omitting configs silently run a different ceiling."""
    declared = set(_declared_lane_counts().values())
    src = (ROOT / "ops" / "loop" / "loop_controller.py").read_text(encoding="utf-8")
    m = re.search(r'CFG\.get\(\s*["\']max_concurrent_lanes["\']\s*,\s*(\d+)\s*\)', src)
    assert m, "could not find the max_concurrent_lanes default in loop_controller.py"
    assert int(m.group(1)) in declared, (
        f"loop_controller defaults to {m.group(1)} but the configs declare "
        f"{declared} - any config omitting the key runs the wrong ceiling")


def test_riot_commander_agrees_on_the_lane_ceiling():
    """Cross-repo half. SKIPS on a CI runner by design - that is exactly why the
    internal half above exists and is not redundant with this one."""
    sys.path.insert(0, str(ROOT / "tools"))
    import drift_guard

    # A RENAMED sibling must fail here, not skip. RC's copy of this guard held
    # LW's old root through the 2026-09-06 rename and silently stopped
    # comparing anything for three hours while staying green (Amberstone
    # e752e4edc). Genuine absence - a CI runner - still skips.
    sibling, status = drift_guard.resolve_sibling_root(Path(r"C:\Riot Commander"))
    assert status != "renamed", (
        f"Riot Commander moved to {sibling}: this guard is comparing nothing "
        f"until the constant is updated, and would stay green while blind"
    )
    if status == "absent":
        pytest.skip("Riot Commander tree not present on this machine")
    rc_root = sibling / "ops" / "loop"
    rc = {}
    for cfg in sorted(rc_root.glob("config*.json")):
        try:
            data = json.loads(cfg.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if "max_concurrent_lanes" in data:
            rc[cfg.name] = data["max_concurrent_lanes"]
    if not rc:
        pytest.skip("no RC config declares max_concurrent_lanes")
    assert set(rc.values()) | set(_declared_lane_counts().values()) == \
        set(_declared_lane_counts().values()), (
        f"RC declares {rc}, LW declares {_declared_lane_counts()} - one slot "
        f"root, so the higher number is the real ceiling in BOTH repos. "
        f"Change them in the same round or re-sync now.")


def test_acquired_is_logged_only_when_actually_held():
    """Emitter side of the defect RC found 2026-07-26: ACQUIRED must be gated on
    a real acquisition, and the fail-open path must emit a DISTINCT marker.
    An unconditional ACQUIRED opens a window that the gated RELEASED never
    closes, so the one case where the mutex did NOT serialize becomes the one
    case invisible to the overlap check."""
    src = (ROOT / "ops" / "loop" / "winmutex.py").read_text(encoding="utf-8")
    body = src[src.index("acquired = rc in"):src.index("yield handle")]
    assert "if acquired:" in body, "ACQUIRED must be gated on acquired"
    assert "UNSERIALIZED" in body, "the fail-open branch needs a distinct marker"
    # and the only ACQUIRED log sits inside that gate
    gated = body[body.index("if acquired:"):]
    assert "ACQUIRED" in gated


def test_unserialized_marker_wording_is_the_judge_contract():
    """p5_probe greps for this exact token; every emit site must use it."""
    src = (ROOT / "ops" / "loop" / "winmutex.py").read_text(encoding="utf-8")
    assert src.count("winmutex: UNSERIALIZED") == 3, (
        "all three unserialized paths (CreateMutexW failure, unexpected wait "
        "result, and the non-Windows no-op) must emit the same marker the "
        "judge hard-fails on")


def test_posix_no_op_branch_is_traced_not_silent(monkeypatch):
    """f1-phase6 item 9. Off Windows there is no named-mutex primitive, so hold
    degrades to a no-op - which is defensible. Yielding SILENTLY is not: every
    overlap guard in this file then passes VACUOUSLY on a POSIX runner, and the
    controller.log the judge reads carries no trace that nothing was serialized.
    Rejected alternative: an fcntl fallback. POSIX record locks are per-PROCESS,
    so test_mutex_serializes_two_threads (threads in ONE process) would stay red
    without a second RLock layer - the wrong size of change for a file that is
    byte-identical across two repos."""
    lines: list[str] = []
    monkeypatch.setattr(sys, "platform", "linux")
    with winmutex.hold("Global\\LWRC_TEST_POSIX", timeout=5, log=lines.append) as h:
        assert h is None, "the POSIX branch holds no handle"
    assert any(ln.startswith("winmutex: UNSERIALIZED Global\\LWRC_TEST_POSIX")
               for ln in lines), \
        f"the no-op branch must emit the judge's marker, got {lines!r}"
    assert not any("ACQUIRED" in ln for ln in lines), \
        "a no-op must never claim ACQUIRED - it would open a window RELEASED never closes"


def test_posix_no_op_lets_a_second_caller_in_while_the_first_holds(monkeypatch):
    """The POSIX mirror of test_mutex_timeout_raises_when_held_elsewhere, and
    the half that test_mutex_serializes_two_threads stops covering off Windows.

    Ported from RC 2c89e2a2 - both repos converged on this shape after RC found
    its own copy of the serialization test unguarded and failing on its nightly
    ubuntu run. The marker assertions above prove the no-op ANNOUNCES itself;
    only an actual second entry into a held name proves what it is announcing,
    and it must be proven rather than assumed - a future fcntl or RLock fallback
    would keep emitting the marker while quietly changing this behaviour, and
    the guard that noticed would be the one deleted as redundant.

    Overlap is established by events, not by timing: the first caller is parked
    inside its block until the second has been and gone. The marker is counted
    PER ENTRY because a log-reading judge sizes the breach by line count - one
    line per name would render N unprotected calls as a single incident.
    """
    monkeypatch.setattr(sys, "platform", "linux")
    name = "Global\\LWRC_TEST_POSIX_OVERLAP"
    lines: list[str] = []
    inside = threading.Event()
    release = threading.Event()

    def holder():
        with winmutex.hold(name, timeout=5, log=lines.append):
            inside.set()
            release.wait(timeout=10)

    t = threading.Thread(target=holder)
    t.start()
    try:
        assert inside.wait(timeout=10), "the first caller never entered its block"
        with winmutex.hold(name, timeout=0.2, log=lines.append) as h:
            assert h is None, "the POSIX branch holds no handle"
            assert not release.is_set(), \
                "the first caller must still be inside or this proves no overlap"
    finally:
        release.set()
        t.join(timeout=10)

    marker = "winmutex: UNSERIALIZED " + name
    assert sum(ln.startswith(marker) for ln in lines) == 2, \
        f"one marker per unprotected entry, not one per name, got {lines!r}"
    assert not any("ACQUIRED" in ln for ln in lines), \
        "a no-op must never claim ACQUIRED - it opens a window RELEASED never closes"


def test_posix_no_op_branch_survives_a_caller_that_passes_no_log(monkeypatch):
    """log= is optional on the two Windows fail-open branches; the new one must
    stay optional too or an unlogged caller crashes off-Windows."""
    monkeypatch.setattr(sys, "platform", "linux")
    with winmutex.hold("Global\\LWRC_TEST_POSIX_NOLOG") as h:
        assert h is None


def test_mutex_names_are_the_shared_contract():
    """Both repos must use the SAME names or they serialize against nothing."""
    assert winmutex.GEMINI_MUTEX == "Global\\MX-7C41A9E2"
    assert winmutex.GPU_MUTEX == "Global\\MX-2E58D3B6"


@pytest.mark.skipif(sys.platform != "win32", reason="windows mutex semantics")
def test_mutex_timeout_raises_when_held_elsewhere():
    got = threading.Event()
    release = threading.Event()

    def holder():
        with winmutex.hold("Global\\LWRC_TEST_TIMEOUT", timeout=10):
            got.set()
            release.wait(timeout=10)

    t = threading.Thread(target=holder)
    t.start()
    assert got.wait(timeout=10)
    try:
        with pytest.raises(winmutex.MutexTimeout):
            with winmutex.hold("Global\\LWRC_TEST_TIMEOUT", timeout=0.2):
                pytest.fail("acquired a mutex held by another thread")
    finally:
        release.set()
        t.join(timeout=10)


# ---------------------------------------------------------------------------
# the release path: a lock that cannot be DELETED must not stay REAPABLE-NEVER
#
# Found by RSC 2026-09-06, confirmed by RC on live ghosts (two of three lanes
# lost for 155 and 73 minutes). Windows refuses the holder's unlink while any
# waiter has the lock open for reading - is_stale -> _read -> Path.read_text
# opens without FILE_SHARE_DELETE - and the old `except OSError: pass` swallowed
# it. The orphan then keeps the pid and ts written at hold() entry, so BOTH fast
# arms of is_stale answer "not stale" and reap() skips it: the fail-open valve is
# disarmed by exactly the case that produces the leak. A controller running many
# cycles under one pid loses that lane for the life of the run.
# ---------------------------------------------------------------------------
def _payload(pid: int) -> dict:
    return {"pid": pid, "repo": "probe", "run_id": "r", "cycle": 1, "ts": time.time()}


def test_release_deletes_the_lock_in_the_ordinary_case(tmp_path):
    p = tmp_path / "0.lock"
    p.write_text(json.dumps(_payload(os.getpid())), encoding="utf-8")
    assert slots.release(p) is True
    assert not p.exists()


def test_a_lock_that_cannot_be_deleted_is_neutralised_so_reap_can_take_it(tmp_path, monkeypatch):
    """The headline regression. Portable: the unlink is forced to fail so the
    LOGIC is covered on POSIX CI too, not only on the Windows box that shows it.
    """
    p = tmp_path / "0.lock"
    p.write_text(json.dumps(_payload(os.getpid())), encoding="utf-8")

    def _refuse(self, *a, **k):
        raise PermissionError(32, "The process cannot access the file")

    monkeypatch.setattr(Path, "unlink", _refuse)
    lines = []
    assert slots.release(p, log=lines.append, attempts=2, backoff=0.001) is False
    assert p.exists(), "the point of this case is that the file survives"
    # the live pid and fresh ts are exactly what disarmed reap()
    assert slots.is_stale(p, stale_after=3600) is True
    assert any("release" in ln.lower() for ln in lines), "a failed release must say so"


def test_hold_does_not_log_released_when_the_unlink_failed(tmp_path, monkeypatch):
    """The log lied: `released` sat outside the try, so a pairing analysis over
    the logs read perfectly clean while a lane was stuck."""
    def _refuse(self, *a, **k):
        raise PermissionError(32, "The process cannot access the file")

    lines = []
    with slots.hold(3, root=tmp_path, repo="probe", run_id="r", cycle=1,
                    log=lines.append):
        monkeypatch.setattr(Path, "unlink", _refuse)
    joined = "\n".join(lines)
    assert "acquired" in joined
    # the SUCCESS marker specifically - the warning line is allowed to use the
    # word while denying it ("it is NOT released")
    assert "slots: released" not in joined, "a failed release must never log as released"
    assert "WARNING" in joined, "a failed release must be visible in the log"


@pytest.mark.skipif(sys.platform != "win32", reason="windows sharing semantics")
def test_a_real_open_reader_blocks_the_unlink_and_the_lane_still_comes_back(tmp_path):
    """The same case with a REAL handle rather than a forced failure, then the
    recovery: once the reader closes, reap() can take the neutralised lock."""
    p = tmp_path / "0.lock"
    p.write_text(json.dumps(_payload(os.getpid())), encoding="utf-8")
    fh = open(p, encoding="utf-8")   # the read handle Path.read_text opens
    try:
        fh.read()
        assert slots.release(p, attempts=2, backoff=0.001) is False
        assert p.exists()
        assert slots.is_stale(p, stale_after=3600) is True
    finally:
        fh.close()
    assert slots.reap(tmp_path, 3, 3600) == 1
    assert not p.exists()


# ---------------------------------------------------------------------------
# the ceiling property: "total concurrent holders never exceeds 5 + surplus"
#
# RC's design review of 2026-09-07 01:35 proposed a reserved floor plus a shared
# surplus - five reserved lanes, one per carrier repo, plus a first-come surplus
# pool - and listed four properties worth pinning. Three are about reservation
# and cannot be tested until the five repos agree the short repo keys; that work
# is BLOCKED and deliberately not started here. The fourth is the machine-wide
# ceiling, it is already true of today's bucket, and RC accepted LW's amendment
# that it belongs in this file rather than in a note (RC, 2026-09-07 00:20):
# "a property asserted in RC's prose and in nobody's test is asserted nowhere".
#
# SCOPE, stated beside the number so nobody reads more into these arms than they
# prove. Today's slots.py has NO reservation: the bucket is index-named and
# first-come, so the ceiling is the ONLY one of the four properties that holds.
# One repo can still take every lane - that is the honest caveat on the
# operator's fallback ladder, not a defect these arms are silent about. They
# assert the TOTAL and say nothing about who holds what, because today nothing
# does.
#
# The two constants below are the PROPOSAL's widths, not LW's configured
# ceiling - the configs still declare 3 (pinned by the lane-agreement arms
# above). They are here so the ceiling is exercised at the width the ladder
# would run at, before anyone runs it.
# ---------------------------------------------------------------------------

RESERVED_FLOOR = 5      # one reserved lane per carrier repo
SURPLUS = 2             # RC's option (3): five reserved, two free-for-all
CEILING = RESERVED_FLOOR + SURPLUS


def _peak_holders(contenders: int, acquire, dwell: float = 0.05):
    """Drive `contenders` threads through `acquire(i)` and sample the peak.

    `acquire` is a context-manager factory so the SAME harness can be pointed at
    the real governor and at a deliberately unbounded one - see the negative
    control below, which is what proves these arms can go red at all.

    The threads meet at a barrier before contending, so "the width was fully
    used" is a real observation rather than a race on thread start-up.
    """
    live = 0
    peak = 0
    lock = threading.Lock()
    errors: list = []
    gate = threading.Barrier(contenders, timeout=60)

    def worker(i: int):
        nonlocal live, peak
        try:
            gate.wait()
            with acquire(i):
                with lock:
                    live += 1
                    peak = max(peak, live)
                time.sleep(dwell)
                with lock:
                    live -= 1
        except Exception as e:  # noqa: BLE001 - surface, do not swallow
            errors.append(e)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(contenders)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=120)
    return peak, errors


@pytest.mark.parametrize("width", [1, 2, 3, RESERVED_FLOOR, CEILING])
def test_total_holders_never_exceed_the_bucket_width(tmp_path: Path, width: int):
    """The ceiling at every width on the operator's ladder, three-times-oversubscribed.

    width 3 is what the configs declare today; RESERVED_FLOOR is option (2), one
    guaranteed lane per repo with no surplus; CEILING is option (3), the "5 +
    surplus" RC asked to have pinned.
    """
    def acquire(i: int):
        return slots.hold(width, root=tmp_path, repo="lw", run_id=f"r{i}",
                          cycle=i, backoff=0.02, jitter=0.02, timeout=60)

    peak, errors = _peak_holders(3 * width, acquire)
    assert not errors, errors
    assert peak <= width, (
        f"slot governor breached at width {width}: {peak} concurrent holders")
    assert peak == width, (
        f"width {width} was never fully used - the arm did not actually contend, "
        f"so the ceiling above was not exercised")


def test_the_bucket_never_holds_more_lockfiles_than_the_ceiling(tmp_path: Path):
    """The same property measured ON DISK rather than through the callers.

    The thread counter above trusts hold() to hand out what it created. This one
    watches the bucket directory instead, so a try_acquire that created an extra
    lockfile - or a scheme that added a differently-named one - is caught even if
    every caller still counted correctly.
    """
    stop = threading.Event()
    seen_max = 0
    names: set[str] = set()

    def sampler():
        nonlocal seen_max
        while not stop.is_set():
            present = [q.name for q in tmp_path.glob("*.lock")]
            names.update(present)
            seen_max = max(seen_max, len(present))
            time.sleep(0.001)

    watcher = threading.Thread(target=sampler, daemon=True)
    watcher.start()
    try:
        def acquire(i: int):
            return slots.hold(CEILING, root=tmp_path, repo="lw", run_id=f"r{i}",
                              cycle=i, backoff=0.02, jitter=0.02, timeout=60)

        peak, errors = _peak_holders(3 * CEILING, acquire)
    finally:
        stop.set()
        watcher.join(timeout=10)

    assert not errors, errors
    assert seen_max <= CEILING, (
        f"the bucket grew to {seen_max} lockfiles at width {CEILING}: "
        f"{sorted(names)}")
    assert names == {f"{i}.lock" for i in range(CEILING)}, (
        f"unexpected lock names in the bucket: {sorted(names)}. Today's scheme is "
        f"index-named ONLY - if this went red because reserved-<key>.lock now "
        f"exists, the ceiling arms here need re-deriving against BOTH schemes and "
        f"reap() must have learned both too, or a repo loses its floor silently.")
    # TWO assertions, not one, because a single `peak == CEILING` reported
    # "width was never fully used" for a peak that EXCEEDED the width. Measured
    # 2026-09-10: one full-suite run went red here with peak 8 at width 7 and
    # printed the not-contended message, which is the opposite of what happened.
    # It did NOT reproduce - 25 isolated runs and 25 under 12-way CPU load, both
    # clean - so the cause is UNKNOWN and recorded as such rather than guessed
    # at. If it recurs, this message says which of the two it is.
    assert peak <= CEILING, (
        f"OVER-ADMISSION: {peak} holders were live at width {CEILING} while the "
        f"bucket sampler never saw more than {seen_max} lockfile(s). The caller "
        f"count cannot exceed the holder count by construction (it decrements "
        f"INSIDE the with), so this is the governor admitting an extra holder, "
        f"not a sampling artifact. ops/loop/slots.py is byte-identical by "
        f"contract with RC - a fix needs a re-sync, and LW's suite is the only "
        f"coverage either side has.")
    assert peak == CEILING, (
        f"width {CEILING} was never fully used - the arm did not actually contend")


def test_the_ceiling_arms_can_actually_go_red(tmp_path: Path):
    """Negative control: point the same harness at a governor with no bucket.

    A passing arm proves nothing until something demonstrably fails it - RSC
    found three of its own gates on 2026-09-07 that were implemented correctly,
    unit-tested, and never consulted by the code that runs. The same class
    applies to a test: if the sampler could not observe a breach, the greens
    above would be indistinguishable from a governor that never governed.
    """
    @contextlib.contextmanager
    def unbounded(i: int):
        p = tmp_path / f"{i}.lock"
        p.write_text("{}", encoding="utf-8")
        try:
            yield p
        finally:
            p.unlink()

    peak, errors = _peak_holders(3 * CEILING, unbounded)
    assert not errors, errors
    assert peak > CEILING, (
        f"the harness observed a peak of {peak} against an UNBOUNDED governor: "
        f"it cannot see a breach, so the ceiling arms above assert nothing")
