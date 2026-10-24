# r28: repeat matrix routing and a constrained signed-byte candidate

**Draft / not merge-ready. Repeat remains inexact; no production wiring.**
The exact r27 clipped initializer/partition is unchanged. No runtime/generated
content, old reference, allowlist, tolerance or coordinate patch changed.

## New native probe

`bitmap-repeat-matrices.as` captures2940 single-pixel RGB responses from four
independent corner impulses on a repeated2x2 bitmap. Blue is constant113 and is
exact2940/2940. It uses scales1.01/1.7/2.5/5/7.99/8/13.3, texture-period offsets
-128/-1/0/1/128, and local coordinates-.125/0/.25/.5/.875/1/1.125. The target
sample is always(32,32), geometry fully covers it, and nominal sourceY is.35.

Three routes have the same *ideal* composed sourceX (2*period+local coordinate):

0. All translation in the draw matrix; fill matrix identity.
1. Draw matrix holds the local coordinate; fill matrix moves by an integer
   number of source periods. The draw matrix is identical across periods.
2. Draw matrix holds the origin; fill matrix carries period and fractional shift.

Do not assume that equal ideal matrices have equal quantized rendering matrices.
Across the five periods, respectively192/196,136/196 and164/196 per-corner
controls differ. In particular, route1 changes despite exact integer-period fill
translations; a coordinate-only periodicity assumption is insufficient. Raw
observations and all group identities are retained in `comparison.json`.

Routes0/1 at scale8 isolate a cleaner subset: binary-exact scale, quarter draw
translation and integer fill translation. No fractional fill-matrix translation
needs to be modeled for those280 RGB samples.

## Signed byte-coordinate hypothesis

The existing clipped initializer is reused unchanged for this controlled subset.
Before repeating texel lookup, test this uniform operation on each source axis:

```
byteCoordinate(v) = trunc(256*v) - (1 if v < 0 else 0)
quantizedCoordinate(v) = byteCoordinate(v) / 256
```

It differs from mathematical floor at exact negative integer byte coordinates.
For example, sourceX=-1.5 lands at byte-385 instead of-384, which wraps to byte127
instead of128 in a two-texel period. This accounts for the negative/positive
transition observed in the binary controls without a sample-specific correction.

**Binary controls improve160/280 ->280/280**, using the same byte bilinear
weights as the existing diagnostic. This does not uniquely identify native C/C++
implementation: on grid-aligned negative inputs, other tiny-negative-bias
hypotheses may be observationally equivalent. Off-grid controls are still needed
before calling the general negative initializer recovered. The function is kept
in the diagnostic analyzer only, not the shared clipped candidate or runtime.

## Independent repeat checks still reject admission

Applying that single operation, without changing the clipped affine coefficients
or choosing any new bulk path, gives:

| Existing native suite | r27 | r28 signed-byte hypothesis | Remaining | Max delta |
|---|---:|---:|---:|---:|
| Single-pixel repeat |858/1008|**862/1008**|146|2|
| Distant repeat (existing separable hypothesis) |511/1008|**513/1008**|495|3|

All641 remaining coordinates and native/candidate RGB values are in
`comparison.json`. The distant score tests the initializer with the previous
whole-suite separable hypothesis; it does **not** claim an exact repeat partition.
Overall admission remains false and the command exits1.

The other matrix routes/scales are native controls, not silently claimed as
predicted by this narrow binary model. Fractional fill translation and general
repeat initialization still lack an exact composition/quantization rule. Exploratory
higher-precision reciprocal, forward-matrix quantization, determinant rounding,
modulo-before-inversion and nearest-byte variants did not produce a uniform
exact model; none replaced the exact clipped initializer.

## Strict clipped regressions: unchanged and rerun

The r27 checker is rerun by the r28 analyzer; all remain exact:

- base1536/1536 and extended4096/4096;
- single-pixel clipped1008/1008 and distant clipped1008/1008;
- continuous scan6048/6048;
- independent clipped widths24080/24080 and axes4032/4032;
- origin sweep1632/1632 and clipped boundaries2016/2016.

These are CPU/native diagnostic comparisons, not Godot component image parity.
The shared clipped sampling candidate file is byte-identical to r27. Capture
validation was generalized with an explicit revision parameter; r27 callers
retain the default r27 prefix, r28 requires r28. No native text is rewritten.

## Remaining blocker / next experiment

Do not apply a bulk selector before solving the repeat scalar initializer. Next
capture distant **positive** X and Y origins separately with exact integer draw
translations and unique4x4 texels. Use four-corner responses to derive intervals
for the affine coefficients and intersect those constraints across origins;
validate any common initializer on held-out scales and the current suites.
This separates coefficient errors from negative wrap. Separately sample negative
coordinates just off the1/256 grid to distinguish truncation-minus-one from a
small epsilon/rounding effect. Keep fractional fill-matrix routing as a separate
composition control; do not choose formulas per pixel to fit observed RGB.

## Acceptance and production status

Fresh counts/logs: `acceptance.json`, `checks/`. Caches remain26/26. Runtime,
generated content and locked inputs are unchanged fromde0fb448. Full roster/GPU/
Web export were not rerun because production did not change (historical full
runtime:r20, Web:r21). Component images were not remeasured: **9/54 baseline**;
color3/5, order2/4, matrix20/24, rush234/5103 differing RGB channels.

Exact production pixels and full AS/clip-action ownership proof still block merge.
Placement34/34 clearance is unchanged. No merge/deploy/Worker changes.

## Reproduction

```sh
python3 tools/probes/build_flash_filter_probe.py --case bitmap-repeat-matrices \
  --output "$OUT/matrices" --ffdec "$FFDEC"
python3 tools/probes/capture_native_player.py "$OUT/matrices" "$OUT/matrices/native.log" \
  --player-app "$FLASH_APP" --allow-window-activation --timeout 50
python3 tools/probes/analyze_bitmap_repeat_matrices.py --output "$OUT/comparison.json"
# Exit1 REQUIRED: repeat is still inexact. Also reruns every r27 clipped regression.
python3 -m unittest tools.tests.test_bitmap_repeat_matrices tools.tests.test_bitmap_sampling_r27
```

`matrices/` retains the original trace, source/SWF hashes and native environment.
The comparison pins every reused trace hash. Tests require ordered identities,
exact sample count, one run, valid RGB and successful completion; they pin the
fixture hash, native binary controls, remaining failures and clipped regressions.
