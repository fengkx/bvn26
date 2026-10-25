# r175 — native integer-boundary controls reject unrounded offsets

A reproducible generator uses only retained matrix properties and arithmetic disagreement, never native RGB, to select five coordinates. Each retains a3×3 neighborhood, actual source texels and transform readbacks. The generator solves a fixed16.16 modular boundary equation; no coefficient is fitted.

**Rounded16.16 offset:45/45 exact, including5/5 distinguishing centers.** Exact norm and floor-quantized offset each match40/45, rejecting every center while retaining all40 neighbors. These counterexamples reject retaining an unrounded norm as a general construction. Floor quantization is mathematically equivalent on these fixed-coordinate inputs, but that behavior is not native here.

This supports nearest rounding at the measured non-tie boundaries. It does not independently establish tie behavior or authorize GPU/production admission before all older controls are rerun with the same rounded rule.

[Summary/selection/readbacks](summary.json), [failures](failures.json.gz), [native capture](native/native.log.gz), [provenance](provenance.json), [acceptance](acceptance.json).

```sh
python3 -m tools.probes.generate_affine_offset_boundaries --native evidence/importer-loud-fail/r171/native --output /tmp/bitmap-affine-offset-boundaries.as --selection /tmp/offset-selection.json
python3 tools/probes/build_flash_filter_probe.py --case bitmap-affine-offset-boundaries --output /tmp/offset-boundaries --ffdec /path/to/ffdec-cli.jar
python3 tools/probes/capture_native_player.py /tmp/offset-boundaries /tmp/offset-boundaries/native.log --player-app '/path/to/Flash Player.app' --allow-window-activation --timeout 90
python3 -m tools.probes.analyze_affine_offset_boundaries --native evidence/importer-loud-fail/r175/native --selection-native evidence/importer-loud-fail/r171/native --output /tmp/offset-boundaries.json
python3 -m unittest tools.tests.test_affine_offset_boundaries
```

Next discriminator: apply one common minimum-component plus rounded16.16 norm offset to every prior control, including consumed fractional fill inputs, held-out reflections, dominant shears and these boundaries. Only if all pass, port the bounded opaque-interior operation into a GPU diagnostic with integer coefficients and preserved raw texels; keep coverage, smoothing and production admission separate.

`candidate_admitted=false`, `gpu_advance_allowed=false`, `production_admitted=false`. Production54 historical9/54;24 live/wrapper diagnostics exact. AS ownership remains open. Draft only.
