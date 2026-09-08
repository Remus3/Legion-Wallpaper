# SHA rewrite map - 2026-09-07 operator-email purge

The operator's real personal email address was readable in a
PUBLIC repo in two places: the `author` and `committer` identity fields of all
526 commits, and the body text of two tracked docs (`docs/LEDGER.md` item 154
and `docs/_archive/2026-09-06-sha-rewrite-map.md`). Commit 219fdb7 scrubbed the
two doc bodies in the working tree; it did nothing about history, which is
where nearly all of the exposure was. This rewrite closed both.

`git filter-repo --force --mailmap <one line> --replace-text <one literal>`
rewrote ALL 526 commits (the identity change touches the repo's first commit,
so every downstream sha moved - 0 of 526 shas survived). Two filters ran
together:

- `--mailmap`: `Moonbeam <the operator's personal address>` ->
  `Moonbeam <7991173+Remus3@users.noreply.github.com>` on BOTH the author and
  the committer field of every commit. The name is unchanged. GitHub's
  ID-prefixed noreply address is the deliberate choice: an arbitrary
  replacement address would have dropped the operator's contribution credit,
  because GitHub attributes commits by email.
- `--replace-text`: the literal address -> `redacted` in blob content, which
  reaches the historical versions of the two docs.

526 commits in, 525 out. The one dropped commit is `219fdb7` itself: once
`--replace-text` had put `redacted` into its parent's copy of those two files,
219fdb7's diff was empty, and filter-repo prunes commits that become empty. Its
content survives - it is what every version of those files now says. The HEAD
tree is byte-identical before and after
(`336db8f1dc8cb1bef6da08e9275b5d146cb7acd4` on both sides), which is also the
cross-check that `--replace-text` produced exactly the bytes the manual edit
did. Old HEAD `219fdb7` -> new HEAD `3dec9e3`.

Verified after the force-push, live against the GitHub API: the HEAD commit's
author and committer both read `Moonbeam
<7991173+Remus3@users.noreply.github.com>`, the commit still resolves to the
`Remus3` account, and `GET /repos/Remus3/Legion-Wallpaper/contributors` returns
exactly one entry, `Remus3` with 525 contributions. Locally, `git log --all`
reports a single identity across all 525 commits and `git grep` over every
object in `git rev-list --all` finds zero occurrences of the address in any
blob; it never appeared in a commit message.

**What this does NOT purge.** A force-push does not delete GitHub-side
unreachable objects - the standing ruling in CLAUDE.md, and re-confirmed here:
`GET /repos/Remus3/Legion-Wallpaper/commits/219fdb70...` still returned HTTP 200
after the push. Anyone holding an old sha can still read the old commit, and
the old commits carry the address in their identity fields. Only a GitHub
Support purge request, or delete-and-recreate of the repo, removes those.
Treat the address as still recoverable by a determined party until one of those
happens.

Follow-up applied in the same session: `git config user.email` was reset to the
noreply address both globally and repo-locally, so the next commit cannot
reintroduce the address.

Chaining note: this is the THIRD rewrite. The 2026-08-01 stray-jpg blob purge is
mapped in `docs/_archive/2026-08-01-sha-rewrite-map.md`, the 2026-09-06
co-author-trailer purge in `docs/_archive/2026-09-06-sha-rewrite-map.md`. Each
map's "new sha" column feeds the next map's "old sha" column, so resolve a sha
by walking the maps forward from the one that covers its date - oldest first.

The authoritative full 526-line map lived at `.git/filter-repo/commit-map` on
the operator's box and is NOT tracked (local git plumbing, overwritten by any
later rewrite). The table below is the durable subset: 275 entries, every sha
cited anywhere in tracked Markdown. The citing prose was deliberately NOT
edited - the ledger is append-only, and the old shas are accurate labels for
what happened at the time.

A `git bundle --all` of the pre-rewrite history was taken before the filter ran
and kept off-repo at `C:\LW-backups\lw-pre-email-scrub-2026-09-07.bundle`. It
still contains the address, by design - it is the rollback path.

