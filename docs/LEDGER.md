# Legion Wallpaper - Item Ledger

Append-only, newest-first per-item completion record. Kept OUT of `CLAUDE.md`
by design (CLAUDE.md has a hard per-turn auto-load size budget - never append
ledger entries there). Do not rewrite history - append each new item at the TOP
of the body below (newest-first, directly under the `---` rule), matching the
entry format documented here.

**Entry format** (one numbered block per completed item, numbering starts at 1
and only ever increases):

```
N. DONE **YYYY-MM-DD (short title; commit SHAs or "docs-only").** Body: what
   shipped, premise verification, how it was built (TDD RED-first evidence,
   worktree slices, verifier verdict), what was verified (suite counts, health
   checks), doc/roadmap syncs, and any FUTURE / do-not-redo notes.
```

Conventions carried from the format's origin: bold date+title lead; premise
VERIFIED/CORRECTED called out explicitly; verification evidence (test counts,
exit codes, health probes) stated, never implied; scope calls and rejected
alternatives logged so they are not re-litigated.

This file keeps the newest 20 entries. Older ones are per month under `docs/ledger/`
(index `docs/ledger/README.md`); `python tools/lw_ledger.py rotate` moves them, and a
rotation is a move, proven entry by entry. Item numbers never change.

Pointers: open work -> `ROADMAP.md` + `BACKLOG.md`; recent sessions ->
`WAKEUP_NOTES.md`; pruned ledger items + archived wakeups ->
`docs/history_notes.md`; decisions -> `docs/adr/`.

---

377. DONE **2026-11-15 (veil-pass5: taller/wider credit box, membrane seam fix of every LaMa fill, contour profile subtraction, ring-hue metric; pass 5 as the next working on all 55 DA-veil slugs).**
   ORDER (operator review of pass 4): credit bottom-edge smudge (meramora, anime-poster-of-soraka, seraphine-by-pebano1),
   inkshadow top-left shadow + ghost lines, 122 ghosting (122_logo_1x.png frame 3 = the pass-4 column: faint outline
   lines on flat skin), hue step where the veil edge sits on background. ROOT CAUSES (measured): (1) credit font is not
   one size - the big font (A, meramora) reaches 63 px + ~3 px drop shadow under the logo foot (0.143 lh) where pass 4's
   box ended at 64 px, and its "(c)" sits ~0.72 lh from the centre where pass 4's reach was the seed's fixed 0.70; LaMa
   extended the cut glyphs (bottom smear, soraka's grey disc). (2)+(3) LaMa's ring fill comes back with a level /
   colour step at its seams - a GREEN deficit of 1-2 levels on the truth pairs (C ring a*/b* bias +0.79 / -0.67) the
   pre-pass does not have - plus a thin coherent edge profile; on 122 the lines sit at the ring seams (-4.75 / +3.5 px).
   NOT JPEG chroma blur (input chroma ratio steps within 2 px on A/B/C). FIX: tools/lw_veil_pass5.py (CREDIT_ROWS
   0.050-0.160, CREDIT_HALF floor 0.78; membrane_fill: harmonic correction from the capped, art-edge down-weighted
   boundary step; contour_profile_fix: per 32 px cell quadratic art + tent profile -5..+5 px, Tukey IRLS, 3x3 coherence
   median, cap 3 levels; seam_fix), lw_veil_credit.locate_credit(rows=, half=, seed_rows=) (defaults = pass 4; the
   reach is read in the text rows only - reading it in the taller box widened C to 1.05 lh, caught), clean_slug(pass5=True)
   / --pass5. METRIC tools/lw_veil_hue.py ring_hue_step (independent, output + coverage only): Spearman 0.986 / 0.994 /
   0.901 vs true ring chroma error on 18 injected tints per pair; veil-free floor p95 2.35 -> HUE_GATE 2.4 (reported).
   TRUTH full lane, pass 4 -> pass 5 (C held out; A/B LOO): edge +-3 ref px C 31.78 -> 32.07, A 26.96 -> 27.19, B
   30.91 -> 31.07 dB; ring deltaE C 3.04 -> 2.60; logo unchanged (36.19 -> 36.17); credit band PSNR lower (C 29.26 ->
   26.84: LaMa fills a larger box, no text on any). Rejected with numbers: wide profile (C 30.09), octant profile vs
   linear trend (C 29.59), local halo-gain refit, interior boundary harmonization (C logo 35.67), per-frame text
   detector (~15 / 55 misses). RUN 55 / 55 from source (6 workers): G2 outside 0, change_ssim max 0.871, resid
   -0.018..+0.013, gate pass 55 (pre-pass mismatch rule now outside LaMa mask OR edge support: 0 on 55); ghost lower on
   55 / 55 (median 0.53 -> 0.34), ring hue lower on 52 (median 0.97 -> 0.49), shading median 1.58 -> 1.33. VISUAL all
   55 at 3x: clean 38, faint border residue 12 (incl. 122 fainter, inkshadow top-left unchanged), worse than pass 4 5
   (credit box LaMa invention: 284f, 286f, ahri-khanzaaiart, yunara, bayonetta-dm7iirw), credit smudge 0; meramora /
   soraka / seraphine-by-pebano1 credit fixed. Saved as the next _cleanworking (dry then real, 55 rc 0); 246
   pre-existing scratch files byte-identical, 55 new = candidates, scan anomalies 0, nothing approved, never
   --allow-ladder. PICKS.md: PASS5 on 50, PASS4 on the 5 regressions. Tests tests/test_lw_veil_pass5.py (12,
   mutation-proven: 5 mutants). Doc docs/_archive/2026-11/VEIL_PASS5_2026-11-15.md.
   SUITE (fleet_suite_gate --exclusive, tools/lw_suite.py -q): parallel 4502 passed 19 skipped, serial 183 passed 1
   skipped, rc 0.
   OPEN: faint border lines on 12 (manual IOPaint); credit box could shrink on small-font lines with a reliable detector.

376. DONE **2026-11-15 (veil-pass4: static alpha field + shading metric + whole credit-line box; pass 4 as the next working on all 55 DA-veil slugs incl. 224f / bamboo-gal / 262f).**
   ORDER (operator, after pass 3): "still some off color on the veil - and the signature line needs work ... still
   after edit shading and inconsistency remaining"; follow-up: include 224f / bamboo-gal / 262f. ROOT CAUSES (purchased
   pairs at 2560, clean frame known, C held out): (1)+(2) ONE cause - the fill alpha is not a scalar: it falls top->foot
   (grid plane slope -0.033..-0.040 on A/B/C, field corr A-C 0.976, C rms vs A+B field 0.0033) and the per-frame fit
   reads it 4-11 pct low (kappa 1.040 / 1.111 / 1.084); a scalar inversion leaves top under / foot over and an e (W - J)
   tint on chromatic art. NOT chromatic (per-channel alpha within 1 pct; gains measured worse), NOT gamma (linear-light
   model rms 5.0 vs sRGB 3.5 on C, tone-dependent), no tone curve needed. (3) credit line = white fill alpha ~0.14-0.15
   + dark rim, FIXED row 0.06-0.13 logo heights under the logo, CENTRED; pass 3's seed+completion missed end glyphs and
   whole words. FIX (lw_clean_overlay PASS-4 block, lw_clean_iopaint --pass4, defaults = pass 3 byte for byte):
   pair_true_alpha_sums (builder) / build/save/load_pair_alpha_field / render_pair_ratio / pair_alpha_field_crop,
   remove_pair_edge + pair_ring_envelope(alpha_field=); tools/lw_veil_alpha_field.py builds
   ops/runtime/clean/da_veil_pair_alpha_field.npz (gitignored) from A+B ONLY (kappa mean 1.0758); tools/lw_veil_credit.py
   (row from the logo, half-width = the lane's own detection's farthest reach, mirrored, +0.12 lh; the whole box to
   LaMa). Rejected with numbers: per-glyph analytic de-blend (outline stays visible), glyph-support mask (fragments).
   METRIC tools/lw_veil_shading.py (independent; Lab plane+step across the contour per logo third): Spearman 0.91 / 0.96
   / 0.86 vs true LF deltaE on 15 injected candidates per pair; veil-free floor p95 3.17 -> SHADING_GATE 3.2 (reported).
   TRUTH C held out, full lane: logo 35.41 -> 36.19 dB, deltaE 1.86 -> 1.70 (floor 1.65), shading 1.43 -> 1.06, ghost
   0.33 -> 0.37; pre-pass LF error 1.83 -> 0.54. A not improved (lowest kappa). RUN 55 / 55 (5 workers): gates pass 55
   (5 via a kappa-free retry after a negative resid fail), outside_max_abs 0, ghost max 1.86; credit removed 55 / 55;
   border classes clean 34 / faint 20 / worse 1 (258-cleanup outline); saved as the next _cleanworking (dry run then
   real), 191 pre-existing scratch files byte-identical, 55 new = candidates, scan anomalies 0, NEEDAUTH kept, nothing
   approved, never --allow-ladder. PICKS.md: PASS4 on all 55 (+ manual IOPaint note on 258-cleanup, 224f, bamboo-gal,
   262f). Tests tests/test_lw_veil_pass4.py (12, mutation-proven). Doc docs/_archive/2026-11/VEIL_PASS4_2026-11-15.md.
   SUITE (fleet_suite_gate --exclusive, tools/lw_suite.py -q): parallel 4489 passed 19 skipped 1 failed
   (test_every_cited_docs_path_resolves: the new doc was not yet tracked) -> staged, that file re-run 3 passed;
   serial 183 passed 1 skipped.
   OPEN: local faint border lines (20 + 258-cleanup) - manual IOPaint or a local-patch lane; resid gate shares the
   edge-read bias (-0.01 on C).

