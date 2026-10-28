# Yulong attack: seven-dimension reproduction

Base `a703c337`, branch `feat/sampling-yulong-attack-one-cell`.
Only `yulong__attack__neutral__ground__near` from the unchanged generated tape:
P1 Yulong (native name 石田) at x=100, P2 Ichigo at x=150, attack ticks 10–12, 60 fight ticks.
Both source paths are lowercase: `scripts/fighter/yulong.json` and
`game/fighter/yulong.swf`. No gameplay/Godot implementation changes.

## Source binding

The only probe addition selects
`DefineSprite_345/frame_1/PlaceObject2_14_31/CLIPACTIONRECORD onClipEvent(enterFrame).as`
whose exact original body is `if(gameRunning()) { doAllAction(); }`.
The original predicate is evaluated once, and the original unqualified call is
preserved. The locked bundle contains one matching handler. No other form or character binding is added. Changed source, absent/uninstrumented
selection and ambiguity reject. Tests read the exact lowercase bundle path.
This is observer selection, not ownership or game-mechanism implementation.

## Build and capture

Use fresh run IDs and paths for every retry. Restore the selected case from
s238, or generate it with:

```sh
python3 -m tools.sampling_matrix generate --output /tmp/bvn-s238-campaign --fighters yulong --require-native
```

Build dimensions independently: s238/no flag, s239/geometry, s240/display,
s241/bitmap, s242/doaction, s243/clipaction, s244/callsite.

```sh
python3 tools/probes/build_ai_reference.py --ffdec /tmp/bvn-s66-tools/ffdec/ffdec.jar \
  --output /tmp/bvn-s239-build --run-id s239-yulong-attack-20261029 --frames 60 \
  --move-case /tmp/bvn-s238-campaign/cases/yulong__attack__neutral__ground__near.json \
  --p1-character 石田 --p2-character 一护 --p1-helper 我爱罗 --p2-helper 魂 --sampling-geometry
```

Native capture uses `tools.probes.capture_native_player.capture(build, trace,
600, lock_timeout=1800)` followed by `tools.sampling_native.seal(case, build,
trace, player.BINARY, receipt)`. Window activation is authorized. The shared
`/tmp/bvn-native-flash-capture.lock` serializes all native capture attempts. See
each capture-command.txt/environment for exact paths and launches. Original
builds and raw traces are archived; failed completion boundaries issue no
receipt. No tail events are removed. Receipts attest the trusted static build;
`runtime_fighter=null` is not independent runtime identity attestation.

## Gates

```sh
python3 -m tools.sampling_matrix run --campaign /tmp/bvn-s238-campaign \
  --output /tmp/bvn-s238-runtime --godot /tmp/bvn-s66-tools/engine/Godot.app/Contents/MacOS/Godot \
  --cases yulong__attack__neutral__ground__near --native-evidence /tmp/bvn-s238-receipts
python3 -m tools.sampling_matrix check --campaign /tmp/bvn-s238-campaign \
  --output /tmp/bvn-s238-runtime --native-evidence /tmp/bvn-s238-receipts
python3 -m tools.sampling_geometry --case /tmp/bvn-s238-campaign/cases/yulong__attack__neutral__ground__near.json \
  --receipt /tmp/bvn-s239-receipts/yulong__attack__neutral__ground__near.json --output /tmp/bvn-s239-geometry.json
python3 -m tools.sampling_display --case /tmp/bvn-s238-campaign/cases/yulong__attack__neutral__ground__near.json \
  --receipt /tmp/bvn-s240-receipts/yulong__attack__neutral__ground__near.json \
  --exports /tmp/bvn-s240-exports.json --output /tmp/bvn-s240-display.json
python3 -m tools.sampling_bitmap --case /tmp/bvn-s238-campaign/cases/yulong__attack__neutral__ground__near.json \
  --receipt /tmp/bvn-s241-receipts/yulong__attack__neutral__ground__near.json \
  --godot /tmp/bvn-s241-godot/frames --output /tmp/bvn-s241-comparison.json
# Repeat DoAction with n=242 and n=243 (clip-action uses the same collector).
python3 -m tools.sampling_doaction --case /tmp/bvn-s238-campaign/cases/yulong__attack__neutral__ground__near.json \
  --receipt /tmp/bvn-s242-receipts/yulong__attack__neutral__ground__near.json --output /tmp/bvn-s242-doaction.json
python3 -m tools.sampling_callsite --case /tmp/bvn-s238-campaign/cases/yulong__attack__neutral__ground__near.json \
  --receipt /tmp/bvn-s244-receipts/yulong__attack__neutral__ground__near.json --output /tmp/bvn-s244-actions.json
```

