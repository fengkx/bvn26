# Pain attack: shared reproduction and evidence contract

Only `pain__attack__neutral__ground__near`, original generated s196 tape. Base
`02919820`; branch
`feat/sampling-pain-attack-one-cell`. No gameplay/Godot implementation changes.
The sole probe change adds the exact Pain Sprite573/PlaceObject2_18_33 handler
whose original body matches the existing predicate/call observer. Source edits,
uninstrumented/absent matches and ambiguous selection reject. Existing Deidara
and Chad tests remain green. This is observation selection, not a silent-drop exception.

## Build and native capture

Use fresh paths/run IDs for fresh runs. Each capture is independent; clocks,
random effects and tracing perturbation are not cross-run equivalence proofs.

```sh
python3 -m tools.sampling_matrix generate --output /tmp/bvn-s196-campaign --fighters pain --require-native
# Set n/flag: 196/(omit flag), 197/geometry, 198/display, 199/bitmap,
# 200/doaction, 201/clipaction, 202/callsite.
python3 tools/probes/build_ai_reference.py --ffdec /tmp/bvn-s66-tools/ffdec/ffdec.jar \
  --output /tmp/bvn-s197-build --run-id s197-pain-attack-20261028 --frames 60 \
  --move-case /tmp/bvn-s196-campaign/cases/pain__attack__neutral__ground__near.json \
  --p1-character 佩恩 --p2-character 一护 --p1-helper 我爱罗 --p2-helper 魂 --sampling-geometry
python3 -m tools.sampling_native \
  --case /tmp/bvn-s196-campaign/cases/pain__attack__neutral__ground__near.json \
  --build /tmp/bvn-s197-build --trace /tmp/bvn-s197-capture/native.log \
  --receipt /tmp/bvn-s197-receipts/pain__attack__neutral__ground__near.json \
  --allow-window-activation --timeout 600
```

Repeat the build/capture with the listed n/flag only for the requested dimension.
Native captures were serialized under the shared native capture lock; each trace uses its own `/tmp/bvn-sNN-capture/native.log` and environment directory. The capture wrapper calls `capture(..., lock_timeout=1800)` then `seal(...)`, allowing parallel character jobs to queue without changing the probe. Each folder retains its own environment file.
Flash process preflight/launch/owned cleanup and the Godot graphics command used
command-scoped escalation, not permanent sandbox changes.

## Gates

```sh
python3 -m tools.sampling_matrix run --campaign /tmp/bvn-s196-campaign \
  --output /tmp/bvn-s196-runtime --godot /tmp/bvn-s66-tools/engine/Godot.app/Contents/MacOS/Godot \
  --cases pain__attack__neutral__ground__near --native-evidence /tmp/bvn-s196-receipts
python3 -m tools.sampling_matrix check --campaign /tmp/bvn-s196-campaign \
  --output /tmp/bvn-s196-runtime --native-evidence /tmp/bvn-s196-receipts
# Full campaign exits 1: other receipts are missing.
python3 -m tools.sampling_geometry --case /tmp/bvn-s196-campaign/cases/pain__attack__neutral__ground__near.json \
  --receipt /tmp/bvn-s197-receipts/pain__attack__neutral__ground__near.json --output /tmp/bvn-s197-geometry.json
python3 -m tools.sampling_display --case /tmp/bvn-s196-campaign/cases/pain__attack__neutral__ground__near.json \
  --receipt /tmp/bvn-s198-receipts/pain__attack__neutral__ground__near.json \
  --exports /tmp/bvn-s198-exports.json --output /tmp/bvn-s198-display.json
mkdir -p /tmp/bvn-s199-godot/frames
/tmp/bvn-s66-tools/engine/Godot.app/Contents/MacOS/Godot --path godot \
  --rendering-method gl_compatibility --resolution 600x400 --log-file /tmp/bvn-s199-godot/capture-engine.log \
  --script res://tests/move_case_reference.gd -- --bitmap-sequence \
  /tmp/bvn-s196-campaign/cases/pain__attack__neutral__ground__near.json /tmp/bvn-s199-godot/frames
python3 -m tools.sampling_bitmap --case /tmp/bvn-s196-campaign/cases/pain__attack__neutral__ground__near.json \
  --receipt /tmp/bvn-s199-receipts/pain__attack__neutral__ground__near.json \
  --godot /tmp/bvn-s199-godot/frames --output /tmp/bvn-s199-comparison.json
# DoAction: n=200; clip-action: n=201 (same collector).
python3 -m tools.sampling_doaction --case /tmp/bvn-s196-campaign/cases/pain__attack__neutral__ground__near.json \
  --receipt /tmp/bvn-s200-receipts/pain__attack__neutral__ground__near.json --output /tmp/bvn-s200-doaction.json
python3 -m tools.sampling_callsite --case /tmp/bvn-s196-campaign/cases/pain__attack__neutral__ground__near.json \
  --receipt /tmp/bvn-s202-receipts/pain__attack__neutral__ground__near.json --output /tmp/bvn-s202-actions.json
```

