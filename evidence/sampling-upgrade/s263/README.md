# s263 — AFTER-s258 rank 5: executed continuation at Chad goto

Baseline master `a230e5b3` / #140; branch `feat/s263-chad-executed-continuation`.
Authority: **rank 5 only** in [AFTER-s258 priority](../next-fix-priority-after-s258.md).
`production_admitted=false`; `native_parity_proven=false`; M0-02 remains pending.
**Evidence-only: exact Chad continuation and an exit-model fix remain unproved.**
Ranks 1–4, s254–s262, production runtime and existing validators are unchanged.

## Result and limit

The locked s257 archive has emitted P-code and absent post markers, but no
executed PC, operand stack or activation observations. Re-reading it cannot
recover those observations. One bounded native capture adds a positive
register-access control; it does not insert another speculative Chad exit marker.

The **same function object** runs twice, with dynamic clips as `this`, once
retained and once removed. A separate operation checks the occupied depth,
optionally removes the receiver, and records slot emptiness while the worker
is suspended. After the operation returns, the worker writes `post=1` through
its saved plain-object register. The surviving root reports the result.

| Native event | Tick / display | Occupied before | Empty inside operation / after worker | Register post |
| --- | --- | --- | --- | --- |
| Retained receiver, seq7487 | 10 / 447 | true | false / false | 1 |
| Removed receiver, seq7488 | 10 / 447 | true | true / true | 1 |
| Actual Chad witness, seq7534 | 11 / 448 | See lifecycle record | Controller slot empty | 0 |
| Actual Chad witness, seq7571 | 12 / 449 | See lifecycle record | Controller slot empty | 0 |

