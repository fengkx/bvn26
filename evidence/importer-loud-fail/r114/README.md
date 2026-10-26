# r114 — public pixel bounds do not reveal hidden cache allocation

16 native cases cover the four failing geometry minima and signed child translations at scale7. The probe captures transform.pixelBounds before and after each uncached/cached draw, plus getBounds and concatenated matrices. A paired route moves outer translation into an actual parent transform and draws the root, so public stage-relative bounds can be compared with the target image coordinates.

Both draw routes match **6400/6400 uncached and6400/6400 cached RGB samples**. Public bounds are unchanged for all64 before/after observations. The failing minimum-0.5/inner-0.5 case reports x124 in the root route, but this public value does not establish the internal cache raster origin or explain the candidate's phase error.

The API truncates fractional coordinates toward zero in this bounded suite: x-0.5 reports0, whereas translating it by128 reports127. Thus the initial expectation that all public rectangles simply translate by128 was rejected; only7/8 do. The analyzer retains this counterexample and explicitly checks the observed truncation rather than treating the API as a hidden allocation oracle. All source480 texels and original images remain unchanged.

## Reproduce

```sh
python3 tools/probes/build_flash_filter_probe.py --case bitmap-cache-pixel-bounds --output /tmp/bvn-r114/native --ffdec /path/to/ffdec-cli.jar
python3 tools/probes/capture_native_player.py /tmp/bvn-r114/native /tmp/bvn-r114/native/native.log --player-app '/path/to/Flash Player.app' --allow-window-activation --timeout 60
python3 -m tools.probes.analyze_bitmap_cache_pixel_bounds --native evidence/importer-loud-fail/r114/native --output /tmp/cache-pixel-bounds.json
python3 -m unittest tools.tests.test_bitmap_cache_pixel_bounds
```

[Summary](summary.json), all property/image readbacks in `analysis.json.gz`, [provenance](provenance.json), [acceptance](acceptance.json).

Next discriminator: use an identity ColorMatrix filter as an explicit unchanged-image control, then a ColorMatrix that maps transparent input to an opaque constant to expose the allocated filtered rectangle. Preserve source bytes, transforms, filter property readbacks and independent fresh instances. Establish whether identity-filter materialization matches cache-only output before interpreting the revealed rectangle; adding a filter may change allocation, so no equivalence is assumed. Do not infer padding from whichever origin matches RGB.

`hidden_cache_allocation_verified=false`, `candidate_admitted=false`, `production_admitted=false`. Components historical9/54, no GPU/production change. Cache normalization and full AS/clip-action ownership remain merge blockers. Draft only; no merge/deploy/Worker.
