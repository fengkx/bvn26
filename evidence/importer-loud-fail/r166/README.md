# r166 — signed fill translation consumes toward-zero twips

3870 native scalar controls sweep declared fill translation from-1 to1 in1/64 increments, independently on X/Y. Geometry, child/draw matrices and raw256 coordinate-coded texels remain fixed. Declared Matrix properties are retained and explicitly distinguished from inaccessible internal fill state.

Identity controls independently support **toward-zero truncation onto1/20 pixels**:774/774 exact. Declared-value, floor, ties-even and ties-away alternatives each match756/774. Applying the supported consumed values removes contradictory linear intervals: **0/30 feasible using declared values →30/30 using consumed values**. All sweeps are monotone and the untouched source-coordinate channel stays constant.

This does **not** solve affine initialization. With the unchanged fixed inverse center, common twip consumption matches3380/3870 overall; rotation/shear failures remain. No interval coefficient is selected and no production sampler is enabled.

[Summary/transition bounds](summary.json), [all model failures](failures.json.gz), [native readbacks](native/native.log.gz), [provenance](provenance.json), [acceptance](acceptance.json).

```sh
python3 tools/probes/build_flash_filter_probe.py --case bitmap-affine-fill-phase --output /tmp/fill-phase --ffdec /path/to/ffdec-cli.jar
python3 tools/probes/capture_native_player.py /tmp/fill-phase /tmp/fill-phase/native.log --player-app '/path/to/Flash Player.app' --allow-window-activation --timeout 90
python3 -m tools.probes.analyze_affine_fill_phase --native evidence/importer-loud-fail/r166/native --output /tmp/fill-phase.json
python3 -m unittest tools.tests.test_affine_fill_phase
```

Next discriminator: first prove full-image equivalence when integer fill scale is compensated by reciprocal child scale and matching authored geometry. Only if that zero-phase control is exact may larger integer fill translations be used to measure finer source phase. Retain all old controls; do not infer fractional consumption or matrix precision solely from declared properties.

`affine_sampler_admitted=false`, `production_admitted=false`.24 live/wrapper diagnostics exact; production54 historical9/54; full AS ownership remains open. Draft only; no merge/deploy/Worker.
