"""Fault-proven gate board (tools/lw_gate_board.py, directive P0-3).

A requirement row is only trusted once it has been SEEN RED: it passes on the
clean subject and fails on a planted copy. These tests pin the board's own
semantics first (BROKEN / UNKNOWN / UNPROVEN / aliasing), then the LW registry
(every live G1 metric rule and every G2 verify arm has a row with a fault), and
finally the mutant the directive names: delete a gate's threshold and its row
flips to BROKEN.

Hermetic: synthetic numpy subjects only, no golden bytes, no venv-only deps.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

import lw_gate_board as B  # noqa: E402


# ------------------------------------------------------------------ core board
def _board_with(measure, fault=None, bar=None):
    board = B.Board()
    board.add(B.Row(name="r", said="value stays small", measure=measure,
                    bar=bar or B.Bar("at_most", hi=1.0), unit="u"))
    if fault is not None:
        board.fault("r", amplitude="test", evidence="test")(fault)
    return board


def _subject():
    return {"slug": "s", "img": np.zeros((4, 4), dtype=np.float64)}


def _plant_big(subj):
    subj["img"] += 5.0
    return subj


def test_proven_when_clean_passes_and_planted_fails():
    board = _board_with(lambda s: float(s["img"].max()), _plant_big)
    (p,) = board.prove(_subject())
    assert p.state == B.PROVEN
    assert p.clean.state == B.PASS and p.planted.state == B.FAIL


def test_fault_that_does_not_move_the_measurement_reads_broken():
    board = _board_with(lambda s: float(s["img"].max()), lambda s: s)
    (p,) = board.prove(_subject())
    assert p.state == B.BROKEN
    assert not B.summary([p])["green"]


def test_measure_that_raises_reads_unknown_and_summary_not_green():
    def boom(_s):
        raise RuntimeError("no input")
    board = _board_with(boom, _plant_big)
    (p,) = board.prove(_subject())
    assert p.state == B.UNKNOWN
    assert p.clean.state == B.UNKNOWN
    assert "no input" in p.clean.detail
    assert not B.summary([p])["green"]


def test_measure_returning_none_or_nan_reads_unknown():
    for val in (None, float("nan")):
        board = _board_with(lambda s, v=val: v, _plant_big)
        assert board.report(_subject())[0].state == B.UNKNOWN


def test_row_without_fault_reads_unproven_and_is_not_green():
    board = _board_with(lambda s: float(s["img"].max()))
    (p,) = board.prove(_subject())
    assert p.state == B.UNPROVEN
    assert not B.summary([p])["green"]


def test_clean_subject_failing_the_row_cannot_prove_it():
    board = _board_with(lambda s: float(s["img"].max()) + 10.0, _plant_big)
    (p,) = board.prove(_subject())
    assert p.state == B.UNKNOWN
    assert "clean" in p.detail


def test_planted_copy_never_aliases_the_original():
    subj = _subject()
    before = subj["img"].copy()
    board = _board_with(lambda s: float(s["img"].max()), _plant_big)
    board.prove(subj)
    assert np.array_equal(subj["img"], before), "fault leaked into the original"


def test_fault_returning_the_original_array_object_reads_broken():
    subj = _subject()
    shared = subj["img"]

    def alias(s):
        s["img"] = shared  # hands back the ORIGINAL buffer
        return s
    board = _board_with(lambda s: float(s["img"].max()), alias)
    (p,) = board.prove(subj)
    assert p.state == B.BROKEN
    assert "alias" in p.detail


def test_validation_rows_are_listed_but_never_count_toward_done():
    board = _board_with(lambda s: float(s["img"].max()), _plant_big)
    board.add(B.Row(name="v", said="reads like the original art",
                    kind="validation"))
    proofs = board.prove(_subject())
    states = {p.row: p.state for p in proofs}
    assert states["v"] == B.VALIDATION
    summ = B.summary(proofs)
    assert summ["green"] is True
    assert summ["validation"] == ["v"]


def test_bar_kinds():
    assert B.Bar("at_most", hi=1.0).holds(1.0)
    assert not B.Bar("at_most", hi=1.0).holds(1.01)
    assert B.Bar("at_least", lo=2.0).holds(2.0)
    assert not B.Bar("at_least", lo=2.0).holds(1.9)
    assert B.Bar("between", lo=0.0, hi=1.0).holds(0.5)
    assert not B.Bar("between", lo=0.0, hi=1.0).holds(1.5)
    # a threshold read live at evaluation time (callable) follows the gate
    th = {"v": 1.0}
    bar = B.Bar("at_most", hi=lambda: th["v"])
    assert bar.holds(0.9)
    th["v"] = 0.5
    assert not bar.holds(0.9)


def test_aggregate_over_subjects():
    board = _board_with(lambda s: float(s["img"].max()), _plant_big)
    per = [board.prove({"slug": f"s{i}", "img": np.zeros((2, 2))}) for i in range(3)]
    agg = B.aggregate(per)
    assert agg[0]["state"] == B.PROVEN and agg[0]["n_proven"] == 3
    # one broken subject makes the whole row BROKEN
    per[1][0].state = B.BROKEN
    assert B.aggregate(per)[0]["state"] == B.BROKEN


def test_proof_table_is_ascii_and_names_every_row():
    board = _board_with(lambda s: float(s["img"].max()), _plant_big)
    board.add(B.Row(name="v", said="operator eye", kind="validation"))
    table = B.proof_table(B.aggregate([board.prove(_subject())]))
    table.encode("ascii")
    assert "r" in table and "PROVEN" in table and "VALIDATION" in table


# ------------------------------------------------------------------ LW registry
def _g1_subject(usm_percent=60):
    """Synthetic source + 2x upscale with a light USM, stripes for strong edges.

    Toy frames are idiosyncratic, so the knobs are pinned: percent 60 proves
    lap_ratio, percent 35 proves halo_pct (both measured 2026-10-04)."""
    from PIL import Image, ImageFilter
    rng = np.random.default_rng(7)
    h, w = 90, 160
    yy, xx = np.mgrid[0:h, 0:w]
    base = 60.0 + 120.0 * xx / w + 30.0 * np.sin(xx / 4.0) * np.sin(yy / 5.2)
    for k in range(3):
        base[10 + k * 7:16 + k * 7, 20:140] = 230.0 if k % 2 == 0 else 20.0
    base += rng.normal(0.0, 1.0, size=base.shape)
    src = np.clip(base, 0, 255).astype(np.uint8)
    src_rgb = np.stack([src] * 3, axis=-1)
    up = Image.fromarray(src_rgb).resize((w * 2, h * 2), Image.LANCZOS)
    up = up.filter(ImageFilter.UnsharpMask(radius=1.2, percent=usm_percent, threshold=3))
    return {"slug": "synthetic", "source_rgb": src_rgb,
            "output_rgb": np.asarray(up).copy(), "backend": "ijn"}


def _textured_frame():
    rng = np.random.default_rng(3)
    img = rng.integers(0, 256, size=(144, 256, 3), dtype=np.uint8)
    return {"slug": "textured", "source_rgb": img, "output_rgb": img.copy(),
            "backend": "ijn"}


# verdict() rules the live first pass no longer feeds. band_delta stays a
# verdict rule only because lw_clean_fr.clean_fr_audit gates it at same scale
# (no common-scale resample there); its first-pass arm and board row were
# retired in R1b (LEDGER 265). Adding a name here needs a LEDGER entry.
NOT_FIRST_PASS_RULES = {"band_delta"}


def test_registry_covers_every_live_g1_metric_rule():
    import lw_first_pass
    import lw_g1_gate as G
    board = B.lw_board()
    names = {r.name for r in board.rows}
    live = set(lw_first_pass.assemble_metrics(
        {"ms_ssim": 1.0, "lpips": 0.0}, 1.0, 0.0, 0.0))
    assert "band_delta" not in live
    for metric, _kind, _th in G._METRIC_RULES:
        if metric in NOT_FIRST_PASS_RULES:
            assert metric not in live
            continue
        assert metric in live, f"verdict rule {metric} is not fed by the first pass"
        assert f"G1.{metric}" in names, f"live G1 arm {metric} has no board row"


def test_registry_covers_every_g2_verify_arm():
    board = B.lw_board()
    names = {r.name for r in board.rows}
    for arm in ("G2.outside_identity", "G2.no_op",
                "G2.seam_step", "G2.text_residue_mf"):
        assert arm in names


def test_every_measured_lw_row_registers_a_fault_with_evidence():
    board = B.lw_board()
    for row in board.rows:
        if row.kind == "validation":
            continue
        f = board.faults.get(row.name)
        assert f is not None, f"{row.name} has no fault"
        assert f.amplitude and f.evidence, f"{row.name} fault lacks amplitude/evidence"


def test_lw_has_operator_validation_rows():
    board = B.lw_board()
    assert any(r.kind == "validation" for r in board.rows)


def test_numpy_g1_rows_prove_on_a_synthetic_subject():
    board = B.lw_board(envs=("base",))
    p60 = {p.row: p for p in board.prove(_g1_subject(60))}
    p35 = {p.row: p for p in board.prove(_g1_subject(35))}
    assert p60["G1.lap_ratio"].state == B.PROVEN, p60["G1.lap_ratio"].detail
    assert p35["G1.halo_pct"].state == B.PROVEN, p35["G1.halo_pct"].detail
    assert p60["G0.aspect"].state == B.PROVEN


def test_deleting_a_g1_threshold_flips_its_row_to_broken(monkeypatch):
    """The directive's mutant: remove the halo threshold from the live table."""
    import lw_g1_gate as G
    th = {k: v for k, v in G.DEFAULT_G1_THRESHOLDS.items() if k != "halo_pct"}
    monkeypatch.setattr(G, "DEFAULT_G1_THRESHOLDS", th)
    board = B.lw_board(envs=("base",))
    proofs = {p.row: p for p in board.prove(_g1_subject(35))}
    assert proofs["G1.halo_pct"].state == B.BROKEN


