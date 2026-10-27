# s58 — special-cell child display list and camera observation

Base: `81bb2f84a69b4f9834a3cd132eee4635842bd02e` (merged PR #80).
Branch: `feat/sampling-special-display-one-cell`.
Exactly `didala__special__neutral__ground__near`, unchanged s56 tape.
Evidence/docs only; s30 observer, collector and source join are unchanged.
`production_admitted=false`; `native_parity_proven=false`.

## Results and review map

Real Flash: **7,716 events**, **61/61 root samples**, **1,567 MovieClip
records**, zero filter entries. Native receipt and structural sample checks pass.
Deleting a whole sample or actor node rejects; original capture rechecks.
**55 focused tests + 19 probe tests**, integrity/handoff/contracts pass.

The **full display/camera gate exits 1** with **264 source/hierarchy obligations**:
122 missing source-frame observations concern `p1.mc.AImain` and `p2.mc.AImain`
(61 each). Another 142 unresolved runtime-symbol observations concern
`layer_effect.xgmc0` through `xgmc6` (47/26/22/18/14/10/5 respectively).
All nodes and obligations remain in the report; none are dropped or allowlisted.
Dynamic mask ownership remains unproven even if source joins were resolved.
`source-gap-summary.json` retains every obligation with tick/path.

`display.json.gz` contains the full sampled hierarchy, parent/depth, instance IDs,
source frames/stamps, local/global transforms, visibility/alpha, scrollRect,
blend/cache state, filter order and child counts. Original timeline records retain
clipDepth and source placement fields, including static leaves which are not
invented native MovieClip objects. Created/removed lists are sampled deltas.

Camera observations include Stage dimensions/scaleMode/align, root local/global
matrices and the entire sampled game transform chain. Root position alone is
not treated as camera proof. There is no framebuffer clipping or Godot camera
comparison. Dynamic setMask, arbitrary nonzero filter classes, exact intra-frame
creation/removal and script mutations to static leaves remain unproven.

## Reproduce

```sh
python3 tools/probes/build_ai_reference.py --ffdec /tmp/bvn-loud-fail/r02/ffdec/ffdec.jar \
  --output /tmp/bvn-s58-build --run-id s58-didala-special-20261027 --frames 60 \
  --move-case /tmp/bvn-s56-campaign/cases/didala__special__neutral__ground__near.json \
  --p1-character 迪达拉 --p2-character 一护 --p1-helper 我爱罗 --p2-helper 魂 --sampling-display
python3 -m tools.sampling_native \
  --case /tmp/bvn-s56-campaign/cases/didala__special__neutral__ground__near.json \
  --build /tmp/bvn-s58-build --trace /tmp/bvn-s58-capture.log \
  --receipt /tmp/bvn-s58-receipts/didala__special__neutral__ground__near.json --allow-window-activation
python3 -m tools.sampling_display \
  --case /tmp/bvn-s56-campaign/cases/didala__special__neutral__ground__near.json \
  --receipt /tmp/bvn-s58-receipts/didala__special__neutral__ground__near.json \
  --exports /tmp/bvn-s30-exports.json --output /tmp/bvn-s58-display.json
# Expected exit 1: 264 unresolved source/hierarchy obligations.
```

The unchanged locked source SWFs reuse the s30 XML exports, with source and XML
hashes revalidated by the gate. `source-exports.json` retains their identities;
[the s30 source archive](../s30/source-exports.tar.gz) supplies the exact exports
without duplicating that bulk. JPEXS identity is recorded in native build metadata.

Fresh captures need fresh paths/run IDs. To revalidate this archived run, restore
its build archive at `/private/tmp/bvn-s58-build`, decompress raw capture at
`/private/tmp/bvn-s58-capture.log`, restore case/receipt at the paths above, and
restore s30's source archive/manifest at their recorded paths. Use this commit's
probes and the pinned player; never rewrite receipt paths/hashes. Raw trace and
full display report are losslessly compressed; artifact hashes bind this evidence.
Build archive retains metadata/diff and five instrumented SWFs only.

Capture-only escalation covered previously authorized ps/player launch/cleanup.
Flash Debugger 32/Rosetta environment and executable/source/probe/output hashes
are retained. Existing static-loader attestation, input alias and random/timer
limitations remain; capture completeness is not behavioral or pixel parity.

## Follow-ups

Bind AImain's unloaded/frame-zero state and the seven effect-node symbols through
explicit provenance; capture
dynamic mask ownership before claiming complete display/camera evidence.
This special cell's BitmapData and DoAction/ownership stacks remain separate thin
slices. Full camera comparison, arbitrary filtered children, exact lifecycle,
other cells and first-cell residuals are unchanged follow-ups. No attack-cell
rerun, full-roster expansion, runtime/importer change, merge/deploy/Worker.

The s57 missing p1 receiver at tick 11 remains open. Structural display
coverage does not settle source-authored hurt-box absence versus observer timing.
No geometry recapture/correction is included in this slice.
