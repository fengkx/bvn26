# r221 — isolated Jinye smooth affine leaf rejects the center-sample baseline

Two independently isolated leaves retain original bitmap55 and shape56/57 raw tags, active fill65, source quadrilateral masks, frame1/10 depth1 matrices, root translation and capture normalization. Four native RGBA captures explicitly vary cacheAsBitmap; source transform/property readbacks are checked. Cache versus uncached differs7/18 pixels, max1. These controls do not replace the original complete references.

A single fixed baseline uses the exact composed affine inverse at destination pixel centers, source half-texel shift and four-corner byte weights. Geometry alone selects fully covered polygon-interior pixels. It is **rejected**: shape56 has176/192 interior matches and0/16 active matches in either cache state (maxRGBA[67,40,72,106]); shape57 has1121/1217 interior matches and0/96 active matches (uncached max[75,64,77,92], cached[76,64,77,92]). All native nonzero-alpha support lies in the strictly covered interior. These counterexamples cannot be assigned to mask-edge coverage. No interpolation route is chosen from RGB; no production shader changed.

[Fixed baseline and every counterexample](candidate.json), [native cache differences](boundaries.json), [source fixture](native/fixture.json), [acceptance](acceptance.json). Source-decoded texels derive only from unchanged JPEG/alpha and retain r220 exact decoder proof. The geometry partition accounts for all240000 pixels per capture, and active-support counts expose sparse transparent backgrounds rather than letting them dominate the score.

Complete diagnostic coverage remains46/54; production historical9/54 is not remeasured. `baseline_admitted=false`, `coverage_admitted=false`, `production_admitted=false`. Jinye4, Yijiao4, full AS/clip-action ownership and production binding remain open.

```sh
python3 -m tools.probes.build_jinye_leaf_boundaries --output /tmp/jinye-leaves --ffdec /path/to/ffdec-cli.jar
python3 tools/probes/capture_native_player.py /tmp/jinye-leaves /tmp/jinye-leaves/native.log --player-app '/path/to/Flash Player.app' --allow-window-activation --timeout 90
python3 -m tools.probes.analyze_jinye_leaf_boundaries --native evidence/importer-loud-fail/r221/native --output /tmp/leaf-boundaries.json
python3 -m tools.probes.analyze_jinye_smooth_leaf --native evidence/importer-loud-fail/r221/native --dump /tmp/jpeg-planes --output /tmp/leaf-candidate
python3 -m unittest tools.tests.test_jinye_smooth_leaf tools.tests.test_jinye_jpeg_source tools.tests.test_orochimaru_wrapper tools.tests.test_jpeg_row_partitions
```

Next discriminator: capture independent corner impulses and horizontal/vertical ramps using the same actual affine fill65 and outer placement, with explicit source byte readbacks. Independently vary outer scale to identity and a non-minifying value. Constrain minification footprint versus coordinate initialization before changing interpolation arithmetic; preserve both cache states and use geometry-defined interiors. Reject a common model against the old axis-aligned smooth controls and original leaf failures before any complete-wrapper/GPU admission. Draft only; no merge/deploy/Worker.
