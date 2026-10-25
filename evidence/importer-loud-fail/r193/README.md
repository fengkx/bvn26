# r193 — cache-local quantization clears original main CPU final images

Rebase the transform into the independently measured integer cache allocation, then compute/quantize the inverse sampler. Rasterize geometry in that same local space and copy at its integer origin. This is not algebraically equivalent to subtracting the origin from an already quantized global inverse.

Both globally fixed surviving origin constructions clear all r192 cached controls:960000 unique pixels per storage path, **1920000/1920000 indexed+AS** for each construction. For the original main transform they produce identical layouts; these data still do not distinguish general initializer internals.

Applied unchanged to original source graph/texels and natural clocks, the original cached boundary becomes **960000/960000 exact** (previous6 failures cleared). Authored filtered output and pinned gray-stage each match **960000/960000**,4/4 CPU final images (previous10 authored failures cleared). Empty frame17/removal/Stop remains explicit.

The bounded final-output proof checks the authored ColorMatrix alpha row is identity and subsequent RGB CXFORM multipliers are zero. Therefore final RGB depends on the authored offsets and filtered alpha, not intermediate matrix RGB. **Intermediate matrix RGB is not proved by this pass**; no filter is silently stripped or production consumer admitted. The next GPU diagnostic must run the actual filter and post-transform boundary.

[Full source/control results](summary.json), [provenance](provenance.json), [acceptance](acceptance.json).

```sh
python3 -m tools.probes.analyze_nearest_cache_local --native evidence/importer-loud-fail/r192/native --output /tmp/nearest-cache-local.json
python3 -m unittest tools.tests.test_nearest_cache_local
```

Next discriminator: bind original texels and geometry-only local coverage to a live GPU cache texture, feed actual FilterGroup with the full authored20-value ColorMatrix, then apply the retained native post-CXFORM/ordinary composition. Require exact four pinned final images and cache/alpha boundaries; explicitly leave intermediate RGB unclaimed unless separately captured. No production enabling from a diagnostic pass.

`cpu_final_wrapper_exact=true`, `matrix_rgb_intermediate_proved=false`, `general_cache_initializer_admitted=false`, `production_admitted=false`. Production54 historical9/54; live complete images remain24 until GPU gate. Full AS/clip-action ownership open. Draft only.
