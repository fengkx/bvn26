# r25: independently measured four-pixel short-span transition

Draft PR #48 remains **not merge-ready**. No runtime sampler was installed, and no
runtime/generated/locked inputs, tolerance, allowlist or old reference changed.
This round supplies a sharper measured blocker, not production parity.

## Experiment and results

The checked-in `bitmap-short-spans.as` produces1896 native rows /4248 RGB samples:

- Translation isolation: clipped/repeat, scales2.5/5/8, X translation-1..1 in1/8
  steps, Y translation independently+/-1/4, one-pixel clips at X3..8,Y4.
- Short spans: the same scales/modes, X translation-1/2 or3/4, Y translation1/4,
  clip starts0/1/3/4/5/17/253 and lengths1..8, Y4. Target size272x8 is fixed.
- The same tiled2x2 RGB basis is used in a1024x1024 clipped bitmap or2x2 repeated
  bitmap. Alpha255; no rotation, negative scale or smoothing-mode variation.

**27/84 first-pixel controls change exactly at length4.** All27 have identical
first-pixel RGB for lengths1–3, another identical RGB for lengths4–8. This is a
native-only comparison: no candidate formula was used to choose a path. For
example clipped scale2.5, translation(-.5,.25), start4 gives(129,127,203) for
lengths1–3 and(127,128,204) for lengths4–8. Repeat scale5 at the same translation
and start gives(128,128,89) then(127,127,88).

This narrows the r24 draw-context effect to a measured four-pixel length boundary
in these short spans. It does NOT prove how longer spans are partitioned, how
source coordinates are initialized or which integer arithmetic is used. No
length-based runtime selector was introduced.

Three whole-model hypotheses were scored, all using fixed byte bilinear weights:

| Interior samples | Quantized inverse (r24) | Exact inverse | Exact start + quantized stepping |
|---|---:|---:|---:|
| Independent translation, clipped |598/612|546/612|546/612|
| Independent translation, repeat |568/612|516/612|516/612|
| Length1–8, clipped |1194/1488|1133/1488|1195/1488|
| Length1–8, repeat |764/1488|710/1488|750/1488|

Maximum deltas for the unchanged quantized-inverse model:1,1,2,3 respectively.
No model is exact; the analyzer exits1. Exact reciprocal or exact initialization
alone does not resolve the error. We do not select a different model per pixel.

48 additional observations at destinationX0 with positiveX translation lie on
the transformed shape's coverage fringe. They remain in `observations.jsonl` with
`geometry_interior:false`; pure texture-sampling scores explicitly exclude them.
Their coverage mismatch reaches185 (clipped) /153 (repeat), so they must not be
mistaken for interpolation-only counterexamples or silently counted as passing.
Geometry coverage is not modeled in this focused probe.

The612 single-pixel translation controls also compare modes at identical
coordinates:30 differ between clipped and repeat; all30 have negative sourceX
in the bilinear footprint (scale8). None differs at a fully interior footprint.
This narrows that mode contrast to boundary wrapping for this control; it does
not resolve the r24 distant-repeat counterexamples or prove general equivalence.

## What remains / next discriminating experiment

The four r24 scale5 scalar failures are still unresolved, not patched. The new
independent translation grid exposes14 clipped scalar failures. Separately
rounding matrix terms or replacing the reciprocal was explored but did not
produce an exact common model; no such adjustment is committed as a candidate.

Next use separate horizontal/vertical grayscale ramps with a third constant
channel to distinguish source-coordinate quantization from bilinear weight
rounding (the current RGB basis can conflate them). Measure each offset within
lengths3/4/5/7/8, keeping clip start and transform fixed. Then vary clip start
without moving the sampled coordinate. Repeat-boundary tests should use unique
edge texels, so clamping/wrapping and weight rounding can be distinguished. Do not
infer a span selector by choosing whichever formula matches a measured pixel.

r23/r24 admission suites are unchanged: base1536/1536, extended4096/4096;
clipped965/1008, repeat509/1008, continuous scan6008/6048; r24 single-pixel
clipped1004/1008 and repeat854/1008. These old scores were not improved this round.
Rotation, negative scales, transparent edges and smoothing variants stay outside
this experiment. Production admission remains blocked.

## Evidence and acceptance

- `short/native.log`: unmodified Flash Player Debugger32 capture, ordered run IDs.
- `short/build.json`, `short/capture-environment.json`: source/SWF hashes and environment.
- `comparison.json`: all model scores and native first-pixel length controls.
- `observations.jsonl`: every coordinate, native RGB and all three predictions,
  including coverage-fringe observations.
- `acceptance.json`, `checks/`: fresh tool/cache/fingerprint checks.

Production runtime is unchanged from9e706e78. Component images were not remeasured:
**9/54 remains the baseline**, color3/5, order2/4, scalar matrix20/24, rush234/5103
RGB channels different. Caches remain26/26. Full roster/GPU/Web export were not
rerun because production did not change (last full runtime:r20; Web:r21).
Exact production pixels and full AS/clip-action ownership proof remain merge
blockers; placement34/34 clearance is unchanged. No merge/deploy/Worker changes.

## Reproduction

```sh
python3 tools/probes/build_flash_filter_probe.py --case bitmap-short-spans \
  --output "$OUT/short" --ffdec "$FFDEC"
python3 tools/probes/capture_native_player.py "$OUT/short" "$OUT/short/native.log" \
  --player-app "$FLASH_APP" --allow-window-activation --timeout 50
python3 tools/probes/analyze_bitmap_short_spans.py \
  --native-log evidence/importer-loud-fail/r25/short/native.log --output "$OUT/comparison.json"
# Exit1 required: no exact model. Output includes all observations.
python3 -m unittest tools.tests.test_bitmap_short_span_analysis
```

Capture validation requires all1896 identities in order, exact per-span sample
counts, RGB range, one run and successful completion. Tests pin the fixture hash
and native length transition, reject malformed captures and preserve the failed
production-admission state. No new runtime behavior is claimed from these tests.