375. DONE **2026-11-15 (veil-pass3: static edge correction + fine scale + bounded LaMa ring; pass 3 as the next working on 25 of the 26 non-clean DA-veil slugs).**
   ORDER (operator): one more pass for the border ghosting/artifacts, KEEP the NEEDAUTHs. ROOT CAUSES (measured on the
   purchased pairs at 2560, clean frame known): (1) TIP DOT = model fill ~0.7 px too far into the bay end (error -11..-16
   levels at sd +0.4..+1.7 px) -> dark px at the ring's inner edge, grown by LaMa; the true local edge offset is ~85 pct
   STATIC along the contour (LOO corr 0.86/0.87/0.90, p10/p90 -0.6/+0.8 ref px) and the per-frame field tracks it only at
   corr 0.66-0.79 - also the faint per-side line; (2) SCALE never refined (search steps 0.04): blood-moon at 1.08 vs a
   score peak at 1.065 (390 -> 495), fit dy/d0 at bounds; truth pairs peak at ~1.005; (3) BLOTCHES = LaMa in the 5 px ring
   along a shallow art edge smears colour tens of levels off the right pre-pass. FIX (lw_clean_overlay PASS-3 block,
   lw_clean_iopaint --pass3, default off = pass 2 byte for byte): static field (pair_true_edge_offsets builder-only,
   build/save/load_pair_edge_corr, render_pair_grid, pair_signed_distance(edge_corr=)), refine_pair_scale, ring fill
   clamped to pair_ring_envelope (edge +-0.75 px, halo +-50 pct, never narrower than pre-pass +-16 levels: tol 0 put
   261f's removed line back). tools/lw_veil_edge_corr.py builds ops/runtime/clean/da_veil_pair_edge_corr.npz (gitignored)
   from A+B ONLY (C held out). Found live: clean_slug shadowed `region` with the clamp map -> json.dumps crash; renamed.
   TRUTH full lane edge dB p2 -> p3: A 23.38 -> 26.93, B 29.94 -> 30.98, held-out C 29.19 -> 31.94, C1920 28.98 -> 31.60;
   C ghost 0.64 -> 0.38; costs: C logo -0.20 / C1920 -0.12 dB, A ghost 0.51 -> 0.63. PASS 3 (26): G2 outside 0 px 26/26,
   gate 25 pass (262f resid -0.028 not saved); visual vs pass 2: clean 7, faint line 15, still ghost 3 (224f, bamboo-gal,
   262f), worse in a patch 1 (261f); zero residue still NOT met on 19. No-save sample of 5 clean slugs: never worse (245f
   tip dot gone). STORAGE: save-working -> _cleanworking_02 x24 + blood-moon _01; 166 pre-existing scratch files sha256
   identical; scan anomalies 0; nothing approved, never --allow-ladder. Picks (gitignored)
   images/_veil_pairs/2026-11-15/PICKS.md: pass3 21, pass2 32, NEEDAUTH 2. TDD: tests/test_lw_veil_pass3.py (14; RED on
   the missing API first), mutation-proven (start-scale refine, zero field, no-op clamp, field not added, region shadow).
   Details: docs/_archive/2026-11/VEIL_PASS3_2026-11-15.md.

374. DONE **2026-11-15 (veil-pass2: border ghost root cause, edge-ghost metric, per-frame edge-profile fit; pass 2 as an ADDITIONAL candidate on 55 slugs; submit skips rejected workings).**
   ORDER (operator): one more pass on the DA-veil NEEDAUTHs for border ghosting / artifacts, KEEP the NEEDAUTHs.
   ROOT CAUSE (measured): purchased pairs A/B/C pushed through the real first-pass chain (veiled and clean preview ->
   IllustrationJaNai V3 + USM -> 2560) give lane-resolution truth. The veil edge there is ~1 px wide vs the matte's ~3 px
   ramp, 0.5-1 px OUTSIDE the matte contour, ~0.3-0.4 px off vertically, wobbles +-1 px per edge segment; the dark halo
   reaches ~20 px (black alpha 0.03-0.06 at 4-8 px) and was never inverted. Lane pre-pass residual +0.04-0.05 alpha on
   the edge, +0.01-0.02 just inside the ring, dark band outside it. Visual on the 55 current candidates: faint outline
   lines 55, dark blotch/dot at the left-arm tip 31, strong dark edge line 22.
   METRIC tools/lw_veil_ghost.py edge_ghost (per edge octant x side bin, smooth-art weighted MEDIAN of the high-pass,
   line_rms): injected errors on the truth pairs (shift/offset/halo/blur, 23 per pair) Spearman 0.92/0.98/0.95; veil-free
   floor (30 frames) median 0.19 p95 2.00 -> GHOST_LINE_GATE 2.0; halo statistic info only (floor p95 4.3); never calls a fit.
   FIX lw_clean_overlay PASS-2 EDGE PROFILE: sub-pixel signed distance, fit_pair_edge (dy, dx, d0, sigma, halo k/t;
   planar-art windows, robust log loss; a start-point "smoother half" found dy -0.03 for a true -0.4 and was replaced),
   pair_edge_offsets (per-pixel offset along the contour), remove_pair_edge (fill AND halo), ring from the fitted edge.
   overlay_prepass/clean_slug edge_fit=False default (byte-identical), --edge-fit. Truth pre-pass edge dB A 25.55->26.29,
   B 28.00->29.94, C 28.74->32.21; held-out C full lane at preview logo 34.34->34.78, edge 28.86->29.64, far unchanged.
   PASS 2 (55 = 54 NEEDAUTH + 225f): G2 outside 0 px 55/55; resid median +0.0007; ghost median 1.50 -> 0.54 (over gate
   15 -> 1); gate pass 53 (fail 262f resid -0.025, blood-moon ghost 2.12). Visual: 29 clean, 13 better but faint line,
   8 new LaMa ring blotch, 4 same/still ghost, 1 worse (blood-moon). STORAGE: save-working writes the next working beside
   a waiting needauth (lw_pipeline.py:1433; scan keeps NEEDAUTH, :467): 52 NEEDAUTH slugs carry _cleanworking_01 = pass 2,
   all 54 needauth files byte-identical after (sha256), scan anomalies 0; 225f saved + submitted. TRAP CLOSED: reject puts
   the needauth at max+1 ABOVE the pass-2 working; cmd_submit now skips REJECTed shas and refuses if all are rejected.
   Operator: approve keeps current; reject + submit takes pass 2. Nothing approved, never --allow-ladder.
   TDD: test_lw_veil_edge_profile.py (11, RED on missing API first), test_lw_veil_ghost.py (7), 2 submit cases in
   test_lw_pipeline_moves.py (RED first). OPEN: left-arm-tip dark dot (LaMa grows 2-3 dark pre-pass px at the ring's
   inner boundary), LaMa ring blotches at the right arm's bottom edge, faint top-edge line on ~13.
   Details: docs/_archive/2026-11/VEIL_PASS2_2026-11-15.md.

373. DONE **2026-11-15 (veil-gate: batch gate residual estimator replaced - colour matched filter on the pre-pass; batch 3 over 22 slugs).**
   DECISION (order, recorded): the gate must not grade the fitter with itself and must track ground truth on A/B/C.
   lw_clean_overlay.pair_residual_alpha: box high-pass (12 ref px) of the frame and of the veil signature
   r[(W - J)cov - J halo] (halo divided out at alpha_used), smooth-art weights 1/(art energy + 16), one r shared by
   R/G/B; never calls fit_pair_alpha / pair_veil_alpha_hat / _strips. pair_gate_frame: graded on the ALGEBRAIC pre-pass
   rebuilt from <slug>_iopaint_before.png, candidate-vs-pre-pass mismatch outside the LaMa mask must be 0 (post-LaMa
   read rejected: A -0.017, slope 0.74-0.87). A/B/C known errors (0, +-0.01, +-0.02, +-0.04; 21 candidates): new |err|
   median 0.0047 max 0.0069 (A -0.006, B +0.005, C +0.000 offsets; +-0.005 met on C only, missed by 0.002 on A/B);
   old step median 0.026 max 0.044 (A -0.026, B -0.009, C -0.043). 30 real arts x synthetic veil (300): new median
   0.0035 p95 0.019 max 0.027; old median 0.0125 p95 0.078. Threshold kept 0.02 = p95 of the new noise floor on 30
   veil-free / cleandone frames (16 veil-free max 0.0195). Batch 3 (15 batch-2 manual + 4 registration + 3 search-found;
   0 NEEDAUTH skipped): G2 outside 0 px 22/22 (281-cleanup no_op), gate 17 -> 15 NEEDAUTH, 2 ADR-009 refused
   (the-ruined-king-viego, fury-tempest-sona); manual 5 (225f -0.040, fantasy-design -0.026, 285f -0.025, ashe -0.023,
   281-cleanup). 225f caught. Nothing approved. tests/test_lw_veil_resid_gate.py (55). Details:
   docs/_archive/2026-11/VEIL_RESID_GATE_2026-11-15.md.

372. DONE **2026-11-15 (veil-alpha: per-frame amplitude + sub-pixel / own registration for the DA logo pair matte; batch 2 over 24 slugs).**
   lw_clean_overlay: fit_pair_alpha (zero-step fit, fill + PAIR_HALO halo model, strips 2-6 ref px both sides, smoother
   half of 15 ref px windows, bisection in PAIR_FIT_BOUNDS 0.03-0.30, clamped fit flagged), refine_pair_shift (integer
   grad-correlation grid + parabola), search_pair_registration (scale about frame centre x shift, 1/4 res);
   lw_clean_iopaint.overlay_prepass(pair_fit=True) + pair_registration (search wins at 1.25x template score; LaMa ring
   kept on the template registration); pair_fit=False = a2eb6c3 path byte for byte. Pairs A/B/C fit - oracle (W 245.1)
   +0.0039 / -0.0005 / -0.0035 (W255-equivalent vs cited 0.1435/0.1396/0.1406: +0.0006 / +0.0007 / -0.0043). Held-out C
   pre-pass 35.19 / 30.46 dB logo / edge (fixed 34.65 / 29.37); full lane 34.34 / 28.86 (fixed 34.38 / 28.89, within
   0.05 dB). The batch-1 step estimator is art-biased (-0.01..-0.04 on the purchased 2560 frames; fit -0.004). Batch 2
   (22 manual + 2 ladder slugs): G2 24/24 outside 0, gate 9 pass -> 6 NEEDAUTH, 3 ADR-009 refused; 15 manual; fits
   0.121-0.187 (median 0.154). 11 NEEDAUTH slugs with |resid| > 0.01 skipped (no clean re-submit). Registration
   "failures": 110-cleanup/122 were amplitude (1.12x zoom registered right); bamboo-gal (template dragged dx +30) and
   fantasy-design (1.2x zoom missed) fixed by own registration; 3 missed family members found (281-cleanup,
   258-cleanup, fury-tempest-sona). Nothing approved. tests/test_lw_veil_alpha_fit.py (29). Details:
   docs/_archive/2026-11/VEIL_ALPHA_FIT_2026-11-15.md.

371. DONE **2026-11-15 (veil-batch: pair-matte overlay lane over the DA logo-veil family in 3.Cleaning Scratch; docs-only).**
   Family by the lane's own presence gate (pair_veil_alpha_hat >= 0.05): 66 of 85 frames (0.088-0.223 vs -0.050..+0.034,
   no frame between); 3 purchased excluded, 63 run. Dry-run all, then clean_slug(overlay=True): 63 cleaned, G2 vs the
   original input 63/63 pass with 0 px changed outside pair coverage + LaMa mask. Batch gate (G2 + registration +
   |residual alpha| <= 0.02, the p75 of the estimator on veil-free frames): 37 pass -> 33 save-working + submit (NEEDAUTH,
   nothing approved), 4 refused by ADR-009 (prior engine; left for an operator --allow-ladder); 26 -> manual IOPaint queue
   (annotate --tool qa), 4 of them registration failures (110-cleanup, 122, bamboo-gal, fantasy-design). Finding: residual
   = frame veil step - 0.151 (median dev 0.002) -> the fixed pair alpha is the limit on upscaled firstdones; per-frame alpha
   is the next slice. Table + method: docs/_archive/2026-11/VEIL_BATCH_2026-11-15.md; crops + contact sheets gitignored
   under images/_veil_pairs/2026-11-15/batch/.

