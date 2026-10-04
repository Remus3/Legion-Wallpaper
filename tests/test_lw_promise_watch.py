"""Promise watch over CLAUDE.md "Reverse if" conditions (directive P1-3, LW part).

A weekly job keeps a dated or conditional promise without anyone remembering:
it runs a machine-checkable condition (argv probe, no shell, allowlisted
executable) and, the FIRST time it is true, posts once with an idempotency
marker. A marker already said - or a closed tracker - means never again. A
probe that cannot decide (exit 2, crash, timeout) fails the run (exit 2)
instead of passing quietly. Manual runs default to dry-run.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

import lw_promise_watch as W  # noqa: E402

PY = sys.executable


def _promises(tmp_path, items):
    p = tmp_path / "promises.json"
    p.write_text(json.dumps({"schema": 1, "promises": items, "not_machine_checkable": []}),
                 encoding="ascii")
    return p


def _probe(code):
    word = {0: "TRUE", 1: "false"}.get(code, "undecided")
    return [PY, "-c", f"import sys; print('probe: {word}'); sys.exit({code})"]


def _item(pid="p1", code=0, **kw):
    d = {"id": pid, "kind": "probe", "condition": _probe(code), "deliver_to": "note",
         "marker": f"promise:{pid}", "says": f"{pid} condition is now true"}
    d.update(kw)
    return d


def _run(tmp_path, promises, dry=False, now=None):
    return W.run(promises, state_dir=tmp_path / "state", dry_run=dry, now=now)


def test_true_condition_posts_exactly_once_across_three_runs(tmp_path):
    p = _promises(tmp_path, [_item()])
    results = [_run(tmp_path, p) for _ in range(3)]
    assert [r["posted"] for r in results] == [["p1"], [], []]
    lines = (tmp_path / "state" / "posts.jsonl").read_text(encoding="ascii").splitlines()
    assert len(lines) == 1 and json.loads(lines[0])["marker"] == "promise:p1"
    assert all(r["exit"] == 0 for r in results)


def test_false_condition_posts_nothing(tmp_path):
    p = _promises(tmp_path, [_item(code=1)])
    r = _run(tmp_path, p)
    assert r["posted"] == [] and r["exit"] == 0


def test_marker_already_said_prevents_a_second_post(tmp_path):
    p = _promises(tmp_path, [_item()])
    _run(tmp_path, p)
    p2 = _promises(tmp_path, [_item(pid="p1-renamed", marker="promise:p1")])
    assert _run(tmp_path, p2)["posted"] == []


def test_closed_tracker_counts_as_said(tmp_path):
    p = _promises(tmp_path, [_item()])
    W.close_tracker("promise:p1", "operator answered in session", state_dir=tmp_path / "state")
    assert _run(tmp_path, p)["posted"] == []


def test_undecidable_probe_fails_the_run_with_exit_2(tmp_path):
    p = _promises(tmp_path, [_item(code=2), _item(pid="p2")])
    r = _run(tmp_path, p)
    assert r["exit"] == 2
    assert r["undecided"] == ["p1"]
    assert r["posted"] == ["p2"]      # one unknown does not hide another's truth


def test_crashing_or_missing_probe_is_undecided(tmp_path):
    # an uncaught exception exits 1 - the same code as "false" - so it must
    # not read as false without the probe saying so
    p = _promises(tmp_path, [_item(condition=[PY, "-c", "raise RuntimeError('x')"]),
                             _item(pid="p2", condition=["no-such-binary-xyz"])])
    r = _run(tmp_path, p)
    assert r["exit"] == 2 and set(r["undecided"]) == {"p1", "p2"}


def test_dry_run_posts_nothing_and_records_nothing(tmp_path):
    p = _promises(tmp_path, [_item()])
    r = _run(tmp_path, p, dry=True)
    assert r["would_post"] == ["p1"] and r["posted"] == []
    assert not (tmp_path / "state" / "posts.jsonl").exists()
    assert _run(tmp_path, p)["posted"] == ["p1"]


def test_cli_defaults_to_dry_run(tmp_path, monkeypatch):
    p = _promises(tmp_path, [_item()])
    rc = W.main(["--promises", str(p), "--state-dir", str(tmp_path / "state")])
    assert rc == 0
    assert not (tmp_path / "state" / "posts.jsonl").exists()
    rc = W.main(["--promises", str(p), "--state-dir", str(tmp_path / "state"), "--post"])
    assert (tmp_path / "state" / "posts.jsonl").is_file()


def test_string_condition_and_unlisted_executable_are_refused(tmp_path):
    for bad in ("python -c 1", ["powershell", "-c", "1"], [], ["cmd", "/c", "echo"]):
        with pytest.raises(W.PromiseError):
            W.validate(_item(condition=bad))


def test_date_kind_is_true_on_and_after_its_date(tmp_path):
    item = {"id": "d1", "kind": "date", "on": "2026-10-09", "deliver_to": "note",
            "marker": "promise:d1", "says": "C4 carrier target date passed"}
    p = _promises(tmp_path, [item])
    assert _run(tmp_path, p, now="2026-10-08")["posted"] == []
    assert _run(tmp_path, p, now="2026-10-09")["posted"] == ["d1"]


def test_tracked_promises_file_covers_every_reverse_if_entry():
    """Every "Reverse if" in CLAUDE.md's Settled list is either a watched
    promise or listed as not machine-checkable - nothing silently unwatched."""
    data = json.loads(W.PROMISES_PATH.read_text(encoding="ascii"))
    for item in data["promises"]:
        W.validate(item)
    covered = {i["settled"] for i in data["promises"] if i.get("settled")}
    covered |= {i["settled"] for i in data["not_machine_checkable"]}
    for entry in W.settled_entries():
        assert entry in covered, f"Settled entry not covered: {entry!r}"


OFFLINE_PROBES = ("adr001_superseded", "adr003_superseded", "adr007_superseded",
                  "ci_python_pin_moved", "ci_paths_filter_added", "privacy_boundary_changed")


@pytest.mark.parametrize("name", OFFLINE_PROBES)
def test_offline_probes_read_false_on_this_tree(name, capsys):
    """Every offline Reverse-if condition is currently NOT met - a probe that
    read TRUE here would be a false alarm (or a real reversal to act on)."""
    import lw_promise_probes as PR
    assert PR.main([name]) == 1
    assert capsys.readouterr().out.strip().endswith("false")


def test_every_promise_probe_name_exists():
    import lw_promise_probes as PR
    data = json.loads(W.PROMISES_PATH.read_text(encoding="ascii"))
    for item in data["promises"]:
        if item["kind"] == "probe":
            assert item["condition"][-1] in PR.PROBES


def test_paths_filter_probe_ignores_comments(tmp_path, monkeypatch):
    import lw_promise_probes as PR
    (tmp_path / ".github" / "workflows").mkdir(parents=True)
    ci = tmp_path / ".github" / "workflows" / "ci.yml"
    ci.write_text("on:\n  push:\n    # paths: ['x']\n", encoding="ascii")
    monkeypatch.setattr(PR, "ROOT", tmp_path)
    assert PR.ci_paths_filter_added() is False
    ci.write_text("on:\n  push:\n    paths-ignore: ['**/*.md']\n", encoding="ascii")
    assert PR.ci_paths_filter_added() is True
