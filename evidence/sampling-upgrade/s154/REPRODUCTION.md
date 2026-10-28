# Itachi attack: shared reproduction and evidence contract

Only `itachi__attack__neutral__ground__near`, original generated s154 tape. Base
`5e1b186c`; branch
`feat/sampling-itachi-attack-one-cell`. No gameplay/Godot implementation changes.
The sole probe change adds the exact Itachi Sprite294/PlaceObject2_11_33 handler
whose original body matches the existing predicate/call observer. Source edits,
uninstrumented/absent matches and ambiguous selection reject. Existing Deidara
and Chad tests remain green. This is observation selection, not a silent-drop exception.

## Build and native capture

Use fresh paths/run IDs for fresh runs. Each capture is independent; clocks,
random effects and tracing perturbation are not cross-run equivalence proofs.

```sh
python3 -m tools.sampling_matrix generate --output /tmp/bvn-s154-campaign --fighters itachi --require-native
# Set n/flag: 154/(omit flag), 155/geometry, 156/display, 157/bitmap,
# 158/doaction, 159/clipaction, 160/callsite.
python3 tools/probes/build_ai_reference.py --ffdec /tmp/bvn-s66-tools/ffdec/ffdec.jar \
  --output /tmp/bvn-s155-build --run-id s155-itachi-attack-20261028 --frames 60 \
  --move-case /tmp/bvn-s154-campaign/cases/itachi__attack__neutral__ground__near.json \
  --p1-character 鼬 --p2-character 一护 --p1-helper 我爱罗 --p2-helper 魂 --sampling-geometry
python3 -m tools.sampling_native \
  --case /tmp/bvn-s154-campaign/cases/itachi__attack__neutral__ground__near.json \
  --build /tmp/bvn-s155-build --trace /tmp/bvn-s155-capture.log \
  --receipt /tmp/bvn-s155-receipts/itachi__attack__neutral__ground__near.json \
  --allow-window-activation --timeout 600
```

Repeat the build/capture with the listed n/flag only for the requested dimension.
Native captures were serialized; each folder retains its own environment file.
Flash process preflight/launch/owned cleanup and the Godot graphics command used
command-scoped escalation, not permanent sandbox changes.

## Gates

```sh
python3 -m tools.sampling_matrix run --campaign /tmp/bvn-s154-campaign \
  --output /tmp/bvn-s154-runtime --godot /tmp/bvn-s66-tools/engine/Godot.app/Contents/MacOS/Godot \
  --cases itachi__attack__neutral__ground__near --native-evidence /tmp/bvn-s154-receipts
python3 -m tools.sampling_matrix check --campaign /tmp/bvn-s154-campaign \
  --output /tmp/bvn-s154-runtime --native-evidence /tmp/bvn-s154-receipts
# Full campaign exits 1: other receipts are missing.
python3 -m tools.sampling_geometry --case /tmp/bvn-s154-campaign/cases/itachi__attack__neutral__ground__near.json \
  --receipt /tmp/bvn-s155-receipts/itachi__attack__neutral__ground__near.json --output /tmp/bvn-s155-geometry.json
python3 -m tools.sampling_display --case /tmp/bvn-s154-campaign/cases/itachi__attack__neutral__ground__near.json \
  --receipt /tmp/bvn-s156-receipts/itachi__attack__neutral__ground__near.json \
  --exports /tmp/bvn-s156-exports.json --output /tmp/bvn-s156-display.json
mkdir -p /tmp/bvn-s157-godot/frames
/tmp/bvn-s66-tools/engine/Godot.app/Contents/MacOS/Godot --path godot \
  --rendering-method gl_compatibility --resolution 600x400 --log-file /tmp/bvn-s157-godot/capture-engine.log \
  --script res://tests/move_case_reference.gd -- --bitmap-sequence \
  /tmp/bvn-s154-campaign/cases/itachi__attack__neutral__ground__near.json /tmp/bvn-s157-godot/frames
python3 -m tools.sampling_bitmap --case /tmp/bvn-s154-campaign/cases/itachi__attack__neutral__ground__near.json \
  --receipt /tmp/bvn-s157-receipts/itachi__attack__neutral__ground__near.json \
  --godot /tmp/bvn-s157-godot/frames --output /tmp/bvn-s157-comparison.json
# DoAction: n=158; clip-action: n=159 (same collector).
python3 -m tools.sampling_doaction --case /tmp/bvn-s154-campaign/cases/itachi__attack__neutral__ground__near.json \
  --receipt /tmp/bvn-s158-receipts/itachi__attack__neutral__ground__near.json --output /tmp/bvn-s158-doaction.json
python3 -m tools.sampling_callsite --case /tmp/bvn-s154-campaign/cases/itachi__attack__neutral__ground__near.json \
  --receipt /tmp/bvn-s160-receipts/itachi__attack__neutral__ground__near.json --output /tmp/bvn-s160-actions.json
```

