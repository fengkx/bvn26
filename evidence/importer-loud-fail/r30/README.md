# r30: repeat scalar half-step rounding and period denominator

**Draft / not merge-ready. All captured scalar admission controls now match;
continuous repeat spans still fail. No production wiring.**
The exact clipped candidate, production runtime/generated content, locked inputs,
old references, thresholds and allowlists are unchanged.

## Native experiment and interpretation

`bitmap-repeat-rounding.as` independently sweeps draw origins14/15/16 and target
pixels3/4/5 at scale3, on both axes, with source sizes2/4/8/16. Four corner impulses
in red, unique source-axis texels in green and constant blue113 provide288 RGB
responses. This reproduces the old scale3/origin15 failures at all three
(origin,pixel) pairs (14,5),(15,4),(16,3), specifically at size4.

The old model rounds the fixed inverse half-step upward at a tie. Changing only
that operation to nearest-even changes276/288 to288/288 and clears the four old
r29 failures without regressing its scalar or pixel-step controls. At scale3,
A=21845, so H changes10923→10922; at scale5,A=13107 and H stays6554. This explains
why the r29 attempt to leave *every* half-step unrounded traded scale3 failures
for scale5 failures.

An independent extension, `bitmap-repeat-half-step.as`, sweeps six scales
3/5/7/11/13/1.7, seven origins0/3/7/14/15/16/31, three target pixels and all four
sizes/both axes:4032 responses. Old r29 gets3972/4032; nearest-even alone gets
4024/4032. The remaining eight are size2, scale5/origin7/pixel5 and
scale7/origin14/pixel3, on both axes/two impulses each.

In those cases the fixed source coordinate is exactly131071/65536. The
first-order factor `1+1/131072` stays just below2; native responses require2.
The exact period ratio `131072/131071` yields2. Using the same ratio for every
size clears4032/4032 and retains all previous scalar suites. This discriminates
the two denominator hypotheses requested inr29; it does not establish a native
C++ implementation or prove fractional fill-matrix composition.

## One scalar model, integer arithmetic

For positive axis scale s, identity fill matrix, source dimension N, draw
translation t and destination pixel p, define R as floor(value+.5):

```
A = R(65536/s)
H = nearest_even(A/2)
T = R(-trunc(4*t)/4/s * 65536)
V = p*A + T + H - 32768
numerator = V*N*256
denominator = N*65536 - 1
byte = trunc_toward_zero(numerator/denominator) - int(numerator < 0)
source_coordinate = byte/256
```

The normalization division is integer/rational, avoiding a floating epsilon at
byte-grid boundaries. The earlier inverse scale and inverse translation rounding
remain unchanged; the new evidence requires a different half-step tie rule for
repeat, not a change to clipped sampling. The signed negative rule remains an
observational model, not a unique native implementation claim.

`analyze_bitmap_repeat_rounding.py` is diagnostic only. It does not add a runtime
sampler or select formulas using native RGB.

| Native scalar suite | r29 candidate | r30 | Max delta |
|---|---:|---:|---:|
| Old draw-translation controls |1196/1200|1200/1200|0|
| Old destination pixel-step |960/960|960/960|0|
| Old repeat single pixel |1008/1008|1008/1008|0|
| Negative off-grid |168/168|168/168|0|
| r28 binary matrix routes |280/280|280/280|0|
| New scale3 size/origin/pixel controls |276/288|288/288|0|
| New independent half-step controls |3972/4032|4032/4032|0|
| New short spans, lengths1/3 |—|768/768|0|

Scales1.3/6.25 fromr29 remain included. Fractional fill-matrix routing is still a
separate unproven composition control; the binary route subset does not admit it.

## Continuous wrap spans: still a hard admission failure

After scalar controls passed, `bitmap-repeat-short-spans.as` captured5376 RGB
responses on sizes2/4/8/16, scales3/5/8/1.7, draw origins-15/0/15, lengths
1/3/4/5/7/8 and all four corner impulses. Each clip starts at destinationX=4;
only its length changes. Other-axis scale8 and targetY=4 remain fixed. Geometry
fully covers every clip; there is no coverage fringe.

Fixed whole-suite diagnostic hypotheses (never chosen per pixel):

| Hypothesis | Exact | Remaining | Max delta |
|---|---:|---:|---:|
| Scalar byte weights everywhere |3469/5376|1907|2|
| Vertical-then-horizontal separable everywhere |3981/5376|1395|2|
| Full groups of4 separable, tail scalar |4789/5376|587|2|
| Old distant suite, previous separable hypothesis |571/1008|437|2|

The old distant score is unchanged. Neither interpolation hypothesis is admitted.
All587 short-span group4 failures and437 distant failures have exact identities,
coordinates, RGB values and deltas in `comparison.json`; alternative whole-suite
scores are retained without duplicating all their failure records.

Native-to-native overlap controls independently reject the simple group4 model:

- Length1 vs3:0/192 first-pixel differences.
- Length1 vs4:96/192 differences.
- Length4 vs5:18/768 overlapping pixel responses differ.
- Length4 vs8:69/768 differ, despite identical first four destination coordinates.

For size2/scale5/origin0/corner0/offset1, native RGB is(96,39,113) at length4,
but(95,39,113) at length8. For size2/scale3/origin-15/corner0/offset3, green is54
at length4 and53 at length5. This is not explained by a length>=4 switch alone.
Lengths1/3 are fully exact with the scalar model, including every offset.

## Next discriminating experiment

Keep the admitted scalar initializer fixed. For size2/scale5/origin0 and
size2/scale3/origin-15, sweep clip lengths4 through16 one at a time, holding clip
start and transform fixed; then shift clip start while retaining overlapping
sample coordinates. Capture four-corner responses plus independent horizontal
and vertical ramps. Recover coordinate/weight intervals for the first, interior
and last pixels to distinguish endpoint-derived stepping from an interpolation
rounding change. Compare spans that cross a wrap with spans wholly within one
period. Do not infer a partition by whichever formula matches RGB.

## Reproduction and acceptance

Build each named `.as` fixture with `build_flash_filter_probe.py --case NAME`,
then capture using `capture_native_player.py --allow-window-activation` and the
same Flash Player Debugger32.0.0.465/Rosetta asr29. `rounding/`, `half/`, `spans/`
retain untouched native traces, source/SWF hashes and per-capture environment.

```sh
python3 tools/probes/analyze_bitmap_repeat_rounding.py --output /tmp/r30-comparison.json
# Exit1 REQUIRED: continuous spans remain inexact; all clipped regressions rerun.
python3 -m unittest tools.tests.test_bitmap_repeat_rounding
```

See `acceptance.json` and `checks/` for fresh acceptance. Caches26/26; all exact
clipped regressions retained: base1536,extended4096,single1008,distant1008,
scan6048,widths24080,axes4032,origins1632,boundaries2016.

Runtime is unchanged, so full roster/GPU/Godot/Web export were not rerun
(historical full runtime:r20; Web:r21). Production components were not remeasured:
9/54 baseline; color3/5,order2/4,matrix20/24,rush234/5103 RGB channels differ.
Exact production pixels and full AS/clip-action ownership proof still block
merge. Placement34/34 clearance remains unchanged. No merge/deploy/Worker.
