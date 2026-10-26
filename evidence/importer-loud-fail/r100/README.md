# r100 — actual cache images close the authored Blur arithmetic boundary

Three original Jiraiya wrappers at integer offsets-128/0/128 retain source bounds, filter properties and full premultiplied readbacks through authored, cleared, cache-only, zero-blur and restored-filter states.

- Authored and cleared references remain exact at all three offsets.
- Actual cache-only images differ from cleared images at233/269/320 pixels respectively (max channel delta2). This is measured pixel behavior, not an inference from the cacheAsBitmap flag.
- Zero Blur(0,0,3) images equal cache-only images **720000/720000**. Both boundaries are independently integer-translation invariant720000/720000.
- Applying the unchanged common integer Blur15×0/quality3 to either measured cache boundary reproduces the original authored-filter images **720000/720000 exact**. The r98 explicit-input277-pixel residual disappears when using this independently observed boundary.
- Restoring Blur15×0/quality3 retains original output720000/720000.

This proves the bounded **arithmetic and observed boundary**, not how to allocate/reproduce the cache image from source texels. Production remains disabled and no native image is used as runtime input. A source-derived cache initializer/allocation must still be independently constrained before the complete GPU path is admitted.

Actual `getBounds` returns(-18.55,-48.5)..(55.45,23.7). The recorded `generateFilterRect` call receives this partly negative rectangle on a600×400 BitmapData and returns(-21,-2,98,28). That API rectangle is affected by source-bitmap clipping; it is **not** claimed to reveal the implicit display-cache allocation. Do not substitute it as the production cache origin.

## Reproduce

```sh
python3 -m tools.probes.build_jiraiya_filter_boundary --output /tmp/bvn-r100/recheck --ffdec /path/to/ffdec-cli.jar --harness tools/probes/flash_filters/jiraiya-cache-boundary.as
python3 tools/probes/capture_native_player.py /tmp/bvn-r100/recheck/components/jiraiya /tmp/bvn-r100/recheck/components/jiraiya/native.log --player-app '/path/to/Flash Player.app' --allow-window-activation --timeout 90
python3 -m tools.probes.analyze_jiraiya_cache_boundary --native evidence/importer-loud-fail/r100/native --output /tmp/bvn-r100/results
python3 -m unittest tools.tests.test_jiraiya_cache_boundary
```

[Summary](summary.json), full differing coordinates in `analysis.json.gz`, [hashes](provenance.json), original log/bounds/properties under `native/`, fifteen image readbacks under `images/`, [acceptance](acceptance.json).

Next discriminator: independent cached/uncached ramp bitmaps with varied source-mask minima, child scale/translation and outer integer/fractional draw origins. Preserve fill offsets and source bounds so local-cache initialization can be separated from final cache placement. Require one construction to retain these controls and all source-bound images; do not choose a cache origin by matching individual RGB pixels. Then connect the source-derived complete GPU wrapper.

`production_admitted=false`; historical54-suite9/54. GPU complete-wrapper binding, general affine/coverage, implicit cache allocation and full AS ownership remain open. Draft only; no merge/deploy/Worker.

Fresh Python741 pass +2skip; caches26/26, fingerprint, protected, integrity, handoff/contracts green. Full roster/Web not rerun: production unchanged.
