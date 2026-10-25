# r159 — nearest affine failures survive single-pixel clipping

5760 native clips retain the exact r158 source bytes and effective transforms. Lengths1/3/4/8 vary while clip start/target positions remain fixed. All **23040/23040 sampled pixels equal full-row output**, including **9531/9531 geometry-selected interior samples**. No overlapping pixel changes with length.

The fixed16.16 center candidate still matches only495/632 single-pixel interior controls. Other lengths preserve the same failure pattern; max delta15 is one source texel. This rules out the measured clip-length/bulk transition as the cause in this domain. It does not prove every affine span or clipping origin.

[Summary](summary.json), [all initializer counterexamples](failures.json.gz), [native readbacks](native/native.log.gz), [provenance](provenance.json), [acceptance](acceptance.json).

```sh
python3 tools/probes/build_flash_filter_probe.py --case bitmap-nearest-affine-spans --output /tmp/nearest-spans --ffdec /path/to/ffdec-cli.jar
python3 tools/probes/capture_native_player.py /tmp/nearest-spans /tmp/nearest-spans/native.log --player-app '/path/to/Flash Player.app' --allow-window-activation --timeout 90
python3 -m tools.probes.analyze_nearest_affine_spans --native evidence/importer-loud-fail/r159/native --full-native evidence/importer-loud-fail/r158/native --output /tmp/nearest-spans.json
python3 -m unittest tools.tests.test_nearest_affine_spans
```

Next discriminator: derive interval constraints for a common affine coordinate map from the independently encoded source indices. First test whether exact/fixed inverse coefficients admit any single intercept per effective transform. Compare independently defined initialization sequences against every bound; never pick an interval midpoint/endpoint or a different route per RGB. If coefficients themselves are infeasible, add independent row/column translations before changing arithmetic.

`affine_sampler_admitted=false`, `production_admitted=false`. Old exact suites remain unchanged. Draft only; full AS ownership and remaining visual gates stay open. No merge/deploy/Worker.
