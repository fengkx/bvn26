# s282 — Post-s281 rerank and ones target-entry observability

Base: master `f66987b3abf2ff329149f75a76a8911dbf8aae31` / #159.
Branch: `feat/s282-post-s281-rerank`. Exclusive authority:
[AFTER-s281 rank 1](../next-fix-priority-after-s281.md).
Ranks 2+ are planning only. `production_admitted=false`;
`native_parity_proven=false`; M0-02 pending; zero product obligations closed.

**Evidence-only: the per-target observation gap is measured; an independent
child clock is not proved.** No runtime implementation or new capture is claimed.

## What rank 1 delivered

The new ranking reviews s273–s281 at the current master, with hashed review
inputs in [ranking-basis-sha256.json](ranking-basis-sha256.json). It prioritizes
the new s274 same-run lifetime evidence ahead of source-only external collision
work; classified s228 completion moves ahead of blocked UI/debugger facilities.
Old deliveries are not reopened as blanket work.

[diagnose.py](diagnose.py) revalidates all **26,828 s274 events**, original receipt
raw hash, archived outputs/instrumentation and source hashes through unchanged
s274 validation, and checks that its full result equals the locked diagnosis.
The new audit binds the complete ten-frame Sprite1810 source/timeline to the
archived frame1 entry patch, then enumerates **all 63 callback windows**, including
pre-fight callbacks. Each window starts after the callback's synchronous state
read and ends before the next callback begins (or at trace end). Sequence
bracketing is observed order, not wall-clock delay or a causal execution model.
No callback tape or evidence from s262 is transplanted into this capture.

| Target frame | Callback selections | Windows with independent entry event | Authored script / archived hook |
| --- | ---: | ---: | --- |
| 1 | 18 | 4 | `stop();` / s274 entry hook |
| 2–10 (each frame) | 5 each | 0 each | No DoAction / no target-entry patch |

The **45 uninstrumented target windows** cannot be filled by `fire_after`,
`_currentframe`, draw-before/after equality or a retained load generation.
The 14 remaining frame1 windows are callbacks1–14 at pre-fight tick -1;
there is no entry event in those windows. This is not a claim that a repeated
same-frame goto must execute a script, nor evidence of nonexecution. Their
`independent_target_entry_observed` remains null. The initial load/frame1 entry
is reported separately, never counted as a callback-selected reentry.

Callbacks24/34/44/54 select frame1 at ticks16/26/36/47; independent entries
appear at ticks17/27/37/48 (sequences23122/23768/24627/25684), after encoding
and before the next callback. These are the four s274 natural joins, now placed
in the denominator of all target selections. The audit does not infer missing
entry events, force a goto, interpolate a child clock or treat generation1 as
native allocation identity. Per-frame glyph IDs1800–1809 and depth1 replacement
MOVE flags are retained in [diagnosis.json](diagnosis.json); those child glyph
placements must not be confused with the new outer ones placement at depth3.

## Source-first boundary and next experiment

1. `scripts/main.json#DefineSprite_1810/frame_1/DoAction.as` contains `stop()`;
   frames2–10 have no authored scripts. s262/source-contract.json retains the
   ten frame changes and Sprite1813 timer callback source. The s274 archive
   has one digit patch, at frame1. This is a source/archive hook inventory,
   not a fresh independent decompilation or native instruction trace.
2. Sprite1813 frame1 places ones Sprite1810 at depth3, new, not MOVE; its frame10
   removes it. Inside the digit, frame1 places glyph1800 at depth1 and frames2–10
   MOVE/replace that glyph. Outer load counters do not observe all inner changes.
3. The callback uses `gotoAndStop`; frame1 stops. Empty target scripts do not
   authorize inventing a stop action, return, auto-advance or frame-entry event.
4. Tests reject source/placement/hook mutations, mixed runs, missing callbacks
   and wrong generations. They enforce source and observation boundaries, not
   a proposed runtime schedule. Missing observations stay null.
5. s274 supplies original-player evidence of the same retained input only.
   No new Godot comparison or independent all-frame clock observation exists.
   The source-first gate therefore permits no runtime change or completion claim.

The next rank-1 discriminator requires a **fresh, independently identified**
ones-only capture with qualified target-entry observations for all ten frames.
Adding DoAction to originally empty frames is itself an instrumentation change:
first audit the complete decoded source/opcode/timeline deltas and preserve all
original actions and evaluation order. Calibrate retained repeated-target,
changed-target and same-depth replacement controls separately; distinguish
callback selection, actual entry and next callback/root order. Keep the natural
ones untouched by control gotos. Compare instrumented/uninstrumented controls
for observable perturbation; source inversion alone cannot prove timing.
If hooks cannot observe empty-frame entry without changing its behavior, report
that facility gap rather than synthesizing a clock. Native allocation identity
remains a separate requirement. Preserve complete streams, fresh run IDs,
receipts and costs. Registration/intro/scene join and images are outside s282.

No new build or capture was made: locked evidence can determine observation
coverage but cannot manufacture absent events. Repeating an unchanged capture
would not qualify missing hooks. Future capture cost is unknown. Actual elapsed
session and gate timings are recorded; person-days are not inferred.

## Reproduction and scope

```sh
PYTHONPATH=. python3 evidence/sampling-upgrade/s282/diagnose.py --output /tmp/s282.json
PYTHONPATH=. python3 evidence/sampling-upgrade/s282/diagnose.py --output /tmp/s282-required.json --require-child-clock # exit 1
PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s282 -p 'test_*.py'
python3 tools/verify.py
python3 tools/check_handoff.py
```

[gates.json](gates.json) records focused/retained tests, diagnosis and negative
child-clock, historical state-admission and strict-RGBA gates. Historical RGBA
remains 0/61; its replay is a regression check, not execution of rank9.
[Project checks](project-checks.json) record integrity/handoff.
No contract/runtime change requires Godot or contract migration checks.

Only s282, the new ranking and requested tracking files change. s254–s281,
original game/scripts, runtime/contracts, shared sampler/validator/threshold,
baselines, historical receipts and tapes are unchanged. No ranks2+ implementation,
production admission, merge or deployment.
