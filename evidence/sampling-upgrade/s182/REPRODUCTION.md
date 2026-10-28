# Minren attack: shared reproduction and evidence contract

Only `minren__attack__neutral__ground__near`, original generated s182 tape. Base
`146dada0`; branch
`feat/sampling-minren-attack-one-cell`. No gameplay/Godot implementation changes.
The sole probe change adds the exact Minren Sprite764/PlaceObject2_16_31 handler
whose original body matches the existing predicate/call observer. Source edits,
uninstrumented/absent matches and ambiguous selection reject. Existing Deidara
and Chad tests remain green. This is observation selection, not a silent-drop exception.

## Build and native capture

Python with Pillow is required for bitmap tools (this run used `/tmp/gaara-venv/bin/python`); JSON Schema validation used `/tmp/bvn-s27-venv/bin/python`.
Use fresh paths/run IDs for fresh runs. Each capture is independent; clocks,
random effects and tracing perturbation are not cross-run equivalence proofs.

```sh
python3 -m tools.sampling_matrix generate --output /tmp/bvn-s182-campaign --fighters minren --require-native
# Set n/flag: 182/(omit flag), 183/geometry, 184/display, 185/bitmap,
# 186/doaction, 187/clipaction, 188/callsite.
python3 tools/probes/build_ai_reference.py --ffdec /tmp/bvn-s66-tools/ffdec/ffdec.jar \
  --output /tmp/bvn-s183-build --run-id s183-minren-attack-20261028 --frames 60 \
  --move-case /tmp/bvn-s182-campaign/cases/minren__attack__neutral__ground__near.json \
  --p1-character 鸣人 --p2-character 一护 --p1-helper 我爱罗 --p2-helper 魂 --sampling-geometry
python3 -m tools.sampling_native \
  --case /tmp/bvn-s182-campaign/cases/minren__attack__neutral__ground__near.json \
  --build /tmp/bvn-s183-build --trace /tmp/bvn-s183-capture.log \
  --receipt /tmp/bvn-s183-receipts/minren__attack__neutral__ground__near.json \
  --allow-window-activation --timeout 600
```

Repeat the build/capture with the listed n/flag only for the requested dimension.
Native captures were serialized; each folder retains its own environment file.
Flash process preflight/launch/owned cleanup and the Godot graphics command used
command-scoped escalation, not permanent sandbox changes.

## Gates

```sh
python3 -m tools.sampling_matrix run --campaign /tmp/bvn-s182-campaign \
  --output /tmp/bvn-s182-runtime --godot /tmp/bvn-s66-tools/engine/Godot.app/Contents/MacOS/Godot \
  --cases minren__attack__neutral__ground__near --native-evidence /tmp/bvn-s182-receipts
python3 -m tools.sampling_matrix check --campaign /tmp/bvn-s182-campaign \
  --output /tmp/bvn-s182-runtime --native-evidence /tmp/bvn-s182-receipts
# Full campaign exits 1: other receipts are missing.
python3 -m tools.sampling_geometry --case /tmp/bvn-s182-campaign/cases/minren__attack__neutral__ground__near.json \
  --receipt /tmp/bvn-s183-receipts/minren__attack__neutral__ground__near.json --output /tmp/bvn-s183-geometry.json
python3 -m tools.sampling_display --case /tmp/bvn-s182-campaign/cases/minren__attack__neutral__ground__near.json \
  --receipt /tmp/bvn-s184-receipts/minren__attack__neutral__ground__near.json \
  --exports /tmp/bvn-s184-exports.json --output /tmp/bvn-s184-display.json
mkdir -p /tmp/bvn-s185-godot/frames
/tmp/bvn-s66-tools/engine/Godot.app/Contents/MacOS/Godot --path godot \
  --rendering-method gl_compatibility --resolution 600x400 --log-file /tmp/bvn-s185-godot/capture-engine.log \
  --script res://tests/move_case_reference.gd -- --bitmap-sequence \
  /tmp/bvn-s182-campaign/cases/minren__attack__neutral__ground__near.json /tmp/bvn-s185-godot/frames
python3 -m tools.sampling_bitmap --case /tmp/bvn-s182-campaign/cases/minren__attack__neutral__ground__near.json \
  --receipt /tmp/bvn-s185-receipts/minren__attack__neutral__ground__near.json \
  --godot /tmp/bvn-s185-godot/frames --output /tmp/bvn-s185-comparison.json
# DoAction: n=186; clip-action: n=187 (same collector).
python3 -m tools.sampling_doaction --case /tmp/bvn-s182-campaign/cases/minren__attack__neutral__ground__near.json \
  --receipt /tmp/bvn-s186-receipts/minren__attack__neutral__ground__near.json --output /tmp/bvn-s186-doaction.json
python3 -m tools.sampling_callsite --case /tmp/bvn-s182-campaign/cases/minren__attack__neutral__ground__near.json \
  --receipt /tmp/bvn-s188-receipts/minren__attack__neutral__ground__near.json --output /tmp/bvn-s188-actions.json
```

