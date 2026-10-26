# r230: native clipping changes uncached samples at fixed coordinates

Preserve raw original shape56/57 tags, fill65/masks, six source patterns, child/outer/draw matrices and camera. Destination remains96x96. Independently vary only clipRect: omitted, explicit full96x96, or starts46/47/48 with widths1/3/4/5/16 and height96. Both cache states remain explicit.

Native capture:816images/7520256RGBA,22080exact source pixels,24matrix groups. Omitted baselines match pinnedr223 **48/48 images,442368/442368pixels**. Explicit full rectangles also match omitted **48/48**. All6234624pixels outside clips are zero.

Of6528clip pairs,720have no overlap and are not counted as evidence of equality. Among5808nonempty pairs,768change at identical output coordinates, with1722differing pixel comparisons and maximumRGBA[2,2,2,0]. All differences occur with cache=false; all2904nonempty cache=true pairs agree. This is an observation about these cache-flag controls, not proof of internal materialization or allocation.

| Uncached geometry | Changed pairs | Differing comparisons |
|---|---:|---:|
| shape56 original scale |26|28|
| shape56 scale1 |283|616|
| shape57 original scale |125|130|
| shape57 scale1 |334|948|

Every same-coordinate overlap is compared; membership does not depend on pixels. All changed coordinates/deltas and explicit argument/property readbacks remain in analysis.json.gz/native. No arithmetic candidate is modified or admitted.

## Reproduce

```sh
python3 -m tools.probes.build_jinye_clip_controls --output /tmp/bvn-r230/native --ffdec /tmp/bvn-loud-fail/r02/ffdec/ffdec-cli.jar
# Capture six source SWFs sequentially with capture_native_player.py.
python3 -m tools.probes.analyze_jinye_clip_controls --native evidence/importer-loud-fail/r230/native --output /tmp/bvn-r230/analysis.json
python3 -m unittest tools.tests.test_jinye_clip_controls tools.tests.test_jinye_clip_comparison
```

Focused tests6/6; mandatory gates in acceptance.json/checks. Retained fullPython1011pass/2skip. Production unchanged; no fresh roster/Web/54production images. Complete source-backed diagnostic coverage46/54; historical production9/54; AS/clip-action ownership open. Candidate/GPU/production admission false.

## Next discriminator

Use existing width1 clips at starts46/47/48, with no further capture. Compare all six independently defined fixed-HV coordinate models against those scalar-width outputs and full baselines at exactly the same geometry-selected coordinates, split by source/shape/scale/cache. Retain all full-image failures. Determine whether small span differences disappear while the shape56 minifying initialization error persists. Do not fit an offset or select a model per clip.
