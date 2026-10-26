# r107 — local scale alone cannot select cache normalization

48 native cases factor total X scale7 into child/ancestor pairs1x7,7x1,0.5x14,2x3.5, and total scale8 into1x8,8x1,0.5x16,2x4. Ancestor translations[-0.5,0,0.5] and outer draw origins128/256.5 are retained. Explicit source128 texels, local/ancestor/concatenated matrices, bounds and both cache flags are read back. The root wrapper is drawn so the ancestor's own transform is actually consumed.

For each total scale, **uncached and child-cached outputs remain12288/12288 identical across all four factorizations**. Parent-cached outputs do not:11537/12288 at total7,11800/12288 at total8. The cached child's local scale changes while its concatenated mapping remains fixed, rejecting a local-scale-only selector. Moving the boundary above the internal child transform changes native sampling even with binary total scale8; this cannot be reduced to reciprocal7 alone.

No arithmetic model or production route is admitted. The first generated scratch harness failed compilation before any capture (a function body was truncated by the generator); the corrected complete harness and successful run are the only native evidence used.

## Reproduce

```sh
python3 tools/probes/build_flash_filter_probe.py --case bitmap-cache-scale-factors --output /tmp/bvn-r107/native --ffdec /path/to/ffdec-cli.jar
python3 tools/probes/capture_native_player.py /tmp/bvn-r107/native /tmp/bvn-r107/native/native.log --player-app '/path/to/Flash Player.app' --allow-window-activation --timeout 60
python3 -m tools.probes.analyze_bitmap_cache_scale_factors --native evidence/importer-loud-fail/r107/native --output /tmp/bvn-r107/analysis.json
python3 -m unittest tools.tests.test_bitmap_cache_scale_factors
```

[Summary](summary.json), full readbacks in `analysis.json.gz`, [provenance](provenance.json), [acceptance](acceptance.json).

Next discriminator: explicitly materialize the parent-cache input for each scale factorization using the same bounds-origin construction, retaining the internal child transform. Compare those local buffers and their integer placement against the native parent cache before testing any inverse/recomposition sequence. The prior identity-parent result must generalize or produce a precise counterexample; keep source bytes, signed phases and binary-scale controls. No local-scale route or origin selected from RGB.

`candidate_admitted=false`, `production_admitted=false`; no runtime/GPU changes. Components historical9/54, source cache normalization and full AS/clip-action ownership remain merge blockers. Draft only; no merge/deploy/Worker.
