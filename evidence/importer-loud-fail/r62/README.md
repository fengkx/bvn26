# r62 — actual native-sized buffers pass the old order gate, broader routing still rejects

The original color-order fixture remains **4/4 groups,2560/2560 channels exact** when the actual diagnostic FilterGroup input and all filter-pass buffers become70×70 at(37,37). This uses the unchanged r59 shader's real texture width, with **no logical-span offset uniform**. The inherited production allocator/filter passes are exercised by a test-only subclass overriding padding from independently measured rectangles; production code is unchanged.

The broader independent native suite **fails closed**:

| Stage | Exact RGBA pixels |
|---|---:|
| Input | 6400/6400 |
| Filtered, before CXFORM | 6400/6400 |
| Final | **6392/6400** |

40 cases vary source width15,16,17,18,19,20,31,32,33,64; integer origin40/41; opacity100/50. Source color, fill alpha80%,5×5 Glow and RGB transform are unchanged from the old order probe. Each native case independently emits its filter rectangle and input/filtered/final rows. Paired transparent and black readbacks recover premultiplied RGB directly, not by lossy multiplication of getPixel32 straight bytes.

## Measured remaining discriminator

Eight final pixels differ by one channel, confined to source widths17 and33 at the rightmost nonzero Glow pixel, both origins/opacities. The diagnostic scalar tail produces red9 vs native8 at100%, green12 vs native11 at50%. The source and filtered pixels are exact, so the remaining issue is routing at an implicit cached/vector boundary, not an admitted-arithmetic or filter-input mismatch.

[Exact sites](rows/comparison.json) include case id, x, native/GPU RGBA; [fixture](rows/fixture.json) maps each id to source width/origin/opacity/native rectangle. Public generateFilterRect width alone does not explain every internal span. Do not select a rounding/extra-border rule because it happens to match these pixels.

Next independently compare the same odd-width vector rectangle against an explicitly materialized bitmap with the same verified input bytes, retaining all stages and geometry. This can distinguish vector bounds/raster cache construction from general bitmap extent/stride partition. Fractional translations and destination clipping can then discriminate the remaining initialization/partition hypotheses. Keep the fixed common arithmetic and old controls unchanged.

## Reproduction

```sh
python3 tools/probes/build_flash_filter_probe.py --case filter-extent-rows \
  --output /tmp/bvn-r62/native --ffdec /path/to/ffdec-cli.jar
python3 tools/probes/capture_native_player.py /tmp/bvn-r62/native /tmp/bvn-r62/native/native.log \
  --player-app '/path/to/Flash Player.app' --allow-window-activation --timeout 30
python3 -m tools.probes.run_native_extent_rows --godot /path/to/Godot \
  --native evidence/importer-loud-fail/r62/native --output /tmp/bvn-r62/rows
# Expected exit1 until all final pixels match.
python3 -m unittest tools.tests.test_native_extent_rows
```

The original order allocation gate is reproducible with `res://tests/native_allocated_color_order.gd`, arguments `OUTPUT/order.json tools/probes/flash_filters/color-matrix.json order evidence/importer-loud-fail/r61/render/fixture.json` (absolute paths), using a graphical Compatibility renderer. Its actual buffers and strict comparison are retained in `order/`. [Acceptance](acceptance.json) records checks and non-rerun gates.

No production enablement, native baseline rewrite, channel tolerance, allowlist or formula chosen from RGB. Components remain historical9/54; full AS/clip-action ownership remains open. r58/r59/r60 exact arithmetic and GPU readbacks are retained by strict Python regressions; full roster/Web export and unchanged graphical suites were not rerun. Draft only; no merge/deploy/Worker.
