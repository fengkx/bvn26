# r180 — original nearest leaf interior bound to integer GPU sampling

The original main Bitmap281 texels, Shape282 mask/fill table and binary owner placement remain in the diagnostic fixture. The shader receives only geometry-derived integer coefficients and target positions; it reads the original137×200 raw texture directly. Actual source dimensions replace the synthetic atlas dimensions. The mask used for comparison explicitly marks only the previously proved geometric interior, not production coverage.

**52921/52921 RGBA pixels exact on GPU** (26730 unit,26191 authored affine), including transparent source holes. No native RGB enters shader parameters. The unclaimed output is deliberately clear and is not counted as native parity. All3/12 nonzero native edge pixels remain listed as unresolved. Neither complete leaf images nor production54 counts are increased.

[GPU report](gpu/report.json), [source/mask/transform fixture](gpu/fixture.json), [provenance](gpu/provenance.json), [acceptance](acceptance.json). Binary metadata regenerates deterministically and is checked against recorded hashes.

```sh
python3 -m tools.probes.run_nearest_component_interior --godot /path/to/Godot --output /tmp/nearest-component-interior
python3 -m unittest tools.tests.test_nearest_component_interior
```

Next discriminator: independently render constant-color bitmap and vector rectangles under the authored affine matrix and signed/sheared held-out matrices. Capture explicit source bytes, actual transform properties and complete analytically bounded image regions. Test common geometric subpixel coverage constructions against native alpha/RGBA before applying any edge rule to the15 unresolved source pixels. Keep ColorMatrix, post-filter CXFORM and complete wrapper/cache composition separate.

`interior_gpu_exact=true`, `complete_component_admitted=false`, `production_admitted=false`, `full_production_suite_rerun=false`. Production54 historical9/54;24 complete live/wrapper diagnostics remain exact. Full AS ownership remains open. Draft only; no merge/deploy/Worker.
