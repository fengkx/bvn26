# r185 — shared fixed scan stepping clears the original affine controls

Apply the r183/r184 independently constrained order: quarter ties-even of each transformed local vertex, followed by separately consumed child/draw translations. Exact rational edge intersections still leave64/161350 pixels wrong, maxRGBA delta16. The prior combined-translation vertex order left318 counterexamples.

A single scan construction clears **161350/161350 pixels**: orient each edge from lower Y, consume slope toward zero to16 fractional bits in quarter-pixel coordinates, initialize at its top endpoint, step that slope, and round intersections half-up. No RGB-dependent selection. Fixed8 and fixed24, floor and ties-even slope consumption, and exact-rational alternatives all have recorded counterexamples. This is a bounded hypothesis supported by old controls; it does not establish the renderer's internal representation or general coverage.

[All fixed constructions](summary.json), [rejected counterexamples](failures.json.gz), [provenance](provenance.json), [native controls](../r181/native/native.log.gz), [acceptance](acceptance.json).

```sh
python3 -m tools.probes.analyze_affine_scan_translation --native evidence/importer-loud-fail/r181/native --output /tmp/affine-scan-translation.json
python3 -m unittest tools.tests.test_affine_scan_translation
```

Next discriminator: independent authored long parallelograms with positive/negative slopes, heights7/31/127/257 and quarter-pixel origins. Keep constant source RGBA and bitmap/vector pairs. Require the one fixed construction to clear these held-out edges before combining it with original-main texel sampling; no coordinate patch or per-case arithmetic switch.

`coverage_admitted=false`, `production_admitted=false`. Original-main full images and15 nonzero edge pixels not yet remeasured. Production54 historical9/54; full AS/clip-action ownership open. No runtime changes; Draft only.
