"""Re-export of the committed cross-score tally so the panel scripts can import
it as `tally` from this directory. The implementation lives one level up in
`docs/_crossscore_tally.py`; this file exists only so that
`sys.path.insert(0, HERE); import tally` resolves.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from _crossscore_tally import (  # noqa: E402,F401
    IN_FAMILY, OUT_FAMILY, PREV, KINDS, EXPECT,
    load_psv, load_rc, rc_norm, pct,
)

SCRATCH = pathlib.Path(__file__).resolve().parent
