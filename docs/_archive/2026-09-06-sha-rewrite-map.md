# SHA rewrite map - 2026-09-06 Claude co-author trailer purge

GitHub listed `claude` as a repo Contributor (2 contributors: `Remus3` +
`claude`). The cause was 84 commits dated 2026-07-03 through 2026-07-26 that
still carried a `Co-Authored-By: Claude ... <noreply@anthropic.com>` trailer -
authored BEFORE `.githooks/commit-msg` started stripping it on 2026-07-26.
GitHub credits co-author trailers to the matching account, so the only way to
drop the contributor was to remove the trailers from history.

`git filter-repo --force --message-callback <strip Claude/anthropic.com
Co-Authored-By lines>` rewrote ALL 483 commits (the first affected commit is
the repo's first commit, so every downstream sha moved). 483 commits in, 483
out - no commit dropped, no author or committer identity touched (all 483 stay
`Moonbeam <redacted>`), and the HEAD tree is byte-identical
before and after (`1c558e45aaa12ea8ff8e7c19b4e40859be9a2927` on both sides),
so not one file changed. Old HEAD `aa99af3` -> new HEAD `16bc443`.

Verified after the force-push: `GET /repos/Remus3/Legion-Wallpaper/contributors`
returns exactly one entry, `Remus3` with 483 contributions.

One prose mention of the trailer survives on purpose, in the body of
"docs(commands): stop instructing the banned Claude co-author trailer" - it is
a sentence describing the ban, not a trailer, and it carries no email, so it is
not attributable.

Trailer counts: 63 `Claude Opus 4.8`, 18 `Claude Fable 5`, 3 `Claude Opus 5`.

This table maps every OLD sha cited in a tracked `.md` that no longer resolves
to its rewritten replacement. 255 entries - every commit sha cited anywhere in
tracked Markdown, since this rewrite moved all of them. The doc text itself was
deliberately NOT edited: the ledger is append-only and the old shas are
accurate labels for what happened at the time.

Chaining note: this is the SECOND rewrite. The 2026-08-01 blob purge is mapped
in `docs/_archive/2026-08-01-sha-rewrite-map.md`; its "new sha" column entries
are themselves cited in tracked Markdown, so they appear in the "old sha"
column below. To resolve a sha from before 2026-08-01, walk that map first,
then this one.

The authoritative full 484-line map lived at `.git/filter-repo/commit-map` on
the operator's box and is NOT tracked (it is local git plumbing, and it is
regenerated/overwritten by any later rewrite). This table is the durable
subset - the shas anything in the repo actually references.

Backup of the pre-rewrite history was taken as a `git bundle --all` before the
filter ran; it is a session scratch artifact, not tracked.

