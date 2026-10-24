# r43 — amplified reciprocal controls retain global rejection

No production or GPU implementation changed. `candidate_admitted=false`,
`gpu_advance_allowed=false`, `production_admitted=false`; analysis exits **1**.
No epsilon, channel tolerance, per-pixel operation selection or inferred
coefficient table is used. Row width/routing and earlier references are unchanged.

## Fixed experiment

The four tightened alphas are146,197,206,244. Every alpha uses the same grid:
base green gains2/4/8, each with adjacent−1/256,0,+1/256; green offsets
`−(gain−1)*128 + {-1,0,1}`; opacity33/67/100. Red/blue retain .5/+8 and1/−4.
There are324 width32 rows, **10368 pixels**. Requested green bytes120–135 repeat
twice across each row; red117/blue240 are unchanged. This fixed narrow input
range keeps the amplified results away from clamping. It is a new control, not
a rewrite of earlier input rasters or references.

Each operation reads back the actual source and result on transparent and black
destinations. The parser verifies source bytes against BitmapData quantization,
identical input bytes across transforms, output alpha and complete capture order.
Both exact rational transformed green and native output green are strictly inside
their clipping bounds for every sample. No clipping samples are discarded.
The original trace is losslessly archived with raw/compressed hashes in `native/`.

## Results and intersection with all prior bounds

All nine previously tested space/order models receive the new green constraints.
The three alpha-first RGB models intersect **661248 constraints each**:
630144 retained r42 constraints +31104 new RGB constraints. No old bound is
relaxed. Every combined model still has255 nonempty alpha intervals; the four
new alphas tighten in all three spaces. Nonempty intervals are constraints, not
permission to choose a coefficient independently for each alpha.

Unit/alpha-first float32 intervals (inclusive):

| Alpha | Previous count | New count | Lower bits | Upper bits |
|---|---:|---:|---|---|
|146|178|39|0x3be07070|0x3be07096|
|197|1262|69|0x3ba65635|0x3ba65679|
|206|828|188|0x3b9f16a4|0x3b9f175f|
|244|388|70|0x3b864e16|0x3b864e5b|

Every bound retains a native witness. For example, alpha197's lower witness is
row121/x2, actual green94, multiplier4, offset−384, opacity67, native53.
Its upper witness is row147/x11, actual green101, multiplier8, offset−896,
opacity33, native37. `analysis.json.gz` contains all exact bounds/witnesses and
per-coordinate candidate failures, including all inherited constraints.

The independent constructions are the unchanged seven r41 measurements; they
receive no pixel data. New green scores below are identical across the nine
space/order variants; this experiment does **not** identify multiplication order.
All failures have maximum channel delta1, and remain failures.

| Independent construction | New green exact /10368 | All unit intervals /255 |
|---|---:|---:|
|rounded_inverse|10064|50|
|estimate_inverse|9712|115|
|estimate_product|9776|127|
|estimate_quotient|10368|208|
|rounded_product|10064|46|
|scalar_estimate|9712|115|
|estimated_normalizer|10336|179|

The locally exact `estimate_quotient` remains rejected by old bounds. Its global
coverage in normalized/byte space is209/255, also insufficient. The new controls
exclude one more alpha from `estimated_normalizer` (180→179) in every space;
byte-space rounded_inverse/rounded_product also lose one (56→55 and50→49).
No tested common construction covers every interval set. Agreement does not
establish an instruction choice, SIMD or a hardware-specific implementation.

## Strict regressions and reproduction

```sh
python3 tools/probes/build_flash_filter_probe.py --case cxform-amplified \
  --output /tmp/r43-native --ffdec "$FFDEC"
python3 tools/probes/capture_native_player.py /tmp/r43-native \
  /tmp/r43-native/native.log --player-app "$FLASH_PLAYER" --allow-window-activation
python3 -m tools.probes.analyze_cxform_amplified \
  --root evidence/importer-loud-fail/r43 \
  --output /tmp/r43-analysis.json.gz  # expected exit 1
python3 -m unittest tools.tests.test_cxform_amplified
python3 -m unittest discover -s tools/tests
```

`provenance.json` pins analysis/source/reference hashes. Native build/environment
records retain player version and source/SWF hashes. Four new tests verify the
common grid and explicit unclamped inputs, reproduce local exactness without
admission, validate every new bound witness and preserve contradictory intervals
rather than replacing them with a local fit.

Fresh results are in `acceptance.json` and `checks/`: Python602 tests (600 passed,
2 skipped); r36 composition4032/4032 and pinned complete Yulong4/4;
r37 nested124416/124416; leaf6/6 (69120 pixels), Glow4/4, GPU sampler71824/71824,
and all CPU sampler regressions exact. Old scalar3072, three-alpha25920 and both
held-out span8652 controls remain covered by the existing Python regressions.
Cache/build-manifest26/26, fingerprint8/8, protected, integrity, handoff and
contracts pass. No full roster replay or Web export was rerun for this probe-only
change; no production component remeasurement is claimed.

## Blocker and next experiment

No common reciprocal construction/sequence is admitted. Native filter-buffer
counterexamples remain the historical r39 **43006/43200**; no new formula was
advanced to the72576 GPU nested-filter gate (historical **67774/72576**).
Production components remain historical **9/54**. Full AS/clip-action ownership
is still a separate merge blocker.

The amplified four-alpha controls constrain coefficients more tightly but cannot
distinguish operation orders. Next apply this same fixed transform/input grid to
the old rejected alphas, including14/135, while retaining these four. Compare
independently measured input-normalization and reciprocal operation sequences
against all old intervals before any rendering experiment. Do not choose an
interval endpoint, a different formula per alpha, or a path from output RGB.

Draft only; no production admission, merge, deployment or Worker change.
