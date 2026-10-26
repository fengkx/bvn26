# r56 — exhaustive bounded hardware-image rejection

No Flash/Godot rendering or production change. Independently enumerate the actual
x86/Rosetta reciprocal-estimate output for **every67,108,865 float32 input** in the
fixed normalized-byte domain[1/256,1]. This domain is chosen independently of native
feasible intervals and includes the positive-byte normalization cases under study.
Read back nearest rounding mode, retain contiguous constant-output runs, and restore
the initial CSR. There are27,153 output runs and zero increasing transitions.

## Stronger rejection

Compare the complete measured output image against r55's source-specific bounds:

| Source normalization | Alphas with no reachable hardware output |
|---|---|
| divide | 1:204 |
| multiply rounded reciprocal | 1:204 |
| multiply estimated reciprocal | 48, including49 and204 |

Therefore a **single unscaled reciprocal estimate** cannot satisfy all native
controls for any of these source-first sequences, regardless of input normalization
within the measured domain. This is not a claim that Flash uses that instruction,
and does not reject post-estimate scaling, combinations, or different operation
orders. No input/output is selected from the feasible intervals.

At alpha204 the decisive native witnesses are:

- source164, multiplier192/256, offset0, opacity100 →123 (r40 alpha row614/x22).
- source103, multiplier2047/256, offset−897, opacity100 →105 (r44 row3620/x9).

Divide/rounded-source bounds are bits1067450369..1067450397; estimated-source bounds
are1067450529..1067450558. None contain any measured output. Raw contiguous runs,
source/executable/output hashes, environment and all native witnesses are retained.
The original bounds and native controls are unchanged.

## Reproduce / checks

```
clang -arch x86_64 -O2 -ffp-contract=off tools/probes/cxform_reciprocal_image.c -o /tmp/bvn-r56/image
arch -x86_64 /tmp/bvn-r56/image > /tmp/bvn-r56/hardware.txt
python3 -m tools.probes.analyze_cxform_reciprocal_image --hardware /tmp/bvn-r56/hardware.txt --output evidence/importer-loud-fail/r56/analysis.json.gz
python3 -m unittest tools.tests.test_cxform_reciprocal_image
python3 -m unittest discover -s tools/tests
```

Analysis exits1. Tests reject missing/reordered runs and recompute every interval's
reachable count. See acceptance.json for fresh checks. No old probe/runtime/reference
change; no additional rendering/full roster/Web export. Latest cache/fingerprint/
protected checks remain r49(caches26/26); exact rendering regressions remain r48.

Admission flags remain false; native buffers43006/43200, GPU67774/72576, historical
components9/54 and full AS/clip-action ownership still block merge.

## Next bounded discriminator

Measure output images for the already independently defined post-scaled reciprocal
constructions, using fixed corresponding integer/product/quotient input domains and
explicit float32 operations. Retain alpha204 and the signed alpha49 witnesses. Reject
an entire construction only when its full measured image misses a required interval;
a reachable value does not identify a normalization function or admit coefficients.
