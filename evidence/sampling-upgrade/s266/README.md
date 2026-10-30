# s266 — AFTER-s263 rank 3: Chad defining-context continuation

Baseline master `065145c8` / #143; branch `feat/s266-chad-defining-context`.
Authority: **rank 3 only** in [AFTER-s263 priority](../next-fix-priority-after-s263.md).
`production_admitted=false`; `native_parity_proven=false`; M0-02 remains pending.
**Evidence-only: no proved Chad continuation/mapping cut or exit-model fix.**
Ranks 1/2/4–9 and s254–s265 are unchanged. No runtime, strict validator,
threshold, input tape or historical baseline changes.

## Result

The locked s263 capture has a root-defined worker, so it cannot answer what
happens when an authored worker's defining timeline is removed. A bounded
extension adds a synthetic authored child Sprite60000, defined on frame1, and
two instances of authored parent Sprite60001. Both parents stop on frame1;
frame2 retains their child, frame3 removes it. No additional Chad marker is added.

The worker saves the witness and operation in registers. It records that its
`this` and frame1 `defining` reference equal the receiver before calling the
root-defined operation. That operation observes the depth occupant, performs
the parent goto, and independently observes the slot before returning. The
surviving root reports the saved plain-object witness after invoking the worker.

| Control at tick10 | Occupied before | Empty inside operation / after worker | Parent frame | Post write |
| --- | --- | --- | --- | --- |
| Authored child, retained, seq7206 | true | false / false | 2 | 1 |
| Authored child, removed, seq7207 | true | true / true | 3 | 0 |
| Inherited s263 root-defined worker, retained | true | false / false | n/a | 1 |
| Inherited s263 root-defined worker, removed | true | true / true | n/a | 1 |

Both authored controls report `before=1`, `receiverBefore=true`,
`definingBefore=true`, `boundary=1`, native depth **-16383** (SWF depth1).
The emitted child P-code has `StoreRegister 4` and the operation's
`CallMethod → Pop → Push register4 → Push "post" → Push 1 → SetMember`.
The retained positive proves this instrumentation can write after the call.
The removed negative does **not** tell us which instruction executed, whether
Pop ran, whether an activation became invalid, or whether the VM returned,
unwound or aborted. Reference equality is not a native activation identifier.
No root-worker equivalence or removal-as-return is inferred.

Actual Chad remains `before=1, control=1, post=0, observerEntry=0` at root ticks
11/12; `goto_after`, `callee_exit`, `caller_after` remain missing. Its instrumented
SWF is byte-identical to s263/s257. The accepted capture has **9,493 events /
61 root samples**; all **122 actor tick/payload rows equal s263**. Different
pre-fight/display timing is retained. This is not Godot or full native parity.

## Provenance and failed attempt

[build_probe.py](build_probe.py) restores s257 plus the locked s263 extension,
checks all source/output hashes, adds two unused synthetic symbols and authored
root placements, then imports only main frame1/frame10 and the new child worker.
[control.as](control.as) and [worker.as](worker.as) are the complete new actions.
No timers, random reads, visual shapes or gameplay receiver writes are added.
The synthetic hosts remain stopped and have no enterFrame handlers.

[timeline-audit.json](timeline-audit.json) compares the final SWF XML with s263:
original tag order and attributes/actions are unchanged except the two root
DoActions and explicitly listed XML roundtrip encoding widths (1→0). Those
width changes are retained, not hidden behind a claim of main byte identity.
The parent frame2 has no placement, MOVE, removal or DoAction; frame3 has
RemoveObject2 depth1. The child's definition is on its own authored frame1.
[audit_timeline.py](audit_timeline.py) reproduces the comparison.
[P-code provenance](pcode-provenance.json) binds emitted code to the captured
main SWF. Emitted code is **not** an executed-PC trace.

The first capture used `getInstanceAtDepth(1)`, incorrectly treating an authored
slot like a dynamic depth. Even the retained slot appeared empty, so it failed
the independent slot discriminator. [Rejected r01](rejected-r01/README.md)
retains its trace, receipt, exact sources, build extension and command; it is
not positive evidence and is explicitly rejected by tests. The corrected run
uses the receiver's `getDepth()` and observes -16383. No old receipt is resealed.

