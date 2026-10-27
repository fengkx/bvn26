# s50 — ranged geometry capture exposes an unbound source-list obligation

Base `5fb359002cb9a1e9f2ab3c4899c53ef3ad4527b2` (merged PR #72).
Branch `feat/sampling-ranged-geometry-one-cell`. Exactly
`didala__ranged__neutral__ground__near`, unchanged s49 tape.
Evidence/docs only; geometry probe and fail-loud gate are unchanged.
`production_admitted=false`; `native_parity_proven=false`.

## Result: full geometry gate rejects

Real native capture completes with **5,066 events** and the case-bound receipt
revalidates. Raw geometry events contain 61 begin/end pairs, 199 box records and
**one geometry_error**. These raw counts do NOT establish 61 complete samples.
The full geometry gate **exits 1** at sequence 4160, display 515, observer tick 14:

```
missing-source-list:_level0.game.p1.mc.abcd.hitmc
```

The immediately preceding box binds to
`game/fighter/didala.swf#DefineSprite_69/frame_1/DoAction.as`, instance 76,
first scripted initialization display 514. Its matrix/bounds remain in the raw
trace. We neither omit the candidate nor reinterpret the error as an empty list.

Only the **ticks 0–13 prefix (14 samples, 54 box records)** validates structurally;
`geometry-prefix.json` explicitly labels that limited scope. It is not a replacement
for the full capture. Deleting a prefix sample or box rejects; restored prefix
rechecks, while the unchanged full capture still rejects. `geometry-errors.json`
and `negative-proof.json` retain exact failure sites and outcomes.
**50 focused tests + 19 probe tests** pass; integrity/handoff/contracts pass.

## Source analysis / precise remaining blocker

The existing `sampling_geometry.as::aiGeoWalk` emits this combined diagnostic
when any of these is undefined: target `_root.game["p" + mc._parent.pn]`,
`mc._fsArray`, `mc._fzfsArray`, or `mc.stgks`. The current trace does not identify
which operand is absent; do not claim a particular root cause from its label.

Locked `scripts/fighter/didala.json`, `DefineSprite_69/frame_1/DoAction.as`
initializes all three arrays and defines `checkHit` using the same parent-pn target
path. This source fact does not prove their values at the failed observation.
Next narrow discriminator: record those four operands plus owner/pn at tick 14
and bind the projectile's initialization/lifetime source path. Keep this capture
as a rejecting regression. Only source-supported ownership can fix the observer;
no empty-array default, guessed ancestor or ignore rule is admitted here.

The shared observer walks the whole game tree and collision candidate lists,
including both actors/helpers/stage. Present candidates are not proof of active
damage eligibility. Sampled births/lifetimes do not prove exact intra-frame
creation/removal or AVM1 identity. Godot geometry comparison has not been run;
full native geometry itself remains incomplete in this capture.

## Reproduction / review map

```sh
python3 tools/probes/build_ai_reference.py --ffdec /tmp/bvn-loud-fail/r02/ffdec/ffdec.jar \
  --output /tmp/bvn-s50-build --run-id s50-didala-ranged-20261027 --frames 60 \
  --move-case /tmp/bvn-s49-campaign/cases/didala__ranged__neutral__ground__near.json \
  --p1-character 迪达拉 --p2-character 一护 --p1-helper 我爱罗 --p2-helper 魂 --sampling-geometry
python3 -m tools.sampling_native \
  --case /tmp/bvn-s49-campaign/cases/didala__ranged__neutral__ground__near.json \
  --build /tmp/bvn-s50-build --trace /tmp/bvn-s50-capture.log \
  --receipt /tmp/bvn-s50-receipts/didala__ranged__neutral__ground__near.json --allow-window-activation
python3 -m tools.sampling_geometry \
  --case /tmp/bvn-s49-campaign/cases/didala__ranged__neutral__ground__near.json \
  --receipt /tmp/bvn-s50-receipts/didala__ranged__neutral__ground__near.json \
  --output /tmp/bvn-s50-geometry.json
# Expected exit 1: missing-source-list. No full geometry report is produced.
```

Review acceptance, geometry-errors, geometry-gate and negative-proof first.
Compressed native trace retains all events, including the failed and later samples.
Build archive retains metadata/diff and five SWFs; receipt binds original case,
source/probe/engine/output hashes. Fresh captures require fresh paths/run IDs.
Restore build at `/private/tmp/bvn-s50-build`, raw trace at its recorded path and
case/receipt paths above for revalidation with this commit's probes/pinned player;
never rewrite receipt hashes/paths. Artifact hashes bind this evidence folder.
Approved native-capture-only escalation covers ps/player launch/owned cleanup.

## Follow-ups

Resolve the native source-list obligation above, then compare native/Godot
geometry separately. Ranged DL/camera, BitmapData and DoAction/ownership are not
run here. Existing static-loader, clock/random and earlier cell residuals remain.
No other cell rerun, runtime/importer change, merge/deploy/Worker.
