# r236: authored fill factorization isolates cache-dependent differences

Reuse original Jinye shape56/57 active raw16.16 fill coefficients, integer-twip translations and masks. Keep dormant style bytes verbatim. S=identity/horizontal±2/vertical±2; F'=S F, C'=C inverse(S), mask'=S mask. Original C/outer remain exactly representable after factoring; raw emitted bits and actual native property readbacks independently prove equal final matrices and complete stage masks. Drawscales1/8,1/4 and geometry-derived integer cameras keep full masks inside256x256. Original nearest67 tags remain separate from identity reencoding.

48nativeimages/3145728rawRGBA;3680source pixels and24matrix readbacks verified. FFDEC independently checks all12tags. Native15-significant-digit text is validated separately from recovered exactfloat32 properties, including a half-up tie; this is transport validation, not changed rendering arithmetic. Original printed bytes remain in the logs. Large FFDEC float fields are likewise checked using their typedfloat32 representation, not approximate decimal thresholds.

Both rawRGBA and independently measured black-composition planes show:

- Original raw tags vs reencodedidentity: **8/8**,524288/524288fullpixels exact.
- Uncached factor pairs: **40/40 full images exact**.
- Cached factor pairs:20/40full images exact;20pairs differ at58pixel comparisons. Across all80pairs:5242822/5242880fullpixels exact.
- Deep geometry differences:28/21820, all10cached shape57scale1/4 factor pairs. Every differing deep pixel is opaque and has a valid source coordinate code; no sample is removed. All uncached deep comparisons exact.
- Cache-state pairs:15/24full images exact,1572844/1572864pixels exact (20differences);10differences in6546deep comparisons.

Raw maxRGBA delta3,7,0,0; independently measured black delta2,6,0,0. Geometry-only comparison scopes and every failure are retained. Native cached results can differ despite identical final affine mapping and stage mask; getBounds values also differ, but no allocation origin is inferred from them. Uncached factorization equivalence does not solve the older uncached Jinye initializer failures.

## Reproduce

```sh
python3 -m tools.probes.build_jinye_source_factorization --output /tmp/bvn-r236/native --ffdec /tmp/bvn-loud-fail/r02/ffdec/ffdec-cli.jar
python3 tools/probes/capture_native_player.py /tmp/bvn-r236/native /tmp/bvn-r236/native/native.log --player-app '/Users/fengkx/me/code/flash-player/Flash Player.app' --allow-window-activation --timeout 90
python3 -m tools.probes.analyze_jinye_source_factorization --native evidence/importer-loud-fail/r236/native --output /tmp/bvn-r236/analysis.json
python3 -m unittest tools.tests.test_jinye_source_factorization_controls tools.tests.test_jinye_source_factorization_analysis
```

Focused7/7 and mandatory gates recorded; fullPython1059pass/2skip retained fromr235 and exact axis suites fromr229. No production/GPU edits or new roster/Web/54production run. Diagnosticcomplete46/54,historicalproduction9/54. Candidate/GPU/production admission false; AS/clip-action ownership open.

## Next discriminator

Isolate bounds metadata from geometry: conservatively expand only authored ShapeBounds outward by predeclared integer twips, retaining fill, edge records, child/outer/draw transforms and source pixels exactly. Independently vary left/top origins versus right/bottom extents, with both cache states and an unchanged baseline. Verify valid enclosure and actual getBounds/property readbacks before comparing full/deep rawRGBA and black outputs. This can constrain cache-bound setup, but must not assume getBounds equals allocation origin or pick a route from output pixels.
