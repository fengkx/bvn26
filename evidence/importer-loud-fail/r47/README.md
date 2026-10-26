# r47 — multiplier consumption independently measured at sub-1/256 steps

No production or GPU implementation changed. Raw and quantized diagnostics both
retain `candidate_admitted=false`, `gpu_advance_allowed=false`,
`production_admitted=false`; analysis exits **1**. No epsilon, tolerance,
interval-derived coefficient, per-alpha splice or per-pixel formula selection.

## Fixed sources and fine multiplier properties

Retain all48 verified r46 source rows, including center and neighboring alphas.
Offsets are fixed at their authored integers; r46's offset-consumption rule is
retained for old controls. Each source is allocated once and reused across13
multiplier changes, in units of1/65536:
`{−256,−255,−129,−128,−127,−1,0,1,127,128,129,255,256}`.
These span neighboring1/256 anchors, half steps and their adjacent fine values.
Source bytes, full32-pixel geometry and opacity stay fixed.

The native capture contains **624 target samples,19968 row pixels**. Every
source/result has transparent and black readbacks, and the probe explicitly
records `greenMultiplier*65536` after draw. All supplied fine property values are
preserved; every source matches the pinned earlier row. Center transforms remain
**1536/1536** exact, with no rational green clipping.

Native-only comparisons against coarser multiplier anchors give:

| Positive multiplier hypothesis | Exact RGBA /19968 |
|---|---:|
|floor to1/256|19968|
|nearest1/256, half upward|16830|
|toward-zero to1/256|19968|

Positive values cannot distinguish floor from truncation. No rule was inferred
from the offset experiment or from positive values alone.

## Independent signed multiplier controls

`cxform-multiplier-signed.as` uses alphas49/51/135/204/255 and multiplier centers
−0.5,0,+0.5 with the same13 fine deltas. Constant source RGB(117,128,240), integer
green offset128 and opacity100 keep these controls away from clipping; enclosing
red/blue transforms remain nonidentity. Property readbacks again preserve every
fine multiplier. The195 rows contain **6240 RGBA samples**.

| Signed multiplier hypothesis | Exact RGBA /6240 |
|---|---:|
|floor to1/256|5760|
|nearest1/256, half upward|5664|
|toward-zero to1/256|6240|

Combined positive and signed native-anchor controls are **26208/26208 exact**
for toward-zero consumption on the1/256 grid. This constrains this tested long-row
BitmapData.draw path; it is not a claim about every Flash API, scalar path,
property storage type, instruction selection or SIMD.

## Common diagnostic rule, all old bounds retained

Apply one uniform diagnostic rule `int(multiplier*256)/256` before the existing
arithmetic, retaining the independently supported integer-offset consumption.
All previous multipliers already lie on this grid, so their operands, interval
bounds and direct-sequence predictions remain unchanged. Never choose a rule
from the locally matching native byte.

The positive-multiplier constraint set grows **1224288→1284192 RGB channels**.
The raw fine-multiplier model makes11 alpha intersections empty. Quantizing the
multiplier removes all empty intersections across the nine green space/order
models and three combined RGB models, without relaxing any old bound.

Signed controls add **18720 directly checked RGB channels**. They are not fed to
the existing interval solver: its binary search assumes the output is increasing
in the reciprocal coefficient, which is false for negative multipliers. They are
retained in direct fixed-sequence scores, not silently discarded or counted as
positive-multiplier interval constraints.

| Fixed normalization sequence | Fine target exact, raw→quantized /624 | New positive RGB exact, raw→quantized /59904 |
|---|---:|---:|
|divide|533→564|57257→58190|
|multiply rounded1/255|532→558|57248→58136|
|multiply estimated1/255|510→486|56606→55994|

The estimated-normalizer comparator gets worse despite the independently exact
native-anchor rule: old arithmetic errors can cancel. This is why local scores
cannot select a consumption rule or a per-alpha formula.

All three quantized sequences give18688/18720 on the signed RGB controls. The
remaining32 repeated green counterexamples have source `[25,49]` (green,alpha),
multiplier−129/256, integer offset128, opacity100: native12, comparator11.
Maximum remaining channel delta is1; every difference remains a failure.
The best positive target result still has60 counterexamples. Alpha/opacity order
variants remain indistinguishable on these bounded controls.

Unit combined interval coverage of the seven old constructions is unchanged at
**50,105,118,208,46,105,177 /255**; no space exceeds209/255. Additional factorized
normalization constructions also fail. No common reciprocal/input-normalization
sequence is admitted. `analysis.json.gz` preserves raw contradictions, adjusted
bounds/witnesses, signed controls and exact per-coordinate failure evidence.

## Reproduction and strict regressions

```sh
python3 tools/probes/build_flash_filter_probe.py --case cxform-multiplier-fine \
  --output /tmp/r47-native --ffdec "$FFDEC"
python3 tools/probes/capture_native_player.py /tmp/r47-native \
  /tmp/r47-native/native.log --player-app "$FLASH_PLAYER" --allow-window-activation
# Build/capture cxform-multiplier-signed into a separate directory as well.
python3 -m tools.probes.analyze_cxform_multiplier \
  --root evidence/importer-loud-fail/r47 \
  --output /tmp/r47-analysis.json.gz  # expected exit 1
python3 -m unittest tools.tests.test_cxform_multiplier
python3 -m unittest discover -s tools/tests
```

Complete lossless captures, source/SWF hashes and player environment are under
`native/` and `signed/`; analysis/reference hashes are in `provenance.json`.
Four new tests enforce fixed input/property/center controls, independent signed
anchor discrimination, all old bounds and new raw/quantized native witnesses,
and global rejection with unchanged old predictions.

Fresh checks in `acceptance.json` and `checks/`: Python618 tests (616 passed,
2 skipped); caches26/26, fingerprint8/8, protected, integrity, handoff and contracts
pass. r36 composition4032/4032 and pinned Yulong4/4, r37 nested124416/124416,
leaf6/6 (69120), isolated Glow4/4, GPU sampler71824/71824 and CPU sampler regressions
remain exact. Existing Python tests retain scalar3072, three-alpha25920 and both
held-out span8652 controls. Full roster replay and Web export were not rerun for
this diagnostic-only change.

## Remaining blocker

Both operand-consumption rules now have independent native controls for this
path, but reciprocal/input-normalization arithmetic remains unresolved. Future
arithmetic comparisons must use consumed integer offsets and1/256 multipliers,
retain signed controls, and reject against every old bound/control. The signed
alpha49/source-green25 case is an additional concrete discriminator; use a proper
monotone-decreasing bound calculation if extending coefficient constraints to
negative multipliers, never the current positive-only binary search.

No new candidate advanced to native filter buffers or the72576 GPU gate.
Historical results remain native-buffer43006/43200, nested GPU67774/72576,
production components9/54. Full AS/clip-action ownership remains separately open.
Draft only; no production admission, merge, deployment or Worker changes.
