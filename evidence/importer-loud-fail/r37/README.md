# r37: explicit native buffers and actual nested production nodes

**432 independent combinations, 124416/124416 RGBA buffer pixels exact.**
The two materialized layer boundaries now run through actual production
`TimelinePreview._compose_blend_group` / `BlendGroup` allocation and reparenting,
with the shared integer compositor enabled only by a diagnostic subclass.
`production_admitted` remains **false**. No production runtime/assets changed.

## Explicit native materialization

`tools/probes/flash_filters/nested-materialized-composition.as` allocates three
independent `flash.display.BitmapData` objects and issues ordered `draw` calls:

1. Child 8x8: an alpha63 bitmap followed by an overlapping 4x4 alpha191 bitmap.
2. Parent 12x8: an alpha128 middle bitmap followed by the **completed child
   BitmapData** at x=2 with child opacity.
3. Final 16x8: background bitmap, then the **completed parent BitmapData** at x=2
   with parent opacity, then an overlapping 2x8 alpha127 sentinel at x=6.

No `cacheAsBitmap` flag, lazy display-list caching or inferred cache allocation
is used. Child and parent bytes are read back independently and reused as completed
source textures; neither buffer is mutated after its composition. The final sentinel and the earlier middle/background make
wrong destination-copy ordering observable. Coverage is integer-aligned rectangles;
there are no sampling, antialias or geometric approximations in these controls.

Two color palettes × six independent destination alphas {0,1,64,128,254,255} × six
child opacities {0,1,25,50,99,100} × six parent opacities {0,1,25,50,99,100} = 432
cases. The native input colors, all three buffers and completion are captured
under a unique run ID. Black readback supplies premultiplied RGB and transparent
readback supplies alpha; no lossy straight-to-premult conversion of references.

An additional source-input event checks all five original bitmap colors for every
case, **2160/2160 source pixels**. BitmapData constructor premultiplication for
these inputs is `floor((color*alpha+127)/255)`. It is distinct from the admitted
PNG/raster-input conversion; they are not conflated. This conversion is checked
against independent native source readback before either CPU or GPU comparison.
The first exploratory run caught this distinction as delta1 and was not admitted.

Source-first answers: the checked-in probe frame1 executes synchronously and
stops; there are no MOVE tags, enterFrame callbacks or label exits involved. Each
byte buffer is freshly allocated, drawn in the explicit source order, read back
and disposed. Assertions describe the native buffers for those same inputs.
This is a synthetic composition proof, not a new BVN gameplay/source-ownership
claim; locked `game/` and `scripts/` are untouched.

## Actual production nodes, diagnostic composition

`nested_buffer_preview.gd` inherits `TimelinePreview` and invokes the unchanged
production `_compose_blend_group` twice with `isolate=true`. Both layers use
actual `blend_group.gd` nodes, `Contents` SubViewports, `source_bounds`, buffer
origin/extent calculation, reparenting and `Composite` texture binding. The child
node really is inside the parent's `Contents`; no flattened one-pass shader
stands in for these layers.

The child has size8x8 at parent-buffer origin(2,0); the parent has size12x8 at
final-target origin(2,0). All 432 allocations are asserted and recorded. Each
case has its own transparent16x8 final viewport and independent World2D.

Only `_apply_blend` is overridden by the opt-in diagnostic. It preserves opacity
from the production composite material, quantizes the Flash8.8 multiplier, uses
r36's unchanged shared integer functions, and disables hardware blending. A
`BackBufferCopy` child with `show_behind_parent=true` captures the destination
immediately before each leaf/composite. Thus ordinary composition at each actual
buffer boundary reads its own actual GPU destination. Inputs are byte textures
constructed from authored colors, checked against native source readback; no
reference output image is uploaded as a source.

The model scales stored premultiplied bytes at each **materialized** boundary,
then performs `front + floor(back*(256-front.alpha)/256)`. Parent opacity is
applied to the finished parent texture, not distributed over its children. This
is intentionally different from assuming every r36 synchronous display-list
cache flag had materialized a buffer.