370. DONE **2026-11-15 (veil-wire: DA logo pair matte wired as the preferred veil path + LaMa edge ring; inpaint_lama mod-8 padding root cause; commit in this entry's commit).**
   Premise VERIFIED from docs/_archive/2026-11/VEIL_PAIR_RESULT_2026-11-15.md (149ce0d). Shipped: lw_clean_overlay
   save/load/register_pair_matte, pair_veil_alpha_hat/present, pair_edge_ring, remove_overlay(pair=); lw_clean_iopaint
   overlay_prepass(pair=, return_ring=) + clean_slug --overlay wiring (ring OR-ed after completion; collection seed
   dropped inside the logo box + PAIR_SEED_GUARD 12 ref px; credit line keeps its seed); tools/lw_veil_pair_matte.py
   builder. Asset ops/runtime/clean/da_veil_pair_matte.npz is GITIGNORED (third-party watermark derivative; numbers
   only: alpha 0.1511, W 245.1, 393x294 window shape), regenerated from pairs A+B by the builder. pair=None is the old
   path byte for byte. CORRECTED on the way: (1) a global strip-mean presence check read -0.03 on veiled C -> local
   median step (veiled A/B/C 0.123/0.142/0.112, clean -0.021/-0.013/-0.073, gate 0.05); (2) collection strokes in the
   algebra cost C 1.3 dB near the logo -> dropped when the pair is active; (3) ROOT CAUSE lw_clean_pass.inpaint_lama
   RESIZED simple-lama's mod-8-padded output, stretching every fill by up to 7 px on non-mod-8 ROIs -> crop; this made
   a 1-2 px ring cost 6 dB; earlier LaMa-lane numbers predate the fix. Held-out C (edge PSNR / edge hp-RMS / logo PSNR /
   residual alpha): input 24.71/5.00/21.59/0.151; old lane 21.76/8.70/23.36/0.039; new de-veil 29.37/5.09/34.65/0.0015;
   new full lane (ring 1/3) 28.89/5.74/34.38/0.0014; 0 changed px in the far region from pair+ring. Zero residue NOT
   reached: faint 1 px outline traces remain at 2x (operator crop images/_veil_pairs/2026-11-15/C_pairwire_logo_crop_*.png).
   TDD: tests/test_lw_veil_pair_matte.py (28) RED first (module missing), then green; mod8 test RED (270x401, 301x400)
   then green. Suite via fleet_suite_gate: parallel 4360 passed 19 skipped + serial 183 passed 1 skipped, rc 0 (first
   run RED only on test_docs_root_layout: the 149ce0d doc sat in docs/ root -> moved to docs/_archive/2026-11/).
   FUTURE: residual outline (step-based sub-pixel pair registration or halo term), grade on 2560 firstdones, re-run
   pre-fix LaMa-lane measurements, lw_clean_overlay_schedule still calls overlay_prepass without the pair.
   OPERATOR VERDICT 2026-11-15: PASS on images/_veil_pairs/2026-11-15/C_pairwire_logo_crop_input_prepass_lama_clean_2x.png
   (held-out C dmax7wo, full new lane; a2eb6c3), recorded in VEIL_PAIR_RESULT_2026-11-15.md "Operator verdict".

369. DONE **2026-11-14 (responder-authored worker: MAIN ORDER 2026-11-14-0935 renditions cap, timeout progress, reopen events, agent pins).**
   Provenance: inbox copy and MAIN's committed outbox copy MATCH (verify_main True; 3281 bytes). Item 1: tools/lw_first_pass.py
   cap_needauth_renditions + `--cap-renditions` (RENDITION_CAP 10, newest by mtime kept, older MOVED never deleted into
   ~/Pictures/_needauth_hold, which rotation does not scan; a name clash in the hold is left in place); a non-dry batch that
   submits re-applies it. Run live: found=146 kept=10 moved=136, read back 10 in Pictures, 136 in the hold, 565 images in the
   rotation folder (10/565 = 1.8 pct of the deck), log line in logs/2026-11-14.log. Item 2: lw_inbox_responder.child_progress
   reads progress/responder-run.json under FLEET_ROOT; a timeout disposition (= the run-log reason) now carries its step and pct.
   Item 3: LW-NEXT-SESSION.txt gains a `Parked:` section; GATE-FIFO-WATCH, RETIRE-JUNCTION, READBACK-2237, R5c, REVIEW-DRIVER
   and R4 moved there, each with PARKED 2026-11-14 + its REOPEN ON event. R4 park: lw_ab_r4.py tally refused 2026-11-14
   (operator has not finished the A/B) - reopen on vote (MAIN W44 2026-10-31-2215 park rule). CHECKLIST now 8 open
   (lw_checklist.handoff_items parses 6: ids over 16 chars, KITROLL-RESPONDER-RACE and FIRSTPASS-APPROVE, are skipped by _ITEM).
   Item 4 (D5, MAIN-authorized): .claude/agents/verifier.md pins model: sonnet, effort: medium (read-only, reasons over code);
   tests/test_agent_pins.py mutation-proven (unpinned file -> 2 failed). Tests: test_first_pass_rendition_cap.py (7),
   test_responder_timeout_progress.py (5). Suite via fleet_suite_gate: exit 0, 4512 passed, 19 skipped. ANSWER HOP 2 to MAIN.

368. DONE **2026-11-12 (session 95: CI-94, v30 ANSWER re-sent, inbox triage, FLEET9-READ closed, Pinterest GC, ORIGINALS-DUPS).**
   CI-94: b89d086 ci 42551320229 success; c79d975 (kit v30 adoption, no LEDGER row of its own - recorded here) ci 43198051683 +
   codeql 43198051919 success; nightlies 11-09..11-12 success (gh run list). KIT-IGNORE-GAP closed by c79d975 (tests/conftest.py
   extra_ignore dropped, kit IGNORE pins it). V30 ANSWER: the 04:11 outbox copy was NOT delivered (sender refusal: the PT5M
   responder child claimed the answer channel at 04:01:59, ran 1800.1 s to timeout, sent nothing; MAIN inbox held no LW note
   after 11-05). Re-sent the same answer body (plus delivery note + HOM ack) via the send_answers steps: 2026-11-12-1443-from-
   LW-ANSWER-to-MAIN-batched-1-answers.md, reached 1/1 (re-hashed), cap 1/12. Finding: Maint-KitRollout and the responder both
   worked the v30 ORDER (double run, opus 713 s + sonnet 1800 s); filed as KITROLL-RESPONDER-RACE. The stale kit-rollout-v30
   progress row (5 pct, running) marked done. INBOX: 6 unread classified with fleet_inbox.classify(): MAIN 1200 ORDER (work done,
   LEDGER 367; executor_effort high / oracle_effort medium read back in ops/loop/config.json), SS 1607 + SS 2052 ANSWER (skip,
   addressed to MAIN), MAIN 0340 HOM INFORMATION (TERMINAL, mechanical ack here), MAIN 0345 v30 ORDER (done c79d975 + ANSWER
   above); marked seen 673. MAIN-NOTE-2104 CLOSED: v30 ships (a) INBOX ADDRESSEE and (b) PYTHON FIRST; (c) SS fan-out is SS's
   tree and its cost to LW is gone (kit addressee skip). GATE-FIFO-WATCH, KIT-PUBLIC-GIT: v30 suite-gate diff is held_readonly +
   free_ram_mb only, no verify_kit_commit helper - carried. FLEET9-READ CLOSED: durations.jsonl LW rows 2026-11-05..11-12 = 10
   gated runs, 7 exit 0; 3 non-zero all 11-12 during the v30 double run (04:02 exit 1 = 6 classify-addressee tests, adoption-
   caused, fixed in c79d975; 04:03 exit 1 hold 300 s and 04:38 exit 143 hold 13 s = the responder child's contended/killed runs);
   0 fleet_test_guard hits and 0 budget() misses in logs/ and the responder run log. FIRSTPASS-HOLDS (adjudicated): the 3
   Pinterest thumbs are 236 px wide, so a 16:9 crop after ONE 4x upscale is 944x531 - below 2560x1440 by construction (ADR-003
   single upscale); decision GC with --keep-backup (alternatives: keep held forever; second upscale - forbidden). Method: folder
   copies sent to the Recycle Bin first, _firstinitial sha256 == 9.Image Backup original (3/3), then lw_pipeline remove --yes
   --keep-backup; read back 0 in 1.First Pass Scratch, 3 backups kept. The 4 alphacoders crop holds (crop placement = operator
   pixels) and the 3 lap_ratio fails (source-limited) carried. ORIGINALS-DUPS: both -pre files sha256-equal to their 9.Image
   Backup copies and intaken slugs; no consumer of 0.Originals but intake (which refuses them); sent to the Recycle Bin
   (Microsoft.VisualBasic DeleteFile SendToRecycleBin); read back 0.Originals holds only .gitkeep; operator task
   physical.lux-coven-pre-duplicate-2 closed (its check passed). Gated items probed, none fired: gallery-dl config absent, no
   readback-2237.ok, no R4 votes file (park date 11-14), watch-swap tripwire 3 passed, repo-review progress file gone.

367. DONE **2026-11-08 (responder: MAIN ORDER 2026-11-08-1200 model-and-effort-fit-the-task).**
   Inbox copy re-hashed: sha256 bc9731aecac1365118f2a3b704df4fb416c163fe19fbc4dafe5d4ca63df219dd, 2178 bytes;
   verify_main True (MAIN committed outbox copy). Memory: no prior memory covered model/effort (grep of the
   memory dir: 0 hits); feedback_model_and_effort_fit_the_task.md written byte-for-byte from the note's
   File text block (1036 bytes, sha256 286cd894...ffacd) and the ordered MEMORY.md index line appended
   (operator memory dir, untracked). Applied: the two LW spawns that left effort to a default now set it
   deliberately - loop executor argv `--effort` from `executor_effort` (default high, code-writing cycle),
   loop oracle spawn `effort=` from `oracle_effort` (default medium, read-only judgement); both keys added
   to ops/loop/config.json. Responder and CI-watchdog already pass explicit effort. TDD: 3 new tests failed
   first, then pass. Gated suite: exit 0, 4497 passed, 19 skipped. No reply note (the ORDER says TERMINAL).
   CI-RED-PATHSEP: the push run on 35701f3 (42155626178) and nightlies 42245905502 / 42383018434 / 42491770307
   read failure: tests/test_headless_env_path.py PSF constant carried "C:", which splits on Linux's ":" pathsep
   into a stray "C" entry. Test-only fix (no drive colon off Windows); that file: 6 passed locally.

366. DONE **2026-11-05 (session 93 wrap: DEPENDABOT-PR7, CI-91, KIT-ROLLOUT-READ, RESPONDER-STATE, KIT-SCAN-STALE closed; docs-only).**
   DEPENDABOT-PR7: 93189fe re-applies pytest 9.2.0 + ruff 0.17.3 as an operator commit (path B); PR 7 read back CLOSED;
   suite 4461 passed 20 skipped. CI-91: run 41704024983 on c728dc9 read success. KIT-ROLLOUT-READ: headless_usage.jsonl
   line 64 is the `kit-rollout v28` row, 1020.3 s / 2.716 USD (v27 1647.4 s / 4.205 USD) - LW-3 done-when met.
   RESPONDER-STATE: LW-InboxResponder read Enabled/Running every 5 min, no HALT file; the session-91 Disabled read was
   MAIN's 2026-11-01 quiesce, re-enabled by MAIN Restore-Quiesce 2026-11-02 22:07:49 - CLAUDE.md ENABLED stands.
   KIT-SCAN-STALE: 571 pre-ledger notes baselined as SKIP via fleet_inbox mark_seen (left 0, pending 0); the stray SS
   FIX-to-MAIN pending row closed via mark_work_done. PY-ON-PATH + SS-MAIL: LEDGER 365 (b7ce5df). Inbox: 3 unread read,
   none needs LW action (v28 closed in LEDGER 361/362; SS 1324 to MAIN, LEDGER 363; bundle 25 files byte-match
   ops/fleet_kit); lw_facts --mark-inbox-seen run at /done (667 marked). OUTBOUND: INFORMATION
   2026-11-05-2104-from-LW-INFORMATION-to-MAIN-classify-addressee-child-env-PATH-SS-deliver-fanout.md (sha256 485dd5c0...)
   reached 1/1; LW has no SS carrier, so the SS deliver fan-out item is relayed via MAIN. Unchanged: GATE-FIFO-WATCH (no
   reply), RETIRE-JUNCTION (3/6), WATCH-SWAP tripwire green. /done pre-flight: ruff clean, drift_guard 0 breaches,
   pytest --lf via fleet_suite_gate 4494 passed 19 skipped exit 0.

365. DONE **2026-11-05 (PY-ON-PATH child PATH sanitizer + launch_loop direct launch; SS-MAIL misaddressed-note skip).**
   PY-ON-PATH ROOT CAUSE (investigation this session): Python Manager registers App Paths python.exe /
   pythonw.exe / py.exe (HKCU+HKLM) with Path = its WindowsApps PythonSoftwareFoundation.PythonManager_* dir;
   every ShellExecute launch of a python.exe prepends it to the child PATH, so bare `python` in descendants
   resolved to pythoncore-3.14-64 without pytest. kit child_env (fleet_headless.py:510) copies os.environ as-is.
   FIX 1: tools/lw_headless_env.py sane_path (:153) drops every PATH entry containing
   `\windowsapps\pythonsoftwarefoundation.` (case-insensitive), puts dirname(sys.executable) + its Scripts dir
   (Windows) first, dedupes, keeps the key spelling; child_env (:178) and spawn (:259, via the _sane_run runner
   wrapper :185 - kit.spawn builds its env from os.environ with no parent seam) both apply it; os.environ is
   never mutated. FIX 2: ops/loop/launch_loop.ps1 Start-Direct (:30) = ProcessStartInfo UseShellExecute
   $false + CreateNoWindow $true, replacing both `Start-Process $py` calls (:57 dry stub, :124 controller).
   powershell.exe 5.1 ParseFile: 0 errors; smoke launch through Start-Direct: child PATH had no PSF entry.
   SS-MAIL: SS's responder copies every note to every participant. tools/lw_inbox_responder.py decide (:476)
   now returns SKIP reason `misaddressed` (why `misaddressed: addressed to <CODES> ...`) when addressees()
   (:511) - the fleet-code run anchored right after `-from-<SNDR>-[<CLASS-WORDS>-]to-` (:507) - names neither
   LW nor ALL and is not just the sender (self-correction broadcast); prose `...-owed-to-LL-...` never counts,
   `-to-ALL-SIX-`/`-to-ALL-SEVEN-` parse as ALL, an unknown code ends the run (fail open). Kit SKIP reasons
   (self/terminal) still win. Dry scan of the live inbox (read-only): 14 notes would be misaddressed, all
   addressed to MAIN/RC/LL/RSC, 0 to LW or ALL.
   TDD: tests/test_headless_env_path.py (6), tests/test_inbox_responder_misaddressed.py (23),
   tests/test_launch_loop_direct_launch.py (4) - RED first (18 + 2 failed), then green.
   READ BACK: ruff clean; fleet_suite_gate run lw_suite.py -q exit 0: parallel 4311 passed 19 skipped,
   serial 183 passed 1 skipped (4494 passed, 20 skipped, 0 failed).

364. DONE **2026-11-05 (operator ask: intake + first pass + wallpaper rotation; docs-only, data outside git).**
   INTAKE: 19 loose files in `images/0.Originals`; `lw_pipeline intake --all --dry-run` then execute: 17 intaken,
   2 refused as hash-equal duplicates of existing slugs (lux-coven-crimson-enchantment dms9tlg-pre,
   mel-coven dmv2qac-pre; left in 0.Originals, deletion is the operator's call). Recovery: campaign run after
   intake from verbatim backups staged in a scratch dir (memory recipe); Tier 1 resolved all 17 deviations
   alive, annotated 17, but its fetch reported `not_configured` - `%APPDATA%/gallery-dl/config.json` is ABSENT
   on this box (the DA client-id config the campaign reads is gone). Fetched directly with the documented
   quota-free flags (original=false intermediary=true quality=100): 17 of 17 landed, verified on disk by
   recursive file count; 9 -pre slugs gained pixels (1163-1194w -> 1280w, heimerdinger 1192x670 -> 1600x900),
   8 fullviews same dims at 4-8x the bytes. Fetch sha256 + dims annotated per manifest (`recovery_fetch`);
   `data/recovery/matches.json` merged back to 41 records (the campaign overwrites it).
   FIRST PASS: `lw_first_pass.py --batch` (explicit 17-slug list, dry-run first; never --all-scratch):
   17 PASS / 0 flag / 0 fail / 0 held, V3 DAT2 upscale-4x, 8 auto-cropped to 16:9 (crop_ok). All at
   _firstneedauth, NONE approved. FIRST_SCRATCH now 148 needauth + 10 pre-existing EDITING left untouched:
   7 HELD aspect_crop_heavy (alphacoders 1109171/1125535/663779/706844, 3 pintrest 236px thumbs) need an
   operator `--crop-overrides` or drop; 3 failed G1 lap_ratio 0.91-0.93 < 1.0 on undersized sources
   (1000040081 375w-2x, alphacoders 420408, lolwallpapers 13182) - unfixable without a better source.
   ROTATION: LW-Wallpaper reads files flat under ~/Pictures (`tools/lw_wallpaper_config.json`) and splices new
   files into the owed tail of the current cycle; no code change. 0 of the 148 needauth slugs had a Pictures
   entry. pHash+dHash vs the 555 Pictures files: 2 are the same art as an existing `_cleaninitial`
   (alphacoders 1011889 = djy560k Katarina dp8/dd5; alphacoders 1078487 = thousand-pierced-bear Volibear dp4/dd11),
   confirmed by eye, NOT delivered; 1 review-band hit (hdqwalls caitlyn vs vayne2, 14/14) is different art,
   delivered. 146 copied as `<slug>_firstneedauth.png`, sha256 equal 146/146. READ BACK after the next
   scheduled tick: status present 555 -> 701, deck 701 entries (146 `_firstneedauth`), cycle 125 position
   547/701, last_shown a newly delivered file. FUTURE: when one of these slugs advances, retire its
   `_firstneedauth` twin from Pictures (one entry per slug, LEDGER 121); restore the gallery-dl DA config.

363. DONE **2026-11-03 (responder-authored: SS FIX to MAIN 2026-11-03-1324 kit checklist caps; mechanical ack, no reply; docs-only).**
   Note 2026-11-03-1324-from-SS-FIX-to-MAIN-KIT-checklist-caps-cut-silently-13a-departure-board-displaced-row-ONE-ANSWER.md,
   sha256 7e6976a9533f71f6a9edc47f28fa775956c0df7e0c2500e94e84b08891f34810, 2920 bytes, HOP: 1. Class FIX, sender SS,
   addressee MAIN only (kit defect: ROWS_MAX/CHECKLIST_MAX/[:120] silent cuts, an item 13a ruling, fleet_board displaced row
   marked done); not from MAIN, so no verify_main match applies. Asks nothing of LW; "ONE ANSWER" is MAIN's kit version note.
   No A-action, no kit file touched, no reply (LW never answers for MAIN). SS-MAIL observation: one more SS note addressed
   to MAIN landed in LW's inbox (count 6 since the session-90 tally of 5). FUTURE: vendor the kit version that fixes it (A3/A4).

362. DONE **2026-11-02 (session 216 responder-authored worker: MAIN ORDER 2026-11-01-0825 kit v28, residual check; docs-only).**
   Inbox copy re-hashed sha256 7b2885f093f5099735976c6be56cc6786e76084ebb4a8dd40b09677908653f59, 7442 bytes, equals the parent's
   MAIN-match digest. Residual wiring already landed by dcec270 / LEDGER 361: MANIFEST.json sha256 343471741c03... == section 1,
   conformance() == [] at KIT_VERSION 28 (read back this run), KIT_VERSION pins 28 in tests/test_fleet_kit_conformance.py,
   tests/test_headless_env.py, tests/test_promise_probe_fleet_kit.py, tools/lw_promise_probes.py. No kit recopy, no code change.
   Gated suite this run (fleet_suite_gate, python -m pytest tests -q, log logs/responder-216-suite.log): exit 0, 4461 passed,
   19 skipped. The 1848 ANSWER of session 91 already carried the sha; one short responder-authored HOP 2 note closes the
   pending-ORDER row.

361. DONE **2026-11-01 (session 91 Maint-KitRollout /done: fleet kit v28 adopted dcec270; MAIN ORDER 2026-11-01-0825).**
   Kit v27 -> v28: MANIFEST.json, fleet_headless.py, fleet_identity.py changed (pre-push scans a push whose remote old tip is
   absent locally). KIT_VERSION pins moved in tests/test_fleet_kit_conformance.py, tests/test_headless_env.py,
   tests/test_promise_probe_fleet_kit.py, tools/lw_promise_probes.py. READ BACK at /done: MANIFEST version 28, 24/24 files hash
   equal plus the manifest (25/25), conformance() == [], git show dcec270 author operator. Suite (adoption run, log
   logs/kit-rollout-v28-suite.log): 4278 passed 19 skipped parallel, 183 passed 1 skipped serial, gated exit 0; the wrap bind is
   the graded run. CI READ: dcec270 ci 41369084316 success, codeql 41369084350 success. CI-90 closed: a025932 ci 41364943000
   success. ANSWER moon_sync_outbox/2026-11-01-1848-from-LW-ANSWER-to-MAIN-batched-1-answers.md, HOP 2, reached 1/1; MAIN's copy
   re-hashed at /done equal to the outbox (d2b96815...6015). DEVIATIONS: (1) gitlock owner was the claims hook id instead of
   the ordered kit-rollout.LW, the hook denied that id; the suite gate ran under kit-rollout.LW. (2) send_answers
   (tools/lw_inbox_responder.py:1038) claims under channel "tick" though this was a rollout. (3) The ANSWER went out before CI on
   dcec270 was read; CI read success afterwards. (4) LW-InboxResponder reads Disabled (schtasks 18:50, 18:51; last run 18:41:56,
   result 0; no HALT file) while CLAUDE.md says ENABLED (read back 2026-10-03) and the hand-off said LIVE; not touched, carried as
   RESPONDER-STATE. KIT-ROLLOUT-READ stays open: this run is that nightly but its usage row is not written until it exits.
   Pre-flight: ruff clean, drift_guard 0 breaches; no code authored, --lf skipped.

360. DONE **2026-11-01 (session 90 inbox triage: 13 unread notes, all DONE or NO-ACTION, none open; docs-only).**
   Operator asked to process the inbox. lw_facts unread set 13 of 664, read oldest first by mtime. 6 MAIN notes verify_main True:
   FIX 1935 pillow-13 (8dfef45, LEDGER 347; live open Dependabot alerts 0), ORDER 2045 suite speed (491bb85, LEDGER 348), ORDER 1926
   v23 (121eb25, LEDGER 346), ORDER 2200 v26 (12fe2f6, LEDGER 354), ORDER 2215 W44 (9308fae, LEDGER 355), ORDER 1223 (LEDGER 359): each
   DONE with its ANSWER in MAIN's inbox, hash equal. 2 kit bundles v23 + v26 bundle_verified True, NO-ACTION: superseded, manifest reads v27,
   24/24 files hash. 5 SS notes addressed to MAIN (2230, 2245, 0431, 1324, 1400), all ANSWER/TERMINAL, NO-ACTION. No outbound note, no code
   change. Mark: lw_facts --mark-inbox-seen (no --all). READ BACK: lw_facts "0 unread of 664 notes". INBOX-MARK dropped.
   Why the counts looked inconsistent: _inbox_lines sorts by display name and prints the last 10 (tools/lw_facts.py:893-894), and
   UserPromptSubmit prints only what this session id was not yet shown, so the two hook lists are disjoint parts of the same 13.
   Finished orders stay unread until an explicit lw_facts mark because the responder keeps its own seen store (three stores: lw_facts
   sync_inbox_seen.json, responder state, kit ledger inbox_seen.jsonl).
   Side findings, none acted on, all hand-off rows: DEPENDABOT-PR7 (gh pr view 7 reads OPEN, created 2026-11-01T22:38:50Z, requirements.txt
   + requirements-cv.txt; path B), KIT-SCAN-STALE (fleet_inbox.scan on LW reads 571 unseen, 25 WORK, all pre-ledger; no LW code calls scan
   or session_start), SS-MAIL (SS notes addressed to MAIN land in LW's inbox; cause not established).
   Previous push CI read before this push: 180e340 ci 41351984310 success. FUTURE: CI-90 reads this push's run.

359. DONE **2026-11-01 (MAIN ORDER 2026-11-01-1223 items 1-6 finished by MAIN drive-lw; 2cb0faa 9861028 6cd026c b689256 ca700f8 90917b6 6a3ddc6 cc5ad1a e7421cb).**
   Provenance: inbox copy sha256 prefix df7ed16b, verify_main True. The responder's work run was killed at 1800 s at 12:57
   after items 1-5, committed and unpushed; each ACCEPT was re-read against the tree, none fell short. Item 1: row stays open
   without a reply (tests/test_inbox_responder_orders.py). Item 2: gate read back 2/500. Item 3: cause in lw_kit_adopt.py
   closeout docstring (about 480 s adoption, then a nested /done with 683 s gate wait and a 179 s second suite).
   Item 4: hand-off read back 18856 B (under 20 KB), this entry's commit. Item 5: 358 entries before and after, same digest multiset.
   Item 6 FLEET-9: 8 bounds moved to budget() here (ca700f8 7, 6a3ddc6 1), 3 more already by 5c39ef3 (2026-10-26), pinned by
   tests/test_timing_assertions_use_budget.py (AST scan; red on real offenders, mutant killed). About 90 timeout= hang guards NOT
   converted: expiry there is not the claim under test. MAIN's "29 lines" NOT matched: pattern recorded nowhere; nearest grep at
   395770f 33 lines, 30 without budget, 2 true timing bounds. tests/conftest.py extra_ignore for inbox_pending_orders.json (90917b6)
   is a local widening of the guard; the same gap is in the kit IGNORE, reported to MAIN. Done-when open: FLEET9-READ on or
   after 2026-11-08.
   Suite: 6a3ddc6 RED, 2 failed test_the_interpreter_is_not_a_microsoft_store_stub[python, pythonw], 4271+183 passed: a Python Manager
   package dir matched the whole-word WindowsApps rule though the interpreter runs; fixed cc5ad1a (rule narrowed, both arms pinned),
   e7421cb (fixtures without an account-shaped path; cc5ad1a alone was red on test_no_account_paths, never pushed alone). Whole suite
   on e7421cb through the gate: exit 0, 4278+183 passed, 19+1 skipped, 104 s, no gate wait; live-state guard armed (FLEET_TEST_GUARD
   unset), its failure would be a non-zero exit. CI: 395770f ci 41297519489 success (CI-85); e7421cb ci 41351305098 + codeql
   41351305099 success. Row closed by fleet_inbox.mark_work_done directly (reconcile_orders only closes on an outbox ANSWER): pending
   read empty, scan and session_start do not list the note, enqueue_work on it returns None. No responder run started.
   FUTURE: PY-ON-PATH, KIT-IGNORE-GAP rows. CI-85 and LW1-READ dropped. fleet_done.py mark not run: driver paperwork, not the ritual.

358. DONE **2026-11-01 (session 88 /done wrap: CI-84 closed, RESPONDER-DUP-V27 read back; docs-only).**
   CI read back via gh run list --branch main: a5c05fb (tip of the push that also carried d903c51) ci 41295918326
   success, codeql 41295918373 success - CI-84 dropped. RESPONDER-DUP-V27: the LW-InboxResponder child spawned at
   04:01 on MAIN ORDER 2026-10-31-2347 ended rc 0 at 04:07:53 (headless_usage.jsonl kind order, sonnet), its
   progress file reads done; moon_sync_outbox holds exactly one 2347 ANSWER (2026-11-01-0407, TERMINAL) and
   git log shows no commit after a5c05fb - no duplicate ANSWER, nothing to reconcile. KIT-V27-PENDING carried.
   Pre-flight: ruff clean, drift_guard 0 breaches; --lf skipped (no code authored; the section-7 bind is the
   graded run).

357. DONE **2026-11-01 (Maint-KitRollout: fleet kit v27 adopted; MAIN ORDER 2026-10-31-2347).**
   Inbox copy sha256 056a54a1544fa4c51fe366f6ae11df5ee46c9088babfe7a4ab3ded7ad4f88d6f: verify_main True (MAIN
   committed outbox copy, 10399 bytes); bundle verified at KIT-COMMIT 56d000f (lw_inbox_responder.bundle_verified
   True, lw_kit_adopt.verify_bundle []). Vendored via lw_kit_adopt (byte copy): 8 files changed (MANIFEST.json,
   fleet_claims, fleet_headless, fleet_hook.sh, fleet_inbox, fleet_lanes, fleet_rewrite, fleet_suite_gate); READ
   BACK 24/24 files + MANIFEST.json sha256 0a90af35...e949c1 == section 1; FLEET-COMMON unchanged (no re-embed);
   conformance() == [] at KIT_VERSION 27. Settings unchanged; `{}` piped into both PreToolUse launcher commands:
   exit 0, empty stdout. KIT_VERSION pins 26 -> 27 (tests/test_fleet_kit_conformance.py, tests/test_headless_env.py,
   tests/test_promise_probe_fleet_kit.py, tools/lw_promise_probes.py). Section 4 tests changed: none (no exact
   usage-key spy, no fleet_claims.subprocess patch, no lanes key-set pin hit). Gated suite (fleet_suite_gate, lw_suite):
   4223 passed / 19 skipped parallel + 183 passed / 1 skipped serial, exit 0. NOT DONE, carried (KIT-V27-PENDING):
   section 5 item 3 - lw_inbox_responder now enqueues an ORDER into inbox_work.jsonl on its post-spawn mark_seen
   and never closes it; it must read `fleet_inbox.py pending` first and call mark_work_done after the ANSWER
   (deferred: the responder was live mid-tick on this same note). The LW-InboxResponder tick (pid of 04:01) had
   spawned a duplicate sonnet child on this ORDER concurrently; it was not touched. No rotator / lane loop to
   restart. One HOP 2 answer to MAIN.

356. DONE **2026-10-31 (session 87 / responder 209 /done; docs-only).** Wrap of the session that shipped 12fe2f6
   (FLEET-KIT v26, LEDGER 354) and 9308fae (MAIN 2215 W44 + UI/UX batch, LEDGER 355). CI-83 CLOSED: 9308fae ci
   41270362926 success + codeql 41270363046 success; 12fe2f6 ci 41268603050 + codeql 41268603049 success (gh run
   list read back). ANSWER 2026-10-31-2246 TERMINAL reached 1/1. WP-PICKLOG closed (ROADMAP flipped DONE, live pick
   line in logs/2026-10-31.log 22:28:58). Pre-flight: ruff all checks passed, drift_guard 0 breaches; the
   responder's suite read 4406 passed / 19 skipped with its exit code lost to a shell timeout, so the section-7
   done_gate bind is the graded run. Inbox: 9 unread of 658 left UNMARKED (INBOX-MARK carried with the list).
   inbox-responder progress read running (N1, pct 0, updated 22:22) while responder-run read done 22:47 - not
   touched. Wrap push CI = CI-84.

355. DONE **2026-10-31 (responder: MAIN ORDER 2026-10-31-2215 public view + W44 + UI/UX batched, 6 items).**
   Inbox copy sha256 b873714f7e7428c29deb93858765714280ddfd30d8dbe4ab6b61761a5e21288d (re-hashed; verify_main True
   against MAIN's committed outbox copy, 2405 bytes). Items: (1) README "Where it stands" Corpus + Code rows lose
   every hand-typed count (737/517/70/142/8, 124 tools, 240 files, 4,370 tests, 13 ADRs, 330 items, 830 commits);
   dated pointer to ops/runtime/pipeline_state.json kept. (2) README hero img -> docs/assets/social-preview.png
   (tracked, relative), alt text unchanged. (3) WP-PICKLOG: tools/lw_wallpaper_rotate.py tick() logs
   `pick <file> pos <i>/<n> cycle <c>` after a successful apply (none on dry-run or failed apply); TDD RED 1 failed
   -> green 45 passed; live LW-Wallpaper tick read back in logs/2026-10-31.log at 22:28:58 (pos 425/555 cycle 121).
   (4) R4 park date 2026-11-14 written into the hand-off R4 line; LEDGER park line due on/after 11-14 if tally 0.
   (5) LW-IOPAINT-RISK: .claude/commands/cleaning-pass.md records upstream archived (MAIN-reported, no fixes since
   2025-04; PyPI newest still 1.6.0, read 2026-10-31), pin iopaint==1.6.0 (pip show read back, torch 2.11.0+cu128),
   fallback = lw_clean_iopaint.py <slug> --region x0,y0,x1,y1 in the lw-clean venv. (6) LW-QA-SLIDER: new
   tools/lw_qa_slider.py + tests/test_lw_qa_slider.py (8 tests, RED collection error -> green): static page, one
   NEEDAUTH item, _<stage>initial vs _<stage>needauth in one box with a range divider, newest gate audit beside it;
   live run on a queued first-pass item wrote ops/runtime/review/qa_slider.html with both file URIs and G1 metrics
   (queue 132). 5-phase UI audit (subagent, before commit): 0 MUST-FIX; SHOULDs taken: header landmark,
   aria-valuetext, visible divider bar, overflow-wrap. Not taken: drag on image, verdict emphasis, inline aspect.
   One HOP 2 answer to MAIN.

354. DONE **2026-10-31 (responder: MAIN ORDER 2026-10-31-2200 FLEET-KIT v26 adopted; supersedes v25).**
   Inbox copy sha256 4e4084a6e3068108572ab638616153fb5daf625248a66034af88be421f104290 (re-hashed; == MAIN outbox
   copy, 12621 bytes). Kit vendored byte-for-byte (24 files + fleet_hook.sh), MANIFEST.json sha256
   45b5088e202a0c0c453fb1dc4ca8969783563d60d3b7b02e8d2c5c547fe4edae == section 1; FLEET-COMMON block re-embedded.
   .claude/settings.json: both PreToolUse hooks now `bash fleet_hook.sh <script>` with timeout 15, no `|| true`;
   `{}` piped into each: exit 0, empty stdout. Section 4 tests changed: tests/test_fleet_kit_v10_wiring.py,
   tests/test_fleet_kit_v12_race_guards.py (launcher form, timeout 15), tests/test_hook_interpreter_resolves.py
   (bash allowed, run-check is `echo`), tests/test_tracked_settings_is_safe.py (strip token before basename).
   KIT_VERSION pins 25 -> 26 (tests/test_fleet_kit_conformance.py, tests/test_headless_env.py,
   tests/test_promise_probe_fleet_kit.py, tools/lw_promise_probes.py). No LW lane loop running (nothing to restart).
   No run budget was hand-reset. One HOP 2 answer to MAIN.

353. DONE **2026-10-28 (Maint-KitRollout: fleet kit v25 LANE-CAP adopted).**
   MAIN ORDER 2026-10-27-2136 FLEET-KIT-v25 (HOP 1): verify_main True (inbox == MAIN committed outbox copy,
   sha256 ac203570c0b7...); bundle verified at KIT-COMMIT 7db5d9d (lw_inbox_responder.bundle_verified True).
   The working tree already held the v25 kit bytes from an earlier half-done rollout (claims: one DEAD owner,
   released; no live one); nothing re-copied. READ BACK: 23/23 kit files + MANIFEST.json (fa04c87c...) match
   section 1; conformance() == []; KIT_VERSION 25; FLEET-COMMON unchanged. Tree side (section 5): the loop
   driver follows fleet_lanes.load_config() - ops/loop/config.json lane_cap 3 -> null (live lane_cap_max),
   max_concurrent_lanes 3 -> removed from config.json / config.gate.json / config.p5.json and the
   loop_controller literal default `CFG.get("max_concurrent_lanes", 3)` -> executor_slot_count() (live
   governor_width, a tree number only asks for fewer and clamps); run_lane gets cap=None; the executor slot's
   repo key str(MAIN_ROOT) -> LANE_CODE so should_yield("LW") counts it; cycle_boundary_yield() calls
   fleet_lanes.should_yield("LW") at each cycle top and on True returns (ends the lane, never kills); an
   admission refusal exits like lanes_full (LaneRefused, retry next tick). Guard test
   tests/test_loop_lane_cap_v25.py (width 5 / cap 5 config reads 5, missing reads 3, no kill on yield).
   Section 4: tests/test_loop_lanes.py (lane_cap 4 clamps instead of raising; slot repo key); the
   pre-v25 config-agreement arms in tests/test_loop_concurrency.py now assert no LW config declares a
   ceiling, no literal default survives, and RC never declares more than the machine width.
   KIT_VERSION pins 24 -> 25 (tests/test_fleet_kit_conformance.py, tests/test_headless_env.py,
   tests/test_promise_probe_fleet_kit.py, tools/lw_promise_probes.py). Graceful restart: no LW lane loop
   running (nothing to restart; the next start loads v25). Gated suite (fleet_suite_gate, tools/lw_suite.py
   -q): 4210 passed 19 skipped + serial 183 passed 1 skipped, exit 0; drift_guard 0 breaches; ruff clean.

352. DONE **2026-10-26 (responder re-verify of MAIN ORDER 2026-10-26-0315 FLEET-KIT-v24; no residual work).**
   Inbox copy sha256 de515317931aad51e6d6f1d226c39a3ee14219601a32635f3c03a75d556e81bb (re-hashed; == MAIN outbox
   copy). Wiring already landed by b8a2057 / LEDGER 351 (KIT_VERSION pins 24, MANIFEST a41ff08e... == section 1).
   Gated suite re-run: exit 0, 4387 passed 19 skipped. CI on b8a2057 (ci + codeql): success. One HOP 2 answer sent.

351. DONE **2026-10-26 (Maint-KitRollout: fleet kit v24 adopted; supersedes v23).**
   MAIN ORDER 2026-10-26-0315 FLEET-KIT-v24 (HOP 1): verify_main True (inbox == MAIN committed outbox copy,
   sha256 de515317931a...); bundle verified at KIT-COMMIT 3ce416e (lw_inbox_responder.bundle_verified True).
   The working tree already held the v24 bytes from an earlier half-done rollout (all 24 files == bundle
   sha256, CLAUDE.md diff = item 19 only; claims: one DEAD owner, no live one; nothing re-copied). READ BACK:
   23/23 kit files + MANIFEST.json (a41ff08e...) match section 1; conformance() == []; KIT_VERSION 24;
   FLEET-COMMON block byte-exact (item 19 new). Section 4: no chart_order / item-18 / shell_targets / _lanes
   order asserts in tests/. Adoption fixes: KIT_VERSION pins 23 -> 24 (tests/test_fleet_kit_conformance.py,
   tests/test_headless_env.py, tests/test_promise_probe_fleet_kit.py, tools/lw_promise_probes.py);
   tests/test_no_absolute_machine_paths.py drops the ops/fleet_kit/ allowlist row (v24 KIT-SIDECAR-PATH: the
   kit has 0 drive-path lines, so the row was dead). reap dry-run: 0 removable, 0 kept, 0 listed. Gated suite
   (fleet_suite_gate, tools/lw_suite.py -q): 4204 passed 19 skipped + serial 183 passed 1 skipped; drift_guard
   0 breaches; ruff clean.

350. DONE **2026-10-26 (responder: MAIN ORDER 2026-10-26-0300 U5 - timing tests to fleet_test_guard.budget()).**
   MAIN provenance: verify_main True, inbox == MAIN outbox sha256 35783c7a4f0704781508ce84e5b140d22472ce184ac3b9bd09b93e8880217193
   (1061 bytes). tests/test_lw_facts_stdin_is_bounded.py (2 arms, elapsed < 3.0) and
   tests/test_slot_hold_is_bounded.py (1 arm, monotonic() - t0 < 30) now assert against
   fleet_test_guard.budget(3.0) / budget(30) (kit v16+ load-scaled); each file imports fleet_test_guard.
   Read back: grep of tests/ for an assert on elapsed/monotonic/perf_counter/time.time with a raw `<`
   bound outside budget() = 0 hits. Touched files: 44 passed, exit 0. Whole suite via fleet_suite_gate
   (timeout 1200 s): exit 0, 4387 passed, 19 skipped, 246 s; untracked/modified file count 2 -> 2.
   ruff clean. Reply: ANSWER note to MAIN (HOP 2, TERMINAL). FUTURE: a new wall-clock upper bound in
   tests/ goes through budget() from the start.

349. DONE **2026-10-25 (session 86 / responder 198 /done: 2045 suite-speed wrap).**
   491bb85 (LEDGER 348) pushed by the responder; CI read back: ci 40266567636 success, codeql 40266567605
   success. ANSWER 2026-10-25-2257-from-LW-ANSWER-to-MAIN-2045-suite-speed-done-491bb85-TERMINAL delivered,
   reached 1/1; outbound 3/12 today. Still unread in the inbox at wrap (not marked seen): MAIN 1926 FLEET-KIT
   v23 ORDER (work done, LEDGER 346), MAIN 1935 FIX gh-review pillow-13 (work done 8dfef45, LEDGER 347), two SS
   ANSWER notes (no reply) - carried as INBOX-MARK. CI-82 closed (prior push green; 491bb85 green).
   Worktree reap: 0 removed, 0 kept, 0 listed.

348. DONE **2026-10-25 (responder: MAIN ORDER 2026-10-25-2045 suite speed - veil fixture module-scoped, test httpd poll 0.05 s, -n 8, BLAS thread caps, torch test serial).**
   MAIN provenance: verify_main True, inbox == MAIN outbox sha256 d1e2037b1fa9dd581d47fbf6cf7967d82571ef1af349900b3e8c2c6c98f92b05
   (2155 bytes). (1) tests/test_lw_clean_overlay_veil.py: estimate_veil built once per module, deep copy per
   test (file 24.70 s -> 6.93 s). (2) every test serve_forever thread (7 files) gets poll_interval 0.05; the
   httpd + served_version + rundash_jobs trio 11.97 s -> 3.04 s; tools/lw_httpd.py production default left as is.
   (3) tools/lw_suite.py parallel pass -n auto -> -n 8 (RED first in test_pytest_parallel_config); CI keeps
   -n auto (small runners). Peak commit located with a temp psutil per-test sampler in a gated -n 8 run:
   test_lw_usm_halo_probe::test_worker_spandrel_branch_produces_both_variants (real torch + IJN child) 10605 MB
   tree peak on one worker, plus ~0.6-1.1 GB per worker of OpenBLAS per-thread buffers (import numpy 500 MB,
   scipy.ndimage 1010 MB private vs 18 / 46 MB at one thread). Fixes: that test marked serial; tests/conftest.py
   setdefaults OPENBLAS/OMP/MKL_NUM_THREADS=1 before any array import (tests/test_suite_thread_caps.py, RED
   first). Gate durations, same command: `python tools/lw_suite.py -q` hold 84.5 / 96.5 s, peak 15563 / 15629 MB
   -> 93.6 s, 9606 MB (exit 0; 4204 passed 19 skipped + serial 183 passed 1 skipped). `python -m pytest tests
   -q` hold 320.8 s, peak 11165 MB -> 289.6 s, 9718 MB (exit 0, 4387 passed, 19 skipped).

347. DONE **2026-10-25 (responder: MAIN FIX 2026-10-25-1935 gh-review - Pillow 13.0.0, Dependabot PRs #5 #6 re-applied as operator commits).**
   Inbox copy re-hashed: sha256 2b7ff2c8966a092dd50e341d56398e59a8c62df709d0633d33fe2d264d2b42d0, 2125 bytes;
   verify_main True (MAIN committed outbox copy). READ BEFORE: 82 open Dependabot alerts (gh api), PRs #5 #6 open.
   No private Pillow internals used (grep of `_save_netpbm`, `Image._`, `ImageFile._`, `GifImagePlugin`: 0 hits).
   PR #6 (head 539ab9b) applied with `git cherry-pick --no-commit`: setup-python v7.0.0 -> v7.1.0 (3 sites),
   codeql-action init/analyze v4.39.0 -> v4.39.1. PR #5 (head 9ef1ece) NOT taken byte-for-byte: its
   requirements files drop colorama (win32 marker) and list every pillow hash twice; both files regenerated
   locally with `uv pip compile ... --generate-hashes --upgrade-package pillow [--upgrade-package ruff]`
   instead. Pins: pillow 12.3.0 -> 13.0.0 (requirements.txt, requirements-cv.txt), ruff 0.17.1 -> 0.17.2
   (requirements.txt); colorama kept; 0 duplicate hashes. Gated suite (fleet_suite_gate, python -m pytest
   tests -q, local Pillow 13.0.0): exit 0, 4381 passed, 19 skipped. CV lane in a fresh venv installed
   `--require-hashes` from requirements-cv.txt (cv2 5.0.0, numpy 2.5.4, scipy 1.18.1, skimage 0.26.0,
   Pillow 13.0.0): exit 0, 18 passed. CLAUDE.md Session gains the MAIN-ordered rule: read the previous
   push's CI verdict before the next push.

