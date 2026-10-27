# s32 — One-cell native DoAction entry coverage

Base `fee75ea2956f9c3be44e17f533b4b1997fff0887`; branch
`feat/sampling-doaction-one-cell`. Only the unchanged s28 case
`didala__attack__neutral__ground__near`. No gameplay/importer edits.
`production_admitted=false`; `native_parity_proven=false`.

## Results / review map

Real Flash capture: **6,165 events**, **61/61 root samples**, **394 block
entries**, **28 distinct source DoAction blocks** including startup. The fight
observation window contains **50 entries across 16 blocks**. Visited blocks are
12 Didala, 14 Yihu, one Kon and one Woailuo (startup included).

The source inventory was constructed before capture: **1,072 script items**
from the five loaded SWFs, **475 eligible non-main DoAction blocks** instrumented.
After capture, **447 eligible blocks remain unvisited** and **597 scripts remain
uninstrumented**. `doaction.json` preserves every entry in order and complete
visited/unvisited/uninstrumented lists with hashes and source locations.

Native receipt/structural collection passes. Full AS coverage CLI **exits 1**:
unvisited blocks, uninstrumented scripts and statement/call ownership are still
unproven. This intentionally incomplete gate does not become green just because
all observed entries are parseable. Missing receipt, source-obligation deletion,
missing entry/sample, changed source identity and unknown observations reject.
Real entry/sample deletion and inventory-deletion negatives reject, then the
original stream rechecks 61 samples / 394 entries.

**51 focused tests, 25 importer guard tests, 19 probe tests pass**, plus
integrity/handoff/contracts. Existing fail-loud importer rules are unchanged.

Review:
- `tools/probes/doaction_observer.py`: source inventory and entry-only injection.
- `build_ai_reference.py --sampling-doaction`: opt-in instrumented-copy builder;
  inventory is bound by the existing native receipt. New observer module is
  included in receipt probe hashes.
- `tools/sampling_doaction.py`: receipt and inventory revalidation, ordered event
  collection, explicit residual lists and rejecting full-coverage gate.
- `tools/tests/test_sampling_doaction.py`: six focused negative/positive tests,
  including preservation of an unsupported expression call in instrumentation.

## Expected versus executed — scope and limits

The 475-block inventory is a conservative **coverage target**, not an assertion
that every authored move or form is reachable in this one short cell. It is not
selected retrospectively from matching events. All 1,072 source script items
remain in the build inventory. Main SWF scripts are not instrumented in this
slice because the static capture bootstrap already replaces/rewrites root
startup. Other paths (including clip-action/function/button handlers) do not
fit the admitted top-level frame-block injection and remain explicit gaps.
These are coverage gaps, not harmless allowlists.

Identity binds source SWF SHA-256, unique exported script path, source text
SHA-256, sprite/frame and probe scope. Duplicate paths reject. Exported paths
are used as identities; a raw binary tag-offset/DoInitAction mapping is not
claimed. Instrumented copies use the established input/random observer builder;
its existing modifications remain visible in `instrumentation.diff`. Originals
under `game/` and `scripts/` are untouched.

Each entry records native sequence, display counter, current root-observer tick,
instance path and actual `_currentframe`. Source sprite/frame are separately
retained in the inventory. Actor callbacks can run before the next root
observer, so `observer_tick` is the observed counter, **not a fabricated
post-root phase assignment**. Startup entries have negative observer ticks.
Example fight entries include Didala sprite 542 frames 178 and 188 once each;
frame 1/2/11 and collision/helper block entries are also retained. An instance
path is not a stable lifetime ID or proof of AVM1 live-reference semantics.

**Entry into a block is not execution of every statement or function declared
inside it.** There is no call/branch/exit, clip-action or Godot-consumer ownership
proof. The full gate therefore always rejects this entry-only schema; there is
no accepted completion mode to falsely certify an unsupported call. Tests keep
`unsupportedCall(speed * 18)` in the injected source, show deleting it changes
identity and rejects the old observation, and show even a fully visited fixture
cannot pass statement/call ownership. This is not a replacement for the existing
compiler's unsupported-call guards and does not claim to audit arbitrary calls.

External timers/random alignment, instrumentation perturbation, dynamic loading
and static-loader attestation limitations from s28 remain. No inference of
native/Godot behavioral or pixel parity is made.

## Reproduction

```sh
python3 tools/probes/build_ai_reference.py --ffdec /tmp/bvn-loud-fail/r02/ffdec/ffdec.jar \
  --output /tmp/bvn-s32-build --run-id s32-didala-20261027 --frames 60 \
  --move-case /tmp/bvn-s28-campaign/cases/didala__attack__neutral__ground__near.json \
  --p1-character 迪达拉 --p2-character 一护 --p1-helper 我爱罗 --p2-helper 魂 --sampling-doaction
python3 -m tools.sampling_native \
  --case /tmp/bvn-s28-campaign/cases/didala__attack__neutral__ground__near.json \
  --build /tmp/bvn-s32-build --trace /tmp/bvn-s32-capture.log \
  --receipt /tmp/bvn-s32-receipts/didala__attack__neutral__ground__near.json --allow-window-activation
python3 -m tools.sampling_doaction \
  --case /tmp/bvn-s28-campaign/cases/didala__attack__neutral__ground__near.json \
  --receipt /tmp/bvn-s32-receipts/didala__attack__neutral__ground__near.json \
  --output /tmp/bvn-s32-doaction.json
# Expected exit 1: incomplete full AS coverage, with report retained.
```

For a new capture use fresh build paths/run ID. For archived revalidation,
restore build archive under `/private/tmp`, decompress raw trace to its bound
path, restore original case and receipt at the paths above, using this commit's
probe files. Receipt paths/hashes are not rewritten. Player and JPEXS hashes are
recorded in build/receipt. The previously approved Flash launch/cleanup
escalation scope was reused. No new visual captures or Godot runs were needed.

## Next thin slice

Select one actual observed callback and add source-bound statement/call execution
or clip-action entry identity without certifying untaken branches. Keep the full
unvisited/source gap lists. Full-roster DoAction, raw-tag mapping, Godot ownership,
s30 hierarchy gaps, s31 pixel differences/clock alignment and Jinye/Yijiao
residuals remain follow-ups. No merge, deployment or Worker changes.
