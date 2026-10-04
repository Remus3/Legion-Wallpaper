"""Admit this machine's tailnet name to the lw_httpd Host guard (phone access).

The review bench stays bound to 127.0.0.1. The operator exposes it to their own
tailnet devices with `tailscale serve`, which proxies requests with the
machine's tailnet DNS name as Host - a name the loopback-only guard refuses.
This tool reads that name from `tailscale status --json` (Self.DNSName, read
only - it never changes Tailscale config) and writes it to the GITIGNORED
local/httpd_allowed_hosts.json; lw_httpd admits it at the next server start.
The name identifies the tailnet account, so it never goes into a tracked file.

  python tools/lw_tailnet_host.py          # write the allowlist, print the next steps
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import lw_httpd  # noqa: E402

NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)
TAILSCALE = Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "Tailscale" / "tailscale.exe"
MONITOR_PORT = 8901


def tailnet_name(status_json=None):
    """Self.DNSName without the trailing dot, lowercased, or None."""
    if status_json is None:
        try:
            r = subprocess.run([str(TAILSCALE), "status", "--json"], capture_output=True,
                               text=True, timeout=30, creationflags=NO_WINDOW)
        except (OSError, subprocess.SubprocessError):
            return None
        if r.returncode != 0:
            return None
        status_json = r.stdout
    try:
        name = json.loads(status_json).get("Self", {}).get("DNSName", "")
    except (ValueError, AttributeError):
        return None
    name = str(name).strip().lower().rstrip(".")
    return name if lw_httpd._TAILNET_RE.match(name) else None


def write_allowlist(name, path=lw_httpd.ALLOWED_HOSTS_PATH):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps({"hosts": [name]}, indent=1) + "\n", encoding="ascii")
    os.replace(tmp, path)
    return path


def main(argv=None):
    name = tailnet_name()
    if name is None:
        print("tailscale status gave no tailnet name (is Tailscale running and logged in?)")
        return 2
    write_allowlist(name)
    print("allowlist written (gitignored local/httpd_allowed_hosts.json); restart the monitor.")
    print(f'operator runs ONCE: "{TAILSCALE}" serve --bg http://127.0.0.1:{MONITOR_PORT}')
    print(f"phone opens: https://{name}/review")
    return 0


if __name__ == "__main__":
    sys.exit(main())
