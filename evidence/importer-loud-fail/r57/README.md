# r57 — bounded post-scaled reciprocal images also reject source-first order

No Flash/Godot rendering or production changes. Independently enumerate every
float32 input in four fixed domains for the already defined post-scaling operations:

| Construction | Domain | Inputs | Unreachable alpha counts: divide / rounded / estimated source |
|---|---|---:|---|
| estimate(x) ×255 | [1,255] | 67043329 | 78 /78 /78 |
| (estimate(x) ×255) ×255 | [255,65025] | 67043585 | 75 /74 /76 |
| (estimate(x) /255) ×255 | [1/256,1] | 67108865 | 1 /1 /48 |
| (estimate(x) ×estimate(255)) ×255 | [1/256,1] | 67108865 | 48 /48 /67 |

Each operation is an explicit x86 float32 intrinsic. Read back nearest rounding
mode, retain contiguous output runs, restore initial CSR. Total268,304,644 inputs.
All **1020/1020 independently measured r41 construction controls** match the new
images exactly; no inferred coefficient or selected input is used.

**Alpha204 is unreachable in every image/source-normalization combination** under
r55's source-first arithmetic. Thus these bounded images cannot satisfy all native
controls under that sequence, even allowing an unknown input normalization within
each domain. This does not infer Flash instructions or reject other operation orders.
Old bounds/native readbacks are unchanged. All admission flags remain false.

## Reproduction / validation

```
clang -arch x86_64 -O2 -ffp-contract=off tools/probes/cxform_scaled_reciprocal_image.c -o /tmp/bvn-r57/image
for mode in 0 1 2 3; do arch -x86_64 /tmp/bvn-r57/image "$mode" > "/tmp/bvn-r57/hardware-$mode.txt"; done
python3 -m tools.probes.analyze_cxform_scaled_image --hardware /tmp/bvn-r57 --output evidence/importer-loud-fail/r57/analysis.json.gz
python3 -m unittest tools.tests.test_cxform_scaled_image tools.tests.test_cxform_reciprocal_image tools.tests.test_cxform_normalized_bounds
```

Analysis exits1. Targeted tests6/6; integrity/handoff/contracts rerun. Latest full
Python r56:637+2skip, cache/fingerprint/protected r49:26/26, exact rendering r48.
No runtime/old probe change or additional rendering/full roster/Web export.
Native-buffer43006/43200, GPU67774/72576, historical components9/54 and AS ownership
remain blockers. Draft only.

## Next discriminator

For alpha204/source164/multiplier192/256/offset0, a normalized reciprocal1.25 gives
122 under source-first arithmetic but123 under gain-first arithmetic (native123).
Derive new gain-first bounds independently; do not apply source-first image rejection
to a different sequence. Also inspect the native binary read-only for potential
instruction sites, requiring actual execution evidence before assigning a role to
any static site. No static instruction/output agreement alone proves Flash routing.
