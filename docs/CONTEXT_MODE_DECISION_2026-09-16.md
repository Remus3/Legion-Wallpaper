# context-mode: licence settled, blast radius measured, wiring HELD

**Date:** 2026-09-16
**Status:** Decision recorded. Nothing is wired into LW. One thing WAS done -
an isolated local install in a scratch directory outside the repo, to turn an
inferred claim into a measured one. It is named below with how to remove it.

The operator queued `mksglu/context-mode` on 2026-09-15 to implement. The
`ROADMAP.md` entry set two gates before anything else: the licence, and the
blast radius. Both are now answered, one of them by measurement rather than by
reading. The wiring is where this stops, and the reason is stated rather than
implied.

## Gate 1 - the licence. SETTLED: install-only, track nothing.

Probed live on 2026-09-16, not carried from the handoff: `gh api` still reports
`NOASSERTION`, and the published `package.json` for v1.0.169 resolves it
explicitly - `"license": "Elastic-2.0"`. Source-available, not OSI open source.

USING it on Legion is squarely permitted. VENDORING its source into this
Apache-2.0 PUBLIC tree is the part that would need an ADR, and nothing here
needs that: the default from the ROADMAP entry stands unchanged - install it,
track NOTHING of it, gitignore whatever it drops. `node_modules/` was already
gitignored at `.gitignore:139` before this session, so no new ignore rule was
required and none was added.

## Gate 2 - the blast radius. MEASURED.

The handoff said this one is materially riskier than archify because it
installs hooks and an MCP server and intercepts tool output. That is right, and
the specific shape is worse than the summary suggests.

### What a GLOBAL install does (read at source, rung 2)

`package.json` declares `"postinstall": "node scripts/postinstall.mjs"`. That
script imports `healInstalledPlugins`, `healSettingsEnabledPlugins`,
`healPluginJsonMcpServers` and `sweepStaleMcpJson` from
`scripts/heal-installed-plugins.mjs`, and those functions write:

- `~/.claude/plugins/installed_plugins.json`
- `~/.claude/settings.json` (the `enabledPlugins` key)
- `~/.claude.json` (user-level MCP server registrations)

and delete files under the per-version plugin cache.

All three are USER-LEVEL and shared by every tree on this box - RC, RSC, CS, LL
and LW. `~/.claude.json` is the specific file behind the false-green trap
CLAUDE.md records at 2026-08-01, where LW carried THREE keys for one directory
and headless silently dropped `permissions.allow` until it was found; it is
monitored today by `drift_guard.check_claude_path_keys`. A tool whose INSTALLER
rewrites that file is not a local decision.

### What a LOCAL install does (measured, rung 4)

The heals are gated behind `isGlobalInstall()`, which returns false unless
`npm_config_global === "true"`. Reading that is rung 3. Proving it is rung 4, so
it was proven:

1. sha256 + size + mtime snapshot of `~/.claude.json`,
   `~/.claude/settings.json`, `~/.claude/plugins/installed_plugins.json`,
   `.claude/settings.json` and `CLAUDE.md`.
2. `npm install context-mode@1.0.169` into a scratch directory OUTSIDE the
   repo (the session scratchpad), never into the tree. 140 packages, 14s,
   exit 0.
3. Re-snapshot.

**Result: 5 of 5 unchanged.** A local install touches no machine-wide Claude
config. No idle control was needed for this one: the result is negative, and a
daemon running in the background can only ADD a difference, never hide one.

### What WIRING it would do

The CLI bundle writes `~/.claude/settings.json` (taking a `.bak` first),
`.mcp.json` and `settings.local.json`. It READS `CLAUDE.md` as an instruction
file for context injection - it does not overwrite it, which is better than the
handoff feared, but LW's `.claude/settings.json` IS tracked and IS the
operating contract, and it carries five hook classes.

## Why the wiring is held

Three reasons, in the order they bind.

1. **The effect cannot be observed in the session that makes the change.**
   Hooks and MCP servers are loaded at session start. Wiring it now would
   commit a change to every FUTURE session's tool-output path while being
   unable to run the deliberate gate-should-FAIL probe against the wired state.
   The ROADMAP entry asks for exactly that probe, and honouring it means the
   wiring and the proof belong in one session that can restart into the wired
   config - not this one.

2. **It is "always substantial" under the protocol adopted an hour earlier.**
   `.claude/commands/adversarial-review.md` names the hook config explicitly in
   its never-overridable list. Shipping the wiring without that review would be
   the first change to walk past a gate LW adopted the same day.

3. **The benefit is a vendor claim.** The 98 pct reduction is theirs, from
   their `BENCHMARK.md`. If it matters here it gets measured on LW's own
   traffic, in-process, with an idle control - a before/after diff on a box
   running four scheduled `LW-*` tasks attributes nothing.

## The gate probes the ROADMAP demanded, run anyway

Run after the local install, because presence is never proof:

- `python tools/install_git_hooks.py --check` -> `git-hook gate active and
  correctly invoked`, exit 0.
- Deliberate should-FAIL: a staged file carrying an em-dash. First attempt used
  `--staged`, a flag `precommit_gate.py` does not have; it fell through to the
  stdin path, found no commit command and returned 0 - **a silent pass that
  looked like a green gate**. That is DC-01 in `docs/DEFECT_CLASSES.md`
  reproducing itself live inside the probe written to catch it, and it is the
  clearest possible argument for the rule it came from. Re-run correctly via
  `--git-hook`, and then through a REAL `git commit`: both BLOCKED, exit 2, and
  `git log` confirms no probe commit exists.

## Cleanup

The isolated install lives in this session's scratchpad, outside the repo, and
the scratchpad is ephemeral. Nothing in `C:\Legion Wallpaper` references it, no
file was added to the tree, and `git status` was clean across the probe.

## Next, for whoever picks this up

Decide whether LW wants it at all, knowing the shape above. If yes: wire it in
a session that can restart into the wired config, run the should-FAIL probe
AFTER the restart, and measure the reduction on LW's own traffic against an
idle control. The machine-wide form stays a sync-inbox matter - the REVIEW note
sent to all four sibling trees on 2026-09-16 asks the fleet whether a shared
`~/.claude/skills` surface should exist at all, and a no-reply reads as no.
