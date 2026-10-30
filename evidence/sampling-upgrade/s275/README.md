# s275 — Nested Yulong operand/owner boundary (unproved repair)

Base: master `af2ddb59` / #152. Branch: `feat/s275-yulong-operand-owner`.
Exclusive authority: [AFTER-s272 rank 3](../next-fix-priority-after-s272.md).
`production_admitted=false`; `native_parity_proven=false`;
`runtime_binding_proved=false`; zero product obligations closed; M0-02 pending.

One source-bound frame188 placement only: Sprite345 depth28 `k1atm` (Sprite104)
→ depth2 `mian` (Sprite2), ticks15–22 on the unchanged s239 tape.
This adds an isolated observer and evidence, **not a production ownership or
receiver-eligibility repair**. Other ranks and s254–s274 are unchanged.

## Observations and their limits

One native player launch produced **5,214 complete events**. All **122 actor
state payloads** match locked s247 on all 14 fields. Full sequence validation
and the fresh receipt pass; strict geometry still rejects
`missing-source-list:_level0.game.p1.mc.k1atm.mian`.
All 61 input-latch rows and 1295 key-read rows also match s247. Random values
and pre-fight counts differ and are retained; this is not a random-tape replay.
No historical receipt was modified or resealed. No tape was transplanted.

| Boundary | Actual observation |
| --- | --- |
| Root15 | Depth28 absent; this precedes placement initialization |
| Callbacks16–17 | All five original sites evaluated; targets undefined, fourth receiver `hitmc.mian` undefined; other receivers are the stamped child |
| Callback18 | First target is P2 `bdmn`, first result true; sites2–5 still execute; fourth receiver/result remain undefined |
| Tick18 before/after goto | Child name and depth2 slot present before goto, both absent after goto; parent still `k1atm`, stamp70, now frame5 |
| Root19 / before rename | Parent still named `k1atm`, child absent |
| Tick19 after rename | Parent is `abcd`, stamp70; depth28 resolves `abcd`, `k1atm` name no longer resolves |
| Callbacks19–20 | Original callback still runs, but all child receiver expressions are undefined |
| Root20–21 | Parent depth28 contains `abcd`, frames6–7 |
| Root22 | Parent depth28 and both names absent |

Full decoded operands and boundary sequences are in [diagnosis.json](diagnosis.json).
The child disappearance occurs inside the goto interval, before the separately
observed rename. Parent removal is only bracketed by root21/root22, not an exact
native removal dispatch/PC. Stamps, paths and slot equality are not continuous
allocation identity. Root snapshots alone do not establish callback execution.

## Source-preserving observation and the `or` correction

[build_probe.py](build_probe.py) extends the locked s247 archive already audited
by s270; it does not rebuild shared tools or mutate any original input. Only the
selected outer enterFrame, Sprite104 frame5 rename and bootstrap/root observer
are patched. Static loader paths point to this new build. The exact original
source and five operand expressions are retained, including **`hitmc.mian`**.

[observer.as](observer.as) returns the same once-evaluated operand/result/guard.
The original native method receiver stays the returned original receiver; no
method alias, ancestor-pn lookup, new hitTest, or forced branch is introduced.
No source clip properties are assigned by the observer. Boundaries inspect the
existing child/parent slots; no synthetic unload event or extra lifecycle is added.

The locked original P-code contains **four eager `Or` opcodes**, not short-circuit
jumps between hitTests. It evaluates each target before its receiver. The new
trace confirms that site1=true does **not** skip sites2–5. Accordingly, s270's
proposed short-circuit precaution must not be interpreted as evidence that this
particular authored expression short-circuits. s270 itself remains untouched.

[original.pcode](original.pcode) and [observed.pcode](observed.pcode) retain the
selected callback only. The analyzer removes only the known observation call
sequences, normalizes Push packing/numeric spelling and compares the complete
remaining instruction sequence **including branch destination indices**. It is
identical: five original hitTest calls, same operands, guards, eager Or chain,
writes, goto and movement. Source rewrite inversion also recovers exact source.
This is a structural preservation check, not proof of wall-clock timing or all
VM internal behavior. No skipped collision site is invented; the pause guard
was true in each observed callback. Other guard outcomes remain unobserved.

## Source-first answers and next discriminator

