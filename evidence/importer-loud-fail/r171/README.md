# r171 — held-out matrices pass; reflection rejects general admission

Sixteen independently authored affine matrices include mixed scale/shear and non-binary ratios. Each is also reflected in source X; four draw origins and16 distant source coordinates are retained. All16384 coordinate-coded source texels and actual child/draw properties are explicitly read back.

Positive-determinant controls: **1024/1024 exact** for all three fixed constructions. Reflected controls: **624/1024**, with400 failures, all predicted source-X indices one below native. No result-dependent route or correction is introduced. The construction therefore remains rejected for general affine sampling, despite49309/49309 older fixed-inverse controls being exact.

[Summary](summary.json), [counterexamples](failures.json.gz), [native capture](native/native.log.gz), [provenance](provenance.json), [acceptance](acceptance.json).

```sh
python3 tools/probes/build_flash_filter_probe.py --case bitmap-affine-heldout --output /tmp/affine-heldout --ffdec /path/to/ffdec-cli.jar
python3 tools/probes/capture_native_player.py /tmp/affine-heldout /tmp/affine-heldout/native.log --player-app '/path/to/Flash Player.app' --allow-window-activation --timeout 90
python3 -m tools.probes.analyze_affine_heldout --native evidence/importer-loud-fail/r171/native --output /tmp/affine-heldout.json
python3 -m unittest tools.tests.test_affine_heldout
```

Next discriminator: isolate pure X/Y/both reflections and reflected signed shears with integer-fill phase sweeps. Require complete zero-phase factor1/factor64 image equivalence before interpreting intervals. Compare the same common geometric construction and all older observations; do not add1 to failed pixels or select a reflection path from native RGB. Determine whether the source-coordinate direction changes the initializer itself or the index-rounding rule.

`candidate_admitted=false`, `gpu_advance_allowed=false`, `production_admitted=false`. Production54 historical9/54;24 source-backed live/wrapper diagnostics exact. Full AS ownership remains open. Draft only.
