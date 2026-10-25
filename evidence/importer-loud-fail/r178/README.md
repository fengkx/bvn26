# r178 — bounded integer affine GPU sampler exact on68322 native controls

The GPU computes source indices from geometry-derived signed32-bit inverse coefficients, the shared minimum-component/ties-even offset, target coordinates and rational fill phase. It fetches original raw texels; expected RGB is never uploaded as sampler input. Fixed metadata packs eight signed words per output pixel; all arithmetic stages are checked before upload, with maximum absolute intermediate98444094 (<2^31).

**68322/68322 RGBA pixels exact**, including held-out reflections, dominant shears, integer boundaries and half-grid controls. Padding is exact. This is opaque nearest interior sampling at independently captured scalar positions. It does not establish arbitrary polygon coverage, transparent sampling, smoothing, storage-format routing, source-edge behavior, continuous spans or production composition.

The initial eleven-sampler fixture returned all-transparent output. CPU metadata remained[5,11,128,1], while GPU metadata readback resembled the default normal texture. Packing coefficients into one texture reduced custom bindings to four and cleared the unchanged native gate. [Failed wiring control](diagnostic-wiring/summary.json) and source/readback artifacts are retained; this was a diagnostic connection failure, not a Flash-reference adjustment.

Fresh unchanged regressions: prior sampler71824/71824; leaf6/6; integer ordinary composition4032/4032; complete Yulong wrappers4/4; Lanran complete images4/4 and12/12 intermediate boundaries. Full CPU suites retain their pinned inputs. Production54 remains historical9/54;24 original live/wrapper diagnostic images remain exact.

[GPU report](gpu/report.json), [geometry metadata specification](gpu/fixture.json), [source/native/readback provenance](gpu/provenance.json), [acceptance](acceptance.json). Binary metadata regenerates from the packaged runner and is checked against recorded hashes; large scratch buffers are not committed.

```sh
python3 -m tools.probes.run_affine_nearest_integer --godot /path/to/Godot --output /tmp/affine-integer-gpu
python3 -m tools.probes.run_half_even_bitmap --godot /path/to/Godot --output /tmp/sampler-regression
python3 -m tools.probes.run_normal_composition --godot /path/to/Godot --native evidence/importer-loud-fail/r36 --output /tmp/normal-regression
python3 -m tools.probes.run_indexed_component_live --godot /path/to/Godot --output /tmp/indexed-regression
python3 -m unittest tools.tests.test_affine_nearest_integer
```

Next discriminator: bind an original main/XG_mfdjx unsmoothed leaf as an isolated diagnostic, retaining its exact format3 bitmap, fill matrix, mask and effective affine transform. First compare geometry-selected fully covered interior pixels against native clear/cache boundaries; independently check indexed versus byte-identical AS-created storage before assuming the admitted ASBitmapData sampler applies. Keep polygon edges, ColorMatrix/CXFORM and full-wrapper composition separate until proven. No production enablement from interior-only success.

`bounded_gpu_exact=true`; `production_admitted=false`; `full_production_suite_rerun=false`. Full AS/clip-action ownership remains a separate merge blocker. Draft only; no merge/deploy/Worker.