1. The complete ten-frame Sprite104 source/timeline and frame188 actions remain
   locked in [s270](../s270/README.md); this extension observes the existing
   branches and operands, not a new collision algorithm.
2. Both placements are new, not MOVE. Child frame5 depth2 removal is now bounded
   by the actual goto; parent frame194 depth28 removal remains independently
   bracketed by root slots. No instance identity is inferred from source stamps.
3. Sprite104 stops at1, conditionally goes to5, renames at5 and stops at10.
   Source order and actual before/after records are retained. No label-end exit.
4. Tests enforce locked source, original opcode/control-flow projection, complete
   operand order and separate removal/rename observations. Missing/wrong records,
   altered receiver/guard and `Or` mutations reject. They do not encode a runtime
   eligibility hypothesis as a required result.
5. This run uses the exact s239 case; 122 states match s247. It is not a Godot
   comparison, clock equivalence or full native parity proof.

**Next discriminator:** on this same placement and tape, observe the authored
parent depth28 removal dispatch and correlate direct nested-function invocation
with actual operand lifetime; qualify pass-through timing perturbation before
proposing an eligibility rule. The present outer operand trace does not establish
whether every source path can invoke the nested receiver functions. Do not
substitute ancestor pn, exempt receivers, create source aliases, enlarge boxes,
add hitTests or expand to other chains. No runtime fix is proved here.

## Cost, recovery and reproduction

A new instrumented capture was necessary: locked s247/s270 have no executed
operand records or before/after rename observations. There was **one successful
build and one player launch**. Two pre-build attempts stopped on the archived
absolute music symlink and a wrong root-sample location, before Java/player work.
The final build skips the archived symlink and recreates it against locked music.
FFDec logged its sandboxed logging-directory warning but produced both changed
SWFs; exported opcode evidence and output hashes verify those results.

The first capture command was sandbox-blocked at `ps`, before launch. The
escalated launch completed, but its destination directory was absent at save.
[capture-command.json](capture-command.json) retains exit1 and measured cost.
All lines for the unique run ID were recovered **in original order** from the
account Flash log, without sorting, deduplication or terminal trimming. Strict
full-stream validation passed before creating the new receipt. The full recovered
stream is archived, not just selected rows. [capture-recovery.json](capture-recovery.json)
records the failure and recovery. This limitation is not hidden as an exit0
capture command. No second launch or image export occurred. One mistyped P-code
CLI attempt failed before export; two script-only exports succeeded.

Measured successful build/capture/check costs and session interval are in
[session-timing.json](session-timing.json), [gates.json](gates.json) and
[project-checks.json](project-checks.json). Unmeasured setup costs and person-days
remain unknown.

Portable evidence replay (no player or exports required):

```sh
PYTHONPATH=. python3 evidence/sampling-upgrade/s275/diagnose.py --output /tmp/s275.json
PYTHONPATH=. python3 evidence/sampling-upgrade/s275/diagnose.py --output /tmp/s275-required.json --require-runtime-binding # exit 1
PYTHONPATH=. python3 evidence/sampling-upgrade/s275/diagnose.py --output /tmp/s275-geometry.json --require-geometry # exit 1
python3 -m unittest tools.tests.test_yulong_operand_boundary tools.tests.test_nested_owner_diagnosis tools.tests.test_yulong_k1atm_observer tools.tests.test_sampling_geometry tools.tests.test_sampling_native tools.tests.test_import_guards
python3 tools/verify.py
python3 tools/check_handoff.py
/tmp/bvn-s27-venv/bin/python tools/validate_contracts.py
```

**61 focused tests pass.** Diagnosis/sequence/receipt exit0; binding and unchanged
full geometry exit1. Project integrity/handoff/contracts pass. Restore the build
archive to `/private/tmp/bvn-s275-r03-build`, the raw log and receipt to
`/private/tmp/bvn-s275-r01-capture` for the original-path receipt command in gates.
Do not rewrite receipt paths or hashes. The receipt remains a static source/build
binding, not live loader attestation. For a future capture, choose a fresh run ID
in the isolated builder, a fresh output path, and create the capture directory
before launch; use the flags in the recorded capture command.

Only s275 evidence, its focused test and requested tracking files change.
No shared sampler/strict validator/schema/gameplay/renderer/threshold/baseline
change, production implementation, merge or deployment. Both admission flags
remain false; the pending task is not marked complete.
