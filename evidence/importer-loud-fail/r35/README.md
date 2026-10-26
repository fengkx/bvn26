# r35: production-path Yulong wrapper diagnostic

**The production-path gate fails: 0/4 complete native images exact. Each image
has 114 differing pixels, with maximum RGB delta 1. Production admission stays
false.** This checkpoint connects the proven bounded sampler to actual production
texture resources, filter buffer allocation and final composition, and isolates
the remaining discrepancy instead of hiding it.

## What now uses the actual production path

`production_sampler_preview.gd` is an opt-in test subclass of `TimelinePreview`.
It runs the inherited timeline loading, placement traversal, texture lookup and
Sprite2D/AtlasTexture construction. It intercepts only the selected leaf's sampler
material. No normal game scene instantiates this subclass; production source and
assets are unchanged.

The material samples the **loaded production Texture2D resource**
`res://generated/fighters/yulong/148.png`. It does not bind raw SWF corner colors
or reconstruct a replacement bitmap. The shader converts decoded straight bytes
to premultiplied bytes, uses the unchanged admitted interpolation, and applies
the bounded source-mask coverage. A metadata texture supplies coordinates/modes
from the unchanged GDScript initializer/span model. The vertex stage covers the
whole destination pixels intersecting the authored half-pixel rectangle; the
fragment stage applies its area coverage.

All of the following remain inherited, without diagnostic replacement:

- `TimelinePreview._compose_blend_group` and its generated final composite shader;
- `FilterGroup` filter passes and `BlendGroup` source bounds, padding and transforms;
- production PNG import/loading, texture upload, and ordinary GPU normal blending.

The actual allocation is **38×8**, origin **(281,196)**. The source rectangle is
**(2,2.5,34,3)** in that buffer; all three filter passes retain the allocated size.
The original Glow colors, blur 5×5, one pass and strength 1 are unchanged. The
complete effective transform remains x=283, y=198.5, scale=1.

The runner checks the original asset manifest hash, source graph/fill/mask from
r33/r34, sample coverage, actual buffer observations and pinned native hashes.
Unknown fields/transforms, unexpected texture or bounds, missing output, engine
errors or any pixel mismatch reject. It exits **1** for this checkpoint. A render
completion marker alone is not a parity pass.

## Measured isolation of the remaining error

| Layer | Exact result |
|---|---:|
| Loaded production PNG → premultiplied source texels | 102/102 |
| Input buffers vs r34 exact diagnostic crop, two cases | 608/608 RGBA pixels |
| Glow buffers vs r34 exact diagnostic crop, two cases | 608/608 RGBA pixels |
| Actual production final composite vs pinned native | **0/4 images** |

The imported PNG has 99 opaque and 3 zero-alpha texels. Godot's configured alpha
border processing changes hidden RGB on those three transparent texels; their
premultiplied values remain exactly zero. The exported resource decode and the
actual GPU input/Glow readbacks agree with the raw-source reference after
premultiplication. This proves the roundtrip for **this bitmap**, not arbitrary
partially transparent PNGs.

Each of the four final images differs in 114 pixels and RGB channel counts
**8 / 113 / 114**. All differing values are **one above native**; alpha is 255 in
both. Across the four images this is 456 differing pixels and 940 differing RGB
channels. Coordinates and exact native/actual bytes are preserved in
`production-path/comparison.json`.

The two intermediate buffers are byte-exact with the cropped r34 buffers, so
PNG decode, bounded sampling and filter-buffer allocation do not explain this
remaining error. It occurs in the unchanged final production normal-composition
path, which decodes premultiplied RGB and uses the hardware blend pipeline.
This evidence does not yet derive every hardware rounding step.

As an independent **read-only diagnosis**, applying the already-used integer
formula `source + floor(96 * (256-alpha) / 256)` to these same Glow bytes matches
all **608/608** pixels in the two native buffer regions. This analysis is saved
in `stages.json`; it is never substituted into rendered images or used to override
the failing final-image gate. The production compositor was not changed to make
this test green.

## Source-first / reference scope

The source chains and five source-first answers remain those in r34:
`157→156→155→148` and `159→158→155→148`, fresh identity placements, one-frame
parent/child lists with no frame controls, and original authored Glow. The source
mask is the full rectangular fill already proved in r33; the test gates this
exact shape/transform before handing its real texture through production code.
No generalized missing-mask fallback is admitted.

The same pinned r21 native images from the r03 Flash capture are used, with their
hashes checked against r32. Ticks 0/3 are static image observations, not a newly
measured 101-tick clock replay. The native target is opaque RGB; alpha=255 checks
do not establish transparent-wrapper parity. No reference was recaptured or
rewritten. Import settings and all shader/runtime/source hashes are archived in
`production-path/texture-import.txt` and `provenance.json`.

## Regressions and admission

Fresh r33 leaf regression remains 6/6 images, 69120/69120 RGBA pixels. Fresh r34
isolated full-wrapper regression remains 4/4. The original GPU sampler remains
71824/71824; the full CPU scalar/clipped/repeat suites remain exact. See `checks/`
and `acceptance.json` for repository checks. Fresh Python: 565 tests (563 pass,
2 skip); caches 26/26; fingerprint 8/8; PROTECTED_FUNCTION_OK, integrity, handoff
and contracts pass. The new final-image gate remains an expected **failure**.

**`production_admitted` is false.** The production 54-image suite was not rerun
and remains the historical r32 **9/54**. The new diagnostic exercises a sampler
substitution in a test subclass, not an enabled production sampling path. No
allowlist, tolerance, per-pixel arithmetic selector or stability deviation.

Remaining blockers:

- Exact ordinary production composition: derive and validate a shared integer
  implementation against native controls covering backgrounds, alpha, opacity
  and nested layers before replacing the current normal composite path.
- PNG upload/premultiplication for partial alpha and other formats remains
  unproven; this particular opaque/zero-alpha bitmap passed.
- Fractional coverage beyond this half-pixel rectangle, nonrectangular masks,
  arbitrary affine/negative transforms and fill-matrix composition remain unproven.
- Nested filter/cache buffers, layer composition and non-unit opacity remain
  unproven even though this specific 38×8 allocation and Glow buffer passed.
- Other component/color/order/matrix/rush differences and full AS/clip-action
  ownership proof remain separate merge gates.

Draft PR #48 is not merge-ready. No production enable, merge, deployment or Worker
changes. Full roster replay, other runtime suites, Web export and the full 54-image
production suite were not rerun because production runtime/assets are unchanged.

## Reproduction

```sh
python3 tools/probes/run_production_wrapper.py --godot "$GODOT" --output "$OUT/production"
# Expected exit 1: actual final composition remains inexact.
python3 tools/probes/run_yulong_wrapper.py --godot "$GODOT" --output "$OUT/r34"
python3 tools/probes/run_bound_bitmap_component.py \
  --build evidence/importer-loud-fail/r33/native --godot "$GODOT" --output "$OUT/leaf"
python3 tools/probes/run_bitmap_godot_fixture.py --godot "$GODOT" --output "$OUT/sampler"
python3 tools/probes/analyze_bitmap_repeat_spans.py --output "$OUT/cpu.json"
python3 -m unittest tools.tests.test_production_wrapper_diagnostic
```

Use actual Compatibility GPU rendering. Tests retain the observed red gate and
verify that exact intermediate buffers cannot turn final pixel failure into a pass.
