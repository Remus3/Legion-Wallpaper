# PARKED next-session prompt - the pipeline queues

Parked 2026-09-10 by operator instruction ("keep the current next-session-prompt
saved for later") when the responder lane was re-armed and took the next-session
slot. Nothing here is done, superseded or wrong - it is the pipeline queue work,
displaced by a higher-priority lane and kept verbatim so it is not re-derived.

Resume it by copying the block below back over `LW-NEXT-SESSION.txt` once the
lane work lands, or by lifting individual items into a fresh prompt. Re-probe
the counts before acting on them: the stage counts and the 108/7/3 queue splits
were true on 2026-09-08 and `0.Originals` has already moved from 5 loose files
to 6 since.

---

```
NEXT SESSION
------------
Task: OPERATOR CHOICE. Three queues from first-pass-batch-2026-09-08 are still
  operator decisions and unchanged: (a) 108 slugs await approve/reject in
  _firstneedauth, (b) 7 slugs HELD aspect_crop_heavy need a per-image framing
  call (3 pintrest lose 68-71 percent of area; --crop-overrides takes
  {slug: {"top": N}}), (c) 3 slugs failed G1 lap_ratio 0.91-0.93 on soft
  SOURCES. Ask which, then work only that one.
  Two NEW open items from 2026-09-08, both also operator calls:
  (d) art-damage measure for scoped_revert - it is supported on residue, an
      axis it cannot lose on by construction, while 95.0 percent of the changed
      area is vouched for only by the search's own stopping rule. Needs a
      no-reference artifact measure over the kept-fill region.
  (e) whether `dists` should gate at all - it is computed on every audit and
      consumed by nothing.
ON STANDBY, do not touch: the inbox responder and all outbound filings. The
  operator placed CS/LW/LL on standby 2026-09-08 while RSC and RC continue
  headless. RSC's 22:04 note records LW's silence as STANDBY, not dissent, and
  asks nothing of LW. Drafted positions on RSC's Q1-Q5 are in WAKEUP_NOTES,
  held and NOT sent. Do not build or file until the operator lifts it.
Context: ROADMAP.md "Open items - High priority"; WAKEUP_NOTES "NEXT SESSION";
  docs/LEDGER.md 177-180; docs/CLEAN_SCOPED_REVERT_HELDOUT_2026-09-08.md;
  ops/runtime/{tier2_queue,intake_refused,crop_overrides}_2026-09-07.*.
  Inbox first: read, THEN ack with `python tools/lw_facts.py --mark-inbox-seen`.
Acceptance: whatever the chosen item states. Standing bar: `python -m pytest
  tests/ -q` green (baseline 2813 passed / 18 skipped, ~140s on 2026-09-08),
  ruff clean, `python tools/drift_guard.py` exit 0, `python tools/done_gate.py
  bind` exit 0, then push the bound sha.
Do NOT redo: LEDGER 177-180 shipped and pushed (b4c9d1a, 18cf063, 5b0cef1,
  ba3263f). PVR is ENABLED - do not re-run the PUT. The .gitignore `_archive/`
  anchor is fixed and its drift_guard exemption RETIRED - do not re-add it. The
  msssim floor is deliberately UNCHANGED; never re-fit a threshold on the
  samples it gates. `dists` being ungated is PINNED as current behaviour by
  tests/test_g1_msssim_arm_binds.py. Pre-existing, NOT yours: the suite runs one
  more item than it collects.
Start with: /clear, then bootstrap from CLAUDE.md + MEMORY.md + WAKEUP_NOTES +
  git log.
```
