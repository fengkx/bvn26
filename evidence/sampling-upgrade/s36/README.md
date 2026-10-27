# s36 — jump-cell global geometry observation

Base: `25496b09c9150bd7f1a3ca45ba0fe749db9ae4a2` (merged PR #58).
Branch: `feat/sampling-jump-geometry-one-cell`.
Exactly one cell: `didala__jump__neutral__ground__near`, unchanged s35 tape.
Evidence/docs only; the s29 geometry observer and gate are reused unchanged.

## Results

Real Flash capture: **6,271 events**, **61/61 root geometry samples**,
**242 hurt-box records**, **6 observed instance IDs**. Attack/helper-attack/stage-attack
arrays are explicitly empty in all samples; both fighters have hurt geometry.

Receipt revalidation and geometry gate pass. Removing all geometry events at
tick 10 rejects; removing one box while retaining its sample count rejects.
The unchanged capture rechecks. 50 focused tests and 19 probe tests pass;
integrity, handoff and contracts results are archived.

`geometry.json` preserves source script paths, instance IDs, source frames and
depths, concatenated global transforms, local bounds and global rectangle bounds
derived from all four corners without tolerance. Per-role empty arrays are
explicit. First/last observed ticks and first scripted initialization display
are retained. Both fighters' hurt candidates are required at every root sample.

## Scope and limits

The existing observer walks `_root.game` children and inspects source collision
lists (`_fsArray`, `_fzfsArray`, `stgks`) to include both fighters, helpers and
stage candidates, rather than only local boxes of the current fighter. Unknown
source candidates or missing source lists reject. See s29 for source mapping
and shared attack/hurt clip classification; no observer rule changes here.

These are present collision candidates at root observation boundaries, not a
claim that each can deal damage. Intra-frame transients, exact creation/removal,
AVM1 reference identity and arbitrary dynamic duplication remain unproven.
Observed lifetime endpoints are sampling bounds, not exact destruction events.
No Godot/native geometry comparison is performed. `production_admitted=false`
and `native_parity_proven=false`.

The existing static-loader attestation, input alias and random/timer limitations
remain. Capture metadata binds the actual fighter configuration; legacy boot
text is not the configuration authority. No runtime behavior, original source,
reference data or admission rule was changed.

## Reproduction and artifacts

```sh
python3 tools/probes/build_ai_reference.py --ffdec /tmp/bvn-loud-fail/r02/ffdec/ffdec.jar \
  --output /tmp/bvn-s36-build --run-id s36-didala-jump-20261027 --frames 60 \
  --move-case /tmp/bvn-s35-campaign/cases/didala__jump__neutral__ground__near.json \
  --p1-character 迪达拉 --p2-character 一护 --p1-helper 我爱罗 --p2-helper 魂 --sampling-geometry
python3 -m tools.sampling_native \
  --case /tmp/bvn-s35-campaign/cases/didala__jump__neutral__ground__near.json \
  --build /tmp/bvn-s36-build --trace /tmp/bvn-s36-capture.log \
  --receipt /tmp/bvn-s36-receipts/didala__jump__neutral__ground__near.json --allow-window-activation
python3 -m tools.sampling_geometry \
  --case /tmp/bvn-s35-campaign/cases/didala__jump__neutral__ground__near.json \
  --receipt /tmp/bvn-s36-receipts/didala__jump__neutral__ground__near.json \
  --output /tmp/bvn-s36-geometry.json
```

Fresh captures need fresh paths/run IDs. The archived receipt retains exact
case/build/trace/player paths and hashes. Restore its build archive under
`/private/tmp/bvn-s36-build`, decompress trace to `/private/tmp/bvn-s36-capture.log`
and restore the original case at its path above to revalidate using this commit's
probes and pinned player. Do not rewrite receipt paths/hashes. Build archive
contains only metadata, instrumentation diff and five SWFs; raw trace is
losslessly compressed. `artifact-sha256.json` binds evidence files.

Native capture-only escalation covered ps/player launch/owned cleanup, as
previously approved. Flash Debugger 32/Rosetta environment, executable/JPEXS
hashes and source/output hashes are retained in environment/build/receipt files.

## Follow-ups

This jump cell still lacks child display list/full camera, BitmapData and
DoAction/ownership observations. Native/Godot parity, full-roster observations,
nonempty helper/stage attack scenes and first-cell residuals remain separate
follow-ups. No first-cell rerun, merge, deployment or Worker change.
