"""Both LW dashboards answer /api/version through the shared scaffold (P0-5)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools import lw_httpd, lw_monitor, lw_rundash  # noqa: E402


def test_rundash_hashes_its_loop_config(tmp_path, monkeypatch):
    monkeypatch.setattr(lw_httpd, "git_head", lambda: "c" * 40)
    cfg = tmp_path / "c.json"
    cfg.write_text("{}", encoding="utf-8")
    srv = lw_rundash.RunDashServer(("127.0.0.1", 0), lw_rundash.Handler, config_path=cfg,
                                   control_dir=tmp_path, repo_root=tmp_path, cache={})
    try:
        assert srv.version_info["commit"] == "c" * 40
        assert srv.version_info["config_hash"] == lw_httpd.config_hash([cfg])
    finally:
        srv.server_close()


def test_monitor_reports_a_version(tmp_path, monkeypatch):
    monkeypatch.setattr(lw_httpd, "git_head", lambda: "d" * 40)
    srv = lw_monitor.MonitorServer(("127.0.0.1", 0), lw_monitor.Handler,
                                   state_path=tmp_path / "s.json", cache={})
    try:
        assert srv.version_info["commit"] == "d" * 40
    finally:
        srv.server_close()
