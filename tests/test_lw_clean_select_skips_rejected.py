"""select_working_image must skip a working the operator REJECTED (2026-10-04)."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import lw_clean_pass as lcp  # noqa: E402


def test_highest_working_is_skipped_when_rejected(tmp_path: Path):
    d = tmp_path / "s"
    d.mkdir()
    (d / "s_cleaninitial.png").write_bytes(b"init")
    (d / "s_cleanworking_01.png").write_bytes(b"ok")
    (d / "s_cleanworking_02.png").write_bytes(b"bad")
    sha = hashlib.sha256(b"bad").hexdigest()
    (d / "manifest.json").write_text(json.dumps({"transitions": [
        {"op": "REJECT", "sha256_in": sha, "sha256_out": sha}]}), encoding="utf-8")
    assert Path(lcp.select_working_image(str(d), "s")).name == "s_cleanworking_01.png"


def test_all_rejected_falls_back_to_the_initial(tmp_path: Path):
    d = tmp_path / "s"
    d.mkdir()
    (d / "s_cleaninitial.png").write_bytes(b"init")
    (d / "s_cleanworking_01.png").write_bytes(b"bad")
    sha = hashlib.sha256(b"bad").hexdigest()
    (d / "manifest.json").write_text(json.dumps({"transitions": [
        {"op": "REJECT", "sha256_in": sha}]}), encoding="utf-8")
    assert Path(lcp.select_working_image(str(d), "s")).name == "s_cleaninitial.png"
