# r126 — second component is exact with its authored inner transform retained

The second Jiraiya source binding reads original bitmap166 premultiplied texels and shape276 mask, validated against r125 source tags. Both inner placement(-17,-10)twips and fill(+17,+10)twips remain in metadata. Cache bounds are computed in wrapper coordinates; wrapper normalization is followed by the independently constrained quarter-pixel inner-translation composition. The owner-alias matrix is never substituted for the primitive matrix.

At all three r124 integer offsets, source-derived cache images are **720000/720000 exact**. The unchanged vertical Blur0x15/quality1 yields authored output **720000/720000 exact**. Ordinary composition reproduces the two original depth29 references: **480000/480000 exact**. Local cache45x46 has transform sx1.170257568359375/sy1.1563720703125/tx-0.75/ty-0.25, placed at x150/278/406,y177. The nonzero local transform demonstrates why simply deleting cancelling source offsets was not assumed.

All fractional edges retain the existing nontransparent-corner rejection. No RGB-selected route, tolerance, native-input texture or per-fighter production special case is added. These are source-derived CPU diagnostics; GPU binding remains a separate gate.

## Reproduce

```sh
python3 -m tools.probes.analyze_translated_component_cache --output /tmp/translated-cache
python3 -m unittest tools.tests.test_translated_component_cache
```

[Summary with authored matrices/computed bounds](summary.json), six derived images under `images/`, [pinned source/native provenance](provenance.json), [acceptance](acceptance.json).

Next discriminator: use one shared live GPU cache/filter/composition fixture for both Jiraiya components, varying local dimensions and authored horizontal/vertical Blur rather than copying per-component arithmetic. Retain original masks/inner transforms and compare all four pinned native images. Keep production admission false until source eligibility and the remaining coverage/affine/AS gates are justified.

`source_derived_cpu_component_exact=true`, `gpu_binding_verified=false`, `production_admitted=false`. Historical production54-suite9/54, not rerun. Draft only; no merge/deploy/Worker.

Validation: focused Python2/2; prior r124 full789 pass+2skip retained. Fresh caches26/26, fingerprint, protected, integrity/handoff/contracts green. Production unchanged; roster/Web and GPU not rerun.
