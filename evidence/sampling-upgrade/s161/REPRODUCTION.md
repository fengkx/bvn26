# Jiraiya attack: shared reproduction and evidence contract

Only `jiraiya__attack__neutral__ground__near`, original generated s161 tape. Base
`5e1b186c`; branch
`feat/sampling-jiraiya-attack-one-cell`. No gameplay/Godot implementation changes.
The sole probe change adds the exact Jiraiya Sprite342/PlaceObject2_11_33 handler
whose original body matches the existing predicate/call observer. Source edits,
uninstrumented/absent matches and ambiguous selection reject. Existing Deidara
and Chad tests remain green. This is observation selection, not a silent-drop exception.

## Build and native capture

Python with Pillow is required for bitmap tools (this run used `/tmp/gaara-venv/bin/python`); JSON Schema validation used `/tmp/bvn-s27-venv/bin/python`.
Use fresh paths/run IDs for fresh runs. Each capture is independent; clocks,
random effects and tracing perturbation are not cross-run equivalence proofs.

```sh
python3 -m tools.sampling_matrix generate --output /tmp/bvn-s161-campaign --fighters jiraiya --require-native
# Set n/flag: 161/(omit flag), 162/geometry, 163/display, 164/bitmap,
# 165/doaction, 166/clipaction, 167/callsite.
python3 tools/probes/build_ai_reference.py --ffdec /tmp/bvn-s66-tools/ffdec/ffdec.jar \
  --output /tmp/bvn-s162-build --run-id s162-jiraiya-attack-20261028 --frames 60 \
  --move-case /tmp/bvn-s161-campaign/cases/jiraiya__attack__neutral__ground__near.json \
  --p1-character 自来也 --p2-character 一护 --p1-helper 我爱罗 --p2-helper 魂 --sampling-geometry
python3 -m tools.sampling_native \
  --case /tmp/bvn-s161-campaign/cases/jiraiya__attack__neutral__ground__near.json \
  --build /tmp/bvn-s162-build --trace /tmp/bvn-s162-capture.log \
  --receipt /tmp/bvn-s162-receipts/jiraiya__attack__neutral__ground__near.json \
  --allow-window-activation --timeout 600
```

Repeat the build/capture with the listed n/flag only for the requested dimension.
Native captures were serialized; each folder retains its own environment file.
Flash process preflight/launch/owned cleanup and the Godot graphics command used
command-scoped escalation, not permanent sandbox changes.

## Gates

```sh
python3 -m tools.sampling_matrix run --campaign /tmp/bvn-s161-campaign \
  --output /tmp/bvn-s161-runtime --godot /tmp/bvn-s66-tools/engine/Godot.app/Contents/MacOS/Godot \
  --cases jiraiya__attack__neutral__ground__near --native-evidence /tmp/bvn-s161-receipts
python3 -m tools.sampling_matrix check --campaign /tmp/bvn-s161-campaign \
  --output /tmp/bvn-s161-runtime --native-evidence /tmp/bvn-s161-receipts
# Full campaign exits 1: other receipts are missing.
python3 -m tools.sampling_geometry --case /tmp/bvn-s161-campaign/cases/jiraiya__attack__neutral__ground__near.json \
  --receipt /tmp/bvn-s162-receipts/jiraiya__attack__neutral__ground__near.json --output /tmp/bvn-s162-geometry.json
python3 -m tools.sampling_display --case /tmp/bvn-s161-campaign/cases/jiraiya__attack__neutral__ground__near.json \
  --receipt /tmp/bvn-s163-receipts/jiraiya__attack__neutral__ground__near.json \
  --exports /tmp/bvn-s163-exports.json --output /tmp/bvn-s163-display.json
mkdir -p /tmp/bvn-s164-godot/frames
/tmp/bvn-s66-tools/engine/Godot.app/Contents/MacOS/Godot --path godot \
  --rendering-method gl_compatibility --resolution 600x400 --log-file /tmp/bvn-s164-godot/capture-engine.log \
  --script res://tests/move_case_reference.gd -- --bitmap-sequence \
  /tmp/bvn-s161-campaign/cases/jiraiya__attack__neutral__ground__near.json /tmp/bvn-s164-godot/frames
python3 -m tools.sampling_bitmap --case /tmp/bvn-s161-campaign/cases/jiraiya__attack__neutral__ground__near.json \
  --receipt /tmp/bvn-s164-receipts/jiraiya__attack__neutral__ground__near.json \
  --godot /tmp/bvn-s164-godot/frames --output /tmp/bvn-s164-comparison.json
# DoAction: n=165; clip-action: n=166 (same collector).
python3 -m tools.sampling_doaction --case /tmp/bvn-s161-campaign/cases/jiraiya__attack__neutral__ground__near.json \
  --receipt /tmp/bvn-s165-receipts/jiraiya__attack__neutral__ground__near.json --output /tmp/bvn-s165-doaction.json
python3 -m tools.sampling_callsite --case /tmp/bvn-s161-campaign/cases/jiraiya__attack__neutral__ground__near.json \
  --receipt /tmp/bvn-s167-receipts/jiraiya__attack__neutral__ground__near.json --output /tmp/bvn-s167-actions.json
```

## Restoring archived evidence

Restore each build archive to its original `/private/tmp/bvn-sNN-build`, decompress
its raw trace to the receipt path, and restore case/receipt paths above. Use this
commit's probes and pinned player; do not rewrite hashes or paths. Build archives
retain metadata, instrumentation diff and five SWFs. Per-folder artifact hashes
bind the evidence; receipt/build files retain source, probe, engine and output hashes.
Godot frames restore under `/tmp/bvn-s164-godot/frames`; native PNGs derive only
from retained BitmapData trace, never uploaded as game textures.

Display joins reuse unchanged main/yihu/helpers from [s30's source archive](../s30/source-exports.tar.gz).
Restore those exports to their recorded paths. Restore the [Jiraiya export](../s163/jiraiya-source-export.tar.gz)
to `/tmp/bvn-s163-source` and s163 `source-exports.json` to `/tmp/bvn-s163-exports.json`.
It was generated with the pinned jar using `-swf2xml game/fighter/jiraiya.swf /tmp/bvn-s163-source/fighter-jiraiya.xml`.
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

## Environment retries

The first s162 capture was rejected for events beyond the completion boundary;
`../s162/rejected-boundary-capture.log.gz` and its command output retain that
unaltered failed attempt. The subsequent capture must pass the unchanged gate.
Shared native capture lock contention was retried without interrupting other
characters. Godot first-run resource import was required in this new worktree;
pre-import diagnostic outputs remain in `/tmp/bvn-s161-runtime-before-import`
and `/tmp/bvn-s164-godot-before-import`, excluded from accepted evidence.
Final runtime and bitmap captures use fresh output directories after import.

After contention, s162–s167 used the existing capture API with a 600-second
lock wait via a local launcher (capture timeout also 600 seconds):

```sh
python3 -c 'from tools import sampling_native as m; from functools import partial; m.player.capture=partial(m.player.capture,lock_timeout=600); m.main()' --case ... --build ... --trace ... --receipt ... --allow-window-activation --timeout 600
```

This changes only lock acquisition waiting; no collector/gate source was changed.