## Restoring archived evidence

Restore each build archive to its original `/private/tmp/bvn-sNN-build`, decompress
its raw trace to the receipt path, and restore case/receipt paths above. Use this
commit's probes and pinned player; do not rewrite hashes or paths. Build archives
retain metadata, instrumentation diff and five SWFs. Per-folder artifact hashes
bind the evidence; receipt/build files retain source, probe, engine and output hashes.
Godot frames restore under `/tmp/bvn-s185-godot/frames`; native PNGs derive only
from retained BitmapData trace, never uploaded as game textures.

Display joins reuse unchanged main/yihu/helpers from [s30's source archive](../s30/source-exports.tar.gz).
Restore those exports to their recorded paths. Restore the [Minren export](../s184/minren-source-export.tar.gz)
to `/tmp/bvn-s184-source` and s184 `source-exports.json` to `/tmp/bvn-s184-exports.json`.
It was generated with the pinned jar using `-swf2xml game/fighter/minren.swf /tmp/bvn-s184-source/fighter-minren.xml`.
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

## Environment and retries

The first s183 geometry capture failed the unchanged completion-boundary gate.
The unmodified rejected trace, command output and build archive are retained in
s183. The accepted retry uses `/tmp/bvn-s183-build-r02` and run ID
`s183-minren-attack-r02-20261028`; restore its accepted archive to that path.
The other builds retain the paths above. Native captures wait on the shared
`/tmp/bvn-native-flash-capture.lock` without interrupting other characters.
The capture environment JSON is extracted from each capture command's own JSON
output, avoiding the shared temporary environment file.

Lock acquisition used the existing capture API with a 600-second wait:

```sh
python3 -c 'from tools import sampling_native as m; from functools import partial; m.player.capture=partial(m.player.capture,lock_timeout=600); m.main()' --case ... --build ... --trace ... --receipt ... --allow-window-activation --timeout 600
```

Initial Godot import completed before the selected runtime and viewport captures.
All generated import sidecars are excluded from this PR. No gameplay source changed.

Accepted build paths and run IDs (authoritative per receipt):

- s182: `/private/tmp/bvn-s182-build`, `s182-minren-attack-20261028`.
- s183: `/private/tmp/bvn-s183-build-r02`, `s183-minren-attack-r02-20261028`.
- s184: `/private/tmp/bvn-s184-build-r02`, `s184-minren-attack-r02-20261028`.
- s185: `/private/tmp/bvn-s185-build`, `s185-minren-attack-20261028`.
- s186: `/private/tmp/bvn-s186-build`, `s186-minren-attack-20261028`.
- s187: `/private/tmp/bvn-s187-build`, `s187-minren-attack-20261028`.
- s188: `/private/tmp/bvn-s188-build`, `s188-minren-attack-20261028`.

Every rejected completion-boundary attempt retains its raw trace, command output and build archive in the corresponding folder. Restore accepted archives to the exact receipt paths above; never truncate a rejected trace.
