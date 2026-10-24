# r29: repeat translation and pixel-step coefficients are distinct

**Draft / not merge-ready. Diagnostic candidate only; no production wiring.**
No runtime, generated data, locked input, clipped candidate, existing native
reference, tolerance or allowlist changed.

## Independent native observations

Three packaged probes use Flash Player Debugger32.0.0.465 under Rosetta:

- `bitmap-repeat-coefficients.as`:1200 RGB responses,300 four-corner groups.
  Identity fill matrix, exact integer negative draw translations, fixed target
  pixel(4,4); sweep X and Y separately over15 positive source origins through16383.
- `bitmap-repeat-pixel-step.as`:960 responses,240 four-corner groups. Zero draw
  translation; move destination pixel instead, through origin2047. This separates
  the pixel-step coefficient from the inverse-translation coefficient.
- `bitmap-repeat-negative-grid.as`:168 responses around negative source positions
  -.5/-1/-1.5, with scale8 perturbed by±1/4096,±4/4096,±16/4096.

The positive probes use unique4x4 edge texels in green, corner impulses in red,
and constant blue113. Scales1.3 and6.25 are independent held-out controls in
addition to1.01/1.7/2.5/3/5/7.99/8/13.3. Fractional fill-matrix routing remains a
separate unresolved composition control fromr28.

## Interval inference, not RGB-dependent path selection

All540 four-corner signatures uniquely recover a byte-coordinate modulo4 under
the byte-weight interpolation family. The orthogonal coordinate is held at16/256.
Each response bounds the variable coordinate to a half-open interval of width1/256.
Pairwise intersection yields open slope intervals for an affine initializer.
`comparison.json` contains every coordinate interval, slope bound and input hash.

Unwrapping explicitly assumes the nearest ideal source period: repeated RGB cannot
prove absolute period. The interval inference is conditional on the interpolation
family; it does not prove Flash implementation internals.

Both axes agree. All translation intervals contain `(1+1/262144)/scale`;
all pixel-step intervals contain
`(1+1/262144)*round(65536/scale)/65536`, including both held-out scales.
These are different coefficients. At scale1.7, for example:

- translation:(0.5882374899727958,0.5882377624511719);
- pixel step:(0.5882432725694444,0.5882457386363636).

The intervals do not uniquely distinguish `1+1/262144` from nearby reciprocal
normalizations. The4-texel period times65536 motivates testing a common period
normalization; it is not a proof of its exact denominator.

## Uniform candidate and remaining counterexamples

Reuse the unchanged r27 fixed-point coordinates `v`, then apply on each axis:

```
v_normalized = v * (1 + 1 / (bitmap_size * 65536))
byte_coordinate = (trunc(256*v_normalized) - int(v_normalized < 0)) / 256
```

This is diagnostic only. No coordinate-specific fixes or interpolation choices
based on observed RGB are used. Scalar captures use byte weights throughout;
the old distant suite retains its previous whole-suite separable hypothesis.

| Suite | r28 | r29 candidate | Remaining | Max channel delta |
|---|---:|---:|---:|---:|
| Existing single-pixel repeat |862/1008|**1008/1008**|0|0|
| Existing distant repeat |513/1008|**571/1008**|437|2|
| New draw-translation controls |—|1196/1200|4|1|
| New pixel-step controls |—|960/960|0|0|

The four new scalar counterexamples are scale3/origin15:
X-axis corners0/2 and Y-axis corners0/1. Native impulse responses238/16 become
239/15; the unique edge green61 and constant blue113 are unchanged. Thus even
scalar initialization is not universally solved. Do not attribute all437 distant
failures to bulk partition before resolving this scalar counterexample.

Negative-grid controls: floor126/168; r28 signed conversion168/168; subtracting
one16.16 unit from negative coordinates before flooring also168/168. Under the
assumed16.16 coordinate grid those latter operations are observationally
indistinguishable at byte resolution. This probe does not settle signed truncation
versus a tiny negative bias. Both hypotheses remain documented, not production rules.

## Next discriminating experiment

At scale3 with exact integer draw translation, sweep origins14/15/16 and target
pixels3/4/5 independently using the same four-corner4x4 source. Repeat at source
widths2/8/16, retaining unique edge values. This distinguishes normalization of
unrounded inverse translation from normalization after fixed-point rounding, and
constrains whether the period denominator is `N*65536` or `N*65536-1`.
Require one initializer to retain all old scalar and held-out controls. Only then
capture continuous short spans around wrap boundaries to infer bulk partition.
Do not select a path by whichever formula matches a pixel.

## Reproduction and acceptance

Build/capture each fixture with `build_flash_filter_probe.py --case NAME` and
`capture_native_player.py`, as inr28. The three capture directories retain raw
traces, source/SWF hashes and native environment. Then:

```sh
python3 tools/probes/analyze_bitmap_repeat_coefficients.py --output /tmp/r29-comparison.json
# Required exit1: candidate is still inexact; also runs every clipped regression.
python3 -m unittest tools.tests.test_bitmap_repeat_coefficients
```

Fresh acceptance is recorded in `acceptance.json` and `checks/`. All clipped
regressions remain exact: base1536,extended4096,single1008,distant1008,scan6048,
widths24080,axes4032,origins1632,boundaries2016. Caches remain26/26.

Runtime is unchanged; full roster/GPU/Web export were not rerun (historical full
runtime:r20; Web:r21). Components were not remeasured:9/54 baseline; color3/5,
order2/4,matrix20/24,rush234/5103 differing RGB channels. Production pixel parity
and full AS/clip-action ownership proof still block merge. Placement34/34 remains
cleared. No merge, deployment or Worker change.
