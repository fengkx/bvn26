# r158 — nearest affine initialization remains unproven

Independent source bytes encode X/Y indices in separate channels, with constant blue/opaque alpha. All256 source texels are explicitly read back.160 native cases cross identity, source-like main/Yijiao rotations, quarter-turn and shear with independent quarter translations and two draw origins; effective matrices are recorded.

A full source-texel geometric margin excludes coverage edges independently of RGB. Among **22261 interior pixels**, exact inverse pixel-center sampling matches17601; the fixed16.16 inverse/half-step construction matches18251. Both have max channel delta15, corresponding to one source index. Identity/quarter-turn controls pass; general rotation/shear counterexamples remain. Neither construction is admitted.

[Summary](summary.json), [all failures](failures.json.gz), [native source/matrix readbacks](native/native.log.gz), [provenance](provenance.json), [acceptance](acceptance.json).233739 outside/fringe pixels are retained in native evidence but excluded from the interior arithmetic claim. No coverage fallback or output-selected route.

```sh
python3 tools/probes/build_flash_filter_probe.py --case bitmap-nearest-affine --output /tmp/nearest-affine --ffdec /path/to/ffdec-cli.jar
python3 tools/probes/capture_native_player.py /tmp/nearest-affine /tmp/nearest-affine/native.log --player-app '/path/to/Flash Player.app' --allow-window-activation --timeout 90
python3 -m tools.probes.analyze_nearest_affine --native evidence/importer-loud-fail/r158/native --output /tmp/nearest-affine.json
python3 -m unittest tools.tests.test_nearest_affine
```

Next discriminator: hold source, effective transform and target sample fixed; vary clip lengths1/3/4/8 and compare overlapping pixels with full rows. This separates scalar initialization from span processing before changing coefficients or routing. Retain the exact axis-aligned/quarter-turn controls and direct source byte readbacks.

`affine_sampler_admitted=false`, `production_admitted=false`. Existing24 original diagnostic images remain exact; production54 historical9/54; full AS ownership still open. Draft only; no merge/deploy/Worker.
