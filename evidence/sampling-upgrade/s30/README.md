# s30 — One-cell native child hierarchy and camera observations

Base `9b2472d8b0867edf101a75bb48e4f2630e86b812`; branch
`feat/sampling-child-dl-camera-one-cell`. Only
`didala__attack__neutral__ground__near`, unchanged s28 tape. No gameplay or
importer changes. `native_parity_proven=false`; `production_admitted=false`.

## Review map and results

- `sampling_display.as`: opt-in native observer at the existing root sampling
  boundary, traversing the game MovieClip tree (both actors, helpers, stage,
  effects). Records parent, depth, instance ID, current frame, source stamp,
  local/concatenated matrices, visibility, alpha, scrollRect, blend/cache state,
  filter array order, explicit child counts and empty arrays.
- `build_ai_reference.py --sampling-display`: uses the existing instrumented
  copy builder and s29 source stamps; original SWFs/scripts unchanged.
- `tools.sampling_display`: receipt revalidation, strict sample/tree checks,
  original source timeline join, sampled create/remove deltas. Preserves raw
  authored placement fields including clipDepth and filter order; static leaves
  are source records, not invented native MovieClip objects.
- Real Flash: **8,837 events, 61/61 samples, 1,538 MovieClip records**.
  Native receipt and structural sample gate pass. Missing whole sample and
  missing actor node reject; original stream rechecks 61/61. 55 focused tests
  and 19 probe tests pass; integrity/handoff/contracts pass.

**Full display/camera gate deliberately exits 1**, not a parity pass. There are
169 unresolved source obligations: two `p1/p2.mc.AImain` nodes each have native
frame 0 (122 observations), and `layer_effect.xgmc0` lacks a source symbol stamp
(47 observations). All nodes remain in `display.json.gz`; none is dropped or
allowlisted. The source join cannot yet represent unloaded/script-created clips
or prove the linkage of the dynamic effect. Source-frame placements also do not
prove that scripts left every static leaf unchanged. The XML exporter is JPEXS
with the hash recorded in the native build; original source and XML hashes are
in `source-exports.json`.

## Camera, masks, filters and lifetime limits

Camera evidence includes actual Stage dimensions/scaleMode/align, root local and
global matrices, and every sampled game descendant's local/global matrix. It is
more than presentation root position, but is **not full camera proof**: no
framebuffer/viewport clipping comparison or Godot comparison is claimed.

Authored clipDepth and runtime scrollRect are retained. Dynamic `setMask`
ownership is not captured: `dynamic_mask_capture_complete=false`, and the CLI
cannot report full completeness even if all source joins succeed. Native filter
counts are zero in all 1,538 records; the generic property observer is not
admitted for arbitrary filter classes. Nonzero filter capture needs class and
complete parameter validation before admission. Creation/removal is the delta
between root-boundary observations, not exact intra-frame placement lifetime.
Native object IDs are observational and not an AVM1-reference model.

## Reproduction and artifacts

```sh
python3 tools/probes/build_ai_reference.py --ffdec /tmp/bvn-loud-fail/r02/ffdec/ffdec.jar \
  --output /tmp/bvn-s30-build --run-id s30-didala-20261027 --frames 60 \
  --move-case /tmp/bvn-s28-campaign/cases/didala__attack__neutral__ground__near.json \
  --p1-character 迪达拉 --p2-character 一护 --p1-helper 我爱罗 --p2-helper 魂 --sampling-display
python3 -m tools.sampling_native \
  --case /tmp/bvn-s28-campaign/cases/didala__attack__neutral__ground__near.json \
  --build /tmp/bvn-s30-build --trace /tmp/bvn-s30-capture.log \
  --receipt /tmp/bvn-s30-receipts/didala__attack__neutral__ground__near.json --allow-window-activation
python3 -m tools.sampling_display \
  --case /tmp/bvn-s28-campaign/cases/didala__attack__neutral__ground__near.json \
  --receipt /tmp/bvn-s30-receipts/didala__attack__neutral__ground__near.json \
  --exports /tmp/bvn-s30-exports.json --output /tmp/bvn-s30-display.json
# Expected exit 1: 169 unresolved source/hierarchy obligations.
```

Fresh capture requires fresh paths/run ID. For archived revalidation restore
both tar archives under `/private/tmp`, decompress the capture to its recorded
path and restore case, receipt and export manifest to the paths above. Receipt
validation intentionally requires original absolute paths and hashes. Captured
player/probe/build hashes are retained, not rewritten. Capture escalation was
limited to the approved ps/player launch/cleanup. Flash Debugger version and
hash remain as s28/s29. Static loader-attestation limits from s28 still apply.

## Next thin slice / known follow-ups

Bind unloaded AImain and dynamic xgmc0 by explicit load/attach provenance, then
capture dynamic mask ownership. Do not convert missing joins into empty source
lists. General filtered child capture, exact lifecycle, full camera comparison,
other cells, BitmapData and DoAction remain follow-ups. Jinye/Yijiao gaps are
unchanged. This PR ships observation plus honest rejection, not complete child
DL/camera admission. No merge, deployment or Worker changes.
