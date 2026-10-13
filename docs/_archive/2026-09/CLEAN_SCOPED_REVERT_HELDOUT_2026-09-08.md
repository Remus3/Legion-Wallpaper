# scoped_revert - held-out measurement

**Date:** 2026-09-08
**Question:** LEDGER 2354 cites "`held` is 0 in all 28" as evidence scoped_revert
worked. `scoped_revert` (`tools/lw_clean_spot.py:232-240`) grows its band
4/8/16/32px and returns on the first candidate the acceptance verdict passes, so
the verdict IS the search's stopping rule. A search that stops when the verdict
passes will report the verdict passing. Does the change survive a measure the
search did not optimise?

**Answer: yes on the axis it was judged on, and that axis is one-sided.** The
conclusion stands, the cited statistic does not carry it, and the axis where the
change can actually lose has no measure at all.

---

## 1. The cited statistic is contaminated, but it was not load-bearing

`held` is the count of blobs the verdict refused - it is the verdict's own
output, downstream of a search whose stopping rule is that verdict. It cannot be
evidence about the search. `committed` and `partial` are the same quantity in
different clothes.

But the decision did not actually rest on it. `run_spot_heal`'s docstring
(`lw_clean_spot.py:326-333`) cites the mark HANDED BACK and the count of slugs a
reader still finds a line in. The second of those, recorded as `still_reads` in
every lane plan, is a genuine outcome: it is produced by reading the output, not
by the verdict, and nothing in the search optimises it.

## 2. Held-out result, and it replicates

Paired over the 39 slugs common to both lanes, recorded on disk, no re-run:

| comparison | still_reads (INDEPENDENT) | improved | regressed | held (verdict output) |
| --- | --- | --- | --- | --- |
| `run` -> `run_scoped` | 13 -> 2 | 12 | 1 | 21 -> 1 |
| `run_stubs` -> `run_stubs_scoped` | 13 -> 2 | 12 | 1 | 43 -> 2 |

The independent measure moves the same way, by the same margin, under two
different stub conditions. That is a replication, not a single reading, and it
is not downstream of the stopping rule. **scoped_revert is supported.**

The one regression is named rather than buried:
`dark-cosmic-ahri-by-pebano1-dlnxav6-pre` - the credit line is readable in the
scoped output where the whole revert had cleared it. 12 improved against 1
regressed is a real result, not a clean sweep, and the sweep is what the
contaminated statistic implied.

## 3. The axis the change cannot lose on

Both cited measures - handed back, still_reads - count RESIDUE. On residue,
scoped_revert cannot lose by construction, and the code says so plainly
(`lw_clean_spot.py:330-332`): the band is a subset of the blob and the ordinary
verdict must still pass on the scoped candidate. A measurement on an axis where
the treatment cannot lose is not worthless, but it cannot be the whole case.

The axis where it CAN lose is art damage. The operator's own note in LEDGER 2354
is the only evidence on it: "on akali it costs what the rollback bought: a
blocky smear where the bodysuit strap was, the comparison layer having no chord
there". That is anecdotal, and nothing in the pipeline measures it.

## 4. How big is the unmeasured surface

Every step where the whole-revert lane reverted and the scoped lane did not, the
scoped lane keeps fill that the whole revert gave back. That kept fill is
exactly where a smear can live.

| comparison | steps flipped revert -> fill | fill kept | of blob area |
| --- | --- | --- | --- |
| `run` -> `run_scoped` | 20 | 256,726 px | 95.0 percent |
| `run_stubs` -> `run_stubs_scoped` | 41 | 326,277 px | 94.4 percent |

The restored corridor is tiny beside the blob it sits in:

| slug | blob px | corridor restored | fill kept |
| --- | --- | --- | --- |
| seraphine-by-pebano1-dmaj431-pre | 42,941 | 372 | 42,569 |
| aatrox-...-vexxsoul-dm6j4xi-pre | 35,083 | 913 | 34,170 |
| evelynn-by-pebano1-dmc9764-pre | 28,453 | 855 | 27,598 |
| 280f | 23,763 | 1,990 | 21,773 |
| queen-of-the-saltwind-...-dmi98yq | 20,294 | 682 | 19,612 |

So scoped_revert keeps about **95 percent** of the pixels the whole revert
handed back, and the evidence base for those pixels being GOOD is the
acceptance verdict - the same verdict that was the search's stopping rule. That
is the contamination's real consequence: not that the conclusion is wrong, but
that 95 percent of the changed area is vouched for only by the thing that
stopped the search.

## 5. Limits of this measurement

- `handed_back_px` was added after most lanes were recorded. Only
  `run_shipdefault` carries it (20,673 px of 1,079,570 mask px = 1.91 percent),
  so it cannot be compared across lanes here. The 28.13 -> 1.80 percent figure
  in the docstring is not reproducible from what is on disk.
- `still_reads` is a reader verdict on the whole slug, so it is coarse: it
  cannot distinguish a slug that got slightly better from one that got much
  better, and it says nothing about art quality.
- Lanes differ in more than one variable (`run_ringfix` reaches still_reads 0
  with no scoping at all), so only the two paired comparisons above isolate
  scoped_revert. Cross-lane comparison is confounded and is not made here.
- No art-damage measurement was attempted. Constructing one is the open work,
  not a gap in this pass.

## 6. What would close it

A no-reference artifact measure over the kept-fill region, compared against the
surrounding art - a smear is a region whose local gradient energy collapses
relative to its neighbourhood. That is measurable with what the repo already
has, and it is the only way the 95 percent stops being vouched for by the
stopping rule. Until then scoped_revert stays the default on the strength of a
replicated independent residue result, with a named cost that has never been
quantified.