| Native vs actual GPU buffer | Exact pixels | Maximum RGBA delta |
|---|---:|---:|
| Child | 27648/27648 | 0 |
| Parent | 41472/41472 | 0 |
| Final | 55296/55296 | 0 |

The correct-order runner exits **0**, while leaving `production_admitted=false`.
Missing events/buffers, changed source hashes, engine errors, unexpected bounds
or even a single channel mismatch reject. Test coverage includes one-byte
mutation, missing boundary, corrupted input, malformed native order and hashes.

## Destination-copy negative control

`--copy-order stale` moves the child's destination copy ahead of the preceding
middle sibling. The production group still gets valid transform metadata and
completes without an engine error; this is a genuine rendered-pixel failure:

- Child remains 27648/27648 exact.
- Parent falls to **13824/41472**, 27648 differing pixels.
- Final falls to **33152/55296**, 22144 differing pixels.
- Maximum channel delta **128**; the runner exits **1**.

`stale/` archives all readback pixels, allocation records and a compact failure
summary. Every mismatch coordinate is recoverable by comparing those lossless
atlases to `native/native.log`; the 17MB expanded repeated-coordinate report is
not committed. The negative result is never counted as an admission pass.

## Regressions, admission and remaining scope

Fresh r36 controls remain **4032/4032 GPU**, native bitmap/vector2016/2016 each,
and the same pinned complete Yulong images remain **4/4** exact. Leaf **6/6**
(69120 RGBA), isolated Glow **4/4**, sampler GPU **71824/71824**, and all CPU
scalar/clipped/repeat regressions are exact. See `checks/` and `acceptance.json`.

**Production remains disabled and PR #48 remains Draft / not merge-ready.**
This proves actual two-level BlendGroup byte-buffer composition for these
integer-aligned synthetic inputs. It does not prove global routing, arbitrary
source eligibility, nested filtered groups, dynamic reparenting/frame scheduling,
noninteger/negative affine coverage or partially transparent PNG decoding.
No production-path enable is inferred from a diagnostic pass. No stability
deviation, allowlist, tolerance or output-dependent formula selection.

Next bounded experiment: use the same explicit native materialization at nested
**filter** boundaries, retaining non-unit parent/child opacity and transparent
destinations; exercise actual FilterGroup allocation/padding and post-filter
CXFORM in the production-path diagnostic before widening eligibility. General
sampling/coverage and remaining component/color/order/matrix/rush pixels still
need independent proof. Full AS/clip-action ownership remains a separate gate.

Production 54-component status stays historical **9/54**; it was not remeasured
or credited with synthetic results. Production compositor remains unchanged.
Full roster replay, other gameplay Godot/GPU suites and Web export were not rerun
because this changes diagnostic code only; repository checks are recorded below.

## Reproduce

```sh
python3 tools/probes/build_flash_filter_probe.py --case nested-materialized-composition \
  --output "$SCRATCH/native" --ffdec "$FFDEC"
python3 tools/probes/capture_native_player.py "$SCRATCH/native" "$SCRATCH/native/native.log" \
  --player-app "$PLAYER" --allow-window-activation --timeout 55
python3 tools/probes/run_nested_composition.py --godot "$GODOT" \
  --native evidence/importer-loud-fail/r37/native --output "$SCRATCH/fresh"
# Expected exit0, 124416/124416 RGBA; production_admitted=false.
python3 tools/probes/run_nested_composition.py --godot "$GODOT" \
  --native evidence/importer-loud-fail/r37/native --output "$SCRATCH/stale" --copy-order stale
# Expected exit1 with pixel failures and no engine errors.
python3 -m unittest tools.tests.test_nested_composition
python3 tools/probes/run_normal_composition.py --godot "$GODOT" \
  --native evidence/importer-loud-fail/r36 --output "$SCRATCH/r36"
```
