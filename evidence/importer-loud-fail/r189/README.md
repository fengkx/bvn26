# r189 — uncached original wrapper is exact; cache/filter boundaries still reject

Reuse source graph, actual owner transform, shape282/290 raw texels, clipped nearest masks and verified r157 natural clocks. Frame17 removes the display slot and stops; both empty observations remain explicitly clear. Preserve authored fixed RGB CXFORM(57,148,230) and all20 ColorMatrix property readbacks.

The unchanged sampler/coverage plus tint-before-coverage construction matches the uncached boundary **960000/960000 pixels** across four observations. Multiplying tint by(alpha+1)/256 is indistinguishable here; multiplying by alpha/255 leaves4 byte counterexamples. No internal order is inferred where outputs coincide.

The same uncached result **does not** reproduce cached output:6 pixels differ (4 at tick0,2 at tick8), maxRGBA delta255. Against authored filtered output,10 differ (8+2). All coordinates/native values are retained. These failures are intentional gates, not hidden by the passing uncached claim. No complete wrapper or production binding.

[Full comparisons/source properties](summary.json), [pinned native boundaries](../r157/main/native.log.gz), [provenance](provenance.json), [acceptance](acceptance.json).

```sh
python3 -m tools.probes.analyze_nearest_wrapper_boundaries --output /tmp/nearest-wrapper-boundaries.json
python3 -m unittest tools.tests.test_nearest_wrapper_boundaries
```

Next discriminator: independently expose affine cache allocation using constant-source bitmap/vector rectangles and an alpha-revealing ColorMatrix, retaining actual matrix/filter/cache properties. Vary signed/sheared transforms and child/draw translations separately. Constrain allocation and cache-local origin before applying ColorMatrix or fitting any original-source pixel; preserve old exact uncached controls.

`cache_boundary_admitted=false`, `complete_wrapper_admitted=false`, `production_admitted=false`. Production54 historical9/54;24 complete live/wrapper images exact. Full AS/clip-action ownership open. Draft only; no production changes.
