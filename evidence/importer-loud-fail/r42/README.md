# r42 — channel identity does not bypass the unresolved arithmetic

No production or GPU implementation changed. `candidate_admitted=false`,
`gpu_advance_allowed=false`, `production_admitted=false`; the analysis exits **1**.
Row routing is unchanged. No interval endpoint or per-alpha fitted coefficient
is used to render a pixel. Earlier references remain unchanged.

## Native controls and explicit inputs

All probes use width32 and retain red/blue transforms .5/+8 and1/−4 in the
combined operation. Every stage records source/result transparent and black
readbacks; captures are complete, source-hash pinned and losslessly archived.

- `native/`: 46 retained alphas, green multipliers255/256,1,257/256, offset0,
  opacity33/67/100; **13248 pixels**.
- `stages/`: 11 alphas including both residual inputs and the tightened-alpha
  controls; the same multipliers, offsets−1/0/1, opacity33/67/100. Five separate
  BitmapData operations record **47520 stage pixels**: combined, multiplier-only,
  offset-only, multiplier-then-offset, and offset-then-multiplier. The latter two
  read the actual earlier stage buffers; the parser checks that equality.
- `zero/`: green input0 removes the reciprocal term, with eight alphas,
  offsets1/7/64/127/255 and opacity33/67/100; **3840 pixels**.

For green multiplier1/offset0, direct source-byte opacity scaling agrees in
1434/1472 samples at opacity33 and1472/1472 at67, but **0/1472 at100**.
Every full-opacity output is one green byte below its source. A channel-specific
identity bypass cannot explain these controls. This does not identify an ISA.

Materialized multiplier-then-offset equals the one combined native draw in only
**3728/9504 RGBA pixels** (3189 green differences, maximum RGBA delta1/1/1/0).
Offset-then-multiplier agrees in326/9504 (3302 green differences, maximum4/1/1/0).
The latter order also changes the real algebra for nonzero offsets; these are
observations, not assertions that the operations should be equivalent.

For example, case95/x26 reads `[62,108,127,135]`, with green multiplier1,
offset0 and opacity100. Combined green is107. Multiplier-only produces107;
the next offset-only operation reads that107 and produces106. Materialization
must not be replaced with a single combined transform.

The zero-green controls isolate offset normalization: division by255 gives
**3840/3840**, division by256 only2976/3840. This supports that premise within
these controls, without solving the reciprocal construction.

## Common-construction rejection

The unchanged r41 method intersects exact float32 feasibility bounds, retaining
native witnesses for both endpoints. All nine green-only models retain the old
constraints; the three combined RGB/alpha-first models now contain
**630144 constraints each** (436320 previous +193824 new). Each still has255
nonempty alpha intervals. New evidence tightens alpha146,197,206,244 in all
three spaces. Nonempty intervals do not authorize a per-alpha coefficient table.

The seven independently measured r41 constructions fit respectively
50,115,127,208,46,115,180 of255 intervals in unit space; normalized space gives
56,114,126,209,52,114,180, and byte space56,114,124,209,50,114,180.
**None clears every interval set.** All old constraints are retained, not replaced
with a locally successful fit. `analysis.json.gz` records bounds, native witnesses,
construction exclusions and explicit mismatch coordinates.

The old native-buffer counterexample remains43006/43200 for the r39 candidate;
the rejected r40 normalized candidate remains43176/43200 while regressing old
controls. Neither is promoted. The72576-pixel GPU gate is deliberately not rerun
with an unproved model (historical67774/72576).

## Reproduction and acceptance

```sh
python3 -m tools.probes.analyze_cxform_identity \
  --root evidence/importer-loud-fail/r42 \
  --output /tmp/r42-analysis.json.gz  # expected exit 1
python3 -m unittest tools.tests.test_cxform_identity
python3 -m unittest discover -s tools/tests
```

Capture build commands, source/SWF hashes and player environment are retained
under each capture directory. `provenance.json` pins analysis inputs/outputs.
Five new tests validate native source bytes, actual materialization inputs,
zero-green isolation, exact interval witnesses and rejection of tampered input.

Fresh checks are recorded in `acceptance.json` and `checks/`: Python598 tests,
596 passed/2 skipped; r36 composition4032/4032 and pinned Yulong4/4;
r37 nested composition124416/124416; leaf6/6 (69120 pixels), isolated Glow4/4,
GPU sampler71824/71824 and all CPU sampler regressions exact. Cache/build-manifest,
fingerprint, protected function, integrity, handoff and contracts are checked
separately in those logs. No full roster replay, Web export, production component
remeasurement or failing nested-filter GPU rerun is claimed for this probe-only
change.

## Remaining blocker and next discriminating experiment

The green identity bypass is rejected and offset normalization is independently
constrained; the shared reciprocal construction/operation sequence remains
unknown. Next, amplify differences between independent constructions using the
same explicit input readbacks at the four tightened alphas: sweep globally fixed
larger multipliers with negative offsets keeping results away from clamping.
Intersect all old bounds before accepting anything. Do not select coefficients
from the feasible intervals or choose a formula from the observed pixel.

Production components remain the historical9/54; general coverage/affine,
nested filter CXFORM and full AS/clip-action ownership remain merge blockers.
Draft only; no production admission, merge, deployment or Worker changes.
