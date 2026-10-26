# r113 — remaining phase errors follow geometry, not fill translation

252 native cases independently vary bitmap fill translation and geometry bounds at scale7 and1.24481201171875, signed node translations and fractional outer origins. All480 source texels, fill matrix properties, node/draw transforms and actual bounds are retained.

| Construction | Uncached model | Unchanged r112 cache candidate |
|---|---:|---:|
| Fixed geometry[-4,64], fill translation varies |17934/17934|**17934/17934**|
| Geometry and fill translation move together |17934/17934|16482/17934|
| Geometry moves, fill translation stays0 |17934/17934|16482/17934|

The latter two share the same four failing geometry/transform groups,363 interior samples each, maximum delta19. All are scale7: minimum-0.5/inner-0.5/outer128; minimum0.25/inner-0.5 or0.5/outer128; minimum0.5/inner-0.5/outer128. Zero-fill counterexamples reject a fill-specific arithmetic splice; fixed-bounds nonzero-fill controls are exact without changing interpolation.

Native getBounds rounds projected geometry to twips at the noninteger scale. The initial analyzer incorrectly expected an unrounded real product and rejected the capture; it was corrected to assert the observed fixed-matrix twip projection for every case. The cache candidate still uses recorded bounds and the unchanged r112 construction. No native data or reference changed, and these bounds readbacks do not establish hidden cache-buffer allocation.

## Reproduce

```sh
python3 tools/probes/build_flash_filter_probe.py --case bitmap-cache-fill-bounds --output /tmp/bvn-r113/native --ffdec /path/to/ffdec-cli.jar
python3 tools/probes/capture_native_player.py /tmp/bvn-r113/native /tmp/bvn-r113/native/native.log --player-app '/path/to/Flash Player.app' --allow-window-activation --timeout 60
python3 -m tools.probes.analyze_bitmap_cache_fill_bounds --native evidence/importer-loud-fail/r113/native --output /tmp/cache-fill-bounds.json
python3 -m unittest tools.tests.test_bitmap_cache_fill_bounds
```

[Summary](summary.json), all coordinates/readbacks in `analysis.json.gz`, [provenance](provenance.json), [acceptance](acceptance.json).

Next discriminator: query native transform pixel bounds before/after cache materialization, retaining getBounds and explicit root/parent draw equivalence controls. Determine whether that API exposes the relevant raster origin; if unavailable or not equivalent, retain the failure rather than substituting zeros. In parallel with those observations, trace static writes to the cached geometry fields before the device-grid shift. No inferred padding, origin correction or fill route may be selected from RGB.

`candidate_admitted=false`, `production_admitted=false`; no GPU or production advance. Components historical9/54. Cache geometry normalization, general affine/coverage and full AS/clip-action ownership remain merge blockers. Draft only; no merge/deploy/Worker.
