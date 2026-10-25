# r183 — independent authored-edge controls support quarter ties-even

One authored rectangle edge moves on exact twips under unit, signed half and signed quarter scale. Every local getBounds readback matches its declared geometry: **840/840**. Explicit4096 source texels and bitmap/vector pairs are retained; storage pairs match115208/115208 pixels.

Direct device-quarter ties-even vertices match **230416/230416 pixels**. Half-up and half-down each have200 counterexamples; twip truncation before quarter rounding has272. Rounding to even twips then nearest quarter produces the same outcomes here; this does not identify an internal intermediate representation. Negative scales are covered, but all measured device coordinates are positive.

This independently constrains vertex ties, not general affine coverage. Applying quarter-even vertices to the previous affine scan construction still leaves318 r181 counterexamples; the apparently better half-up construction is now independently rejected. No mixed per-case route is admitted.

[Summary/local bounds](summary.json), [all failures](failures.json.gz), [native capture](native/native.log.gz), [provenance](provenance.json), [acceptance](acceptance.json).

```sh
python3 tools/probes/build_flash_filter_probe.py --case affine-vertex-rounding --output /tmp/vertex-rounding --ffdec /path/to/ffdec-cli.jar
python3 tools/probes/capture_native_player.py /tmp/vertex-rounding /tmp/vertex-rounding/native.log --player-app '/path/to/Flash Player.app' --allow-window-activation --timeout 90
python3 -m tools.probes.analyze_affine_vertex_rounding --native evidence/importer-loud-fail/r183/native --output /tmp/vertex-rounding.json
python3 -m unittest tools.tests.test_affine_vertex_rounding
```

Next discriminator: keep these verified authored bounds and independently vary child translation versus exact-quarter draw translation, including half-quarter child properties. Determine where translation consumption and quarter ties-even occur before changing the general scan rule. Preserve all r181/r182 controls; do not choose rounding order from local RGB agreement. Negative device coordinates, arbitrary polygon coverage and the15 real-source edge pixels remain gated.

`coverage_admitted=false`, `production_admitted=false`. Production54 historical9/54;24 complete live/wrapper diagnostics exact. Full AS ownership remains open. Draft only.
