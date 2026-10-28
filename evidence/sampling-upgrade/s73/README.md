# s73 — Chad attack-cell BitmapData and exact RGBA gate

Base: `dc65102881bcf93a1a2a11d0030d8d96d9fa5903` (merged PR #95).
Branch: `feat/sampling-chad-bitmap-one-cell`.
Exactly `chad__attack__neutral__ground__near`, unchanged s70 input tape.
Evidence/docs only: s31 native BitmapData, Godot capture and byte gate unchanged.
`production_admitted=false`; `native_parity_proven=false`.

## Results

Real native capture: **29,564 events**, **61/61 images**. Real Godot capture:
**61/61 images**, exit 0. Each capture has 58,560,000 RGBA bytes at 600×400,
all alpha 255; receipt and image manifests revalidate. Strict comparison
**exits 1: 0/61 exact frames**, **17,616,253 differing channels**, **6,832,516
differing pixels**, maximum channel delta **255**.

Removing a native frame or row rejects; removing Godot image 010 rejects.
Original bytes are restored and all images/receipt revalidate. A one-channel
mutation is also detected without tolerance. 63 focused tests and 19 probe tests
pass, with integrity/handoff/contracts logs included.

Review `acceptance.json`, `comparison.json` and `negative-proof.json` for exact
counts, every frame's first differing coordinate/bytes, and rejecting checks.
Archives retain actual native/Godot images, not fixture substitutes. Original
SWF/script inputs, runtime and reference bytes are unchanged.

## Observation contract and residuals

The unchanged native probe synchronously draws `_root` at its root observer to
opaque-black 600×400 BitmapData. ARGB words are losslessly decoded into RGBA8;
all alpha bytes must be 255. The Godot runner uses the same case, replays from
fresh actors for each target tick, stops at its terminal root observer boundary,
settles drawing and captures the actual root viewport. PNGs are decoded to bytes;
no resize, alignment, cropping, gamma correction or channel tolerance is applied.
Source reference pixels are never uploaded as runtime textures.

Matching phase labels do not prove native/Godot phase equivalence. Synchronous
pixel tracing affects native wall-clock timers; clocks/random inputs are not
fully locked. Framebuffer composition, scene framing and rendering/state phase
may contribute to the measured differences. This slice does not attribute them
to sampler math or fix them by rewriting references. Transparent destinations,
complete geometry/child display ownership and exact gameplay parity remain
unproven. Pixel images cannot prove individual display-node ownership; s72's
167 source-frame/effect-symbol obligations and dynamic-mask gap remain open.

## Reproduction

```sh
python3 tools/probes/build_ai_reference.py --ffdec /tmp/bvn-s66-tools/ffdec/ffdec.jar \
  --output /tmp/bvn-s73-build --run-id s73-chad-attack-20261028 --frames 60 \
  --move-case /tmp/bvn-s70-campaign/cases/chad__attack__neutral__ground__near.json \
  --p1-character 茶渡 --p2-character 一护 --p1-helper 我爱罗 --p2-helper 魂 --sampling-bitmap
python3 -m tools.sampling_native \
  --case /tmp/bvn-s70-campaign/cases/chad__attack__neutral__ground__near.json \
  --build /tmp/bvn-s73-build --trace /tmp/bvn-s73-capture.log \
  --receipt /tmp/bvn-s73-receipts/chad__attack__neutral__ground__near.json \
  --allow-window-activation --timeout 600
mkdir -p /tmp/bvn-s73-godot/frames
/tmp/bvn-s66-tools/engine/Godot.app/Contents/MacOS/Godot \
  --path godot --rendering-method gl_compatibility --resolution 600x400 \
  --log-file /tmp/bvn-s73-godot/capture-engine.log \
  --script res://tests/move_case_reference.gd -- --bitmap-sequence \
  /tmp/bvn-s70-campaign/cases/chad__attack__neutral__ground__near.json /tmp/bvn-s73-godot/frames
python3 -m tools.sampling_bitmap \
  --case /tmp/bvn-s70-campaign/cases/chad__attack__neutral__ground__near.json \
  --receipt /tmp/bvn-s73-receipts/chad__attack__neutral__ground__near.json \
  --godot /tmp/bvn-s73-godot/frames --output evidence/sampling-upgrade/s73/comparison.json
# Expected exit 1 for measured channel differences.
```

Fresh captures require fresh paths/run IDs. Restore archived native build at
`/private/tmp/bvn-s73-build`, trace at `/private/tmp/bvn-s73-capture.log`, original
case/receipt at recorded paths, and Godot `frames/` under `/tmp/bvn-s73-godot`
for revalidation using this commit's probes and pinned engines. Do not rewrite
hashes or paths. Native image archive is derived solely from retained raw trace;
paired tick-13 PNGs are review previews, never game assets. `artifact-sha256.json`
binds evidence; native receipt and Godot manifest bind case/probe/engine/images.

Native Flash process and Godot screenshot commands were separately approved
through command-only escalation. No permanent sandbox settings changed.
Flash Debugger 32/Rosetta and Godot environment details/hashes remain in the
capture logs, build and receipts. Static-loader attestation limitations remain
as in s28/s35; original metadata/tape is configuration authority.

## Follow-ups

Establish external-clock/render-phase alignment before interpreting residuals
as individual rendering defects. This Chad attack cell's DoAction/ownership evidence
is a separate thin slice. Full-roster capture, pixel-parity fixes, transparent
alpha and other known residuals are not required for this observation gate.
No other cell rerun, merge, deployment or Worker change.
