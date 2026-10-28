# Gaara attack: shared reproduction and evidence contract

Only `gaara__attack__neutral__ground__near`, original generated s147 tape. Base
`de0bbe51`; branch
`feat/sampling-gaara-attack-one-cell`. No gameplay/Godot implementation changes.
The sole probe change adds the exact Gaara Sprite673/PlaceObject2_20_31 handler
whose original body matches the existing predicate/call observer. Source edits,
uninstrumented/absent matches and ambiguous selection reject. Existing Deidara
and Chad tests remain green. This is observation selection, not a silent-drop exception.

## Build and native capture

Use fresh paths/run IDs for fresh runs. Each capture is independent; clocks,
random effects and tracing perturbation are not cross-run equivalence proofs.

```sh
python3 -m tools.sampling_matrix generate --output /tmp/bvn-s147-campaign --fighters gaara --require-native
# Set n/flag: 147/(omit flag), 148/geometry, 149/display, 150/bitmap,
# 151/doaction, 152/clipaction, 153/callsite.
python3 tools/probes/build_ai_reference.py --ffdec /tmp/bvn-s66-tools/ffdec/ffdec.jar \
  --output /tmp/bvn-s148-build --run-id s148-gaara-attack-20261028 --frames 60 \
  --move-case /tmp/bvn-s147-campaign/cases/gaara__attack__neutral__ground__near.json \
  --p1-character 我爱罗 --p2-character 一护 --p1-helper 我爱罗 --p2-helper 魂 --sampling-geometry
python3 -m tools.sampling_native \
  --case /tmp/bvn-s147-campaign/cases/gaara__attack__neutral__ground__near.json \
  --build /tmp/bvn-s148-build --trace /tmp/bvn-s148-capture.log \
  --receipt /tmp/bvn-s148-receipts/gaara__attack__neutral__ground__near.json \
  --allow-window-activation --timeout 600
```

Repeat the build/capture with the listed n/flag only for the requested dimension.
Native captures were serialized; each folder retains its own environment file.
Flash process preflight/launch/owned cleanup and the Godot graphics command used
command-scoped escalation, not permanent sandbox changes.

## Gates

```sh
python3 -m tools.sampling_matrix run --campaign /tmp/bvn-s147-campaign \
  --output /tmp/bvn-s147-runtime --godot /tmp/bvn-s66-tools/engine/Godot.app/Contents/MacOS/Godot \
  --cases gaara__attack__neutral__ground__near --native-evidence /tmp/bvn-s147-receipts
python3 -m tools.sampling_matrix check --campaign /tmp/bvn-s147-campaign \
  --output /tmp/bvn-s147-runtime --native-evidence /tmp/bvn-s147-receipts
# Full campaign exits 1: other receipts are missing.
python3 -m tools.sampling_geometry --case /tmp/bvn-s147-campaign/cases/gaara__attack__neutral__ground__near.json \
  --receipt /tmp/bvn-s148-receipts/gaara__attack__neutral__ground__near.json --output /tmp/bvn-s148-geometry.json
python3 -m tools.sampling_display --case /tmp/bvn-s147-campaign/cases/gaara__attack__neutral__ground__near.json \
  --receipt /tmp/bvn-s149-receipts/gaara__attack__neutral__ground__near.json \
  --exports /tmp/bvn-s149-exports.json --output /tmp/bvn-s149-display.json
mkdir -p /tmp/bvn-s150-godot/frames
/tmp/bvn-s66-tools/engine/Godot.app/Contents/MacOS/Godot --path godot \
  --rendering-method gl_compatibility --resolution 600x400 --log-file /tmp/bvn-s150-godot/capture-engine.log \
  --script res://tests/move_case_reference.gd -- --bitmap-sequence \
  /tmp/bvn-s147-campaign/cases/gaara__attack__neutral__ground__near.json /tmp/bvn-s150-godot/frames
python3 -m tools.sampling_bitmap --case /tmp/bvn-s147-campaign/cases/gaara__attack__neutral__ground__near.json \
  --receipt /tmp/bvn-s150-receipts/gaara__attack__neutral__ground__near.json \
  --godot /tmp/bvn-s150-godot/frames --output /tmp/bvn-s150-comparison.json
# DoAction: n=151; clip-action: n=152 (same collector).
python3 -m tools.sampling_doaction --case /tmp/bvn-s147-campaign/cases/gaara__attack__neutral__ground__near.json \
  --receipt /tmp/bvn-s151-receipts/gaara__attack__neutral__ground__near.json --output /tmp/bvn-s151-doaction.json
python3 -m tools.sampling_callsite --case /tmp/bvn-s147-campaign/cases/gaara__attack__neutral__ground__near.json \
  --receipt /tmp/bvn-s153-receipts/gaara__attack__neutral__ground__near.json --output /tmp/bvn-s153-actions.json
```

## Restoring archived evidence

Restore each build archive to its original `/private/tmp/bvn-sNN-build`, decompress
its raw trace to the receipt path, and restore case/receipt paths above. Use this
commit's probes and pinned player; do not rewrite hashes or paths. Build archives
retain metadata, instrumentation diff and five SWFs. Per-folder artifact hashes
bind the evidence; receipt/build files retain source, probe, engine and output hashes.
Godot frames restore under `/tmp/bvn-s150-godot/frames`; native PNGs derive only
from retained BitmapData trace, never uploaded as game textures.

Display joins reuse unchanged main/yihu/helpers from [s30's source archive](../s30/source-exports.tar.gz).
Restore those exports to their recorded paths. Restore the [Gaara export](../s149/gaara-source-export.tar.gz)
to `/tmp/bvn-s149-source` and s149 `source-exports.json` to `/tmp/bvn-s149-exports.json`.
It was generated with the pinned jar using `-swf2xml game/fighter/gaara.swf /tmp/bvn-s149-source/fighter-gaara.xml`.
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