def test_deleting_the_lap_ratio_floor_flips_its_row_to_broken(monkeypatch):
    import lw_g1_gate as G
    th = {k: v for k, v in G.DEFAULT_G1_THRESHOLDS.items() if k != "lap_ratio"}
    monkeypatch.setattr(G, "DEFAULT_G1_THRESHOLDS", th)
    proofs = {p.row: p for p in B.lw_board(envs=("base",)).prove(_g1_subject(60))}
    assert proofs["G1.lap_ratio"].state == B.BROKEN


def test_g2_outside_identity_and_no_op_prove_on_a_textured_frame():
    board = B.lw_board(envs=("base",))
    subj = B.g2_subject(_textured_frame())
    proofs = {p.row: p for p in board.prove(subj)}
    for name in ("G2.outside_identity", "G2.no_op"):
        assert proofs[name].state == B.PROVEN, (name, proofs[name].detail)


def test_mean_only_outside_arm_is_broken_on_a_localized_change(monkeypatch):
    """Mutation proof of the strict arm (OUTSIDE_MAX_ABS): with only the old
    frame-mean arms the planted 32x32 block is invisible and the row reads
    BROKEN - which is what the golden run measured before the fix."""
    import lw_clean_pass as cp
    monkeypatch.setattr(cp, "OUTSIDE_MAX_ABS", float("inf"))
    rng = np.random.default_rng(5)
    img = rng.integers(0, 256, size=(720, 1280, 3), dtype=np.uint8)
    subj = B.g2_subject({"slug": "big", "source_rgb": img, "output_rgb": img,
                         "backend": "ijn"})
    board = B.lw_board(envs=("base",))
    row = next(r for r in board.rows if r.name == "G2.outside_identity")
    assert board.prove_row(row, subj).state == B.BROKEN
    monkeypatch.setattr(cp, "OUTSIDE_MAX_ABS", 0.0)
    assert board.prove_row(row, subj).state == B.PROVEN


