# Rifagu attack: shared reproduction and evidence contract

Only `rifagu__attack__neutral__ground__near`, original generated s203 tape. Base
`02919820`; branch
`feat/sampling-rifagu-attack-one-cell`. No gameplay/Godot implementation changes.
The sole probe change adds the exact Rifagu Sprite638/PlaceObject2_14_31 handler
whose original body matches the existing predicate/call observer. Source edits,
uninstrumented/absent matches and ambiguous selection reject. Existing Deidara
and Chad tests remain green. This is observation selection, not a silent-drop exception.

## Build and native capture

Use fresh paths/run IDs for fresh runs. Each capture is independent; clocks,
random effects and tracing perturbation are not cross-run equivalence proofs.

```sh
python3 -m tools.sampling_matrix generate --output /tmp/bvn-s203-campaign --fighters rifagu --require-native
# Set n/flag: 203/(omit flag), 204/geometry, 205/display, 206/bitmap,
# 207/doaction, 208/clipaction, 209/callsite.
python3 tools/probes/build_ai_reference.py --ffdec /tmp/bvn-s66-tools/ffdec/ffdec.jar \
  --output /tmp/bvn-s204-build --run-id s204-rifagu-attack-20261028 --frames 60 \
  --move-case /tmp/bvn-s203-campaign/cases/rifagu__attack__neutral__ground__near.json \
  --p1-character 日番谷 --p2-character 一护 --p1-helper 我爱罗 --p2-helper 魂 --sampling-geometry
python3 -m tools.sampling_native \
  --case /tmp/bvn-s203-campaign/cases/rifagu__attack__neutral__ground__near.json \
  --build /tmp/bvn-s204-build --trace /tmp/bvn-s204-capture/native.log \
  --receipt /tmp/bvn-s204-receipts/rifagu__attack__neutral__ground__near.json \
  --allow-window-activation --timeout 600
```

Repeat the build/capture with the listed n/flag only for the requested dimension.
Native captures were serialized under the shared native capture lock; each trace uses its own `/tmp/bvn-sNN-capture/native.log` and environment directory. The capture wrapper calls `capture(..., lock_timeout=1800)` then `seal(...)`, allowing parallel character jobs to queue without changing the probe. Each folder retains its own environment file.
Flash process preflight/launch/owned cleanup and the Godot graphics command used
command-scoped escalation, not permanent sandbox changes.

## Gates

```sh
python3 -m tools.sampling_matrix run --campaign /tmp/bvn-s203-campaign \
  --output /tmp/bvn-s203-runtime-r02 --godot /tmp/bvn-s66-tools/engine/Godot.app/Contents/MacOS/Godot \
  --cases rifagu__attack__neutral__ground__near --native-evidence /tmp/bvn-s203-receipts
python3 -m tools.sampling_matrix check --campaign /tmp/bvn-s203-campaign \
  --output /tmp/bvn-s203-runtime-r02 --native-evidence /tmp/bvn-s203-receipts
# Full campaign exits 1: other receipts are missing.
python3 -m tools.sampling_geometry --case /tmp/bvn-s203-campaign/cases/rifagu__attack__neutral__ground__near.json \
  --receipt /tmp/bvn-s204-receipts/rifagu__attack__neutral__ground__near.json --output /tmp/bvn-s204-geometry.json
python3 -m tools.sampling_display --case /tmp/bvn-s203-campaign/cases/rifagu__attack__neutral__ground__near.json \
  --receipt /tmp/bvn-s205-receipts/rifagu__attack__neutral__ground__near.json \
  --exports /tmp/bvn-s205-exports.json --output /tmp/bvn-s205-display.json
mkdir -p /tmp/bvn-s206-godot/frames
/tmp/bvn-s66-tools/engine/Godot.app/Contents/MacOS/Godot --path godot \
  --rendering-method gl_compatibility --resolution 600x400 --log-file /tmp/bvn-s206-godot/capture-engine.log \
  --script res://tests/move_case_reference.gd -- --bitmap-sequence \
  /tmp/bvn-s203-campaign/cases/rifagu__attack__neutral__ground__near.json /tmp/bvn-s206-godot/frames
python3 -m tools.sampling_bitmap --case /tmp/bvn-s203-campaign/cases/rifagu__attack__neutral__ground__near.json \
  --receipt /tmp/bvn-s206-receipts/rifagu__attack__neutral__ground__near.json \
  --godot /tmp/bvn-s206-godot/frames --output /tmp/bvn-s206-comparison.json
# DoAction: n=207; clip-action: n=208 (same collector).
python3 -m tools.sampling_doaction --case /tmp/bvn-s203-campaign/cases/rifagu__attack__neutral__ground__near.json \
  --receipt /tmp/bvn-s207-receipts/rifagu__attack__neutral__ground__near.json --output /tmp/bvn-s207-doaction.json
python3 -m tools.sampling_callsite --case /tmp/bvn-s203-campaign/cases/rifagu__attack__neutral__ground__near.json \
  --receipt /tmp/bvn-s209-receipts/rifagu__attack__neutral__ground__near.json --output /tmp/bvn-s209-actions.json
```

