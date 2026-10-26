# r172 — reflection phase separates negative-component handling

Pure X/Y/both reflections and eight reflected signed shears retain the same coordinate-coded source and scale64 integer-fill phase sweep. **49152/49152 full zero-phase pixels** agree between factor1 and factor64; **72/72 scalar zero phases** agree with full images. All72 coordinate intervals remain feasible and monotone.

The old sum-of-negative-components construction matches8904/9288 samples. Pure reflections pass;384 failures are confined to two phases where an inverse row has both components negative. Native offsets for the affected rows lie in[-29/64,-7/16), whereas summing both negative terms predicts a substantially smaller offset. No pixel is corrected from its observed error.

[Summary](summary.json), [failures](failures.json.gz), [native capture](native/native.log.gz), [provenance](provenance.json), [acceptance](acceptance.json).

```sh
python3 tools/probes/build_flash_filter_probe.py --case bitmap-affine-reflection-phase --output /tmp/reflection-phase --ffdec /path/to/ffdec-cli.jar
python3 tools/probes/capture_native_player.py /tmp/reflection-phase /tmp/reflection-phase/native.log --player-app '/path/to/Flash Player.app' --allow-window-activation --timeout 90
python3 -m tools.probes.analyze_affine_reflection_phase --native evidence/importer-loud-fail/r172/native --output /tmp/reflection-phase.json
python3 -m unittest tools.tests.test_affine_reflection_phase
```

Next discriminator: compare two independently defined common constructions globally: use only the minimum of(0,a,b), versus give a negative diagonal component priority over the off-diagonal component. Keep the same Euclidean norm and fixed inverse arithmetic; retain every old observation. If both survive, capture reflected shears whose off-diagonal magnitude exceeds the diagonal to distinguish them. Never choose either path from RGB.

`candidate_admitted=false`, `gpu_advance_allowed=false`, `production_admitted=false`. Production54 historical9/54;24 live/wrapper diagnostics exact. AS ownership remains open. Draft only.
