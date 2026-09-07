# WAKEUP_NOTES - LW hand-off ledger

---

## 2026-09-06 - root renamed to "C:\Legion Wallpaper", RM replaced by RSC

Commits 1ef672e (inbox) and 81de837 (rename), both pushed. Suite green: ruff
clean, 2501 passed, 19 skipped.

**Two spellings, both deliberate - do not "fix" either.** The local root is
`C:\Legion Wallpaper` WITH A SPACE. The GitHub repo is `Remus3/Legion-Wallpaper`
with a HYPHEN, because a repo name cannot hold a space. The agent project slug
`C--Legion-Wallpaper` is unchanged, since the slug hyphenates the space anyway.
Rule of thumb: a filesystem path is anchored on `C:`; a bare `Legion-Wallpaper`
token is the repo name. Any NEW hardcoded path needs QUOTING - an unquoted
`-File C:\Legion Wallpaper\tools\x.ps1` is read as `-File C:\Legion` plus a
stray positional, and fails silently.

**drift_guard WILL report a slots.py divergence between LW and RC. That is
correct and expected - do NOT revert it.** Red Moon is archived read-only and
its working copy deleted; Resin Compute took the vacated third slot in the
concurrency governor. LW authored the new bytes (docstring only, line 5,
`MAX_CONCURRENT_SLOTS` still 3) and re-pinned from its own disk:

    1c4f8af43ff349709c11bf3fe622e922b24cb720771c49a522b13a4d5e58c492
    previous 5297f2d041030398a9ba240aad527b2b01a86d6e7f57a196719af8f0a91cb0a6

RC copies those bytes verbatim next; RSC lands its vendored copy LAST, being
the only participant with no pin to break. The flip cannot be atomic. Replies
explaining the sequencing are in RC's and RSC's `moon_sync_inbox`.

Also landed: `RSC: 8790-8809` recorded in `tools/lw_ports.py` FORBIDDEN (the
seventh block). LW binds nothing in that band - checked against source, the
registry and all three task definitions. `RM: 8770-8789` stays declared even
though Red Moon is gone, because Amberstone's `core/ports.py` still declares
`RM_BLOCK = range(8770, 8790)`.

If the folder move has not run yet: close Claude Code and run
`C:\finish-legion-rename.cmd`. It is idempotent and also repairs the three
agreeing `~/.claude.json` trust spellings, the three `LW-*` scheduled tasks
(quoting `-File` for the space), the agent memory directory, and checks that
all four venvs still resolve.

> Newest-first. Keep only the last 2-3 sessions here at FULL fidelity; archive
> older sessions verbatim to `docs/history_notes.md` (append a pointer line to
> this banner when you prune). Per-item completion records live in
> `docs/LEDGER.md`; open work lives in `ROADMAP.md` + `BACKLOG.md`.
> Archived to `docs/history_notes.md`: the two 2026-07-03 sessions (genesis +
> product-defined, pruned 2026-07-04), 2026-07-04 QA Session 1 (pruned
> 2026-07-05), 2026-07-04 QA Session 2 (pruned 2026-07-07), and the 2026-07-07
> first-pass-queue session + the lw-gen generator-sidecar/deep-research session (both pruned 2026-07-11), and the 2026-07-11 QA-floor calibration + recipe-v2 session (pruned 2026-07-11), and the 2026-07-11 GOLDEN DEFINITION session (pruned 2026-07-12), and the 2026-07-11 M0-foundations + M1-slices-1-2 session (pruned 2026-07-12), and the 2026-07-11 localizer-decision session (pruned 2026-07-12), and the 2026-07-12 M1-weapon-CLIP-gate session (pruned 2026-07-16), and the 2026-07-16 W4-M3 weapon-parked session (pruned 2026-07-16), and the 2026-07-16 Stage-2 cleaning-pipeline session (pruned 2026-07-18), and the 2026-07-27 loop-cycle-11 alpha-audit session (pruned 2026-07-29), and the 2026-08-01 three-repo-N=3 / hook-rule-correction session (pruned 2026-08-01), and the 2026-08-01 (evening) Stage-2-drain / L1 / dashboard-spine session (pruned 2026-08-01), and the 2026-08-01 (night) dashboard-spec-completion session (pruned 2026-08-01), and the 2026-08-01 (earlier) P3/P4/P5 + wiki-swap session and the 2026-08-01 (late) MCP-list/P1 session (both pruned 2026-08-02), and the 2026-08-02 all-five-recommendations/USM-flip/watchdog session (pruned 2026-08-09), and the 2026-08-10/11 intake/retry-degrades session + the 2026-08-11 detector-precision/recall session + the 2026-08-11 (evening) centre-overlay-inpaint session (all three pruned 2026-08-12), and the 2026-08-12 faint-mark REMOVAL lane session (pruned 2026-08-12), and the 2026-08-12 (later) overlay-registration-SCALE session (pruned 2026-08-12), and the 2026-08-12 QA-lane precision-census session (pruned 2026-08-12), and the 2026-08-12 veil-ring session (pruned 2026-08-13), and the 2026-08-12 clean-retry-degrades/one-engine session + the 2026-08-12 bare-pytest-wrong-tree session (both pruned 2026-08-16), and the 2026-08-23 queue-run/revert-lever session (pruned 2026-08-29), and the 2026-08-29 chord-coverage session (pruned 2026-08-29) - keep the last 3.

