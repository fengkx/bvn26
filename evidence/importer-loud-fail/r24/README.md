# r24: native bitmap sampling depends on draw spans

**Not merge-ready. No production sampler admitted.** No runtime, generated content,
reference output, tolerance or allowlist changed. This round isolates a sharper
blocker rather than claiming exact rendering from an incomplete coordinate model.

## New native controls

`bitmap-spans.as` keeps source contents, transform, geometry and sampled coordinates
fixed, varying only destination width (260/520/524/768) and clip start (0/5/17).
It tests clipped1024x1024 and repeating2x2 fills at scales2.5/8, phases-224/224,
y155. All source bitmaps contain the same tiled RGB basis. Pixels outside either
clip are excluded from paired comparisons.

**26/40 comparisons differ, by at most2 channels.** For clipped scale2.5,
phase224, changing width520 to768 changes pixels517–519 even though their source
coordinates do not change. Width260 instead changes257–259; width524 changes521–523.
Changing the clip start also changes some interior pixels. Full coordinates and
both native RGB values are in `span-context.json` (96 validated native rows).

This establishes draw-context dependence. It does **not** establish the internal
Flash implementation: bulk versus short-span arithmetic and segmented coordinate
initialization are hypotheses. A shader depending only on texture coordinates is
not justified by the current model. No fixed x=255 or last-three-pixels patch was
added.

## Isolating short spans

`bitmap-scalar-clipped.as` and `bitmap-scalar-repeat.as` draw each sampled pixel
with its own1x1 destination clip. Transform/source contents/coordinates match the
r23 sparse probes. A single fixed byte-weight interpolation hypothesis is tested;
we never choose whichever formula happens to match the native answer.

| Probe | Exact | Remaining | Maximum channel delta |
|---|---:|---:|---:|
| Single-pixel clipped |1004/1008|4|1|
| Single-pixel repeat |854/1008|154|2|

Both comparison commands exit1. The four clipped failures are all at destination
(4,4), scale5; phase-128 and224, alpha255 and128. Their native/candidate RGB:

| Alpha | Phase | Native | Candidate |
|---:|---:|---|---|
|255|-128|128,128,89|129,127,89|
|255|224|134,64,115|135,63,115|
|128|-128|64,64,45|65,64,45|
|128|224|67,32,58|68,32,58|

Full per-coordinate results are in `scalar-clipped.json` and `scalar-repeat.json`.
These are new diagnostic suites, not improvements to the unchanged r23 long-span
scores: clipped965/1008, repeat509/1008, scan6008/6048. Base1536/1536 and
extended4096/4096 remain historical r23 results, with no candidate arithmetic change.

Next experiment: independently vary translation and destination clip origin near
these four scale5 cases to distinguish inverse-matrix translation quantization
from multiplication of a quantized inverse scale. Then measure dense short spans
of lengths1–8 around a moved clip start, comparing initialization and stepping.
Do not infer a span selector from whichever arithmetic happens to match. Repeat
mode needs its own coordinate/wrap explanation; the single-pixel isolation still
fails154 points. Affine rotation, negative scales, transparent edges and smoothing
flags also need coverage before production admission.

## Validation and production status

Fresh checks and counts: `acceptance.json`; raw check outputs: `checks/`.
Runtime/generated/locked files are unchanged from6ea1cf2f. Consequently production
GPU images were not re-rendered: components **9/54→9/54** (baseline retained),
color3/5, order2/4, matrix20/24, rush21/21 clocks with234/5103 RGB channels differing.
Caches remain26/26. No full roster/GPU/Web export rerun: runtime was not changed.
Last full runtime acceptance:r20; last full build_web:r21, not fresh r24 claims.
Placements remain34/34 cleared. Exact component pixels and full AS/clip-action
ownership proof still block merge. No merge, deployment or Worker changes.

## Reproduction

```sh
# Run once per CASE: bitmap-spans, bitmap-scalar-clipped, bitmap-scalar-repeat.
python3 tools/probes/build_flash_filter_probe.py --case "$CASE" --output "$OUT/$CASE" --ffdec "$FFDEC"
python3 tools/probes/capture_native_player.py "$OUT/$CASE" "$OUT/$CASE/native.log" \
  --player-app "$FLASH_APP" --allow-window-activation --timeout 50
python3 tools/probes/analyze_bitmap_spans.py \
  --native-log evidence/importer-loud-fail/r24/spans/native.log --output "$OUT/spans.json"
# Context diagnostic only; its success does not mean rendering parity.
python3 tools/probes/analyze_bitmap_inverse.py --kind scalar-clipped \
  --native-log evidence/importer-loud-fail/r24/scalar-clipped/native.log --output "$OUT/clipped.json"
python3 tools/probes/analyze_bitmap_inverse.py --kind scalar-repeat \
  --native-log evidence/importer-loud-fail/r24/scalar-repeat/native.log --output "$OUT/repeat.json"
# Both arithmetic comparisons MUST exit1; no tolerance.
python3 -m unittest tools.tests.test_bitmap_span_analysis tools.tests.test_bitmap_inverse_analysis tools.tests.test_bitmap_phase_analysis
```

Build metadata pins AS/SWF hashes and run identities. Native trace files are
unmodified captures. Analyzers require ordered identities, exact sample counts,
a single run and successful completion; malformed or partial captures fail.