| old sha | new sha | subject |
|---|---|---|
| `00ae1f4` | `e0d7815` | docs(g1): merge the USM halo census slice |
| `0184089` | `19a5175` | fix(cleaning): a stub may add a verdict, never soften a ch |
| `0204cfa` | `e11d8d6` | feat(lw-gen): M2 W3 IP-Adapter weapon rung - transplant +  |
| `024d0a8` | `3e6b7a2` | fix(test): assert the CUDA DLL PATH policy on POSIX too in |
| `02a9bdc` | `0aa07b3` | fix(loop): a hung sdk child could not be killed, and the l |
| `0472a72` | `3b0b43d` | ci: arm the git-hook gate in cv-lane, teach the parity gua |
| `065679b` | `a483c91` | test(lw-gen): harden hand/pose negatives + prove img2img-f |
| `07b7e30` | `bf09b80` | feat(lw-clean): SDXL reconstruction inpaint worker (lw_cle |
| `07ed5bc` | `0755e96` | fix(truth_gate): tell CI will never run apart from CI has  |
| `09a68f4` | `b586906` | fix(settings): stop publishing a permission-disabling defa |
| `09e4905` | `d584ba5` | ci: arm the git-hook gate in the checkout instead of asser |
| `0c255d8` | `a0fe700` | feat(lw-gen): W4 M3 - wire rung==w4 weapon-concept LoRA in |
| `0c9b1f5` | `773a73f` | chore(first-pass): triage the 9 residual working slugs |
| `0cce31a` | `82f2ef4` | perf(dwpose): bind the CUDA execution provider, and wire i |
| `0cd8991` | `45c9994` | feat(rundash): P1b Cycle History panel, and the cost bound |
| `0d5211a` | `f1e329d` | test(hooks): port RC's real end-to-end hook refusal probe, |
| `0f7bab3` | `df8e0de` | docs(cleaning): algebraic-only reviewed too - 2 of 45, rem |
| `109124d` | `b6c1796` | feat(clean): overlay matte seeds the LaMa mask - 32/32 und |
| `1253bab` | `ef81f13` | feat(rundash): P4 Operator Queue and P5 Suite Trajectory |
| `15844aa` | `faaae89` | chore: repo renamed to Remus3/LegionWallpaper, update wake |
| `17693cb` | `ea7df18` | fix(wallpaper): time trigger so rotation starts without wa |
| `17db253` | `a3bff3d` | docs: record the wiki reference set and the dead-end galle |
| `18b7ddd` | `8013956` | fix(loop): unserialized mutex holds were invisible to the  |
| `191742a` | `c1f36aa` | chore(first-pass): merge the R26 alpha audit slice |
| `1998e2b` | `5105bea` | fix(guard): a RENAMED sibling repo must go red, not quiet |
| `19b5848` | `65b167d` | docs(spec): F1 P5 PASSED - concurrent LW+RC run, all four  |
| `1b98e9c` | `4398e81` | fix(inbox): do not descend a junction, and stop dropping e |
| `1d3631b` | `7384571` | feat: restoration pipeline v1 - state machine, monitor, st |
| `1dbfc2d` | `954b129` | feat(gen): port weapon renderer to glb named joints |
| `1de8d4e` | `25a393e` | feat(winmutex): rotate the mutex names to opaque strings,  |
| `1ea9144` | `b5bcedc` | fix: stop the test suite destroying the lw-clean venv (ult |
| `1ef672e` | `2f929e7` | chore(sync): Resin Compute replaces Red Moon in the govern |
| `2028026` | `c7e65cd` | feat(first-pass): operator-directed crop override for aspe |
| `202cef3` | `9aa7ada` | chore(loop): point the directive_suffix at the f1-phase6 d |
| `2248313` | `e1a151e` | fix(cleaning): one verified IOPAINT_LAUNCH constant, kill  |
| `24b7d5f` | `b99025a` | feat(gen): IP-Adapter reference-image guidance on the txt2 |
| `25bafcc` | `2e83a2d` | docs: RESTORATION_PLAN hygiene - fix stale iopaint venv re |
| `269cba6` | `22b26a1` | docs(first-pass): run the last 5 slugs, and the census kil |
| `26c5ae3` | `1e6a798` | ci(cv-lane): run tools/test_lw_clean_dekel.py - 8 tests th |
| `271a4f7` | `b07e345` | fix(inbox): key on CONTENT, and watch at prompt time as we |
| `2894e0b` | `59145a6` | feat(lw-gen): calibrate QA floors on real Vayne sweep (T_b |
| `2958338` | `9cb2e03` | fix: cleaning retry default 1 - measured, retries never wi |
| `2b94040` | `e2a0836` | fix(tests): the wired fixture must install hooks executabl |
| `2d744d7` | `e75e3d4` | fix(secrets): the guard read a doc's markdown as part of t |
| `2fe8087` | `6431ad0` | feat(intake): perceptual near-dup gate - the twin the byte |
| `3070b2e` | `4d8a3f8` | feat(loop): P3 - machine-wide concurrency governor (slots, |
| `30e98cd` | `47ade64` | fix(cleaning): a stub speaks with the others or not at all |
| `31e5d96` | `29d33ba` | docs(mcp-lift): P3 - the wiki has the pixels, and neither  |
| `31e68c7` | `da5ca60` | docs(triage): LW-native MCP lift triage - 63 links, LW rub |
| `34506a4` | `0a6a1a7` | feat(lw-gen): M1 weapon-region gate - CLIP is a dead gate, |
| `34d366a` | `cb41ac6` | feat(gen): face-realism block for splash-booru, measured a |
| `357b0a6` | `09e3700` | feat(gen): recover the medium yardstick as a tool, measure |
| `363d9e5` | `5b068b0` | feat(cleaning): run the credit-line lane on the queue, and |
| `374c79e` | `896bdba` | fix(slots): a lock that cannot be deleted is neutralised,  |
| `375afdd` | `69218fc` | feat(first-pass): merge the fetched-fullview glob slice |
| `37741ea` | `4a3dac1` | feat(golden): promote V3 detail DAT2 to primary + re-freez |
| `3a3f6f7` | `9c25fde` | feat: guard the Desktop hand-off target, wire it into /don |
| `3a8a296` | `0ada15e` | docs: sync living docs - ledger 146-150, two open roadmap  |
| `3b8e0f1` | `ecdd96b` | docs: 46 held refs intaken to first-pass scratch (LEDGER 3 |
| `3bd9a8b` | `ccc0169` | fix(loop): the POSIX winmutex branch was unserialized AND  |
| `3c4e704` | `01f401d` | docs: pay the ledger the interrupted session owed |
| `3cc6d8f` | `590fe9b` | feat(render): preserve the .skn multi-angle renderer as tr |
| `3d81298` | `81b57f1` | feat(pipeline): remove subcommand - a sanctioned writer fo |
| `3f2b9bc` | `165cf36` | fix(gen): never drop a frame the face-key cannot score |
| `4184ad2` | `72f2cde` | test: cover align_rois (10 tests, lw-clean venv) and corre |
| `418f328` | `243baa3` | feat(cleaning): template detection + scheduled fill on the |
| `44cb0f2` | `bf74bd6` | feat(lw-gen): M2 W2 reference-transplant rung - affine cro |
| `4682b5c` | `a40c5f4` | docs(cleaning): second hand-clean capture confirms the str |
| `47903a2` | `c6459d4` | fix(clean): measure where the credit line starts instead o |
| `486b5f5` | `43be450` | fix(cleaning): record the 45/45 overlay rejection, split f |
| `486c448` | `60e04eb` | feat(facts): unread cross-repo mail is surfaced at SESSION |
| `4a1cc3a` | `3a30987` | docs: AGENTS hygiene pass (R10) |
| `4a7c047` | `d3f23ee` | feat(cleaning): a second credit-line round, and what it co |
| `4c5abf7` | `81723bc` | feat(cleaning): residue-targeted passes - the text finally |
| `4c97b95` | `f148898` | fix(tests): raw strings for the two backslash paths I ship |
| `4dbe017` | `04428e7` | feat(cleaning): sweep the percentile on all ten, and close |
| `4e3b617` | `e369b92` | chore: Apache-2.0 LICENSE, untrack + purge the root style  |
| `4f88831` | `f41b14b` | chore(loop): flip to N=3 and apply the three-repo slots re |
| `4fd66f7` | `a1d9939` | docs(ledger): record the audit's outbound deliveries, per  |
| `5099a48` | `7929abb` | feat(rundash): the directive-history spine - run id, cost, |
| `511f1d8` | `c39949b` | chore(meta): add self-authored social preview card for the |
| `547dffd` | `4f5baf4` | feat(rundash): merge the run dashboard server and page |
| `549f52c` | `7da3b2a` | fix(loop): the sdk executor never logged the session id it |
| `5527059` | `3724cc2` | docs(clean): matte rebuilt on the wider grid - alpha 0.133 |
| `5715cf0` | `7191e45` | fix(golden): pin the USM recipe against lw_upscale, not a  |
| `58896c5` | `9520a8f` | docs(loop): P5 concurrent smoke cycle 2 |
| `58b30c4` | `49eca28` | docs: WAKEUP hygiene - relocate W4-M3 session to history_n |
| `58dc53c` | `6e9a246` | feat(first-pass): merge slice b - carry usm_applied into G |
| `5aec00d` | `47fef3d` | feat(lw-gen): wire subject-LoRA loading + --lora-path/--no |
| `5c2cf42` | `516f8a2` | feat(recover): SauceNAO multipart POST + campaign driver + |
| `5d2600e` | `0b96549` | feat(rundash): persist verifier verdicts so the P2 chip ca |
| `5e9c691` | `dc374b6` | docs(cleaning): 0 of 87 automated candidates accepted - cl |
| `5f6f119` | `f565536` | feat(dwpose): stamp eval runs with their bound providers;  |
| `60461ae` | `8d1b40d` | feat(gen): pull a canonical LoL wiki reference set for lw- |
| `60dd217` | `56f8a3a` | feat(anat): merge the head-spine diagnostic slice - gating |
| `61b34f4` | `181a02a` | feat(loop): truth_gate persists what it observed onto the  |
| `62555c6` | `f9d93fa` | docs(first-pass): batch 5 more slugs, and all five were hi |
| `63cc35b` | `9d3f0aa` | docs: ref triage - 226 clean delivered, 46 held (LEDGER 35 |
| `646263d` | `fdaaed2` | docs(loop): P5 concurrent smoke cycle 1 |
| `6737d04` | `1c457a0` | docs: orchestration plan R11 DONE (e326d25) |
| `67c87bf` | `df98556` | docs(ledger): item 169 - independent audit of RC's public  |
| `6830211` | `b42f90e` | fix(loop): wire truth_gate into the run flow, and fix what |
| `690ffb7` | `6711b83` | fix(ops): LW-WeeklyHygiene opened a visible powershell con |
| `693920f` | `680a03c` | feat(lw-gen): M1 slice 1 - pure weapon-mask derivation (we |
| `6c0423c` | `63463a5` | ci: docs-only pushes ran no CI while guards read docs off  |
| `6c6006a` | `610b5b3` | feat(first-pass): needauth queue cleared + bucket A+B held |
| `6cebfd7` | `e326d25` | docs: DEEP_AUDIT_CHARTER hygiene pass (R11) |
| `6cffc3d` | `c6bf896` | feat(upscale): G0 over-target source-gate - downscale-only |
| `6db5443` | `8544114` | fix(pipeline): prune Done N at the transition, not at Done |
| `6e1aa9b` | `5050da3` | docs(backlog): P6 closed as NOT APPLICABLE - LW replays no |
| `6f07bd5` | `3d637f7` | docs(gen): record the 616.56 driver and the CUDA-12 onnxru |
| `6fffd74` | `bfaf505` | chore: drop tracked scratch dumps and untrack a stray log |
| `70838da` | `4bc48bd` | feat(lw-gen): W4 M2 - in-house UNet-only SDXL LoRA trainer |
| `711f5f9` | `e330216` | fix(loop): the director stamped its own premises and nothi |
| `71bf503` | `5a58a34` | fix(clean): the veil ring was hiding a cliff the lane itse |
| `737a160` | `a076db0` | feat(cleaning): dispose the 566-slug cleaning corpus gate- |
| `7453936` | `0475e4d` | chore: apply UP017 - datetime.timezone.utc to datetime.UTC |
| `74a6b09` | `92175ff` | feat(clean): one engine per submission - drop the cross-en |
| `751702d` | `8f7c309` | feat(hooks): P1 - the Stop-hook claimed-green gate, and th |
| `7657356` | `527f980` | feat(lw-gen): W4 M1 - weapon-crop curation tool (DWPose au |
| `77650b1` | `de5634d` | test(ports): guard the ARCHITECTURE.md port map against th |
| `77937d2` | `df1c826` | feat(gpu): merge the GPU mutex wiring slice |
| `7809618` | `f3c1b7d` | docs: rewrite README for an outward audience - badges, pip |
| `7826b22` | `dca1906` | docs(corpus): apply 122 operator champion labels to CHAMPI |
| `78a0521` | `b6e55b4` | feat(pipeline): flag a globally-filtered submission at sav |
| `78d0ad1` | `f012cad` | docs: weekly hygiene - relocate 2026-08-02 session, keep W |
| `7927d09` | `b1ed487` | docs(mcp-lift): stage-4 deep dive - all 63 read at source, |
| `7a20a0f` | `e359c0f` | docs(mcp-lift): close L1, kill L2's flag half, file the Gp |
| `7afb92f` | `62ef61a` | docs: ROADMAP hygiene - drop LEDGER-superseded blocks, res |
| `7b11f21` | `37a63e7` | feat(first-pass): ADR-006 downscale-only drops G1 lap_rati |
| `7d1796b` | `2eca9f4` | test: probe torch-free imports in a clean interpreter, not |
| `7d4b6ef` | `6649b82` | feat(cleaning): generate the operator's mask schedule - fi |
| `7d62062` | `90c3ca7` | chore: ruff target-version py39 -> py312, ratchet UP017 +  |
| `7d6a3ca` | `cccf555` | feat(lw-gen): provision + prove Phase-0 (RealVis SDXL, sm_ |
| `7e21c9d` | `0a18a23` | feat(lw-gen): M1 localizer - adopt DWPose onnx-CPU (5/6 vs |
| `7e5374c` | `bae23d8` | fix(loop): my config-path fix made the Windows paths in it |
| `7ea35e6` | `d25f2fc` | fix(tests): the teardown test asserted taskkill on a platf |
| `7ea5707` | `3bcae83` | feat(guard): scan agent config, and fix the trust-key bug  |
| `7fe4785` | `6604653` | feat(rundash): P6 Fleet History - read the mirror nothing  |
| `7fffd41` | `108aec5` | test(loop): measure three-way concurrency with real proces |
| `808d96b` | `fe747ae` | fix(pipeline): finalize silently dropped an operator audit |
| `81de837` | `b019e5b` | chore(rename): the local root is "C:\Legion Wallpaper", wi |
| `827e688` | `f251a2a` | docs: the 65 decomposed - two levers falsified, the reach  |
| `82aacc2` | `37aa0da` | feat(first-pass): committed lw_first_pass driver (intake-> |
| `834b74e` | `705473c` | feat(lw-gen): M1 weapon pass W1 - DWPose-wrist masked SDXL |
| `852a721` | `9cdb6f2` | fix(rundash): a live clock made the time-in-status bound f |
| `8530f5e` | `6e31cd4` | fix(inbox): report a WITHDRAWAL, close the shared pin, and |
| `8562788` | `d74ad17` | docs: BACKLOG hygiene - drop expired product-TBD notations |
| `8717016` | `360b0be` | fix(recover): merge the oEmbed-inconclusive slice |
| `8766adf` | `d96159a` | fix(clean): the veil gain was a boundary solution, not a f |
| `879ddd6` | `8ef8cc9` | fix(recover): P2 - mockd replay, and the non-200 branch it |
| `88e1ac7` | `96b5f74` | fix(clean): keep artwork out of the fill mask |
| `8971391` | `d638395` | docs(cleaning): quantify the operator's 82-step hand clean |
| `89f55ae` | `f6c2167` | feat(cleaning): scope the revert to the line it damaged, n |
| `8a3fcae` | `835ff51` | feat(cleaning): approve the 7 detector false positives une |
| `8afab90` | `91be9bb` | feat(intake): 20 originals intaken with the recovery water |
| `8c0a67c` | `a6f9586` | feat(cleaning): drive the 87-slug manual QA lane, 85 candi |
| `8e30892` | `d5f75e9` | feat(lw-gen): ControlNet-OpenPose pose control - natural p |
| `8e8b9a0` | `8bc23de` | feat(golden): lw_golden.py freeze/regress tool + gitignore |
| `907ff46` | `d67ecb3` | fix(ops): P0 correction - the gate was wired into the ACTI |
| `920afeb` | `9cbb191` | feat(loop): no Claude dollar cap or accounting - it does n |
| `92b89ba` | `805d201` | feat(golden): re-freeze all 12 baselines under USM 35 and  |
| `936d99b` | `069dbe6` | feat(golden): freeze first-pass golden set (10 blessed IJN |
| `9451535` | `2e00ad6` | fix(recover): the one-off diagnostic still called an incon |
| `9477a7e` | `354a7c7` | docs(first-pass): the 46-slug upscale batch has nothing to |
| `94db5d0` | `0a58ec9` | feat(cleaning): scoped revert defaults ON, because the pai |
| `9718e05` | `0dadcc4` | docs: analysis-by-synthesis needs a matched pair, and none |
| `973838f` | `59e8ede` | docs: archive RESTORATION_PLAN_v1.md to docs/_archive (R9) |
| `98f1d65` | `c9755b0` | feat(cleaning): relative residue measure - built, calibrat |
| `9c14b8d` | `19833d7` | fix(upscale): merge slice a - no resample, no unsharp mask |
| `9db4371` | `ee274bd` | fix(inbox): the watcher was blind to subdirectories, and t |
| `9e48223` | `0e1862b` | docs: OPERATIONS hygiene - drop stale TBD tags on existing |
| `9ed619b` | `dea5506` | feat(cleaning): tiled decomposition worker - built, measur |
| `a019586` | `c9e986c` | docs(wakeup): record the root rename and the expected slot |
| `a116989` | `6aa8b5e` | feat(clean): record the mark a step hands back; falsify th |
| `a15394b` | `33b9c27` | fix: resolve both B905 sites per-site, drop the ignore |
| `a214af6` | `e14f204` | fix(loop): label the static suffix, and make the stdin-cap |
| `a270dce` | `3e31156` | feat(clean): land the confirmed per-slug presets and drain |
| `a469624` | `a6cbd40` | docs: look at all 39 credit-line sheets, flag-only |
| `a573363` | `1b8ab84` | feat(handoff): gate the WRITE, not just the commit, with O |
| `a68aa77` | `f84517d` | fix(cleaning): share the mask-coverage guard across every  |
| `a72ea8b` | `27c77b3` | feat(ops): adopt per-session drift guard, keep full suite  |
| `a751b19` | `7d701ea` | feat(rundash): mirror the agent fleet before Claude Code r |
| `a7dfde5` | `ef09286` | docs(commands): stop instructing the banned Claude co-auth |
| `a934243` | `136bdf9` | feat(lw-gen): M0 foundations - Animagine config flip, pose |
| `aa99af3` | `e28e145` | docs: sync living docs - ledger 152-153, golden re-freeze  |
| `abc8f14` | `b86ad4c` | feat(cleaning): gate subdivision on gradient; blanket esca |
| `ad4643e` | `7509606` | feat(cleaning): 107 analysed - fill holds, the residue det |
| `ad99249` | `50cb751` | fix(first-pass): an apostrophe in a source filename killed |
| `b086e18` | `f5ee25b` | test(inbox): the digest key is a CONTENT key, proved by mu |
| `b096533` | `3be4ad5` | chore: CI python 3.12 -> 3.14, ruff target-version py314 |
| `b14b688` | `f1debb1` | fix(g1): cap FR common scale so DISTS stops OOMing on 8K s |
| `b1ad327` | `bae9cb5` | docs(loop): P4 sdk-channel smoke cycle 1 |
| `b2c932f` | `ed0ec65` | feat(pipeline): reopen - the reverse move, and the academy |
| `b2fc3a2` | `9d09beb` | feat(lw-gen): generator sidecar (run/qa/promote) + /genera |
| `b57c2ed` | `ef84001` | fix(inbox): a withdrawal could never be CLEARED, and the d |
| `b61c1a5` | `d86d46b` | feat(recover): source-recovery waterfall scaffolding + art |
| `b63992a` | `5aa827e` | docs(gen): close glb-render-pipeline, open glb-render-fetc |
| `b6b69e9` | `1511f03` | feat(ops): P0 - move the glyph/ruff gate into git hooks, e |
| `b80e7cb` | `34b9a89` | docs: sync living docs - ADR-009 in README, rundash port + |
| `b90b260` | `dd79c24` | fix(gen): face-key crushed detail to black - shading-only, |
| `b93ddc7` | `09141c0` | docs(spec): wallpaper deck rotator design - once-per-cycle |
| `ba308ff` | `d5c1851` | docs(corpus): apply operator audit - 32 attribution correc |
| `bad25c8` | `0622780` | feat(lw-clean): Dekel multi-image watermark remover (prope |
| `bc5fc19` | `04bcf34` | feat(lw-clean): IOPaint-emulation watermark cleaner (lw_cl |
| `bd7521e` | `04bd1c6` | fix(lw-clean): tighten gate false-positives - bare @ + dil |
| `be057ee` | `329d148` | feat(orchestrator): P7 start gate - a slice cannot begin u |
| `bee362c` | `618f818` | docs(mcp-lift): P5 - memi audited our pages and got them b |
| `bf06cf6` | `da38156` | docs(claude): PreToolUse hooks DO fire headless on 2.1.220 |
| `bf94629` | `0ec750b` | feat(lw-clean): Stage-2 cleaning harness + gate-v2 calibra |
| `bfdae45` | `86aa426` | feat(cleaning): tile on edge-following contours - the seam |
| `bfe0bd8` | `06c430d` | fix(tests): guard the two winmutex semantics tests behind  |
| `c02980a` | `e2a28c1` | fix(loop): the hardcoded root was a class, and I fixed one |
| `c41c5e1` | `de4bd63` | test(loop): port RC's POSIX overlap test - the half a skip |
| `c8eb152` | `bf6dd89` | docs: record the (c) ring fix and what it did not reach |
| `c993009` | `a29a30c` | feat(cleaning): sweep the glyph percentile on 259f, and ca |
| `ca5ecfd` | `7aedbbb` | docs(mcp-lift): the off-list sources ARE retrievable, and  |
| `ca8403a` | `25cf4ac` | fix(hooks): mark .githooks executable so the gate is not i |
| `cb1475f` | `1737f45` | feat(cleaning): let a stub walk further for its expectatio |
| `cb19250` | `d79c494` | fix(done): the gate must grade the tree that gets pushed |
| `cc2875a` | `9aa2da9` | feat(lw-gen): painterly retune step-1 - archetype rubric d |
| `cdc93df` | `25cd11b` | feat(gpu): wire the last three CUDA consumers - the lane i |
| `ce8b4ad` | `b49f9b0` | docs(wakeup): evening session hand-off, prune 2 sessions t |
| `d13cdfc` | `69aee85` | feat(clean): mask-excluded G1 FR, with the tautology guard |
| `d220e6e` | `377afa9` | feat(wallpaper): deck rotator - every image once before an |
| `d37be63` | `e3c9ed1` | docs: the two opt-in lanes run together - 91 percent less  |
| `d441993` | `4522243` | feat(first-pass): bucket-C source recovery + crop-held ful |
| `d5810e8` | `aa500f8` | feat(rundash): join the three run-id namespaces, on eviden |
| `d61e382` | `a7b4374` | feat(ports): name the neighbours, so the registry can say  |
| `d737f01` | `c56fcde` | feat(pipeline): merge the approval-override recording slic |
| `d74888b` | `0fc8cad` | docs(clean): skip-LaMa-when-the-pre-pass-clears, measured  |
| `d77dbe2` | `a2e56d8` | test(lw-gen): tune Vayne animagine brief (canonical navy+c |
| `d7db23e` | `233a28c` | docs: LEDGER 42 + R13 + roadmap/wakeup sync for f1 item 3 |
| `d8f5bc8` | `c2f23a4` | fix(truth_gate): tell "CI will never run" apart from "CI h |
| `d916f9a` | `f178ad9` | fix(ci-watchdog): stop the two-minute console flash on the |
| `d9861e9` | `2672d89` | feat(cleaning): spend the lone crossings, because the pair |
| `da598c1` | `8954e0c` | fix(loop): the no-argv config path resolved on exactly one |
| `dac7872` | `f7a6935` | feat(cleaning): name the flat surround, because 54 blind s |
| `dc4a3bf` | `b5bb95f` | docs(spec): F1 SDK executor channel - retire AHK GUI bridg |
| `dca6071` | `a4376cf` | feat(g1): IllustrationJaNai primary path + frozen G1 gate  |
| `dd0e418` | `7765de7` | docs: the pooled veil estimate failed, and the mechanism i |
| `df6f5bc` | `546b303` | fix(glyphs): one CLAUDE.md rule, one banned set - converge |
| `e0a1250` | `3c95ed6` | docs: sync living docs - first-pass golden set shipped (LE |
| `e132d00` | `45c477e` | feat(gen): face-key correction, validated against the corp |
| `e27054f` | `b83b02c` | docs(corpus): 330-image champion-attribution audit list +  |
| `e31a91a` | `64c6e0c` | ci: add cv-lane so the dekel alignment tests actually regr |
| `e35ea14` | `fad857c` | feat(lw-gen): img2img from a real reference - the painterl |
| `e5bcdc5` | `5a47575` | feat(lw-gen): M1 slice 2 - raw-pose to name-keyed kp_map a |
| `e62543b` | `90be0db` | test(slots): pin RC's ceiling property "never exceeds 5 +  |
| `e63a1b0` | `93b0781` | docs(loop): P4 sdk-channel smoke cycle 2 |
| `e7f98ea` | `5660746` | feat(lw-gen): anime base (Animagine XL 4.0) - the anime-fl |
| `ea05ef3` | `4086b06` | docs: gen-nonahri-deformed round 1 - the pose stack is the |
| `ea74508` | `7701f97` | docs(recover): LEDGER item 8 + ROADMAP - source-recovery c |
| `eb1b671` | `5460c38` | docs: ARCHITECTURE hygiene - fix stale iopaint venv claim  |
| `eb8e442` | `5e3697b` | fix(loop): a recycled pid wedged the headless loop for fiv |
| `ebc970f` | `3df382d` | docs: sync living docs - P7 shipped, LW's f1-phase6 item 7 |
| `ec38749` | `4938a84` | feat(orchestrator): P4 - the file-claim table, so disjoint |
| `ec7c17e` | `ce4c926` | feat(gpu): merge the last three CUDA consumers - no consum |
| `ee73136` | `c13c462` | fix: pin ultralytics autoinstall off in lw_clean_pass itse |
| `eee55d6` | `d893f84` | test: pin pytest testpaths=tests so bare pytest matches CI |
| `ef67c49` | `34f9c3a` | feat(first-pass): record source_mode + alpha_flattened in  |
| `f0ac578` | `7579b38` | feat(lw-gen): splash-booru posing vocab (ArtStation line-o |
| `f293428` | `7ea5775` | fix: move ruff exclude to top level (inert under [lint]) a |
| `f3e34a0` | `3c505f3` | chore(orchestrator): merge the headless run-infra slice |
| `f49102f` | `77e2d25` | feat(cleaning): stack the lane configurations in one colum |
| `f502543` | `275d8a4` | fix(gpu): one GpuBusy for every consumer, and close the tw |
| `f6706d1` | `ba3c4b1` | feat: inherit Riot Commander operating system (ADR-001) |
| `f67c8f4` | `081f597` | test(lw-gen): add splash-anime style + vayne_anime brief ( |
| `f9cd7a1` | `5059848` | docs: ledger 88 - repo went public; sha rewrite map for th |
| `f9f3ecd` | `4a529d6` | docs: LEDGER 113 - long-prompt encoding works and is rever |
| `fa56adc` | `3c56eb0` | fix(pipeline): the canonical backup name must hold the CUR |
| `faac97e` | `398430e` | feat(rundash): merge the verifier-verdict persistence slic |
| `fc4bf4e` | `702cdc7` | docs(roadmap): DWPose is onnx-CPU, so it is not one of the |
| `ff4098f` | `00a21cd` | fix(guard): the console-flash check was a substring test w |
| `ff7e582` | `33830f0` | feat(cleaning): replay the operator's masks - the fill is  |