def test_rows_outside_the_requested_envs_are_not_evaluated():
    board = B.lw_board(envs=("base",))
    names = {r.name for r in board.rows}
    assert "G1.msssim" not in names and "G2.text_residue_mf" not in names


# ------------------------------------------------------------------ proofs file
def test_write_and_check_proofs_round_trip(tmp_path):
    board = _board_with(lambda s: float(s["img"].max()), _plant_big)
    agg = B.aggregate([board.prove(_subject())])
    out = tmp_path / "gate_proofs.json"
    B.write_proofs(out, agg, registry=B.registry_digest(board), subjects=["s"])
    data = json.loads(out.read_text(encoding="ascii"))
    assert data["green"] is True
    assert B.check_proofs(out, board) == []


def test_check_proofs_flags_unproven_broken_missing_and_stale(tmp_path):
    board = _board_with(lambda s: float(s["img"].max()), lambda s: s)
    agg = B.aggregate([board.prove(_subject())])
    out = tmp_path / "gate_proofs.json"
    B.write_proofs(out, agg, registry=B.registry_digest(board), subjects=["s"])
    problems = B.check_proofs(out, board)
    assert any("BROKEN" in p for p in problems)
    # a newly registered row with no proof is a breach, and so is a stale digest
    board.add(B.Row(name="new", said="x", measure=lambda s: 0.0,
                    bar=B.Bar("at_most", hi=1.0)))
    problems = B.check_proofs(out, board)
    assert any("new" in p for p in problems)
    assert any("stale" in p for p in problems)


