# r162 — distant source positions preserve the initializer counterexamples

A128×128 source explicitly reads back all **16384 texels**, encoding X/Y directly with constant blue/opaque alpha.640 single-pixel captures cross independent source positions8/40/80/112, the five existing linear transforms, quarter translations and two larger draw origins. Actual child/draw matrices and chosen destination coordinates are retained; every sample is geometrically interior.

Exact and fixed16.16 center initialization each match **555/640**, max channel delta1 (one source index). Both coefficient families still admit **80/80 per-axis intercept intervals** across distant positions. This strengthens the coefficient constraints without selecting a fitted intercept. It does not prove those coefficients uniquely or explain initialization.

[Summary and all failures/intervals](summary.json), [native readbacks](native/native.log.gz), [provenance](provenance.json), [acceptance](acceptance.json).

```sh
python3 tools/probes/build_flash_filter_probe.py --case bitmap-nearest-affine-distant --output /tmp/nearest-distant --ffdec /path/to/ffdec-cli.jar
python3 tools/probes/capture_native_player.py /tmp/nearest-distant /tmp/nearest-distant/native.log --player-app '/path/to/Flash Player.app' --allow-window-activation --timeout 90
python3 -m tools.probes.analyze_nearest_affine_distant --native evidence/importer-loud-fail/r162/native --output /tmp/nearest-distant.json
python3 -m unittest tools.tests.test_nearest_affine_distant
```

Next discriminator: independent axis-only minification/magnification and single signed off-diagonal terms, keeping distant source readbacks and translations fixed. Separate diagonal footprint/half-step effects from off-diagonal contributions before proposing another common initializer. Require every old interval/control; no coefficient selection from feasible bounds.

`coefficients_selected_from_intervals=false`, `affine_sampler_admitted=false`, `production_admitted=false`. Production unchanged; full AS ownership remains open. Draft only; no merge/deploy/Worker.