| old sha | new sha | subject |
|---|---|---|
| `00ae1f4` | `88db039` | docs(g1): merge the USM halo census slice |
| `0184089` | `b2aba78` | fix(cleaning): a stub may add a verdict, never soften a ch |
| `0204cfa` | `017d8cd` | feat(lw-gen): M2 W3 IP-Adapter weapon rung - transplant +  |
| `024d0a8` | `62e7867` | fix(test): assert the CUDA DLL PATH policy on POSIX too in |
| `02a9bdc` | `beb7280` | fix(loop): a hung sdk child could not be killed, and the l |
| `0472a72` | `5852ea4` | ci: arm the git-hook gate in cv-lane, teach the parity gua |
| `065679b` | `ab4d2ea` | test(lw-gen): harden hand/pose negatives + prove img2img-f |
| `07b7e30` | `5190caa` | feat(lw-clean): SDXL reconstruction inpaint worker (lw_cle |
| `07ed5bc` | `c48b283` | fix(truth_gate): tell CI will never run apart from CI has  |
| `09e4905` | `7cf585f` | ci: arm the git-hook gate in the checkout instead of asser |
| `0c255d8` | `31f59c4` | feat(lw-gen): W4 M3 - wire rung==w4 weapon-concept LoRA in |
| `0c9b1f5` | `986a8a7` | chore(first-pass): triage the 9 residual working slugs |
| `0cce31a` | `589da92` | perf(dwpose): bind the CUDA execution provider, and wire i |
| `0cd8991` | `72732ad` | feat(rundash): P1b Cycle History panel, and the cost bound |
| `0f7bab3` | `d12d11c` | docs(cleaning): algebraic-only reviewed too - 2 of 45, rem |
| `109124d` | `abb2fe7` | feat(clean): overlay matte seeds the LaMa mask - 32/32 und |
| `1253bab` | `e3ab6fc` | feat(rundash): P4 Operator Queue and P5 Suite Trajectory |
| `15844aa` | `4ae9e28` | chore: repo renamed to Remus3/LegionWallpaper, update wake |
| `17693cb` | `1db81ab` | fix(wallpaper): time trigger so rotation starts without wa |
| `17db253` | `f6b8bef` | docs: record the wiki reference set and the dead-end galle |
| `18b7ddd` | `f2a0d26` | fix(loop): unserialized mutex holds were invisible to the  |
| `191742a` | `de2596f` | chore(first-pass): merge the R26 alpha audit slice |
| `1998e2b` | `76c4731` | fix(guard): a RENAMED sibling repo must go red, not quiet |
| `19b5848` | `0f57ef0` | docs(spec): F1 P5 PASSED - concurrent LW+RC run, all four  |
| `1d3631b` | `33eaebb` | feat: restoration pipeline v1 - state machine, monitor, st |
| `1dbfc2d` | `615c52b` | feat(gen): port weapon renderer to glb named joints |
| `1ea9144` | `4b2ef50` | fix: stop the test suite destroying the lw-clean venv (ult |
| `1ef672e` | `dd44d81` | chore(sync): Resin Compute replaces Red Moon in the govern |
| `2028026` | `97b4036` | feat(first-pass): operator-directed crop override for aspe |
| `202cef3` | `55495b0` | chore(loop): point the directive_suffix at the f1-phase6 d |
| `2248313` | `a7f28dd` | fix(cleaning): one verified IOPAINT_LAUNCH constant, kill  |
| `24b7d5f` | `ae3b690` | feat(gen): IP-Adapter reference-image guidance on the txt2 |
| `25bafcc` | `c89a56c` | docs: RESTORATION_PLAN hygiene - fix stale iopaint venv re |
| `269cba6` | `3eb3b29` | docs(first-pass): run the last 5 slugs, and the census kil |
| `26c5ae3` | `198ed9a` | ci(cv-lane): run tools/test_lw_clean_dekel.py - 8 tests th |
| `2894e0b` | `e111233` | feat(lw-gen): calibrate QA floors on real Vayne sweep (T_b |
| `2958338` | `598f2e7` | fix: cleaning retry default 1 - measured, retries never wi |
| `2b94040` | `e3f9e0d` | fix(tests): the wired fixture must install hooks executabl |
| `2fe8087` | `b38192d` | feat(intake): perceptual near-dup gate - the twin the byte |
| `3070b2e` | `c59880c` | feat(loop): P3 - machine-wide concurrency governor (slots, |
| `30e98cd` | `7cc6630` | fix(cleaning): a stub speaks with the others or not at all |
| `31e5d96` | `50ff873` | docs(mcp-lift): P3 - the wiki has the pixels, and neither  |
| `31e68c7` | `6c4fc00` | docs(triage): LW-native MCP lift triage - 63 links, LW rub |
| `34506a4` | `af47dc7` | feat(lw-gen): M1 weapon-region gate - CLIP is a dead gate, |
| `34d366a` | `f11f56a` | feat(gen): face-realism block for splash-booru, measured a |
| `357b0a6` | `51a3eae` | feat(gen): recover the medium yardstick as a tool, measure |
| `363d9e5` | `b305e59` | feat(cleaning): run the credit-line lane on the queue, and |
| `375afdd` | `8ac7af7` | feat(first-pass): merge the fetched-fullview glob slice |
| `37741ea` | `cba4968` | feat(golden): promote V3 detail DAT2 to primary + re-freez |
| `3a3f6f7` | `24b30f5` | feat: guard the Desktop hand-off target, wire it into /don |
| `3a8a296` | `997ce41` | docs: sync living docs - ledger 146-150, two open roadmap  |
| `3b8e0f1` | `cc7454e` | docs: 46 held refs intaken to first-pass scratch (LEDGER 3 |
| `3bd9a8b` | `8b009ac` | fix(loop): the POSIX winmutex branch was unserialized AND  |
| `3c4e704` | `5bcd761` | docs: pay the ledger the interrupted session owed |
| `3cc6d8f` | `7725e4a` | feat(render): preserve the .skn multi-angle renderer as tr |
| `3d81298` | `290dae1` | feat(pipeline): remove subcommand - a sanctioned writer fo |
| `3f2b9bc` | `f04f308` | fix(gen): never drop a frame the face-key cannot score |
| `4184ad2` | `a59b01a` | test: cover align_rois (10 tests, lw-clean venv) and corre |
| `418f328` | `da18dd3` | feat(cleaning): template detection + scheduled fill on the |
| `44cb0f2` | `2a48870` | feat(lw-gen): M2 W2 reference-transplant rung - affine cro |
| `4682b5c` | `5d51b3f` | docs(cleaning): second hand-clean capture confirms the str |
| `47903a2` | `e590f18` | fix(clean): measure where the credit line starts instead o |
| `486b5f5` | `6a88278` | fix(cleaning): record the 45/45 overlay rejection, split f |
| `4a1cc3a` | `4f6db7b` | docs: AGENTS hygiene pass (R10) |
| `4a7c047` | `297eb13` | feat(cleaning): a second credit-line round, and what it co |
| `4c5abf7` | `1e291bd` | feat(cleaning): residue-targeted passes - the text finally |
| `4c97b95` | `6c608ca` | fix(tests): raw strings for the two backslash paths I ship |
| `4dbe017` | `f0faf11` | feat(cleaning): sweep the percentile on all ten, and close |
| `4e3b617` | `7c6d645` | chore: Apache-2.0 LICENSE, untrack + purge the root style  |
| `4f88831` | `29fef5b` | chore(loop): flip to N=3 and apply the three-repo slots re |
| `5099a48` | `3fd2040` | feat(rundash): the directive-history spine - run id, cost, |
| `511f1d8` | `e54aed6` | chore(meta): add self-authored social preview card for the |
| `547dffd` | `3ba8856` | feat(rundash): merge the run dashboard server and page |
| `549f52c` | `04d2397` | fix(loop): the sdk executor never logged the session id it |
| `5527059` | `c5c86ed` | docs(clean): matte rebuilt on the wider grid - alpha 0.133 |
| `5715cf0` | `91eb4d3` | fix(golden): pin the USM recipe against lw_upscale, not a  |
| `58896c5` | `b494820` | docs(loop): P5 concurrent smoke cycle 2 |
| `58b30c4` | `7156408` | docs: WAKEUP hygiene - relocate W4-M3 session to history_n |
| `58dc53c` | `0129a78` | feat(first-pass): merge slice b - carry usm_applied into G |
| `5aec00d` | `dd00b11` | feat(lw-gen): wire subject-LoRA loading + --lora-path/--no |
| `5c2cf42` | `3bbd5e0` | feat(recover): SauceNAO multipart POST + campaign driver + |
| `5d2600e` | `5f409a2` | feat(rundash): persist verifier verdicts so the P2 chip ca |
| `5e9c691` | `1e29905` | docs(cleaning): 0 of 87 automated candidates accepted - cl |
| `5f6f119` | `259856e` | feat(dwpose): stamp eval runs with their bound providers;  |
| `60461ae` | `07ce48c` | feat(gen): pull a canonical LoL wiki reference set for lw- |
| `60dd217` | `35dc86e` | feat(anat): merge the head-spine diagnostic slice - gating |
| `61b34f4` | `0e2ec81` | feat(loop): truth_gate persists what it observed onto the  |
| `62555c6` | `973799d` | docs(first-pass): batch 5 more slugs, and all five were hi |
| `63cc35b` | `f5e66e7` | docs: ref triage - 226 clean delivered, 46 held (LEDGER 35 |
| `646263d` | `707897b` | docs(loop): P5 concurrent smoke cycle 1 |
| `6737d04` | `fe0478a` | docs: orchestration plan R11 DONE (8fd5d40) |
| `6830211` | `8a88bb6` | fix(loop): wire truth_gate into the run flow, and fix what |
| `690ffb7` | `7029acd` | fix(ops): LW-WeeklyHygiene opened a visible powershell con |
| `693920f` | `3bf620b` | feat(lw-gen): M1 slice 1 - pure weapon-mask derivation (we |
| `6c0423c` | `faac443` | ci: docs-only pushes ran no CI while guards read docs off  |
| `6c6006a` | `32f642f` | feat(first-pass): needauth queue cleared + bucket A+B held |
| `6cebfd7` | `8fd5d40` | docs: DEEP_AUDIT_CHARTER hygiene pass (R11) |
| `6cffc3d` | `6f6eb58` | feat(upscale): G0 over-target source-gate - downscale-only |
| `6db5443` | `133a41a` | fix(pipeline): prune Done N at the transition, not at Done |
| `6e1aa9b` | `1f4cfe7` | docs(backlog): P6 closed as NOT APPLICABLE - LW replays no |
| `6f07bd5` | `788dcd9` | docs(gen): record the 616.56 driver and the CUDA-12 onnxru |
| `6fffd74` | `4ef047c` | chore: drop tracked scratch dumps and untrack a stray log |
| `70838da` | `f9f0a51` | feat(lw-gen): W4 M2 - in-house UNet-only SDXL LoRA trainer |
| `711f5f9` | `d0aeed7` | fix(loop): the director stamped its own premises and nothi |
| `71bf503` | `859d676` | fix(clean): the veil ring was hiding a cliff the lane itse |
| `737a160` | `02f80bf` | feat(cleaning): dispose the 566-slug cleaning corpus gate- |
| `7453936` | `731cbe0` | chore: apply UP017 - datetime.timezone.utc to datetime.UTC |
| `74a6b09` | `eb340e4` | feat(clean): one engine per submission - drop the cross-en |
| `751702d` | `a1b55d2` | feat(hooks): P1 - the Stop-hook claimed-green gate, and th |
| `7657356` | `b18e5ae` | feat(lw-gen): W4 M1 - weapon-crop curation tool (DWPose au |
| `77937d2` | `382955f` | feat(gpu): merge the GPU mutex wiring slice |
| `7809618` | `cb0f00f` | docs: rewrite README for an outward audience - badges, pip |
| `7826b22` | `95c5b32` | docs(corpus): apply 122 operator champion labels to CHAMPI |
| `78a0521` | `50cc628` | feat(pipeline): flag a globally-filtered submission at sav |
| `78d0ad1` | `d8285a9` | docs: weekly hygiene - relocate 2026-08-02 session, keep W |
| `7927d09` | `4fae78f` | docs(mcp-lift): stage-4 deep dive - all 63 read at source, |
| `7a20a0f` | `7bc1dab` | docs(mcp-lift): close L1, kill L2's flag half, file the Gp |
| `7afb92f` | `cc7c1b5` | docs: ROADMAP hygiene - drop LEDGER-superseded blocks, res |
| `7b11f21` | `5b221f1` | feat(first-pass): ADR-006 downscale-only drops G1 lap_rati |
| `7d1796b` | `9a6bd65` | test: probe torch-free imports in a clean interpreter, not |
| `7d4b6ef` | `79105d6` | feat(cleaning): generate the operator's mask schedule - fi |
| `7d62062` | `84f3dcb` | chore: ruff target-version py39 -> py312, ratchet UP017 +  |
| `7d6a3ca` | `a835c5c` | feat(lw-gen): provision + prove Phase-0 (RealVis SDXL, sm_ |
| `7e21c9d` | `305dd2a` | feat(lw-gen): M1 localizer - adopt DWPose onnx-CPU (5/6 vs |
| `7e5374c` | `11dc35e` | fix(loop): my config-path fix made the Windows paths in it |
| `7ea35e6` | `26bc9d7` | fix(tests): the teardown test asserted taskkill on a platf |
| `7ea5707` | `cda487b` | feat(guard): scan agent config, and fix the trust-key bug  |
| `7fe4785` | `ce7702b` | feat(rundash): P6 Fleet History - read the mirror nothing  |
| `7fffd41` | `bf81475` | test(loop): measure three-way concurrency with real proces |
| `808d96b` | `ab59bbd` | fix(pipeline): finalize silently dropped an operator audit |
| `81de837` | `7ff7f22` | chore(rename): the local root is "C:\Legion Wallpaper", wi |
| `827e688` | `665661f` | docs: the 65 decomposed - two levers falsified, the reach  |
| `82aacc2` | `bd129b1` | feat(first-pass): committed lw_first_pass driver (intake-> |
| `834b74e` | `56c3233` | feat(lw-gen): M1 weapon pass W1 - DWPose-wrist masked SDXL |
| `852a721` | `84b881f` | fix(rundash): a live clock made the time-in-status bound f |
| `8562788` | `e094571` | docs: BACKLOG hygiene - drop expired product-TBD notations |
| `8717016` | `2312e5c` | fix(recover): merge the oEmbed-inconclusive slice |
| `8766adf` | `ae47462` | fix(clean): the veil gain was a boundary solution, not a f |
| `879ddd6` | `a6d9dca` | fix(recover): P2 - mockd replay, and the non-200 branch it |
| `88e1ac7` | `3a9a010` | fix(clean): keep artwork out of the fill mask |
| `8971391` | `077acd6` | docs(cleaning): quantify the operator's 82-step hand clean |
| `89f55ae` | `a785cb6` | feat(cleaning): scope the revert to the line it damaged, n |
| `8a3fcae` | `b73cb05` | feat(cleaning): approve the 7 detector false positives une |
| `8afab90` | `64e75d0` | feat(intake): 20 originals intaken with the recovery water |
| `8c0a67c` | `dca54ec` | feat(cleaning): drive the 87-slug manual QA lane, 85 candi |
| `8e30892` | `c5af7c2` | feat(lw-gen): ControlNet-OpenPose pose control - natural p |
| `8e8b9a0` | `9325139` | feat(golden): lw_golden.py freeze/regress tool + gitignore |
| `907ff46` | `e5a35ca` | fix(ops): P0 correction - the gate was wired into the ACTI |
| `920afeb` | `14f200e` | feat(loop): no Claude dollar cap or accounting - it does n |
| `92b89ba` | `77107d4` | feat(golden): re-freeze all 12 baselines under USM 35 and  |
| `936d99b` | `ba6440b` | feat(golden): freeze first-pass golden set (10 blessed IJN |
| `9451535` | `5a18ca6` | fix(recover): the one-off diagnostic still called an incon |
| `9477a7e` | `9ee3834` | docs(first-pass): the 46-slug upscale batch has nothing to |
| `94db5d0` | `9510ebe` | feat(cleaning): scoped revert defaults ON, because the pai |
| `9718e05` | `92f482d` | docs: analysis-by-synthesis needs a matched pair, and none |
| `973838f` | `6a54b3b` | docs: archive RESTORATION_PLAN_v1.md to docs/_archive (R9) |
| `98f1d65` | `68262a7` | feat(cleaning): relative residue measure - built, calibrat |
| `9c14b8d` | `1958edb` | fix(upscale): merge slice a - no resample, no unsharp mask |
| `9e48223` | `c81b033` | docs: OPERATIONS hygiene - drop stale TBD tags on existing |
| `9ed619b` | `1686e87` | feat(cleaning): tiled decomposition worker - built, measur |
| `a019586` | `0ef1cb7` | docs(wakeup): record the root rename and the expected slot |
| `a116989` | `1bc2aa1` | feat(clean): record the mark a step hands back; falsify th |
| `a15394b` | `4a09385` | fix: resolve both B905 sites per-site, drop the ignore |
| `a214af6` | `0a37c43` | fix(loop): label the static suffix, and make the stdin-cap |
| `a270dce` | `53f68d6` | feat(clean): land the confirmed per-slug presets and drain |
| `a469624` | `0f1bcf4` | docs: look at all 39 credit-line sheets, flag-only |
| `a68aa77` | `3966058` | fix(cleaning): share the mask-coverage guard across every  |
| `a72ea8b` | `23f951c` | feat(ops): adopt per-session drift guard, keep full suite  |
| `a751b19` | `4cd50d2` | feat(rundash): mirror the agent fleet before Claude Code r |
| `a7dfde5` | `b0db9b6` | docs(commands): stop instructing the banned Claude co-auth |
| `a934243` | `dd88f1f` | feat(lw-gen): M0 foundations - Animagine config flip, pose |
| `abc8f14` | `bea479f` | feat(cleaning): gate subdivision on gradient; blanket esca |
| `ad4643e` | `77931fe` | feat(cleaning): 107 analysed - fill holds, the residue det |
| `ad99249` | `a24f401` | fix(first-pass): an apostrophe in a source filename killed |
| `b096533` | `e249335` | chore: CI python 3.12 -> 3.14, ruff target-version py314 |
| `b14b688` | `c7dead1` | fix(g1): cap FR common scale so DISTS stops OOMing on 8K s |
| `b1ad327` | `a781012` | docs(loop): P4 sdk-channel smoke cycle 1 |
| `b2c932f` | `69d301f` | feat(pipeline): reopen - the reverse move, and the academy |
| `b2fc3a2` | `dc7c308` | feat(lw-gen): generator sidecar (run/qa/promote) + /genera |
| `b61c1a5` | `5a19635` | feat(recover): source-recovery waterfall scaffolding + art |
| `b63992a` | `83305d0` | docs(gen): close glb-render-pipeline, open glb-render-fetc |
| `b6b69e9` | `2c58d70` | feat(ops): P0 - move the glyph/ruff gate into git hooks, e |
| `b80e7cb` | `9681f1a` | docs: sync living docs - ADR-009 in README, rundash port + |
| `b90b260` | `5339690` | fix(gen): face-key crushed detail to black - shading-only, |
| `b93ddc7` | `04eea5c` | docs(spec): wallpaper deck rotator design - once-per-cycle |
| `ba308ff` | `88eff59` | docs(corpus): apply operator audit - 32 attribution correc |
| `bad25c8` | `0aa8424` | feat(lw-clean): Dekel multi-image watermark remover (prope |
| `bc5fc19` | `c9f6c8d` | feat(lw-clean): IOPaint-emulation watermark cleaner (lw_cl |
| `bd7521e` | `e56eace` | fix(lw-clean): tighten gate false-positives - bare @ + dil |
| `be057ee` | `b3e28e8` | feat(orchestrator): P7 start gate - a slice cannot begin u |
| `bee362c` | `504fb65` | docs(mcp-lift): P5 - memi audited our pages and got them b |
| `bf06cf6` | `ba41cbc` | docs(claude): PreToolUse hooks DO fire headless on 2.1.220 |
| `bf94629` | `22ab8bb` | feat(lw-clean): Stage-2 cleaning harness + gate-v2 calibra |
| `bfdae45` | `c7ef7cb` | feat(cleaning): tile on edge-following contours - the seam |
| `bfe0bd8` | `33c3b2a` | fix(tests): guard the two winmutex semantics tests behind  |
| `c02980a` | `56a7d9e` | fix(loop): the hardcoded root was a class, and I fixed one |
| `c41c5e1` | `57829bf` | test(loop): port RC's POSIX overlap test - the half a skip |
| `c8eb152` | `ac267a4` | docs: record the (c) ring fix and what it did not reach |
| `c993009` | `d903ce3` | feat(cleaning): sweep the glyph percentile on 259f, and ca |
| `ca5ecfd` | `6083318` | docs(mcp-lift): the off-list sources ARE retrievable, and  |
| `ca8403a` | `d4b0a11` | fix(hooks): mark .githooks executable so the gate is not i |
| `cb1475f` | `ef277f4` | feat(cleaning): let a stub walk further for its expectatio |
| `cc2875a` | `0a67df3` | feat(lw-gen): painterly retune step-1 - archetype rubric d |
| `cdc93df` | `5c0f9b4` | feat(gpu): wire the last three CUDA consumers - the lane i |
| `ce8b4ad` | `c812305` | docs(wakeup): evening session hand-off, prune 2 sessions t |
| `d13cdfc` | `e6fe340` | feat(clean): mask-excluded G1 FR, with the tautology guard |
| `d220e6e` | `519112e` | feat(wallpaper): deck rotator - every image once before an |
| `d37be63` | `daa07b8` | docs: the two opt-in lanes run together - 91 percent less  |
| `d441993` | `76b2af8` | feat(first-pass): bucket-C source recovery + crop-held ful |
| `d5810e8` | `acbc16c` | feat(rundash): join the three run-id namespaces, on eviden |
| `d61e382` | `79d14f4` | feat(ports): name the neighbours, so the registry can say  |
| `d737f01` | `480d55d` | feat(pipeline): merge the approval-override recording slic |
| `d74888b` | `d61a4b4` | docs(clean): skip-LaMa-when-the-pre-pass-clears, measured  |
| `d77dbe2` | `1cbb36b` | test(lw-gen): tune Vayne animagine brief (canonical navy+c |
| `d7db23e` | `22de10d` | docs: LEDGER 42 + R13 + roadmap/wakeup sync for f1 item 3 |
| `d8f5bc8` | `ece6577` | fix(truth_gate): tell "CI will never run" apart from "CI h |
| `d916f9a` | `f02e273` | fix(ci-watchdog): stop the two-minute console flash on the |
| `d9861e9` | `a50955a` | feat(cleaning): spend the lone crossings, because the pair |
| `da598c1` | `bc95e92` | fix(loop): the no-argv config path resolved on exactly one |
| `dac7872` | `f3eeefb` | feat(cleaning): name the flat surround, because 54 blind s |
| `dc4a3bf` | `7e639a8` | docs(spec): F1 SDK executor channel - retire AHK GUI bridg |
| `dca6071` | `b37f5b1` | feat(g1): IllustrationJaNai primary path + frozen G1 gate  |
| `dd0e418` | `b671bc8` | docs: the pooled veil estimate failed, and the mechanism i |
| `e0a1250` | `67c2a83` | docs: sync living docs - first-pass golden set shipped (LE |
| `e132d00` | `9d220f4` | feat(gen): face-key correction, validated against the corp |
| `e27054f` | `b87de59` | docs(corpus): 330-image champion-attribution audit list +  |
| `e31a91a` | `b8e6533` | ci: add cv-lane so the dekel alignment tests actually regr |
| `e35ea14` | `eab398d` | feat(lw-gen): img2img from a real reference - the painterl |
| `e5bcdc5` | `c9f8a26` | feat(lw-gen): M1 slice 2 - raw-pose to name-keyed kp_map a |
| `e63a1b0` | `e894514` | docs(loop): P4 sdk-channel smoke cycle 2 |
| `e7f98ea` | `d82837c` | feat(lw-gen): anime base (Animagine XL 4.0) - the anime-fl |
| `ea05ef3` | `6d29c29` | docs: gen-nonahri-deformed round 1 - the pose stack is the |
| `ea74508` | `159c428` | docs(recover): LEDGER item 8 + ROADMAP - source-recovery c |
| `eb1b671` | `45b561c` | docs: ARCHITECTURE hygiene - fix stale iopaint venv claim  |
| `eb8e442` | `5578578` | fix(loop): a recycled pid wedged the headless loop for fiv |
| `ebc970f` | `926de20` | docs: sync living docs - P7 shipped, LW's f1-phase6 item 7 |
| `ec38749` | `ab802ee` | feat(orchestrator): P4 - the file-claim table, so disjoint |
| `ec7c17e` | `dbdf28e` | feat(gpu): merge the last three CUDA consumers - no consum |
| `ee73136` | `494184e` | fix: pin ultralytics autoinstall off in lw_clean_pass itse |
| `eee55d6` | `fb38a3f` | test: pin pytest testpaths=tests so bare pytest matches CI |
| `ef67c49` | `cdab825` | feat(first-pass): record source_mode + alpha_flattened in  |
| `f0ac578` | `022fac7` | feat(lw-gen): splash-booru posing vocab (ArtStation line-o |
| `f293428` | `f74e750` | fix: move ruff exclude to top level (inert under [lint]) a |
| `f3e34a0` | `9e4488f` | chore(orchestrator): merge the headless run-infra slice |
| `f49102f` | `6e833ed` | feat(cleaning): stack the lane configurations in one colum |
| `f502543` | `e510be0` | fix(gpu): one GpuBusy for every consumer, and close the tw |
| `f6706d1` | `d35714c` | feat: inherit Riot Commander operating system (ADR-001) |
| `f67c8f4` | `aea981c` | test(lw-gen): add splash-anime style + vayne_anime brief ( |
| `f9cd7a1` | `8ef9c12` | docs: ledger 88 - repo went public; sha rewrite map for th |
| `f9f3ecd` | `af579d2` | docs: LEDGER 113 - long-prompt encoding works and is rever |
| `fa56adc` | `62a20e5` | fix(pipeline): the canonical backup name must hold the CUR |
| `faac97e` | `1f2a592` | feat(rundash): merge the verifier-verdict persistence slic |
| `fc4bf4e` | `8ec4332` | docs(roadmap): DWPose is onnx-CPU, so it is not one of the |
| `ff4098f` | `9425b71` | fix(guard): the console-flash check was a substring test w |
| `ff7e582` | `1270b41` | feat(cleaning): replay the operator's masks - the fill is  |
