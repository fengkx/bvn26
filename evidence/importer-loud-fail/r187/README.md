# r187 — complete original main nearest leaf CPU images are exact

Combine the unchanged bounded nearest integer sampler with r185/r186 geometry-only coverage. Preserve original Bitmap281/Shape282 raw tags, fill67 clipped/unsmoothed metadata,137×200 mask and source matrix. All pixels are compared, including transparent holes, previously excluded zeros and all15 formerly unproved nonzero edge pixels.

Both unique600×400 leaf images are **480000/480000 exact**. Across before/after loadBitmap and byte-identical AS materialization, **1440000/1440000 RGBA pixels** match. These are two unique leaf images, not six distinct components or complete wrappers.

The affine image contains377 nonzero-coverage out-of-source sample indices; all are listed with source indices, clamped texel and native RGBA. Three have nonzero native output: clearing instead of clamping fails3 pixels per epoch (9 total). Clamp is explicit and globally applied; no sample is silently skipped or selected from native RGB. Other boundary directions and arbitrary shapes remain unproved.

[Complete results and every footprint](summary.json), [original native](../r179/native/native.log.gz), [provenance](provenance.json), [acceptance](acceptance.json).

```sh
python3 -m tools.probes.analyze_nearest_component_coverage --native evidence/importer-loud-fail/r179/native --output /tmp/nearest-component-coverage.json
python3 -m unittest tools.tests.test_nearest_component_coverage
```

Next discriminator: bind this exact geometry mask and fixed sampler in a standalone GPU diagnostic against the same two full native images. Preserve real source texels and masks; check signed index arithmetic, clamp and premultiplied coverage multiplication explicitly. Do not infer complete main wrapper parity or enable production from a leaf pass.

`complete_wrapper_admitted=false`, `production_admitted=false`. Production54 historical9/54;24 complete live/wrapper diagnostics exact. Main wrapper filter/CXFORM and full AS/clip-action ownership remain blockers. Production unchanged; Draft only.
