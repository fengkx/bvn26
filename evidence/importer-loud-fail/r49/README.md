# r49 — fixed reciprocal refinement rejected at both alpha49 witnesses

No rendering, production change, tolerance, allowlist or fitted coefficient. All
operands retain r47 consumption: integer offsets and toward-zero 1/256 multipliers.
The signed native controls and every old bound/control remain in the comparison.

## Independent definitions

From the previously independently measured reciprocal estimate r for input a, test
one/two iterations of `r * (2 - a*r)` and `r + r*(1 - a*r)`, rounding each indicated
operation to float32. Also test one iteration after each of the three independently
measured input-normalization sequences, then convert to the unit coefficient.
These ten constructions never read an interval endpoint or native output. They
are arithmetic hypotheses, not a claim about Flash's instructions or algorithm.

Each construction is tested with all three coefficient spaces and three operation
orders: 90 models. The original sequences and pinned evidence are unchanged.

## Paired discriminator and global rejection

- Signed: source25, alpha49, multiplier−129/256, offset128, opacity100 → native12.
- Old upper witness: source23, alpha49, multiplier2046/256, offset−894,
  opacity100 → native11; source r46 brackets row328/x1/green.

**0/90 models match both.** In unit/alpha-first all ten produce11 at the signed
site and12 at the older upper witness: the error changes sign between the controls.
The best global model is `normalized_multiply_estimated_product/unit/alpha_first`:
1,253,245/1,284,192 old channels plus18,496/18,720 signed channels, or
**1,271,741/1,302,912**. This is a rejection count, not a selected implementation.
All90 models violate old interval bounds. The full report retains every counted
counterexample and all255 constructed coefficient bits for reproducibility.

The new hypothesis therefore does not resolve reciprocal/input-normalization
arithmetic. More accurate reciprocal refinement is not sufficient. No model
advances to the pinned native-buffer/GPU gates; all admission flags remain false.

## Reproduce

```
python3 -m tools.probes.analyze_cxform_refinement --output evidence/importer-loud-fail/r49/analysis.json.gz
python3 -m unittest tools.tests.test_cxform_refinement
python3 -m unittest discover -s tools/tests
```

Analysis deliberately exits1. Tests lock construction independence, explicit
float32 refinement, all old/signed sample counts, endpoint witness and rejection.
`provenance.json` pins sources and reused native evidence. `acceptance.json` records
fresh checks. Existing exact rendering/CPU suites are unchanged and retain r48
verification; no additional rendering was performed before arithmetic admission.

## Next round and remaining blockers

A separate common-operation hypothesis can move multiplier/offset normalization
into precomputed affine coefficients instead of normalizing each source pixel.
Define each operation order before reading outputs, test both witnesses, and reject
against all controls; do not apply r48 coefficient intervals to a different operation
sequence as if they were universal. Keep the old sequence's bounds intact.

Native-buffer status remains43006/43200, GPU nested67774/72576, components historical
9/54. Full AS/clip-action ownership is unresolved. Draft only, not merge-ready.