---

## 2026-09-06 - the license question, answered by refusing its premise

One commit (`511f1d8`) plus a docs sync, all pushed. Suite **2501 passed / 18
skipped / 1 pre-existing GPU failure**, ruff clean, `drift_guard` 0 breaches,
CI green.

- **No license change shipped, and that IS the result. Do not re-open it -
  CLAUDE.md Settled + LEDGER 145 carry the full reasoning.** The operator asked
  MIT vs Apache-2 wanting to block "downloaded + altered + commercialized".
  Both are permissive and both allow exactly that, so the premise was void; the
  governing axis is permissive vs copyleft and neither candidate was on it.
  MIT, GPL-3.0, AGPL-3.0, MPL-2.0, BUSL-1.1, PolyForm NC and the whole CC
  family were each weighed and each lost to the incumbent Apache-2.0.
- **The GPL-3.0 probe was the sharp one and it still came back empty.**
  CC BY-SA 4.0 -> GPLv3 is a real one-way bridge, but LW has nothing to carry
  over it: `data/reference/wiki/` is `render/` + `splash/` IMAGE bytes
  (gitignored, zero tracked) and BY-SA covers wiki TEXT, while the art is Riot
  IP regardless; ComfyUI (GPL-3.0) is a headless SUBPROCESS, which is mere
  aggregation and already fine under Apache-2. Copyleft binds on distribution
  of a combined work only - never subprocess, private use, or optional deps.
- **Visibility is metadata, not license.** All four levers set and verified
  live: description, homepage -> `docs/adr`, 19 topics, and a 1280x640
  social-preview card (`docs/assets/social-preview.png`, self-authored with
  PIL, no corpus bytes). Social preview had to be uploaded by hand - GitHub has
  no REST endpoint for it - and it is CONFIRMED landed because the page serves
  `og:image` from the `repository-images` custom CDN, not the
  `opengraph.githubassets.com` fallback. One topic slot is free.
- **Do NOT redo:** the licensing exploration, the metadata levers, or the
  social preview. All shipped and verified this session.
- **Pre-existing, not mine:** `test_worker_spandrel_branch_produces_both_variants`
  OOMs on an IDLE GPU (11105/12227 MiB free, no compute process), reproduced
  twice. CI never sees it - no CUDA runner. Now tracked as ROADMAP
  `usm-halo-probe-cuda-oom`.
- **Next:** the 123f hand-clean (veil stage) in Photoshop - unchanged from the
  last hand-off, this session never touched it.

---

## 2026-09-05 - three ways to measure a watermark, all refused; plus a live permissions bug

