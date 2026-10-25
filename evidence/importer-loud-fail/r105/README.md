# r105 — explicit cache materialization isolates the remaining input boundary

30 native controls keep source16x8, scales5/7, signed child origins[-1,-0.5,0,0.5,0.95] and outer origins128/128.25/256.5. Each captures uncached and implicit-cache rows, then explicitly materializes a128x16 bitmap with authored-bounds floor origin. Two globally fixed constructions are tested:

- Draw the parent using outer translation minus the integer bounds origin, retaining its child transform.
- Draw the child directly with composed scale and translation minus that origin.

Each explicit bitmap is read back before attachBitmap and integer placement onto a transparent destination. Source128 texels, local matrices and all intermediate rows are retained. Comparisons use native getPixel32 ARGB equality (not invented premultiplied bytes); no filter arithmetic is inferred from transparent-edge unpremultiplied values.

**Integer placement preserves15360/15360 pixels for each construction.** But the parent construction matches implicit cache only14825/15360; direct-child only14699/15360. Against uncached these are14985 and14506 respectively. Therefore neither explicit source-raster construction is admitted. The mismatch precedes the tested integer texture-placement boundary; this does not establish general fractional cache composition.

## Reproduce

```sh
python3 tools/probes/build_flash_filter_probe.py --case bitmap-cache-materialized --output /tmp/bvn-r105/native --ffdec /path/to/ffdec-cli.jar
python3 tools/probes/capture_native_player.py /tmp/bvn-r105/native /tmp/bvn-r105/native/native.log --player-app '/path/to/Flash Player.app' --allow-window-activation --timeout 60
python3 -m tools.probes.analyze_bitmap_cache_materialized --native evidence/importer-loud-fail/r105/native --output /tmp/bvn-r105/analysis.json
python3 -m unittest tools.tests.test_bitmap_cache_materialized
```

[Summary](summary.json), all original/intermediate bytes and mismatch coordinates in `analysis.json.gz`, [provenance](provenance.json), [acceptance](acceptance.json).

Next discriminator: preserve the same effective affine mapping while moving the cache boundary between child and identity parent, and separately move translation between the child and outer draw matrix. Capture actual local/concatenated matrices, bounds and flag readbacks for every construction. Establish which boundary changes source sampling before proposing a shared cache normalization; do not select an origin or correction from whichever pixel matches. Reject candidates against all existing cached and uncached controls.

`candidate_admitted=false`, `production_admitted=false`. No GPU or production changes. Components remain historical9/54; source cache normalization, general affine/coverage and full AS/clip-action ownership still block merge. Draft only; no merge/deploy/Worker.
