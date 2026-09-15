<div align="center">

# Legion Wallpaper

**An AI image restoration pipeline - staged, self-auditing, gate-ladder verified - and the multi-agent Claude Code orchestration system that builds it.**

[![ci](https://github.com/Remus3/Legion-Wallpaper/actions/workflows/ci.yml/badge.svg)](https://github.com/Remus3/Legion-Wallpaper/actions/workflows/ci.yml)
[![License: Apache 2.0](https://img.shields.io/badge/license-Apache_2.0-blue.svg)](LICENSE)
[![Python 3.14](https://img.shields.io/badge/python-3.14-3776AB.svg)](https://www.python.org/)
[![platform: Windows](https://img.shields.io/badge/platform-Windows-0078D6.svg)](#requirements)
[![decisions: 12 ADRs](https://img.shields.io/badge/decisions-12%20ADRs-6f42c1.svg)](docs/adr/)
[![tests: 2.9k arms](https://img.shields.io/badge/tests-2.9k%20arms-2ea44f.svg)](tests/)

</div>

Drop an illustration into `images\0.Originals`. The pipeline finds the best
full-resolution source, upscales it exactly once with an illustration-tuned
super-resolution model, removes watermarks and generation artifacts by masked
LaMa inpainting, repairs anime faces and eyes, audits its own output at every
stage through a metric-plus-vision gate ladder, and delivers an approved
2560x1440 PNG.

Nothing advances on an unbacked claim. Autonomy is earned through a calibration
ladder - shadow, then spot-check, then full auto - and every promotion is backed
by a measured census.

## The pipeline

```mermaid
flowchart LR
  A["<b>0</b><br/>Originals"] --> B["<b>1-2</b> First Pass<br/><i>source recovery<br/>ONE upscale</i>"]
  B --> C["<b>3-4</b> Cleaning<br/><i>watermark and<br/>artifact inpaint</i>"]
  C --> D["<b>5-6</b> Final<br/><i>face + eye repair<br/>2560x1440</i>"]
  D --> E["<b>7</b> Last Pass<br/><i>fresh-eyes<br/>regression</i>"]
  E --> F["<b>8</b> End Review<br/><i>deep audit<br/>per milestone</i>"]
  F --> G["<b>9</b> Backup<br/><i>and delivered</i>"]
  style A fill:#1f6feb,color:#fff,stroke:none
  style G fill:#2ea44f,color:#fff,stroke:none
```

Ten numbered stage folders under `images\`, each a scratch/done pair, with an
append-only transition log and an atomic state file. Every advance is gated:

| Gate | Asks |
|---|---|
| **G0** intake | Is this file real, stable, and worth a slot? |
| **G1** fidelity | Full-reference metrics (MS-SSIM, LPIPS, DISTS) at a common scale, plus sharpness and halo checks |
| **G2** style | Does the result still look like the corpus it came from? |
| **Vision** | A Claude reviewer that may FLAG but never REJECT ([ADR-008: a reviewer may flag, never reject](docs/adr/ADR-008-vision-reviewer-flags-never-rejects.md)) |

A rejection demotes the image to the previous stage with the reason logged, or
routes it to a human QA queue. The single-writer rule has no exceptions:
`lw_pipeline` moves images, never a hand-drag in Explorer.

## Where it stands

_Probed live 2026-09-14. A static status table goes stale, so the machine-readable version is `ops/runtime/pipeline_state.json`, refreshed by `lw_pipeline scan`._

| Area | Status |
|---|---|
| **Running on the corpus** | Intake, source recovery, first pass (spandrel DAT2 super-resolution plus the G1 fidelity gate), and cleaning (detect, mask, LaMa inpaint, verify, with IOPaint as the human QA lane) |
| **Built, not yet exercised end to end** | Final pass, last pass and end review are coded, tested and gated, but no image has been carried through to delivery yet |
| **Corpus** | 713 tracked illustrations on one Windows workstation: 517 through cleaning, 70 in cleaning scratch, 118 in first pass, each with a retained milestone snapshot set |
| **Code** | 98 tools, 145 test files, 2,938 test arms, 12 ADRs, 201 ledger items, 571 commits |
| **Autonomy** | Phase A (shadow). Promotion needs a window of 50 or more operator-reviewed images |

## What is next

The roadmap lives in [`ROADMAP.md`](ROADMAP.md), highest priority at the top.
The headline items:

- **Carry the first image through stages 5 to 9.** The back half of the ladder
  has never run on a real submission. That is the next proof the product owes.
- **Earn autonomy phase B.** Accumulate the shadow window, then promote by the
  calibration ladder rather than by confidence.
- **Gate `dists` on something.** It is computed on every audit and binds nothing.
- **An art-damage measure for `scoped_revert`.** Cleaning can win on seam and
  lose on art. Today only the first half is measured.
- **One glyph engine.** The banned-glyph rule is declared in three places. They
  agree today, and nothing makes them agree tomorrow.
- **Package the process as the deliverable.** Pipeline, gate ladder, rubric,
  golden-set protocol and manifests. Never the images.
- **The tooling-tier lane.** Five sibling agent projects each audited their own
  history for "done" claims that a later session refuted, then asked what share
  a better gate or a tighter contract would have caught. Four landed on 78 to 83
  percent; one dissents hard at 31. No tooling gets built until that
  disagreement is resolved, because the lane is only worth it if the answer is
  high.

## What is reusable

The corpus stays private. The process is what ships: a Claude Code agent
operating system - orchestrator, worktree subagents, hooks and gates - that is
not specific to images at all.

| Piece | Where | What it does |
|---|---|---|
| **Agent operating contract** | `CLAUDE.md` | The rules, tiers, gates and rituals an AI agent must follow to work in this repo |
| **Multi-agent framework** | `docs/AGENTS.md`, `.claude/` | Orchestrator plus worktree subagent slices plus a read-only verifier that must CONFIRM before any merge |
| **Verifier subagent** | `.claude/agents/verifier.md` | Independently re-runs the suite and tries to falsify an implementing agent's "green" claim |
| **Commit and hygiene gates** | `tools/precommit_gate.py`, `tools/install_git_hooks.py` | Blocks banned glyphs and net-new lint on staged lines. `--check` proves the hooks actually fire |
| **Drift guard** | `tools/drift_guard.py` | Wrap-up probe for doc and repo drift: budgets, memory index, cited SHAs, untracked authored files, and whether the hooks fire |
| **Agent-config scanner** | `tools/drift_guard.py` | Parses `.claude/settings.json` (invalid JSON is a breach, since an unparsed config presents exactly as one with no hooks) and reports directories whose `~/.claude.json` spellings disagree on trust |
| **Publication guards** | `tests/test_no_secret_literals.py`, `tests/test_no_account_paths.py`, `tests/test_no_split_identity.py` | Sweep every tracked file for credential literals, account home paths and personal identity, including values split across lines or written in reverse. Pinned by sha256, never spelled out |
| **Headless run loop** | `ops/loop/` | Self-continuing `claude -p` executor with slot arbitration and a truth gate |
| **Pipeline state machine** | `tools/lw_pipeline.py` | Atomic stage transitions, per-image manifests, append-only transition log |

The recurring theme: **an agent's claim is not evidence.** Most of the code
above exists to make a machine prove its own work before a human is asked to
believe it. The same instinct runs through the publication guards, which pin
every forbidden value by hash rather than writing it down, because a guard that
names what it forbids publishes it.

## Decisions are written down, including the wrong ones

Every choice with lasting consequences becomes a numbered ADR in
[`docs/adr/`](docs/adr/): the folder and state scheme, the upscaler chosen on a
golden A/B sweep, signature removal, the comparison pixel budget, one cleaning
engine per submission.

[ADR-010: switch the SDXL generator base](docs/adr/ADR-010-gen-base-realvisxl.md)
flipped the image-generation base after a CLIP similarity measure ranked a
challenger first.
[ADR-011: put the base back](docs/adr/ADR-011-gen-base-stays-animagine.md)
reversed it the same day, once someone looked at the frames: the measure reads rendering register and is
blind to hands, weapon canon and likeness, so it had ranked the two failing
bases above the working one. A number that disagrees with the pixels loses, and
the losing number stays in the record.

## The images are not here

They never will be. The wallpapers are third-party illustrations, `images/**` is
gitignored, and the restored output stays private. What this repo publishes is
the pipeline code, the gate ladder, the golden-set regression protocol, the
provenance manifests, and the agent operating system that produced all of it.

## Requirements

Windows, Python 3.14, and GPU-backed super-resolution and inpainting virtualenvs
provisioned outside the repo (spandrel plus torch for upscaling, LaMa and
IOPaint for cleaning, ComfyUI with an SDXL illustration checkpoint for face
repair and generation). Built around one machine, one corpus and one operator:
treat it as a reference implementation, not a turnkey tool.

The three commands that drive everything:

```powershell
python tools\lw_pipeline.py scan      # refresh pipeline_state.json
python tools\lw_pipeline.py status    # per-stage counts and the needs-attention list
python tools\lw_pipeline.py intake --all   # pull new files out of 0.Originals
```

[`CONTRIBUTING.md`](CONTRIBUTING.md) states what an invited change would have to
clear. Security or privacy problems go through the private channel in
[`SECURITY.md`](SECURITY.md), never a public issue.

<details>
<summary><b>Where things live</b></summary>

| Surface | Path |
|---|---|
| Operational plan (pipeline, gates, autonomy ladder) | `docs/RESTORATION_PLAN.md` |
| Architecture and module map | `docs/ARCHITECTURE.md` |
| Ops commands and runbook | `docs/OPERATIONS.md` |
| Decisions | `docs/adr/` |
| Roadmap (highest priority at top) | `ROADMAP.md` |
| Aspirational backlog | `BACKLOG.md` |
| Per-item completion ledger (append-only, newest-first) | `docs/LEDGER.md` |
| Session hand-off notes (newest-first) | `WAKEUP_NOTES.md` |
| Operating rules (per-session auto-load) | `CLAUDE.md` |
| Harness config, hooks, agents, commands | `.claude/` |
| Pipeline stage folders (content gitignored) | `images\0.Originals` .. `images\9.Image Backup` |
| Pipeline machine state (atomic) | `ops/runtime/pipeline_state.json` |
| Pipeline transition log (append-only, gitignored) | `PIPELINE_LOG.md` |
| Runtime health (written by the supervisor, TBD) | `ops/runtime/health.json` |
| Daily logs | `logs/YYYY-MM-DD.log` |

</details>

<details>
<summary><b>How this repo operates</b></summary>

Inherited 1:1 from a prior project
([ADR-001: inherit the operating system](docs/adr/ADR-001-inherit-rc-operating-system.md)) and enforced by
hooks, not by good intentions.

- **TDD, RED first.** Every feature or bugfix starts with a failing test. No
  implementation before the test is observed RED.
- **Tiered verification.** Changes are classified by tier, and each tier carries
  its own mandatory gate, from docs-only up to full suite plus restart plus
  health confirm.
- **Subagent-first delegation.** Non-trivial work fans out to worktree subagent
  slices. An independent read-only verifier must CONFIRM before the orchestrator
  merges, and the orchestrator is the sole merger.
- **Session rituals.** Wake by reading `WAKEUP_NOTES.md` and `ROADMAP.md`. Wrap
  by appending a ledger entry to `docs/LEDGER.md` and syncing the living docs.
- **Ledger discipline.** Every completed item gets a numbered, append-only entry
  in `docs/LEDGER.md`, never in `CLAUDE.md` (it has a hard size budget).
- **7-bit ASCII only** in authored content: no em or en dashes, no smart quotes.

Full rules: [`CLAUDE.md`](CLAUDE.md).

</details>

## License

Apache License 2.0, see [`LICENSE`](LICENSE). The license covers the PROCESS
shipped in this repo: pipeline code, gate ladder, docs, agent framework. It does
not and cannot grant any right to the image corpus.
