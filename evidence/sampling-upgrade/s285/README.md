# s285 — Yulong nested lifetime qualification (evidence-only, unproved)

Base: master `3a5ce953` / #162. Branch: `feat/s285-yulong-nested`.
Exclusive authority: [AFTER-s281 rank 4](../next-fix-priority-after-s281.md).
`production_admitted=false`; `native_parity_proven=false`;
`runtime_binding_proved=false`; zero product obligations closed; M0-02 pending.

Only Sprite345 frame188 depth28 k1atm (Sprite104) → depth2 mian (Sprite2),
ticks15–22 of the unchanged s239 tape retained in s275. No new build or capture.
This slice executes a removal-byte/trace correlation and observer qualification
audit. It does **not** obtain a direct native removal dispatch or nested invocation.

## New bounded evidence

[diagnose.py](diagnose.py) revalidates all 5,214 s275 events, archived binaries,
receipt hashes, outer opcode projection and 122 actor rows against s247 before
joining the retained stream. Inputs are pinned in [input-sha256.json](input-sha256.json).
[diagnosis.json](diagnosis.json) is regenerated, not copied from historical reports.

| Boundary | Result and limit |
| --- | --- |
| Parent removal source | Original SWF Sprite345/frame194 tag361 is RemoveObject2 depth28, bytes `02071c00`, uncompressed offset687655. s275 build retains identical bytes at702677. These are file offsets, **not native dispatch PCs**. |
| Same-run parent bracket | P1 body193/root21 slot still contains `abcd` (sequence3776); body194/root22 slot is undefined (sequence3794). This correlates the authored removal frame with the disappearance interval, not execution of the tag. |
| Child boundary | Sprite104/frame5 tag8 removes depth2: `02070200`, original offset66858 / s275 offset75020. s275 before/after goto sequences3692/3693 show child removal at tick18; rename sequences3713/3714 occur at tick19. These remain separate from parent removal. |
| Nested functions | The archived Sprite2 source retains all six function bodies exactly. Only `aiGeoStamp` and `source_after_stamp` are appended after initialization. There are no direct function entry/operand hooks. Invocation remains **unknown**, not zero or unreachable. |
| Observer qualification | Outer opcode/control-flow projection and actor/input/key payload checks pass. The five logged callback spans are2/2/1/1/2ms with16/16/17/16/16 value records. They include source execution and logging, not observer latency. Random rows differ; no paired timing/dispatch control exists. Perturbation qualification fails. |

The nested operand inventory retains direct `_parent.pn`, `_parent.pw`,
`_parent.fzpw`, `this.hitTest(_loc4_)` and `this.hitTest(_loc4_.mian)` literally.
Here `_parent` is Sprite104. The outer clip callback's `_parent` is Sprite345.
Calling native `mian.hitTest` outside Sprite2 does not prove invocation of
`gameRunning`, `beida`, `fangyu`, `checkHit`, `getHitObj` or `getStgHitObj`.
Definitions, function-typed properties and initialized arrays are not executions.

## Qualification outcome and remaining experiment

The available observer is **not qualified for the requested exact correlation**.
Repeating it would retain the same blind spots, so this slice does not launch a
new player or add an unqualified nested call. The missing observations are:

1. Bind an actual native RemoveObject2 dispatch to the byte-pinned Sprite345
   frame194/depth28 tag and the selected placement, with ordered pre/post slot
   observations. A frame194 DoAction, root read, unload callback or missing name
   alone cannot substitute for tag dispatch. File offsets need a proved native
   dispatch mapping before use as breakpoints.
2. Observe a naturally executed call/entry and its actual arguments/receiver at
   the Sprite2 defining activation, preserving the direct parent. Capture guard
   and existing hitTest operands once and in compiled order, including returns
   or invalidated continuation. Do not invoke these functions just to obtain a
   record or treat absent hooks as proof of nonexecution.
3. Before capture, qualify the complete compiled function headers, registers,
   branches and original operation projection. Then run independently retained
   observer-off/on controls on this same tape/placement with direct dispatch
   witnesses, preserving full logs and random differences. Trace spans and equal
   actor state are insufficient to bound perturbation; no tolerance is invented.

These are remaining prerequisites within rank4, not work on another chain.
No ancestor pn, alias, artificial hitTest, enlarged box, forced call, eligibility
rule, shared sampler/threshold/validator or runtime change is introduced.
No historical s254–s284 file, receipt, tape or baseline is edited.

## Source-first answers

1. Complete Sprite104 ten-frame source/timeline and frame188 outer callback remain
   in [s270](../s270/README.md); s285 independently binds child/parent removal bytes
   and audits the six Sprite2 function bodies in the actual s275 build archive.
2. The source placements are new, not MOVE (locked s247 source-binding / s270
   timeline). No continuous allocation identity is inferred from stamp70/71.
3. Sprite104 stops at1, conditionally goes to5, renames at5 and stops at10;
   Sprite345 removes depth28 at194. No label-end exit is invented.
4. Tests reject wrong/missing source removal tags, missing or reordered joins,
   an operand omission, ancestor substitution and an added direct nested call.
   Unknown execution and perturbation remain explicit; no gameplay rule is tested.
5. The retained s275 native run is revalidated on its original tape. No new native
   or Godot comparison is claimed; exact dispatch/invocation/parity remain unproved.

## Reproduction and gates

```sh
PYTHONPATH=. python3 evidence/sampling-upgrade/s285/diagnose.py --output /tmp/s285.json
PYTHONPATH=. python3 evidence/sampling-upgrade/s285/diagnose.py --output /tmp/s285-parent.json --require-parent-removal # exit 1
PYTHONPATH=. python3 evidence/sampling-upgrade/s285/diagnose.py --output /tmp/s285-nested.json --require-nested-invocation # exit 1
PYTHONPATH=. python3 evidence/sampling-upgrade/s285/diagnose.py --output /tmp/s285-observer.json --require-observer-qualification # exit 1
PYTHONPATH=. python3 evidence/sampling-upgrade/s285/diagnose.py --output /tmp/s285-geometry.json --require-geometry # exit 1
PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s285 -p 'test_*.py'
python3 -m unittest tools.tests.test_yulong_operand_boundary tools.tests.test_nested_owner_diagnosis tools.tests.test_yulong_k1atm_observer tools.tests.test_sampling_geometry tools.tests.test_sampling_native tools.tests.test_import_guards
python3 tools/verify.py
python3 tools/check_handoff.py
```

Eight new focused tests and61 retained tests pass. Diagnosis, verify and handoff
pass; all four requested negative gates retain exit1. Strict geometry still
rejects `missing-source-list:_level0.game.p1.mc.k1atm.mian` through the unchanged
collector. Measured subprocess costs are in [gates.json](gates.json) and
[project-checks.json](project-checks.json); session time is in
[session-timing.json](session-timing.json). Person-days remain unknown.
No runtime contracts changed; no merge, deployment or production readiness claim.
