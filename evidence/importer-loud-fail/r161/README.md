# r161 — equivalent child/fill transform paths reproduce identical native output

320 native images realize the same source-to-device matrix through two paths: transformed child with identity fill, and identity child with transformed fill plus corresponding authored contour. Original256 source bytes, actual child/draw matrices, declared fill matrices, authored vertices and observed bounds are retained.

All **256000/256000 paired pixels match**, including **22261/22261 geometrically isolated interior pixels**. The child path also reproduces the old r158 images256000/256000. This rejects transform-path decomposition as an explanation within these controls; it does not reveal the internal consumed fill matrix or admit any sampler.

[Summary/geometry](summary.json), [native readbacks](native/native.log.gz), [provenance](provenance.json), [acceptance](acceptance.json). The fill matrix is explicitly labeled **declared**, since the graphics API does not expose an internal fill-matrix readback.

```sh
python3 tools/probes/build_flash_filter_probe.py --case bitmap-affine-transform-paths --output /tmp/affine-paths --ffdec /path/to/ffdec-cli.jar
python3 tools/probes/capture_native_player.py /tmp/affine-paths /tmp/affine-paths/native.log --player-app '/path/to/Flash Player.app' --allow-window-activation --timeout 90
python3 -m tools.probes.analyze_affine_transform_paths --native evidence/importer-loud-fail/r161/native --old-native evidence/importer-loud-fail/r158/native --output /tmp/affine-paths.json
python3 -m unittest tools.tests.test_affine_transform_paths
```

Next discriminator: enlarge the coordinate-coded source to128×128 and sample independent distant source X/Y positions with single-pixel clips. The old16×16 intervals may be too broad to reject incorrect step coefficients. Retain exact raw texel readbacks, child/draw properties and all old bounds; compare feasibility before attributing residuals solely to the intercept. Never fit a coefficient from an interval.

`affine_sampler_admitted=false`, `production_admitted=false`.24 live/wrapper original images remain exact; production54 historical9/54; full AS ownership remains open. Draft only; no merge/deploy/Worker.
