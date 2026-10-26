# r109 — left bounds independently change cache sampling

144 native cases hold the visible16x8 bitmap fill and every transform fixed while extending geometry to minima0/-0.5/-1/-2/-4/-8. Total scales7/8, signed child phases and outer draw fractions are retained. A separate rectangle is either alpha-zero or opaque; native bounds verify identical minima for both constructions. All128 source texels remain unchanged.

The visible interior's uncached samples stay **7524/7524** identical in each opacity construction. Cached samples match only7202/7524, with12 changed groups each. Alpha-zero and opaque extensions produce the same pattern of changes. Thus bounds affect this cache input even without changing the visible texture mapping; the result is not an RGB-dependent selector.

At minimum-0.5, three scale7 groups shift their whole tested interior. At minima-4/-8, some scale7 groups differ at only1–5 pixels. Scale8 controls remain invariant here despite the prior transformed-cache counterexamples. Exact coordinate lists and original ARGB values are retained; no tolerance or correction is admitted.

## Reproduce

```sh
python3 tools/probes/build_flash_filter_probe.py --case bitmap-cache-left-bounds --output /tmp/bvn-r109/native --ffdec /path/to/ffdec-cli.jar
python3 tools/probes/capture_native_player.py /tmp/bvn-r109/native /tmp/bvn-r109/native/native.log --player-app '/path/to/Flash Player.app' --allow-window-activation --timeout 60
python3 -m tools.probes.analyze_bitmap_cache_left_bounds --native evidence/importer-loud-fail/r109/native --output /tmp/bvn-r109/analysis.json
python3 -m unittest tools.tests.test_bitmap_cache_left_bounds
```

[Summary](summary.json), complete per-coordinate changes in `analysis.json.gz`, [provenance](provenance.json), [acceptance](acceptance.json).

Next discriminator: compare globally defined inverse/recomposition sequences for a bounds-relative raster matrix, retaining binary-scale counterexamples and all old origin controls. Independently inspect the installed player's static affine/coordinate conversion arithmetic if useful; record exact binary hashes/operation constants and do not infer executed routing from static agreement. A construction must explain both whole-interior phase shifts and distant single-byte changes before any GPU advance. Feasible output intervals are rejection constraints, never coefficient sources.

`candidate_admitted=false`, `production_admitted=false`. Components historical9/54. Cache normalization, general affine/coverage and full AS/clip-action ownership remain merge blockers. Draft only; no merge/deploy/Worker.
