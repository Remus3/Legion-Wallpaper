# SHA rewrite map - 2026-10-09 GH-HYGIENE rewrite (LEDGER 292)

FOURTH rewrite of this repo. Ordered by MAIN's REPO-REVIEW ORDER of 2026-10-08
22:46 (section 4), confirmed by the operator in the attended session of
2026-10-09 ("1 yes; 2. yes remove"). Run ONLY through the fleet kit's
`ops/fleet_kit/fleet_rewrite.py` (plan f7f7b61d648d, then run), which drives
`git filter-repo --force` with:

- a mailmap: every non-operator author / committer -> the operator identity
  (the one dependabot-authored commit `2c6a492`, committer `GitHub`);
- a message callback: strips AI / bot co-author and sign-off trailers and every
  `Claude-*:` line (six commits carried one, among them the v12 adoption
  `e601e50`, whose `Claude-Session:` line the operator ordered removed);
- `--replace-text` from a LOCAL, gitignored replace file: the account and
  organisation UUID of README-AUDIT finding 3.1 -> `<account-uuid>` /
  `<org-uuid>` in every historical blob (the two commits that carried them).

Plan before: 759 commits scanned (every branch), 7 to rewrite (ai-or-bot-author
1, claude-trailer 6, non-operator-committer 1, trailer 1), replace #1 and #2 in
2 commits each, 0 HEAD hits. Plan after: 760 scanned, 0 to rewrite, 0 replace
hits. `fleet_identity.py check main`: 758 commits clean.

The oldest changed commit is the one that first added the UUIDs (2026-09-20),
so every sha from there on changed: 153 on main, 2 on local side
branches, 155 in all. No commit was dropped. The HEAD TREE is byte-identical
before and after (`a1db95f` on both sides: the scrubbed values had 0 HEAD hits,
removed in the ordinary commit `22a8ee9` -> `a109d9c` first).
Old main tip `22a8ee9` (remote tip `3b62ee4`) -> new `a109d9c`.

HOW TO RESOLVE AN OLD SHA (never chain maps). Look the sha up in THIS table
first; if it is not here it did not change in this rewrite. This rewrite
touched only commits from 2026-09-20 on, and none of its OLD shas appears in
the 2026-09-07 map (0 overlap, checked), so for a sha older than 2026-09-07
the 09-07 map alone still answers - this map never needs to be walked after it.

