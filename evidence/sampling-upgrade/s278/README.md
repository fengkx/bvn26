# s278 — Chad native instruction/activation facility (unproved)

Base: master `783e69d7` / #155. Branch: `feat/s278-chad-continuation`.
Exclusive authority: [AFTER-s272 rank 6](../next-fix-priority-after-s272.md).
`production_admitted=false`; `native_parity_proven=false`; M0-02 pending.
Zero product obligations closed. No runtime implementation is justified.

**Native debugger startup works outside the sandbox, but the required AVM1
instruction/activation observation facility is not established.** The successful
CPU entry stop is not an executed Chad instruction. This is an evidence-only
qualification failure with a specific next discriminator, not a proved cut.

## Locked evidence and exact observation sites

[diagnose.py](diagnose.py) reruns unchanged s266 diagnosis, verifies the complete
9,493-event stream against its original receipt hash, checks archived build and
source hashes through the existing s266→s263→s257 audits, and binds the exact
exported instruction windows. [Input pins](input-sha256.json) lock the reused
artifacts. No historical archive, capture, receipt or tape is modified.

| Site | Emitted code | Historical native result | Still missing |
| --- | --- | --- | --- |
| Chad Sprite16 frame1, original conditional parent goto | s257 export lines 4444–4453: label `砍1`, count1, register2 receiver, `gotoAndPlay`, **CallMethod → Pop → Push register5 → Push post → Push 1 → SetMember** | tick10 entry/before; tick11/12 witness before/control=1, post/observerEntry=0 | Executed AVM1 PC, stack, register5 object, defining activation and transition after call |
| s266 authored worker in Sprite60000 | operation **CallMethod → Pop → register4 post SetMember** | retained post=1, removed post=0; independent depth -16383 occupied/empty observations | Same native resolver across both control activations |
| Inherited root-defined worker | Separate defining context | retained/removed post=1/1 | Not equivalent to Chad or authored-child activation |

The post write is **s257 instrumentation**, not original authored gameplay.
Line numbers are exported text coordinates, not byte offsets or native addresses.
The original Chad goto site is in `DefineSprite_16/frame_1/DoAction.as`, called
from Sprite607 frame1 depth31's enterFrame handler. The source has subsequent
predicates and `doDropDown`; no authored return follows this goto. Existing
source/timeline facts remain: new Sprite16 placement, linear removal at frame13,
attack `砍1` at frame183. Skipped-frame execution is not inferred.

The retained control demonstrates that the authored observer can write after
its operation call. It supplies no native activation identifier and does not
prove that Chad executed Pop, returned, unwound or aborted. The existing 122
actor tick/payload rows still match s263; this is not Godot parity.

## Facility attempt and retained failures

[audit_facility.py](audit_facility.py) requires the exact s266 receipt executable
SHA-256 `8d4c1f5934adae809b5f4ce4f6ca7c64d4260df46bb3eb9c41fe32be2ee905be`.
Each directory below contains commands, exit codes, transcript hashes and
measured subprocess times in `audit.json`.

- [Rejected query](rejected-query/audit.json): the first breakpoint regular
  expression used unsupported `(?i)` syntax. Its failure is not evidence of
  missing symbols. Retained unchanged, then corrected.
- [Corrected query](facility/audit.json): module-scoped AVM1/CallMethod/Pop/
  SetMember/dispatch candidate breakpoint resolves **zero locations (pending)**.
  LLDB returns exit0 for creating a pending breakpoint; that is not success at
  the required site. Separate ActionExec and Activation type lookups exit1.
  These name queries do not exhaust stripped-code reverse engineering.
- [Sandbox startup](entry-sandbox/audit.json): `process launch --stop-at-entry`
  fails with lost connection, exit1. No movie was supplied.
- [Unsandboxed startup](entry-unsandboxed/audit.json): the same owned startup
  probe exits0, stops at `dyld_start`, reads x86_64 RIP/RSP/RBP and a one-frame
  native backtrace, then explicitly kills its own process. No movie supplied.
  CPU RIP is not AVM1 PC; CPU RSP is not the AVM1 operand stack. This rules out
  treating the sandbox startup failure as a blanket inability to use LLDB.

