# r53 — paired success rejected by all older controls

No rendering, production change, tolerance, allowlist or fitted coefficient.
The independently defined normalized inverse is `f32(255 * estimate(integer_alpha))`,
not an estimate of normalized alpha. Source bytes use each of the three previously
independently measured normalization sequences. Also retain correctly rounded
integer reciprocals as controls and source-first/gain-first operation orders.
All consumed integer offsets and 1/256 multipliers remain unchanged.

## Meaningful local success, explicit global rejection

Two of12 fixed models match **both alpha49 witnesses** and all **18,720/18,720 signed
channels**: integer reciprocal estimate + estimated source normalizer, with either
operation order. They still pass only **1,257,866/1,284,192 old channels**;26,326 fail.
Overall1,276,586/1,302,912 is not admission.

A concrete older counterexample is source31/alpha33/multiplier256/256/offset−4/
opacity33: native9 versus candidate10 (1,632 occurrences). Additional failures
include source32/alpha33/multiplier191/256/offset1/opacity100: native23 versus24.
There are failures in both directions, not a uniform correction. No per-alpha or
per-pixel splice is permitted. All12 models remain rejected globally.

The original reciprocal intervals remain unchanged and are not applied as if
factorized input normalization were one exact per-alpha multiplication. The full
compressed report retains all counted old/signed counterexamples. Tests preserve
paired success **and** global rejection, so this local result cannot enable a path.

## Reproduction / checks

```
python3 -m tools.probes.analyze_cxform_scaled_inverse --output evidence/importer-loud-fail/r53/analysis.json.gz
python3 -m unittest tools.tests.test_cxform_scaled_inverse
```

Analysis deliberately exits1. Targeted r48–r53 tests15/15 and integrity/handoff/
contracts are rerun; latest full Python is r51(627+2skip), full cache/fingerprint/
protected checks r49(caches26/26), rendering regressions r48. No older probe or
runtime was modified, no rendering/full roster/Web export rerun.

All admission flags stay false. Native buffers43006/43200, GPU nested67774/72576,
historical components9/54 and full AS/clip-action ownership still block merge.

## Next bounded experiment

Apply the same fixed source-normalization orders to the remaining independently
measured reciprocal constructions (product/quotient alpha normalizations), retaining
the paired alpha49 success and alpha33 counterexamples. Define the whole grid
before comparing, score every old/signed control, and never choose a construction
per alpha or from a native output. Admission still requires every pinned control
and native-buffer boundary before GPU work.
