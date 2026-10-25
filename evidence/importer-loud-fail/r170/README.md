# r170 — one geometric initializer clears all retained affine controls

The r169 axis-separated shear observations motivate one fixed construction, used uniformly for every source coordinate:

`q = a*x + b*y + t + sqrt(a*a+b*b)/2 + min(0,a) + min(0,b)`

Here(a,b,t) is one inverse-matrix row. No native RGB selects the arithmetic or any coefficient. Square-root comparisons use exact rational inequalities, including integer equality; no float epsilon or tolerance. Three globally fixed arithmetic variants are tested, with every failure retained.

Both fixed16.16 inverse variants are **49309/49309 exact** across r158/r162/r163/r164/r165/r166/r168/r169. The unquantized inverse variant has40 counterexamples and is rejected. Quantizing the geometric offset itself to16.16 remains indistinguishable from retaining its exact norm on these controls; its precision is not claimed as established.

This clears all controls used here, including distant coordinates, independent axis/shear coefficients, source/mask sizes, split translations, consumed fractional fill inputs, integer phase sweeps and horizontal/vertical shear. Old interval constraints are retained implicitly by matching every underlying observation. This remains a diagnostic construction, not proof for arbitrary affine/source-boundary coverage or production assets.

[Summary](summary.json), [all failures](failures.json.gz), [provenance](provenance.json), [acceptance](acceptance.json).

```sh
python3 -m tools.probes.analyze_affine_footprint --output /tmp/affine-footprint.json
python3 -m unittest tools.tests.test_affine_footprint
```

Next discriminator: independently capture held-out non-axis-aligned matrices, scale factors and reflected transforms, preserving actual source bytes and child/draw properties at distant coordinates. Test the same globally fixed construction, including integer-boundary counterexamples, before considering GPU binding. If both offset precisions remain indistinguishable, retain that uncertainty rather than choosing a path from pixels.

`candidate_admitted=false`, `gpu_advance_allowed=false`, `production_admitted=false`. Production54 remains historical9/54;24 original live/wrapper diagnostics exact. AS ownership remains open. Draft only.
