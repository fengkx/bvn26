# s55 — ranged-cell native branch and call-site observations

Base `7c6fe8e519f97ba7b801321dcf1aacb631d8d880` (merged PR #77).
Branch `feat/sampling-ranged-callsite-one-cell`. Exactly
`didala__ranged__neutral__ground__near`, unchanged s49 tape.
Evidence/docs only; s34 probe/collector unchanged.
`production_admitted=false`; `native_parity_proven=false`.

## Results

Real Flash capture: **9,130 events**, **61/61 root samples**.
Selected handler: Didala `DefineSprite_542/frame_1/PlaceObject2_16_31/CLIPACTIONRECORD onClipEvent(enterFrame).as`.
The original `gameRunning()` predicate is evaluated once; its true branch retains
original unqualified `doAllAction()` and observes before/after boundaries.
**417 complete invocations: 396 false, 21 true with paired calls**.

One additional true invocation at tick 10 (entry sequence 7987,
`_level0.game.p1.mc.instance275`) reaches `call_before` but has no `call_after`
or `end`. **Selected-boundary gate exits 1**. We retain this invocation without
inventing a return or claiming why the observation ends. Both branch outcomes
are observed, not every internal branch of either callee.

Full AS ownership remains false: **608 unvisited and 416 uninstrumented source
items** are retained. Callee bodies, other statements, dynamic dispatch, exits
and Godot consumers remain unproven. This is real call-site evidence with an
honest incomplete gate, not full call ownership.

## Validation and review map

- `callsite-summary.json`: source identity, counts and incomplete invocation.
- `actions.json.gz`: every observed entry/invocation and all residual source lists.
- `negative-proof.json`: remove each of six phase markers from actual complete
  invocations and reject. This selected-event subset tests marker grammar only;
  global ordering is independently checked on the full raw stream, where deleting
  a call-site event or root sample rejects. Deleting a source obligation rejects.
  Original diagnostic report and receipt revalidate unchanged. No incomplete
  invocation is removed from the full report or admitted by these local tests.
- 63 focused tests, 25 importer guard tests and 19 probe tests pass; integrity,
  handoff and contracts logs included.

Source selection is exact and hash-bound, not based on matching RGB or inferred
behavior. Unknown source edits and malformed markers remain rejected by existing
code. No gameplay/importer changes, allowlists or reference rewrites.

## Reproduction

```sh
python3 tools/probes/build_ai_reference.py --ffdec /tmp/bvn-loud-fail/r02/ffdec/ffdec.jar \
  --output /tmp/bvn-s55-build --run-id s55-didala-ranged-20261027 --frames 60 \
  --move-case /tmp/bvn-s49-campaign/cases/didala__ranged__neutral__ground__near.json \
  --p1-character 迪达拉 --p2-character 一护 --p1-helper 我爱罗 --p2-helper 魂 --sampling-callsite
python3 -m tools.sampling_native \
  --case /tmp/bvn-s49-campaign/cases/didala__ranged__neutral__ground__near.json \
  --build /tmp/bvn-s55-build --trace /tmp/bvn-s55-capture.log \
  --receipt /tmp/bvn-s55-receipts/didala__ranged__neutral__ground__near.json --allow-window-activation
python3 -m tools.sampling_callsite \
  --case /tmp/bvn-s49-campaign/cases/didala__ranged__neutral__ground__near.json \
  --receipt /tmp/bvn-s55-receipts/didala__ranged__neutral__ground__near.json \
  --output /tmp/bvn-s55-actions.json
# Expected exit 1: incomplete selected call-site boundaries; report retained.
```

Fresh captures require fresh paths/run IDs. Restore build under
`/private/tmp/bvn-s55-build`, trace at its original recorded path, and original
case/receipt at paths above for archived revalidation using this commit's probes
and pinned player. Never edit receipt hashes/paths. Trace/report are losslessly
compressed; build archive retains metadata/diff and five SWFs. Source, probe,
engine and output hashes are retained; artifact hashes bind this evidence folder.
Approved native capture-only escalation covers ps/player launch/owned cleanup.

## Residuals / next thin discriminator

Observe the tick-10 doAllAction exit/lifecycle boundary to distinguish nonreturn
from loss of the observer receiver. Do not silently accept the missing return.
External clocks, tracing perturbation, static-loader attestation and AVM1 live
reference semantics remain unproven. Full AS ownership, other cells, s50 geometry source-list blocker, s51 mask/source gaps and s52 pixel/phase residuals remain follow-ups. No geometry/image
rerun, full-roster expansion, merge/deploy/Worker.
