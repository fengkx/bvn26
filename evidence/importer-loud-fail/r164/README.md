# r164 — independent bitmap/mask dimensions leave interior sampling unchanged

Two raw coordinate-coded sources (16×16 and128×128) explicitly verify **16640 texels**. Each is drawn through independently authored16×16 and128×128 masks. The common sampled source region, effective transforms and target positions remain fixed; actual bounds and paired pixel readbacks are retained.

All **160/160 groups** have identical pixels across their four source/mask combinations (**640 observations**). Geometric checks keep every sample a full source texel away from the common16×16 boundary. Thus neither tested bitmap dimension nor mask extent explains the existing interior initializer failures. This is not a general size-invariance or edge-coverage admission.

[Summary/groups](summary.json), [native source/bounds readbacks](native/native.log.gz), [provenance](provenance.json), [acceptance](acceptance.json).

```sh
python3 tools/probes/build_flash_filter_probe.py --case bitmap-affine-source-mask-size --output /tmp/affine-sizes --ffdec /path/to/ffdec-cli.jar
python3 tools/probes/capture_native_player.py /tmp/affine-sizes /tmp/affine-sizes/native.log --player-app '/path/to/Flash Player.app' --allow-window-activation --timeout 90
python3 -m tools.probes.analyze_affine_source_mask_size --native evidence/importer-loud-fail/r164/native --output /tmp/affine-sizes.json
python3 -m unittest tools.tests.test_affine_source_mask_size
```

Next discriminator: redistribute exact integer translation independently between child and draw matrices while keeping the total source-to-device matrix and target coordinates unchanged. Compare with the existing size-control baseline. This tests separate translation consumption before attributing all residuals to a matrix-only half-step rule. Keep old counterexamples; no interval-derived coefficients or RGB-selected routes.

`affine_sampler_admitted=false`, `production_admitted=false`. Production54 remains historical9/54;24 live/wrapper diagnostics exact; full AS ownership remains open. Draft only; no merge/deploy/Worker.
