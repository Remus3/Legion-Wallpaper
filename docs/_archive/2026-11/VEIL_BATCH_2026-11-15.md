# DA logo veil batch over 3.Cleaning Scratch - result (2026-11-15)

**Verdict.** The pair-matte overlay lane (a2eb6c3) ran on the whole DA logo-veil
family: 63 slugs cleaned, the G2 outside-mask identity held on all 63 (0 px
changed outside pair coverage + LaMa mask), 37 passed the batch gate, 33 were
submitted to `_cleanneedauth` for operator review, 26 went to the manual IOPaint
queue, and 4 gate-pass slugs were refused by save-working under ADR-009 (prior
cleaning engine). Nothing approved. The dominant failure is AMPLITUDE, not
registration: with the fixed pair alpha 0.1511 the residual tracks each frame's own
measured veil step (residual = input step - 0.151: median deviation 0.002, max
0.013 over the 63 slugs),
so frames whose veil reads 0.17-0.22 keep a faint logo and frames reading
0.10-0.13 get a faint dark imprint.

## Method

- Input per slug: `lw_clean_pass.select_working_image` (highest non-rejected
  `_cleanworking_NN`, else `_cleaninitial`); all 85 frames are 2560x1440.
- Family (step 2): `lw_clean_overlay.pair_veil_alpha_hat` at the wide-template
  registration >= `PAIR_PRESENT_MIN` 0.05 - the lane's own presence gate. The 85
  frames split cleanly: 66 read 0.088-0.223, the other 19 read -0.050..+0.034
  (no frame between). The detector score (`overlay_score`, flag 0.15) misses 19
  family members (0.09-0.15) and flags no frame outside it.
- Lane (step 3): `lw_clean_iopaint.clean_slug(slug, overlay=True)`, dry-run on all
  63 first (all ok, mask coverage 4.4-6.6 pct of the ROI, ceiling 25), then
  executed. The pair matte was used on all 63 (ring 9195 px; 10314 at scale 1.12).
- Registration residual: `pair_veil_alpha_hat` on the algebraic pre-pass output at
  the registered position (the boundary step the inverted matte leaves). A +-4 px
  search for the step peak was tried and DROPPED: the step estimator is flat over
  +-3 px (0.1464 vs 0.1477), so it cannot localise a few-px error.
  Registration FAIL = pair not used, or the template moved the matte off frame
  geometry (|shift| > 3 px or scale != 1) AND the pre-pass residual is >= 0.01.
- Residual alpha after: `pair_veil_alpha_hat` on the final candidate (strips 2-6 px
  in / 8-14 px out, outside the LaMa ring, so it equals the pre-pass value).
- G2 (hard, `lw_clean_pass.verify_verdict`): candidate vs the ORIGINAL input,
  mask = pair coverage > 0 OR the LaMa mask; outside_max_abs must be 0;
  change_ssim <= 0.90 inside; seam_step flag at 6.0. residue_mf not run.
- Batch gate = G2 pass AND registration ok AND |residual alpha| <= 0.02. 0.02 is
  the p75 of |alpha_hat| on the 19 veil-free frames (median 0.012, max 0.050), i.e.
  the estimator's own noise on clean art. The earlier 0.01 bar was graded against
  a clean reference; at 0.01 only 24 slugs pass, at 0.035 51.
- Gate pass -> `save-working --tool iopaint` (params carry the batch metrics) +
  `submit --actor tool:lw_clean_iopaint`, dry-run first. Gate fail ->
  `annotate --tool qa` with route manual_iopaint + reason (cleaning-pass skill
  section 4); candidates stay in `ops/runtime/clean/<slug>/`, never forced.

## Counts

- family 66 = 63 run + 3 purchased (excluded)
- cleaned 63; G2 pass 63; outside-mask px changed: 0 on every slug
- batch gate pass 37; submitted (NEEDAUTH) 33; ladder-blocked 4
- manual IOPaint queue 26 (residual only 22, registration 4)
- registration failures 4: 110-cleanup, 122, bamboo-gal-seraphine-by-mrphantomknight-dm1rp4q-fullview, fantasy-design-by-aivio-dkdq5p7-pre
- worst residual: 225f +0.0854; fantasy-design-by-aivio-dkdq5p7-pre -0.0746; 285f +0.0592
- ladder-blocked: aidraw-2662100118-by-watercolornessie-dma7o8j-fullview, prestige-coven-xayah-by-pebano1-dmc27t0-pre, syndra-coven-league-of-legends-by-kintanki1-dm6e10u-fullview, viego-the-king-by-slimshadywallpaper-dhawigh-pre

