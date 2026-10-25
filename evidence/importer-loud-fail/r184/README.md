# r184 — translation is applied after vertex rounding in these controls

Independently vary one authored edge, scale, child translation and exact-quarter draw translation. All768 cases retain explicit4096 source texels, local bounds and actual matrix readbacks. Bitmap and vector fill captures agree. Child translation properties written as0.125,0.375,-0.125 read back as0.1,0.35,-0.1: toward-zero twip consumption is visible directly, not inferred from RGB.

Using those actual matrix properties, quarter ties-even of the transformed local vertex **before** adding separately consumed translations matches **310232/310232 pixels**. Combining translation before vertex rounding fails1024 pixels; child-before-draw rounding fails768. These are globally fixed operation orders, never selected per pixel. The result constrains this bounded axis-aligned set only; no general coverage or production admission.

[Summary/readbacks](summary.json), [counterexamples](failures.json.gz), [native capture](native/native.log.gz), [provenance](provenance.json), [acceptance](acceptance.json).

```sh
python3 tools/probes/build_flash_filter_probe.py --case affine-vertex-translation --output /tmp/vertex-translation --ffdec /path/to/ffdec-cli.jar
python3 tools/probes/capture_native_player.py /tmp/vertex-translation /tmp/vertex-translation/native.log --player-app '/path/to/Flash Player.app' --allow-window-activation --timeout 90
python3 -m tools.probes.analyze_affine_vertex_translation --native evidence/importer-loud-fail/r184/native --output /tmp/vertex-translation.json
python3 -m unittest tools.tests.test_affine_vertex_translation
```

Next discriminator: apply this independently constrained operation order unchanged to all r181 affine controls. If edges still fail, examine the exact edge intersections and native subpixel coverage; distinguish slope initialization/stepping from intersection rounding with independent edge geometry, rather than mixing vertex rules from observed RGB.

`coverage_admitted=false`, `production_admitted=false`. The15 original main nonzero edge pixels remain unproved. Production54 historical9/54;24 complete live/wrapper diagnostics exact. Full AS/clip-action ownership remains open. Draft only; no production changes.
