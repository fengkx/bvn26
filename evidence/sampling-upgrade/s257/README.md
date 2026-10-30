# s257 — AFTER-s253 rank 4: positive AS continuation discriminator

Baseline master `360c483f` / #134; branch `feat/s257-as-continuation`.
Authority: rank 4 in [AFTER-s253 priority](../next-fix-priority-after-s253.md).
Only the exact Chad s76 tick10 normal-attack call is investigated.
`production_admitted=false`; `native_parity_proven=false`; M0-02 remains pending.
**Evidence-only: positive continuation and a VM exit model remain unproved.**
Zero product obligations are closed; no runtime fix is admitted.

## Result

A plain AS object, saved on the surviving root before the authored goto, retains
its positive pre-call control but neither post-goto write. This observation does
not depend on reading the removed controller's properties or on the old observer's
guards. The first post-goto instruction itself is still not positively witnessed.

| Boundary | Sequence / tick / display | Result |
| --- | --- | --- |
| Root before selected call | 7439 / 10 / 445 | Witness undefined |
| Selected caller / callee entry | 7462–7463 / 10 / 445 | Same occupied controller slot |
| Goto front edge | 7469 / 10 / 445 | Same occupied controller slot; parent frame5 |
| Root after goto | 7484 / 11 / 446 | Plain object; before=1, control=1, post=0, observerEntry=0 |
| Existing lifecycle root observation | 7485 / 11 / 446 | Parent frame183; controller depth empty |
| Following root | 7521 / 12 / 447 | Same token/values; post=0, observerEntry=0 |

The call-site gate retains one incomplete tick10 invocation. All three original
exit markers (`goto_after`, `callee_exit`, `caller_after`) remain missing.
All **122 actor tick/payload rows** exactly match s252 on all 14 state fields.
Pre-fight counts/display offsets are retained, not normalized. This native/native
control is not Godot parity or proof of zero instrumentation timing cost.

## Independent discriminator and compilation proof

The isolated [builder](build_probe.py) first runs the unchanged `--chad-lifecycle`
build, then patches only temporary copies of Chad's callee and the root observer:

- Immediately before the existing goto-front marker, allocate a plain object with
  a unique probe token, save it on the root, and retain it in a local register.
  Capture the observer function reference before the goto as well.
- A pre-goto control calls that captured function with the object as a third
  parameter. The observer's first statement writes `observerEntry=1`, before any
  receiver lookup or guard. A control-only return avoids emitting a fake lifecycle
  phase. Save the control result, then reset `observerEntry=0` before the goto.
- Immediately after the original `_parent.gotoAndPlay("砍1")`, write `post=1`
  through the saved object register. Then call the captured observer with the
  existing `goto_after` phase and the extra object parameter. The old observer
  body and all other original phase calls remain intact. No `call_after` is made up.
- Root ticks10–12 read only the probe object. No receiver fields are written.
  No source predicate, gameplay call, goto, or source statement is removed.

P-code exported from the **captured build's** SWFs is retained under original
paths in `pcode/chad/` and `pcode/main/`. Provenance locks both SWFs and JPEXS.
The callee uses `InitObject → StoreRegister 5`; the observer reference is register6.
The original goto `CallMethod` is followed by `Pop`, then
`Push register5; Push "post"; Push 1; SetMember`, then a register6 function call.
The observer entry writes via parameter register4 before any guard or `_global`
lookup. The actual compiled caller is byte-identical to s252, preserving the
unqualified `doAllAction()` and single `gameRunning()` evaluation.

Thus there is no invalidated-target property lookup between the goto and the
first persistent write. The control proves that the same captured function can
write this object before removal; it does **not** prove register/context survival
after the goto. The first bytecode after `CallMethod` is still `Pop`, which has no
persistent witness. Zero post/entry values do not establish whether that `Pop`,
any `Push`, or the VM's call-return boundary executed. Absence is not return or
abort. A pure old-observer-guard explanation is insufficient, but no exit model
is selected and no validator is changed.

## Source-first boundary

[diagnosis.json](diagnosis.json) recomputes the full source callee and handler,
locked hashes, and source XML timeline facts (s72 archive), not guessed frames:

1. Chad `DefineSprite_607/frame_1/PlaceObject2_16_31/CLIPACTIONRECORD onClipEvent(enterFrame).as`
   calls unqualified `doAllAction()` after `gameRunning()`. The complete
   `DefineSprite_16/frame_1/DoAction.as::doAllAction(special)` retains subsequent
   predicates and `doDropDown()` after the normal-hit goto, with no explicit return.