Purchased (excluded; veil step on the cleaninitial):
- dark-cosmic-ahri-by-pebano1-dlnxav6-pre: 0.1183
- mecha-ahri-by-smalltavernx-dia857d-pre: 0.1413
- yuumi-by-narumicsibe-dmax7wo-fullview: 0.1099

Veil-free frames (not in the family), alpha_hat:
- 281-cleanup: -0.0499
- dfzypoo-482973ff-dfb0-44e4-a90c-386714d27faf: -0.0177
- kayle-new-splash-by-su-ke-d85w02l-fullview: -0.0119
- 106-cleanup: -0.0097
- dfzypp1-251c5c37-e25f-496e-a9a6-4900304e6fa5: -0.0053
- 219-cleanup: -0.0020
- karthasbasefinal-by-alexflores-d7q5tbt-fullview: -0.0019
- dfzypou-30bef263-c754-4a26-9797-484757b1c4cf: -0.0018
- spirit-blossom-ahri-mono-01-by-hriful-dk79ceq-pre: +0.0034
- dragon-slayer-pantheon-by-alexflores-d7fr57n-fullview: +0.0047
- dgk8f8n-398197d0-65d6-4299-8f0b-afdd9021c395: +0.0071
- image3: +0.0099
- dfz5w2g-8ba7345b-5776-4d83-b939-4ca7d045f545: +0.0152
- brair-league-of-legends-by-kairahi-dles4n2-pre: +0.0165
- fury-tempest-sona-by-ryoairtist-dm7ziam-pre: +0.0180
- dfzlox4-7e2bdc64-36ce-41fa-80b0-c83f97fdf5f5: +0.0206
- akali-godly-deer-by-ryoairtist-dm2su3h-fullview: +0.0226
- caitlyn-love-confession-lol-skin-splash-art-4k-wallpaper-uhdpape: +0.0293
- 258-cleanup: +0.0338

## Per-slug table

veil = input step alpha_hat; shift = template (dy,dx)@scale; reg = registration
verdict (pre-pass residual); resid = residual alpha after; outside = outside-mask
max abs diff; G2 = verdict; chg = change_ssim; seam = seam_step; route.

