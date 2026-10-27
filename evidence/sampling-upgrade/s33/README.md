# s33 — One-cell native clip-action handler entry coverage

Base `16e0c8eb5f809146b4352d246bdda9b0a510091b`; branch
`feat/sampling-clipaction-one-cell`. Same unchanged case
`didala__attack__neutral__ground__near`. No gameplay/importer changes and no
new geometry, pixels or full-roster campaign.
`production_admitted=false`; `native_parity_proven=false`.

## Results

Real Flash capture: **9,464 events**, **61/61 root samples**, **3,138 clip-action
entries across 12 source handlers**. **347 clip entries** occur at nonnegative
fight observer ticks. Both `load` and `enterFrame` are actually observed; the two
outer fighter `load` handlers occur during startup. The accompanying s32
DoAction observer records 403 entries across 28 blocks.

Pre-capture inventory: **1,072 source script items**, **656 instrumented**
(475 DoAction blocks + 181 clip-action handlers). Visited: 28 blocks + 12 handlers.
Remaining: **616 unvisited** (447 blocks + 169 handlers), **416 uninstrumented**.
The native receipt and structural entry capture pass. The **full AS ownership
gate exits 1**, retaining every residual and explicitly denying statement/call
ownership. The larger unvisited count versus s32 comes from expanding the
inventory, not deleting previously observed obligations.

Real missing clip-event / root-sample mutations and removal of clip obligations
from the build inventory all reject; original stream rechecks 61 samples and
3,138 clip entries. Tests also reject wrong event kind, mismatched handler
wrapper, source-call deletion, and a stream containing DoAction entries but no
clip observations. **57 focused tests, 25 importer guard tests, 19 probe tests**
pass; integrity/handoff/contracts pass.

## Review map

- `tools/probes/doaction_observer.py`: extend the existing source inventory with
  exact exported PlaceObject path and `load`/`enterFrame` event identity. Insert
  the observer inside the matched handler opening brace, preserving its body.
  A mismatched/unsupported source wrapper raises at build time.
- `build_ai_reference.py --sampling-clipaction`: opt in to both s32 block and new
  handler entry observations; default s32 mode remains unchanged.
- `tools/sampling_doaction.py`: regenerate the source inventory, validate event
  kind against its source record, preserve ordering and reject missing clip
  observations. Existing case-bound receipt revalidation remains mandatory.
- `tools/tests/test_sampling_clipaction.py`: six focused regressions.
- `clipaction-summary.json`: small human-readable list of all 12 observed
  handlers and startup/fight counts. `actions.json.gz` retains the full event
  stream plus visited/unvisited/uninstrumented obligations without dropping any.
  `native-build.json` retains the pre-capture inventory; archive is reproduction
  material, not product source.

## What is and is not proved

Unlike a DoAction block containing a function declaration, the new marker runs
**inside the native clip-event handler when invoked**. Each record binds original
SWF hash, exported script path/hash, containing sprite/frame, PlaceObject path,
and authored event name. Runtime records retain instance path, current child
frame, event order/display counter and current root-observer counter. The source
containing frame and runtime child frame are distinct; placement path tokens
are preserved without inventing a binary tag index.

For example, Didala outer `frame_1/PlaceObject2_542_1` has one startup `load`
entry and 574 `enterFrame` entries (60 during fight observer ticks). Didala
sprite 542/frame 182/PlaceObject2_16_36 has five fight `enterFrame` entries.
Both opponent receiver/controller and player controller handlers are captured;
this is not a player-only local scan.

The conservative coverage target is fixed before capture; unvisited handlers
are not claimed reachable in this short cell. Main SWF scripts remain outside
instrumentation because the existing static bootstrap rewrites startup. Only
non-main `load`/`enterFrame` wrappers are admitted here; other event types and
nonmatching script paths remain listed, not silently ignored or allowlisted.
All source scripts remain in the inventory, including uninstrumented ones.

**Handler entry is not proof of every call or taken branch within its body.**
Tests retain `unsupportedCall(speed*18)` in the source, reject its removal via
identity mismatch, and continue to reject full ownership even if that fixture's
handler was entered. No fake compiler consumer or call allowlist is introduced.
Exit/return paths, statement/call ownership, key/button/unload events, main-root
handlers, raw binary tag offsets and dynamic attachments remain unproven.
Instance paths do not prove lifetimes or AVM1 reference identity. Actor handlers
can precede the next root observer; `observer_tick` is the native counter as
observed, not an inferred phase. Startup entries retain negative counters.

Existing input/random instrumentation and static-loader limitations remain
visible in the build diff/receipt. The event counts differ from s32 because
this is a fresh native run with additional tracing; no cross-run timing or
behavioral equality is claimed. External-clock alignment remains separate.
Original `game/` and `scripts/` files are untouched.

## Reproduction

```sh
python3 tools/probes/build_ai_reference.py --ffdec /tmp/bvn-loud-fail/r02/ffdec/ffdec.jar \
  --output /tmp/bvn-s33-build --run-id s33-didala-20261027 --frames 60 \
  --move-case /tmp/bvn-s28-campaign/cases/didala__attack__neutral__ground__near.json \
  --p1-character 迪达拉 --p2-character 一护 --p1-helper 我爱罗 --p2-helper 魂 --sampling-clipaction
python3 -m tools.sampling_native \
  --case /tmp/bvn-s28-campaign/cases/didala__attack__neutral__ground__near.json \
  --build /tmp/bvn-s33-build --trace /tmp/bvn-s33-capture.log \
  --receipt /tmp/bvn-s33-receipts/didala__attack__neutral__ground__near.json --allow-window-activation
python3 -m tools.sampling_doaction \
  --case /tmp/bvn-s28-campaign/cases/didala__attack__neutral__ground__near.json \
  --receipt /tmp/bvn-s33-receipts/didala__attack__neutral__ground__near.json \
  --output /tmp/bvn-s33-actions.json
# Expected exit 1: full statement/call ownership remains incomplete.
```

New capture needs fresh build path/run ID. Archived receipt revalidation requires
the build restored under `/private/tmp`, decompressed capture at its bound path,
and original case/receipt paths above, using this commit's probes. Never rewrite
receipt hashes/paths. Flash/JPEXS hashes and source/output hashes are retained;
the previously approved native ps/launch/cleanup escalation scope was reused.

## Next thin slice

Select one of these actually invoked handlers and witness a specific nested
call/branch using source-bound sites. Preserve all residual lists instead of
certifying the whole handler. Full-roster ownership, remaining clip event types,
s30 hierarchy/masks and s31 pixels/clock alignment stay follow-ups. Geometry
from s29 is not repeated. No merge, deployment or Worker changes.
