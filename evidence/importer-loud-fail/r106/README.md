# r106 — the transformed node's cache boundary matters

30 native groups reuse the r105 source, scales, signed child origins and outer translations. Each moves cache ownership between the transformed child and its identity parent, then repeats with child translation moved into the draw matrix. All128 source texels, local/concatenated/effective matrices, bounds and both cache flags are read back; effective matrices agree across the translation routes.

Cache ownership changes native bytes: child versus parent only14825/15360 match in the original route,14932/15360 in the moved route. Moving translation also changes uncached sampling (14806/15360), so effective matrix equality alone must not be treated as raster equivalence.

**The identity-parent cache exactly matches r105's independently materialized parent draw:15360/15360.** Both use the authored-bounds floor origin, explicit local raster and integer copy; the transformed child cache does not match. This localizes the unresolved behavior to cache normalization associated with a transformed node. It does not prove a general inverse/recompose formula or admit a cache route.

## Reproduce

```sh
python3 tools/probes/build_flash_filter_probe.py --case bitmap-cache-boundary-routing --output /tmp/bvn-r106/native --ffdec /path/to/ffdec-cli.jar
python3 tools/probes/capture_native_player.py /tmp/bvn-r106/native /tmp/bvn-r106/native/native.log --player-app '/path/to/Flash Player.app' --allow-window-activation --timeout 60
python3 -m tools.probes.analyze_bitmap_cache_boundary_routing --native evidence/importer-loud-fail/r106/native --output /tmp/bvn-r106/analysis.json
python3 -m unittest tools.tests.test_bitmap_cache_boundary_routing
```

[Summary](summary.json), full native readbacks/comparisons in `analysis.json.gz`, [provenance](provenance.json), [acceptance](acceptance.json).

Next discriminator: keep the same effective scale while factoring it independently between the cached node and an uncached ancestor (child/parent scale pairs1x7,7x1,0.5x14,2x3.5 and binary-scale controls). Preserve signed translations, outer fractions, explicit source and matrix readbacks. Compare whether cache differences follow the cached node's local transform or its concatenated transform before proposing a common inverse/recomposition sequence. Retain old controls; no formula or origin selected from RGB.

`candidate_admitted=false`, `production_admitted=false`; no production/GPU changes. Components historical9/54. Cache normalization, general affine/coverage and full AS/clip-action ownership remain merge blockers. Draft only; no merge/deploy/Worker.