The archive contains only the changed main/build/patch files; unchanged game
dependencies remain in s257. `runtime_fighter=null` remains an independent loader
attestation gap. No work on that separate rank is performed here.

## Source-first boundary and next discriminator

1. Chad source remains `DefineSprite_16/frame_1/DoAction.as`, called by
   `DefineSprite_607/frame_1/PlaceObject2_16_31/CLIPACTIONRECORD onClipEvent(enterFrame).as`.
   Its complete source/timeline audit is inherited from s257 through s263;
   `doAllAction` has subsequent predicates and `doDropDown`, not an explicit
   return after the conditional parent goto. No original action is rewritten.
2. Chad Sprite607 newly places Sprite16 at depth31/frame1, removes it linearly
   at frame13; normal attack `砍1` is frame183. The synthetic control instead uses
   its explicitly recorded parent frames1/2/3. It does not prove identical Chad
   activation or VM state, nor that a goto executes skipped-frame scripts.
3. Parent goto is the original exit operation; neither synthetic natural
   function end nor an absent post write becomes an original AS return event.
4. Tests lock positive native slot/write observations, reject the faulty first
   capture, and keep exact continuation/exit flags false. They do not install
   a runtime expectation that removal suppresses continuation.
5. Two original-player captures use the unchanged s76 tape; only the corrected
   control is accepted. No runtime implementation or Godot parity is attempted.

**Next discriminator:** original-player executed-PC, operand stack and defining
activation records at the exact Chad `gotoAndPlay` CallMethod, following Pop and
register5 SetMember, paired with retained same-context execution. This slice
establishes no such debugger facility and does not claim none exists. The
removed authored-context negative means another absent marker is insufficient.
No thin mapping is proved; do not implement fabricated exits, removal-as-return,
root-worker equivalence, broad AS rewrites or validator exceptions.

## Gates, costs and reproduction

[Gates](gates.json): receipt/diagnosis exit0; exact continuation, lifecycle,
callsite and full-AS gates honestly exit1. Full AS retains **594 unvisited /
415 uninstrumented** obligations. **100 focused tests pass**. Project integrity,
handoff and contracts are recorded in [project-checks.json](project-checks.json).
No product obligation closes.

New capture was required because locked s263 has no authored defining-context
pair. First build **6.889s**, rejected capture **27.688s**; corrected build
**7.041s**, accepted capture **27.330s**. Two native launches total, both serialized
by the existing capture lock. JPEXS emitted a sandbox logging warning but
completed exports/builds. These are measured subprocess costs, not person-days
or total human effort. No native PC/stack capture was performed.

```sh
PYTHONPATH=. python3 evidence/sampling-upgrade/s266/diagnose.py --output /tmp/s266.json
PYTHONPATH=. python3 evidence/sampling-upgrade/s266/diagnose.py --output /tmp/s266-exact.json --require-exact-continuation # expected exit 1
python3 -m unittest tools.tests.test_chad_defining_context tools.tests.test_chad_register_control tools.tests.test_as_continuation_discriminator tools.tests.test_chad_lifecycle_observer tools.tests.test_call_exit_diagnosis tools.tests.test_sampling_callsite tools.tests.test_sampling_doaction tools.tests.test_sampling_native tools.tests.test_import_guards
python3 tools/verify.py
python3 tools/check_handoff.py
/tmp/bvn-s27-venv/bin/python tools/validate_contracts.py
```

For receipt/product gates, restore s257 `native-build.tar.gz` into
`/tmp/bvn-s266-r02-build`, overlay s266 `build-extension.tar.gz`, decompress
`native-capture.log.gz` into `/tmp/bvn-s266-r02-capture/native.log` and copy the
receipt as `receipt.json`. Use [gates.json](gates.json); do not reseal receipts.
For a fresh capture use `PYTHONPATH=. python3 evidence/sampling-upgrade/s266/build_probe.py
--output /tmp/fresh-s266-build --ffdec /path/to/ffdec.jar`, then the capture command
with fresh build/capture paths. The builder uses its fixed s266 run ID.

For timeline audit, export restored s263 and s266 main files with JPEXS
`-swf2xml input.swf output.xml`, then run `audit_timeline.py --before s263.xml
--after s266.xml --swf captured-main.swf --output /tmp/s266-timeline.json`.
For P-code, use the command in pcode-provenance.json with a fresh output directory.

No production change, merge or deployment.
