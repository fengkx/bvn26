# s28 — One real native Deidara sampling cell

Base: `4eda37f00879dc6b05913e6a68fb2bb55f26c973` (merged PR #50).
Branch: `feat/sampling-native-one-cell`. No adapter/runtime/importer changes.

## Result

Exactly one cell: `didala__attack__neutral__ground__near` (60 ticks).
Real Adobe Flash Player Debugger 32 capture: **5,572 events**, **122 actor
observations** (both actors at ticks 0–60), completed at tick 60. The existing
adapter sealed and revalidated its case-bound receipt. The same tape ran in
Godot with `--native-evidence`: **1/324 executed**, no execution errors.

Missing and wrong-case receipts reject; restored bytes revalidate. Unmarked
entries need no receipt. Full-campaign `check` correctly rejects the other 323
missing native receipts. No previously proven fighters were rerun.
`gate-proof.json` also records source key-read validation and independently
checks that recorded attack intent is true at ticks **10,11,12**, matching tape.

**45 focused tests**, integrity, handoff and contracts pass. This establishes
capture/receipt plumbing and execution completeness for one cell, not native
behavior or pixel parity. No state-by-state parity comparison was performed.
`production_admitted=false`; `native_parity_proven=false`.

## Artifacts and environment

- `native-receipt.json`: original receipt, absolute case/build/trace/engine paths
  and hashes, plus all source/probe/build artifact bindings.
- `native-build.tar.gz`: only build.json, instrumentation.diff and the five
  receipt-bound instrumented SWFs. No Flash executable, music, exports or caches.
- `native-capture.log.gz`: original captured log, losslessly compressed.
- `runtime-report.json`, compressed runtime state/presentation and original case.
- `gate-proof.json`, `full-campaign-negative.txt`, test and verification logs.
- `acceptance.json`: counts and executable/JPEXS hashes.

Player: Adobe Flash Player Debugger 32.0.0.465, x86_64/Rosetta, windowed
LaunchServices. Executable SHA-256 matches the pinned reference environment:
`8d4c1f5934adae809b5f4ce4f6ca7c64d4260df46bb3eb9c41fe32be2ee905be`.
This run used JPEXS jar hash
`090ab695053ad94cba6408574c7d7eea20ec60b6ae789ee6056a23f45106762f`, recorded in
build metadata (not the older jar hash in reference-environment.md).
Godot: 4.7.2.stable.official.ed1daf0bf. Source files were unchanged.
The static bootstrap's legacy boot text says `vs_com,minren,yihu,AI=5`; it is not
the configuration authority. Build configuration and source hashes bind Didala
versus Yihu in mode 3 with P2 CPU disabled. Capture reported runtime_fighter=null
because the existing path resolver checks dynamic fixtures only. This slice
uses the trusted static builder; it does not add loader attestation.

The initial sandbox attempt failed before launch (`ps` denied). The user then
explicitly authorized elevation for this capture's process query/launch/cleanup
only. Capture completed and its owned process cleanup returned successfully.

## Commands used

```sh
python3 -m tools.sampling_matrix generate --output /tmp/bvn-s28-campaign --fighters didala --require-native
python3 tools/probes/build_ai_reference.py --ffdec /tmp/bvn-loud-fail/r02/ffdec/ffdec.jar \
  --output /tmp/bvn-s28-build --run-id s28-didala-20261027 --frames 60 \
  --move-case /tmp/bvn-s28-campaign/cases/didala__attack__neutral__ground__near.json \
  --p1-character 迪达拉 --p2-character 一护 --p1-helper 我爱罗 --p2-helper 魂
python3 -m tools.sampling_native \
  --case /tmp/bvn-s28-campaign/cases/didala__attack__neutral__ground__near.json \
  --build /tmp/bvn-s28-build --trace /tmp/bvn-s28-capture.log \
  --receipt /tmp/bvn-s28-receipts/didala__attack__neutral__ground__near.json \
  --allow-window-activation
python3 -m tools.sampling_matrix run --campaign /tmp/bvn-s28-campaign \
  --output /tmp/bvn-s28-runtime \
  --godot /tmp/bvn-loud-fail/r02/engine/Godot.app/Contents/MacOS/Godot \
  --cases didala__attack__neutral__ground__near --native-evidence /tmp/bvn-s28-receipts
```

A new capture needs fresh build/output paths and a unique run ID. Archived receipt
validation uses retained absolute paths. If those scratch files are missing,
restore the archive under `/private/tmp`, decompress native-capture.log.gz to
`/private/tmp/bvn-s28-capture.log`, and restore the case under
`/private/tmp/bvn-s28-campaign/cases/` with its original filename. Do not overwrite
an existing run. With the pinned player and this worktree path present:

```python
from pathlib import Path
from tools.sampling_native import validate
print(validate(
    Path('/tmp/bvn-s28-campaign/cases/didala__attack__neutral__ground__near.json'),
    Path('evidence/sampling-upgrade/s28/native-receipt.json')))
```

No references are rewritten for portability. A different path/version requires
a new capture/receipt, not editing this receipt to pass.

## Follow-ups

Native parity/random-timer alignment, BitmapData, hitboxes, child display lists,
full camera and DoAction remain open, as do Jinye/Yijiao residuals. Receipts are
trusted-local-build audit records, not signatures. Dynamic fixtures/post-done
tails remain outside this adapter. No full roster native run is required for
this evidence slice. No merge, deployment, Worker change or new character port.
