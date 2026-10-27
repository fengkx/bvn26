# s54 — ranged-cell native clip-action handler entries

Base: `ee273f56d732cafd4497706c175c72dd7a955f36` (merged PR #76).
Branch: `feat/sampling-ranged-clipaction-one-cell`.
Exactly `didala__ranged__neutral__ground__near`, unchanged s49 tape.
Evidence/docs only; unchanged s33 clip-action probe and strict collector.
`production_admitted=false`; `native_parity_proven=false`.

## Results and review map

Real Flash: **7,981 events**, **61/61 root samples**, **2,933 clip-action entries
across 12 source handlers**; **296 clip entries** occur at nonnegative fight
observer ticks. Frame-block observations: **371 entries across 36 blocks**.
Fixed inventory: **1,072 scripts**, **656 instrumented** (475 DoAction blocks +
181 clip handlers). **608 unvisited** (439 blocks + 169 handlers) and
**416 uninstrumented scripts** remain explicit.

Receipt and structural entry collection pass. Full AS ownership gate **exits 1**;
no claim that a handler entry proves its internal statements/calls/branches.
Deleting a real clip-entry event or root sample rejects, as does deleting clip
obligations from the pre-capture inventory. Original stream/receipt revalidate.
57 focused tests, 25 importer guard tests and 19 probe tests pass, with
integrity/handoff/contracts logs included.

`clipaction-summary.json` lists all actually observed handlers, source locations,
event types and startup/fight execution counts. `visited-summary.json` includes
both frame blocks and handlers. `doaction.json.gz` retains every ordered entry
and complete visited/unvisited/uninstrumented lists. `acceptance.json`,
`negative-proof.json` and `ownership-gate.txt` distinguish observation completeness
from full-ownership rejection. Build/trace/receipt archives are real evidence.

## Scope and limits

The observer executes inside the original native `load`/`enterFrame` handler.
Source identity binds SWF hash, exported script path/hash, containing sprite/frame,
PlaceObject path and event type. Runtime identity retains instance path, current
child frame, sequence/display counter and root-observer counter. Source frame
and runtime child frame are separate. No binary tag offsets or precise lifetime
are invented; instance paths do not prove AVM1 live-reference identity.

Inventory is fixed before capture from five loaded SWFs, not pruned based on
visited results. Unvisited blocks/handlers are conservative coverage targets,
not claims that every move is reachable in this cell. Other events, main-root
handlers, function bodies, calls, branches and exit paths remain explicit gaps,
not harmless exceptions. Existing compiler fail-loud guards are unchanged.
Unsupported wrappers, wrong source/event kinds and dropped obligations still
reject. The full ownership gate cannot become green merely from visited entries.

External clocks/random alignment, instrumentation timing and static-loader
attestation limitations remain. No native/Godot behavior or pixel parity follows
from this observation. No geometry or BitmapData rerun was needed.

## Reproduction

```sh
python3 tools/probes/build_ai_reference.py --ffdec /tmp/bvn-loud-fail/r02/ffdec/ffdec.jar \
  --output /tmp/bvn-s54-build --run-id s54-didala-ranged-20261027 --frames 60 \
  --move-case /tmp/bvn-s49-campaign/cases/didala__ranged__neutral__ground__near.json \
  --p1-character 迪达拉 --p2-character 一护 --p1-helper 我爱罗 --p2-helper 魂 --sampling-clipaction
python3 -m tools.sampling_native \
  --case /tmp/bvn-s49-campaign/cases/didala__ranged__neutral__ground__near.json \
  --build /tmp/bvn-s54-build --trace /tmp/bvn-s54-capture.log \
  --receipt /tmp/bvn-s54-receipts/didala__ranged__neutral__ground__near.json --allow-window-activation
python3 -m tools.sampling_doaction \
  --case /tmp/bvn-s49-campaign/cases/didala__ranged__neutral__ground__near.json \
  --receipt /tmp/bvn-s54-receipts/didala__ranged__neutral__ground__near.json \
  --output /tmp/bvn-s54-doaction.json
# Expected exit 1: full AS ownership incomplete; report retained.
```

Fresh captures require fresh paths/run IDs. Archived revalidation requires the
build restored at `/private/tmp/bvn-s54-build`, raw trace decompressed to its
recorded path, original case/receipt paths above, this commit's probes and pinned
player. Do not rewrite receipt hashes/paths. Build archive contains metadata,
instrumentation diff and five SWFs; trace/report are losslessly compressed.
Source/probe/tool/output hashes remain in build/receipt; artifact hashes bind
this folder. Approved capture-only escalation covers ps/player launch/owned
cleanup. Original game/scripts and runtime are unchanged.

## Follow-ups

Observe one source-bound internal call/branch for an actually invoked ranged-cell
handler in a later thin slice; entry is not full call ownership. Other event
kinds, main handlers, exact lifecycle/dynamic provenance, full-roster ownership,
s50 geometry source-list blocker, s51 display/mask gaps and s52 pixel/clock differences remain open. No other cell
rerun, merge, deployment or Worker change.
