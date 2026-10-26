# r143 — scalar fill-translation controls exact but operation order unresolved

Fresh native controls fix an8×8 rectangle, use an explicitly read horizontal-red/vertical-green/constant-blue source, and vary fractional fill-matrix translation independently of child scale1/1.25/3/5 and integer draw translation. Single-pixel clips at independently varied X/Y locations eliminate bulk-span routing. Source64 texels and all1152 source/matrix/output readbacks are retained.

All three predeclared constructions clear **1152/1152**: subtract fill translation after fixed inverse, compose fill translation before fixed translation rounding, and consume fill translation in twips before composition. Their predictions coincide on these controls. This **does not** identify one sequence or explain Lanran's retained source-image differences; no candidate is admitted.

[Summary with complete native samples](summary.json), [provenance](provenance.json), [acceptance](acceptance.json).

```sh
python3 tools/probes/build_flash_filter_probe.py --case bitmap-fill-translation-scalar --output /tmp/fill-translation --ffdec /path/to/ffdec-cli.jar
python3 tools/probes/capture_native_player.py /tmp/fill-translation /tmp/fill-translation/native.log --player-app '/path/to/Flash Player.app' --allow-window-activation --timeout 90
python3 -m tools.probes.analyze_fill_translation_scalar --native evidence/importer-loud-fail/r143/native --output /tmp/fill-translation.json
python3 -m unittest tools.tests.test_fill_translation_scalar
```

Next discriminator: native cross-API source construction. Feed the exact original Lanran bitmap7 bytes and shape8 fill/rectangle coordinates through AS `beginBitmapFill` while retaining the original SWF-tag shape in a separate control, identical child/draw transforms and independently read source bytes. Compare authored/clear/cache boundaries at the original first frame. Do not assume AS drawing and SWF-tag fill-matrix consumption are equivalent from numeric properties alone; then isolate non-quarter geometry coverage if needed.

`fill_translation_admitted=false`, `production_admitted=false`. No component counts changed; eight source-backed live original images exact, production54 historical9/54. Original Lanran source input still rejects as r142 records. Full AS/clip-action ownership and general affine/coverage remain open. Draft only; no merge/deploy/Worker.
