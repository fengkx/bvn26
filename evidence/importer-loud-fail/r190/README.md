# r190 — affine cache alpha allocation uses separate geometry and translation

Independent constant-source bitmap/vector rectangles retain actual matrices and source bytes; compare uncached, cacheAsBitmap and alpha-revealing ColorMatrix paths. All27621 source texels,198 cases and20 filter properties are retained. Fresh uncached controls preserve **161350/161350 pixels**; bitmap/vector pairs match **242025/242025**.

All66 revealed alpha supports are solid opaque rectangles. One geometry-derived construction predicts **66/66 bounds**: round local transformed corners to quarter pixels, floor/ceil their minima/maxima separately, add floored consumed translation, and extend the upper bound by one pixel. Combining geometry and translation before integer bounds matches22/66; omitting the upper extension matches12/66. This constrains allocation only, not cache-local sampling or internal implementation.

Color is deliberately not claimed: only12/66 rectangles are uniformly(57,148,230,255). Others also contain(205,0,230,255), including transparent source regions revealed by the filter. Complete raw readbacks and color counts are retained. Alpha support remains exact independently; do not silently treat these as the requested RGB.

[Support/properties/color counts](summary.json), [native](native/native.log.gz), [provenance](provenance.json), [acceptance](acceptance.json).

```sh
python3 tools/probes/build_flash_filter_probe.py --case affine-cache-support --output /tmp/affine-cache-support --ffdec /path/to/ffdec-cli.jar
python3 tools/probes/capture_native_player.py /tmp/affine-cache-support /tmp/affine-cache-support/native.log --player-app '/path/to/Flash Player.app' --allow-window-activation --timeout 90
python3 -m tools.probes.analyze_affine_cache_support --native evidence/importer-loud-fail/r190/native --output /tmp/affine-cache-support.json
python3 -m unittest tools.tests.test_affine_cache_support
```

Next discriminator: keep these transforms/allocation controls and replace constant RGB with independently read coordinate-coded opaque texels. Compare native uncached/cache sampling using one extension of the previously measured device-space cache-origin construction; preserve signed/rotated matrices and original-main transform. Distinguish inverse-origin rounding/composition globally before applying to real components. Treat alpha-zero filter color behavior separately; no color-selected coordinate route.

`cache_allocation_admitted=false`, `production_admitted=false`. Main cached boundary still6 failures; full authored wrapper10; production54 historical9/54. AS ownership open. No production changes. Draft only.
