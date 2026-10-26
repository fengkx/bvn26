# r41 — reciprocal feasibility intervals, no admissible common construction

Production and GPU code are unchanged. `candidate_admitted=false`,
`gpu_advance_allowed=false`, `production_admitted=false`. Analysis exits **1**.
The new evidence constrains the arithmetic; it does not supply an implementation.
No inferred interval endpoint is used to render a pixel or build a lookup table.

## Explicit native rows

`cxform-residual-intervals.as` uses46 alphas: the45 failing r40 normalized-alpha
values, plus the retained7/93/135/231 controls (overlap removed). Width32 keeps the
existing long-row selector constant. There are five green multipliers
{191,192,193,255,257}/256, offsets{−1,0,1,7}, and opacity{33,67,100}.
Each of2760 rows contains32 pixels, **88320 pixels** total.

Green inputs target integer products at multiples of4, capped at the source
alpha. The probe explicitly reads back every input and output, both transparent
and drawn on black. This verifies the exact residual premultiplied inputs:

- alpha14 / green12: **[5,12,13,14]**,60 observations;
- alpha135 / green108: **[62,108,127,135]**,60 observations.

Red/blue transforms stay .5/+8 and1/−4; their source bytes are preserved and
included in the combined constraints. The capture is complete and source-hash
pinned; `native.log.gz` is a lossless archive of the original log with both raw
and compressed hashes. No earlier native reference was modified.

## Interval method

The analyzer tests three coordinate spaces (unit, normalized, byte) and three
multiplication orders (alpha first, opacity first, combined alpha/opacity).
Every multiplication/addition is explicitly rounded to binary32, followed by
clamp and truncation. Opacity uses the previously measured8.8 source value.
Nonnegative source channels and positive multipliers make these sequences
monotone in the nonnegative finite float32 reciprocal coefficient.

For **each native constraint**, binary search over the entire nonnegative finite
float32 domain finds the first coefficient producing at least the native byte
and the first producing the next byte. Their difference gives a closed interval
of coefficients producing exactly that byte. Intersect all intervals for an
alpha; record the actual native sample imposing each lower and upper bound.
No epsilon, real-number approximation, tolerance, or RGB-selected operation is
used. Tests validate the bound witnesses against the original captures and
recompute the exact bit endpoints.

The nine green-only models each have46 nonempty intersections. The three
alpha-first space models also retain255 nonempty intersections after including
all RGB channels from these new rows and the r40 all-alpha/nonbinary-opacity
captures: **436320 constraints** per model. Nonempty intervals mean the selected
sequence is not yet disproved if an unknown reciprocal were allowed. They do
**not** identify one common construction, and do not authorize choosing a
coefficient independently for each alpha.

Example unit/alpha-first combined intervals (inclusive float32 bit patterns):

| Alpha | Lower | Upper |
|---|---|---|
| 14 | 0x3d922fff | 0x3d924890 |
| 67 | 0x3c7479d6 | 0x3c747d08 |
| 95 | 0x3c2c7418 | 0x3c2c75e3 |
| 135 | 0x3bf2b0ab | 0x3bf2b2f4 |
| 231 | 0x3b8dd4a8 | 0x3b8dd5ff |

For example, alpha135's lower witness is native row2012/x30, green124,
multiplier193/256, offset1, opacity100, native94. Its upper witness is
row2036/x30, multiplier257/256, offset1, opacity100, native124.
`intervals.json.gz` includes every bound and witness, not just these examples.

## Independent coefficient measurements

`cxform_reciprocal_constructions.c` independently computes seven common formulas
for all nonzero alphas. `E` below denotes the measured reciprocal estimate and
`f` float32 rounding; no native pixels enter this helper:

1. `f(1/a)`;
2. `E(a)`;
3. `f(E(f(a*255))*255)`;
4. `f(E(f(a/255))/255)`;
5. `f(f(1/f(a*255))*255)`;
6. scalar estimate of `a` (independently measured; same bits as packed estimate);
7. `k=E(255); f(E(f(a*k))*k)`.