2. Sprite607 frame1 newly places Sprite16 at depth31; linear frame13 removes it;
   label `砍1` is frame183. Jumping to183 does not prove execution of frame13 scripts.
3. The authored conditional parent goto is a timeline transition, not an AS return.
4. Tests lock observed writes/absences, source structure and emitted instruction
   order. They reject missing control/identity/records, never assume removal is return.
5. One fresh original-player run uses the unchanged s76 tape. The limited source
   audit does not cover all move frames or authorize any Godot mechanism change.

## Next discriminator and limits

Obtain an **executed-PC / VM stack observation** at this exact source-bound
`gotoAndPlay` CallMethod, its following Pop, and the register5 SetMember, with a
positive same-context continuation control. Record caller/callee stack unwind and
receiver invalidation separately. If an original-player PC facility is unavailable,
that is an explicit evidence gap; additional missing markers cannot replace it.
A second possible control must independently establish local-register/object
access after invalidation before interpreting a zero as non-execution.

Runtime-loaded fighter identity is still unattested (`runtime_fighter=null`);
compiled SWF hashes and source-scoped events are not loader attestation. No full
AS completion, nested receiver change, removal-as-return model or gameplay fix.
Ranks **1/2/3/5**, s254–s256, baseline tapes, thresholds and strict validators are
untouched. No merge or deployment.

## Gates, cost and reproduction

- One player launch, **9,727 complete events / 61 root samples**; strict receipt exit0.
- Portable diagnosis exit0; lifecycle, selected call-site and full AS gates exit1.
  Full AS retains **594 unvisited / 415 uninstrumented** obligations.
- **91 focused tests pass**; integrity, handoff and contracts pass. Exact commands,
  exits and measured subprocess durations are in `gates.json` and `project-checks.json`.
- Build **8.889 s**; launch/capture/cleanup **28.016 s**, then log recovery **0.789 s**.
  These are measured subprocess times, not person-days or total elapsed work.

The first capture completed, but the caller had not created its destination
folder, so writing `native.log` failed after sampling. Cleanup still ran. The
failure is retained in `capture-environment.json`. Under the existing capture lock,
all run-prefixed lines were recovered from the player log in original order,
without deduplication, sorting or suffix trimming, and the unchanged strict
adapter sealed this new capture. See `capture-recovery.json` for hashes and cost.
No second launch, historical receipt resealing or validation exception was used.
An initial test assumed s252 archived patch sources; it did not. The failure is
retained; the corrected test compares actual exported caller P-code instead.

Portable reproduction from repository root (no player or external XML cache):

```sh
PYTHONPATH=. python3 evidence/sampling-upgrade/s257/diagnose.py --output /tmp/s257-diagnosis.json
python3 -m unittest tools.tests.test_as_continuation_discriminator tools.tests.test_chad_lifecycle_observer tools.tests.test_call_exit_diagnosis tools.tests.test_sampling_callsite tools.tests.test_sampling_doaction tools.tests.test_sampling_native tools.tests.test_import_guards
python3 tools/verify.py
python3 tools/check_handoff.py
/tmp/bvn-s27-venv/bin/python tools/validate_contracts.py
```

To rerun retained receipt/product gates, restore `native-build.tar.gz` into
`/tmp/bvn-s257-r01-build`, decompress `native-capture.log.gz` into
`/tmp/bvn-s257-r01-capture/native.log`, and copy `native-receipt.json` there as
`receipt.json`. Use exact commands in `gates.json`, pinned probe sources and
`/Volumes/Flash Player/Flash Player.app`; preserve original receipt paths/hashes.

For a new capture, use fresh paths/run ID and create the capture directory first:

```sh
PYTHONPATH=. python3 evidence/sampling-upgrade/s257/build_probe.py --ffdec /tmp/bvn-s66-tools/ffdec/ffdec.jar --output /tmp/bvn-s257-new-build --run-id s257-chad-new
mkdir -p /tmp/bvn-s257-new-capture
python3 -m tools.sampling_native --case evidence/sampling-upgrade/s76/chad__attack__neutral__ground__near.json --build /tmp/bvn-s257-new-build --trace /tmp/bvn-s257-new-capture/native.log --receipt /tmp/bvn-s257-new-capture/receipt.json --timeout 180 --allow-window-activation
```

Use the existing serialized native capture lock; do not remove locks. The retained
build includes the complete instrumentation diff and generated patch sources;
[diagnose.py](diagnose.py) verifies source, build, P-code and raw-stream integrity.
