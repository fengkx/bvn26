# r38: actual nested filters; final CXFORM still rejects

**Not admitted.** The opt-in integer diagnostic matches **67774/72576 RGBA
pixels**. Every child input/filter and parent input/filter pixel is exact, but
24 final images with nonidentity RGB CXFORM still differ: **4802 pixels, maximum
RGB delta2**, alpha exact. No production runtime, assets, references or tolerances
changed. `production_admitted=false`; Draft PR48 is not merge-ready.

## Explicit native filter boundaries and actual production allocation

`nested-filter-composition.as` allocates independent BitmapData objects for:

- child input12x12: partial-alpha8x8 and overlapping4x4 sources, padding2;
- child filtered12x12: applyFilter into a fresh bitmap;
- parent input18x18: alpha128 middle16x16, then the completed child filtered
  bitmap with child opacity and optional RGB CXFORM;
- parent filtered18x18: applyFilter into another fresh bitmap, padding1;
- final24x24: independent background, completed parent filtered bitmap with
  parent opacity/CXFORM, then a later overlapping sentinel.

No `cacheAsBitmap` materialization inference. Source colors are independently
read back; native black readback provides premultiplied RGB, transparent readback
provides alpha. Each capture has strict identities, row coordinates and completion.

48 combinations: two filter orders × destination alpha{0,128,255} × child opacity
{25,100}% × parent opacity{50,100}% × identity/nonidentity RGB CXFORM.
The filter orders are outer Glow5 then Blur3, or Blur5 then outer Glow3; each is
one pass per axis, strength1, Glow alpha1, no knockout/inner mode. Glow colors
are 0x51d3ef / 0x5de1f4. Nonidentity CXFORM uses RGB multipliers(0.5,0.75,1),
byte offsets(8,0,-4), with alpha opacity independently applied at each boundary.

`nested_filter_preview.gd` inherits TimelinePreview. The unchanged production
`_compose_blend_group` allocates **actual filter_group.gd** nodes, their Contents
SubViewports, filter passes and Composite textures. The child lives inside the
parent Contents. Readbacks verify child12x12 (parent-buffer origin3,3), parent18x18
(final origin1,1), and every filter pass's size/count. The surrounding middle
rectangle contains the child's filter extent; tight enclosing bounds are not
claimed proven. Allocation, padding and actual filter shader are not replaced.

The diagnostic override binds integer destination-copy composition and reads the
actual post_mul/post_add/group_opacity from the production composite material.
It is never instantiated by gameplay. Integer-aligned coverage, no arbitrary
transform, scaling or PNG decode is introduced in this synthetic buffer proof.

Source-first: the checked-in native frame1 allocates, draws, filters and reads
fresh buffers synchronously, then stops/quits. No timeline MOVE, enterFrame or
label-exit behavior is assumed. This proves the explicit synthetic operations,
not new BVN source ownership; locked game/ and scripts/ remain untouched.

## Measurements and rejected candidates

| Stage, 48 cases | Initial continuous CXFORM | Fixed reciprocal candidate |
|---|---:|---:|
| Child input | 6912/6912 | 6912/6912 |
| Child filter | 6912/6912 | 6912/6912 |
| Parent input | 13080/15552 | 15552/15552 |
| Parent filter | 12504/15552 | 15552/15552 |
| Final | 24854/27648 | 22846/27648 |
| All pixels | **64262/72576** | **67774/72576** |

The identity-CXFORM subset is **24/24 complete images exact** with either
candidate. In the nonidentity subset, the initial production-style floating
straight-RGB transform fails all24 final images (max delta1). The fixed candidate
makes all intermediate buffers exact, but still fails all24 final images and
regresses some final channels to delta2. This is **not** an acceptable replacement
or a claim of net production parity. No mixed per-pixel path is selected.

`render/` retains the initial continuous diagnostic, its full per-coordinate
comparison and exact shader snapshot. `integer/` retains the current fixed
candidate and its full per-coordinate failures. `inventory.json` and
`integer-inventory.json` summarize by filter order, CXFORM and stage. Original
native images/traces are unchanged; no reference regeneration to match output.