Run the pinned Godot editor with `--headless --editor --path godot --import`
before capturing. The initial sandbox import was stopped during import preparation; the
command-scoped elevated retry completed. Both logs are retained. Generated UID
files and imported caches are excluded from this slice.

```sh
mkdir -p /tmp/bvn-s241-godot/frames
/tmp/bvn-s66-tools/engine/Godot.app/Contents/MacOS/Godot --path godot \
  --rendering-method gl_compatibility --resolution 600x400 \
  --log-file /tmp/bvn-s241-godot/capture-engine.log \
  --script res://tests/move_case_reference.gd -- --bitmap-sequence \
  /tmp/bvn-s238-campaign/cases/yulong__attack__neutral__ground__near.json /tmp/bvn-s241-godot/frames
```

Display source joins reuse unchanged main/yihu/helpers from
[s30's source archive](../s30/source-exports.tar.gz). Restore its XMLs to their
recorded paths. Export Yulong via the pinned jar:
`-swf2xml game/fighter/yulong.swf /tmp/bvn-s240-source/fighter-yulong.xml`.
Restore s240's source archive and source-exports.json to those exact paths;
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


## Focused verification

```sh
python3 -m unittest tools.tests.test_sampling_callsite tools.tests.test_sampling_native tools.tests.test_sampling_matrix tools.tests.test_sampling_geometry tools.tests.test_sampling_display tools.tests.test_sampling_bitmap tools.tests.test_sampling_doaction tools.tests.test_sampling_clipaction
python3 -m unittest tools.tests.test_import_guards tools.tests.test_probe_builder tools.tests.test_owned_debugger_probe tools.tests.test_move_reference_mapping tools.tests.test_move_reference_capture_preflight
python3 tools/verify.py
python3 tools/check_handoff.py
/tmp/bvn-s27-venv/bin/python tools/validate_contracts.py
```

The 83 sampling and 40 probe/import tests are distinct. Native receipts verify
source/build/trace hashes and capture completeness; they do not establish
Flash/Godot parity. s239 retains three `missing-source-list` observer errors
for `_level0.game.p1.mc.k1atm.mian` at ticks 16–18. The complete raw capture
contains 61 geometry boundaries and 245 box records, but the geometry gate
rejects it. No source lists, receiver classification or gameplay rules were
guessed to bypass this failure.

An initial build using the informal name 玉龙 rejected before instrumentation
with `move fixture fighter mismatch`; all captured builds use the source menu
name 石田. A sandbox capture launch rejected process inspection before starting
Flash; the command-scoped elevated capture used the same validated build.

## Actual retained paths and rejected attempts

- s238: build `/private/tmp/bvn-s238-build-r02`, trace `/private/tmp/bvn-s238-capture-r02/native.log`. Receipt admitted.
- s239: build `/private/tmp/bvn-s239-build`, trace `/private/tmp/bvn-s239-capture/native.log`. Receipt admitted.
- s240: build `/private/tmp/bvn-s240-build-r02`, trace `/private/tmp/bvn-s240-capture-r02/native.log`. Receipt rejected; raw evidence only.
- s241: build `/private/tmp/bvn-s241-build`, trace `/private/tmp/bvn-s241-capture/native.log`. Receipt admitted.
- s242: build `/private/tmp/bvn-s242-build`, trace `/private/tmp/bvn-s242-capture/native.log`. Receipt admitted.
- s243: build `/private/tmp/bvn-s243-build`, trace `/private/tmp/bvn-s243-capture/native.log`. Receipt admitted.
- s244: build `/private/tmp/bvn-s244-build`, trace `/private/tmp/bvn-s244-capture/native.log`. Receipt admitted.

The first failed attempts for s238/s240 are retained under rejected-attempt-1 filenames. Later rejected attempts retain the ordinary native-* filenames. Neither suffix events nor source obligations were removed. See character-acceptance.json for per-dimension results.
