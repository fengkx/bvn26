# r163 — axis controls separate inverse rounding from remaining shear initialization

The same16384 verified source texels and640 distant scalar measurements now use independent linear transforms:1/2,1/3 and2 axis scales, plus positive/negative single cross terms. Effective child properties are retained;1/3 reads back as float32 rather than an assumed16.16 forward matrix.

Exact inverse center matches **576/640**; fixed16.16 inverse center matches **608/640**. Fixed inverse rounding clears the32 exact-inverse failures in the1/3 controls. The remaining32 failures belong to negative shear; max delta1 is one source index. Both inverse coefficient families retain80/80 feasible intercept intervals. This is not an admitted initializer.

[Summary/all counterexamples](summary.json), [native source/property readbacks](native/native.log.gz), [provenance](provenance.json), [acceptance](acceptance.json).

```sh
python3 tools/probes/build_flash_filter_probe.py --case bitmap-nearest-affine-axes --output /tmp/nearest-axes --ffdec /path/to/ffdec-cli.jar
python3 tools/probes/capture_native_player.py /tmp/nearest-axes /tmp/nearest-axes/native.log --player-app '/path/to/Flash Player.app' --allow-window-activation --timeout 90
python3 -m tools.probes.analyze_nearest_affine_distant --native evidence/importer-loud-fail/r163/native --output /tmp/nearest-axes.json
python3 -m unittest tools.tests.test_nearest_affine_axes
```

Next discriminator: independently vary bitmap dimensions and authored mask dimensions while keeping the sampled source bytes, effective transform and target position fixed. This tests hidden size/geometry dependence before inventing another matrix-only intercept. Preserve original16/128 source readbacks and only compare common interior source positions; do not use edge mismatches to choose arithmetic routes.

`coefficients_selected_from_intervals=false`, `affine_sampler_admitted=false`, `production_admitted=false`. All old controls remain pinned.24 live/wrapper images exact; production54 historical9/54; full AS ownership still open. Draft only; no merge/deploy/Worker.
