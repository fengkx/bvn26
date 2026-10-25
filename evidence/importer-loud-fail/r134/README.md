# r134 — independent ramps constrain signed affine initialization

The fixed r133 geometry/transform grid is recaptured with opaque horizontal-red `(16+64x)`, vertical-green `(16+96y)` and constant-blue73 texels. Explicit source and all four byte permutations are retained. No source coordinate is inferred from whichever output formula matches.

One predeclared construction inverts the complete authored matrix, independently rounds each inverse coefficient/translation to16.16 and uses ties-even for the summed half-step. Three globally fixed interpolation orders are compared; none is selected per pixel. Fully covered interior pixels are counted separately from coverage/exterior.

| Source | Byte weights | V then H | H then V |
|---|---:|---:|---:|
| Independent ramps |21522/22224|13872/22224|13872/22224|
| Retained r133 transparent source |21206/22224|10634/22224|9916/22224|

For the short90°/270° controls, fixed byte weights clear **11112/11112 interior pixels per source suite**, including both native and physically permuted sources and both cache states. This does **not** admit universal byte interpolation: identity/180° controls still reject it (maximumΔ2 on transparent source), and existing long-span routes remain mandatory. Fringe pixels are explicitly excluded, not treated as exact.

[Summary and all rejected coordinates](summary.json), [retained transparent rejection](transparent-rejection.json), [native permutation comparison](equivalence.json), [provenance](provenance.json), [acceptance](acceptance.json).

## Reproduce

```sh
python3 tools/probes/build_flash_filter_probe.py --case bitmap-quarter-turn-ramps --output /tmp/quarter-ramps --ffdec /path/to/ffdec-cli.jar
python3 tools/probes/capture_native_player.py /tmp/quarter-ramps /tmp/quarter-ramps/native.log --player-app '/path/to/Flash Player.app' --allow-window-activation --timeout 90
python3 -m tools.probes.analyze_quarter_turn_ramps --native evidence/importer-loud-fail/r134/native --output /tmp/quarter-ramps.json
python3 -m unittest tools.tests.test_quarter_turn_ramps
```

Next discriminator: increase the source height while retaining distinct ramp channels/transparent readbacks, making reversed-axis interior scan spans longer than four pixels. Vary clip lengths independently around four-pixel boundaries without moving the same sampled coordinates. Only independently explained geometry can route scalar/bulk interpolation. Keep r133/r134 and all admitted positive-axis controls as rejection gates; do not enable a rotated source binding from these short interiors.

`initializer_admitted=false`, `interpolation_routing_admitted=false`, `production_admitted=false`. Production54 historical9/54; six bounded Blur live images exact, not a new full-suite count. General coverage/affine, remaining components and AS ownership remain separate blockers. Draft only; no merge/deploy/Worker.