## Restoring archived evidence

Restore each build archive to its original `/private/tmp/bvn-sNN-build`, decompress
its raw trace to the receipt path, and restore case/receipt paths above. Use this
commit's probes and pinned player; do not rewrite hashes or paths. Build archives
retain metadata, instrumentation diff and five SWFs. Per-folder artifact hashes
bind the evidence; receipt/build files retain source, probe, engine and output hashes.
Godot frames restore under `/tmp/bvn-s157-godot/frames`; native PNGs derive only
from retained BitmapData trace, never uploaded as game textures.

Display joins reuse unchanged main/yihu/helpers from [s30's source archive](../s30/source-exports.tar.gz).
Restore those exports to their recorded paths. Restore the [Itachi export](../s156/itachi-source-export.tar.gz)
to `/tmp/bvn-s156-source` and s156 `source-exports.json` to `/tmp/bvn-s156-exports.json`.
It was generated with the pinned jar using `-swf2xml game/fighter/itachi.swf /tmp/bvn-s156-source/fighter-itachi.xml`.
All source/XML hashes are verified before joining.

## Limits shared by all seven dimensions

Receipt completeness is not native/gameplay parity. `runtime_fighter=null`
retains static-loader attestation limitations; config/source hashes bind the
trusted build, not an independent runtime identity assertion. Observation phases,
external clocks/random tapes and instrumentation timing are not proven equivalent.
Geometry includes both fighters/helper/stage candidates via global traversal;
explicit empty arrays are not missing samples. Candidate presence is not damage
eligibility; sampled lifetimes are not exact intra-frame create/remove or AVM1 identity.
Display includes hierarchy/child counts, transforms, depth and camera chain; root
position alone is not camera proof. Dynamic masks and framebuffer clipping remain
unproven. Opaque 600×400 native ARGB is losslessly decoded to RGBA; Godot PNGs
are actual viewport outputs. No crop/align/gamma/resize/tolerance is applied.
Action entries and paired calls do not prove callee bodies, every branch, dynamic
dispatch or Godot ownership. Full source lists stay retained even when unvisited.
`production_admitted=false`; `native_parity_proven=false` throughout.

## Shared capture lock

The first s159 CLI attempt exited before launch because another native capture
held the shared lock. No lock was removed and no other process was terminated.
s159/s160 then used the existing `capture_native_player.capture` API with
`lock_timeout=1800`, followed by `sampling_native.seal`, with the same build/case
and trace paths. The retained command JSON records all arguments. This only
extends lock waiting; it does not change capture timeout, validation or source.

## Rejected first call-site capture

The first s160 capture was rejected by receipt validation: `native evidence:
events beyond completion boundary`. Its unchanged trace, build and environment
are retained in s160 as `rejected-*` artifacts. No events were trimmed. The same source,
case and observer were rebuilt under fresh run ID
`s160-itachi-attack-20261028-retry1` and recaptured; that receipt passes. Its
incomplete invocation remains in the ownership report and the full gate exits 1.
