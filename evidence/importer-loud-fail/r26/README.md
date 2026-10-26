# r26: isolated axes and corner responses narrow the scalar initialization error

**Draft / not merge-ready. No production sampler admitted.** This round records
stronger native constraints, not an exact general model. No runtime, generated
content, old reference, allowlist, tolerance or coordinate patch changed.

## 1. Independent axes and unique wrap edges

`bitmap-axis-ramps.as` keeps red dependent only on sourceX, green only on sourceY,
and blue constant113. Modes0/1 use alternating0/255 axes in clipped1024x1024 and
repeat2x2 bitmaps. Modes2/3 use clipped/repeat4x4 with unique edge values:
red[17,223,61,149], green[29,197,83,241]. Every source pixel is opaque.

The fixture samples every offset of lengths1/3/4/5/7/8, starts1/3/4/5/17/253,
scales2.5/5/8, translationsX=-.5/.75 and independentlyY=+/-.25, destinationY4.
Shape geometry extends beyond the sampled footprint, avoiding the r25 coverage
fringe. All8064 native blue samples are exactly113.

**336/336 overlapping-coordinate controls within lengths1/3 are identical.**
Across all lengths,825/3024 matched-coordinate observations differ from a native
single-pixel draw. Critically, eight differences are the fifth pixel of a
length5 span, in both repeat modes (2x2 and unique4x4). Thus a naive "first four
bulk, final pixel scalar" rule is not supported. Example:

- Repeat2x2, scale5, translation(-.5,.25), clip start1,length5,offset4:
  native RGB(178,88,113); drawing that same destinationX5 alone gives(179,89,113).
- The vertical gradient also changes, although sourceY and destinationY do not.
  A correction to horizontal UV alone cannot explain this observation.

Whole-model arithmetic hypotheses, without selecting a winner per pixel:

| Mode (2016 samples each) | Existing byte weights | Separable floor interpolation | Split initialization |
|---|---:|---:|---:|
| Clipped tiled1024 |1568|720|1568|
| Repeat2 |1004|1162|1004|
| Clipped unique4 |1880|807|1902|
| Repeat unique4 |1067|1438|1067|

None is exact; the comparison command exits1. Full per-length scores, deltas,
scalar overlaps and context differences: `comparison.json`; every native RGB
and candidate prediction: `comparison.jsonl`. Maximum byte-weight deltas by mode
are1/2/1/1. These are new probe scores, not component rendering improvements.

## 2. Four independent corner impulses

`bitmap-weight-impulses.as` independently sets each of four neighboring red texels
to255 while the other three remain0; green retains the vertical gradient, blue
remains113. Clipped/repeat modes, scales2.5/5/8, the same four translations,
starts3/4/5 and lengths1/4/5 give864 rows,2880 samples,720 four-corner groups.
All2880 blue samples remain113. Captures and derived responses: `weights/`,
`weights.json`.

For the four scale5 scalar controls at destination(4,4), all corner responses are
strictly between0 and255. **Within the existing byte-weight arithmetic family**,
`floor(255*w/256)` therefore uniquely recovers each weight as response+1.
Exhaustively testing all256x256 fractional pairs gives one solution per control:

| Translation | Native corner-red responses | Recovered weights | Unique fractions (fx,fy) | Old candidate |
|---|---|---|---|---|
|(-.5,.25)|82,82,43,45|83,83,44,46|(128,89)|(127,89)|
|(-.5,-.25)|69,69,56,58|70,70,57,59|(128,115)|(127,115)|
|(.75,.25)|124,40,65,23|125,41,66,24|(64,89)|(63,89)|
|(.75,-.25)|104,34,85,29|105,35,86,30|(64,115)|(63,115)|

This isolates the old scalar error to the X fraction under that arithmetic
family, rather than an arbitrary final-RGB offset. It is not proof that every
Flash path uses that family, or permission to patch these coordinates.

## 3. Attractive local fix rejected by independent captures

A diagnostic split-initialization hypothesis floors the exact inverse transform
at the integer pixel origin, then adds a rounded half-step of the16.16 inverse;
subsequent X steps use the quantized inverse. It fixes all72/72 single-pixel
clipped controls in both new clipped modes (previous68/72 and70/72).

However, independent pinned native captures reject it:

- r22 extended: **4096/4096 ->3775/4096**;
- r24 single-pixel clipped: **1004/1008 ->751/1008**.

Regression tests reproduce that rejection. The production model and old
candidate remain unchanged. No sample-dependent formula choice was introduced.

## Remaining blocker and next experiment

We now know four required X fractional bytes and a native context effect that
also changes the Y-gradient result. The missing rule is how Flash initializes
coordinates and partitions clipped/repeated scan spans, together with arithmetic
used for each partition. A length>=4 switch alone is insufficient.

Next vary source width while preserving local unique edge texels (e.g.4/8/16),
then move the same length5 probe across the first and last source boundaries.
Record all four impulses at every offset. This can distinguish a prefix split
at wrap/clamp boundaries from a global four-pixel grouping. Independently sweep
integer pixel origins and translations around the four known scalar fractions;
require one initializer to retain the distant r23 and extended r22 suites before
accepting it. Do not pick a span path based on whichever formula matches RGB.
Rotation, negative scales, transparent edges and smoothing variants were not added.

## Production and validation

Caches remain26/26. Fresh checks/counts are in `acceptance.json` and `checks/`.
Runtime/generated/locked files are unchanged from6c964fc4. Full roster/GPU/Web
export were not rerun because runtime did not change (historical full runtime:r20,
Web:r21). Component images were not remeasured: **9/54** baseline, color3/5,
order2/4, matrix20/24; rush234/5103 differing RGB channels. r23/r24 admission
suite results are unchanged, not cleared by these new measurements.

Exact production pixel parity and full AS/clip-action ownership proof still block
merge. Placement34/34 clearance is unchanged. No merge, deployment or Worker change.

## Reproduction

```sh
# CASE=bitmap-axis-ramps, then bitmap-weight-impulses
python3 tools/probes/build_flash_filter_probe.py --case "$CASE" --output "$OUT/$CASE" --ffdec "$FFDEC"
python3 tools/probes/capture_native_player.py "$OUT/$CASE" "$OUT/$CASE/native.log" \
  --player-app "$FLASH_APP" --allow-window-activation --timeout 50
python3 tools/probes/analyze_bitmap_axis_ramps.py \
  --native-log evidence/importer-loud-fail/r26/axis/native.log --output "$OUT/comparison.json"
# Required exit1; writes summary JSON plus full per-coordinate JSONL.
python3 tools/probes/analyze_bitmap_weight_impulses.py \
  --native-log evidence/importer-loud-fail/r26/weights/native.log --output "$OUT/weights.json"
# Diagnostic success is not a production parity gate.
python3 -m unittest tools.tests.test_bitmap_axis_ramps tools.tests.test_bitmap_weight_impulses
```

Source/SWF hashes, run identities and native launch metadata are retained.
Both analyzers reject missing, duplicate, mixed-run or misidentified rows and
invalid RGB samples. Tests pin source hashes and the independently observed
constraints, including the old-suite rejection of the local initialization fit.
