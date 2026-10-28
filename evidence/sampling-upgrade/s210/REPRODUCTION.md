# Rukia attack: shared reproduction and evidence contract

Only `rukia__attack__neutral__ground__near`, original generated s210 tape. Base
`02919820`; branch
`feat/sampling-rukia-attack-one-cell`. No gameplay/Godot implementation changes.
The locked catalog name is 露其雅; paths remain lowercase `game/fighter/rukia.swf` and `scripts/fighter/rukia.json`. Base root placement is Sprite 533; Sprite 976 is another form and is not selected.
The sole probe change adds the exact Rukia Sprite533/PlaceObject2_16_31 handler
whose original body matches the existing predicate/call observer. Source edits,
uninstrumented/absent matches and ambiguous selection reject. Existing Deidara
and Chad tests remain green. This is observation selection, not a silent-drop exception.

## Build and native capture

Use fresh paths/run IDs for fresh runs. Each capture is independent; clocks,
random effects and tracing perturbation are not cross-run equivalence proofs.

```sh
/tmp/bvn-rukia-venv/bin/python -m tools.sampling_matrix generate --output /tmp/bvn-s210-campaign --fighters rukia --require-native
# Set n/flag: 210/(omit flag), 211/geometry, 212/display, 213/bitmap,
# 214/doaction, 215/clipaction, 216/callsite.
/tmp/bvn-rukia-venv/bin/python tools/probes/build_ai_reference.py --ffdec /tmp/bvn-s66-tools/ffdec/ffdec.jar \
  --output /tmp/bvn-s211-build --run-id s211-rukia-attack-20261028 --frames 60 \
  --move-case /tmp/bvn-s210-campaign/cases/rukia__attack__neutral__ground__near.json \
  --p1-character 露其雅 --p2-character 一护 --p1-helper 我爱罗 --p2-helper 魂 --sampling-geometry
/tmp/bvn-rukia-venv/bin/python -m tools.sampling_native \
  --case /tmp/bvn-s210-campaign/cases/rukia__attack__neutral__ground__near.json \
  --build /tmp/bvn-s211-build --trace /tmp/bvn-s211-capture/native.log \
  --receipt /tmp/bvn-s211-receipts/rukia__attack__neutral__ground__near.json \
  --allow-window-activation --timeout 600
```

Repeat the build/capture with the listed n/flag only for the requested dimension.
Native captures were serialized under the shared native capture lock; each trace uses its own `/tmp/bvn-sNN-capture/native.log` and environment directory. The capture wrapper calls `capture(..., lock_timeout=1800)` then `seal(...)`, allowing parallel character jobs to queue without changing the probe. Each folder retains its own environment file.
Flash process preflight/launch/owned cleanup and the Godot graphics command used
command-scoped escalation, not permanent sandbox changes.

## Gates

