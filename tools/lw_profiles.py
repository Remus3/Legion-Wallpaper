"""Calibration profiles as data with evidence (directive P2-7).

Numbers that depend on the machine - GPU tile sizes, VRAM headroom, and later
UI timings - live in config/profiles/*.json instead of as bare literals:

    {"kind": "gpu", "name": "...",
     "match": {"gpu_name_contains": "RTX 5070", "vram_mib_min": 11000},
     "values": {"upscale_tile": {"value": 512, "evidence": "when + how measured"}},
     "procedure": "the command that re-measures this profile"}

Every value MUST carry an evidence string (load refuses one without). A
profile matches when every `match` key holds for the probed environment; an
unknown environment matches nothing and the caller's default is used, reported
as source "default". Match keys are a closed set (MATCH_KEYS) so a typo is an
error, not a profile that silently never matches.

A profile RECORDS the calibrated value; it does not by itself change a number
the pipeline uses. Moving the upscale tile changes output bytes, so it needs a
golden regress first (tests pin profile == code default until then).

  python tools/lw_profiles.py show
  python tools/lw_profiles.py calibrate-gpu      # measures under .venv-upscale
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROFILES_DIR = ROOT / "config" / "profiles"
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)

MATCH_KEYS = {"gpu_name_contains", "vram_mib_min", "vram_mib_max"}
_ENV_CACHE: dict = {}


class ProfileError(ValueError):
    pass


def _validate(prof, src):
    for k in ("kind", "name", "match", "values", "procedure"):
        if k not in prof:
            raise ProfileError(f"{src}: missing {k}")
    bad = set(prof["match"]) - MATCH_KEYS
    if bad:
        raise ProfileError(f"{src}: unknown match key(s) {sorted(bad)}")
    for key, v in prof["values"].items():
        if not isinstance(v, dict) or "value" not in v:
            raise ProfileError(f"{src}: {key} needs a value")
        if not str(v.get("evidence", "")).strip():
            raise ProfileError(f"{src}: {key} has no evidence")
    return prof


def load_all(profiles_dir=PROFILES_DIR):
    d = Path(profiles_dir)
    if not d.is_dir():
        return []
    out = []
    for p in sorted(d.glob("*.json")):
        try:
            prof = json.loads(p.read_text(encoding="ascii"))
        except (OSError, ValueError) as exc:
            raise ProfileError(f"{p.name}: unreadable ({exc.__class__.__name__})") from None
        out.append(_validate(prof, p.name))
    return out


def environment():
    """{gpu_name, vram_mib} from nvidia-smi, or {} - never raises."""
    if "env" in _ENV_CACHE:
        return dict(_ENV_CACHE["env"])
    env = {}
    try:
        r = subprocess.run(["nvidia-smi", "--query-gpu=name,memory.total",
                            "--format=csv,noheader,nounits"],
                           capture_output=True, text=True, timeout=15,
                           creationflags=NO_WINDOW)
        if r.returncode == 0 and r.stdout.strip():
            name, mem = r.stdout.strip().splitlines()[0].rsplit(",", 1)
            env = {"gpu_name": name.strip(), "vram_mib": int(float(mem.strip()))}
    except (OSError, ValueError, subprocess.SubprocessError):
        env = {}
    _ENV_CACHE["env"] = env
    return dict(env)


def matches(prof, env):
    m = prof["match"]
    if not env:
        return False
    name = str(env.get("gpu_name", ""))
    vram = env.get("vram_mib")
    if "gpu_name_contains" in m and m["gpu_name_contains"].lower() not in name.lower():
        return False
    if "vram_mib_min" in m and (vram is None or vram < m["vram_mib_min"]):
        return False
    if "vram_mib_max" in m and (vram is None or vram > m["vram_mib_max"]):
        return False
    return True


def value(kind, key, default, env=None, profiles_dir=PROFILES_DIR):
    """(value, source): the first matching profile's value, else (default,
    "default")."""
    env = environment() if env is None else env
    for prof in load_all(profiles_dir):
        if prof["kind"] == kind and key in prof["values"] and matches(prof, env):
            return prof["values"][key]["value"], prof["name"]
    return default, "default"


# ---------------------------------------------------------------- calibration
_GPU_PROBE = (
    "import json, sys; sys.path.insert(0, sys.argv[1]); import lw_upscale as up; "
    "print(json.dumps(up.measure_tile_peak(sys.argv[2], sys.argv[3], "
    "[int(t) for t in sys.argv[4].split(',')])))"
)


def calibrate_gpu(src, model, tiles=(256, 384, 512, 768), py=None):
    """Measure peak VRAM + time per tile size under .venv-upscale (which owns
    the GPU lock inside upscale_spandrel). Returns the rows; the caller writes
    the evidence string from them."""
    py = Path(py) if py else ROOT / ".venv-upscale" / "Scripts" / "python.exe"
    r = subprocess.run([str(py), "-c", _GPU_PROBE, str(ROOT / "tools"), str(src), str(model),
                        ",".join(str(t) for t in tiles)],
                       capture_output=True, text=True, timeout=3600, creationflags=NO_WINDOW)
    if r.returncode != 0:
        raise ProfileError(f"calibration failed: {(r.stderr or '').strip().splitlines()[-1:]}")
    return json.loads(r.stdout.strip().splitlines()[-1])


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(prog="lw_profiles")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("show")
    c = sub.add_parser("calibrate-gpu")
    c.add_argument("--src", required=True, help="a golden first-pass input")
    c.add_argument("--model", required=True)
    c.add_argument("--tiles", default="256,384,512,768")
    c.add_argument("--python", default=None, help=".venv-upscale interpreter (default: this tree's)")
    a = ap.parse_args(argv)
    if a.cmd == "show":
        env = environment()
        print(json.dumps({"environment": env}))
        for prof in load_all():
            print(f"{prof['kind']}/{prof['name']} match={matches(prof, env)}")
            for k, v in prof["values"].items():
                print(f"  {k} = {v['value']}  ({v['evidence']})")
        return 0
    rows = calibrate_gpu(a.src, a.model, tuple(int(t) for t in a.tiles.split(",")), a.python)
    print(json.dumps({"measured": time.strftime("%Y-%m-%d"), "environment": environment(),
                      "rows": rows}))
    return 0


if __name__ == "__main__":
    os.environ.setdefault("PYTHONIOENCODING", "ascii")
    sys.exit(main())
