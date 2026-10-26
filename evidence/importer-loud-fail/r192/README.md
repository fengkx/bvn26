# r192 — indexed versus AS storage agrees; cache coordinate differences survive

Keep original Shape282/fill67/mask/placement transform. In separate synthetic SWFs replace only Bitmap281 with independent horizontal/vertical indexed coordinate ramps, each with original binary alpha or all-opaque alpha. All109600 explicit source texels match; every other source tag remains byte-identical. Fresh AS materialization uses those same bytes. Synthetic controls never replace original references.

Indexed/AS native images agree **1920000/1920000 pixels** across cached and uncached paths. The unchanged uncached sampler/coverage model also matches **1920000/1920000 uncached pixels**. Thus source encoding does not explain this measured cache difference.

Cached versus uncached differs48 pixels for opaqueX,22 opaqueY(maxdelta1),14 binary-alphaX and6 binary-alphaY(maxdelta255), identically for both storage paths. Full coordinates and values are retained. The alpha differences follow source index transitions; no alpha-dependent sampling route is selected.

[Comparisons](summary.json), [native/input captures](native), [provenance](provenance.json), [acceptance](acceptance.json).

```sh
python3 -m tools.probes.build_indexed_nearest_cache --output /tmp/indexed-nearest-cache --ffdec /path/to/ffdec-cli.jar
# Capture each x-opaque/x-original/y-opaque/y-original folder with capture_native_player.py.
python3 -m tools.probes.analyze_indexed_nearest_cache --native evidence/importer-loud-fail/r192/native --output /tmp/indexed-nearest-cache.json
python3 -m unittest tools.tests.test_indexed_nearest_cache
```

Next discriminator: apply the two surviving r191 cache-local origin constructions unchanged to these complete cached images, preserving geometry coverage and recomputing fixed inverse coefficients in cache-local coordinates. Do not algebraically substitute globally rounded translation coefficients: rounding need not commute with rebasing. Then reject against original r157 cached boundaries before any GPU/cache admission.

`cache_initializer_admitted=false`, `production_admitted=false`. Main original cache6/filtered10 failures still open; production54 historical9/54. Full AS ownership remains separate. Draft only; no production changes.
