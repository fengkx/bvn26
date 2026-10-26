# r34: complete Yulong Glow wrapper diagnostic

**4/4 complete images match the pinned 54-suite native images exactly. Production
admission remains false.** These are the two Yulong Glow placements at owner 157
and owner 159, frame 1/depth 1, each sampled at ticks 0 and 3. This replaces the
leaf-only diagnostic boundary with a complete isolated wrapper comparison; it
does not enable or certify the production texture/render path.

## Source and reference preservation

The wrapper fixture retains the existing component cases, including the authored
outer GLOWFILTER, child hierarchy, placement matrices, sample ticks and normalization.
Both paths are `157 → 156 → shape155 → bitmap148` and
`159 → 158 → shape155 → bitmap148`. All source placement matrices are identity.
The existing fixture normalization is scale 1, x=283, **y=198.5**; it is not rounded
or changed. The two authored colors are (81,211,239) and (93,225,244), alpha 255,
blurX/Y=5, one pass, strength 1.

The r33 validated leaf fixture preserves original Lossless2 premultiplied texels,
fill type 65, identity-in-pixels fill MATRIX, and directed rectangular mask.
The diagnostic derives the covered bounds from that mask, rather than discarding
it and substituting texture coverage. Parent/child graphs, one-frame display lists,
frame events, placement fields, filter fields and the effective transform are
checked before rendering. Unknown clip actions, filters or transforms are rejected.

Five source-first answers:

1. Shapes have no frame actions. Both selected parent/child sprites have one
   frame and empty compiled frame-event lists; the diagnostic rejects changes.
2. Source frame 1 places the identity child/shape at depth 1 as a fresh placement;
   no MOVE, clip-depth mask or CXFORM is being omitted.
3. There is no compiled terminal control or evolving multi-frame child in this
   selected graph. Its two pinned image ticks are static observations. The
   diagnostic renders the static graph once per color and compares it against
   both original tick images; it does not claim a fresh 101-tick clock replay.
4. The invariants are the original hierarchy/filters/transforms/mask/source bytes
   and all 600×400 destination pixels, with exact byte comparisons.
5. References are the **unchanged** r21 native PNGs decoded from the pinned r03
   Adobe Flash Player captures. Their SHA-256 hashes are checked against r32's
   component inventory. No native reference was recaptured or rewritten.

## Diagnostic path and measured result

1. The unchanged r32 GDScript initializer/span model computes coordinates/modes.
   Four source corners are bound from the r33 raw bitmap, not regenerated colors.
2. `wrapper_bitmap_input.gdshader` keeps the admitted interpolation code unchanged
   (a test verifies this). Its output remains premultiplied for filtering. It
   applies geometric pixel/rectangle area coverage and floors to source bytes.
   Coverage is stored in RF, so the measured half-edge is exactly 1/2, not 128/255.
3. The **unchanged production flash_filter.gdshader** applies authored horizontal
   blur, vertical blur and outer Glow composition. Intermediate input/glow images
   are archived for independent diagnosis.
4. The diagnostic composites premultiplied bytes onto the original opaque
   (96,96,96) background with the integer source-over rule. No extra straight-RGB
   readback/re-premultiply roundtrip is inserted before the Glow.

| Fixed native image | Previous production max RGB delta | Diagnostic max RGB delta |
|---|---|---|
| yulong-157-1-1, tick 0 | 64 / 76 / 83 | 0 / 0 / 0 |
| yulong-157-1-1, tick 3 | 64 / 76 / 83 | 0 / 0 / 0 |
| yulong-159-1-1, tick 0 | 64 / 80 / 85 | 0 / 0 / 0 |
| yulong-159-1-1, tick 3 | 64 / 80 / 85 | 0 / 0 / 0 |

All **960000 destination pixels / 2880000 RGB channels** match. The native
component target is opaque BitmapData; alpha=255 is also checked, but this is
not evidence of transparent-wrapper RGBA parity. The r33 transparent leaf suite
is separately rerun and remains 6/6 images, 69120/69120 RGBA pixels exact.

`wrapper/comparison.json` records hashes and per-channel deltas; `wrapper/` also
contains actual GPU input, filtered cache and complete readback images. Source,
fixture, GPU command and executable hashes are in `wrapper/provenance.json`.
The strict runner rejects incomplete/duplicate samples, missing outputs, GPU
errors, wrong native hashes and any channel mismatch. Tests inject a one-channel
delta and require failure. No allowlist, tolerance or RGB-dependent formula choice.

## Admission and remaining blockers

`wrapper_passed` is true; **`production_admitted` stays false**. This is still a
GDScript/data-texture diagnostic, not a binding in TimelinePreview. The full
production 54-image suite was not rerun and remains its r32 result **9/54**. Do
not report 13/54 production parity by mixing diagnostic and production results.
The four previously failing references now have exact isolated diagnostic matches.

Remaining proof before a production path can be admitted:

- Fractional coverage: only this axis-aligned rectangle's specific half-pixel Y
  boundary is now covered by the complete-image evidence. Quarter phases,
  fractional X, scaled/nonrectangular masks and arbitrary coverage remain unproven.
- Real PNG upload/premultiplication: this path consumes original premultiplied
  Lossless2 bytes and avoids the production PNG roundtrip.
- Arbitrary affine/negative transforms and fill-matrix composition remain unproven.
- Production compositing/filter-buffer allocation and attachment are not exercised;
  this diagnostic uses complete destination-sized buffers and explicit integer
  composition. Multiple backgrounds, nested layers and production opacity need
  validation before generalization.
- Other component/color/order/matrix/rush differences and full AS/clip-action
  ownership remain separate merge blockers. No AS ownership claim is added here.

Next: connect this exact bounded wrapper path in a production-path *diagnostic*
that preserves texture decoding, buffer bounds and actual composition. Reuse these
same native images as the gate; do not enable production merely from this pass.

## Reproduction and acceptance

```sh
python3 tools/probes/run_yulong_wrapper.py --godot "$GODOT" --output "$OUT/wrapper"
python3 tools/probes/run_bound_bitmap_component.py \
  --build evidence/importer-loud-fail/r33/native --godot "$GODOT" --output "$OUT/leaf"
python3 tools/probes/run_bitmap_godot_fixture.py --godot "$GODOT" --output "$OUT/sampler"
python3 tools/probes/analyze_bitmap_repeat_spans.py --output "$OUT/cpu.json"
python3 -m unittest tools.tests.test_yulong_wrapper_diagnostic
```

Fresh Python: 560 tests (558 pass, 2 skip); caches 26/26; fingerprint 8/8;
PROTECTED_FUNCTION_OK, integrity/handoff/contracts pass. All existing CPU sampler
regressions and 71824/71824 GPU samples remain exact.

GPU runs require actual Compatibility rendering, not `--headless`. Fresh checks
and counts are in `acceptance.json` and `checks/`. Production runtime/assets,
locked inputs and admitted r27/r30/r31/r32 sampler code remain unchanged. Full
roster replay, other runtime suites and Web export were not rerun. No intentional
stability deviation; no merge, deployment or Worker changes. Draft PR #48 remains
not merge-ready.
