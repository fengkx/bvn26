# s35 — second Deidara native sampling cell

Base: `831342e530d0b739b998f88408b950b11a5372f7` (merged PR #57).
Branch: `feat/sampling-second-cell-native`. Evidence/docs only; existing adapter,
probe, runtime and importer are unchanged.

## Result

Exactly one new cell: **`didala__jump__neutral__ground__near`**, 60 ticks.
The existing matrix generates jump intent at ticks 10,11,12. Real Flash capture
completed at tick 60: **5,926 events**, **122 actor observations** (both actors,
ticks 0–60). The existing adapter sealed and revalidated the case-bound receipt.
Source key-read validation passed (1,809 reads, one pressed jump read); intent
ticks independently match the original tape. This is observation completeness,
not proof of jump behavior or parity.

The existing Godot matrix run accepted required-native evidence for this cell:
**1/324 executed, no errors**. Missing receipt, wrong-cell receipt and deleted
native sample each reject; the original receipt revalidates unchanged. Unmarked
entries require no receipt. Full campaign check correctly exits 1 on missing
native evidence for the other cells. No other cell was executed or recaptured.

45 focused tests pass; integrity, handoff and contracts pass. Both
`production_admitted=false` and `native_parity_proven=false` remain unchanged.
`runtime-report.json` does not claim complete 324-case execution.

## Evidence and reproduction

Receipt/build bind source SWFs, input case, probe, player and output hashes.
`native-build.tar.gz` retains only build metadata, instrumentation diff and five
SWFs; raw native log and runtime traces are losslessly compressed. `matrix.json`
retains the generated campaign identity; only the selected case is captured.
`gate-proof.json` records negative checks and source input read verification.
`artifact-sha256.json` binds the archived files.

```sh
python3 -m tools.sampling_matrix generate --output /tmp/bvn-s35-campaign --fighters didala --require-native
python3 tools/probes/build_ai_reference.py --ffdec /tmp/bvn-loud-fail/r02/ffdec/ffdec.jar \
  --output /tmp/bvn-s35-build --run-id s35-didala-jump-20261027 --frames 60 \
  --move-case /tmp/bvn-s35-campaign/cases/didala__jump__neutral__ground__near.json \
  --p1-character 迪达拉 --p2-character 一护 --p1-helper 我爱罗 --p2-helper 魂
python3 -m tools.sampling_native \
  --case /tmp/bvn-s35-campaign/cases/didala__jump__neutral__ground__near.json \
  --build /tmp/bvn-s35-build --trace /tmp/bvn-s35-capture.log \
  --receipt /tmp/bvn-s35-receipts/didala__jump__neutral__ground__near.json --allow-window-activation
python3 -m tools.sampling_matrix run --campaign /tmp/bvn-s35-campaign \
  --output /tmp/bvn-s35-runtime --godot /tmp/bvn-loud-fail/r02/engine/Godot.app/Contents/MacOS/Godot \
  --cases didala__jump__neutral__ground__near --native-evidence /tmp/bvn-s35-receipts
python3 -m tools.sampling_matrix check --campaign /tmp/bvn-s35-campaign \
  --output /tmp/bvn-s35-runtime --native-evidence /tmp/bvn-s35-receipts
# Expected exit 1 for the full campaign: other required receipts are missing.
```

Fresh captures require fresh paths/run IDs. Revalidate this archived receipt by
restoring build/trace/case at its retained absolute paths, with this commit's
probes and pinned player present; do not edit receipt paths/hashes. Call
`tools.sampling_native.validate(case_path, receipt_path)` for revalidation.
Before capture finished, an attempted matrix run rejected missing native evidence;
the successful run above started only after receipt creation. No gate was softened.

Player/environment remain the s28 pinned Flash Player Debugger 32/Rosetta setup;
`capture-environment.json` records this run. The approved native-capture-only
escalation covered ps/player launch/cleanup. JPEXS/player hashes are in the build
and receipt. Static bootstrap text is not configuration authority: metadata/tape
bind Didala versus Yihu with P2 CPU disabled. `runtime_fighter=null` remains the
static-loader attestation limitation described in s28. No signatures or independent
loader attestation are claimed by these trusted-local-build receipts.

## Follow-ups

This second cell has no geometry, child-DL/camera, BitmapData, DoAction or internal
ownership stack yet. Native/Godot behavioral comparison and clock alignment remain
unproven. The first cell's s34 missing return boundary and other documented
residuals remain open. Additional cells and observation dimensions can be separate
thin slices; none are silently treated as covered here. No merge/deploy/Worker.
