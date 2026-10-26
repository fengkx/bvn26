# r191 — opaque cache coordinates reject rounded products but do not separate initializers

Keep r190 geometry/matrices/cache properties and replace constant RGB with explicit opaque coordinate-coded texels(R=x,G=y,B=73). All27621 source readbacks match. Each case is captured twice with the same bitmap path; **242025/242025 replicate pixels** agree. These are temporal/storage-path replicates, not bitmap/vector comparisons.

Geometry-only fully covered selection retains **61756/61756 uncached pixels**. Cached baseline(consume translation minus independently measured allocation origin) and one float32 inverse-origin/forward-composition construction with rounding after each dot sum both match **61756/61756**. Rounding each product before its sum rejects258 pixels,maxdelta1. No locally selected route or fitted coefficient.

These inputs do not distinguish the two surviving constructions. The real indexed/binary-alpha main cache still has6 failures; this opaque AS input pass cannot clear it. No initializer or production admission.

[Scores/translations](summary.json), [counterexamples](failures.json.gz), [native](native/native.log.gz), [provenance](provenance.json), [acceptance](acceptance.json).

```sh
python3 tools/probes/build_flash_filter_probe.py --case affine-cache-coordinates --output /tmp/affine-cache-coordinates --ffdec /path/to/ffdec-cli.jar
python3 tools/probes/capture_native_player.py /tmp/affine-cache-coordinates /tmp/affine-cache-coordinates/native.log --player-app '/path/to/Flash Player.app' --allow-window-activation --timeout 90
python3 -m tools.probes.analyze_affine_cache_coordinates --native evidence/importer-loud-fail/r191/native --output /tmp/affine-cache-coordinates.json
python3 -m unittest tools.tests.test_affine_cache_coordinates
```

Next discriminator: preserve the original main shape/fill and transform, independently encode horizontal/vertical coordinate ramps as format3 indexed bitmaps versus byte-identical AS materialization, with original binary alpha versus all-opaque alpha. Read every input byte and compare uncached/cache paths. Separate storage/alpha routing from cache-origin arithmetic before applying either surviving construction to real pixels.

`cache_initializer_admitted=false`, `production_admitted=false`. Production54 historical9/54; complete main wrapper and full AS ownership remain open. Draft only; no production changes.