## Restoring archived evidence

Restore each build archive to its original `/private/tmp/bvn-sNN-build`, decompress
its raw trace to the receipt path, and restore case/receipt paths above; native trace paths are `/private/tmp/bvn-sNN-capture/native.log`. Use this
commit's probes and pinned player; do not rewrite hashes or paths. Build archives
retain metadata, instrumentation diff and five SWFs. Per-folder artifact hashes
bind the evidence; receipt/build files retain source, probe, engine and output hashes.
Godot frames restore under `/tmp/bvn-s199-godot/frames`; native PNGs derive only
from retained BitmapData trace, never uploaded as game textures.

Display joins reuse unchanged main/yihu/helpers from [s30's source archive](../s30/source-exports.tar.gz).
Restore those exports to their recorded paths. Restore the [Pain export](../s198/pain-source-export.tar.gz)
to `/tmp/bvn-s198-source` and s198 `source-exports.json` to `/tmp/bvn-s198-exports.json`.
It was generated with the pinned jar using `-swf2xml game/fighter/pain.swf /tmp/bvn-s198-source/fighter-pain.xml`.
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

## Fresh worktree preparation

Run the pinned Godot editor with `--headless --editor --path godot --import`
before the probes to populate ignored resource caches. Generated `.uid` files
are excluded from this slice. No production content is changed.

## Capture and environment retries

The initial s197 geometry trace was rejected for events beyond completion boundary.
Its complete trace, environment and build are retained as rejected-* in s197.
The accepted retry uses `/tmp/bvn-s197-build-r02` and run ID
`s197-pain-attack-20261028-r02`. No log suffix was removed.

Initial tests failed because Pillow was absent. Final tests and image processing use
`/tmp/bvn-pain-venv/bin/python` with Pillow and jsonschema installed.
Godot probes launched before resource import completed failed with missing imported
textures; their logs are retained, and final probes run after import completion.

The initial s198 display trace was also rejected for events beyond completion
boundary. Its full rejected-r01 archive is in s198; accepted display capture uses
`/tmp/bvn-s198-build-r02` and `s198-pain-attack-20261028-r02`.

Final validation commands (all 144 tests):

```sh
/tmp/bvn-pain-venv/bin/python -m unittest -v tools.tests.test_move_acceptance_harness tools.tests.test_move_cases_paths tools.tests.test_move_cases_targets tools.tests.test_sampling_bitmap tools.tests.test_sampling_callsite tools.tests.test_sampling_clipaction tools.tests.test_sampling_display tools.tests.test_sampling_doaction tools.tests.test_sampling_geometry tools.tests.test_sampling_matrix tools.tests.test_sampling_native
/tmp/bvn-pain-venv/bin/python -m unittest -v tools.tests.test_import_guards tools.tests.test_qualified_visual_control_guard
/tmp/bvn-pain-venv/bin/python -m unittest -v tools.tests.test_hit_receive_observer tools.tests.test_move_reference_capture_preflight tools.tests.test_move_reference_helper_mapping tools.tests.test_move_reference_mapping tools.tests.test_probe_builder
```
