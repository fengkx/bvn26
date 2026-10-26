# r104 — binary matrix readbacks reject the tested roundtrip explanations

240 fixed-width16 controls sweep child translation from -1 through0.95 in twips, scales5/7 and outer draw origins128/128.25/256.5. All128 source texels are verified. Each case records the same source/cached/uncached outputs plus53-bit binary significands and exponents for15 public Matrix inverse/forward and reciprocal intermediates. The default15-digit decimal trace is not used to infer their precision.

The public child inverse/inverse roundtrip changes bits in120/240 cases; the composed roundtrip changes64/240. These are real observable numerical changes, but **none of the four globally fixed roundtrip/division sequences improves the cached pixels**: each is16379/19980, identical to the old baseline. Uncached remains19980/19980 exact. Applying nearest-quarter consumption after these public operations makes their tested translations identical; their presence does not establish the hidden renderer's operation order.

No per-case coefficient, origin or output-selected route is admitted. These controls do not prove that hidden cache arithmetic is identical to public Matrix methods, nor exclude every floating-point construction.

## Reproduce

```sh
python3 tools/probes/build_flash_filter_probe.py --case bitmap-cache-matrix-bits --output /tmp/bvn-r104/native --ffdec /path/to/ffdec-cli.jar
python3 tools/probes/capture_native_player.py /tmp/bvn-r104/native /tmp/bvn-r104/native/native.log --player-app '/path/to/Flash Player.app' --allow-window-activation --timeout 60
python3 -m tools.probes.analyze_bitmap_cache_matrix_bits --native evidence/importer-loud-fail/r104/native --output /tmp/bvn-r104/analysis.json
python3 -m unittest tools.tests.test_bitmap_cache_matrix_bits
```

[Summary](summary.json), full coordinates and binary intermediates in `analysis.json.gz`, [provenance](provenance.json), [acceptance](acceptance.json).

Next discriminator: materialize the two raster boundaries independently at fixed signed child phases and outer fractions. Draw the child into a local bitmap using an explicitly read-back matrix, then attach/draw that bitmap through the outer transform; compare with the original implicit cache and with a direct uncached draw. Preserve each intermediate bitmap and test globally fixed bounds/translation constructions, rather than deducing a phase correction from RGB. This separates cache-input rasterization from cache-texture placement/resampling. Retain r101–r104 and earlier exact sampler controls as rejection constraints.

`candidate_admitted=false`, `production_admitted=false`; no GPU advance. Historical components9/54; source-derived cache normalization, general affine/coverage, production composition and full AS/clip-action ownership remain open. Draft only; no merge/deploy/Worker.