| slug | veil | shift | reg | resid | outside | G2 | chg | seam | gate | route |
|---|---|---|---|---|---|---|---|---|---|---|
| 105-cleanup | 0.1515 | 0,0@1 | ok (+0.0007) | +0.0007 | 0 | pass | 0.840 | 0.30 | pass | submitted |
| 107-cleanup | 0.1957 | 1,0@1 | ok (+0.0537) | +0.0537 | 0 | pass | 0.858 | 0.25 | fail | manual_iopaint |
| 109-cleanup | 0.1464 | 0,0@1 | ok (-0.0036) | -0.0036 | 0 | pass | 0.676 | 0.47 | pass | submitted |
| 110-cleanup | 0.1808 | 24,-1@1.12 | FAIL (+0.0353) | +0.0353 | 0 | pass | 0.888 | 1.42 | fail | manual_iopaint |
| 122 | 0.1740 | 24,-1@1.12 | FAIL (+0.0272) | +0.0272 | 0 | pass | 0.851 | 1.46 | fail | manual_iopaint |
| 123f | 0.1482 | 0,0@1 | ok (-0.0032) | -0.0032 | 0 | pass | 0.787 | 0.13 | pass | submitted |
| 124f | 0.1429 | 0,0@1 | ok (-0.0089) | -0.0089 | 0 | pass | 0.763 | 0.22 | pass | submitted |
| 221-cleanup | 0.1742 | 0,-1@1 | ok (+0.0315) | +0.0315 | 0 | pass | 0.750 | 0.67 | fail | manual_iopaint |
| 224f | 0.1238 | 0,-2@1 | ok (-0.0312) | -0.0312 | 0 | pass | 0.866 | 0.23 | fail | manual_iopaint |
| 225f | 0.2233 | 0,-1@1 | ok (+0.0854) | +0.0854 | 0 | pass | 0.874 | 1.09 | fail | manual_iopaint |
| 239f | 0.1036 | 0,-1@1 | ok (-0.0553) | -0.0553 | 0 | pass | 0.798 | 0.04 | fail | manual_iopaint |
| 244f | 0.1263 | 0,-1@1 | ok (-0.0290) | -0.0290 | 0 | pass | 0.848 | 1.92 | fail | manual_iopaint |
| 245f | 0.1640 | 0,-1@1 | ok (+0.0154) | +0.0154 | 0 | pass | 0.796 | 0.47 | pass | submitted |
| 259f | 0.1244 | -1,-1@1 | ok (-0.0315) | -0.0315 | 0 | pass | 0.747 | 0.29 | fail | manual_iopaint |
| 261f | 0.1599 | -1,-1@1 | ok (+0.0108) | +0.0108 | 0 | pass | 0.860 | 1.32 | pass | submitted |
| 262f | 0.1712 | -1,-1@1 | ok (+0.0241) | +0.0241 | 0 | pass | 0.855 | 0.21 | fail | manual_iopaint |
| 266f | 0.1442 | -1,-1@1 | ok (-0.0081) | -0.0081 | 0 | pass | 0.781 | 0.41 | pass | submitted |
| 268f | 0.1959 | 1,0@1 | ok (+0.0524) | +0.0524 | 0 | pass | 0.857 | 1.25 | fail | manual_iopaint |
| 269f | 0.1626 | 0,1@1 | ok (+0.0144) | +0.0144 | 0 | pass | 0.562 | 0.10 | pass | submitted |
| 270f | 0.1779 | 0,0@1 | ok (+0.0317) | +0.0317 | 0 | pass | 0.807 | 0.26 | fail | manual_iopaint |
| 272-cleanup | 0.1270 | 0,0@1 | ok (-0.0283) | -0.0283 | 0 | pass | 0.696 | 1.00 | fail | manual_iopaint |
| 273f | 0.1707 | 0,-1@1 | ok (+0.0251) | +0.0251 | 0 | pass | 0.729 | 0.29 | fail | manual_iopaint |
| 276f | 0.1406 | 0,0@1 | ok (-0.0120) | -0.0120 | 0 | pass | 0.564 | 0.11 | pass | submitted |
| 277f | 0.1801 | 0,1@1 | ok (+0.0342) | +0.0342 | 0 | pass | 0.751 | 0.18 | fail | manual_iopaint |
| 278f | 0.1373 | -1,-1@1 | ok (-0.0160) | -0.0160 | 0 | pass | 0.802 | 0.00 | pass | submitted |
| 280f | 0.1479 | 0,0@1 | ok (-0.0023) | -0.0023 | 0 | pass | 0.565 | 1.00 | pass | submitted |
| 284f | 0.1517 | 0,-1@1 | ok (+0.0007) | +0.0007 | 0 | pass | 0.863 | 0.57 | pass | submitted |
| 285f | 0.2016 | 0,-1@1 | ok (+0.0592) | +0.0592 | 0 | pass | 0.897 | 2.51 | fail | manual_iopaint |
| 286f | 0.1491 | 0,0@1 | ok (-0.0018) | -0.0018 | 0 | pass | 0.757 | 0.51 | pass | submitted |
| 287f | 0.1690 | -1,-1@1 | ok (+0.0214) | +0.0214 | 0 | pass | 0.789 | 0.78 | fail | manual_iopaint |
| 32-cleanup | 0.1513 | -1,0@1 | ok (+0.0007) | +0.0007 | 0 | pass | 0.773 | 0.17 | pass | submitted |
| 9-cleanup | 0.1486 | -1,0@1 | ok (-0.0027) | -0.0027 | 0 | pass | 0.804 | 0.71 | pass | submitted |
| aatrox-the-darkin-blade-in-flames-by-vexxsoul-dm6j4xi-pre | 0.1717 | -1,-1@1 | ok (+0.0272) | +0.0272 | 0 | pass | 0.737 | 1.05 | fail | manual_iopaint |
| ahri-by-stellastria-dmbclo0-pre | 0.1578 | 0,0@1 | ok (+0.0083) | +0.0083 | 0 | pass | 0.760 | 0.15 | pass | submitted |
| ahri-league-of-legends-by-khanzaaiart-dmbzcmq-pre | 0.1043 | -1,-1@1 | ok (-0.0547) | -0.0547 | 0 | pass | 0.819 | 1.10 | fail | manual_iopaint |
| aidraw-2662100118-by-watercolornessie-dma7o8j-fullview | 0.1464 | -1,-1@1 | ok (-0.0053) | -0.0053 | 0 | pass | 0.678 | 0.53 | pass | ladder_blocked |
| anime-poster-of-soraka-from-league-of-legends-by-givemenine-dg8j | 0.1722 | -1,1@1 | ok (+0.0249) | +0.0249 | 0 | pass | 0.859 | 0.56 | fail | manual_iopaint |
| ashe-by-stellastria-dlzcque-fullview | 0.1895 | 0,0@1 | ok (+0.0463) | +0.0463 | 0 | pass | 0.759 | 0.27 | fail | manual_iopaint |
| bamboo-gal-seraphine-by-mrphantomknight-dm1rp4q-fullview | 0.1047 | 1,30@1 | FAIL (-0.0471) | -0.0471 | 0 | pass | 0.872 | 1.06 | fail | manual_iopaint |
| bayonetta-by-stellastria-dm7iirw-pre | 0.1572 | 0,0@1 | ok (+0.0077) | +0.0077 | 0 | pass | 0.726 | 0.47 | pass | submitted |
| bayonetta-by-stellastria-dm7iiug-pre | 0.1607 | 0,0@1 | ok (+0.0110) | +0.0110 | 0 | pass | 0.796 | 0.23 | pass | submitted |
| blood-moon-priestess-mel-by-aiaida-dmhckey-pre | 0.1553 | 10,-9@1 | ok (+0.0061) | +0.0061 | 0 | pass | 0.652 | 0.73 | pass | submitted |
| caitlyn-by-pebano1-dm9fw9z-fullview | 0.1632 | 0,0@1 | ok (+0.0148) | +0.0148 | 0 | pass | 0.626 | 0.79 | pass | submitted |
| dawnbringer-soraka-celestial-radiance-by-cherrynest-dml4dmh-full | 0.1546 | -1,0@1 | ok (+0.0042) | +0.0042 | 0 | pass | 0.864 | 2.00 | pass | submitted |
| evelynn-by-pebano1-dmc9764-pre | 0.1508 | 0,0@1 | ok (-0.0001) | -0.0001 | 0 | pass | 0.700 | 0.88 | pass | submitted |
| fantasy-design-by-aivio-dkdq5p7-pre | 0.0876 | 43,-10@1 | FAIL (-0.0746) | -0.0746 | 0 | pass | 0.826 | 0.27 | fail | manual_iopaint |
| fierce-enforcer-of-piltover-by-vexxsoul-dm5crlf-pre | 0.1366 | -1,-1@1 | ok (-0.0155) | -0.0155 | 0 | pass | 0.682 | 0.49 | pass | submitted |
| inkshadow-kai-sa-by-pebano1-dm7m9lz-fullview | 0.1384 | 0,0@1 | ok (-0.0143) | -0.0143 | 0 | pass | 0.584 | 0.68 | pass | submitted |
| meramora-artwork-by-meramora-dm9c8hi-pre | 0.1472 | 0,0@1 | ok (-0.0043) | -0.0043 | 0 | pass | 0.804 | 0.20 | pass | submitted |
| miss-fortune-by-stellastria-dmcdsno-fullview | 0.1268 | 0,0@1 | ok (-0.0288) | -0.0288 | 0 | pass | 0.711 | 0.12 | fail | manual_iopaint |
| prestige-coven-xayah-by-pebano1-dmc27t0-pre | 0.1411 | 0,0@1 | ok (-0.0112) | -0.0112 | 0 | pass | 0.581 | 0.98 | pass | ladder_blocked |
| queen-of-the-saltwind-by-rasrpunk-dmi98yq-fullview | 0.1463 | -1,0@1 | ok (-0.0055) | -0.0055 | 0 | pass | 0.600 | 0.48 | pass | submitted |
| riven-broken-blade-unbroken-will-by-vexxsoul-dm9po91-fullview | 0.1504 | -1,-1@1 | ok (+0.0020) | +0.0020 | 0 | pass | 0.605 | 0.65 | pass | submitted |
| seraphine-by-pebano1-dmaj431-pre | 0.1563 | 0,0@1 | ok (+0.0059) | +0.0059 | 0 | pass | 0.832 | 1.45 | pass | submitted |
| seraphine-stage-of-brilliance-by-vexxsoul-dm5uzf1-pre | 0.1643 | -1,-1@1 | ok (+0.0134) | +0.0134 | 0 | pass | 0.741 | 2.25 | pass | submitted |
| syndra-coven-league-of-legends-by-kintanki1-dm6e10u-fullview | 0.1514 | -5,3@1 | ok (+0.0011) | +0.0011 | 0 | pass | 0.713 | 0.89 | pass | ladder_blocked |
| syndra-league-of-legends-by-smalltavernx-dlsfckr-pre | 0.1532 | 0,0@1 | ok (+0.0041) | +0.0041 | 0 | pass | 0.818 | 0.11 | pass | submitted |
| syndra-league-of-legends-by-smalltavernx-dlsfcue-pre | 0.1656 | 0,0@1 | ok (+0.0185) | +0.0185 | 0 | pass | 0.774 | 0.42 | pass | submitted |
| the-ruined-king-viego-by-vexxsoul-dm6j4mu-pre | 0.1853 | -1,-1@1 | ok (+0.0421) | +0.0421 | 0 | pass | 0.742 | 0.15 | fail | manual_iopaint |
| viego-the-king-by-slimshadywallpaper-dhawigh-pre | 0.1629 | 0,-1@1 | ok (+0.0140) | +0.0140 | 0 | pass | 0.741 | 1.17 | pass | ladder_blocked |
| viego-the-ruined-king-by-slimshadywallpaper-dgemoim-pre | 0.1484 | -1,1@1 | ok (-0.0029) | -0.0029 | 0 | pass | 0.686 | 0.29 | pass | submitted |
| xayah-by-pebano1-dm44iab-fullview | 0.1079 | 0,0@1 | ok (-0.0495) | -0.0495 | 0 | pass | 0.627 | 0.16 | fail | manual_iopaint |
| yunara-by-pebano1-dm7zwfb-fullview | 0.1568 | 0,0@1 | ok (+0.0067) | +0.0067 | 0 | pass | 0.757 | 0.78 | pass | submitted |

