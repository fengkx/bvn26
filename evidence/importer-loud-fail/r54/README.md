# r54 — complete predefined measured factorization grid rejected

No rendering, production change, tolerance, allowlist or fitted coefficient.
Complete the r53 grid using all seven independently measured r41 reciprocal
constructions, all three independently measured r44 source normalizations and both
fixed operation orders:42 models. Every model consumes integer offsets and1/256
multipliers and checks all1,302,912 old/signed RGB controls.

**0/42 models match all four alpha49/alpha33 sites.** Best total is
**1,276,643/1,302,912** (`estimate_quotient/divide/gain_first`), still rejected.
Every model fails old controls. The12 r53 models retain identical full scores,
counterexample lists and paired-site outputs, checked by regression tests.

The report retains every counted failure. No alpha-specific construction selection
or interval endpoint is used. Original bounds and source evidence are unchanged.
Candidate/GPU/production flags remain false. Native-buffer43006/43200, nested
GPU67774/72576, historical components9/54 and AS ownership remain open.

## Reproduce / validation

```
python3 -m tools.probes.analyze_cxform_factor_grid --output evidence/importer-loud-fail/r54/analysis.json.gz
python3 -m unittest tools.tests.test_cxform_factor_grid tools.tests.test_cxform_scaled_inverse tools.tests.test_cxform_signed_bounds
```

Analysis exits1. Targeted tests8/8; integrity/handoff/contracts rerun. Older probes
and runtime are unchanged; latest full Python r51(627+2skip), cache/fingerprint/
protected r49(caches26/26), exact rendering r48. No new rendering/full roster/Web
export or54-component measurement.

## Next discriminating experiment

For each independently measured source-normalization table, derive rejection-only
feasibility intervals for a single unknown normalized-alpha reciprocal under the
fixed source-first operation sequence. Retain signed monotone-decreasing controls
and zero-source cases. If old controls require disjoint intervals, record the exact
native lower/upper witnesses: that rejects the entire sequence regardless of its
reciprocal construction. If nonempty, do not choose coefficients from it. These are
new sequence-specific bounds; never replace or reinterpret the old r48 bounds.
