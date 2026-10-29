# s245 — Chad tick-10 call exit / receiver lifecycle

User-selected [s76 follow-up](../s76/README.md#residuals--next-thin-discriminator),
from master `0afcc200ca41f722de5cb475bb153f5a2674e43e` on
`feat/s245-chad-tick10-lifecycle`. Only the unchanged
`chad__attack__neutral__ground__near` s76 tape. No other residual or gameplay change.
`production_admitted=false`; `native_parity_proven=false`.

## Observed result

Native capture contains **9,486 events, 61 root samples and 122 actor states**.
Receipt revalidation exits **0**. The new exit-observation gate exits **1**;
the unchanged full call-site/AS gate also exits **1**.

| Boundary | Sequence / tick | Observation |
| --- | --- | --- |
| Caller before original `doAllAction()` | 7226 / 10 | `instance257`, parent frame 5, runtime depth -16353 occupied by the same receiver |
| Callee entry | 7227 / 10 | Same receiver, parent and depth occupant |
| Before original `_parent.gotoAndPlay("砍1")` | 7233 / 10 | Same receiver and occupied depth |
| Independent root sample | 7248 / 11 | Parent frame 183; depth occupant `undefined`; saved receiver string empty, its parent/frame `undefined`; occupant equality false |

There is **no `goto_after`, `callee_exit`, or `caller_after` observation**.
The old call-site invocation at sequence 7222 still ends at `call_before`.
This establishes receiver/depth loss between the observed goto front edge and
next root sample. It does **not** establish whether the VM aborted execution,
a return happened without an observable continuation, or another removed-target
execution rule suppressed the remaining sites. No missing return is synthesized.
The independent observer survives and emits at tick 11; absence of exit markers
must not be promoted into a proven return/nonreturn classification.

The unchanged call-site collector reports 442 complete invocations
(397 false / 45 true) and one incomplete invocation. Full AS coverage retains
594 unvisited and 415 uninstrumented items. The extra pre-fight false invocation
versus s76 is retained, not trimmed. All 122 fight-tick actor-state payloads match
the retained s76 capture exactly; this bounded native/native check is not a
Godot comparison or proof that instrumentation has no timing effects.

## Source and observation binding

- Caller: `scripts/fighter/chad.json` →
  `DefineSprite_607/frame_1/PlaceObject2_16_31/CLIPACTIONRECORD onClipEvent(enterFrame).as`.
  The original predicate is evaluated once and the original unqualified call stays intact.
- Callee: `DefineSprite_16/frame_1/DoAction.as::doAllAction(special)`.
  Its exact normalized source is hash-checked. The normal-hit branch contains
  the observed goto; the function has no explicit return. Added statements only
  report its entry, goto boundaries and fall-through exit.
- The source XML retained by s72 is hash-checked. Sprite 607 places Sprite 16
  at authored depth 31 on frame 1, removes that depth on frame 13, and labels
  frame 183 `砍1`. See `source-boundaries.json`. This is source timeline evidence,
  not a claim that jumping to 183 executes frame 13's scripts.
- `--chad-lifecycle` accepts only the exact s76 case and enables the existing
  call-site probe. The new observer stores the root, receiver, parent, path and
  depth outside the receiver in `_global`. Its armed flag is independent of
  the saved MovieClip reference, so an invalidated reference does not disable
  the tick-11 observation. It performs no gameplay writes, extra predicates,
  wrapper calls, unload handlers or substitute gotos.
- Only this one invocation's boundaries and the tick-11 root sample are collected.
  The global hook and source-bound builder are included in receipt probe hashes.
  Static-loader attestation remains limited (`runtime_fighter=null`).

## Gates and negative evidence

`gates.json` records actual commands, exits and measured durations. `lifecycle.json`
retains all four decoded observations and all three missing boundaries.
`callsite-summary.json` and `actions.json.gz` retain the existing AS obligations.
`negative-proof.json` removes each of the four actual lifecycle markers: native
sequence validation and the discriminator both reject; restoring the raw stream
revalidates the receipt while leaving the exit gate incomplete.

132 focused sampling/probe/import tests pass, including source-change rejection,
unchanged authored call/goto checks, wrong-case rejection, and actual-capture
missing/duplicate/wrong-identity negatives. Integrity, handoff and contract
checks are recorded alongside the evidence. M0-02 remains pending.

## Reproduction

Use a fresh build path and run ID for any new capture. Actual capture used r02;
r01 was an unrun development build, not a rejected or admitted capture.

```sh
python3 tools/probes/build_ai_reference.py \
  --ffdec /tmp/bvn-s66-tools/ffdec/ffdec.jar \
  --output /tmp/bvn-s245-build-r02 --run-id s245-chad-lifecycle-r02-20261029 \
  --frames 60 \
  --move-case evidence/sampling-upgrade/s76/chad__attack__neutral__ground__near.json \
  --p1-character 茶渡 --p2-character 一护 --p1-helper 我爱罗 --p2-helper 魂 \
  --chad-lifecycle
```

Capture calls `capture_native_player.capture(build, trace, 180, lock_timeout=45)`
with window activation authorized. It acquires the shared
`/tmp/bvn-native-flash-capture.lock` and releases it on return. Capture plus sealing
took 31.352 seconds. Exact launch and environment are in `capture-environment.json`.
The complete raw trace is retained without suffix trimming. There was one capture,
no rejected capture retry, and no concurrent player use by this slice.

Restore `native-build.tar.gz` inside `/tmp/bvn-s245-build-r02`, raw gzip trace to
`/tmp/bvn-s245-capture-r02/native.log`, and receipt to
`/tmp/bvn-s245-capture-r02/receipt.json`. Retain the original s76 case path and
this commit's probes at the receipt-recorded repository path. Do not rewrite hashes.

```sh
python3 -m tools.sampling_chad_lifecycle \
  --case evidence/sampling-upgrade/s76/chad__attack__neutral__ground__near.json \
  --receipt /tmp/bvn-s245-capture-r02/receipt.json --output /tmp/s245-lifecycle.json
# Exit 1: goto_after, callee_exit, caller_after remain unobserved.
python3 -m tools.sampling_callsite \
  --case evidence/sampling-upgrade/s76/chad__attack__neutral__ground__near.json \
  --receipt /tmp/bvn-s245-capture-r02/receipt.json --output /tmp/s245-actions.json
# Exit 1: incomplete selected call-site boundaries; full AS coverage also remains open.
python3 -m unittest tools.tests.test_chad_lifecycle_observer
python3 tools/verify.py
python3 tools/check_handoff.py
/tmp/bvn-s27-venv/bin/python tools/validate_contracts.py
```

Residuals: exact VM exit semantics, callee-body ownership beyond these sites,
other branches and Godot ownership remain unproven. Earlier display/mask,
clock/RGBA, and other-character residuals are untouched. No merge/deploy/Worker.
