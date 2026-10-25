# r173 — two common negative-term constructions remain indistinguishable

Keep the same fixed16.16 inverse and exact Euclidean-norm comparison. Test three complete, globally fixed constructions on all retained controls:

- Sum both negative components:59861/60645 exact; rejected.
- Use minimum(0,a,b):60645/60645 exact.
- Give a negative diagonal component priority, otherwise use the negative off-diagonal component:60645/60645 exact.

No per-pixel selection, fitted coefficients or tolerances. Both surviving constructions remain hypotheses; their agreement does not identify which operation Flash uses. All original source/native inputs are pinned, including the400 held-out reflections and384 phase counterexamples of the previous rule.

[Summary](summary.json), [failures](failures.json.gz), [provenance](provenance.json), [acceptance](acceptance.json).

```sh
python3 -m tools.probes.analyze_affine_negative_terms --output /tmp/negative-terms.json
python3 -m unittest tools.tests.test_affine_negative_terms
```

Next discriminator: independent reflected shears with off-diagonal magnitude larger than the diagonal, plus transposed and opposite-sign controls. Preserve factor1/factor64 zero-phase full images and integer-fill phase readbacks. These inputs separate the two surviving constructions without choosing from RGB. Reject any survivor against all old controls before GPU work.

`candidate_admitted=false`, `gpu_advance_allowed=false`, `production_admitted=false`. Production54 historical9/54;24 original live/wrapper diagnostics exact. Full AS ownership remains open. Draft only.