Backup: a full `git bundle --all` (10 refs, verified) taken by
`fleet_rewrite.py bundle` before the run, in the LW sidecar folder
(`E:\Sidecars\LW\Rewrite-backup\`), sha256 recorded in LEDGER 292.

| old | new | where | subject |
|---|---|---|---|
| `02664d5` | `d27ecd6` | main | feat(gpu): calibration profiles as data with evidence (ing |
| `0335fce` | `6d7b156` | main | feat(ops): lw_watch watcher primitive - baseline, advance  |
| `04fe420` | `e215848` | main | fix(ab_r4): apply the 3 UI-audit MUST-FIX (double-vote bus |
| `062ffd5` | `d3fa56e` | main | chore(fleet): adopt MAIN FLEET-KIT v3 - vendor kit, confor |
| `07e3fa2` | `2bee396` | main | refactor(ops): lw_ops_tasks to MAIN 0020 section 4 task-en |
| `07f3244` | `da7ec8f` | main | docs(handoff): record /done gate RED read-back; hand-off c |
| `082cd18` | `7ea7f68` | main | feat(r4): anime-lama vs LaMa blind A/B prepared, 19 approv |
| `0962316` | `b994c00` | main | fix(responder): the budget is ONE number, 120 runs per 24  |
| `0a0b17e` | `b0edc29` | main | fix(truth_gate): the no-path-filter tripwire was blind to  |
| `0aa78f0` | `047c76c` | main | docs(r5): DINOv2 patch-kNN residue map NOT ACCEPTED; no do |
| `0bc2253` | `4d52490` | main | build(fleet): vendor FLEET-KIT v8 (MAIN 0310) |
| `113fa22` | `28c93d5` | main | docs(roadmap): close stale transcript-key Now row (LEDGER  |
| `13a83c1` | `898cdc0` | main | feat(ops): promise watch over CLAUDE.md Reverse-if entries |
| `1451ac6` | `a5463c0` | main | fix(paths): derive LW root from __file__ / lw_paths, guard |
| `14a11be` | `5923fa4` | main | feat(g1): CAMBI banding arm G1.cambi_delta PROVEN 12/12 (r |
| `15000a2` | `83dd9f6` | main | docs(skills): failure catalogues for cleaning lane, first  |
| `16d9134` | `c029bf3` | main | feat(headless): every headless claude spawn goes through t |
| `17b5326` | `0d26158` | main | feat(ops): per-job run log, tri-state job health, rundash  |
| `1ac1a01` | `ef2fff4` | main | test(state): present-but-empty fixtures for the ingest-tou |
| `1d8fd05` | `a91dc65` | main | feat(fleet): roster change - EW (Ebonwake) joins, LL (Lant |
| `1db7f65` | `9a764a2` | main | fix(guards): RC half-move no-git guard, stdin shutdown cra |
| `1f56c0f` | `8b525e0` | main | docs(handoff): C4 round closed - slots.py 290cbf80 on all  |
| `1fe3db8` | `d54380a` | main | fix(responder): drop DETACHED_PROCESS - it disabled CREATE |
| `21a210b` | `38836a4` | main | fix(paths): derive the C:\Tools root, junction-off proof ( |
| `22a8ee9` | `a109d9c` | main | fix(hygiene): scrub account and org UUIDs, add keyed-UUID  |
| `248abe8` | `a523735` | main | refactor(ops): lw_watch to MAIN 0020 section 4 watcher con |
| `2575942` | `c4aa242` | main | Merge branch 'main' into lw/triage-wip-finish |
| `28e5b49` | `01bdfb1` | main | fix: my WAKEUP entry went in at the top of a newest-first  |
| `2a2625f` | `7572072` | main | docs: session 68 wrap - LEDGER 289, wakeup notes, hand-off |
| `2b3c84d` | `695a9ac` | main | refactor(ops): job health + served version to MAIN 0020 se |
| `2b4a266` | `ab6fbde` | main | docs: /done - research R1-R5 shipped, R4 A/B ready, hriful |
| `2bb65f5` | `636b2f8` | main | docs: sync living docs - operator arming, the responder th |
| `2c06e38` | `7bca065` | main | docs: record the MAIN stand-in grant - the operator grante |
| `2c6a492` | `06b2d35` | main | build(deps): bump the github-actions group with 2 updates  |
| `2e6ac2b` | `9d02b1a` | main | docs: hand-off carries Dependabot PR #1 merge; MAIN 0300 d |
| `2f1b070` | `d99cdb4` | main | docs: session 67 wrap - LEDGER 283, wakeup notes, hand-off |
| `31604ac` | `2ad315f` | main | docs(ledger): yuumi first pass approved (operator); cleani |
| `31bd485` | `dab729c` | main | docs: the joint re-pin round is ONE item, not two, and its |
| `322abbd` | `4e4d36e` | main | docs(handoff): ingest LW-ops lane - LEDGER 256-257, archit |
| `3498768` | `9a67e3c` | main | fix(tests): two invalid escape sequences, and the class gu |
| `380d160` | `1ddcc26` | main | docs(readme): banner from hosted social preview, no tracke |
| `3b62ee4` | `048bc64` | main | docs(handoff): kit v13 context, REPO-REVIEW and KIT-SPAWN- |
| `3bb4ad1` | `00b4631` | main | feat(responder): the parent verifies MAIN provenance from  |
| `3dbf336` | `9e96e05` | main | docs(roadmap): LW withdraws its own margin sentence, re-is |
| `3e4a54f` | `451f110` | main | test(lw_facts): spy the reported-record writer instead of  |
| `3ea5fed` | `a45e379` | main | docs(handoff): carry ingest LW-gates findings + operator v |
| `4096078` | `af5b063` | main | fix(hooks): Stop gate emits one feedback line, not an erro |
| `422d4c9` | `8425226` | main | build(fleet): vendor FLEET-KIT v9, /done marker + Stop hoo |
| `42ed383` | `6430fd6` | main | fix(gate): conditional green phrasing is a plan, not a cla |
| `436e20b` | `f4546e6` | main | fix(gate): the PreToolUse gate read the SESSION tree, not  |
| `446b7c9` | `d91d98f` | main | chore(fleet): vendor MAIN FLEET-KIT v7 (11 files) and re-e |
| `451f30d` | `9664415` | main | fix(ci): the revived ruff gate went red on a fixture that  |
| `4654c32` | `b50f2c5` | main | docs: ledger 234 and hand-off - tripwire parser fixed, C4  |
| `4a5e9ad` | `2de1179` | main | docs(ledger): ingest P0-1, P0-2, P0-4, P0-5, P1-6 landed w |
| `4c7d729` | `3fbfd0d` | main | docs(ledger): LEDGER 242 - FLEET-KIT v3 adopted, MAIN 1029 |
| `4e49d0c` | `5038a06` | main | feat(guards): the history-aware identity gate, and the res |
| `4f2106c` | `1b0936a` | main | test(responder): observe the no-scheduler claim at run tim |
| `5068eeb` | `fc70a16` | main | fix: the union tool would have DUPLICATED 346 records - it |
| `55c18c8` | `8234ad9` | main | test(inbox-status): track he.kit.KIT_VERSION, not a stale  |
| `57da489` | `db6dfd1` | main | fix(loop): the executor directive quoted a pre-round-B dig |
| `58ff889` | `3c87c6f` | main | docs: sync living docs - inbox triage, kit-pin fix, triage |
| `5a05e6f` | `2e6e96a` | main | docs: LEDGER 281 kit v9 reply + CI, hand-off carries MIG-1 |
| `5a38893` | `d30765c` | main | docs: the hand-off went stale in an hour - five notes land |
| `5d50e2c` | `377c085` | main | docs: LEDGER 275 supply-chain hardening (MAIN 0300) |
| `62442fc` | `8f5c86d` | main | chore(fleet): adopt MAIN FLEET-KIT v4 - vendor 5 files, sp |
| `6673203` | `5a8613c` | main | docs(handoff): /done close - LEDGER 261 live read-back; yu |
| `672c2e9` | `d96aa6e` | main | fix(clean): skip REJECTED workings in select_working_image |
| `68aaf57` | `c477587` | main | chore(commands): drop Firecrawl from the headless research |
| `6ab5765` | `2c59e1a` | main | docs: ledger 233 and hand-off - responder self-loop closed |
| `6dbe5e9` | `8b013e8` | main | fix(guards): three sibling defect classes measured in LW - |
| `6e1da28` | `cd164c3` | main | fix(loop): an unaudited cycle no longer advances the clean |
| `6ff360d` | `0516ebc` | main | feat(g2): residue_mf LIVE in clean verify; OCR+MSER text_r |
| `700cd64` | `277b314` | main | feat(loop): land joint-round C4 in ops/loop/slots.py - LW  |
| `7061dc9` | `04705ed` | main | docs(handoff): owed queue empty; headless children commit  |
| `7101023` | `f458047` | main | feat(pipeline): stage ledger + end-review lock gate (inges |
| `7290b81` | `866ce24` | main | fix(fleet): v7 adoption follow-ups - checklist CLAUDE.md t |
| `791b431` | `bd5413c` | main | docs: ledger 239 - stop-gate no-verify false positive, MAI |
| `79d201e` | `547efbe` | main | docs(claude): repo-relative paths in agent + command instr |
| `7b79eaa` | `15c5402` | main | refactor(responder): inbox seen-set on lw_watch.run_source |
| `7c6d639` | `ec297fe` | main | fix: two guards that could not fail - the shared-file arms |
| `7d54d16` | `0ed0453` | main | fix(tests): give LW its own pytest temp root, out of the s |
| `80d5922` | `bc82ea2` | main | feat(gates): fault-proven gate board; strict G2 outside ar |
| `82ae760` | `4567a40` | main | fix(clean): rejected candidates re-shipped as clean-scan;  |
| `8530e48` | `767e196` | main | refactor(ci_watchdog): settled-failure handling on lw_watc |
| `8573634` | `8fc8877` | main | docs: sync living docs - round B landed, transcript split  |
| `864a173` | `8545bbc` | main | docs(handoff): 7 slugs intaken + first-passed, awaiting op |
| `883b5f2` | `fdde253` | main | fix(headless): launch the resolved claude.CMD, not the bar |
| `8a0e9ad` | `7fcce75` | main | docs: session 64 wrap - LEDGER 280, wakeup notes, hand-off |
| `8af8a2d` | `f367d10` | main | docs(ledger): 285 sync-reply-arm - proxy outage, owed MAIN |
| `8b1c09e` | `daee2a3` | main | docs(roadmap): the bytes are FROZEN at da35f8b1 and 2.0 is |
| `8c2ca8e` | `683dfc5` | main | docs: ledger 235 and hand-off - unaudited verdict, and the |
| `8f4ed93` | `5f56bc7` | main | fix(paths): tools_dir builds one string so POSIX CI does n |
| `8f593f8` | `16bb0c3` | main | feat(review): reviewability pre-check + picture-judging do |
| `9355c6d` | `b39b3ca` | main | docs: sync living docs - the 12-day gap, three false green |
| `937d745` | `6f0df7f` | main | feat(fleet): adopt MAIN FLEET-KIT v13 - identity hooks, no |
| `93b61d5` | `ffda59a` | main | docs(readme): 2026-10-03 presentation pass - live status,  |
| `9506a9a` | `5b5f60c` | main | Merge branch 'worktree-agent-ad6f0167d0529b955' |
| `96c94dd` | `12b81d9` | main | docs: sync living docs - the backlog answered, the round f |
| `96ea28e` | `5a8bec8` | main | docs(handoff): the inbox responder is armed, not a do-not- |
| `98a08ac` | `caba51f` | main | docs: the frozen candidate failed on landing - a carrier c |
| `9989ca0` | `38b5555` | main | feat(g2): seam_step live in clean verify; ring-SSIM seam f |
| `9cca88b` | `ef3a2cc` | main | docs(handoff): C4 carrier tally 2 of 5 from own-disk hashe |
| `a23fc68` | `54952aa` | main | fix(loop): bound the executor slot wait, and the owed hold |
| `a29cbe7` | `8d3ee8c` | main | docs: LEDGER 277 R4 unvoted, R5c blocked, G1.lpips arm pro |
| `a329840` | `d27b8d4` | main | feat(review): P1-2 acceptance met; operator residue marks  |
| `a3515d6` | `3332b22` | main | feat(fleet): adopt MAIN FLEET-KIT v11 - triage_spawn_kwarg |
| `a416222` | `283bdeb` | main | feat(fleet): adopt MAIN FLEET-KIT v10 - SUBAGENT-FIRST hoo |
| `a4a8f4d` | `1dcb556` | main | docs(handoff): session 6 - FLEET-KIT v3 adopted, C4 tally  |
| `a5568d0` | `7af7b36` | main | docs(ledger): cite RSC halt clause by name - the line guar |
| `a70da35` | `5edd898` | main | feat(ops): verified operator-task engine; hand-off asks re |
| `aa9774a` | `10d7628` | main | fix(recover): campaign imports lw_paths via the tools pack |
| `acd2335` | `75e53a5` | main | build(ci): supply-chain hardening - dependabot, SHA pins,  |
| `ae144d0` | `773d949` | main | docs: /done - C4 round closed and pushed; research experim |
| `af5d876` | `efc4ea5` | main | docs(handoff): session 7 - FLEET-KIT v4 adopted, v5 gaps + |
| `b118f36` | `25f9d96` | main | fix(tests): two asserts were printing the whole environmen |
| `b32e632` | `b811d06` | main | feat(inbox): finish item-14 classify-first responder; reco |
| `b45005d` | `4d7275e` | main | feat(review): spatial review bench - marks on the image be |
| `b6484a1` | `ed533e3` | main | feat(g1): cambi_delta live in the first pass; blind band_d |
| `b7d50a7` | `01e83ca` | main | fix(responder): never spawn on LW's own notes or on a TERM |
| `ba3ecc4` | `5328a88` | main | feat(responder): publish the lane widget's inbox status fi |
| `bac788f` | `d9bbbf1` | main | feat(g1): retire G1.band_delta board row + ack entry; R1b  |
| `bdc0486` | `8476e02` | main | feat(g2): re-inpaint matched filter G2.text_residue_mf PRO |
| `c1a32c3` | `2f5ea39` | main | refactor(recover): read API-Key-*.txt via vendored fleet_s |
| `c509021` | `42e0214` | main | Merge branch 'lw/triage-wip-finish' |
| `c6e9984` | `cf2b4a8` | main | docs(research): MoE / MIM / ExPLoRA survey mapped to the b |
| `c8b0c6c` | `5c8294f` | main | fix(gate): read no-verify per simple command, not across a |
| `cb34f3a` | `e1f0aa4` | main | docs: ledger 235 - the held loop model id answers through  |
| `cc4912d` | `43e44f8` | main | fix(review): bench showed no image - slug picker + auto-lo |
| `cd05625` | `3b1cc2d` | main | fix(tests): the new empty-parametrize arm inherited the en |
| `d013ae0` | `680c921` | main | docs: sync living docs - the inbox round, the two dead gua |
| `d1a8566` | `740eeb1` | main | perf(headless): lean flags on every claude spawn, sonnet f |
| `d3c036c` | `41c949e` | main | fix(tests): a guard told me a pytest feature had changed w |
| `d612b43` | `0a3f4d4` | main | docs: ledger 240 - MAIN 0912 headless overhead cut |
| `d65067f` | `b29005e` | side branch | chore(wip): preserve abandoned v6 responder attempt before |
| `d6cdf87` | `c32a2ea` | main | docs: answer CS's credential/PII ACTION note, and remove L |
| `d871a57` | `2e54f30` | main | docs: LEDGER 274 roster change; hand-off drops ROSTER, car |
| `d927d07` | `7fa73ff` | main | feat(httpd): /api/version on every lw_httpd server + serve |
| `daa846c` | `6617a85` | side branch | build(deps): bump the github-actions group with 2 updates |
| `dbe1b03` | `4ae0655` | main | docs(roadmap): the round's first candidate attestation, CS |
| `dbf067e` | `ac50e57` | main | test(responder): guard the live run log at the writer, not |
| `df2fb8a` | `d4e5c58` | main | feat(responder): one uniform budget at ten times the old f |
| `e2aa704` | `a5b2cc6` | main | docs: sync living docs - session 5 intake + first pass of  |
| `e466348` | `45fb1e8` | main | feat(loop): AHK bridge single-paste delivery, target proce |
| `e50866d` | `50753d1` | main | docs(roadmap): close stale pytest temp-root row (fixed at  |
| `e601e50` | `b7bc64d` | main | feat(fleet): adopt MAIN FLEET-KIT v12 race guards - gitloc |
| `eb69fef` | `c9b3cdd` | main | chore(inbox): park INCOMPLETE item-14 triage responder WIP |
| `eb7b02b` | `2888bed` | main | Merge branch 'worktree-agent-a6608fdf6d94503e6' |
| `ed25c00` | `29aaf94` | main | fix(loop): derive repo root and control dir, drop C: liter |
| `f0fe8f6` | `662f2ae` | main | docs: LEDGER 282 MIG-1 prune done, move to E: staged, hand |
| `f145dd8` | `8ebf72d` | main | docs(handoff): first line records hand-off held local (gat |
| `f68ed40` | `27f1e20` | main | feat(ops): isolated verify copy of live runtime state + da |
| `f99e358` | `7d499a9` | main | docs: ledger 238 - audit-hook arm, live-file guards moved  |
| `fc6cdb4` | `625c048` | main | refactor(headless): route every headless claude spawn thro |
| `fd4d63f` | `6a75eeb` | main | feat(fleet): v6 lanes (cap 3, worktree per lane, one gover |
| `fe71425` | `7cb5bbf` | main | docs: ledger 232 and hand-off - C4 landed in LW first, rou |
