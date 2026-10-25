# r112 — device-space origin construction clears two independent cache suites

Following the r111 sampled caller, static field setup at0x10015e678 copies an affine matrix and replaces its translation with stored origin fields;0x10015e795 inverts it and stores only inverse translation into an identity matrix at object offset0x3d8. The sampled caller later composes that field through a device-scale constructor. Short instruction spans and float32 constant0x3d4ccccd (0.05) are independently pinned. Specific branch/field values remain unverified at execution; this is a constrained candidate, not a proven decompilation.

The common diagnostic uses device scale `f32(f32(4*f32(0.05))*f32(scale))`, inverse-origin conversion to nearest-even integer local units, then float32 forward translation rounded to device subpixels. The4-subpixel grid and separate child/draw translation consumption come from earlier independent controls; no coefficient is selected from output pixels. Both authored-bounds and consumed-bounds geometric origins remain reported, with no per-case route selection.

| Suite | Old baseline | Device + consumed bounds | Maximum delta remaining |
|---|---:|---:|---:|
| r101 |37842/37842|37842/37842|0|
| r102 |210078/240900|228317/240900|19|
| r103 |53556/68544|**68544/68544**|0|
| r104 |16379/19980|**19980/19980**|0|
| r109 |10228/15048|14854/15048|10|

The candidate remains rejected. r102 leftovers are12571 pixels at scale7 with fill minima0.25/0.5/-0.5, plus12 pixels at scale1.24481201171875/minimum-2. r109 has194 leftovers in the transparent/opaque minimum-0.5,scale7,inner-0.5,outer128 pair. The exact zero-fill suites do not authorize choosing a formula for nonzero fills or changing production.

## Reproduce

```sh
python3 -m tools.probes.extract_cache_normalization_binary --binary '/path/to/Flash Player Debugger' --output /tmp/cache-normalization-static.json
python3 -m tools.probes.analyze_cache_device_origin --output /tmp/cache-device-origin.json
python3 -m unittest tools.tests.test_cache_device_origin
```

[Summary](summary.json), per-case failure counts and native witnesses in `analysis.json.gz`, [static bytes](static-binary.json), [provenance](provenance.json), [acceptance](acceptance.json). Old source/readback hashes are retained; no fresh references rewritten.

Next discriminator: independently vary the bitmap fill's nonzero translation while holding geometry bounds and node/draw transforms fixed, then move geometry bounds with fill translation fixed. Retain zero-fill controls, signed origins, scale7 and the noninteger-scale/-2 counterexample. This separates fill-matrix concatenation from cache-bounds normalization before changing either operation order. The one common construction must pass all old cache and exact sampler controls before GPU work; no per-fill or RGB-selected splice.

`candidate_admitted=false`, `gpu_advance_allowed=false`, `production_admitted=false`. Components historical9/54, no rerender or production/GPU change. General affine/coverage and full AS/clip-action ownership remain separate merge blockers. Draft only; no merge/deploy/Worker.
