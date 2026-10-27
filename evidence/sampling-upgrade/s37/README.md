# s37 — jump-cell child display list and camera observation

Base: `8b15e36e49cae02ea5b7e48ca38bcab77dd74e28` (merged PR #59).
Branch: `feat/sampling-jump-display-one-cell`.
Exactly `didala__jump__neutral__ground__near`, unchanged s35 tape.
Evidence/docs only; s30 observer, collector and source join are unchanged.
`production_admitted=false`; `native_parity_proven=false`.

## Results and review map

Real Flash capture: **8,968 events**, **61/61 root samples**, **1,522 MovieClip
records**, zero observed filter entries. Native receipt revalidation and structural
sample checks pass. Deleting a whole sample or one actor node rejects; original
capture rechecks 61/61. **55 focused tests + 19 probe tests** pass; integrity,
handoff and contracts logs are included.

The **full display/camera gate exits 1** with **122 source-frame obligations**:
`_level0.game.p1.mc.AImain` and `_level0.game.p2.mc.AImain`, 61 each. These nodes
report frame 0 and cannot join an authored frame; they remain in the evidence.
No missing source joins are converted into empty lists or allowlisted.
`source-gap-summary.json` retains every obligation and its tick/path.
Dynamic mask ownership remains unproven even if the source joins were resolved.

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
  --output /tmp/bvn-s37-build --run-id s37-didala-jump-20261027 --frames 60 \
  --move-case /tmp/bvn-s35-campaign/cases/didala__jump__neutral__ground__near.json \
  --p1-character 迪达拉 --p2-character 一护 --p1-helper 我爱罗 --p2-helper 魂 --sampling-display
python3 -m tools.sampling_native \
  --case /tmp/bvn-s35-campaign/cases/didala__jump__neutral__ground__near.json \
  --build /tmp/bvn-s37-build --trace /tmp/bvn-s37-capture.log \
  --receipt /tmp/bvn-s37-receipts/didala__jump__neutral__ground__near.json --allow-window-activation
python3 -m tools.sampling_display \
  --case /tmp/bvn-s35-campaign/cases/didala__jump__neutral__ground__near.json \
  --receipt /tmp/bvn-s37-receipts/didala__jump__neutral__ground__near.json \
  --exports /tmp/bvn-s30-exports.json --output /tmp/bvn-s37-display.json
# Expected exit 1: 122 unresolved source/hierarchy obligations.
```

The unchanged locked source SWFs reuse the s30 XML exports, with source and XML
hashes revalidated by the gate. `source-exports.json` retains their identities;
[the s30 source archive](../s30/source-exports.tar.gz) supplies the exact exports
without duplicating that bulk. JPEXS identity is recorded in native build metadata.

Fresh captures need fresh paths/run IDs. To revalidate this archived run, restore
its build archive at `/private/tmp/bvn-s37-build`, decompress raw capture at
`/private/tmp/bvn-s37-capture.log`, restore case/receipt at the paths above, and
restore s30's source archive/manifest at their recorded paths. Use this commit's
probes and the pinned player; never rewrite receipt paths/hashes. Raw trace and
full display report are losslessly compressed; artifact hashes bind this evidence.
Build archive retains metadata/diff and five instrumented SWFs only.

Capture-only escalation covered previously authorized ps/player launch/cleanup.
Flash Debugger 32/Rosetta environment and executable/source/probe/output hashes
are retained. Existing static-loader attestation, input alias and random/timer
limitations remain; capture completeness is not behavioral or pixel parity.

## Follow-ups

Bind AImain's unloaded/frame-zero state through explicit provenance; capture
dynamic mask ownership before claiming complete display/camera evidence.
This jump cell's BitmapData and DoAction/ownership stacks remain separate thin
slices. Full camera comparison, arbitrary filtered children, exact lifecycle,
other cells and first-cell residuals are unchanged follow-ups. No attack-cell
rerun, full-roster expansion, runtime/importer change, merge/deploy/Worker.
