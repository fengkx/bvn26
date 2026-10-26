# r223 — bounded original-tag and Drawing API equivalence exact

Synthetic lossless bitmap55 controls retain the unchanged original shape56/57 tags, including bitmap matrices and shape records. Six separate SWFs preserve those raw shape bytes before and after script import. The six inputs, two shapes, three draw scales and two cache states reproduce r222's Drawing API controls **72/72 images,663552/663552 RGBA pixels exactly**. All22080 source-pixel readbacks and36 placement/outer/draw matrix groups match. Full images are compared, including transparent and outside-mask pixels; geometry never excludes an API mismatch.

[Comparison](comparison.json), [direct-tag captures](native/), [acceptance](acceptance.json). The original r222 reference hashes are pinned. This is bounded equivalence for opaque ramp/impulse inputs and these source transforms, not a universal API equivalence proof. The original sparse JPEG leaf's sampler is still unproved; no sampling math or production runtime changed. `bounded_source_tag_equivalence_proved=true`, `general_source_tag_equivalence_proved=false`, `source_jpeg_leaf_sampler_admitted=false`, `production_admitted=false`.

The first experiment used short tag headers for highly compressed impulse bitmaps. Native loadBitmap returned0×0 for those inputs, and the strict input guard rejected the capture before comparing images. Explicit long bitmap headers corrected the fixture; all six inputs were recaptured. [Rejected captures](rejected-short-header/) are retained and tested as a negative control. Source shape bytes and accepted references were not rewritten to hide a rendering difference.

```sh
python3 -m tools.probes.build_jinye_tag_controls --output /tmp/jinye-tags --ffdec /path/to/ffdec-cli.jar
# Capture source0 through source5 sequentially with the same command.
python3 tools/probes/capture_native_player.py /tmp/jinye-tags/source0 /tmp/jinye-tags/source0/native.log --player-app '/path/to/Flash Player.app' --allow-window-activation --timeout 90
python3 -m tools.probes.compare_jinye_tag_controls --native evidence/importer-loud-fail/r223/native --output /tmp/jinye-api-comparison.json
python3 -m unittest tools.tests.test_jinye_tag_controls
```

Complete component diagnostics remain46/54 (Jinye4/Yijiao4 unbound); historical production9/54 not rerun. Full AS/clip-action ownership and justified production binding remain separate merge gates.

Next discriminator: globally test independently defined quantized-center and nearest-derived geometric-offset smooth coordinate constructions against the now-bounded-equivalent H/V ramps, then corner impulses and original r221 JPEG leaves. Retain r91/r92 half-even axis controls; the old clipped ceiling initializer is already rejected. Use r176 `min(0,a,b)` geometry, not the older sum-of-negative-components; cache rebasing must precede inverse quantization where justified. Do not choose coefficients, cache routes or interpolation order from observed RGB. No GPU admission before every applicable control clears. Draft only; no merge/deploy/Worker.
