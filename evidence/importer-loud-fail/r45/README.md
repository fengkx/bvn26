# r45 — adjacent source bytes and independent alpha retain global rejection

`candidate_admitted=false`, `gpu_advance_allowed=false`, `production_admitted=false`.
Analysis exits **1**. No production/GPU implementation, row routing, old reference,
epsilon, tolerance, coefficient lookup or per-alpha/pixel formula splice changed.

## Fixed sites and explicit source readbacks

Retain these r44 transforms and the complete32-pixel row geometry:

| Site | Center alpha | Changed x | Multiplier | Offset | Opacity |
|---|---:|---:|---:|---:|---:|
|0|49|13|2049/256|−896|67|
|1|51|0|8|−895|100|
|2|204|9|4|−385|100|

Each site independently crosses alpha offsets−4…4 with requested green offsets
−8…8: **459 rows/target pixels,14688 total pixels**. Only the selected x changes
its requested green byte. Other row pixels retain r44 `(117,120+x%16,240)`;
red/blue transforms remain .5/+8 and1/−4. Row width, clip and draw matrix stay
unchanged. Input and output are read back on transparent and black destinations.
The three centered complete rows match r44 **96/96** pixels exactly.

The requested byte and actual premultiplied source byte are kept separately.
Actual target greens span22–29,21–28,95–112 across the three sites. There are200
distinct site/source-RGBA groups;94 have multiple requested-green values. Every
such group has exactly one native result: no hidden requested-byte dependence
was observed within these controls.

Eight edge controls at site1 reach rational green clipping after input
quantization: `(alpha,delta_green)` = `(48,−8/−7/−6)`, `(51,−8)`,
`(53,−8/−7)`, `(55,−8/−7)`. They are explicitly marked in `targets`, retained
in every score/constraint and not presented as evidence of unclipped arithmetic.
No sample is filtered by how well a formula matches.

## Fixed sequence comparisons

Reuse the independently measured r44 input normalizations/reciprocals unchanged.
The three fixed sequences normalize by division, multiplication by rounded1/255,
or multiplication by estimated1/255. They retain input rounding before reciprocal
multiplication. Factorized coefficients are evaluated separately, never assumed
equivalent to those direct sequences. All old bounds and actual RGB controls are
retained before evaluating the new observations.

| Direct sequence | Actual target green exact /459 | New row RGB exact /44064 | Old RGB exact /1057824 |
|---|---:|---:|---:|
|divide|431|42812|1036354|
|multiply rounded1/255|418|42510|1036355|
|multiply estimated1/255|410|42434|1031716|

Every mismatch is a strict failure; maximum channel delta remains1. All three
alpha/opacity orders give identical predictions for each of these sequences on
these controls, so this experiment still does not identify their general order.
Division and rounded multiplication differ on408 new row channels (including
repeated unchanged neighbors); the459 actual target results are reported
separately to avoid treating those neighbors as new independent target controls.

At center alpha49, actual green24/25/26/27 yields native13/18/23/29. At center
alpha51, green23/24/25/26 yields4/12/20/28 (green22 is the separately marked
clipped case). At center alpha204, actual green97…110 yields80…132 in steps of4.
The full adjacent-alpha results and exact candidate counterexamples are retained
in `analysis.json.gz`; these observations do not authorize different formulas at
the three sites. Even the best target comparator still has28 counterexamples.

## Interval intersection and rejection

Combined constraints increase **1057824→1101888 RGB channels**. All old bounds
remain; new endpoints retain native source/transform/output witnesses. Unit-space
intervals tighten at alpha46 (7404→7257 float32 values),200 (3577→983), and208
(6070→5061). The corresponding normalized/byte intervals also tighten.

Every common construction is rejected against the retained interval sets.
Unit combined coverage for the seven old constructions is now
**50,106,119,208,46,106,178 /255**. The added factorized divide/rounded/estimated
normalizations give208/208/178. No space exceeds209/255. Both green-only interval
sets for all nine space/order models and the three combined RGB sets are checked;
no interval endpoint is used as an implementation coefficient.

## Reproduction and regressions

```sh
python3 tools/probes/build_flash_filter_probe.py --case cxform-adjacent-sites \
  --output /tmp/r45-native --ffdec "$FFDEC"
python3 tools/probes/capture_native_player.py /tmp/r45-native \
  /tmp/r45-native/native.log --player-app "$FLASH_PLAYER" --allow-window-activation
python3 -m tools.probes.analyze_cxform_adjacent \
  --root evidence/importer-loud-fail/r45 \
  --output /tmp/r45-analysis.json.gz  # expected exit 1
python3 -m unittest tools.tests.test_cxform_adjacent
python3 -m unittest discover -s tools/tests
```

Build/player/source/SWF hashes and the lossless original capture are under
`native/`. `provenance.json` pins analysis inputs and outputs. Four new tests
validate the independent grid, centered rows and clipping retention, all old
bounds/new native witnesses, globally fixed target comparisons, and hard rejection
of changed source bytes even when trace hashes are updated consistently.

Fresh checks in `acceptance.json` and `checks/`: Python610 tests (608 passed,
2 skipped); caches26/26, fingerprint8/8, protected, integrity, handoff and contracts
pass. r36 composition4032/4032 and complete Yulong4/4, r37 nested124416/124416,
leaf6/6 (69120), Glow4/4, GPU sampler71824/71824 and CPU sampler regressions
remain exact. Existing Python tests retain scalar3072, three-alpha25920 and both
held-out span8652 controls. No full roster replay or Web export was rerun for
this diagnostic-only change.

## Remaining blocker

The actual input-byte sweep rejects all tested common sequences; normalization
and reciprocal/rounding construction remain unexplained. The absence of output
variation for identical read-back source RGBA constrains a hidden input-provenance
hypothesis, but does not establish any arithmetic implementation.

A useful next independent comparison is to hold the verified premultiplied source
bytes fixed and bracket the transform multiplier/offset at the remaining target
counterexamples, retaining both center-alpha and neighboring-alpha controls.
Compare common operation sequences and all old bounds; never select coefficients
or an operation path from the locally matching RGB.

No new candidate advanced to native filter buffers or GPU. Historical results
remain native-buffer43006/43200, nested GPU67774/72576 and production components
9/54. Full AS/clip-action ownership remains a separate merge blocker. Draft only;
no production admission, merge, deployment or Worker change.