Both controls also verify `this == saved.receiver` before the operation. Exported
P-code shows `StoreRegister 4`, then the operation's `CallMethod → Pop → Push
register4 → Push "post" → Push 1 → SetMember`. The successful write is positive
behavioral evidence of continuation in this **root-defined worker**, including
its post-call Pop, not a directly sampled instruction pointer or stack dump.

**Dynamic receiver removal is not proved equivalent to invalidating Chad's
function-defining timeline/activation.** The worker is defined at root; invoking
it as a method of a removed clip does not establish that its defining execution
context was invalidated. Chad's `doAllAction` is defined in Sprite16 frame1 and
called from that controller's authored enterFrame. Thus this control disproves
only a blanket claim that removing any `this` always prevents register writes.
It does not prove post-invalidation register access in the exact Chad context.
The original CallMethod/Pop/SetMember execution discriminator remains open.
No source-mapped native debugger PC/stack facility was established in this slice;
we do not claim that none exists. P-code export is not such a facility.

The new trace contains **9,774 events / 61 root samples**. All **122 actor
tick/payload rows** match s257 exactly. Pre-fight events and display offsets are
retained, not normalized; this is not zero-cost instrumentation or Godot parity.
Actual Chad still has `before=1, control=1, post=0, observerEntry=0`, one incomplete
tick10 invocation, and missing `goto_after`, `callee_exit`, `caller_after`.
No return, unwind, abort or stack corruption is inferred from those absences.

## Bounded extension and provenance

[build_probe.py](build_probe.py) restores the hash-bound s257 archive and changes
only main frame1 (the isolated [control](control.as)) and frame10 (one invocation
at tick10), plus the run ID. Chad SWF is **byte-identical to s257**, preserving the
original caller, goto, subsequent predicates and all existing observers. The
control creates empty dynamic clips, installs no enterFrame handlers, uses no
randomness or timer, and removes its temporary host before the root sample.
No receiver gameplay fields, input tape or existing baseline outputs are edited.

[diagnose.py](diagnose.py) validates the raw sequence, input identity, archived
build hashes, source hashes, positive pair, emitted register sequence, unchanged
Chad SWF, source/timeline checks inherited from s257, and exact actor comparison.
[diagnosis.json](diagnosis.json) retains the full boundary window and limitations.
[build-extension.tar.gz](build-extension.tar.gz) contains only the changed build
files; unchanged dependencies remain in s257's archive. New receipt and capture
are retained without resealing any historical receipt. `runtime_fighter=null`
remains an independent loader-attestation gap.

## Source-first boundary and next discriminator

1. Original scripts remain s257's locked Chad `DefineSprite_16/frame_1/DoAction.as`
   and `DefineSprite_607/frame_1/PlaceObject2_16_31/CLIPACTIONRECORD onClipEvent(enterFrame).as`.
   `doAllAction(special)` has no explicit return after its conditional goto and
   retains subsequent predicates/`doDropDown`. Complete source is in s257 diagnosis.
2. Sprite607 newly places Sprite16 at depth31 on frame1, removes it linearly on
   frame13; `砍1` is frame183. A jump to183 does not execute frame13 scripts by proof.
   The new control uses dynamic `createEmptyMovieClip/removeMovieClip`, a distinct
   lifetime operation; no MOVE or authored-placement equivalence is assumed.
3. Original exit remains the conditional parent goto, not an AS return. The
   control's natural function end is a probe operation, never a synthetic exit
   for an original invocation and never input to a fabricated call-after event.
4. Tests lock positive slot/removal/write observations, source preservation and
   rejection of missing/altered controls; they explicitly keep the exact context
   unproved. No implementation assumption is turned into a runtime expectation.
5. One new original-player capture uses the unchanged s76 tape. No Godot behavior
   changes or parity claim; the full move-frame audit remains outside this cut.

**Next discriminator:** define the register-bound worker in an authored child
timeline, bind its defining target/activation to that instance, and pair a
retained parent goto with a removing parent goto. Observe slot removal separately
from the suspended function's local-register write. A root-defined function with
changed `this` is insufficient. If the authored-context positive control cannot
be established, obtain original-player executed-PC and activation/stack records
at the exact Chad `gotoAndPlay` CallMethod, following Pop and register5 SetMember,
with a retained same-context positive control. No additional absent marker closes
this gap. Do not implement removal-as-return, synthetic exits, full AS rewrite,
receiver fixes, threshold changes or validator exceptions.

## Checks, costs and reproduction

[Gates](gates.json) record commands, exits and measured durations. Large callsite
and full-AS JSON reports are retained losslessly as `.json.gz`. Receipt and
portable diagnosis pass; exact-continuation requirement, unchanged lifecycle,
callsite and full-AS gates retain **exit1**. Full AS still has **594 unvisited /
415 uninstrumented** obligations. **95 focused tests pass**. Integrity, handoff
and contracts results are in [project-checks.json](project-checks.json).

The bounded build took **2.342 seconds**; the single successful native launch,
capture and cleanup took **30.160 seconds**. The first sandbox preflight failed
on `ps` before a player launch; its command/error are retained separately.
The retry used authorized sandbox escalation and the existing serialized native
capture lock. No second player capture or log recovery was needed. JPEXS export
reported a sandbox logging-file warning but exited0 and produced the retained
P-code. Measured subprocess costs are not inferred person-days or total effort.

```sh
PYTHONPATH=. python3 evidence/sampling-upgrade/s263/diagnose.py --output /tmp/s263.json
PYTHONPATH=. python3 evidence/sampling-upgrade/s263/diagnose.py --output /tmp/s263-exact.json --require-exact-continuation # expected exit 1
python3 -m unittest tools.tests.test_chad_register_control tools.tests.test_as_continuation_discriminator tools.tests.test_chad_lifecycle_observer tools.tests.test_call_exit_diagnosis tools.tests.test_sampling_callsite tools.tests.test_sampling_doaction tools.tests.test_sampling_native tools.tests.test_import_guards
python3 tools/verify.py
python3 tools/check_handoff.py
/tmp/bvn-s27-venv/bin/python tools/validate_contracts.py
```

For unchanged receipt/product gates, restore s257 `native-build.tar.gz` into
`/tmp/bvn-s263-r01-build`, then overlay this slice's `build-extension.tar.gz`.
Decompress `native-capture.log.gz` to `/tmp/bvn-s263-r01-capture/native.log` and
copy `native-receipt.json` there as `receipt.json`. Use commands in `gates.json`
and the original player path recorded in the receipt; do not reseal old receipts.
For a fresh capture, use `build_probe.py --ffdec /path/to/ffdec.jar --output
/tmp/fresh-build --run-id fresh-id`, create a fresh capture directory, and follow
[capture-command.json](capture-command.json) with fresh paths. P-code export
command and hashes are in [pcode-provenance.json](pcode-provenance.json).

No product obligation closed; no runtime change, merge or deployment.
