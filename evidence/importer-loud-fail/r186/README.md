# r186 — held-out long signed edges retain one scan construction

Independent authored parallelograms cross subrow256/1024 with heights7,31,127,257; signed horizontal differences±17/±65; integer and quarter origins. All64 bitmap/vector cases retain explicit4096 source texels, verified bounds and identity matrix readbacks. Storage pairs are exact249896/249896 pixels.

The unchanged r185 toward-zero fixed16 slope construction matches **499792/499792 pixels**. Fixed16 ties-even also matches this new set, but remains rejected by r185 old controls. Exact rational and every fixed24 construction leave32 counterexamples; fixed8 fails more. This does not infer internal implementation from agreement; it retains one bounded common construction across independent geometry.

[Results](summary.json), [failures](failures.json.gz), [native](native/native.log.gz), [provenance](provenance.json), [acceptance](acceptance.json).

```sh
python3 tools/probes/build_flash_filter_probe.py --case affine-edge-stepping --output /tmp/edge-stepping --ffdec /path/to/ffdec-cli.jar
python3 tools/probes/capture_native_player.py /tmp/edge-stepping /tmp/edge-stepping/native.log --player-app '/path/to/Flash Player.app' --allow-window-activation --timeout 90
python3 -m tools.probes.analyze_affine_edge_stepping --native evidence/importer-loud-fail/r186/native --output /tmp/edge-stepping.json
python3 -m unittest tools.tests.test_affine_edge_stepping
```

Next discriminator: compose the unchanged bounded nearest sampler and this geometry-only coverage against the original main Bitmap281/Shape282 full native leaf images, including all zeros and15 formerly unproved nonzero edge pixels. Record every out-of-source footprint and compare clamp/clear behavior explicitly; do not silently discard such samples or claim a full wrapper from a leaf pass. GPU binding follows only after the full CPU image gate.

`coverage_admitted=false`, `production_admitted=false`. Production54 historical9/54;24 complete live/wrapper diagnostics exact. Full AS/clip-action ownership remains separate. No production rendering change. Draft only.
