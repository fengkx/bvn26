# s64 — summon geometry capture exposes an unbound helper source stamp

Base `d39529e3c61bd6700f7ff6abb9d01b0d1acd1543` (merged PR #86).
Branch `feat/sampling-summon-geometry-one-cell`. Exactly
`didala__summon__neutral__ground__near`, unchanged s63 tape.
Evidence/docs only; geometry probe and fail-loud gate are unchanged.
`production_admitted=false`; `native_parity_proven=false`.

## Result: full geometry gate rejects

Real native capture completes with **5,349 events** and the case-bound receipt
revalidates. Raw geometry has 61 begin/end pairs, 238 bound box records and
**three explicit geometry errors**. These counts do NOT establish 61 complete samples.
The full geometry gate **exits 1** on the first error, sequence 5263, display 553,
observer tick 58:

```
unbound:_level0.game.p1fz.atm1
```

The same path fails at ticks 59 and 60 (sequences 5311 and 5343).
Only **ticks 0–57 (58 samples, 228 bound box records)** validate structurally;
`geometry-prefix.json` explicitly labels that scope. No failing tick is silently
removed from the raw capture. Delete a prefix sample or box and the collector
rejects; restore it and the prefix rechecks, while the full capture still rejects.
**52 focused tests + 19 probe tests** pass; integrity/handoff/contracts pass.

## Exact blocker and next discriminator

`sampling_geometry.as::aiGeoBox` emits `unbound` when `__aiGeoId` or
`__aiGeoSource` is undefined. It reports the path instead of fabricating a source,
identity or bounds. The candidate is in the actual p1 helper container, not the
current fighter's local body. The runtime case selects Woailuo for p1; the locked
helper bundle is `scripts/fighter/fz/woailuo.json`. This does not identify atm1's
symbol/placement by itself. No native source hash or reference was changed.

Next narrow discriminator: join helper atm1's authored placement and lifecycle
with the stamping sites and first observation around tick 58. Determine which
stamp field is absent and whether placement-time ownership is needed. Do not
infer a symbol from its name, default an empty list, or exempt helper candidates.

The observer scans both fighters, helpers and stage candidate lists. Bound
records retain source script, instance ID, global matrices/bounds and sampled
lifetimes; zero candidate roles retain explicit arrays. Present candidates do
not prove damage eligibility. Exact intra-frame lifetime, AVM1 identity and
Godot geometry comparison remain unproven; full native geometry is incomplete.

## Reproduction / review map

```sh
python3 tools/probes/build_ai_reference.py --ffdec /tmp/bvn-loud-fail/r02/ffdec/ffdec.jar \
  --output /tmp/bvn-s64-build --run-id s64-didala-summon-20261027 --frames 60 \
  --move-case /tmp/bvn-s63-campaign/cases/didala__summon__neutral__ground__near.json \
  --p1-character 迪达拉 --p2-character 一护 --p1-helper 我爱罗 --p2-helper 魂 --sampling-geometry
python3 -m tools.sampling_native \
  --case /tmp/bvn-s63-campaign/cases/didala__summon__neutral__ground__near.json \
  --build /tmp/bvn-s64-build --trace /tmp/bvn-s64-capture.log \
  --receipt /tmp/bvn-s64-receipts/didala__summon__neutral__ground__near.json --allow-window-activation
python3 -m tools.sampling_geometry \
  --case /tmp/bvn-s63-campaign/cases/didala__summon__neutral__ground__near.json \
  --receipt /tmp/bvn-s64-receipts/didala__summon__neutral__ground__near.json \
  --output /tmp/bvn-s64-geometry.json
# Expected exit 1: unbound helper atm1. No full geometry report is produced.
```

Review acceptance, geometry-errors, geometry-gate and negative-proof first.
Compressed native trace retains all events, including the failed and later samples.
Build archive retains metadata/diff and five SWFs; receipt binds original case,
source/probe/engine/output hashes. Fresh captures require fresh paths/run IDs.
Restore build at `/private/tmp/bvn-s64-build`, raw trace at its recorded path and
case/receipt paths above for revalidation with this commit's probes/pinned player;
never rewrite receipt hashes/paths. Artifact hashes bind this evidence folder.
Approved native-capture-only escalation covers ps/player launch/owned cleanup.

## Follow-ups

Resolve the helper stamp obligation above, then compare native/Godot geometry.
Summon DL/camera, BitmapData and DoAction/ownership remain separate thin slices.
Static-loader, timer/random and earlier-cell residuals remain open. No other
cell rerun, runtime/importer/probe change, merge/deploy/Worker.
