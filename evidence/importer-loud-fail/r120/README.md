# r120 — original Jiraiya cache and authored Blur are exact from source

The common r116/r118/r119 source-origin construction and unchanged r112 normalization now render bitmap273/shape274/wrapper275 directly from the locked SWF's premultiplied texels, fill matrix and rectangular mask. Original nested transforms and outer draw translations are retained. No measured native input image enters the renderer.

At all three r100 integer offsets(-128,0,128), source-derived cache images are **720000/720000 premultiplied RGBA pixels exact**. Applying the unchanged integer Blur15x0/quality3 yields original authored output **720000/720000 exact**. All six full600x400 images match with zero channel deltas. Computed local cache75x74 has transform sx1.23333740234375/sy1.24481201171875/tx0/ty-0.25, placed at x135/263/391,y163.

The bounded renderer preserves the existing rejection of fractional coverage whenever a sampled corner is nontransparent. It does not claim arbitrary affine support, general coverage, nested opacity or a globally enabled production sampler. These are CPU source-derived component images, not a new54-suite production count.

## Reproduce

```sh
python3 -m tools.probes.analyze_jiraiya_source_cache --output /tmp/jiraiya-source-cache
python3 -m unittest tools.tests.test_jiraiya_source_cache
```

[Exact comparisons and computed buffer metadata](summary.json), six derived images under `images/`, [pinned source/native provenance](provenance.json), [acceptance](acceptance.json). Reuses pinned r89/r99/r100 native captures; no reference changes.

Next discriminator: feed the same source-derived local cache transform and original texels/mask through the admitted diagnostic GPU sampler, then actual FilterGroup buffer allocation/padding/pass nodes and integer final placement. Compare cache, padded input, filtered buffer and full original images, retaining all71824 sampler controls and six leaf images. Do not enable production from a diagnostic pass.

`source_derived_cpu_component_exact=true`, `gpu_binding_verified=false`, `production_admitted=false`. Historical production components9/54; AS/clip-action ownership remains separate. Draft only; no merge/deploy/Worker.

Validation: focused Python2/2; prior r119 full779 pass+2skip retained. Fresh caches26/26, fingerprint, protected, integrity/handoff/contracts green. No runtime change; roster/Web and GPU/component renders not rerun.
