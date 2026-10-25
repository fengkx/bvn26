# r194 — original main wrapper passes actual FilterGroup GPU final-image gate

Live original format3 texels and source mask feed the integer nearest sampler with geometry-only cache-local metadata. Its ViewportTexture feeds actual production FilterGroup allocation and the complete authored20-value ColorMatrix. Existing native post-CXFORM/normal composition consumes the filtered texture with verified destination-copy ordering. Frame17 removal/Stop produces an empty view; original clocks select the two active source leaves.

**4/4 pinned original final images,960000/960000 RGBA pixels exact.** Six native alpha-boundary comparisons(local cache, Contents, filtered output at two active frames) are **326472/326472 exact**. Source texture identity, allocation223×244, filter uniforms/pass connection and Copy-before-Composite are asserted. No CPU-rendered/native image enters a shader input.

The post-transform's RGB multipliers are zero, so these final images and alpha checks **do not prove intermediate ColorMatrix RGB**. The full filter executes; its RGB results are not used to fabricate a passing intermediate claim. Production sampler stays disabled.

[GPU report](gpu/report.json), [source/filter fixture](gpu/fixture.json), [provenance](gpu/provenance.json), [acceptance](acceptance.json). Binary metadata regenerates from pinned source and is hash-checked; scratch buffers are not committed.

```sh
python3 -m tools.probes.run_nearest_matrix_component --godot /path/to/Godot --output /tmp/nearest-matrix-component
python3 -m unittest tools.tests.test_nearest_matrix_component
```

Next discriminator: preserve the same geometry and animation while exercising the other two authored owner states: white post-CXFORM and identity post-CXFORM. Capture their original uncached/cache/filter boundaries and compare all12 pinned family images through actual FilterGroup. Identity post-CXFORM exposes the previously unproved matrix RGB; do not infer its parity from the blue state.

`live_final_wrapper_exact=true`, `matrix_rgb_intermediate_proved=false`, `production_admitted=false`. Source-backed complete live/wrapper diagnostics24→28 images. Production54 historical9/54, not remeasured or rebound. Full AS/clip-action ownership remains separate. Draft only; no production/merge/deploy/Worker.