The initial byte hypothesis (exact integer division by alpha, truncate RGB
transform, transform alpha before premultiplication) matched scalar96/96 but
only3144/3456 child-placement observations; it remains rejected in
`cx-analysis.json`. Failures at alpha93/135/231 exposed reciprocal quantization.

The fixed candidate truncates `65280/alpha` before unpremultiplication, then
truncates the8.8 RGB multiply, applies byte offsets/clamp, transforms alpha and
premultiplies by `(new_alpha+1)/256`. It is exact for the child placement and
independent **3072/3072** scalar controls covering all256 alpha values, four
source colors and opacities25/50/100. However scalar success does not establish
long-row semantics.

Independent width/origin controls deliberately hold source operands fixed while
varying width{1,3,4,7,8,12,15,16,17,18,31,32,33} and destination origin{0,1,3},
with four alphas and three opacities. Both constant-color and alternating-color
sources are captured, **468 cases each**:

- Universal fixed candidate: constant **5292/8652** pixels exact;
- alternating colors: **5922/8652** pixels exact;
- observed differences first appear at width16, not at widths1–15, and recur
  through long-row prefixes; matching tail pixels alone do not establish a
  general partition rule.

For example, alpha7/opacity25, constant color0x46c4ec: a width1 row yields
`[0,1,1,1]`, while the first pixel at width16 yields `[0,0,1,1]`, with the same
source bytes and destination origin. Thus a universal scalar CXFORM is disproved
without choosing whichever formula matches a pixel. A direct rational
premultiplied transform also leaves independent and nested counterexamples;
no bulk implementation or RGB-dependent selector is admitted.

## Precise remaining blocker / next experiment

The same input bytes do not imply the same CXFORM result when only row width
changes. Derive the long-row arithmetic and partition independently before
altering the diagnostic further, preserving scalar3072 controls and native filter
buffers. Use ramp/impulse channels near exact integer products (e.g. alpha135,
green104, multiplier0.75: the long-row native result at opacity100 is77, whereas
exact real arithmetic gives78). Sweep width15/16/17/19/20 and clip start/end;
separate fixed reciprocal/truncation from float32 reciprocal/multiply ordering.
Do not add epsilon or infer SIMD instructions from output agreement alone.

Only after both paths and routing are independently explained should the GPU
candidate be rerun against **all72576 nested filter pixels** and earlier gates.
Global production admission additionally still needs general source eligibility,
partial-alpha PNG upload, fractional/nonrectangular coverage, affine transforms,
tight nested filter extents, dynamic buffer lifetime, other component/color/order/
matrix/rush parity and full AS/clip-action ownership proof.

## Regressions and status

Fresh strict regressions: r36 GPU4032/4032 plus the same four complete Yulong
images4/4; r37 actual nested buffers124416/124416; leaf6/6 (69120 RGBA), isolated
Glow4/4, GPU sampler71824/71824, all CPU suites exact. `checks/` and
`acceptance.json` record repository checks. The new filter runner exits **1**;
render completion or intermediate success cannot override final pixel mismatch.

Production54 remains historical9/54, not remeasured or credited with diagnostic
passes. Full roster/Web export and unrelated gameplay GPU/Godot suites are not
rerun because production code/assets are unchanged. No global enable, stability
deviation, allowlist, merge, deployment or Worker change.

## Reproduction

```sh
python3 tools/probes/build_flash_filter_probe.py --case nested-filter-composition \
  --output "$SCRATCH/native" --ffdec "$FFDEC"
python3 tools/probes/capture_native_player.py "$SCRATCH/native" "$SCRATCH/native/native.log" \
  --player-app "$PLAYER" --allow-window-activation --timeout 55
python3 tools/probes/run_nested_filters.py --godot "$GODOT" \
  --native evidence/importer-loud-fail/r38/native --output "$SCRATCH/integer"
# Expected exit1; 67774/72576, no production admission.
python3 -m tools.probes.analyze_materialized_controls \
  --root evidence/importer-loud-fail/r38 --output "$SCRATCH/controls.json"
# Expected exit1: dense scalar controls pass; long spans reject universal model.
python3 -m unittest tools.tests.test_nested_filters
```