## Review aid and outputs (gitignored)

- Crops: `images/_veil_pairs/2026-11-15/batch/<slug>_logo_before_after_2x.png`
  (input | candidate, logo window + credit line, 2x nearest).
- Contact sheets: `images/_veil_pairs/2026-11-15/batch/contact_sheet_01.png` to
  `contact_sheet_06.png` (12 per sheet, labelled gate / residual / shift).
- Data: `enum.json`, `family.json`, `dry.json`, `exec.json`, `submit.json` in the
  same folder. Candidates + masks: `ops/runtime/clean/<slug>/`.

## Observations and open items

- Eyeball at 2x (225f +0.085, 239f -0.055, 105-cleanup +0.001): the residual sign
  matches what is seen - 225f keeps a faint light logo, 239f shows dark edge
  traces. Even 105-cleanup keeps faint 1 px outline traces (the residue the
  operator passed on held-out C); zero residue is not reached on any slug.
- Per-frame amplitude: the firstdones went through upscale + USM, which changes the
  veil's apparent step frame by frame; a per-frame alpha (fit from this frame's
  step, bounded) instead of the fixed 0.1511 is the next slice. Not done here;
  production code is unchanged by this batch.
- Credit line: LaMa removes most of the artist credit line, but some frames
  (225f) keep a ghost of the text.
- Ladder-blocked (gate pass, ADR-009 exit 3): candidates are ready; the operator
  can register them with `save-working --allow-ladder` if that swap is wanted.
- 110-cleanup and 122 register at scale 1.12 (+24 px), bamboo-gal at dx +30,
  fantasy-design at (+43,-10): the template drags the matte off frame geometry;
  bamboo-gal reads 0.158 at frame centre vs 0.105 at the template position.

## Operator

Nothing approved. Review the needauth queue (`python tools/lw_qa_slider.py --list`)
against the contact sheets; approve / reject via lw_pipeline.
