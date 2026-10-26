# r232: nearest source-code controls locate a coordinate-path failure

Generate source bytes independently as R=2x,G=6y,B73,A255. Authored smooth65 retains original raw shape56/57 tags. The explicit nearest67 countercontrol changes exactly one parsed active bitmap55 fill-type byte per shape; dormant style, matrices, mask records and all remaining bytes stay unchanged. Original references and locked input SWFs are not rewritten.

64nativeimages/589824RGBA,7360source pixels and8matrix groups are verified; outside clips remainclear. Smooth full images reproduce the assembled pinnedr223 horizontal-red/vertical-green/shared-blue-alpha references **73728/73728** pixels.

All **18216/18216** geometry-deep nearest samples are compatible with the independently generated texel codes. No incompatible/nonopaque sample is removed from any model denominator. Six fixed coordinate constructions remain rejected; scaled-child/minimum matches **17077/18216**.

- Shape56 authored minifying scale: nearest full0/48 in both cache states.
- Shape56 scale1: uncached4192/4192; cached4191/4192.
- Shape57 originalscale:260/260 in both cache states.
- Shape57 scale1:uncached3825/4320;cached3827/4320.

The large discrepancy exists in nearest sampling too; smooth weight arithmetic alone cannot fix it. Compatible source codes are measurements, not output-selected render coordinates. Compound-fill transfer and cache postprocessing remain unproved. All model failures and measured source-cell deltas are retained.

## Reproduce

```sh
python3 -m tools.probes.build_jinye_sampling_modes --output /tmp/bvn-r232/native --ffdec /tmp/bvn-loud-fail/r02/ffdec/ffdec-cli.jar
# Capture mode65 and mode67 sequentially with capture_native_player.py.
python3 -m tools.probes.analyze_jinye_nearest_origin --native evidence/importer-loud-fail/r232/native --output /tmp/bvn-r232/analysis.json
python3 -m unittest tools.tests.test_jinye_sampling_modes_controls tools.tests.test_jinye_nearest_origin_analysis
```

Mandatory gates and focused tests in acceptance.json/checks; retained fullPython1011pass/2skip. No production/GPU edits or fresh roster/Web/54production suite. Complete diagnosticcoverage46/54, historicalproduction9/54; fullAS/clip-actionownershipopen. Candidate/GPU/productionadmissionfalse.

## Next discriminator

Independently vary authored fill translation by exact integer twips while display matrices remain fixed, then vary draw translation separately. Keep coordinate-coded inputs, quad geometry and linear matrices, and retain exact parsed raw-fill bits plus actual display property readbacks. Match the unchanged baseline to this round before comparing globally defined composition/translation-consumption sequences. Use geometry-common interiors when draw moves the quad. Reject against old nearest/smooth controls; never fit an offset or select a coordinate from local RGB.