def test_check_proofs_absent_file_is_reported_not_green(tmp_path):
    board = _board_with(lambda s: float(s["img"].max()), _plant_big)
    assert B.check_proofs(tmp_path / "nope.json", board) is None


def test_check_proofs_unparseable_file_is_a_problem(tmp_path):
    out = tmp_path / "gate_proofs.json"
    out.write_text("{not json", encoding="ascii")
    board = _board_with(lambda s: float(s["img"].max()), _plant_big)
    problems = B.check_proofs(out, board)
    assert problems and "unreadable" in problems[0]


@pytest.mark.parametrize("name", ["fault_downup", "fault_usm", "fault_posterize",
                                  "fault_shift", "fault_outside_block",
                                  "fault_seam", "fault_text"])
def test_fault_primitives_never_touch_their_input(name):
    rng = np.random.default_rng(1)
    img = rng.integers(0, 255, size=(64, 96, 3), dtype=np.uint8)
    keep = img.copy()
    fn = getattr(B, name)
    if name == "fault_outside_block":
        mask = np.zeros(img.shape[:2], dtype=bool)
        mask[40:50, 10:30] = True
        out = fn(img, mask)
    elif name == "fault_seam":
        mask = np.zeros(img.shape[:2], dtype=bool)
        mask[40:50, 10:30] = True
        out = fn(img, mask)
    elif name == "fault_text":
        out = fn(img, (10, 10, 90, 40), alpha=0.5)
    else:
        out = fn(img)
    assert np.array_equal(img, keep)
    assert not np.shares_memory(out, img)
    assert out.dtype == np.uint8


# ------------------------------------------------------------------ acknowledgements
# Adjudicated 2026-10-04 (option b): non-PROVEN rows breach by default; a
# TRACKED acknowledgement entry downgrades exactly that row to a note while its
# recorded state is no worse than the entry pins. Anything else still breaches.
def _ack_fixture(tmp_path, fault, ack_entries, ledger_ids=(7,)):
    board = _board_with(lambda s: float(s["img"].max()), fault)
    per = [board.prove({"slug": f"s{i}", "img": np.zeros((2, 2))}) for i in range(2)]
    agg = B.aggregate(per)
    proofs = tmp_path / "gate_proofs.json"
    B.write_proofs(proofs, agg, registry=B.registry_digest(board), subjects=["s0", "s1"])
    ack = tmp_path / "ack.json"
    ack.write_text(json.dumps({"schema": 1, "entries": ack_entries}), encoding="ascii")
    ledger = tmp_path / "LEDGER.md"
    ledger.write_text("".join(f"{n}. DONE **x**\n" for n in ledger_ids), encoding="ascii")
    return board, proofs, ack, ledger


def _entry(**kw):
    e = {"row": "r", "state": "BROKEN", "n_proven": 0, "failing": ["s0", "s1"],
         "reason": "metric blind", "ledger": 7, "clears_when": "PROVEN 2/2"}
    e.update(kw)
    return e


def test_acknowledged_broken_row_is_a_note_not_a_problem(tmp_path):
    board, proofs, ack, ledger = _ack_fixture(tmp_path, lambda s: s, [_entry()])
    problems, notes = B.check_proofs_acked(proofs, board, ack, ledger)
    assert problems == []
    assert any("ACKNOWLEDGED" in n and "r" in n for n in notes)