Six commits, all pushed. Suite **2501+ passed / 18 skipped**, ruff clean,
`drift_guard` 0 breaches. CI went RED once and the cause is recorded below -
read it before writing another test that touches machine state.

- **The veil resisted three independent attacks. All three are written up in
  `docs/POOLED_VEIL_RESULT_2026-09-05.md`; do not retry them blind.**
  (1) 62-frame POOLED estimate, 123f held out: registration is NOT the problem
  (every sampled frame at scale 1.00, shift within +-3 px, correlation
  0.35-0.58) and pooling cancels the art cleanly, but the estimators are built
  on `highpass`, which discards the DC band the veil lives in - so it recovers
  EDGES and is blind to the FILL. Applied, it darkened the logo outline and left
  the interior. (2) The operator's ANALYSIS-BY-SYNTHESIS proposal, which is the
  better formulation - a ~12-parameter generator cannot absorb a hand
  reconstruction the way a free per-pixel alpha does - but it needs a matched
  pair and none exists: no clean/watermarked duplicate in the corpus (closest
  consensus distance 18 against accept 8), DA watermarks every render size down
  to the 300px thumb, and two sizes do not separate it because each is
  independently JPEG'd. (3) Shape-from-pool + amplitude-from-ring gave
  **alpha = 0.0578 +- 0.0046 over 62 frames**, matching LEDGER's independent
  ~0.06, and damaged nothing - but it cannot be validated per frame (6 of 62
  frames measure NEGATIVE alpha, and 123f's own step is -1.33 levels, so the
  pooled value over-corrected it).
- **Correction carried from earlier in the session:** a whole-frame
  `residual_mae` of 0.028 does NOT show the hand-clean inverted rather than
  reconstructed - that was dilution over untouched pixels. On touched pixels the
  hand-finished line fits the alpha model NO BETTER than the known-invented LaMa
  layer (7.00 vs 6.12 median levels). Hand-cleans are the ACCEPTANCE TARGET,
  never fitting data.
- **Pulled a canonical wiki reference set for lw-gen (`60461ae`, `17db253`):**
  173 champions x 2 axes, 346/346 files, 0 missing, 1.2 GB in
  `data/reference/wiki/` (gitignored). The champion universe is the
  `OriginalSkin` file, NOT the render category - `Category:Champion renders` is
  incomplete (it omits `Kayle Render.png`, so a render-derived universe lost
  Kayle while keeping four of her forms).
- **Evaluated ECC/AgentShield: declined the framework, took the check list
  (`7ea5707`).** Reasons in the commit body. The mined checks
  (`drift_guard.check_agent_config` + `check_claude_path_keys`) immediately
  found the 2026-08-01 trust-key bug LIVE on two sibling projects - Clockspeed
  [True, True, False] and Lanternlight [True, False], with the SUBSTANTIVE entry
  (30 and 27 fields) untrusted while a 7-field stub held the trust. **Both fixed
  machine-wide; all 7 collision groups now agree.**
- **CI RED, and the lesson is the point.** `test_other_projects_key_collisions`
  read the operator's real `~/.claude.json`, so it passed locally and failed on
  a runner where that file does not exist. Projects are now INJECTED. A local
  green on a test that touches machine state proves nothing about CI.

---

## 2026-09-01 (later) - twenty through first pass, and the watermark under the queue

One commit (`ad99249`), pushed. Suite **2450 passed / 18 skipped** on a fresh
full run (120s) - baseline 2449, +1 for the new regression test. ruff clean,
`verify: ok (604 images checked)` zero mismatches, scan anomalies 0.
Ran `/first-pass` then `/cleaning-pass` over the 24 slugs in scratch.

- **15 slugs reached `4.Cleaning Done` at exactly 2560x1440.** All 20 that
  entered the upscale scored G1 PASS - no FLAG, no FAIL. `clean_done` 492 ->
  507, `clean_scratch` 100 -> 85 (5 new QA + the 80 pre-existing),
  `first_scratch` 24 -> 4.
