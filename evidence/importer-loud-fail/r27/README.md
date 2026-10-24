# r27: independently quantized affine initialization and exact clipped scan candidate

**Draft / not merge-ready. CPU diagnostic only, no production sampler installed.**
Clipped suites are now exact under one geometric candidate. Repeat remains
inexact, so the overall admission command still exits1. No runtime, generated
content, original reference, tolerance, allowlist or coordinate patch changed.

## Initializer: quantize inverse coefficients independently

The new origin fixture moves destinationX and translation together, preserving
ideal source coordinates. At exact quarter phases,20/108 native corner groups
change across origins4/5/8/17/63/127/255/511. The previous expression multiplied
a quantized inverse by an already translated coordinate and could not express
this. The new candidate instead computes:

```
Q(t) = trunc(4*t)/4
A = floor(65536/scale + 0.5)
Tx = floor(-Q(tx)*65536/scale + 0.5)
Ty = floor(-Q(ty)*65536/scale + 0.5)
H = floor(A/2 + 0.5)
sourceX = (pixelX*A + Tx + H)/65536 - 0.5
sourceY = (pixelY*A + Ty + H)/65536 - 0.5
```

This is an inferred positive-uniform-scale model, not a claim of recovered Flash
source code or coverage of arbitrary affine transforms. It preserves all r22
base/extended samples. Unlike the rejected r26 split initializer, it also fixes
all four r24 clipped scalar counterexamples without regressing distant probes.

Example: scale5 givesA13107,H6554. At destinationX4,tx=-.5,Tx6554 yields a source
fraction128/256. Moving toX5,tx=.5 givesTx=-6554 and a fraction127/256, exactly as
native observes despite the same ideal source coordinate. No origin-specific
branch is used. New independent origin sweep: **1632/1632 RGB exact**.

## Clipped scan partition candidate

For full-coverage pixels in the axis-aligned rectangular fixtures:

1. Anchor chunks at the first fully covered destination pixel after clipping;
   each chunk contains at most256 pixels.
2. Within each chunk, the candidate interior has sourceX/sourceY in
   `[1, sourceDimension-1)`. Outside that interval, use byte bilinear weights.
3. Process the contiguous interior X run in complete groups of four using
   vertical integer interpolation then horizontal integer interpolation, flooring
   after each. The remaining0–3 interior pixels use byte weights.
4. Byte weights floor the first three products and assign the residual to the
   fourth, preserving sum256. Both arithmetic functions are shared diagnostics.

The selector reads geometry, clip bounds, source dimensions and coordinates;
**it never reads native RGB or chooses whichever formula matches a pixel**.
There are no special cases for particular fighters, output widths, sample Xs or
measured channel deltas. The256/four-pixel partition remains an inferred model,
validated against independent moved-width/clip probes as well as sparse/row data.

| Native suite | Before | r27 | Max delta |
|---|---:|---:|---:|
| r22 base |1536/1536|1536/1536|0|
| r22 extended |4096/4096|4096/4096|0|
| r24 single-pixel clipped |1004/1008|**1008/1008**|0|
| r23 distant clipped |965/1008|**1008/1008**|0|
| r23 continuous rows |6008/6048|**6048/6048**|0|
| r24 independent widths/clip starts |not previously scored with this model|**24080/24080**|0|
| r26 independent clipped axes |not previously scored with this model|**4032/4032**|0|
| New origin sweep |new|**1632/1632**|0|
| New clipped boundaries |new|**2016/2016**|0|

Sixteen r24 observations outside the requested clip rectangle are explicitly
excluded from sampling scores; their raw native captures are unchanged. Coverage
fringes are rejected by the candidate, not silently treated as interior samples.
These numbers are native-vs-CPU arithmetic comparisons, **not Godot image parity**.

## New source-width / boundary controls and remaining repeat blocker

`bitmap-boundary-spans.as` uses widths4/8/16, height2, unique first/last green
texels17/223, interior61, blue113, and four separate red corner impulses. It
moves length1/5 clips around the first and last texel centers at scales5/8,
keeping comparable local boundary coordinates. Native1344 rows /4032 RGB samples.

All **1344/1344** per-corner width controls are identical across4/8/16. Matched
single-pixel vs length5 comparisons: clipped1200/1200 identical; repeat996/1200
identical (**204 differ**). Thus width alone does not explain the repeat arithmetic;
changing clipped to repeated does. Full identity/offset and both RGB values are
in `boundary_context_differences` in `comparison.json`.

Only the initializer is updated in the repeat diagnostic controls; no repeat
partition has been inferred or admitted:

| Repeat control | Before | Initializer-only r27 | Remaining | Max delta |
|---|---:|---:|---:|---:|
| Distant (existing separable hypothesis) |509/1008|511/1008|497|3|
| Single-pixel (existing byte hypothesis) |854/1008|858/1008|150|2|

The647 remaining points have full scale,phase,X,Y,alpha,native/candidate RGB in
`comparison.json`. This prevents the clipped success from masking repeat failures.
**Overall admission stays false; no production wiring.**

Next isolate the repeat initializer from its interpolation: capture four corner
responses at distant source coordinates while holding the modulo position fixed,
then independently translate the bitmap fill matrix versus the draw matrix. The
negative/positive wrap transition and scalar initialization must be explained
before applying any bulk partition. Keep the now-exact clipped suites as strict
regressions; do not replace their initializer with the earlier locally fitted one.
Rotation, negative scales, transparent edges and smoothing variants remain outside
this experiment; no production support for them is claimed by these probes.

## Evidence and acceptance

- `boundary/`, `origin/`: original native traces, source/SWF hashes and launch metadata.
- `comparison.json`: exact counts, all remaining repeat coordinates, new native
  controls and SHA256 of every reused native capture.
- `acceptance.json`, `checks/`: fresh Python/cache/fingerprint/protected/integrity/
  handoff/contracts checks.
- `tools/probes/bitmap_sampling_candidate.py`: shared diagnostic math, not runtime code.

Runtime/generated/locked files remain unchanged fromf2c946b5. Caches remain26/26.
Full roster/GPU/Web export was not rerun because production did not change
(historical full runtime:r20, Web:r21). Components were not remeasured and remain
**9/54 baseline**, color3/5, order2/4, matrix20/24, rush234/5103 differing RGB
channels. Exact production pixels and full AS/clip-action ownership proof still
block merge. Placement34/34 clearance is unchanged. No merge/deploy/Worker change.

## Reproduction

```sh
# CASE=bitmap-boundary-spans, then bitmap-origin-sweep
python3 tools/probes/build_flash_filter_probe.py --case "$CASE" --output "$OUT/$CASE" --ffdec "$FFDEC"
python3 tools/probes/capture_native_player.py "$OUT/$CASE" "$OUT/$CASE/native.log" \
  --player-app "$FLASH_APP" --allow-window-activation --timeout 50
python3 tools/probes/analyze_bitmap_sampling_r27.py --output "$OUT/comparison.json"
# Exit1 REQUIRED: repeat is not exact; clipped success cannot admit production.
python3 -m unittest tools.tests.test_bitmap_sampling_r27
```

Both new captures require complete ordered identities, exact sample counts,
one run and successful completion. Reused captures pass their existing strict
validators. Tests pin new fixture hashes, all exact clipped suites, repeat
rejection, the native origin/width observations and explicit coverage rejection.
