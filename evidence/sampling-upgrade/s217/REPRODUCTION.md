# Sasuke attack: shared reproduction and evidence contract

Only `sasuke__attack__neutral__ground__near`, original generated s217 tape. Base
`02919820`; branch
`feat/sampling-sasuke-attack-one-cell`. No gameplay/Godot implementation changes.
The sole probe change adds the exact Sasuke Sprite603/PlaceObject2_16_31 handler
whose original body matches the existing predicate/call observer. Source edits,
uninstrumented/absent matches and ambiguous selection reject. Existing Deidara
and Chad tests remain green. This is observation selection, not a silent-drop exception.

## Build and native capture

Use fresh paths/run IDs for fresh runs. Each capture is independent; clocks,
random effects and tracing perturbation are not cross-run equivalence proofs.

```sh
python3 -m tools.sampling_matrix generate --output /tmp/bvn-s217-campaign --fighters sasuke --require-native
# Set n/flag: 217/(omit flag), 218/geometry, 219/display, 220/bitmap,
# 221/doaction, 222/clipaction, 223/callsite.
python3 tools/probes/build_ai_reference.py --ffdec /tmp/bvn-s66-tools/ffdec/ffdec.jar \
  --output /tmp/bvn-s218-build --run-id s218-sasuke-attack-20261028 --frames 60 \
  --move-case /tmp/bvn-s217-campaign/cases/sasuke__attack__neutral__ground__near.json \
  --p1-character 佐助 --p2-character 一护 --p1-helper 我爱罗 --p2-helper 魂 --sampling-geometry
python3 -m tools.sampling_native \
  --case /tmp/bvn-s217-campaign/cases/sasuke__attack__neutral__ground__near.json \
  --build /tmp/bvn-s218-build --trace /tmp/bvn-s218-capture/native.log \
  --receipt /tmp/bvn-s218-receipts/sasuke__attack__neutral__ground__near.json \
  --allow-window-activation --timeout 600
```

Repeat the build/capture with the listed n/flag only for the requested dimension.
Native captures were serialized under the shared native capture lock; each trace uses its own `/tmp/bvn-sNN-capture/native.log` and environment directory. The capture wrapper calls `capture(..., lock_timeout=1800)` then `seal(...)`, allowing parallel character jobs to queue without changing the probe. Each folder retains its own environment file. Only s217/s220/s221/s222 have admitted receipts; the other receipt-producing commands fail without issuing a receipt.
Flash process preflight/launch/owned cleanup and the Godot graphics command used
command-scoped escalation, not permanent sandbox changes.

## Gates

