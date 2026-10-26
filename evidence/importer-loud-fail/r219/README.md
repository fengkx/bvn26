# r219 — complete source-derived Orochimaru wrappers exact

The unchanged original JPEG3 bitmap340 now feeds the diagnostic sampler directly from decoded source planes and source alpha. Five authored placements retain fill67, the original rectangle mask, inner/outer translations, non-unit capture transform, BlurY20 and cache bounds. The existing nearest affine coverage shader feeds actual FilterGroup allocation and integer Blur/composition; native reference pixels are never uploaded as source textures.

All **15 local/input/filtered boundaries are exact,702535/702535 RGBA pixels**, followed by **10/10 pinned complete images,2400000/2400000 RGBA pixels**. Fresh native captures independently preserve Blur properties and reproduce the original complete references10/10; their clear/cache comparisons are3600000/3600000 exact. This admits only the isolated diagnostic, not production. The older r22 stripped-input capture is not interchangeable with these explicit boundaries and was not substituted.

[GPU comparisons](gpu/report.json), [source/readback hashes](gpu/provenance.json), [native properties and comparisons](native-boundaries.json), [coverage inventory](inventory.json), [acceptance](acceptance.json). Binary source textures and coefficient maps regenerate from locked source; only measurement PNGs/metadata are committed. Exact source plane hashes retain r218. No source, reference, production shader or generated gameplay asset changed.

Source-backed complete diagnostic coverage rises **36/54→46/54**. Remaining8: Jinye4 and Yijiao ColorMatrix4. Historical production remains9/54; no new production54 run is claimed. `production_admitted=false`; full AS/clip-action ownership and production binding still block merge.

The JPEG retained comparator now rejects missing cases, rows, row values, reordered rows and missing completion markers, preventing zip truncation from falsely passing an incomplete capture. Retained JPEG controls11/11 and sampler/matrix checks9/9 pass; the original494424/494424 decoder results remain unchanged.

```sh
# Repeat each of the five IDs from the pinned cases file.
python3 -m tools.probes.build_component_cache_boundaries --cases evidence/importer-loud-fail/r32/components/orochimaru/cases.json --case orochimaru-356-1-2 --output /tmp/orochimaru-native/orochimaru-356-1-2 --ffdec /path/to/ffdec-cli.jar
python3 tools/probes/capture_native_player.py /tmp/orochimaru-native/orochimaru-356-1-2/components/orochimaru /tmp/orochimaru-native/orochimaru-356-1-2/components/orochimaru/native.log --player-app '/path/to/Flash Player.app' --allow-window-activation --timeout 90
cc -Wall -Wextra -Werror tools/probes/jpeg_scaled_planes.c -I/opt/homebrew/opt/libjpeg-turbo/include -L/opt/homebrew/opt/libjpeg-turbo/lib -ljpeg -o /tmp/jpeg-planes
python3 -m tools.probes.run_orochimaru_wrapper --dump /tmp/jpeg-planes --godot /path/to/Godot --native evidence/importer-loud-fail/r219/native --output /tmp/orochimaru-wrapper
python3 -m unittest tools.tests.test_orochimaru_wrapper tools.tests.test_component_diagnostic_inventory tools.tests.test_jpeg_row_partitions
python3 -m tools.probes.inventory_component_diagnostics --include-orochimaru --output /tmp/components.json
```

Next discriminator: inventory Jinye's remaining21-frame cached graph from locked tags, retaining ratio40, source transforms, clip actions and nested layer lifetimes. Capture explicit native authored/uncached/cache boundaries with original clocks before selecting a bounded sampler or filter path. Identify every bitmap/fill/mask and prove source decoding first; do not assume cacheAsBitmap alone implies the same materialization as Orochimaru. Keep all admitted decoder/sampler/matrix controls exact. Draft only; no merge/deploy/Worker.