## Restoring archived evidence

Restore each build archive to its original `/private/tmp/bvn-sNN-build`, decompress
its raw trace to the receipt path, and restore case/receipt paths above; native trace paths are `/private/tmp/bvn-sNN-capture/native.log`. Use this
commit's probes and pinned player; do not rewrite hashes or paths. Build archives
retain metadata, instrumentation diff and five SWFs. Per-folder artifact hashes
bind the evidence; receipt/build files retain source, probe, engine and output hashes.
Godot frames restore under `/tmp/bvn-s206-godot/frames`; native PNGs derive only
from retained BitmapData trace, never uploaded as game textures.

Display joins reuse unchanged main/yihu/helpers from [s30's source archive](../s30/source-exports.tar.gz).
Restore those exports to their recorded paths. Restore the [Rifagu export](../s205/rifagu-source-export.tar.gz)
to `/tmp/bvn-s205-source` and s205 `source-exports.json` to `/tmp/bvn-s205-exports.json`.
It was generated with the pinned jar using `-swf2xml game/fighter/rifagu.swf /tmp/bvn-s205-source/fighter-rifagu.xml`.
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


## Character identity

The requested ID `rifagu` is 日番谷 in the locked source catalog. 李洛克 uses `lee`; this slice follows the explicitly requested `rifagu` ID and does not modify Lee evidence. Source paths remain lowercase on disk and in the test binding.

The first required-native Godot run began before fresh resource import finished and failed with missing resource loaders. Its logs/report are retained in `rejected-pre-import-runtime.tar.gz`; the accepted run is executed after import completion.

The display capture was retried after the independently running Godot image sequence finished. Multiple completion-boundary rejections remain retained; this sequencing change is not evidence that host load caused the failures.

## Accepted builds and retained rejected attempts

- s203: accepted run `s203-rifagu-attack-20261028-r02`; original build and trace paths are retained in native-receipt.json.
- s204: accepted run `s204-rifagu-attack-20261028`; original build and trace paths are retained in native-receipt.json.
- s205: accepted run `s205-rifagu-attack-20261028-r06`; original build and trace paths are retained in native-receipt.json.
- s206: accepted run `s206-rifagu-attack-20261028`; original build and trace paths are retained in native-receipt.json.
- s207: accepted run `s207-rifagu-attack-20261028`; original build and trace paths are retained in native-receipt.json.
- s208: accepted run `s208-rifagu-attack-20261028`; original build and trace paths are retained in native-receipt.json.
- s209: accepted run `s209-rifagu-attack-20261028-r03`; original build and trace paths are retained in native-receipt.json.

Rejected attempts retain the complete raw trace, original build and environment under `rejected-attempt-*`; no receipt was issued and no suffix was trimmed. Retry build directories have a `-rNN` suffix; restore each accepted archive at its receipt path.
