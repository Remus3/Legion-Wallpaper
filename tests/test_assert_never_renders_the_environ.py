"""No assert statement may put the process environment in pytest's failure text.

Reported by sibling LL 2026-10-02 and reproduced here before this guard was
written. `assert os.environ.get("NAME") == "false"` does not merely print the
value it fetched: pytest's assertion rewriter explains every Attribute and Call
subexpression inside an assert, so the `.get` attribute access forces a repr of
the `os._Environ` object itself. The whole environment lands in the failure
output. This repo is PUBLIC and CI output is world-readable.

MEASURED on this box, pytest 9.0.3, with a FAKE decoy planted in the
environment (never a real value - see memory
feedback-documenting-a-leak-republishes-it). Counting DISTINCT REAL ENV KEYS
rendered into the FAILURES block, because the two obvious measures each
undercount: a decoy-value grep misses the leak whenever the decoy sorts into
pytest's truncated tail, and an `environ({` grep misses the plain-dict reprs
that a snapshot produces.

    shape                                            keys@-q  keys@-vv
    assert os.environ.get(K) == V                           3        92
    env = os.environ;      assert env.get(K) == V           3        92
    env = os.environ;      assert env == {}                 0        92
    assert "K" in os.environ                                3        92
    assert dict(os.environ) == {}                           5        92
    assert os.environ.keys() ...                            3        92
    assert os.environ["K"] == V                             0         0
    assert os.getenv(K) == V                                0         0
    value = os.environ.get(K); assert value == V             0         0

Two readings of that table matter:

  (a) `-q` (what CI runs) truncates each repr, so it leaks 3 to 5 keys rather
      than 92. Truncation is not a defence - the keys it keeps are simply the
      ones that sort first, and any `-v`/`-vv` run, local or in a re-run job,
      prints all 92 of 102.
  (b) The subscript and `os.getenv` forms measured clean, and one ATTRIBUTE
      form (`os.environ.get(K, "y") == "x"`) also measured clean - but only
      incidentally: a str-vs-str comparison makes pytest print a string diff
      INSTEAD of the where-chain. Change the expected side to `is None` and the
      identical shape leaks 92 keys. So this guard bans the SHAPE and does not
      trust which values happen to print. The one safe rewrite is to bind the
      lookup to a local BEFORE the assert, which denies the rewriter the
      attribute access entirely.

AST, not substring. LL reported their own substring guard holed twice, and LW
carries a standing note that a substring ban is the wrong instrument
(tests/test_lw_rundash.py has a related one). A substring ban on
"os.environ" would miss every alias form and would fire on docstrings - this
file is itself full of the banned text in prose.
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent

# tests/ and tools/ are where asserts live. ops/ is swept too: it measured
# clean, so including it is free coverage rather than a new obligation.
SCAN_DIRS = ("tests", "tools", "ops")

# Vendored trees are excluded: they are not authored here, and a finding in one
# is an upstream report, not an LW fix.
EXCLUDED_PARTS = ("dwpose_onnx", "__pycache__", "site-packages", "node_modules")


def _excluded(path: Path) -> bool:
    parts = path.parts
    return any(p in EXCLUDED_PARTS or p.startswith(".venv") for p in parts)


# Methods whose RESULT is the whole environment, or a full copy or view of it.
# `.get` / `.pop` / `.setdefault` are deliberately absent: their result is ONE
# value, so a name bound from one is not an alias. The attribute access that
# reaches `.get` still leaks, but that is the position rule below, not this one.
WHOLE_ENV_METHODS = ("copy", "keys", "values", "items")


def _is_environ_object(node: ast.AST, aliases: frozenset[str]) -> bool:
    """True if `node` evaluates to the environment, or to a full snapshot of it.

    A snapshot counts: `dict(os.environ)` is a plain dict, so it dodges the
    `environ({...})` spelling in the output while carrying exactly the same
    values into the failure text. Measured: that form leaks 92 of 102 keys.
    """
    if isinstance(node, ast.Attribute):
        # Any `<anything>.environ`, not only `os.environ`, so an indirect
        # module reference (`mod.os.environ`) cannot slip past.
        return node.attr == "environ"
    if isinstance(node, ast.Name):
        return node.id in aliases
    if isinstance(node, ast.Call):
        func = node.func
        if isinstance(func, ast.Name) and func.id in ("dict", "vars") and len(node.args) == 1:
            return _is_environ_object(node.args[0], aliases)
        if isinstance(func, ast.Attribute) and func.attr in WHOLE_ENV_METHODS:
            return _is_environ_object(func.value, aliases)
    return False


def _alias_names(tree: ast.AST) -> frozenset[str]:
    """Names bound to the environment anywhere in the file.

    Deliberately FLAT - no per-scope analysis. A flat name set over-reports
    rather than under-reports, which is the safe direction for a guard: the
    worst case is a spurious red that a rename clears, not a silent leak.
    Iterated to a fixed point so a chained alias (`a = os.environ; b = a`) is
    caught at `b` too.
    """
    aliases: set[str] = set()
    for node in ast.walk(tree):
        # `from os import environ` makes the bare name an alias.
        if isinstance(node, ast.ImportFrom) and node.module == "os":
            for a in node.names:
                if a.name == "environ":
                    aliases.add(a.asname or a.name)
    while True:
        before = len(aliases)
        frozen = frozenset(aliases)
        for node in ast.walk(tree):
            targets: list[ast.AST] = []
            value: ast.AST | None = None
            if isinstance(node, ast.Assign):
                targets, value = list(node.targets), node.value
            elif isinstance(node, ast.AnnAssign) and node.value is not None:
                targets, value = [node.target], node.value
            elif isinstance(node, ast.NamedExpr):
                targets, value = [node.target], node.value
            if value is None or not _is_environ_object(value, frozen):
                continue
            for t in targets:
                if isinstance(t, ast.Name):
                    aliases.add(t.id)
                elif isinstance(t, ast.Tuple):
                    for elt in t.elts:
                        if isinstance(elt, ast.Name):
                            aliases.add(elt.id)
        if len(aliases) == before:
            return frozenset(aliases)


def environ_in_assert_violations(source: str, filename: str = "<src>") -> list[tuple[int, str]]:
    """[(lineno, snippet)] for every assert that can render the environment.

    The rule is the SHAPE plus the POSITION. The environment (or an alias, or a
    snapshot) may not appear inside an `assert` statement in any position
    pytest's rewriter explains. Exactly one position is carved out, and it is
    carved out on a measurement rather than on reasoning: the BASE OF A
    SUBSCRIPT. `assert os.environ["K"] == "v"` leaks 0 keys at both `-q` and
    `-vv`, and so do the alias (`env["K"]`) and snapshot (`dict(os.environ)`
    then `env["PATH"]`) spellings of it. pytest does not repr the object a
    subscript is taken from.

    One deliberate OVER-report, kept because the safe direction is to flag:
    in the assert MESSAGE, a single-value lookup (`assert c, os.environ.get(K)`)
    measured clean, because the message is not rewritten - but interpolating
    the whole environment there (`assert c, f"{os.environ}"`) leaks 92 keys.
    Rather than model which message expressions are safe, both are flagged. The
    fix is the same one line either way.

    WHAT THIS DOES NOT CATCH, and why that is accepted:
      - an environment reached through a FUNCTION RETURN
        (`def e(): return os.environ` then `assert e().get(K)`). Catching it
        needs interprocedural analysis; the repo has no such call site, and the
        arms below pin that this gap is known rather than assumed absent.
      - an environment stored on an ATTRIBUTE (`self.env = os.environ` then
        `assert self.env.get(K)`). Only Name targets are tracked as aliases.
        Partly mitigated: any `.environ` attribute access inside an assert is
        flagged whatever its base, so the common spelling is still caught.
      - dynamic access (`getattr(os, "environ")`, `vars(os)["environ"]`).
      - a third-party object whose own __repr__ embeds the environment.
    Each of those is a leak if it ever appears. None is in the tree today, and
    all three are strictly harder to write by accident than the forms above.
    """
    tree = ast.parse(source, filename=filename)
    aliases = _alias_names(tree)
    out: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assert):
            continue
        parents: dict[int, ast.AST] = {}
        for parent in ast.walk(node):
            for child in ast.iter_child_nodes(parent):
                parents[id(child)] = parent
        for sub in ast.walk(node):
            if sub is node or not _is_environ_object(sub, aliases):
                continue
            parent = parents.get(id(sub))
            if isinstance(parent, ast.Subscript) and parent.value is sub:
                continue  # measured clean - pytest does not repr a subscript base
            out.append((node.lineno, ast.unparse(node)[:120]))
            break
    return sorted(set(out))


def _scanned_files() -> list[Path]:
    files: list[Path] = []
    for d in SCAN_DIRS:
        base = ROOT / d
        if not base.is_dir():
            continue
        files.extend(p for p in sorted(base.rglob("*.py")) if not _excluded(p))
    return files


def test_the_sweep_actually_finds_files():
    """A sweep over an empty list is a pass that asserts nothing."""
    files = _scanned_files()
    assert len(files) > 100, f"only {len(files)} files scanned - the sweep is not reaching the tree"
    names = {p.name for p in files}
    assert "test_no_venv_mutation.py" in names
    assert "lw_paths.py" in names


def test_no_assert_in_the_tree_can_render_the_environment():
    found: list[str] = []
    for path in _scanned_files():
        try:
            src = path.read_text(encoding="utf-8", errors="replace")
        except OSError:  # pragma: no cover - unreadable file is not our finding
            continue
        for lineno, snippet in environ_in_assert_violations(src, str(path)):
            found.append(f"{path.relative_to(ROOT).as_posix()}:{lineno}  {snippet}")
    assert not found, (
        "these asserts can render the whole process environment into pytest's "
        "failure output, and this repo is PUBLIC:\n  " + "\n  ".join(found)
        + "\nFix: bind the lookup to a local FIRST, then assert on the local.")


# ---- does the detector bind? positive and negative arms --------------------
#
# A guard nobody has seen fail asserts nothing. These arms are the mutants,
# carried in-file so they run on every suite rather than once by hand.

LEAKING_SHAPES = [
    pytest.param("import os\ndef t():\n    assert os.environ.get('K') == 'v'\n", id="attr-get"),
    pytest.param("import os\ndef t():\n    assert os.environ.get('K', 'd') is None\n", id="attr-get-default"),
    pytest.param("import os\ndef t():\n    assert 'K' in os.environ\n", id="in-environ"),
    pytest.param("import os\ndef t():\n    assert os.environ.keys()\n", id="keys"),
    pytest.param("import os\ndef t():\n    assert dict(os.environ) == {}\n", id="dict-snapshot"),
    pytest.param("import os\ndef t():\n    e = os.environ\n    assert e.get('K') == 'v'\n", id="alias-get"),
    pytest.param("import os\ndef t():\n    seen = os.environ\n    assert seen is not None\n", id="alias-is-not-none"),
    pytest.param("import os\ndef t():\n    seen = os.environ\n    assert seen == {}\n", id="alias-bare"),
    pytest.param("import os\ndef t():\n    a = os.environ\n    b = a\n    assert b.get('K')\n", id="alias-chained"),
    pytest.param("import os\ndef t():\n    e = dict(os.environ)\n    assert e == {}\n", id="alias-snapshot"),
    pytest.param("import os\ndef t():\n    e = os.environ.copy()\n    assert e == {}\n", id="alias-copy"),
    pytest.param("from os import environ\ndef t():\n    assert environ.get('K') == 'v'\n", id="from-import"),
    pytest.param("import os\ndef t():\n    assert c, f'{os.environ}'\n", id="whole-env-in-the-message"),
    pytest.param("import os\ndef t():\n    assert c, os.environ.get('K')\n", id="message-conservative"),
    pytest.param("import os\ndef t():\n    assert (e := os.environ) and e.get('K')\n", id="walrus"),
]

# Every entry here is MEASURED at 0 leaked keys at both -q and -vv. The
# subscript rows are the carve-out in the detector; the rest are the rewrites
# this guard is pushing people towards.
CLEAN_SHAPES = [
    pytest.param("import os\ndef t():\n    v = os.environ.get('K')\n    assert v == 'v'\n", id="bound-local"),
    pytest.param("import os\ndef t():\n    assert os.getenv('K') == 'v'\n", id="getenv"),
    pytest.param("import os\ndef t():\n    env = dict(os.environ)\n    run(env=env)\n", id="snapshot-not-asserted"),
    pytest.param("import os\nR = os.environ.get('K')\ndef t():\n    assert R == 'v'\n", id="module-level-lookup"),
    pytest.param("import os\ndef t():\n    assert os.environ['K'] == 'v'\n", id="subscript-direct"),
    pytest.param("import os\ndef t():\n    e = os.environ\n    assert e['K'] == 'v'\n", id="subscript-alias"),
    pytest.param("import os\ndef t():\n    e = dict(os.environ)\n    assert e['K'] == 'v'\n", id="subscript-snapshot"),
]


@pytest.mark.parametrize("src", LEAKING_SHAPES)
def test_the_detector_flags_every_leaking_shape(src):
    assert environ_in_assert_violations(src), "detector missed a shape measured to leak"


@pytest.mark.parametrize("src", CLEAN_SHAPES)
def test_the_detector_does_not_flag_a_clean_shape(src):
    got = environ_in_assert_violations(src)
    assert got == [], f"detector over-reported a clean shape: {got}"


def test_the_known_gaps_are_gaps_on_purpose():
    """Pins the three forms the docstring says are NOT caught.

    If a later change starts catching one, this arm goes red and the docstring
    gets corrected - rather than the docstring quietly over-claiming.
    """
    uncaught = [
        "import os\ndef e():\n    return os.environ\ndef t():\n    assert e().get('K')\n",
        "import os\nclass C:\n    def s(self):\n        self.env = os.environ\n    def t(self):\n        assert self.env.get('K')\n",
        "import os\ndef t():\n    assert getattr(os, 'environ').get('K')\n",
    ]
    for src in uncaught:
        assert environ_in_assert_violations(src) == [], (
            "this form is now caught - widen the guard's docstring to say so")
