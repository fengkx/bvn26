# r220 — Jinye source graph, exact decoder and native cache boundaries

The remaining Jinye component is a21-frame cached sprite with eleven overlapping depth instances. The locked graph retains231 placement/move/replacement/removal events, original matrices, shape56→57→56 transitions and removal of every child at frame21. Root frame41 retains ratio40 and cacheAsBitmap; neither ratio consumption nor dormant stream metadata is declared implemented. Two authored shapes use active fill65 (clipped, smoothed), affine bitmap matrices and quadrilateral masks. The unused bitmap65535 style remains recorded and is not rendered as an active fill.

Bitmap55's original92×40 JPEG3 now has independent native loadBitmap readback: **3680/3680 RGBA exact**, using the unchanged r218 scaled-plane decoder and eight-pixel row route. Alpha is source-derived binary0×3531/255×149; native pixels are comparison-only. This proves decoding, not smooth affine sampling or the complete renderer.

Fresh explicit authored/uncached/cache/stage captures preserve **48/48 original clocks** and **4/4 original complete native images,960000/960000 RGBA**. Authored equals explicit cache and normal composition reproduces the gray stage. Cache versus uncached differs **174 pixels** (tick0/10/20/23:25/101/0/48), maximum RGBA deltas[2,1,1,2]. Tick20 is empty; native getBounds sentinel6710886.35 is recorded as an empty state and must not become an allocation size. No approximate renderer is admitted.

[Source inventory](inventory.json), [bounded source XML](jinye-bounded.xml), [boundary measurements](boundaries.json), [decoder comparison](jpeg/analysis/summary.json), [acceptance](acceptance.json). The inventory's required-rendering list records source requirements before decoder measurement; the separate decoder report clears only its JPEG entry. Source-backed complete diagnostics remain46/54; Jinye4 and Yijiao4 still unbound. Historical production9/54 has not been remeasured; `production_admitted=false`. Full AS/clip-action ownership remains open.

```sh
java -Djava.awt.headless=true -jar /path/to/ffdec-cli.jar -swf2xml game/fighter/fz/jinye.swf /tmp/jinye.xml
python3 -m tools.probes.inventory_jinye_component --xml /tmp/jinye.xml --output /tmp/jinye-inventory.json
python3 -m tools.probes.build_cached_component_boundaries --cases evidence/importer-loud-fail/r32/components/jinye/cases.json --case jinye-0-41-1 --output /tmp/jinye-native --ffdec /path/to/ffdec-cli.jar
python3 tools/probes/capture_native_player.py /tmp/jinye-native/components/jinye /tmp/jinye-native/components/jinye/native.log --player-app '/path/to/Flash Player.app' --allow-window-activation --timeout 90
python3 -m tools.probes.analyze_cached_component_boundaries --native evidence/importer-loud-fail/r220/native --output /tmp/jinye-boundaries.json
python3 -m tools.probes.jinye_jpeg_source build --output /tmp/jinye-jpeg --ffdec /path/to/ffdec-cli.jar
python3 tools/probes/capture_native_player.py /tmp/jinye-jpeg /tmp/jinye-jpeg/native.log --player-app '/path/to/Flash Player.app' --allow-window-activation --timeout 90
python3 -m tools.probes.jinye_jpeg_source analyze --native evidence/importer-loud-fail/r220/jpeg/native --dump /tmp/jpeg-planes --output /tmp/jinye-decoder
python3 -m unittest tools.tests.test_jinye_component_inventory tools.tests.test_cached_component_boundaries tools.tests.test_jinye_jpeg_source
```

Next discriminator: isolate one active Jinye fill65 leaf at its actual source bitmap/placement matrices, retaining the quadrilateral mask and source-decoded texels. Capture native cache and uncached boundaries before attempting eleven-layer composition. Separate smooth affine interpolation from edge coverage using geometry-defined interior samples; do not route from output RGB. Only after exact leaf/cache evidence may the complete animated graph be bound. Keep r219 wrappers and all old sampler/matrix/decoder controls exact. Draft only; no merge/deploy/Worker.
