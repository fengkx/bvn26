# r242 — actual Jinye pre-outer raster boundary

The original shape56 / first authored placement is now measured before its outer transform. The unchanged rejected CPU sampler matches **15,979/15,980 local pixels**, with one interior RGBA mismatch of1. This does **not** clear the minified direct leaf: inserting an explicit native intermediate changes21 final pixels by as much as136/137. No renderer, component count, or production admission advances.

## Source-bound experiment

The native harness preserves the original JPEG3 bitmap55 and raw shape56/57 tags. It uses the exact r221 first-placement matrices and draw camera. The direct path in both cache states must reproduce the pinned r221 image before any new boundary result is interpreted: **2/2 images,480,000 pixels exact in raw RGBA and independently in premultiplied RGBA**.

An explicit local BitmapData is allocated from the source child polygon, floored/ceiled with one pixel of padding: origin(280,219), size170×94. Its draw matrix includes the original child transform minus that origin. It is then attached with `pixelSnapping="never", smoothing=true` under the unchanged outer transform and camera. Both authored cache property states are retained and read back. This is a deliberately new materialization boundary and bitmap API; it is **not** evidence that Flash internally implements `cacheAsBitmap` this way.

Strict decode checks all1,843 events, exact image dimensions/row widths/order,3,680 original source pixels, source-tag hashes, the pinned r221 fixture, independently recomputed allocation/polygon, actual matrices and direct/materialized bounds. The source-only decoder's plane hashes remain pinned to r220. Native local pixels are experiment outputs and comparison targets; the CPU candidate reads only source-derived JPEG planes.

## Local and final results

[materialization/report.json](materialization/report.json) retains every residual and property readback.

| Boundary | Uncached | Cached |
|---|---:|---:|
|Direct versus pinned r221, raw and premultiplied|240,000/240,000|240,000/240,000|
|Fixed CPU versus explicit local buffer|15,979/15,980|15,979/15,980|
|Strict geometric interior|6,113/6,114|6,113/6,114|
|Geometric edge|515/515|515/515|
|Outside polygon|9,351/9,351|9,351/9,351|
|Explicit materialized versus native direct|21 changed, max136|21 changed, max137|

Native local buffers are identical across the two cache states,15,980/15,980. Their single CPU mismatch is at local(90,45): candidate `[25,14,24,37]`, native `[26,15,25,38]` in **premultiplied RGBA**. The candidate PNG stores those premultiplied bytes directly; it is not a straight-alpha display preview.

The retained global sampler is still `scaled_child_then_draw_quarters/minimum/HV`. At this pixel it produces fixed coordinates `(3039002,1058559)`, source cell(46,16), fractional bytes(95,38). The four source texels are `[0,0,0,0]`, `[0,0,0,0]`, `[179,106,172,255]`, `[167,94,160,255]`. The Y fixed coordinate lies one unit below the next byte-weight boundary. Adding one unit locally would reproduce this pixel, but is **not an admissible fix**: r241 retains other witnesses that require incompatible phase bounds, including≥2387 and≤2386 for the same fixed-row family. No phase or operation path is chosen from this pixel.

## Supplemental rejected scan constructions

[scan-initialization.json.gz](scan-initialization.json.gz) tests two fixed alternatives against all436,000 retained r233 nearest-cell samples. Exact row initialization with quantized X stepping gives409,480 exact; exact column initialization with quantized Y stepping gives409,756; the retained construction gives409,816. Their common-phase feasible groups are8/16,9/16 and12/16 respectively. None qualifies for an old-axis retest or rendering change. Origin0 is the declared diagnostic construction, not an asserted native scan origin.

[footprint-scope.md](footprint-scope.md) explains a critical scope limit: r170–178 proved identity-fill or uniform compensated-fill families. They did **not** establish the minimum/norm footprint rule for `inverse(display * rotated/anisotropic authored_fill)`. The source-unit audit proves the source matrix encoding, not this operation ordering or execution route. Generic native affine/cache addresses in older evidence remain unverified for this bitmap-fill path.

## Reproduction and acceptance

```sh
python3 -m tools.probes.build_jinye_materialization \
  --output /tmp/bvn-r242/native --ffdec /tmp/bvn-loud-fail/r02/ffdec/ffdec-cli.jar
python3 tools/probes/capture_native_player.py /tmp/bvn-r242/native \
  /tmp/bvn-r242/native/native.log \
  --player-app '/Users/fengkx/me/code/flash-player/Flash Player.app' \
  --allow-window-activation --timeout 90
python3 -m tools.probes.analyze_jinye_materialization \
  --native /tmp/bvn-r242/native --dump /tmp/bvn-r215/jpeg-planes \
  --output /tmp/bvn-r242/materialization
# Expected exit1: the source-local candidate remains inexact.
python3 -m tools.probes.analyze_jinye_scan_initialization \
  --output /tmp/bvn-r242/scan-initialization.json
python3 -m unittest tools.tests.test_jinye_materialization \
  tools.tests.test_jinye_scan_initialization
```

Tests:6 passed. Independent source-tag, native-baseline and scan reviews are retained beside this README. Runtime and production assets are unchanged; no new full gameplay/build acceptance claim. `candidate_admitted=false`, `gpu_advance_allowed=false`, `production_admitted=false`. Full AS/clip-action ownership remains a separate blocker.

## Next bounded discriminator

A single common source-coordinate operation must clear the local one-unit witness and the retained old upper-bound witness simultaneously; a constant phase adjustment is already disproved. Keep this actual shape56 source and both the direct and explicit-local workloads fixed. Identify the **executed bitmap-fill matrix setup** and record its authored-fill/display/device operands before inverse/footprint initialization, first for the local near-exact path and then for the minified direct path. The concrete unknown is whether the identity-fill footprint construction is applied before or after the authored rotated fill; retained generic affine/cache addresses alone do not prove this route. A targeted execution/operand observation must establish that distinction before another rendering construction is admitted. Retain the local(90,45) one-unit witness and both contradictory old phase witnesses as mandatory rejection tests. Do not infer a route from matching RGB, substitute explicit materialization for native caching, or fit a per-leaf phase.
