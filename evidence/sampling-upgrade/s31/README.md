# s31 — One-cell BitmapData capture and strict byte gate

Base `1e942e1a4d2188ee8f8f348a3a237c9910b00e0d`; branch
`feat/sampling-bitmapdata-one-cell`. Only the unchanged s28 tape
`didala__attack__neutral__ground__near` (ticks 0–60).
`native_parity_proven=false`; `production_admitted=false`.

## Results and review map

- **Real native capture passes**: 30,059 events; 61/61 images, each 600×400;
  58,560,000 RGBA bytes. Receipt revalidation passes. Every alpha byte is 255.
  Removing a real frame or row rejects, then the original rechecks 61/61.
- **Real Godot capture now passes** after user-approved command-only escalation:
  OpenGL 4.1 Metal / Apple M2, 61/61 actual 600×400 RGBA images, all alpha 255.
  Every replay's actor-state prefix covers its target tick. Removing image 010
  rejects; restoration revalidates all 61 hashes/images.
- The actual byte comparison **exits 1: 0/61 exact frames**, with **18,630,929
  differing channels**, **7,189,017 differing pixels**, maximum channel delta
  **255**. `comparison.json` preserves counts and first coordinates/bytes for
  every frame. No image was resized, aligned, substituted or omitted.
- **61 focused tests + 19 probe tests pass**. Godot parser and unchanged default
  one-cell runner pass. Default headless runner reports the existing exit
  resource-leak warnings, retained in its log. Integrity/handoff/contracts pass.

Review `tools/sampling_bitmap.py` and its six tests first; then the opt-in
`sampling_bitmap.as`/builder branch and `--bitmap-sequence` mode of the existing
Godot move runner. Archives contain real reproduction material, not new game
assets. No game/importer semantics, original source or reference images changed.

## Pixel and observation contract

Native draws `_root` synchronously into `BitmapData(600,400,false,0)` at the
existing root observer, after actor state samples and before terminal quit.
Each row is losslessly run-length encoded. `getPixel32` ARGB words are decoded
explicitly into RGBA bytes. Opaque black is the declared destination; straight
versus premultiplied representation coincides at alpha 255. This slice does not
claim transparent-destination alpha coverage or color-managed screenshot parity.
No resizing, gamma correction, channel tolerance, cropped comparison or omitted
frame is allowed. PNG bytes are decoded as RGBA, not compared as compressed files.

Godot mode reuses the same tape and runner. For each target tick it replays from
fresh actors, returns true at the existing terminal root-observer boundary
(`main.gd::_advance_fight`), skips deferred target scripts, disables scene
processing, waits for pending drawing and captures the actual root viewport.
All 61 images are required; output directories must be fresh. It records case,
runner, engine and PNG hashes. Default runner behavior is unchanged. The planned
capture is the actual `main.tscn` viewport, not native pixels uploaded as textures.
The real path has now executed. Render settlement equivalence still needs
analysis: matching manifest phase strings alone does not prove visual phase
equivalence. Tick 0 shows different stage framing and missing actors in the
Godot image; tick 13 shows both actors but HUD countdown 00 versus native 53.
These are observed residuals, not attributed exclusively to sampler math.

The first native attempt was rejected, not used: AVM1 signed hex serialization
produced invalid pixel words, and asynchronous quit allowed tick 61. Final probe
encodes opaque alpha explicitly and closes the observation window immediately
after the tick-60 `done` event while quit is pending. Nothing before `done` is
suppressed. Only the final fresh build/run is archived as accepted capture.

**Instrumentation timing limitation:** full pixel tracing slows native wall
clock substantially. The captured countdown visibly advances while display
frames are traced (tick 13 shows 53, tick 60 shows 10). External timers/random
inputs are not locked by this slice. The original tape and native outputs are
retained unchanged; no resimulation or reference correction conceals this.
Complete capture is not gameplay or pixel parity.

## Reproduce

```sh
python3 tools/probes/build_ai_reference.py --ffdec /tmp/bvn-loud-fail/r02/ffdec/ffdec.jar \
  --output /tmp/bvn-s31-bounded-build --run-id s31-didala-bounded-20261027 --frames 60 \
  --move-case /tmp/bvn-s28-campaign/cases/didala__attack__neutral__ground__near.json \
  --p1-character 迪达拉 --p2-character 一护 --p1-helper 我爱罗 --p2-helper 魂 --sampling-bitmap
python3 -m tools.sampling_native \
  --case /tmp/bvn-s28-campaign/cases/didala__attack__neutral__ground__near.json \
  --build /tmp/bvn-s31-bounded-build --trace /tmp/bvn-s31-bounded-capture.log \
  --receipt /tmp/bvn-s31-bounded-receipts/didala__attack__neutral__ground__near.json \
  --allow-window-activation --timeout 600
mkdir -p /tmp/bvn-s31-godot/frames
/tmp/bvn-loud-fail/r02/engine/Godot.app/Contents/MacOS/Godot \
  --path godot --rendering-method gl_compatibility --resolution 600x400 \
  --log-file /tmp/bvn-s31-godot/capture-engine.log \
  --script res://tests/move_case_reference.gd -- --bitmap-sequence \
  /tmp/bvn-s28-campaign/cases/didala__attack__neutral__ground__near.json /tmp/bvn-s31-godot/frames
python3 -m tools.sampling_bitmap \
  --case /tmp/bvn-s28-campaign/cases/didala__attack__neutral__ground__near.json \
  --receipt /tmp/bvn-s31-bounded-receipts/didala__attack__neutral__ground__near.json \
  --godot /tmp/bvn-s31-godot/frames --output /tmp/bvn-s31-comparison.json
```

Use new build paths/run ID for a new native capture. Archived revalidation needs
build archive restored under `/private/tmp`, raw trace decompressed to its bound
path, and original case/receipt paths restored as above. Receipt hashes are not
rewritten. `native-images.tar.gz` is derived solely from the archived trace;
`native-tick013.png` is a review preview, never a runtime texture. Python image
inspection uses the same installed Pillow tooling as existing render probes.

## Capture continuation and next thin slice

The original sandbox GUI attempt exited 134 without output. The user explicitly
approved this Godot screenshot command only. The first escalated launch reached
OpenGL but the engine log made the image directory nonempty; the existing
fresh-directory assertion correctly rejected it. That process was stopped;
images were then written to a fresh `frames/` subdirectory, leaving logs in the
parent. The second launch exited 0 with all 61 captures. No sandbox setting was
changed permanently; no runtime or probe code changed for this continuation.

`godot-capture.tar.gz` retains the original `frames/` directory including PNGs,
case-bound manifest and per-target state traces. Restore under
`/tmp/bvn-s31-godot` to rerun the comparison. The command log, image manifest,
negative proof and one paired preview are also archived. The native capture
and all existing reference bytes remain unchanged.

Establish external-clock/phase alignment
before interpreting differences as sampler defects. Full roster, transparent
alpha, BitmapData parity fixes, s30 source/mask gaps, DoAction and Jinye/Yijiao
residuals remain follow-ups. No production admission, merge, deployment or Worker.
