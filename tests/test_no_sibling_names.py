"""RRF-3.2 (MAIN README-AUDIT 3.2): sibling trees by CODE, never by display name.

MAIN's 2026-10-08 audit counted sibling display names in 48 / 17 / 14 / 11 / 10
tracked files (RC / LL / RSC / CS / SS). The channel names a tree by its two-
to-three letter code and nothing else (docs/CHANNEL.md section 0). The rule:
no tracked file outside docs/_archive/ spells a sibling's display name.

HASH-PINNED. The name list cannot live in a tracked file as text - it would be
the very thing the guard forbids - so tools/sibling_names.py pins sha256 over
each name's squashed key (lowercase, alphanumerics only). The fixtures below
build each name from fragments for the same reason.

Matched: one token, or two adjacent tokens joined by a space, "-" or "_",
whose squashed key hashes to a pin, in any case - except the two names that are
also English nouns, which need a capital (LEDGER 2108).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import gitdep
import pytest
import tracked_corpus

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import sibling_names as sn  # noqa: E402

# Fragments, so no display name is spelled in this file.
PLANTED = {
    "RC": ["Riot" + " " + "Commander", "Riot" + "-" + "Commander", "Riot" + "Commander",
           "RIOT" + " " + "COMMANDER", "Amber" + "stone"],
    "RSC": ["Resin" + " " + "Compute", "Resin" + "Compute"],
    "RM": ["Red" + " " + "Moon"],
    "LL": ["Lantern" + "light", "Lantern" + " " + "Light"],
    "CS": ["Clock" + "speed"],
    "SS": ["Sub" + "strate"],
    "EW": ["Ebon" + "wake"],
}


def test_a_lowercase_spelling_fires_except_for_the_two_nouns():
    assert sn.find("c--" + "clock" + "speed\n") == [(1, "CS")]
    assert sn.find("x_" + "riot" + "_" + "commander_y\n") == [(1, "RC")]
    assert sn.find("sub" + "strate\n") == []


@pytest.mark.parametrize("code,name", [(c, n) for c, ns in PLANTED.items() for n in ns])
def test_every_spelling_of_every_pinned_name_fires(code, name):
    text = f"x\nsee {name}'s tree at C:\\{name}\\ops and C--{name.replace(' ', '-')}\n"
    hits = sn.find(text)
    assert hits and {c for _ln, c in hits} == {code}
    assert {ln for ln, _c in hits} == {2}


def test_codes_and_the_english_noun_do_not_fire():
    text = ("RC CS LL RSC RM SS EW MAIN LW\n"
            "a research " + "sub" + "strate, a blood-" + "red" + " " + "moon\n"
            "Legion Wallpaper is this tree, not a sibling\n")
    assert sn.find(text) == []


def test_the_pins_are_hashes_and_every_code_has_one():
    assert set(sn.PINS) == set(PLANTED)
    for code, pins in sn.PINS.items():
        assert pins, code
        assert all(re.fullmatch(r"[0-9a-f]{64}", p) for p in pins), code
    src = (ROOT / "tools" / "sibling_names.py").read_text(encoding="utf-8")
    assert sn.find(src) == [], "the pin module spells a name it pins"


def test_sibling_dir_resolves_by_key_whatever_the_spelling(tmp_path, monkeypatch):
    monkeypatch.setenv("LW_SIBLINGS_DIR", str(tmp_path))
    (tmp_path / "Other Tree").mkdir()
    assert sn.sibling_dir("RC").parent == tmp_path
    assert not sn.sibling_dir("RC").exists()           # absent: a CI runner
    real = tmp_path / ("Riot" + "-" + "Commander")
    (real / ".git").mkdir(parents=True)
    assert sn.sibling_dir("RC") == real
    with pytest.raises(KeyError):
        sn.sibling_dir("NOPE")


def test_the_sweep_skips_the_archive_and_binaries(tmp_path):
    name = "Clock" + "speed"
    files = {"docs/_archive/2026-09/x.md": f"{name}\n".encode(),
             "img.bin": b"\0\0" + name.encode(),
             "docs/live.md": f"ok\n{name}\n".encode()}
    hits = sn.sweep(list(files), files.__getitem__)
    assert hits == [("docs/live.md", 2, "CS")]


def test_the_pre_push_hook_runs_the_sweep():
    hook = (ROOT / ".githooks" / "pre-push").read_text(encoding="utf-8")
    assert re.search(r'tools/sibling_names\.py" sweep \|\| exit 1', hook)


@gitdep.requires_git
def test_no_tracked_file_outside_the_archive_spells_a_sibling_name():
    files = tracked_corpus.tracked_files()
    assert len(files) > 100

    def read(rel):
        try:
            return tracked_corpus.read_bytes(rel)
        except OSError:
            return b""
    hits = sn.sweep(files, read)
    assert hits == [], "sibling display names (use the code): " + ", ".join(
        f"{r}:{ln} {c}" for r, ln, c in hits[:40]) + f" ({len(hits)} total)"
