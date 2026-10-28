# Yijiao attack: seven-dimension reproduction

Base `70951935`, branch `feat/sampling-yijiao-attack-one-cell`.
Only `yijiao__attack__neutral__ground__near` from the unchanged generated tape:
P1 Yijiao at x=100, P2 Ichigo at x=150, attack ticks 10–12, 60 fight ticks.
Both source paths are lowercase: `scripts/fighter/yijiao.json` and
`game/fighter/yijiao.swf`. No gameplay/Godot implementation changes.

## Source binding

The only probe addition selects
`DefineSprite_455/frame_1/PlaceObject2_18_31/CLIPACTIONRECORD onClipEvent(enterFrame).as`
whose exact original body is `if(gameRunning()) { doAllAction(); }`.
The original predicate is evaluated once, and the original unqualified call is
preserved. The frame-12 handler has the same body but is not selected for
call-site markers; it remains in the complete clip-action inventory. No other
form or character binding is added. Changed source, absent/uninstrumented
selection and ambiguity reject. Tests read the exact lowercase bundle path.
This is observer selection, not ownership or game-mechanism implementation.

## Build and capture

Use fresh run IDs and paths for every retry. Restore the selected case from
s231, or generate it with:

```sh
python3 -m tools.sampling_matrix generate --output /tmp/bvn-s231-campaign --fighters yijiao --require-native
```

Build dimensions independently: s231/no flag, s232/geometry, s233/display,
s234/bitmap, s235/doaction, s236/clipaction, s237/callsite.

```sh
python3 tools/probes/build_ai_reference.py --ffdec /tmp/bvn-s66-tools/ffdec/ffdec.jar \
  --output /tmp/bvn-s232-build --run-id s232-yijiao-attack-20261028 --frames 60 \
  --move-case /tmp/bvn-s231-campaign/cases/yijiao__attack__neutral__ground__near.json \
  --p1-character 一角 --p2-character 一护 --p1-helper 我爱罗 --p2-helper 魂 --sampling-geometry
```

Native capture uses `tools.probes.capture_native_player.capture(build, trace,
600, lock_timeout=1800)` followed by `tools.sampling_native.seal(case, build,
trace, player.BINARY, receipt)`. Window activation is authorized. The shared
`/tmp/bvn-native-flash-capture.lock` serializes capture with sibling jobs. See
each capture-command.txt/environment for exact paths and launches. Original
builds and raw traces are archived; failed completion boundaries issue no
receipt. No tail events are removed. Receipts attest the trusted static build;
`runtime_fighter=null` is not independent runtime identity attestation.

## Gates

```sh
python3 -m tools.sampling_matrix run --campaign /tmp/bvn-s231-campaign \
  --output /tmp/bvn-s231-runtime --godot /tmp/bvn-s66-tools/engine/Godot.app/Contents/MacOS/Godot \
  --cases yijiao__attack__neutral__ground__near --native-evidence /tmp/bvn-s231-receipts
python3 -m tools.sampling_matrix check --campaign /tmp/bvn-s231-campaign \
  --output /tmp/bvn-s231-runtime --native-evidence /tmp/bvn-s231-receipts
python3 -m tools.sampling_geometry --case /tmp/bvn-s231-campaign/cases/yijiao__attack__neutral__ground__near.json \
  --receipt /tmp/bvn-s232-receipts/yijiao__attack__neutral__ground__near.json --output /tmp/bvn-s232-geometry.json
python3 -m tools.sampling_display --case /tmp/bvn-s231-campaign/cases/yijiao__attack__neutral__ground__near.json \
  --receipt /tmp/bvn-s233-receipts/yijiao__attack__neutral__ground__near.json \
  --exports /tmp/bvn-s233-exports.json --output /tmp/bvn-s233-display.json
python3 -m tools.sampling_bitmap --case /tmp/bvn-s231-campaign/cases/yijiao__attack__neutral__ground__near.json \
  --receipt /tmp/bvn-s234-receipts/yijiao__attack__neutral__ground__near.json \
  --godot /tmp/bvn-s234-godot/frames --output /tmp/bvn-s234-comparison.json
# Repeat DoAction with n=235 and n=236 (clip-action uses the same collector).
python3 -m tools.sampling_doaction --case /tmp/bvn-s231-campaign/cases/yijiao__attack__neutral__ground__near.json \
  --receipt /tmp/bvn-s235-receipts/yijiao__attack__neutral__ground__near.json --output /tmp/bvn-s235-doaction.json
python3 -m tools.sampling_callsite --case /tmp/bvn-s231-campaign/cases/yijiao__attack__neutral__ground__near.json \
  --receipt /tmp/bvn-s237-receipts/yijiao__attack__neutral__ground__near.json --output /tmp/bvn-s237-actions.json
```

