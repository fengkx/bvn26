# r177 — explicit signed scale controls support ties-even offsets

Signed scale3/5/7/13 on each axis independently varies source coordinates4/8/12, six target origins and five quarter-pixel translation brackets. All256 source texels and actual child/draw matrix properties are retained.1080/1440 observations contain exact half-grid offsets.

**Ties-even:1440/1440 exact.** Half-up and ties-away each match1416/1440;24 positive-scale controls distinguish and reject them. Negative-scale controls are retained and pass the same ties-even construction, but do not independently distinguish all signed tie alternatives. No special-case route is introduced.

Combined with the r176 global regression, the same common ties-even construction covers68322 native observations. This permits a bounded GPU diagnostic of opaque interior sampling; it does not admit source-boundary coverage, transparent-edge behavior, smoothing, buffer composition or production placements.

[Summary](summary.json), [failures](failures.json.gz), [native capture](native/native.log.gz), [provenance](provenance.json), [acceptance](acceptance.json).

```sh
python3 tools/probes/build_flash_filter_probe.py --case bitmap-affine-offset-ties --output /tmp/offset-ties --ffdec /path/to/ffdec-cli.jar
python3 tools/probes/capture_native_player.py /tmp/offset-ties /tmp/offset-ties/native.log --player-app '/path/to/Flash Player.app' --allow-window-activation --timeout 90
python3 -m tools.probes.analyze_affine_offset_ties --native evidence/importer-loud-fail/r177/native --output /tmp/offset-ties.json
python3 -m unittest tools.tests.test_affine_offset_ties
```

Next discriminator: render all68322 controls through a GPU diagnostic using fixed integer coefficients, common rounded offset and original raw source texels. Metadata must derive only from geometry/matrices, never expected RGB; verify integer overflow bounds. Require exact native RGBA before any component binding. Keep production and general coverage admission false; retain every old sampler/leaf/Glow suite.

`candidate_admitted=false`; `gpu_advance_allowed=true` only for the explicitly bounded opaque-interior diagnostic. `production_admitted=false`. Production54 historical9/54;24 live/wrapper diagnostics exact. AS ownership remains open. Draft only.
