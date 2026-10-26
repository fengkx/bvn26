# Scope audit of the affine footprint proof

This is a read-only provenance audit. No renderer, arithmetic construction, source input or native reference is changed. Paths and line numbers below refer to this repository snapshot.

## What the retained proof covers

- `tools/probes/flash_filters/bitmap-affine-heldout.as:13` uses `beginBitmapFill` with an identity fill matrix, clipped and unsmoothed. The independent affine matrix is applied to the child at line14. The tie controls likewise use identity fill at `tools/probes/flash_filters/bitmap-affine-offset-ties.as:11`.
- `tools/probes/flash_filters/bitmap-affine-fill-phase.as:13` varies **translation-only** fill matrices. It does not vary a rotated or anisotropic fill linear part.
- `tools/probes/flash_filters/bitmap-affine-reflection-phase.as:16` uses uniform fill scale `factor` with an integer phase. Line19 compensates the child linear matrix by that same factor; line39 uses factor64. This is a bounded nonidentity-fill proof, not a proof for every compound fill matrix.
- `tools/probes/analyze_affine_heldout.py:13` constructs the inverse from the child/display matrix; line16 independently consumes child and draw translations on quarter grids. `tools/probes/analyze_affine_rounded_footprint.py:32` quantizes inverse rows and line37 applies minimum-component plus Euclidean norm offset. Its scalar fill phase is subtracted separately in `indices`, line47.
- `evidence/importer-loud-fail/r176/README.md:3` records66882 exact native observations. `r177/README.md:5` independently distinguishes ties-even; line7 explicitly limits the combined68322 observations to bounded opaque-interior sampling, excluding smoothing, boundaries and production composition.
- The next real-source leaf was not a general compound-fill test either: gzip-decoded `evidence/importer-loud-fail/r179/native/fixture.json.gz`, JSON pointer `/leaf/fill_matrix`, contains scaleX=scaleY=20, no rotation, zero translation. Dividing the SWF twip matrix by20 gives identity in pixels.

## What remains unproved for Jinye

Jinye's raw fill matrices contain rotation and unequal scale components; they are not identity or uniform-factor copies. `tools/probes/analyze_jinye_smooth_leaf.py:122` correctly reconstructs raw fixed16.16 coefficients and converts twips to pixels; line136 composes the full source-to-stage matrix with that fill. The r241 source-unit audit independently checks this reconstruction against unchanged raw tags. It does **not** prove the native rasterizer consumes that full rational composition in one operation, or applies the identity-fill footprint correction to its inverse.

Thus transfer of the minimum/norm phase to `inverse(display * authored_fill)` remains a rejected hypothesis. r232/r233 nearest counterexamples exist before smooth interpolation. r223's DrawingAPI/direct-tag equivalence covers its explicitly retained geometries and input textures only; it does not prove arbitrary identity-fill refactorings of the original JPEG leaf.

## Existing binary evidence and its limits

No sampler-specific compound-fill setup function is established by the inspected r170–178 artifacts. Existing relevant binary evidence is generic affine/cache setup:

- `evidence/importer-loud-fail/r110/README.md:3`: generic compose at `0x10029dad0`, inverse at `0x10029de20`; execution routing is explicitly unverified. The proposed generic cache constructions regress old controls.
- `tools/probes/extract_cache_affine_binary.py:10` pins fixed compose translation bytes `0x10029db0e..0x10029db56`; lines11–12 pin float/fixed inverse-axis spans. Line35 retains `execution_routing_verified=false`.
- `evidence/importer-loud-fail/r111/README.md:5`: sampled cache-workload call edges narrow the caller to `0x10015c080`, but do not prove branch values or sampler invocation.
- `tools/probes/extract_cache_normalization_binary.py:10` pins device setup `0x10015c991..0x10015c9ca`; lines11–12 pin origin-field inverse `0x10015e678..0x10015e6c8` and inverse-translation store `0x10015e795..0x10015e7cf`. Line32 pins float32 0.05 at `0x10107ba48` and explicitly leaves the normalization branch unverified.

These are useful addresses for a future targeted call-site investigation, not permission to transplant cache arithmetic into bitmap-fill setup. The next missing fact is the independently verified ordering and units of authored fill/display/device composition before inverse and footprint setup. Actual source local/input buffer boundaries should locate the failing boundary first; no new variant or native grid was run for this audit.

`candidate_admitted=false`, `gpu_advance_allowed=false`, `production_admitted=false`.
