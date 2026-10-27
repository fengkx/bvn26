# s34 — one native predicate and call site

Base: `25084d3ea7579ca98280dbfd82971c10e4b4f814` (PR #56 merged).
Cell: `didala__attack__neutral__ground__near`; no other cells run.
`production_admitted=false`, `native_parity_proven=false`.

## Result and review map

`callsite_observer.py` source-checks Didala's
`DefineSprite_542/frame_1/PlaceObject2_16_31/CLIPACTIONRECORD onClipEvent(enterFrame).as`.
It retains the original unqualified `gameRunning()` predicate (one evaluation)
and `doAllAction()` call, recording branch outcome and before/after boundaries.
`sampling_callsite.py` binds these observations to the existing native receipt,
source inventory, instance path and sequence. Other scripts retain s33 entry
instrumentation. No gameplay/compiler consumer changes or allowlists.

Real Flash capture: 10,497 events, 61 root samples. The selected handler has
454 complete invocations: 406 false branches and 48 true branches with paired
call boundaries. One additional true branch reaches `call_before` but has no
`call_after` or `end`: entry sequence 8180, observer tick 10, instance281.
The next selected entry is sequence 8450, tick 22, instance504.
This demonstrates a missing return boundary, **not** proof of why it is missing
or of instance lifetime/replacement semantics. We do not synthesize a return.

The selected boundary gate **exits 1**. Diagnostic collection retains the
incomplete invocation explicitly; it does not turn that rejection into success.
Full AS ownership also remains false: 616 unvisited and 416 uninstrumented source
items remain in `actions.json.gz`. Callee bodies, dynamic resolution, other
statements and branches, exits and Godot consumers are not certified.

`negative-proof.json` deletes each of six marker types from a complete real
native prefix and checks rejection; deleting an event also fails the global
sequence gate. The full unchanged trace remains rejected. Focused tests cover
wrong branches, duplicate/foreign markers, dropped/changed source obligations,
unsupported source edits, and retaining incomplete diagnostics without admission.
63 focused tests, 25 importer-guard tests and 19 probe tests pass. Integrity,
handoff and contracts logs accompany this evidence.

## Reproduce

```sh
python3 tools/probes/build_ai_reference.py --ffdec /tmp/bvn-loud-fail/r02/ffdec/ffdec.jar \
  --output /tmp/bvn-s34-build --run-id s34-didala-20261027 --frames 60 \
  --move-case /tmp/bvn-s28-campaign/cases/didala__attack__neutral__ground__near.json \
  --p1-character 迪达拉 --p2-character 一护 --p1-helper 我爱罗 --p2-helper 魂 --sampling-callsite
python3 -m tools.sampling_native \
  --case /tmp/bvn-s28-campaign/cases/didala__attack__neutral__ground__near.json \
  --build /tmp/bvn-s34-build --trace /tmp/bvn-s34-capture.log \
  --receipt /tmp/bvn-s34-receipts/didala__attack__neutral__ground__near.json --allow-window-activation
python3 -m tools.sampling_callsite \
  --case /tmp/bvn-s28-campaign/cases/didala__attack__neutral__ground__near.json \
  --receipt /tmp/bvn-s34-receipts/didala__attack__neutral__ground__near.json \
  --output /tmp/bvn-s34-actions.json
# Expected exit 1: incomplete selected call-site boundaries; report retained.
```

Archived build/receipt preserve hashes and paths, raw trace is losslessly gzipped.
Restore archives at the receipt's original paths using this commit's probes to
revalidate; do not rewrite receipts. New captures require fresh run IDs/paths.
`capture-environment.json` records Flash Player Debugger 32 environment; receipt
and build record source/probe/tool/output hashes. Approved native capture-only
escalation was used for ps/player launch/cleanup. No native pixels supplied as
textures, original game/scripts unchanged. Additional tracing changes timing;
no cross-run behavioral equality or native/Godot parity is asserted.

## Next thin discriminator / follow-ups

Inspect the source-bound `doAllAction` path reached at tick 10 and observe its
exit/lifecycle boundary to distinguish nonreturn from loss of the observation
receiver. Preserve this raw missing-return case as a negative; do not weaken
its gate. Full ownership, full-roster capture, native/Godot clock alignment,
BitmapData differences and remaining s30 hierarchy/mask gaps are follow-ups,
not prerequisites for this observation-only slice. No merge/deploy/Worker.
