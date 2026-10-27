# s57 — special-cell global geometry observation

Base: `a50fb32995869e4555d499f6a5ddeb359385b53d` (merged PR #79).
Branch: `feat/sampling-special-geometry-one-cell`.
Exactly one cell: `didala__special__neutral__ground__near`, unchanged s56 tape.
Evidence/docs only; the s29 geometry observer and gate are reused unchanged.

## Results

Real Flash capture: **5,000 events**, **61/61 structurally collected samples**,
**177 hurt + 27 attack records**, **13 observed instance IDs**. Helper/stage attack
arrays are explicitly empty. Receipt revalidation and structural collection pass.

**Full geometry gate exits 1: missing p1 receiver at tick 11.** This is not a
complete geometry pass. Tick 10 contains p1 bdmn/mian, tick 11 contains only p2
bdmn/mian, and tick 12 contains both actors again. Native p1 state frame is
1/474/475 at these three observations. No missing receiver is fabricated or
allowlisted; absence alone does not establish invulnerability or probe correctness.

Removing tick-10 geometry events or one box rejects. Original structural samples
and receipt revalidate; original full gate still rejects. 50 focused tests and
19 probe tests pass; integrity/handoff/contracts results are archived.

`geometry-diagnostic.json` retains **all** samples, source paths, instance IDs,
source frames/depths, global matrices, local and derived global bounds, sampled
lifetimes and explicit per-role arrays. It is marked `full_geometry_complete=false`.
`missing-receivers.json`, `geometry-gate.txt` and `negative-proof.json` preserve
exact failure and rejecting checks. No successful full `geometry.json` is issued.

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
  --output /tmp/bvn-s57-build --run-id s57-didala-special-20261027 --frames 60 \
  --move-case /tmp/bvn-s56-campaign/cases/didala__special__neutral__ground__near.json \
  --p1-character 迪达拉 --p2-character 一护 --p1-helper 我爱罗 --p2-helper 魂 --sampling-geometry
python3 -m tools.sampling_native \
  --case /tmp/bvn-s56-campaign/cases/didala__special__neutral__ground__near.json \
  --build /tmp/bvn-s57-build --trace /tmp/bvn-s57-capture.log \
  --receipt /tmp/bvn-s57-receipts/didala__special__neutral__ground__near.json --allow-window-activation
python3 -m tools.sampling_geometry \
  --case /tmp/bvn-s56-campaign/cases/didala__special__neutral__ground__near.json \
  --receipt /tmp/bvn-s57-receipts/didala__special__neutral__ground__near.json \
  --output /tmp/bvn-s57-geometry.json
```

Fresh captures need fresh paths/run IDs. The archived receipt retains exact
case/build/trace/player paths and hashes. Restore its build archive under
`/private/tmp/bvn-s57-build`, decompress trace to `/private/tmp/bvn-s57-capture.log`
and restore the original case at its path above to revalidate using this commit's
probes and pinned player. Do not rewrite receipt paths/hashes. Build archive
contains only metadata, instrumentation diff and five SWFs; raw trace is
losslessly compressed. `artifact-sha256.json` binds evidence files.

Native capture-only escalation covered ps/player launch/owned cleanup, as
previously approved. Flash Debugger 32/Rosetta environment, executable/JPEXS
hashes and source/output hashes are retained in environment/build/receipt files.

## Follow-ups

First resolve tick 11 / p1 frame 474: compare authored placement/removal and
scripted initialization against the root-observer phase for bdmn/mian. Determine
whether this is source-authored absence or an observation gap before changing the
receiver obligation. Do not insert a default box, guess invulnerability or drop
this tick. The current full gate remains rejecting.


This special cell still lacks child display list/full camera, BitmapData and
DoAction/ownership observations. Native/Godot parity, full-roster observations,
nonempty helper/stage attack scenes and earlier-cell residuals remain separate
follow-ups. No first-cell rerun, merge, deployment or Worker change.
