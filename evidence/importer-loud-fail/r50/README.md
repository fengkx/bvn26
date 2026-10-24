# r50 — precomputed affine orders retain a positive-control blocker

Diagnostic only; no rendering or production changes. All inputs retain consumed
integer offsets and 1/256 multipliers. Native controls and all older bounds remain
unchanged. No coefficient is chosen from an interval or output byte.

## Fixed operations

Use each of the seven independently measured r41 reciprocal constructions with:

1. Unit gain: compute `gain=f32(reciprocal*f32(multiplier/256))` and
   `bias=f32(offset/255)` before the source multiplication, then clamp, premultiply
   by alpha and apply quantized opacity, with explicit float32 operations.
2. Premultiplied gain: additionally multiply gain and bias by alpha before applying
   the source byte; clamp to `[0, alpha]`, then apply opacity.

The old reciprocal intervals describe the old operation order. Their memberships
are retained for comparison, **not** misused as bounds on these new sequences.
Every sequence is checked directly against all1,302,912 old/signed RGB controls.

## Result

**0/14 models match both alpha49 witnesses.** All produce12 at the old positive
witness where native is11. Four models (`estimate_inverse` and `scalar_estimate`,
both orders) now match **18,720/18,720 signed channels**, but old controls remain
only1,255,698 or1,255,697 of1,284,192. This is a concrete reason not to admit a path
from signed-only success. The best total is1,276,409/1,302,912
(`estimate_quotient/unit_gain`), also rejected.

The compressed report retains counted counterexamples for every sequence and
sample group. Summary/provenance retain counts, paired sites and source hashes.
All admission flags remain false. Native buffers43006/43200, nested GPU67774/72576
and historical components9/54 remain unchanged; full AS ownership is still open.

## Reproduction / validation

```
python3 -m tools.probes.analyze_cxform_affine --output evidence/importer-loud-fail/r50/analysis.json.gz
python3 -m unittest tools.tests.test_cxform_affine tools.tests.test_cxform_refinement tools.tests.test_cxform_signed_bounds
```

Analysis exits1. Focused regressions9/9; integrity, handoff and contracts rerun.
No runtime or prior probe changed. r49 Python623+2skip, caches26/26, fingerprint and
protected results remain applicable; exact rendering/CPU evidence remains r48.
No additional rendering, full roster or Web export run.

Next independently compare offset normalization (division versus multiplication by
fixed rounded/measured reciprocal), without changing multiplier/source arithmetic
per pixel. Retain the pure-offset controls and paired alpha49 witnesses; any local
improvement must still satisfy all previous controls before rendering.