Run the pinned Godot editor with `--headless --editor --path godot --import`
before capturing. The initial sandbox import was stopped during scanning; the
command-scoped elevated retry completed. Both logs are retained. Generated UID
files and imported caches are excluded from this slice.

```sh
mkdir -p /tmp/bvn-s234-godot/frames
/tmp/bvn-s66-tools/engine/Godot.app/Contents/MacOS/Godot --path godot \
  --rendering-method gl_compatibility --resolution 600x400 \
  --log-file /tmp/bvn-s234-godot/capture-engine.log \
  --script res://tests/move_case_reference.gd -- --bitmap-sequence \
  /tmp/bvn-s231-campaign/cases/yijiao__attack__neutral__ground__near.json /tmp/bvn-s234-godot/frames
```

Display source joins reuse unchanged main/yihu/helpers from
[s30's source archive](../s30/source-exports.tar.gz). Restore its XMLs to their
recorded paths. Export Yijiao via the pinned jar:
`-swf2xml game/fighter/yijiao.swf /tmp/bvn-s233-source/fighter-yijiao.xml`.
Restore s233's source archive and source-exports.json to those exact paths;
source and XML hashes were independently checked before the join.

## Limits and restoration

Each receipt retains exact build/trace/engine paths and hashes. Restore normal
build archives into the build directory recorded in capture-command.txt;
rejected-attempt archives include their build-directory prefix. Restore raw
logs at the recorded trace paths and receipts at the paths above. Use this
commit's probes and original pinned engine. No receipt exists for rejected
captures; do not synthesize one from a diagnostic report.

Geometry records candidates, not damage eligibility or exact intra-frame
creation/removal. Display includes hierarchy, transforms, depths and camera
chain; dynamic masks and framebuffer clipping remain unproven. Bitmap capture
losslessly decodes native opaque 600×400 ARGB to RGBA; Godot PNGs are actual
viewport outputs. No crop, alignment, resize, gamma adjustment or tolerance.
Native PNGs are evidence only, never game textures. Action entries and paired
calls do not prove callee bodies, all branches, dynamic dispatch or Godot
ownership. Every source obligation remains retained, including unvisited ones.
Independent runs do not prove clock/random/render-phase equivalence.
`production_admitted=false`; `native_parity_proven=false` throughout.

## Actual retained paths and rejected attempts

- s231: build `/private/tmp/bvn-s231-build-r02`, trace `/private/tmp/bvn-s231-capture-r02/native.log`. Receipt rejected; raw evidence only.
- s232: build `/private/tmp/bvn-s232-build-r02`, trace `/private/tmp/bvn-s232-capture-r02/native.log`. Receipt rejected; raw evidence only.
- s233: build `/private/tmp/bvn-s233-build-r02`, trace `/private/tmp/bvn-s233-capture-r02/native.log`. Receipt rejected; raw evidence only.
- s234: build `/private/tmp/bvn-s234-build`, trace `/private/tmp/bvn-s234-capture/native.log`. Receipt admitted.
- s235: build `/private/tmp/bvn-s235-build-r02`, trace `/private/tmp/bvn-s235-capture-r02/native.log`. Receipt rejected; raw evidence only.
- s236: build `/private/tmp/bvn-s236-build`, trace `/private/tmp/bvn-s236-capture/native.log`. Receipt admitted.
- s237: build `/private/tmp/bvn-s237-build`, trace `/private/tmp/bvn-s237-capture/native.log`. Receipt rejected; raw evidence only.

The first failed attempts for s231/s232/s233/s235 are retained under rejected-attempt-1 filenames. Later rejected attempts retain the ordinary native-* filenames. Neither suffix events nor source obligations were removed. See character-acceptance.json for per-dimension results.
