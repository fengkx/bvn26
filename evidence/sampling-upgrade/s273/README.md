# s273 — External body-push callsite at the initialization boundary

Base: master `68136e5efd64160e7a2bd94a8b57ef4abf4f566f` / #150.
Branch: `feat/s273-after-s272-rerank`. Authority:
[AFTER-s272 rank 1 only](../next-fix-priority-after-s272.md).
Ranks 2+ are planning only. `production_admitted=false`;
`native_parity_proven=false`; `eligibility_fix_proved=false`;
`external_callsite_execution_proved=false`; M0-02 pending.
Zero product obligations closed. This is an evidence-only diagnosis.

## New bounded finding

s264's body-entry observations do not cover this external collision site:
`scripts/fighter/yihu.json#DefineSprite_638/frame_1/DoAction.as::on_enterframe`.
The base P2 body callback uses **its own bdmn as receiver**, and the opponent's
`mc.bdmn` as the argument to native `hitTest`. P1's custom `getHitObj/checkHit`
functions are not on this call path. Their uninitialized state therefore cannot
by itself establish that P1's new clip cannot participate in any collision query.
This is a source-level distinction, not proof that this call ran in the gap.

The [diagnosis](diagnosis.json) adds a source/build/observation join for this
single site, rather than another full collision inventory:

- The wrapper frame1 places base body Sprite638 at depth1, new PlaceObject,
  and its authored enterFrame calls `on_enterframe()`.
- The entire selected function in the s264 build archive equals original source.
  There is no callsite observation in that function. The new report preserves
  its complete source, line number, operands and short-circuit expressions.
- Early `dashing` and pause returns precede the query. `doDashX()` runs before
  the displacement computation; both actors' `airBody == false` and then
  `_loc3_ >= 0` guard the native hitTest. Snapshot position/paused values cannot
  reconstruct these actual evaluations or authorize evaluating the call twice.
- The s30 original XML export binds the wrapper placement and body frames1–7,
  including bdmn at depth29. Sampled P2 frames at ticks10/11/12 are **4/5/6**;
  body frames4–7 have no scripts. These are sampled states, not execution order.
- All **5,437** s264 events are revalidated through its unchanged analyzer.
  Raw bytes also match the historical receipt. The eight events from sequence
  **4055 through 4062** retain the unready root sample, geometry collection,
  destination entry, frame1 entry and initialized exit. They contain no
  observation of this external callsite's guards, evaluated operands or result.
  All **12** existing receiver-function query rows follow initialization.

`execution_observed`, actual operands, native result and operand-lifetime join
remain **null**, not false. Missing instrumentation cannot prove nonexecution.
The current full geometry gate still exits1: **missing p1 receiver at tick11**.
No receiver exemption, alternate sample time or initialization change follows.
The historical receipt is reused unchanged, not resealed or promoted to live
loader attestation. This is portable evidence replay, not fresh native parity.

## Source-first boundary

1. Complete selected callback and caller are retained, together with frame4–7
   empty script maps. Earlier guards and movement side effects remain visible.
2. Source XML binds the wrapper/body placements and their ClipActions. s260/s264
   separately bind P1's frame840 new bdmn, not MOVE; a source placement or stamp
   does not prove continuous engine allocation or an evaluated target operand.
3. The callback has explicit early returns and conditional goto/plays later in
   its body. No implicit label-end return is invented. P1's existing summon
   exit/source inventory remains in the unchanged s264 diagnosis.
4. Tests lock source operands, short-circuit guards, archived function equality,
   sampled frames and raw boundaries. Mutated operands/guards, an inserted
   archived observer, missing boundary rows and wrong hashes reject.
5. The same s64 input case already ran as s264. It lacks this site's actual
   execution observations; no same-input proof of the proposed eligibility
   rule exists. No runtime mechanism is changed or marked complete.

## Next discriminator and capture decision

One future owned capture should extend only **P2 base Sprite638 on_enterframe,
 ticks10–12**, retaining s260/s264 initialization markers and the exact s64 tape:

1. Observe callback entry and actual early-return/short-circuit outcomes in
   original order, including skipped-site reasons. Do not infer them from a root
   snapshot or re-evaluate guards after a side effect.
2. At the existing hitTest, observe the once-evaluated receiver and target,
   their direct owner/depth/frame and source placement boundaries, then the
   actual result. Preserve the original receiver binding, argument evaluation
   and short-circuit behavior; introduce no additional hitTest invocation.
3. Require natural same-site executed and skipped controls. If this tape never
   reaches the site, retain that bounded result; do not force a branch or change
   the baseline to manufacture a positive. An independently declared control
   would then be required before claiming observation coverage.
4. Correlate those observations with the unready/init boundaries in that same
   run. A path or stamp alone is not allocation identity. Even a proved result
   for this one site cannot establish coverage of every collision path or admit
   a receiver omission. Undefined-method dispatch elsewhere remains outside
   this cut, as do tick41 and nested Yulong ownership.

No safe operand-preserving probe or executed evidence is claimed here. Locked
artifacts suffice to establish the exact blind spot; repeating the old capture
would not recover missing events. A new instrumented capture is required to
resolve it, with source-preservation/operand evaluation qualification first.
**Zero builds, exports, player launches or new images; capture cost zero.**
Future capture cost and actual person-days remain unknown. Measured analysis
session and check durations are in [session timing](session-timing.json) and
[gates](gates.json).

## Reproduce and scope

```sh
PYTHONPATH=. python3 evidence/sampling-upgrade/s273/diagnose.py --output /tmp/s273.json
PYTHONPATH=. python3 evidence/sampling-upgrade/s273/diagnose.py --output /tmp/s273-required.json --require-external-callsite # exit 1
python3 -m unittest tools.tests.test_external_collision_callsite tools.tests.test_receiver_authored_query tools.tests.test_receiver_init_order tools.tests.test_p1_receiver_availability tools.tests.test_sampling_geometry tools.tests.test_sampling_native tools.tests.test_import_guards
python3 tools/verify.py
python3 tools/check_handoff.py
/tmp/bvn-s27-venv/bin/python tools/validate_contracts.py
```

Portable diagnosis needs no player or external XML cache. The historical full
geometry command in gates.json uses s264's original build/capture paths; restore
its archives as described in [s264](../s264/README.md) if needed, never reseal its
receipt. Diagnosis and **65 focused tests** pass. External-callsite requirement
and unchanged full geometry honestly exit1. [Project checks](project-checks.json)
record integrity/handoff/contracts; contracts are not behavioral proof.

Only the new priority table, s273 evidence/test and requested tracking files
change. Ranks2+ are planning only; s249–s272 and the closed s241–s244 queue stay
unchanged. No shared sampler, strict validator, schema, tape, baseline, threshold,
production gameplay/runtime, renderer, merge or deployment change.
