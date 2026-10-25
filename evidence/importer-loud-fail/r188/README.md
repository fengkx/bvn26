# r188 — complete original nearest leaf GPU images are exact

Bind original Bitmap281 raw137×200 texels and Shape282 mask to a standalone integer shader. CPU metadata contains only source-derived transforms, signed integer sampler coefficients and geometry-derived0..16 coverage; native RGB is used only in the final comparator. Negative fixed indices use explicit floor division, source indices clamp, and premultiplied bytes multiply by coverage with integer division. No output selection or tolerance.

**2/2 complete leaf images,480000/480000 RGBA pixels exact**, including all15 formerly unproved nonzero edge pixels and every transparent output pixel. Source tags/fill/mask, real texture upload and buffer size remain recorded. This is the untinted leaf; ColorMatrix, post-filter CXFORM, animation and complete wrapper are still separate gates.

[GPU report](gpu/report.json), [source metadata](gpu/fixture.json), [provenance](gpu/provenance.json), [acceptance](acceptance.json). Large metadata/source buffers regenerate deterministically from pinned inputs; tests verify their hashes without committing scratch binaries.

```sh
python3 -m tools.probes.run_nearest_component_coverage --godot /path/to/Godot --output /tmp/nearest-component-coverage-gpu
python3 -m unittest tools.tests.test_nearest_component_full_coverage
```

Next discriminator: compare the complete authored main wrapper's native uncached/cache/filter boundaries using the source graph and existing r157 captures. Preserve natural frame changes/removal/Stop and post-filter fixed RGB CXFORM. Determine cache allocation/transform differences before composing the ColorMatrix; do not substitute the exact leaf for a wrapper admission. Keep pinned full-stage images as the eventual gate.

`complete_leaf_gpu_exact=true`, `complete_wrapper_admitted=false`, `production_admitted=false`. Production54 historical9/54;24 complete live/wrapper diagnostics exact. Full AS/clip-action ownership remains open. No production change, merge/deploy/Worker. Draft only.
