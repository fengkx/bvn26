# Kakashi attack: shared reproduction and evidence contract

Only `kakashi__attack__neutral__ground__near`, original generated s168 tape. Base
`5e1b186c`; branch
`feat/sampling-kakashi-attack-one-cell`. No gameplay/Godot implementation changes.
The sole probe change adds the exact Kakashi Sprite710/PlaceObject2_9_31 handler
whose original body matches the existing predicate/call observer. Source edits,
uninstrumented/absent matches and ambiguous selection reject. Existing Deidara
and Chad tests remain green. This is observation selection, not a silent-drop exception.

## Build and native capture

Use fresh paths/run IDs for fresh runs. Each capture is independent; clocks,
random effects and tracing perturbation are not cross-run equivalence proofs.

```sh
/tmp/gaara-venv/bin/python -m tools.sampling_matrix generate --output /tmp/bvn-s168-campaign --fighters kakashi --require-native
# Set n/flag: 168/(omit flag), 169/geometry, 170/display, 171/bitmap,
# 172/doaction, 173/clipaction, 174/callsite.
/tmp/gaara-venv/bin/python tools/probes/build_ai_reference.py --ffdec /tmp/bvn-s66-tools/ffdec/ffdec.jar \
  --output /tmp/bvn-s169-build --run-id s169-kakashi-attack-20261028 --frames 60 \
  --move-case /tmp/bvn-s168-campaign/cases/kakashi__attack__neutral__ground__near.json \
  --p1-character 卡卡西 --p2-character 一护 --p1-helper 我爱罗 --p2-helper 魂 --sampling-geometry
/tmp/gaara-venv/bin/python -m tools.sampling_native \
  --case /tmp/bvn-s168-campaign/cases/kakashi__attack__neutral__ground__near.json \
  --build /tmp/bvn-s169-build --trace /tmp/bvn-s169-capture.log \
  --receipt /tmp/bvn-s169-receipts/kakashi__attack__neutral__ground__near.json \
  --allow-window-activation --timeout 600
```

Repeat the build/capture with the listed n/flag only for the requested dimension.
Native captures were serialized; each folder retains its own environment file.
Flash process preflight/launch/owned cleanup and the Godot graphics command used
command-scoped escalation, not permanent sandbox changes.

## Gates

```sh
/tmp/gaara-venv/bin/python -m tools.sampling_matrix run --campaign /tmp/bvn-s168-campaign \
  --output /tmp/bvn-s168-runtime --godot /tmp/bvn-s66-tools/engine/Godot.app/Contents/MacOS/Godot \
  --cases kakashi__attack__neutral__ground__near --native-evidence /tmp/bvn-s168-receipts
/tmp/gaara-venv/bin/python -m tools.sampling_matrix check --campaign /tmp/bvn-s168-campaign \
  --output /tmp/bvn-s168-runtime --native-evidence /tmp/bvn-s168-receipts
# Full campaign exits 1: other receipts are missing.
/tmp/gaara-venv/bin/python -m tools.sampling_geometry --case /tmp/bvn-s168-campaign/cases/kakashi__attack__neutral__ground__near.json \
  --receipt /tmp/bvn-s169-receipts/kakashi__attack__neutral__ground__near.json --output /tmp/bvn-s169-geometry.json
/tmp/gaara-venv/bin/python -m tools.sampling_display --case /tmp/bvn-s168-campaign/cases/kakashi__attack__neutral__ground__near.json \
  --receipt /tmp/bvn-s170-receipts/kakashi__attack__neutral__ground__near.json \
  --exports /tmp/bvn-s170-exports.json --output /tmp/bvn-s170-display.json
mkdir -p /tmp/bvn-s171-godot/frames
/tmp/bvn-s66-tools/engine/Godot.app/Contents/MacOS/Godot --path godot \
  --rendering-method gl_compatibility --resolution 600x400 --log-file /tmp/bvn-s171-godot/capture-engine.log \
  --script res://tests/move_case_reference.gd -- --bitmap-sequence \
  /tmp/bvn-s168-campaign/cases/kakashi__attack__neutral__ground__near.json /tmp/bvn-s171-godot/frames
/tmp/gaara-venv/bin/python -m tools.sampling_bitmap --case /tmp/bvn-s168-campaign/cases/kakashi__attack__neutral__ground__near.json \
  --receipt /tmp/bvn-s171-receipts/kakashi__attack__neutral__ground__near.json \
  --godot /tmp/bvn-s171-godot/frames --output /tmp/bvn-s171-comparison.json
# DoAction: n=172; clip-action: n=173 (same collector).
/tmp/gaara-venv/bin/python -m tools.sampling_doaction --case /tmp/bvn-s168-campaign/cases/kakashi__attack__neutral__ground__near.json \
  --receipt /tmp/bvn-s172-receipts/kakashi__attack__neutral__ground__near.json --output /tmp/bvn-s172-doaction.json
/tmp/gaara-venv/bin/python -m tools.sampling_callsite --case /tmp/bvn-s168-campaign/cases/kakashi__attack__neutral__ground__near.json \
  --receipt /tmp/bvn-s174-receipts/kakashi__attack__neutral__ground__near.json --output /tmp/bvn-s174-actions.json
```

## Restoring archived evidence

Restore each build archive to its original `/private/tmp/bvn-sNN-build`, decompress
its raw trace to the receipt path, and restore case/receipt paths above. Use this
commit's probes and pinned player; do not rewrite hashes or paths. Build archives
retain metadata, instrumentation diff and five SWFs. Per-folder artifact hashes
bind the evidence; receipt/build files retain source, probe, engine and output hashes.
Godot frames restore under `/tmp/bvn-s171-godot/frames`; native PNGs derive only
from retained BitmapData trace, never uploaded as game textures.

Display joins reuse unchanged main/yihu/helpers from [s30's source archive](../s30/source-exports.tar.gz).
Restore those exports to their recorded paths. Restore the [Kakashi export](../s170/kakashi-source-export.tar.gz)
to `/tmp/bvn-s170-source` and s170 `source-exports.json` to `/tmp/bvn-s170-exports.json`.
It was generated with the pinned jar using `-swf2xml game/fighter/Kakashi.swf /tmp/bvn-s170-source/fighter-Kakashi.xml`.
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

Source paths retain exact authored capitalization: `scripts/fighter/Kakashi.json` and `game/fighter/Kakashi.swf`.

## Retained diagnostic failures and environment setup

Display r01 and r02 were rejected by the unchanged native receipt validator with
`events beyond completion boundary`. Their complete raw logs, build metadata and
build archives remain in s170. They are not receipts and no prefix was admitted.
The retained final display build uses run ID `s170-kakashi-attack-20261028-r03`.

The fresh worktree required `Godot --headless --editor --path godot --import`
before execution and viewport sampling. Early runs missing the class/texture
cache were not used as evidence. Import's external editor-settings save failed
in the sandbox; subsequent game execution and actual viewport capture succeeded.
No generated UID or import cache files are included in this PR.
Pillow-based gates/tests used `/tmp/gaara-venv/bin/python` (Python 3.11);
contract validation used `/tmp/bvn-s27-venv/bin/python` with jsonschema 4.25.1.

Visual inspection of tick 13 confirms the intended Kakashi/Ichigo pair and
attack pose in both actual captures. The native HUD clock reads 47 versus
Godot 59; full-image differences include clock/rendering differences and are
not a synchronized-clock proof. No inferred cause closes the RGBA failure.
