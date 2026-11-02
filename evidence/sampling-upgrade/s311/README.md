# s311 — AFTER-s308 rank #3: Chad activation/value ownership bounds

Base: origin/master `f246bfccdae6e3ea62ec2b701d4d349a01905c7d` (s310 #188).
Branch: `feat/s311-chad-continuation`.
Authority: [AFTER-s308 rank #3](../next-fix-priority-after-s308.md).
**Evidence-only, honest-unproved.** `production_admitted=false`;
`native_parity_proven=false`; M0-02 pending. Zero product obligations closed.
Only rank #3 is executed; ranks 1–2 and 4–9 remain outside this slice.

## Result

[diagnose.py](diagnose.py) pins the entire locked [s303](../s303/README.md)
artifact set and reproduces its diagnosis, recursively checking 9,493 historical
events. No native binary extraction or live observation is added. The new audit
uses previously retained machine bytes to bound **value provenance and local
transfers**, not merely repeat the existing opcode table derivation.
[diagnosis.json](diagnosis.json) retains seven exact byte witnesses, three slot
transfers, six external edges and three separate ownership boundaries.

All addresses below are unslid module-relative machine-code coordinates in the
s303 receipt-pinned Mach-O, UUID `067c4cfe5b2a3424aaa01fae2df056eb`.
They are neither SWF offsets nor live PCs. `frame` below means native rbp,
not an authored AVM activation or timeline frame.

| Bounded relation | Machine-code witness | Limit |
| --- | --- | --- |
| Operand stack candidate | `0x124c2b–0x124cc2` (exclusive end): owner `[frame-0x558]`, count +0x520, storage +0x528 | Owner allocation, scope and activation remain unknown |
| Three transfers | Initial unsigned count n: if n≥1/2/3, read slot n-1/n-2/n-3 into `[frame-0x60]`, `[frame-0x68]`, `[frame-0x548]`; write raw 2 into each consumed slot | Local copy/clear does not prove retain/release or object lifetime; destinations are not named method/receiver/argument count |
| Carrier provenance | `0x12479b–0x1247b5`, `0x124960–0x124982`: r12 follows two +8 reads from `[frame-0x578]`, with null intermediate producing zero; r9 selects r12 or `[frame-0x568]->+0x28` according to byte +0x6a | No equality or ownership join to the stack owner is established |
| Value classification candidate | `0x124982–0x1249bc`: read carrier +0x48/+0xb8; low3==7 dereferences `(value & ~7)+0x18`; low3==2 selects low5, otherwise low3; compare with 10 | Raw masks/constants do not supply AVM type names |
| Second value path | `0x1249bc–0x1249fc`: preceding-byte checks 0x96/0x1c/0x4e, separate unwrap and full-qword comparison with 10 | Full-value comparison is not the earlier masked comparison |
| Helper boundary | `0x1249fc–0x124a66`: save r8/r15d/r9, page-align carrier field address, load page+8, call two external targets, use raw temporary 10 then 0, restore registers | Page-derived arguments alone prove neither GC/barrier semantics nor helper preservation |

The three count guards branch to `0x1264b9`, `0x1264c8`, `0x1264d0`;
the third transfer jumps to `0x1264db`. The second and third conditional jumps
use flags from the preceding decrement/add, preserved by intervening MOVs.
Both helper calls resolve by signed rel32 to `0x98b8e0` and `0x12f580`.
These six target bodies are outside the audited windows. They are explicit
coverage gaps, not inferred returns, unwinds or harmless helpers.

The byte descriptor remains a **third distinct origin**, `[frame-0x160]`.
Its signed extent permits -1, so its pointer cannot prove finite worker bounds.
The local value carrier, stack owner and descriptor are not asserted to be
independent allocations either: their alias/ownership relation is unknown.
The audit leaves defining scope, register4, AVM type names, allocation generation,
activation identity and helper preservation null. It does not decode arbitrary
values, accept caller-supplied memory, or implement a broad interpreter.

## Gates and next prerequisite

| Requirement | Exit | Code |
| --- | --- | --- |
| Reproducible archived layout audit | 0 | `S311_DIAGNOSIS_OK` |
| Qualified activation layout | 1 | `S311_ACTIVATION_LAYOUT_UNPROVED` |
| Qualified value ownership | 1 | `S311_VALUE_OWNERSHIP_UNPROVED` |
| Live module/worker binding | 1 | `S311_LIVE_BINDING_UNPROVED` |
| Measured cursor convention | 1 | `S311_CURSOR_CONVENTION_UNPROVED` |
| One retained authored invocation | 1 | `S311_RETAINED_INVOCATION_UNPROVED` |

Resolve the origins/lifetimes of these candidates and the external helper/exit
paths before live binding. Then independently qualify the live module UUID,
slide and code bytes, loaded worker bytes and finite extent, cursor measurements,
and a retained invocation with defining scope/register4. Only then observe the
three authored instruction boundaries. Static local relations do not advance
that sequence automatically. The 139-byte worker's unique archived body and
589408 next-CallMethod/current-Pop ambiguity remain exactly as in s303.
No CPU-entry-as-AVM proof, pointer-only binding, silence/removal-as-return,
root-worker equivalence or broad interpreter is permitted in diagnosis or docs.

## Source-first and scope

1. Locked s266/s278/s288/s295/s303 source remains Sprite16 frame1 doAllAction,
   called from Sprite607 frame1 depth31 enterFrame; no gameplay change is made.
2. Helper placement is new and linear removal is at frame13. Neither these
   facts nor the copied raw slot values identify an activation lifetime.
3. The authored attack goes to183; predicates/doDropDown remain. Missing logs,
   removal, CPU exits and external branch targets do not prove authored return.
4. Tests lock actual byte operands, guard targets, masks, indirection, transfer
   destinations, helper arguments and custody, including rehashed mutations.
   No speculative gameplay result or guessed tag identity is a test invariant.
5. Only historical native evidence is revalidated; no fresh original/Godot
   same-input comparison exists. Mechanism and parity remain unproved.

Only s311 and proportionate STATUS/SAMPLING_UPGRADE/tasks/manifest updates change.
No edits under s254–s310, game/, scripts/, runtime, contracts, shared sampler,
threshold or validator. Zero builds, player launches, process memory reads,
new captures or images. No other ranks, merge, deployment or production admission.
M0-02 remains pending; delivery of this evidence slice does not close it.

## Reproduce and validation

```sh
PYTHONPATH=. python3 evidence/sampling-upgrade/s311/diagnose.py --output /tmp/s311.json
# Each proof requirement independently expects exit 1:
PYTHONPATH=. python3 evidence/sampling-upgrade/s311/diagnose.py --output /tmp/s311-a.json --require-activation-layout
PYTHONPATH=. python3 evidence/sampling-upgrade/s311/diagnose.py --output /tmp/s311-v.json --require-value-ownership
PYTHONPATH=. python3 evidence/sampling-upgrade/s311/diagnose.py --output /tmp/s311-l.json --require-live-binding
PYTHONPATH=. python3 evidence/sampling-upgrade/s311/diagnose.py --output /tmp/s311-c.json --require-cursor-convention
PYTHONPATH=. python3 evidence/sampling-upgrade/s311/diagnose.py --output /tmp/s311-i.json --require-retained-invocation
PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s311 -p 'test_*.py'
PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s303 -p 'test_*.py'
PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s295 -p 'test_*.py'
PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s288 -p 'test_*.py'
PYTHONPATH=. python3 -m unittest tools.tests.test_chad_native_instruction_diagnosis tools.tests.test_chad_defining_context tools.tests.test_chad_register_control tools.tests.test_as_continuation_discriminator tools.tests.test_chad_lifecycle_observer tools.tests.test_call_exit_diagnosis tools.tests.test_sampling_callsite tools.tests.test_sampling_doaction tools.tests.test_sampling_native tools.tests.test_import_guards
python3 tools/verify.py
python3 tools/check_handoff.py
```

[Gates](gates.json), [checks](project-checks.json), [scope](scope-audit.json),
[manifest audit](manifest-audit.json), [timing](session-timing.json) and
[artifact hashes](artifact-sha256.json) retain actual outcomes. Hash index excludes
itself. Initial reading/design and person-days are unknown; implementation time
excludes later commit/push/PR work. No runtime/contract change requires their suites.

Validation: **138 tests pass** (10 focused, 11 retained s303, 8 retained s295,
4 retained s288, 105 retained tools). Archived diagnosis exits0; all five proof
gates exit1. Integrity, handoff and whitespace checks pass. These green checks
validate the evidence package; they do not prove Chad continuation.