- **One slug was lost to a quoting bug, not to quality.**
  `deviantart_1375265414_Kai'Sa.jpg` - the apostrophe closed the `r'...'`
  literal in the generated `python -c` snippet and the upscale subprocess died
  on a SyntaxError. Both snippet sites now go through `_pylit()`
  (`json.dumps`); `run_fr_metrics` had the identical pattern and would have
  failed on the same file at the gate step, so it was fixed in the same slice.
  RED-first test `ast.parse`s the snippet and asserts the paths round-trip.
  kai-sa reran to PASS.
- **The QA-queued slugs all carry the DeviantArt preview watermark.** A
  semi-transparent `(c) ARTIST.DEVIANTART.COM` band at y=971..1013 of 1440,
  across three different artists. I cropped the detected boxes and looked - this
  is confirmed, not inferred. It is an artifact of the quota-free
  `intermediary=true` fetch route, so it will recur on every slug recovered that
  way. The gate was RIGHT to refuse (`centre_overlay` x4, `not_border` x1): the
  strip crosses the subject. Doctrine says recover, do not inpaint, when a clean
  source exists - so these want a re-fetch at `original=true` (weekly quota),
  NOT a 660px LaMa repaint through a face. Annotated into all 5 manifests.
- **Checked the 15 shipped rather than trusting the zero-detection verdict.**
  Cropped the same y-band from all 15 plus a full-frame contact sheet: clean.
  The split is by artist - all 15 came from fudoyuseivn.
- **Operator granted the sona crop; it landed in the same watermark queue.**
  `sona-feathers-void` (1920x1280) center-cropped top+bottom to 1920x1080 and
  scored G1 **PASS** (lap_ratio 1.3576, halo 0.0239, msssim 0.9990, lpips
  0.0059), then the cleaning scan routed it to QA on `faint_mark` - and the crop
  shows the SAME `(c) ARTIST.DEVIANTART.COM` band, caught by the faint-mark lane
  at conf 0.12 instead of by a yolo box. So the recovery bucket is **6**, not 5.
  `cozy-fall-with-seraphine` (910px wide after crop) and `leona-and-diana`
  (900px) stay held: both sit under the 1280px G0 floor, so they queue for
  source recovery rather than a thin ~2.8x upscale.

- **Re-fetched the 6 at `original=true` as asked; DeviantArt refuses at source.**
  A control fetch on `akali` came back **byte-identical** to the intermediary we
  already had (same sha256, same 717037 bytes, same 1280x718). The reason is not
  quota and not the missing refresh-token: `gallery-dl -j` reports
  **`is_downloadable: false` on all 6**, across all 4 artists - the artists
  disabled downloads, so DA serves only the watermarked intermediary and no
  OAuth would change it. Worth noting `content.filesize` runs to 28 MB behind a
  1280px served frame, so the clean original exists, it is just withheld. All 6
  manifests carry the finding; the memory now says check
  `gallery-dl -j <url>` for `is_downloadable` BEFORE spending anything, since
  the check is free. **Do not retry this route.**

- **Dropped 3, attempted the hand-clean on 3 - and the hand-clean is a PARTIAL,
  so nothing shipped.** `akali`, `kai-sa` and `xayah` were GC'd via
  `lw_pipeline remove --yes` (full GC, both the scratch folder and the
  `9.Image Backup` entry, matching the `note=full GC` precedent);
  `clean_scratch` 86 -> 83.
- **The DA mark is TWO objects, and only one of them came off.** The credit
  line `(c) ARTIST.DEVIANTART.COM` removes cleanly: a strip mask over the
  measured glyph rows (45px / 39px / 62px bands, 0.9-1.2 percent of frame) plus
  one simple-lama pass, outside-mask MAD exactly 0.000000. Verified at 2x on the
  busiest crossings - the first attempt used the full 58-62px strip and smeared
  neon-jinx's braid, so the band was tightened to the measured glyph rows and
  the braid, zipper and hair now survive.
