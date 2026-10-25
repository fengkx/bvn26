# r118 — consumed local endpoints clear the held-out bounds without changing their rule

Fresh capture repeats all r117 cases and adds local `getBounds(child)` before applying any transform. Removing only these new observation events leaves every prior event payload unchanged: **768000/768000 row pixels**, properties, source bytes and columns are retained exactly.

The16 r117 right-edge counterexamples came from the consumed drawing endpoint: minimum-1.05 plus width1.25 does not produce the ideal mathematical decimal0.2 after AS2 drawing-to-twip conversion. A single toward-zero integer-twip conversion matches **960/960 local endpoint pairs**. No epsilon, decimal rounding correction or special case is introduced. The r116 support formula, unchanged and supplied independently read local endpoints, now matches **480/480** held-out supports. Cache interiors remain the r11729494/29494 exact result.

These controls prove bounded local endpoint consumption and support measurements, not a general production cache implementation. RGB does not select the origin or arithmetic route.

## Reproduce

```sh
python3 tools/probes/build_flash_filter_probe.py --case bitmap-cache-support-local --output /tmp/bvn-r118/native --ffdec /path/to/ffdec-cli.jar
python3 tools/probes/capture_native_player.py /tmp/bvn-r118/native /tmp/bvn-r118/native/native.log --player-app '/path/to/Flash Player.app' --allow-window-activation --timeout 60
python3 -m tools.probes.analyze_bitmap_cache_support_local --native evidence/importer-loud-fail/r118/native --output /tmp/support-local.json
python3 -m unittest tools.tests.test_bitmap_cache_support_local
```

[Summary](summary.json), full observations in `analysis.json.gz`, [provenance](provenance.json), [acceptance](acceptance.json).

Next discriminator: apply the source-derived left bound and unchanged r112 normalization to every old r101/r102/r103/r104/r109/r113 cache-only reference, preserving original interior masks and source bytes. Any remaining failure must reject admission; do not splice the former origin back into locally matching cases. Only after those pass should the original Jiraiya cached input be measured, before filter or GPU work.

`source_cache_initializer_admitted=false`, `production_admitted=false`; components historical9/54. General affine/coverage and AS/clip-action ownership remain open. Draft only; no merge/deploy/Worker.

Validation: focused Python2/2; prior r115 full771 pass+2skip retained. Fresh caches26/26, fingerprint, protected, integrity/handoff/contracts green. No runtime change; roster/Web and GPU/component renders not rerun.
