# s288 — Chad byte-pinned continuation prerequisite (honest-unproved)

Base: `origin/master` `c0bb50ee` (#165, s287 squash merge).
Branch: `feat/s288-chad-continuation`.
Exclusive authority: [AFTER-s281 rank #7](../next-fix-priority-after-s281.md).
`production_admitted=false`; `native_parity_proven=false`; M0-02 pending.
Evidence-only; zero product obligations closed.

**The archived instruction bytes and containing function definitions are now
located; executed AVM1 instructions and defining activation remain unproved.**
Both requirement gates exit 1 with `S288_NATIVE_CONTINUATION_UNPROVED`.

## What was checked

[diagnose.py](diagnose.py) replays the unchanged [s278 diagnosis](../s278/README.md)
and its s266 → s263 → s257 provenance checks. The complete 9,493-event stream,
receipt hash, archived SWFs, source pins and retained/removed controls are
checked again. No historical capture or receipt is edited or resealed.

The new bounded static decoder walks SWF tags and action record boundaries,
resolves the constant-pool operands in the two locked s278 windows, and requires
one matching window inside a function definition. It is not an interpreter and
executes no opcode. The archive member SHA-256, DoAction digest, function header,
body digest, window digest and individual bytes are in [diagnosis.json](diagnosis.json).
[Input pins](input-sha256.json) also bind the selected archives and authority.

All offsets below are **uncompressed SWF file coordinates**, not loaded action
buffer pointers, executed AVM1 PCs or native code addresses.

| Site | Definition / body | CallMethod | Pop | Register target push / SetMember |
| --- | --- | --- | --- | --- |
| Chad Sprite16 frame1, `doAllAction` | 27876 / 27907, body length 1360, register count 9 | 28257 (`52`) | 28258 (`17`) | register5 at 28259 / 28277 (`4f`) |
| s266 authored Sprite60000 frame1 worker | 589258 / 589289, body length 139, register count 6 | 589407 (`52`) | 589408 (`17`) | register4 at 589409 / 589427 (`4f`) |

Chad bytes come from s257's archived instrumented `game/fighter/chad.swf`,
which s266 retains unchanged; worker bytes come from s266's extension
`game/main.swf`. The Chad `post` write is s257 instrumentation, not authored
gameplay. `SetMember` writes the witness object's member using a register-held
reference; it is not a StoreRegister instruction. The static function definition
is not the identity or lifetime of a live defining activation.

The retained authored control has post=1; the removed authored control has
post=0, with independent occupied/empty slot observations. Chad's later
post/observerEntry remain 0. Root-defined dynamic controls have post=1/1 and
remain separate. These observations neither prove removal-as-return nor
establish root-worker equivalence. The 122 actor rows still match s263, which
is not native/Godot parity.

## Blocking boundary and next discriminator

The s278 CPU entry stop and zero-location AVM1 breakpoint resolver are retained
historical observations, not new facility attempts. No new player launch,
attach, SWF build or movie capture was made. Repeating CPU entry or marker
captures would not supply the missing instruction/activation join. Name-query
failure does not prove stripped-code analysis impossible.

A decisive next observation requires a native dispatch/activation resolver for
the receipt-pinned executable, with module identity, relative addresses, bytes
and derivation. Bind the actual loaded action buffer to the archived function
bytes above; measure whether the cursor names the current or next opcode.
First observe the retained authored worker's CallMethod, Pop and register4
post write in one identified activation, with operand stack and witness mapping.
Keep the removed control separate. Then observe Chad's CallMethod and every
executed transition to Pop/register5 write, or an actual invalidation/unwind and
resume destination, with unchanged tape. CPU return, empty slot and silence do
not substitute for this record. Loaded buffers, stack and activation records
are explicitly null in this diagnosis. No new accepting trace schema is added.

## Scope and source-first

The five source-first answers remain those locked by s266/s278: Sprite16 frame1
DoAction called by Sprite607 frame1 depth31 enterFrame; new placement, linear
frame13 removal, attack label at frame183; subsequent predicates/doDropDown
rather than an authored return; retained source/control invariants; same-input
native instruction comparison still absent. Static location does not answer
that final question, so no runtime implementation is justified.

Only s288 and proportionate tracking files change. No ranks 1–6 or 8–9 are
executed. No edits under s254–s287, game/scripts, runtime, contracts, shared
samplers, thresholds or validators. No broad interpreter, fabricated after-event,
production admission, merge or deployment.

## Reproduce

```sh
PYTHONPATH=. python3 evidence/sampling-upgrade/s288/diagnose.py --output /tmp/s288.json
PYTHONPATH=. python3 evidence/sampling-upgrade/s288/diagnose.py --output /tmp/s288-required.json --require-native-continuation # expected exit 1
PYTHONPATH=. python3 evidence/sampling-upgrade/s288/diagnose.py --output /tmp/s288-control.json --require-retained-activation # expected exit 1
PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s288 -p 'test_*.py'
PYTHONPATH=. python3 -m unittest tools.tests.test_chad_native_instruction_diagnosis tools.tests.test_chad_defining_context tools.tests.test_chad_register_control tools.tests.test_as_continuation_discriminator tools.tests.test_chad_lifecycle_observer tools.tests.test_call_exit_diagnosis tools.tests.test_sampling_callsite tools.tests.test_sampling_doaction tools.tests.test_sampling_native tools.tests.test_import_guards
python3 tools/verify.py
python3 tools/check_handoff.py
```

[Gates](gates.json), [project checks](project-checks.json), [scope audit](scope-audit.json),
[manifest audit](manifest-audit.json) and [timing](session-timing.json) retain
results and measured costs. Initial reading/design and future resolver/capture
costs are unmeasured; person-days remain unknown. No Godot or contract tests
apply because implementation and contracts are unchanged.

Validation: **109 tests pass** (4 new boundary tests + 105 retained tests).
Diagnosis, integrity, handoff and diff checks exit 0; both proof requirements
exit 1 as expected.