- **The second object is a big faint LOGO veil mid-frame, and it defeats the
  existing assets.** `overlay_prepass` made all three WORSE: the cached
  `overlay_matte_wide` encodes a DIFFERENT render's credit line
  (`(c) SMALLTAVERNX.DEVIANTART.COM`), so it mis-registers (sona shift
  [43,-35]), leaves the veil and paints red streaks across sona's face. Those
  candidates were deleted. A clean-frame control (two fudoyuseivn `_cleandone`
  frames at the same coordinates, 2.4x contrast) shows no such block edge, so
  the veil is real and not a measurement artifact.
- **Operator ruling: drop all six.** Zero-residue is the bar, the veil failed
  it, and the remaining three were GC'd on the same ruling as the first three.
  All 6 gone via `lw_pipeline remove --yes` (full GC, scratch + `9.Image Backup`);
  their `ops/runtime/clean/<slug>/` side-files were cleared too. `clean_scratch`
  100 -> 80 (back to the pre-existing WIP), `verify: ok (598 images checked)`,
  anomalies 0. **If the route is ever re-opened:** re-estimate template+matte for
  THIS render via `lw_clean_overlay.estimate_template` / `estimate_veil` on a
  LARGER same-render frame set - it was deliberately NOT fitted on those 3,
  because the settled ruling puts the veil estimator at SNR ~1 and 40 percent
  movement when the frame set changes.

