# r131 — original Yulong Glow arithmetic is exact with complete property readbacks

Fresh original Yulong345/frame753/depth29→sprite267 captures retain authored, clear and cache-only paired transparent/black images at three integer offsets. Native Glow readbacks include blurX/Y, quality, color, alpha, strength, inner and knockout; all match the pinned source filter. No property is inferred from a visually matching image.

Cache equals clear **720000/720000 pixels**. The unchanged grouped blur and independently admitted premultiplied color/gain/source-over construction applied to measured cache input reproduces authored Glow **720000/720000 exact**. Normal composition matches both original pinned images **480000/480000 exact**. Source-derived input and GPU binding for this placement are still separate gates.

## Reproduce

```sh
python3 -m tools.probes.build_component_glow_boundaries --cases evidence/importer-loud-fail/r21/components/yulong/cases.json --case yulong-345-753-29 --output /tmp/yulong-glow --ffdec /path/to/ffdec-cli.jar
python3 tools/probes/capture_native_player.py /tmp/yulong-glow/components/yulong /tmp/yulong-glow/components/yulong/native.log --player-app '/path/to/Flash Player.app' --allow-window-activation --timeout 90
python3 -m tools.probes.analyze_component_glow_boundaries --native evidence/importer-loud-fail/r131/native --output /tmp/yulong-glow-analysis
python3 -m unittest tools.tests.test_component_glow_boundaries
```

[Summary/property readbacks](summary.json), native capture/environment under `native/`, full boundary images in `images/`, [provenance](provenance.json), [acceptance](acceptance.json).

Next discriminator: source-extract shape266's complete fill table, active edge/style mapping and exact fill matrix. The current single-positive-axis-fill extractor rejects it; do not bypass that guard. Distinguish unused style slots from active styles and retain the quarter-turn matrix before designing independent native rotation controls. Only after source input is exact may the shared live filter-family path advance.

`source_derived_input_verified=false`, `production_admitted=false`. Six earlier pinned Blur images have exact live GPU diagnostics; full production54-suite historical9/54 not rerun. General affine/coverage and full AS ownership remain open. Draft only; no merge/deploy/Worker.
