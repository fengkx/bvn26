# r23: exact r22 bitmap phases; independent scanline counterexamples remain

Draft PR #48 is **not merge-ready**. No production sampler was installed.
No runtime, generated content, original reference trace, tolerance or allowlist changed.

## Result

| Native probe | r22 candidate | r23 candidate | Admission |
|---|---:|---:|---|
| Original bitmap phases | 1536/1536 | 1536/1536 | CPU diagnostic only |
| Non-power-of-two / negative two-axis phases | 3393/4096 | **4096/4096** | CPU diagnostic only |
| Independent large clipped bitmap, sparse distant points | — | **965/1008** | Rejected:43 failures,max2 |
| Independent repeated bitmap, sparse distant points | — | **509/1008** | Rejected:499 failures,max3 |
| Independent continuous clipped scanlines | — | **6008/6048** | Rejected:40 failures,max2 |
| Same near-origin coordinates across six bitmap sizes | — | **240/240** |40/40 size-control groups identical |

These are native-vs-CPU arithmetic measurements, **not Godot rendering parity**.
Closing the old4096 suite alone would have admitted an incorrect shared sampler.
The independent captures are therefore retained as mandatory counterexamples.

## What the experiments establish, and what is still a hypothesis

1. Quantizing the inverse scale before calculating source coordinates closes all
   703 r22 differences. The old small probes cannot distinguish floor from nearest
   rounding of the inverse or identify its precision. Distant points at scales1.7
   and13.3 provide additional evidence favoring nearest16.16 over floor16.16.
   This is a candidate arithmetic model, not a claim of recovered Flash internals.
2. The candidate retains observed quarter-screen-pixel translation phases and
   byte source-coordinate fractions. Its near-border path uses three truncated
   byte bilinear weights and assigns their residual to the fourth.
3. The distant clipped samples mostly fit a different candidate: vertical integer
   interpolation first, then horizontal interpolation, truncating after each.
   Selecting the byte-weight hypothesis when either source index is at/before
   the first texel, and the two-stage hypothesis elsewhere, gives965/1008.
   **That selection condition is not proven and is not production code.**
4. Repeated2x2 and clipped1024x1024 images with the same tiled color contents
   differ at566/1008 measured native positions. Mode cannot be discarded when
   deriving a sampler. A separate same-coordinate control across bitmap sizes
   2/4/8/16/64/1024 is identical40/40, ruling out bitmap size alone as the cause.
5. Continuous rows expose residual differences near some scan segment boundaries
   and final pixels. Neither a global bias nor accepting +/-1 is justified.
   No x-specific correction was added.

All four new fixtures use smooth bitmap fills, the same RGBA basis pixels, and
alpha255/128 (the continuous row uses255). Each source bitmap is created in the
native harness; large versions tile the same2x2 basis via copyPixels. Captures
include source AS hash, SWF hash, run identity, ordered samples and completion.
`analyze_bitmap_inverse.py` rejects incomplete, mixed-run, duplicated or
misidentified captures; any channel mismatch exits1. Neither analyzer can admit
production support. The r22 native files were reused unchanged, with hashes in
`reference-hashes.json`.

## Precise remaining continuous-row list

All observations below use destination y=155, x=16..519, with translation
(x=phase/256,y=-phase/512). Each row contains504 samples. Full native/candidate RGB
and per-point deltas are retained in `row-comparison.json`.

| Scale | Phase | Exact/504 | Remaining destination x |
|---:|---:|---:|---|
|1.01|-224|499|237,253,254,255,493|
|1.01|0|500|220,254,255,476|
|1.01|224|496|203,254,255,256,459,517,518,519|
|2.5|-224|499|128,255,256,384,512|
|2.5|0|504|none|
|2.5|224|501|517,518,519|
|5|-224|501|255,256,512|
|5|0|502|258,514|
|5|224|498|256,260,516,517,518,519|
|8|-224|503|255|
|8|0|504|none|
|8|224|501|517,518,519|

Next discriminating experiment: vary destination width and clip origin while
keeping source texel coordinates fixed; emit dense samples around each moved
span end. Compare coordinate initialization/stepping and scalar vs bulk arithmetic
hypotheses, without assuming a fixed x=255 special case. Also cover affine
rotation, negative scales, transparent edges and source smoothing flags before
admitting a shared sampler to production.

## Production parity and acceptance

Production runtime/generated files remain byte-identical to eaa61af4; see
`runtime-preservation.json`. Consequently, **no improvement to production images
is claimed**. The r22 measurements remain the current baseline and were not
re-rendered this turn:

- components9/54; clocks4242/4242;
- color3/5, order2/4, scalar ColorMatrix20/24;
- rush21/21 entered frames,234/5103 differing RGB channels.

Fresh acceptance counts are in `acceptance.json`: Python, focused analyzer tests,
26 cached fighters / online manifest,8 fingerprint tests, protected-function,
integrity, handoff and contracts. Full roster/GPU acceptance and build_web were
not rerun because production runtime did not change. Last full runtime suite:r20;
last full Web build:r21. These are historical successes, not r23 runs.

Merge blockers remain exact production component/color/order/matrix/rush pixels
and full AS/clip-action ownership proof. No new placement admission or AS owner
mapping was added; placements remain34/34 cleared. No merge/deploy/Worker changes.

## Reproduction

```sh
python3 tools/probes/analyze_bitmap_phase.py --extended \
  --native-log evidence/importer-loud-fail/r22/bitmap-phase-extended/native.log \
  --output "$OUT/extended.json"
# 4096/4096, exit0; still diagnostic only.
python3 tools/probes/build_flash_filter_probe.py --case bitmap-row \
  --output "$OUT/row" --ffdec "$FFDEC"
python3 tools/probes/capture_native_player.py "$OUT/row" "$OUT/row/native.log" \
  --player-app "$FLASH_APP" --allow-window-activation --timeout 50
python3 tools/probes/analyze_bitmap_inverse.py --kind row \
  --native-log "$OUT/row/native.log" --output "$OUT/row-comparison.json"
# 6008/6048, exit1 REQUIRED. No channel tolerance.
# Other fixture/kind pairs: bitmap-inverse/repeat,
# bitmap-inverse-clipped/clipped, bitmap-size/size.
python3 -m unittest tools.tests.test_bitmap_phase_analysis tools.tests.test_bitmap_inverse_analysis
```