```sh
python3 -m tools.sampling_matrix run --campaign /tmp/bvn-s217-campaign \
  --output /tmp/bvn-s217-runtime-r02 --godot /tmp/bvn-s66-tools/engine/Godot.app/Contents/MacOS/Godot \
  --cases sasuke__attack__neutral__ground__near --native-evidence /tmp/bvn-s217-receipts
python3 -m tools.sampling_matrix check --campaign /tmp/bvn-s217-campaign \
  --output /tmp/bvn-s217-runtime-r02 --native-evidence /tmp/bvn-s217-receipts
# Full campaign exits 1: other receipts are missing.
python3 -m tools.sampling_geometry --case /tmp/bvn-s217-campaign/cases/sasuke__attack__neutral__ground__near.json \
  --receipt /tmp/bvn-s218-receipts/sasuke__attack__neutral__ground__near.json --output /tmp/bvn-s218-geometry.json
python3 -m tools.sampling_display --case /tmp/bvn-s217-campaign/cases/sasuke__attack__neutral__ground__near.json \
  --receipt /tmp/bvn-s219-receipts/sasuke__attack__neutral__ground__near.json \
  --exports /tmp/bvn-s219-exports.json --output /tmp/bvn-s219-display.json
mkdir -p /tmp/bvn-s220-godot/frames
/tmp/bvn-s66-tools/engine/Godot.app/Contents/MacOS/Godot --path godot \
  --rendering-method gl_compatibility --resolution 600x400 --log-file /tmp/bvn-s220-godot/capture-engine.log \
  --script res://tests/move_case_reference.gd -- --bitmap-sequence \
  /tmp/bvn-s217-campaign/cases/sasuke__attack__neutral__ground__near.json /tmp/bvn-s220-godot/frames
python3 -m tools.sampling_bitmap --case /tmp/bvn-s217-campaign/cases/sasuke__attack__neutral__ground__near.json \
  --receipt /tmp/bvn-s220-receipts/sasuke__attack__neutral__ground__near.json \
  --godot /tmp/bvn-s220-godot/frames --output /tmp/bvn-s220-comparison.json
# DoAction: n=221; clip-action: n=222 (same collector).
python3 -m tools.sampling_doaction --case /tmp/bvn-s217-campaign/cases/sasuke__attack__neutral__ground__near.json \
  --receipt /tmp/bvn-s221-receipts/sasuke__attack__neutral__ground__near.json --output /tmp/bvn-s221-doaction.json
python3 -m tools.sampling_callsite --case /tmp/bvn-s217-campaign/cases/sasuke__attack__neutral__ground__near.json \
  --receipt /tmp/bvn-s223-receipts/sasuke__attack__neutral__ground__near.json --output /tmp/bvn-s223-actions.json
```

## Restoring archived evidence

Restore each build archive to its original `/private/tmp/bvn-sNN-build`, decompress
its raw trace to the receipt path, and restore case/receipt paths above; native trace paths are `/private/tmp/bvn-sNN-capture/native.log`. Use this
commit's probes and pinned player; do not rewrite hashes or paths. Build archives
retain metadata, instrumentation diff and five SWFs. Per-folder artifact hashes
bind the evidence; receipt/build files retain source, probe, engine and output hashes.
Godot frames restore under `/tmp/bvn-s220-godot/frames`; native PNGs derive only
from retained BitmapData trace, never uploaded as game textures.

The unevaluated display join is configured to reuse unchanged main/yihu/helpers from [s30's source archive](../s30/source-exports.tar.gz).
Restore those exports to their recorded paths. Restore the [Sasuke export](../s219/sasuke-source-export.tar.gz)
to `/tmp/bvn-s219-source` and s219 `source-exports.json` to `/tmp/bvn-s219-exports.json`.
It was generated with the pinned jar using `-swf2xml game/fighter/Sasuke.swf /tmp/bvn-s219-source/fighter-sasuke.xml`.
The recorded source/XML hashes were verified. Receipt rejection prevents the display join from running.

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

## Fresh worktree preparation

Run the pinned Godot editor with `--headless --editor --path godot --import`
before the probes to populate ignored resource caches. Generated `.uid` files
are excluded from this slice. No production content is changed.

## Retained rejected attempts

All four s218 geometry attempts, all three s219 display attempts, and both s223
call-site attempts emitted events after the completion boundary. The unchanged validator
rejected each; no receipt was issued and no suffix was trimmed. Full raw traces,
build archives and environment records are retained with `rejected-*` names.
Geometry attempt 2 reused the first build; attempt 3 uses build-r03. Display
attempt 2 uses build-r02. The final failed builds use s218-build-r04,
s219-build-r03 and s223-build-r02 respectively, with corresponding fresh run IDs.
Their full raw traces and builds use the ordinary native-* filenames. No native
receipt exists for these three dimensions. The call-site diagnostic is explicitly
unadmitted and consumes the entire raw stream, including the invalid suffix.

The initial s217 Godot execution ran before resource imports were ready and failed
with missing resource loaders. Its report and logs are retained in
`rejected-pre-import-runtime.tar.gz`. The retry uses `/tmp/bvn-s217-runtime-r02`.
The sandbox import was stopped and a command-scoped elevated import populated
ignored caches. Both import logs are retained.
