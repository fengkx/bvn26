# r205 — all-alpha paired and remainder inputs are exact

The unchanged r204 packed candidate matches **55296/55296 native RGBA pixels**, maxdelta0. Independently vary all256 source alphas, three colors, neighbor alpha0/127/255, processed width3/4/5 and first/last target position. All13824 cases retain the actual premultiplied source readbacks and complete output rows; no source-color conversion is invented to match the filter. Full authored matrix properties match the original main filter.

This covers independent alpha changes in both the paired prefix and scalar remainder. It does not prove arbitrary alpha-changing matrices, coefficient-overflow cases, platform dispatch or production buffer binding. Production admission and GPU advancement remain false pending retained early scalar/ramp checks with explicit inputs.

[Full cases](summary.json.gz), [native](native/native.log.gz), [provenance](provenance.json), [acceptance](acceptance.json).

```sh
python3 tools/probes/build_flash_filter_probe.py --case matrix-all-alpha-pairs --output /tmp/matrix-all-alpha-pairs --ffdec /path/to/ffdec-cli.jar
python3 tools/probes/capture_native_player.py /tmp/matrix-all-alpha-pairs /tmp/matrix-all-alpha-pairs/native.log --player-app '/path/to/Flash Player.app' --allow-window-activation --timeout 120
python3 -m tools.probes.analyze_matrix_all_alpha_pairs --native evidence/importer-loud-fail/r205/native --output /tmp/matrix-all-alpha-pairs.json
python3 -m unittest tools.tests.test_matrix_all_alpha_pairs tools.tests.test_matrix_packed_candidate
```

Next discriminator: capture unfiltered input bytes for the original r11 scalar and r12 ramp vector geometries without changing their authored filters or draw APIs. Require original filtered outputs unchanged, then compare the fixed packed construction globally. Only after these retained controls and all original materialized buffers are exact may the bounded diagnostic GPU path advance. Main family still10/12 on GPU; production54 historical9/54. Full AS ownership remains open. Draft only.
