# r225: independent child/draw translation controls

Retain original shape56/57 records, fill65 and authored quadrilateral masks. Independent opaque horizontal/vertical source ramps replace only bitmap55. Sweep one child or draw translation operand at a time, X/Y, around quarter boundaries; preserve both cache states and two draw scales.

Native capture contains **576 images / 1327104 RGBA**, **7360 exact source readbacks**, **288 matrix groups**. Requested and actual properties are separate: child translations are read back on the twip grid. Bounds are read independently in each cache state; all 288 pairs agree. Bounds are not assumed to be filter/cache allocation origins.

Twelve globally fixed models all fail. Scaled-child quarter consumption / minimum footprint / vertical-horizontal is **563949/686772**, maximum RGBA deltas **[17,14,14,48]**. Full geometry-interior comparisons retain alpha/coverage failures, including pixels not proved fully covered by native rasterization. No best-match model is admitted or routed per pixel. Original r224 controls and JPEG rejection totals are retained.

Native adjacent-pair evidence is independent of those formulas: 240/256 child pairs and 192/256 draw pairs are unchanged. All 128 child pairs with identical actual translation properties are unchanged. Draw differences occur only across the sampled quarter-boundary neighbors. This constrains property/consumption behavior, not complete affine sampling.

## Reproduce

```sh
python3 -m tools.probes.build_jinye_translation_controls --output /tmp/bvn-r225/native --ffdec /tmp/bvn-loud-fail/r02/ffdec/ffdec-cli.jar
# Capture source0 and source1 sequentially using capture_native_player.py.
python3 -m tools.probes.analyze_jinye_translation_controls --native evidence/importer-loud-fail/r225/native --output /tmp/bvn-r225/analysis.json
python3 -m unittest tools.tests.test_jinye_translation_controls tools.tests.test_jinye_tag_controls tools.tests.test_jinye_affine_initializers tools.tests.test_smooth_affine_axis_reduction
```

`analysis.json.gz` retains every fixed-model failure, property ledger and adjacent native pairs. Source textures come only from the synthetic generator; native images remain references. Original locked SWFs and production code are unchanged. Mandatory checks and focused tests are recorded in acceptance.json/checks. Full roster/Web and 54 production images were not rerun. Source-backed complete diagnostic coverage remains46/54; historical production9/54. Full AS/clip-action ownership remains open. Candidate/GPU/production admission remain false.

## Next discriminator

Analyze pinned r223/r225 horizontal/vertical ramp adjacent-pixel differences on a geometry-selected deep-interior subset (both endpoints at least two pixels from the authored edge), separately by cache/scale and native-unchanged translation groups. Verify opaque alpha and constant-blue invariants without using output RGB to choose a renderer. Retain every full-suite failure: this subset isolates gradients; it does not shrink admission. Compare globally fixed predicted gradients and level residuals. Gradient counterexamples reject slope/rounding; consistent gradients with constant level bias would isolate initialization. Conditional centroid intervals may reject independently defined coefficients, never supply fitted coefficients. Retain original corner impulses for weight-order checks before any further rendering experiment.