Source/executable/output hashes, compiler and commands are pinned in
`reciprocal-environment.json`. These are independent mathematical comparators,
**not evidence that Flash uses SIMD, any specific instruction, or this helper's
coefficient table**. Normalized/byte models convert these common coefficients
to their255/a units using float32 multiplication.

None fits all combined intervals. Unit/alpha-first fits respectively
**51,115,128,208,48,115,181 of255 alphas**. The best count in either other space
is209/255, still rejected. Correctly rounded1/a fits **0/46** new green-only
intersections. Multiplying all exact reciprocals by a common gain is also not
supported by the observed intervals: coefficient×alpha requires at least
0.999943949 at alpha95 but at most0.999799989 at alpha67 in the unit model.
This is a rejection constraint, not a proposal to insert a bias.

## Operation-order discrimination and remaining blocker

Nonzero offsets now separate one previously coincident case. Native row1525/x15:
alpha87, premult green64, multiplier193/256, offset−1, opacity67 gives **31**.
With the independently measured `E(87)`, unit alpha-first gives31 and
opacity-first gives32. Across all new green channels, the former is
**88087/88320**, the latter88086/88320. The alpha-first comparator still has
**233 counterexamples**. Normalized alpha-first gives86015/88320; byte
opacity-first gives86016/88320. Full counts and every failing coordinate are
retained. This one separating observation cannot select a globally correct
sequence; each tested sequence still permits a range of unknown coefficients.

All common constructions fail before the held-out native-buffer gate can be
cleared. Old native-buffer scores remain r39 **43006/43200** and rejected r40
normalized **43176/43200**. No coefficient inferred from these intervals is
substituted into either comparison. The full72576 GPU nested-filter gate is
therefore **not advanced**; its unchanged r38 score remains67774/72576.

Next discriminating experiment: test a green identity channel (multiplier1,
offset0) while red/blue keep the enclosing transform nonidentity, together with
adjacent255/256 and257/256 multipliers. Read back the same explicit source bytes
and compare within the current coefficient intervals. This can distinguish
channel-specific identity treatment from reciprocal multiplication, without
changing row routing. If needed, materialize separate multiplier-only and
offset-only native operations and retain their intermediate bytes; do not assume
two materialized operations are equivalent to one combined transform. Reject
any proposed common construction against **all** interval sets and old exact
controls before further GPU work.

## Reproduction and regression status

```sh
python3 tools/probes/build_flash_filter_probe.py --case cxform-residual-intervals \
  --output "$SCRATCH/native" --ffdec "$FFDEC"
python3 tools/probes/capture_native_player.py "$SCRATCH/native" "$SCRATCH/native/native.log" \
  --player-app "$PLAYER" --allow-window-activation --timeout 55
clang -arch x86_64 -O2 -ffp-contract=off tools/probes/cxform_reciprocal_constructions.c \
  -o "$SCRATCH/reciprocal"
arch -x86_64 "$SCRATCH/reciprocal" > "$SCRATCH/reciprocal.txt"
python3 -m tools.probes.analyze_cxform_intervals \
  --root evidence/importer-loud-fail/r41 --output "$SCRATCH/intervals.json.gz"
# Expected exit1; gzip -dc exposes all witnesses and strict counterexamples.
python3 -m unittest tools.tests.test_cxform_intervals
```

Fresh prior exact regressions: scalar3072/3072; three-alpha25920/25920;
constant/alternating spans8652/8652 each; r36 composition4032/4032 plus complete
Yulong4/4; r37 nested124416/124416; leaf6/6 (69120 pixels); isolated Glow4/4;
GPU sampler71824/71824; CPU sampler suites exact. Commands/provenance and
repository acceptance are under `checks/` and `acceptance.json`. Python591 pass
+2skip; caches26/26, fingerprint8/8, PROTECTED_FUNCTION_OK, integrity, handoff
and contracts pass.

Production54 remains historical9/54, not remeasured. Full roster/Web export
are not rerun because production runtime/assets are unchanged. General image
parity and full AS/clip-action ownership remain merge blockers. No allowlist,
stability exception, production enable, merge, deployment or Worker change.
PR remains Draft, not merge-ready.
