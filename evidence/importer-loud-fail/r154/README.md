# r154 — live indexed Lanran GPU input and all four complete images exact

The diagnostic reads original format3 texels and retained source fill/mask metadata. Coordinates, eight-bit weights and quarter-grid coverage derive solely from geometry; no CPU-rendered or native image is uploaded as source. A live sampler ViewportTexture feeds actual FilterGroup allocation/padding, grouped integer Blur passes and integer normal composition.

All four original complete Lanran images match **960000/960000 pixels**. All12 intermediate comparisons (local input, padded Contents and filtered output for each frame) are exact. Existing FilterGroup checks assert live texture identity, allocation size, pass dependencies/axes and destination-copy ordering. [GPU report](gpu/report.json), [fixture](gpu/fixture.json), [provenance](gpu/provenance.json), [acceptance](acceptance.json).

```sh
python3 -m tools.probes.run_indexed_component_live --godot /path/to/Godot --output /tmp/indexed-live
python3 -m unittest tools.tests.test_indexed_component_live
```

This raises source-backed live original component images from8 to12 (six Jiraiya/Yijiao, two Yulong, four Lanran). **Production54 remains historical9/54**: no production sampler binding or global eligibility change. `live_indexed_component_exact=true`, `production_admitted=false`.

Next discriminator: inventory the next remaining source component's full bitmap encoding, fills/masks, placement transform and native cache/filter boundaries. Prefer a source-proven rectangular indexed/lossless component in the admitted domain; otherwise retain a precise unsupported geometry/encoding reason. Do not extrapolate to JPEG3, non-unit indexed coverage, arbitrary affine, midpoint ties, nested opacity or full AS ownership from these images. Re-run prior sampler and live component suites before widening diagnostics.

Draft only; not merge-ready. Full AS/clip-action ownership and remaining visual components are separate blockers. No merge/deploy/Worker.
