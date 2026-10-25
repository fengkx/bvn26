# r169 — independent signed horizontal and vertical shear phases

Eleven fixed shear coefficients from-1 to1 are applied separately on the horizontal and vertical axes, with the same explicit16×16 coordinate-coded source. Each matrix first retains complete factor1/factor64 zero-phase images, then sweeps integer fill translation on X/Y with the fixed scale64 decomposition.

**90112/90112 full-image pixels** match across scale paths; **132/132 scalar zero-phase samples** match those full images. All17028 phase samples retain explicit source/property readbacks. **132/132 coordinate intervals** are feasible and monotone, untouched channels remain constant, and **24/24 corresponding old interval intersections** remain feasible.

The measured offsets transpose with the shear direction. They are not explained by a constant screen-axis correction. For example, the affected coordinate offset at shear+1 lies in[-19/64,-9/32), while shear-1 lies in[45/64,23/32). These are rejection intervals, not rendering coefficients. No new arithmetic is admitted.

[Summary](summary.json), [native capture](native/native.log.gz), [provenance](provenance.json), [acceptance](acceptance.json).

```sh
python3 tools/probes/build_flash_filter_probe.py --case bitmap-affine-shear-phase --output /tmp/shear-phase --ffdec /path/to/ffdec-cli.jar
python3 tools/probes/capture_native_player.py /tmp/shear-phase /tmp/shear-phase/native.log --player-app '/path/to/Flash Player.app' --allow-window-activation --timeout 90
python3 -m tools.probes.analyze_affine_shear_phase --native evidence/importer-loud-fail/r169/native --old-summary evidence/importer-loud-fail/r168/summary.json --output /tmp/shear-phase.json
python3 -m unittest tools.tests.test_affine_shear_phase
```

Next discriminator: test one common geometric construction independently against all prior affine controls: half the inverse row-vector Euclidean length plus its negative components, added to the inverse-transformed pixel origin. Compare exact and globally fixed16 inverse arithmetic, without selecting either from RGB. Use exact rational/square-root comparisons at integer boundaries; reject a construction on any old counterexample before GPU or production work.

`affine_sampler_admitted=false`, `production_admitted=false`. Production54 historical9/54;24 original live/wrapper diagnostics exact. AS ownership remains open. Draft only.