def test_unacknowledged_broken_row_still_breaches(tmp_path):
    board, proofs, ack, ledger = _ack_fixture(tmp_path, lambda s: s, [])
    problems, _ = B.check_proofs_acked(proofs, board, ack, ledger)
    assert any("BROKEN" in p for p in problems)


def test_ack_with_missing_ledger_item_or_clearing_condition_breaches(tmp_path):
    for bad in (_entry(ledger=99), _entry(clears_when="")):
        board, proofs, ack, ledger = _ack_fixture(tmp_path, lambda s: s, [bad])
        problems, _ = B.check_proofs_acked(proofs, board, ack, ledger)
        assert problems, bad


def test_row_worse_than_its_ack_breaches(tmp_path):
    # ack pins 1 proven subject and only s1 failing; the run proves 0 and fails both
    board, proofs, ack, ledger = _ack_fixture(
        tmp_path, lambda s: s, [_entry(n_proven=1, failing=["s1"])])
    problems, _ = B.check_proofs_acked(proofs, board, ack, ledger)
    assert any("worse" in p for p in problems)


def test_ack_for_a_row_now_proven_says_remove_it(tmp_path):
    board, proofs, ack, ledger = _ack_fixture(tmp_path, _plant_big, [_entry()])
    problems, notes = B.check_proofs_acked(proofs, board, ack, ledger)
    assert problems == []
    assert any("remove" in n for n in notes)


def test_absent_proofs_breach_when_the_golden_set_is_on_disk(tmp_path):
    board = _board_with(lambda s: float(s["img"].max()), _plant_big)
    problems, _ = B.check_proofs_acked(tmp_path / "none.json", board,
                                       tmp_path / "ack.json", tmp_path / "L.md",
                                       golden_present=True)
    assert problems and "absent" in problems[0]
    problems, notes = B.check_proofs_acked(tmp_path / "none.json", board,
                                           tmp_path / "ack.json", tmp_path / "L.md",
                                           golden_present=False)
    assert problems == [] and notes


def test_tracked_ack_file_is_well_formed():
    data = json.loads((Path(B.ROOT) / "config" / "gate_board_ack.json").read_text(encoding="ascii"))
    rows = {r.name for r in B.lw_board().rows}
    for e in data["entries"]:
        assert e["row"] in rows
        assert e["reason"] and e["clears_when"] and isinstance(e["ledger"], int)
        assert e["state"] in (B.BROKEN, B.UNKNOWN, B.UNPROVEN)


def test_g1_rows_measure_on_the_live_first_pass_basis(tmp_path):
    """The board must measure what the live gate measures: its numpy G1 values
    equal lw_first_pass.compute_numpy_metrics on the same pair (the golden
    freeze uses a different, PIL-'L' basis - docs/GATE_BOARD.md finding 7)."""
    import lw_first_pass
    from PIL import Image
    subj = _g1_subject(60)
    sp, op = tmp_path / "s.png", tmp_path / "o.png"
    Image.fromarray(subj["source_rgb"]).save(sp)
    Image.fromarray(subj["output_rgb"]).save(op)
    lap, halo, _band = lw_first_pass.compute_numpy_metrics(str(sp), str(op))
    assert B._g1_value("lap_ratio")(subj) == pytest.approx(lap, rel=1e-9)
    assert B._g1_value("halo_pct")(subj) == pytest.approx(halo, abs=1e-9)


def test_band_delta_arm_retired_with_its_ack_entry():
    """R1b (LEDGER 265): the blind G1.band_delta row is gone from the board and
    its acknowledgement left config/gate_board_ack.json in the same change;
    G1.cambi_delta carries the banding fault."""
    names = {r.name for r in B.lw_board().rows}
    assert "G1.band_delta" not in names
    assert "G1.cambi_delta" in names
    ack = json.loads((Path(B.ROOT) / "config" / "gate_board_ack.json")
                     .read_text(encoding="utf-8"))
    assert all(e["row"] != "G1.band_delta" for e in ack["entries"])
    with pytest.raises(KeyError):
        B._g1_value("band_delta")
