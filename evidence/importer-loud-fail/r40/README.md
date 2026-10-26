# r40 — all-alpha CXFORM and independent row extents (rejected)

No production or GPU code changed. `production_admitted=false`,
`gpu_advance_allowed=false`. The analysis command exits **1**. Neither a local
improvement nor source-intersection observations admit an implementation.

## Native experiment

All captures use explicit input/result transparent and black readbacks. Inputs,
source hashes, event identities, payload lengths, ordering and completion are
validated. Compressed original logs are lossless; `trace-sha256.json` pins both
raw and compressed bytes. No reference was rewritten.

- `alpha/`: every alpha0..255, opacity25/50/100, width32. The32 straight green
  bytes span neighborhoods around the r39 failing filter inputs (listed in the
  checked-in probe). Red70/blue236 remain constant. **768 rows /24576 pixels**.
- `opacity/`: the same input pattern and all alphas, opacity1/33/67/99.
  **1024 rows /32768 pixels**. These controls avoid relying only on binary-exact
  .25/.5/1 when comparing multiplication order.
- `extents/`: widths34,35,47,63,64,65,127,128,129,255,256,257,511,512,513;
  clip starts0/3; independent source translations−590/−15/0/11/590;
  alpha135/197, opacity50/100; source600x1 and destination640x1.
  **600 rows /384000 pixels**, including transparent exterior. Trace payloads
  are chunked in32-pixel records; the native draw is one whole row, not chunks.

The last set includes left/right source-boundary intersections, long interior
spans, tails and fully nonintersecting draws. No affine/fractional coverage or
arbitrary nested-layer eligibility is inferred from these integer rectangles.

## Arithmetic comparison — one rule for every pixel in each candidate

`cxform_reciprocal_precision.c` independently records float32 reciprocal
estimates for alpha, alpha/255 and alpha*(1/255). Command/compiler/source/binary/
output hashes are in `reciprocal-environment.json`. The original alpha estimates
are byte-identical to r39. This is a comparator, **not evidence that Flash uses
these instructions, SIMD, or this table**.

Every arithmetic comparator keeps r39's selector unchanged: width<16 scalar;
otherwise long prefix `floor(width/4)*4`, then scalar tail. No choice depends on
RGB, expected output, or whichever model matches a pixel. The scalar model is
unchanged. Alternatives compare correctly rounded vs estimated reciprocal,
byte vs normalized intermediates, division vs multiplication by1/255, and
premultiplication/opacity order; each float32 operation is explicitly rounded.

| All-alpha width32 comparator | Exact /24576 |
|---|---:|
| Unchanged r39 reciprocal estimate | 23288 |
| Correctly rounded1/alpha, otherwise same | 22181 |
| Normalized reciprocal estimate | 23902 |
| Byte-space correctly rounded255/alpha | 22165 |

Normalized comparator, per channel (f denotes float32 rounding):

```
a_unit = f(alpha / 255)
c_unit = f(channel / 255)
s = f(c_unit * measured_reciprocal_estimate(a_unit))
t = f(f(s * multiplier) + f(offset / 255))
p = f(clamp(t, 0, 1) * a_unit)
rgb = trunc(f(f(p * 255) * opacity))
```

Multiplier/offset stay(.5,.75,1)/(8,0,−4). Using normalized multiplication instead
of division, or moving opacity before the final255 multiplication, does not
separate the measured outputs. Neither does the tested byte-space rearrangement
of the estimated reciprocal. Thus these observations do **not** uniquely identify
operation order. No epsilon, fitted per-alpha coefficients, tolerance or formula
selection has been introduced.

For opacity1/33/67/99, the normalized estimate scores22167/32768 using unquantized
opacity, versus32610/32768 using `floor(opacity*256/100)/256`. Alpha readbacks
match the8.8 alpha calculation throughout, but158 RGB counterexamples remain.
The unchanged r39 arithmetic with that same source-opacity quantization scores
32466/32768. All tested permutations and exact maximum channel differences are
in `summary.json`; complete remaining coordinates are in `analysis.json.gz`.
The tested multiply orders still do not separate these controls; do not claim a
unique order from their agreement.

## Held-out failure prevents GPU advancement

The normalized comparator reduces the pinned native-buffer boundary errors
from194 to24 (**43176/43200**, maximum green delta1), but it **regresses** the
previous exact controls:

| Existing capture | Unchanged r39 | Normalized alternative |
|---|---:|---:|
| Three-alpha rows | 25920/25920 | 24239/25920 |
| Constant spans | 8652/8652 | 7812/8652 |
| Alternating spans | 8652/8652 | 7602/8652 |

The24 remaining boundary failures use source premultiplied RGBA
[62,108,127,135] or[5,12,13,14]. Example: case7 final(x5,y5) predicts
[35,81,124,135], native[35,80,124,135]. All-alpha normalized failures include
alpha6, green input4: candidate3 vs native2 after multiplier. There are674
all-alpha failures across45 alpha values. The unchanged r39 model remains
43006/43200 on native buffers. These are CPU comparisons consuming pinned native
filter outputs, **not new GPU image counts**.

The original all-alpha scalar3072/3072 and every old exact suite remain intact.
Do not combine the two rejected reciprocal models by alpha/color or credit the
24-error local improvement as admission. Full72576 GPU nested-filter execution
is deliberately not advanced; the unchanged r38 result remains67774/72576.

## Independent geometry result

For alpha135, the unchanged request-width selector gives191860/192000 on the
new extent suite. A separate diagnostic passes the geometric intersection of
source rectangle, destination bounds and clip rectangle to the **same** selector:
**192000/192000**. This accounts for all140 errors without consulting RGB.
For example, source translation−590 intersects only10 pixels of a requested
width34 row; native uses the scalar result at x6/7. Treating all34 pixels as a
long span incorrectly gives green38 rather than39 at opacity50.

The alpha197 intersection control still fails (**185436/192000**, max green1),
consistent with the independently exposed arithmetic limitation. Thus source
intersection matters, but this is only an isolated geometry control, not a
replacement of the r39 selector or a proof for general rendering. No arbitrary
work-chunk partition or SIMD inference is justified by these results.

## Next discriminating experiment / remaining gate

The data now separate source-boundary clipping from unresolved reciprocal/
rounding arithmetic. Use explicit native rows containing the two residual filter
inputs and integer-product green channels at the failing alpha values, retaining
the successful old controls. Derive intervals for one common reciprocal
construction and operation sequence from these inputs; compare independent
coefficient measurements rather than selecting a fitted coefficient per alpha.
If operation orders still coincide, add intermediate readbacks or deliberately
nonzero green offsets/multipliers near the distinguishing rounding boundaries.
Do not move to GPU until one model passes all these controls and all pinned
native-buffer boundaries simultaneously.

## Reproduction

```sh
# Repeat for cxform-alpha-rows, cxform-alpha-opacity, cxform-row-extents.
python3 tools/probes/build_flash_filter_probe.py --case cxform-alpha-rows \
  --output "$SCRATCH/alpha" --ffdec "$FFDEC"
python3 tools/probes/capture_native_player.py "$SCRATCH/alpha" "$SCRATCH/alpha/native.log" \
  --player-app "$PLAYER" --allow-window-activation --timeout 55
clang -arch x86_64 -O2 -ffp-contract=off tools/probes/cxform_reciprocal_precision.c \
  -o "$SCRATCH/reciprocal"
arch -x86_64 "$SCRATCH/reciprocal" > "$SCRATCH/reciprocal.txt"
python3 -m tools.probes.analyze_cxform_alpha \
  --root evidence/importer-loud-fail/r40 --output "$SCRATCH/analysis.json.gz"
# Expected exit1. gzip -dc prints the complete per-coordinate counterexamples.
python3 -m unittest tools.tests.test_cxform_alpha
```

## Regression / release status

Fresh r36 ordinary composition4032/4032 plus complete Yulong4/4; r37 nested
124416/124416; leaf6/6 (69120 RGBA); isolatedGlow4/4; GPU sampler71824/71824;
CPU sampler suites exact. Python587 pass+2skip; caches26/26, fingerprint8/8,
PROTECTED_FUNCTION_OK, integrity, handoff and contracts pass. Commands are recorded under
`checks/` and `acceptance.json`. Production component count stays historical9/54,
not remeasured. Full roster and Web export are not rerun because production code
and assets are unchanged. General image parity and AS/clip-action ownership
remain separate merge blockers. No production enable, allowlist, stability
exception, merge, deployment or Worker change. PR remains Draft.