Two debugger launch requests, one confirmed entry stop; zero movie captures,
zero new SWF builds. No existing user process was attached, no binary was
patched/re-signed, no security setting changed. The next capture needs a
resolved native adapter first; repeating the old marker capture adds no decisive
evidence. Actual costs are retained, future resolver/capture cost is unknown.

## Next discriminator

1. Resolve a native AVM1 dispatch boundary and activation layout in this exact
   executable. Pin module UUID/relative addresses and instruction bytes, retaining
   the derivation. AS2 export names and pending breakpoints are not that resolver.
2. Restore the s266 build by its documented archive recipe without resealing.
   Bind the **loaded** action buffer to the archived Chad function bytes and
   locate the goto CallMethod, next Pop and register5 SetMember by decoded byte
   boundaries. File hashes alone are not live buffer identity. Record actual
   opcode cursor convention (current/next), operand stack bounds/types, witness
   object/register and defining activation identity/lifetime.
3. Qualify the same resolver first on s266's retained authored control: observe
   the call, following Pop and register4 post write in the same activation,
   consistent with independent retained slot and post=1. Observe the removed
   control separately. Root-defined workers do not substitute for either.
4. In one unchanged-tape Chad run, observe before CallMethod and every executed
   transition to Pop/write or an actual invalidation/unwind boundary. Record
   nested activation changes and resume destination, avoiding CPU-return-as-AS-
   return. If the next opcode is not observed, preserve unknown execution;
   absence and slot removal do not manufacture an after-event.

Until those records exist, the requirement gate exits1. This slice adds no
accepting native-trace schema or broad interpreter. No removal-as-return,
root-worker equivalence, fabricated after-event, threshold relaxation or gameplay
rewrite is implemented.

## Source-first and scope

The five source-first questions inherit s266's explicit source/timeline/control
answers; the same-input **native instruction** comparison is still missing.
No runtime change is authorized by these observations. All other ranks,
s254–s277, priority documents, strict validators, production files and contracts
remain unchanged. Only s278 evidence, focused tests and requested tracking files
change. No merge or deployment.

## Reproduce

```sh
PYTHONPATH=. python3 evidence/sampling-upgrade/s278/diagnose.py --output /tmp/s278.json
PYTHONPATH=. python3 evidence/sampling-upgrade/s278/diagnose.py --output /tmp/s278-required.json --require-native-continuation # expected exit 1
python3 -m unittest tools.tests.test_chad_native_instruction_diagnosis tools.tests.test_chad_defining_context tools.tests.test_chad_register_control tools.tests.test_as_continuation_discriminator tools.tests.test_chad_lifecycle_observer tools.tests.test_call_exit_diagnosis tools.tests.test_sampling_callsite tools.tests.test_sampling_doaction tools.tests.test_sampling_native tools.tests.test_import_guards
python3 tools/verify.py
python3 tools/check_handoff.py
```

Portable diagnosis consumes retained observations; it does not launch LLDB.
To repeat the facility queries use `audit_facility.py --output /tmp/s278-facility`
with a fresh path. `--launch` requests the bounded no-movie entry stop and kill;
its successful retained run used sandbox escalation. Do not overwrite historical
observations with different host results. Receipt/product commands inherit the
s266 restore recipe, with s278 output paths; no receipt repair.

Actual gate exits, focused test count and validation costs are retained in
[gates.json](gates.json) and [project-checks.json](project-checks.json).
[Scope audit](scope-audit.json), [manifest audit](manifest-audit.json) and
[session timing](session-timing.json) document the delivery boundary.

Validation: **105 focused tests pass**; original s266 receipt, diagnosis, integrity,
handoff and contracts exit0. Native continuation, lifecycle, callsite and full-AS
requirements exit1 (594 unvisited / 415 uninstrumented unchanged). The first
contract command used an old environment missing jsonschema (exit1, retained);
rerunning with the existing s276 validation environment passes. No Godot test
applies because no Godot implementation changed.
