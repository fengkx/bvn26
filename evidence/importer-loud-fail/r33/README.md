# r33: source-bound bitmap leaf diagnostic

**Yulong shape 155 / bitmap 148: 6/6 complete RGBA images exact, 69120/69120
pixels. Production admission remains false.** This is a new source-backed leaf
component measurement, not six additional passes in the historical 54-image
filter/cache suite. That suite remains 9/54 (last measured r32).

## Source eligibility and preserved semantics

The selected leaf is `game/fighter/yulong.swf / DefineShape_155`, referenced by
`DefineSprite_156/frame_1/depth_1` and `DefineSprite_158/frame_1/depth_1`. Both
place it with an identity matrix. Its authored fill is type 65 (smooth clipped),
bitmap 148, bitmap MATRIX scale 20/20 twips with zero translation/skew. The source
edges form a 34×3 rectangle. The 34×3 DefineBitsLossless2 format-5 bitmap contains
99 opaque and 3 transparent texels, with actual non-primary RGB values.

The builder exports the locked SWF with FFDEC, compiles the directed fill edges
using the existing contour extractor, and retains the full shape XML, fill flags,
fill matrix, mask contour, source hash and raw tag hashes in `native/fixture.json`.
Native input copies the **original bitmap and shape tags byte for byte** into an
isolated one-frame wrapper. After instrumentation the builder checks those tags
again; a rewrite is an error. The wrapper places the leaf at identity; it does
not copy, remove or claim to implement the outer Glow filter.

Five source-first answers for this diagnostic scope:

1. The selected shape has no DoAction/enterFrame or timeline; it is a shape, not
   an animated sprite. The diagnostic wrapper only places this shape once.
2. The wrapper uses a new identity PlaceObject2 at depth 1, not MOVE. Original
   source parents 156/158 also place the shape at identity in their sole frame.
3. The one-frame wrapper remains on its single frame; capture is synchronous
   BitmapData.draw. There is no source goto/stop behavior being replaced.
4. Assertions preserve raw shape/bitmap tags, actual fill contour, exact ARGB
   words and all destination pixels, including transparent outside coverage.
5. The same source tags and declared draw transforms/clips were captured in
   Adobe Flash Player Debugger 32. Native trace, build metadata and environment
   are under `native/`; no existing reference was rewritten.

Other inspected inputs are not interchangeable: Orochimaru 341 and main/XG_mfdjx
bitmap shapes use type 67 (non-smoothed); Jinye has rotated fill matrices. Those
were not routed into this smooth axis-aligned diagnostic.

## Bound path and exact-image gate

`build_bound_bitmap_component.py` decodes the native Lossless2 premultiplied ARGB
bytes directly. This avoids making an unproven PNG decode/re-premultiply roundtrip.
`bound_bitmap_component.gd` uses the actual retained fill contour to calculate
covered rows and intersect the destination clip. It passes the actual bitmap
width/height, effective transform and covered span to the unchanged r32 sampler;
source corners come from the original bitmap bytes rather than synthetic colors.
The unchanged r32 GPU shader interpolates those bytes and applies its native
getPixel32 readback encoding. Outside coverage remains transparent.

This is still a diagnostic atlas path: CPU/GDScript supplies source corners and
row metadata to data textures. It is **not** the production Sprite2D/Polygon2D
texture upload, rasterizer, filtered wrapper or framebuffer composition path.
The six whole-image comparisons exercise scales 1/3/5/8 and two independent X/Y
scale + clip combinations. All shape/clip edges are integral; fractional coverage,
nonpositive scale, rotation and unknown transform fields reject the diagnostic.
The original fill matrix must remain identity in pixel units. Unsupported fills,
strokes or masks reject; there is no bounding-box fallback.

`run_bound_bitmap_component.py` validates source metadata/bytes, deletes stale
renders, requires a successful GPU process and completion marker, then performs
strict whole-image native comparison. Missing/reordered/duplicated trace rows,
wrong dimensions, or any differing RGBA channel fail. The report separately records
`diagnostic_passed: true` and `production_admitted: false`.

| Measurement | Exact / total |
|---|---:|
| New source-backed leaf images | 6/6 |
| Complete destination RGBA pixels | 69120/69120 |
| Existing r32 GPU/native regression | 71824/71824 |
| Production filter/cache components | 9/54, historical r32; not rerun |

`render/comparison.json` contains per-case transforms, clip rectangles, changed
channel counts and maxima (all zero). `render/case-*.png` are GPU readbacks;
`render/native-*.png` are lossless decoded native trace images. Provenance pins
code, source fixture, native capture, GPU executable and readback hashes.

## Acceptance and remaining blockers

Fresh Python: 555 tests (553 pass, 2 skip); caches 26/26; fingerprint 8/8;
PROTECTED_FUNCTION_OK, integrity/handoff/contracts pass. Full roster replay,
other runtime GPU/Godot suites and Web export were not rerun. See
`acceptance.json` and `checks/`. No production runtime,
production assets, shared sampler, native baseline or locked input changed.
No new allowlist, tolerance or intentional stability deviation. The shared
production component renderer is unchanged, so the 54-image suite was not
rerun and its exact count is not raised. Color/order/matrix/rush and full
AS/clip-action ownership proof remain separate unresolved gates.

Next: carry the proven raw-texel/coverage binding into an isolated *complete*
Yulong wrapper diagnostic, retaining its authored Glow and effective transforms,
then compare against the pinned 54-suite native image. Do not enable the production
path based on this leaf-only result. Fractional coverage, real PNG upload and
premultiplication, arbitrary affine transforms and production compositing require
separate proof. Draft PR #48 is not merge-ready.

## Reproduce

```sh
python3 tools/probes/build_bound_bitmap_component.py --output "$OUT/native" --ffdec "$FFDEC"
python3 tools/probes/capture_native_player.py "$OUT/native" "$OUT/native/native.log" \
  --player-app "$FLASH_APP" --allow-window-activation --timeout 50
python3 tools/probes/run_bound_bitmap_component.py --build "$OUT/native" \
  --output "$OUT/render" --godot "$GODOT"
python3 -m unittest tools.tests.test_bound_bitmap_component
```

Use an actual Compatibility GPU, not `--headless`. To compare the pinned capture
without a new Flash run, pass `evidence/importer-loud-fail/r33/native` as `--build`.
The tests also deliberately inject a one-channel delta and require gate failure.
No merge, deployment or Worker changes.
