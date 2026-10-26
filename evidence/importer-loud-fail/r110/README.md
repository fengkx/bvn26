# r110 — static affine candidates fail independent cache controls

Read-only inspection of the pinned installed Flash Player Debugger32 binary identifies affine composition at0x10029dad0 and inverse at0x10029de20, with fixed16.16 and float32 branches. [Static bytes](static-binary.json) retain the short relevant instruction spans and executable hash. **Execution routing is unverified:** these are static candidates, not proof that the cache probe uses these functions or branches. No debugger attachment or renderer modification was performed.

Two globally defined bounds-origin hypotheses are compared:

- Fixed16.16 inverse scale, translation products rounded individually with+32768 then shift16, and fixed forward recomposition.
- Float32 reciprocal/multiplications, nearest-even integer translation products, and float32 forward recomposition.

Both invert the authored translation and integer raster origin independently, combine their integer local translations, then recompose into a local raster matrix. The existing direct clipped sampler consumes that matrix. This explicit construction is a hypothesis; no origin, coefficient or branch is chosen from RGB. The float conversion's rounding mode is assumed nearest-even for this rejected hypothesis, not established as a cache execution fact.

| Native suite | Previous local-origin baseline | Fixed candidate | Float candidate |
|---|---:|---:|---:|
| r104 signed phases |16379/19980|12886/19980|12886/19980|
| r109 independent left bounds |10228/15048|6564/15048|6564/15048|

Both regress; maximum delta rises to28 on r104. They are rejected before any attempt to widen admission or bind GPU. Old reference bytes and all exact regression controls remain unchanged. r109's table here compares an arithmetic candidate to native, whereas its own7202/7524 figures compare shifted-bound native images to unshifted native images; those are different comparisons.

## Reproduce

```sh
python3 -m tools.probes.extract_cache_affine_binary --binary '/path/to/Flash Player Debugger' --output /tmp/cache-static.json
python3 -m tools.probes.analyze_cache_affine_candidate --output /tmp/cache-affine.json
python3 -m unittest tools.tests.test_cache_affine_candidate
```

[Analysis](analysis.json), [provenance](provenance.json), [acceptance](acceptance.json).

Next discriminator: identify the cache-specific normalization construction rather than substituting a generic inverse/compose pair. Inspect static callers for bounds-origin conversion and affine setup, retaining instruction bytes/constant words independently of output pixels. If no cache caller can be established, use explicit cache-boundary controls to distinguish rounding the origin before versus after the node transform, including binary-scale and negative-origin cases. Static agreement alone cannot establish routing; every proposed common construction must survive all old native controls before GPU work.

`candidate_admitted=false`, `gpu_advance_allowed=false`, `production_admitted=false`. Components historical9/54; source cache normalization, general affine/coverage and full AS/clip-action ownership still block merge. Draft only; no merge/deploy/Worker.
