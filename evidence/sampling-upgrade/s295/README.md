# s295 — AFTER-s290 rank #5: Chad continuation resolver

Base: origin/master `0f6610ab` (s294 #172). Branch: `feat/s295-chad-continuation`.
Exclusive authority: [AFTER-s290 rank #5](../next-fix-priority-after-s290.md).
**Evidence-only, honest-unproved.** `production_admitted=false`;
`native_parity_proven=false`; zero product obligations closed; M0-02 pending.

## Result and blocking boundary

[diagnose.py](diagnose.py) exactly reproduces the locked [s288 diagnosis](../s288/README.md),
including 9,493 historical events. Three fresh LLDB metadata queries against the
s266 receipt-pinned executable look for ActionBuffer, ActionBufferData and
buffer/execution/activation symbols. All return exit1 with no matches; exact
commands, transcripts, binary hash and measured costs are in [facility.json](facility.json).
These are new static queries, not new player launches, memory reads or captures.
Name-query failure does not prove stripped-code analysis impossible.

The requested loaded-buffer/current-or-next-cursor/retained-activation join is
**not resolved**. No instruction observation follows an unqualified resolver.
There is no loaded buffer base/extent, dispatch PC, cursor convention, operand
stack, register4 witness or native retained activation in this evidence.

## Bounded cursor audit

The archived s266 Sprite60000 frame1 worker body is independently extracted and
hash-checked against s288. Its 139 complete bytes occur once in that archived
SWF. This is archive uniqueness, not memory uniqueness or invocation identity.
Full bytes and candidate coordinates are in [diagnosis.json](diagnosis.json).

| Instruction | Current file offset | Next file offset | Current / next body-relative offset |
| --- | --- | --- | --- |
| CallMethod (`52`) | 589407 | 589408 | 118 / 119 |
| Pop (`17`) | 589408 | 589409 | 119 / 120 |
| SetMember (`4f`) | 589427 | 589428 | 138 / 139 |

These are **uncompressed file offsets, not loaded addresses or executed PCs**.
At 589408, a next-cursor interpretation of CallMethod and a current-cursor
interpretation of Pop coincide. Reading a byte or relocating the body cannot
choose the convention. The last next offset is the function body's end; it
is not evidence of an executed return. SetMember writes the member through a
register4-held witness reference; it is not StoreRegister.

The retained and removed authored controls call the same static worker body.
Historical post=1/0 and occupied/empty-slot markers stay separate; they do not
identify a live native activation or prove removal-as-return. Root-defined
controls remain separate, with no root-worker equivalence claim. Chad's post=0
and observerEntry=0 remain silence, not proof of return or invalidation. The
122 equal historical actor rows are a comparison to s263, not native parity.

## Gates and next observation

Each requirement exits 1, even though the archival diagnosis itself exits 0:

- `S295_LOADED_BUFFER_UNPROVED`: no loaded bytes/extent bound to archived body.
- `S295_CURSOR_CONVENTION_UNPROVED`: no measured current/next convention.
- `S295_RETAINED_ACTIVATION_UNPROVED`: no retained native invocation identity,
  defining scope, operand stack and register4 witness join.
- `S295_INSTRUCTION_BOUNDARIES_UNPROVED`: no three executed boundaries in that
  single qualified retained activation.

Next, derive the native dispatch and activation layout from the receipt-pinned
executable, retaining module identity, relative addresses, bytes and derivation.
Bind actual loaded bytes and extent to the archived worker; measure cursor
convention; identify one retained authored invocation with its scope, witness and
stack. Only then observe CallMethod, Pop and SetMember. Keep the removed control
separate. Chad continuation requires a later qualified observation of its call
and every executed transition, or an actual invalidation/unwind and resume
destination with the unchanged tape. CPU entry/return, silence and empty slots
cannot substitute. No accepting trace schema or broad interpreter is introduced.

## Source-first and scope

1. Source remains s266/s278/s288: Sprite16 frame1 doAllAction, called from
   Sprite607 frame1 depth31 enterFrame. No new gameplay behavior is inferred.
2. The helper is a new placement, with linear frame13 removal; static body
   identity is not placement or activation lifetime.
3. The attack goes to frame183; subsequent predicates/doDropDown are retained,
   without synthesizing an authored return from missing observations.
4. Tests protect source-bound byte coordinates, cursor ambiguity, separate
   controls and rejection of corrupted inputs. No guessed outcome is asserted.
5. Locked same-input native history is revalidated, but no new native instruction
   comparison or Godot run exists. Runtime implementation remains unauthorized.

Only s295 and proportionate tracking/manifest updates change. Ranks 1–4 and 6–9
are not executed. s254–s294 trees, game/scripts, runtime, contracts, shared
samplers, thresholds and validators remain unchanged. No CPU-entry-as-AVM proof,
silence/removal-as-return, root-worker equivalence, broad interpreter, production
admission, merge, deployment or default rollout.

## Reproduction

```sh
PYTHONPATH=. python3 evidence/sampling-upgrade/s295/diagnose.py --output /tmp/s295.json
PYTHONPATH=. python3 evidence/sampling-upgrade/s295/diagnose.py --output /tmp/s295-buffer.json --require-loaded-buffer # exit1
PYTHONPATH=. python3 evidence/sampling-upgrade/s295/diagnose.py --output /tmp/s295-cursor.json --require-cursor-convention # exit1
PYTHONPATH=. python3 evidence/sampling-upgrade/s295/diagnose.py --output /tmp/s295-activation.json --require-retained-activation # exit1
PYTHONPATH=. python3 evidence/sampling-upgrade/s295/diagnose.py --output /tmp/s295-boundaries.json --require-instruction-boundaries # exit1
PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s295 -p 'test_*.py'
PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s288 -p 'test_*.py'
PYTHONPATH=. python3 -m unittest tools.tests.test_chad_native_instruction_diagnosis tools.tests.test_chad_defining_context tools.tests.test_chad_register_control tools.tests.test_as_continuation_discriminator tools.tests.test_chad_lifecycle_observer tools.tests.test_call_exit_diagnosis tools.tests.test_sampling_callsite tools.tests.test_sampling_doaction tools.tests.test_sampling_native tools.tests.test_import_guards
python3 tools/verify.py
python3 tools/check_handoff.py
```

The optional `audit_facility.py` requires the exact receipt-pinned executable and
LLDB; it performs no launch. Retained diagnosis replay uses archived transcripts
and does not require that local installation. Rerunning facility queries changes
custody artifacts and requires an explicit evidence review before repinning.

[Gates](gates.json), [project checks](project-checks.json), [scope](scope-audit.json),
[manifest audit](manifest-audit.json) and [session timing](session-timing.json)
retain verification and measured effort. Initial reading/design, future resolver
cost and person-days remain unknown. No runtime/contract changes require Godot or
contract tests.

Validation: **117 tests pass** (8 new, 4 retained s288, 105 retained tools).
All four proof requirements exit1; archival diagnosis exits0.