- **The last 2 held slugs were checked, and they were the same story - dropped.**
  `cozy-fall-with-seraphine` (1024x512) and `leona-and-diana` (900x600) BOTH
  carry the two-part DA watermark (leona's logo is blatant), BOTH read
  `is_downloadable: false`, and BOTH sit under the 1280px G0 floor even before
  their 11-16 percent crop. The crop cannot dodge the mark either - cozy-fall is
  too WIDE so the crop takes width, and leona is too tall by only 94px, while
  both marks sit mid-frame. Processing them was futile, so they were GC'd on the
  same ruling as the other six.
- **The 2 pending-intake files were GC'd - they were proven redundant, not new.**
  `battle_cat_jinx_...dlokdgx-pre.jpg` and `pulsefire_fiora_...dlrpczo-pre.jpg`
  sat in `0.Originals` because the intake gate refused them as `hash-equal
  original` duplicates. Verified independently rather than on the CLI's word:
  each is BYTE-IDENTICAL by sha256 and size to the archived original already in
  `9.Image Backup/<slug>/`, and both parent slugs are already `CLEAN_DONE`. So
  deleting them lost no bytes and no provenance. `0.Originals` is now empty but
  for `.gitkeep`; `pending_intake` 2 -> 0. This closes the GC call that
  WAKEUP had been carrying as open.

- **Drained the `3.Cleaning Scratch` backlog: 80 triaged, 10 shipped, and the
  rest is one decision.** Ran `lw_clean_pass` over the 76 fresh slugs - **not one
  auto-cleaned** (41 at `overlay_score >= 0.15`, 19 in the 0.10-0.15 defer band,
  15 below 0.10). Sampling 12 across the reason codes showed why: the backlog is
  the SAME DA preview overlay, with `SLIMSHADYWALLPAPER`, `SMALLTAVERNX`,
  `GIVEMEHINTEI` and `PEBANO1` credit lines legible at 1:1.
- **Closed the "would a matching matte work" question - it would not.** Slug
  `122` is a SMALLTAVERNX frame, the exact render the cached matte was estimated
  from. The overlay lane STILL failed on it: line ghosts, the logo gains a hard
  bright block, the lip is damaged, and registration reported `scale=1.12`, so
  even same-artist frames carry the overlay at different scales. Do not re-open
  this on matte-matching grounds.
- **Shipped 10.** Three (`128-cleanup`, `138-cleanup`, `18-cleanup`) were
  faint-mark FALSE POSITIVES whose boxes verify at 1:1 as smoke, bamboo leaves
  and a bottom edge strip - clean-scanned through. Seven carried non-DA marks
  that masked LaMa removes cleanly per ADR-005: a `CHENBO` signature, two
  `PUPPETWORKS` studio logos, a `@lulalakill` script watermark and three
  `NAMAKXIN P&M` banners. Outside-mask MAD 0.000000 on all seven, all at exactly
  2560x1440. Two masks under-covered on the first pass (`PUPPETWORKS` lost
  "ANIMATION STUDIO"; `NAMAKXIN` lost its final N, which survived as a hooked
  stroke) - the same under-cover lesson the credit-line strips taught, so
  ALWAYS re-verify the mark extent at 1:1 after inpainting.
- **4 excluded, not re-run:** `aatrox`, `aidraw-2662100118`, `the-ruined-king-viego`
  and `viego-the-king` already climbed lama -> sdxl-animagine -> iopaint with
  every rung rejected. They ARE part of the evidence base ADR-009 rests on.
- **What remains: ~63 DA-overlay slugs in `3.Cleaning Scratch`, one drop-or-keep
  call.** Per-slug census with scores and reasons:
  `docs/CLEAN_SCRATCH_CENSUS_2026-09-01.md`. `clean_done` 507 -> 517,
  `clean_scratch` 80 -> 70.

- **Tried the 62-frame pooled veil estimate (123f held out). IT DID NOT WORK,
  and the mechanism is now known - see `docs/POOLED_VEIL_RESULT_2026-09-05.md`.**
  What DID work: registration is NOT the problem (all 26 sampled frames at
  scale 1.00, shift within +-3 px, correlation 0.35-0.58 - so the `scale=1.12`
  reading on slug 122 does not generalise), and pooling cancels the art cleanly
  (median high-pass leaves the logo outline crisp, 29,492 support px).
  What failed: the pooled matte recovers the mark's EDGES, not its flat FILL,
  because `estimate_template`/`estimate_matte` are built on `highpass`, which by
  construction discards the DC band the veil lives in. Applied to held-out 123f
  it DARKENED the logo outline and left the interior. `estimate_veil`, the one
  component meant to catch a flat region, returned 693 px at alpha 0.021.
  **Do not retry with more frames or looser thresholds - the blindness is in the
  transform, not the sample size.**
- **The credit line can never be pooled: it is artist-specific.** The pooled
  matte carried PEBANO1's glyphs (that artist dominates the set) and subtracting
  them from a SMALLTAVERNX frame produced a dark smeared double plus new jaw
  artifacts.
- **A live re-demonstration of the settled ruling: `overlay_score` fell
  0.5492 -> 0.2085 (62 percent) on an output that is visibly WORSE.** Disbelieve
  any future success claimed on that metric without looking at pixels.
- **Correction to an earlier claim in this session.** I read a whole-frame
  `residual_mae` of 0.028 as proving the operator's hand-clean inverted rather
  than reconstructed. That was dilution - only 0.39 percent of pixels were
  touched. Measured on touched pixels the hand-finished line fits the alpha
  model NO BETTER than the known-invented LaMa layer (7.00 vs 6.12 median
  levels, 94.0 vs 94.3 percent unexplained). So hand-cleans are the ACCEPTANCE
  TARGET, never fitting data.

- **SIDE MISSION: pulled a canonical LoL wiki reference set for lw-gen
  (`60461ae`).** The operator-supplied gallery (deviantart.com/savage-shapes) was
  a dead end and it was PROVEN so, not eyeballed: `anthro` returns 39,792 of its
  39,795 deviations while `league of legends`, `ahri`, `jinx`, `runeterra`,
  `card`, `splash art` and `human` all return 0. The anthro/fox counts are the
  control, so the search works and those zeroes are real - it is a furry gallery.
- **Pulled from the wiki.gg Action API instead (LEDGER 72 route):
  173 champions x 2 axes, 346/346 files, 0 missing, 1.2 GB.** `render` (isolated
  figure, anatomy/silhouette/proportion) + `splash` HD original (median 6000px,
  up to 10000x5626) for pose-in-composition, colour register and face detail.
  Lands in `data/reference/wiki/{render,splash}/`, gitignored - verified with
  `git check-ignore` BEFORE a byte was fetched, since the repo is public and the
  art is third-party. Provenance records the sha256 of what arrived (spot-checked
  6/6 against disk), never the API-declared sha1 that no host serves.
  **9 champions have no HD upload** and stay at 1215x717: Amumu, Briar, Corki,
  Karthus, Kayle, Lulu, Morgana, Nunu, Pyke.
- **The champion universe is the `OriginalSkin` file, NOT the render category,
  and both reasons were measured.** `Category:Champion renders` is INCOMPLETE -
  `Kayle Render.png` exists but is not in it, so a render-derived universe lost
  Kayle outright while still carrying four of her forms as champions. It is also
  ambiguous: `Aatrox Winged`, `Kayle Aflame`, `Nunu & Willump` and `Dr. Mundo`
  are all multi-token and indistinguishable by name shape. My first filter
  dropped any name whose prefix also had a render and got `Nunu & Willump`
  exactly backwards, keeping legacy `Nunu`. The `OriginalSkin` suffix is fixed so
  the prefix is the whole name, and no variant, form or placeholder has one:
  172 champions / 20 unresolved -> 173 / 346 of 346. 29 tests, all offline.

- **OPERATOR RULING, and it reverses my recommendation: the 63 are NOT dropped.**
  I had enumerated them exactly and was verifying the mid band when the operator
  stopped it. The plan instead is to HAND-CORRECT them, then study the
  before/after pairs and build an automated emulation from what the hand work
  reveals - the same route that turned manual IOPaint into `lw_clean_iopaint`.
  **Nothing was deleted.** All 63 remain in `3.Cleaning Scratch`.
- **Why this is the stronger plan, stated so it is not re-argued later.** Blind
  matte estimation on these frames sits at SNR ~1 because it must separate mark
  from art with NEITHER known - the reason the settled ruling says not to refit
  that estimator on a small frame set. A hand-cleaned frame supplies the art, so
  the overlay follows in CLOSED FORM from the compositing model
  (`alpha = (obs - orig) / (W - orig)`). Hand work is therefore not just cleaning
  one image; it manufactures the ground truth the automation never had.
- **Built `tools/lw_overlay_from_pair.py` (TDD, 8 tests) to cash that in.** It
  measures the matte and the mark colour from a pair and reports `residual_mae`,
  which is the honest diagnostic: how far the measured matte is from reproducing
  the watermarked frame when composited back. Validated twice - synthetic
  composites with a known alpha, and a REAL frame carrying a known synthetic
  mark, where it recovered mark colour 248.0 exactly, the 0.06 veil and the 0.30
  line, at residual 0.0 and mean alpha error 1e-6. The 16 px of 123,500 that miss
  are the documented singular case where the art already sits at the mark colour.
- **Worklist: `docs/HANDCLEAN_WORKLIST_2026-09-01.md`.** All 63 ranked by detail
  in the overlay band, ascending - a smooth background under the mark is both the
  easiest hand-clean and the cleanest matte extraction, since less art texture
  contaminates the recovered alpha. `123f` is the best first subject: the
  strongest overlay signal in the set (0.634) over its smoothest background
  (detail 2.25). Adopt finished files with
  `lw_pipeline save-working <slug> --adopt`, which still runs the G2 outside-mask
  assertion.
- **NEXT: the emulation must be judged on frames its matte was NOT fitted on.**
  A matte that reproduces the frame it came from proves nothing.

- **FINAL TALLY for the 2026-09-01 intake: 15 shipped, 8 dropped, all 8 to the
  DA preview watermark.** That is **35 percent of a 23-slug intake lost to the
  fetch route**, which is the number to weigh before the next intake.
  `1.First Pass Scratch` is down to `1000040081-...-375w-2x` alone - a 750x436
  source under the G0 floor, pre-existing since 2026-08-17, untouched.
  `verify: ok (596 images checked)`, anomalies 0.