```sh
/tmp/bvn-rukia-venv/bin/python -m tools.sampling_matrix run --campaign /tmp/bvn-s210-campaign \
  --output /tmp/bvn-s210-runtime --godot /tmp/bvn-s66-tools/engine/Godot.app/Contents/MacOS/Godot \
  --cases rukia__attack__neutral__ground__near --native-evidence /tmp/bvn-s210-receipts
/tmp/bvn-rukia-venv/bin/python -m tools.sampling_matrix check --campaign /tmp/bvn-s210-campaign \
  --output /tmp/bvn-s210-runtime --native-evidence /tmp/bvn-s210-receipts
# Full campaign exits 1: other receipts are missing.
/tmp/bvn-rukia-venv/bin/python -m tools.sampling_geometry --case /tmp/bvn-s210-campaign/cases/rukia__attack__neutral__ground__near.json \
  --receipt /tmp/bvn-s211-receipts/rukia__attack__neutral__ground__near.json --output /tmp/bvn-s211-geometry.json
/tmp/bvn-rukia-venv/bin/python -m tools.sampling_display --case /tmp/bvn-s210-campaign/cases/rukia__attack__neutral__ground__near.json \
  --receipt /tmp/bvn-s212-receipts/rukia__attack__neutral__ground__near.json \
  --exports /tmp/bvn-s212-exports.json --output /tmp/bvn-s212-display.json
mkdir -p /tmp/bvn-s213-godot/frames
/tmp/bvn-s66-tools/engine/Godot.app/Contents/MacOS/Godot --path godot \
  --rendering-method gl_compatibility --resolution 600x400 --log-file /tmp/bvn-s213-godot/capture-engine.log \
  --script res://tests/move_case_reference.gd -- --bitmap-sequence \
  /tmp/bvn-s210-campaign/cases/rukia__attack__neutral__ground__near.json /tmp/bvn-s213-godot/frames
/tmp/bvn-rukia-venv/bin/python -m tools.sampling_bitmap --case /tmp/bvn-s210-campaign/cases/rukia__attack__neutral__ground__near.json \
  --receipt /tmp/bvn-s213-receipts/rukia__attack__neutral__ground__near.json \
  --godot /tmp/bvn-s213-godot/frames --output /tmp/bvn-s213-comparison.json
# DoAction: n=214; clip-action: n=215 (same collector).
/tmp/bvn-rukia-venv/bin/python -m tools.sampling_doaction --case /tmp/bvn-s210-campaign/cases/rukia__attack__neutral__ground__near.json \
  --receipt /tmp/bvn-s214-receipts/rukia__attack__neutral__ground__near.json --output /tmp/bvn-s214-doaction.json
/tmp/bvn-rukia-venv/bin/python -m tools.sampling_callsite --case /tmp/bvn-s210-campaign/cases/rukia__attack__neutral__ground__near.json \
  --receipt /tmp/bvn-s216-receipts/rukia__attack__neutral__ground__near.json --output /tmp/bvn-s216-actions.json
```

## Restoring archived evidence

Restore each build archive to its original `/private/tmp/bvn-sNN-build`, decompress
its raw trace to the receipt path, and restore case/receipt paths above; native trace paths are `/private/tmp/bvn-sNN-capture/native.log`. Use this
commit's probes and pinned player; do not rewrite hashes or paths. Build archives
retain metadata, instrumentation diff and five SWFs. Per-folder artifact hashes
bind the evidence; receipt/build files retain source, probe, engine and output hashes.
Godot frames restore under `/tmp/bvn-s213-godot/frames`; native PNGs derive only
from retained BitmapData trace, never uploaded as game textures.

Display joins reuse unchanged main/yihu/helpers from [s30's source archive](../s30/source-exports.tar.gz).
Restore those exports to their recorded paths. Restore the [Rukia export](../s212/rukia-source-export.tar.gz)
to `/tmp/bvn-s212-source` and s212 `source-exports.json` to `/tmp/bvn-s212-exports.json`.
It was generated with the pinned jar using `-swf2xml game/fighter/rukia.swf /tmp/bvn-s212-source/fighter-rukia.xml`.
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


## Initial setup failures

The first build rejected the display name 露琪亚 before compilation; the locked catalog key is 露其雅. The failure is recorded in setup-failures.json. Initial test attempts lacked Pillow; the successful runs use an isolated temporary environment with Pillow and requirements-dev.txt. No source or gate was changed to bypass either error.

## Retained completion-boundary failures

All rejected native traces are complete and untrimmed. See character-acceptance.json for the list. Accepted receipt paths (restore archives to these paths, not to the initial attempt paths):

- s210: build `/private/tmp/bvn-s210-build`, trace `/private/tmp/bvn-s210-capture/native.log`.
- s211: build `/private/tmp/bvn-s211-build-r06`, trace `/private/tmp/bvn-s211-capture-r06/native.log`.
- s212: build `/private/tmp/bvn-s212-build-r011`, trace `/private/tmp/bvn-s212-capture-r011/native.log`.
- s213: build `/private/tmp/bvn-s213-build`, trace `/private/tmp/bvn-s213-capture/native.log`.
- s214: build `/private/tmp/bvn-s214-build`, trace `/private/tmp/bvn-s214-capture/native.log`.
- s215: build `/private/tmp/bvn-s215-build`, trace `/private/tmp/bvn-s215-capture/native.log`.
- s216: build `/private/tmp/bvn-s216-build`, trace `/private/tmp/bvn-s216-capture/native.log`.

The initial Godot viewport capture began before asset import completed; its full partial frame archive and logs are retained in s213/rejected-import-*. The accepted retry produced 61 frames with no SCRIPT ERROR or ERROR diagnostics. The import log preserves editor-settings save errors separately.
