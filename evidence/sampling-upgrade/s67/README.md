# s67 — summon-cell native DoAction entry coverage

Base: `f65c7676a3e2f0f2799998e62bcc774a91a6d426` (merged PR #89).
Branch: `feat/sampling-summon-doaction-one-cell`.
Exactly `didala__summon__neutral__ground__near`, unchanged s63 tape.
Evidence/docs only; s32 entry probe and current fail-loud collector unchanged.
`production_admitted=false`; `native_parity_proven=false`.

## Results / review map

Real Flash: **5,446 events**, **61/61 root samples**, **380 block entries**,
**32 distinct source blocks** including startup. Fight window: **42 entries
across 18 blocks**. Fixed inventory: **1,072 script items**, **475 instrumented
non-main DoAction blocks**. **443 eligible blocks remain unvisited; 597 scripts
remain uninstrumented**.

Receipt and structural entry collection pass. Full AS gate **exits 1**:
unvisited blocks, uninstrumented scripts and statement/call ownership remain
unproven. Removing one real entry or root sample rejects; deleting a source
inventory obligation rejects; original capture and receipt revalidate unchanged.
53 focused tests, 25 importer guard tests and 19 probe tests pass, along with
integrity/handoff/contracts.

`visited-summary.json` lists source paths/hashes, sprite/frame and execution
counts. `doaction.json.gz` retains every ordered entry plus complete visited,
unvisited and uninstrumented lists. `acceptance.json`, `negative-proof.json`
and `ownership-gate.txt` distinguish structural success from ownership rejection.
Native trace/build/receipt artifacts are real captures, not synthetic fixtures.

## Expected versus observed / limits

The source inventory is fixed before execution from the five loaded SWFs,
not selected retrospectively from observed events. Eligible DoAction blocks are
conservative coverage targets, not a claim that every move/form is reachable
in this short cell. Unvisited and uninstrumented lists are gaps, not allowlists.
Main-root startup is rewritten by the existing static bootstrap and is not
certified by this entry probe. Other script kinds remain explicit residuals.

Events retain sequence, display tick, root-observer counter, instance path and
actual current frame. Source frame/sprite are separately bound to original SWF
and script hashes. Startup entries have negative observer ticks; these are not
assigned invented post-root phases. Instance paths do not prove exact lifetimes
or AVM1 reference identity. Entry into a block does not prove its statements,
functions, branches, exits or Godot consumers executed. Full ownership always
rejects this entry-only schema, including fully visited fixtures in focused tests.
Existing compiler unsupported-call guards remain unchanged.

Static-loader attestation, input alias, external timers/random alignment and
instrumentation timing limitations remain. No native/Godot behavioral or pixel
parity is inferred. This cell's clip-action/call ownership is not deepened here.

## Reproduction

```sh
python3 tools/probes/build_ai_reference.py --ffdec /tmp/bvn-s66-tools/ffdec/ffdec.jar \
  --output /tmp/bvn-s67-build --run-id s67-didala-summon-20261028 --frames 60 \
  --move-case /tmp/bvn-s63-campaign/cases/didala__summon__neutral__ground__near.json \
  --p1-character 迪达拉 --p2-character 一护 --p1-helper 我爱罗 --p2-helper 魂 --sampling-doaction
python3 -m tools.sampling_native \
  --case /tmp/bvn-s63-campaign/cases/didala__summon__neutral__ground__near.json \
  --build /tmp/bvn-s67-build --trace /tmp/bvn-s67-capture.log \
  --receipt /tmp/bvn-s67-receipts/didala__summon__neutral__ground__near.json --allow-window-activation
python3 -m tools.sampling_doaction \
  --case /tmp/bvn-s63-campaign/cases/didala__summon__neutral__ground__near.json \
  --receipt /tmp/bvn-s67-receipts/didala__summon__neutral__ground__near.json \
  --output /tmp/bvn-s67-doaction.json
# Expected exit 1: incomplete full AS coverage; report retained.
```

Use fresh paths/run IDs for new captures. Archived revalidation requires build
restored at `/private/tmp/bvn-s67-build`, trace decompressed to its recorded path,
and original case/receipt paths above, with this commit's probes and pinned
player. Do not rewrite receipt paths/hashes. Build archive retains metadata,
instrumentation diff and five SWFs; trace/report are losslessly compressed.
Player/JPEXS/source/probe/output hashes are retained; artifact hashes bind this
folder. Previously authorized native-capture-only escalation covers ps/player
launch/owned cleanup. No Godot or image rerun is needed for this slice.

## Follow-ups

Observe one actually invoked summon-cell clip handler or call site in a separate
thin slice while retaining source gaps. Full-roster AS ownership, raw-tag
mapping, dynamic provenance, s64 unbound helper box, s65 display/mask gaps and s66 pixel/clock residuals
remain open. No other cell rerun, gameplay/importer change, merge/deploy/Worker.
