# r108 — explicit normalization does not generalize to transformed parent caches

48 scale-factorization cases retain the r107 source, local/concatenated transforms, signed phases and binary-scale controls. Fresh uncached/child-cache/parent-cache readbacks match the prior73728/73728 ARGB samples. Two explicit local raster constructions use the authored-bounds floor origin:

1. Draw the parent with its scale and combined local translation in the supplied draw matrix, retaining its internal child transform.
2. Draw the root with shifted outer translation, retaining both parent and child transforms.

Both read back each local160x16 bitmap and its integer attachBitmap placement. Integer copies are24576/24576 exact for each construction. Both match parent cache only23553/24576, child cache22744/24576. Thus the identity-parent construction from r106 does not generalize. Counterexamples include total scale8 with parent scale8/16 as well as total7; reciprocal7 alone is not a sufficient explanation. All mismatches remain recorded, including edge ARGB changes; this is equality of native readbacks, not inferred premultiplied filter arithmetic.

## Reproduce

```sh
python3 tools/probes/build_flash_filter_probe.py --case bitmap-cache-factor-materialized --output /tmp/bvn-r108/native --ffdec /path/to/ffdec-cli.jar
python3 tools/probes/capture_native_player.py /tmp/bvn-r108/native /tmp/bvn-r108/native/native.log --player-app '/path/to/Flash Player.app' --allow-window-activation --timeout 60
python3 -m tools.probes.analyze_bitmap_cache_factor_materialized --native evidence/importer-loud-fail/r108/native --output /tmp/bvn-r108/analysis.json
python3 -m unittest tools.tests.test_bitmap_cache_factor_materialized
```

[Summary](summary.json), original and intermediate bytes in `analysis.json.gz`, [provenance](provenance.json), [acceptance](acceptance.json).

Next discriminator: extend geometry bounds to the left with alpha-zero shapes while keeping the visible bitmap fill and every transform unchanged. Sweep signed integer/fractional bounds minima in the failing scale7/8 cases; verify native getBounds and uncached visible-prefix invariance. Compare whether implicit cache changes follow the bounds-origin shift before proposing a shared normalization. Do not choose an origin from RGB; keep old bounds and scale controls.

`candidate_admitted=false`, `production_admitted=false`. No GPU or runtime advance. Components historical9/54; source cache normalization, general affine/coverage and full AS/clip-action ownership remain open. Draft only; no merge/deploy/Worker.
