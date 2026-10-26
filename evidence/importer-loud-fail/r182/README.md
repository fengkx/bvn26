# r182 — vertex and scan quantization narrow coverage failures to256

Thirty globally fixed geometric constructions compare exact/quarter-quantized vertices, independent X/Y sample phases and screen-space top-left half-open scan lines. Scan intersections use exact rational arithmetic. No native RGB selects a construction or arithmetic branch.

Closest: quarter-nearest-half-up vertices, quarter-row scan positions and half-up horizontal intersections, **161094/161350 exact**,256 failures,max channel delta64. This improves the prior point-grid blocker2838→256 but is still rejected. All alternatives and per-coordinate counterexamples are retained. The original main affine constant-rectangle case still has8 failing pixels across its bitmap/vector pair.

[Summary](summary.json), [all failures](failures.json.gz), [provenance](provenance.json), [acceptance](acceptance.json).

```sh
python3 -m tools.probes.analyze_affine_scan_coverage --native evidence/importer-loud-fail/r181/native --output /tmp/scan-coverage.json
python3 -m unittest tools.tests.test_affine_scan_coverage
```

Next discriminator: independently move one authored axis-aligned rectangle edge on exact twip coordinates, read back local getBounds, and use half-scale transforms to produce exact device-quarter midpoint ties. Bitmap/vector controls must isolate vertex consumption/rounding before changing scan interpolation. Retain all33 affine cases. Do not derive a vertex rule from whichever pixel happens to match; negative coordinates and arbitrary polygon/source-edge behavior remain unproven.

`coverage_admitted=false`, `production_admitted=false`. Original main15 nonzero edge pixels remain gated; production54 historical9/54;24 complete live/wrapper diagnostic images exact. Full AS ownership remains open. Draft only.
