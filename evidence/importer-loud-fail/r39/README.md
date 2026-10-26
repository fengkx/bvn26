# r39 — independent long-row CXFORM arithmetic (not admitted)

Production and GPU diagnostics are unchanged. `production_admitted=false`.
The new CPU hypothesis still exits **1**: independent row controls pass but
held-out native filter buffers reject it. No epsilon, tolerance, allowlist,
reference modification or RGB-dependent choice of arithmetic was introduced.

## Independent capture and arithmetic

`cxform-row-controls.as` captures 810 cases: ramp/impulse channels,
alpha{7,135,231}, opacity{25,50,100}, clipped width{15,16,17,19,20},
clip start{4,5,7}, and independent integer draw translation{-3,0,1}.
Every destination pixel records both source and result, each as transparent
and opaque-black readbacks. Source values, event order, completion and source
hash are validated. There are 14094 active pixels plus 11826 clear pixels.

The tested geometry-only partition is: width below16 uses the existing scalar
path; otherwise the first `floor(width/4)*4` pixels use the long-row path and
the remainder use scalar. Coordinates are relative to the clipped row start,
not to source texels or global destination alignment. This explains the tested
width/start/translation controls; it is not a proof for arbitrary row extents.
No partition is selected by whichever formula matches an output pixel.

The long-row hypothesis uses independently measured reciprocal estimates:
`tools/probes/cxform_reciprocal.c` records x86 reciprocal-estimate float bits for
all integer alpha1..255. This is an arithmetic comparator, **not evidence that
Flash executes that instruction or uses SIMD**. The table was measured from
the helper, not fitted from Flash pixels. Float32 operation order per channel:

```
s = f32(premult_byte * measured_reciprocal[alpha])
t = f32(f32(s * multiplier) + f32(offset / 255))
rgb = trunc(f32(f32(clamp(t, 0, 1) * alpha) * f32(opacity / 100)))
alpha_out = alpha * floor(opacity * 256 / 100) // 256
```

The RGB transform remains the independent probe's (.5,.75,1)/(8,0,-4).
Zero alpha returns zero. Scalar arithmetic is unchanged from r38.
Using correctly rounded float32 `1/alpha` in the same sequence is a negative
control: **299 green-channel errors**, max1. For alpha135/premult green104,
this sequence explains the native77 boundary that real arithmetic gives78.
Ordinary normalized/byte-space operation orders also fail the new controls;
no such approximate model is admitted.

## Results and counterexample

`arithmetic.json` contains every remaining coordinate and actual/native RGBA.

| Comparison | Exact / total |
|---|---:|
| New native row pixels (including clear clip exterior) | 25920/25920 |
| Active long prefix | 11016/11016 |
| Active scalar/tail | 3078/3078 |
| Existing all-alpha scalar controls | 3072/3072 |
| Held-out r38 constant spans | 8652/8652 |
| Held-out r38 alternating spans | 8652/8652 |
| Held-out native filter boundary composition | **43006/43200** |
| Exact-reciprocal negative control | 25621/25920 |

The last comparison consumes **pinned native filter outputs**, then predicts
parent-input and final composition in CPU. It does not rerender or replace those
buffers, and cannot count as GPU filter parity. All194 errors are final-layer
nonidentity CXFORM, green channel off by1; alpha is exact. For example case3,
final(x9,y7), source parent-filter RGBA[66,108,121,146]: candidate
[37,80,118,146], native[37,81,118,146]. Other failing source alpha values include
132,133,134,197,206,210,229,244. They were not in the three-alpha long-row
training control. Thus the independent long-row hypothesis is still incomplete;
no GPU shader or production binding was changed.

Next experiment: independently capture all-alpha long rows around these source
bytes, with explicit input readback, then compare reciprocal precision and
multiply/round ordering without changing the geometry selector. Preserve the
current three-alpha controls and held-out constant/alternating rows. Also test
row lengths beyond33 and clipped source-boundary intersections before claiming
a general partition. Only a model that clears the native-buffer counterexamples
may advance to the full72576 GPU nested-filter gate.

## Reproduction

```sh
python3 tools/probes/build_flash_filter_probe.py --case cxform-row-controls \
  --output "$SCRATCH/native" --ffdec "$FFDEC"
python3 tools/probes/capture_native_player.py "$SCRATCH/native" "$SCRATCH/native/native.log" \
  --player-app "$PLAYER" --allow-window-activation --timeout 55
clang -arch x86_64 -O2 tools/probes/cxform_reciprocal.c -o "$SCRATCH/reciprocal"
arch -x86_64 "$SCRATCH/reciprocal" > "$SCRATCH/reciprocal.txt"
python3 -m tools.probes.analyze_cxform_rows \
  --root evidence/importer-loud-fail/r39 --output "$SCRATCH/arithmetic.json"
# Expected exit1: held-out native filter boundaries reject the hypothesis.
python3 -m unittest tools.tests.test_cxform_rows
```

## Admission / remaining blockers

Fresh regressions: r36 GPU4032/4032 and complete Yulong4/4; r37 nested
124416/124416; leaf6/6 (69120 pixels); isolated Glow4/4; GPU sampler
71824/71824; CPU sampler suites exact. Python584 pass+2skip. Caches26/26,
fingerprint8/8, protected, integrity, handoff and contracts pass. Commands
and results are recorded in `checks/` and `acceptance.json`. The unchanged GPU nested filter result remains r38's
67774/72576; it is not improved by this CPU analysis. Production54 remains
historical9/54, not remeasured. General coverage/affine/PNG alpha, dynamic nested
filter bounds/lifetimes, other component/color/order/matrix/rush parity, and full
AS/clip-action ownership remain unproven. Draft is not merge-ready. No production
runtime/assets changed, so full roster/Web export was not rerun this round.
