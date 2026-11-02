# s298 — AFTER-s290 rank #8 AImain allocation (evidence-only, honest-unproved)

Base: origin/master `0038929ce894539da159afe3331ba0a3e8e2da25` (s297 #175).
Branch: `feat/s298-aimain-allocation`.
Exclusive authority: [AFTER-s290 rank #8](../next-fix-priority-after-s290.md).
`production_admitted=false`; `native_parity_proven=false`; M0-02 pending.
Zero product obligations closed.

**One native slot/saved-reference pair remains unresolved; actual clearing,
replacement, free and reuse controls have no ordered native generations.**
The four proof gates exit 1. Diagnosis exit 0 only means the evidence audit
reproduced, not that the requested mechanism was proved.

## Bounded investigation

[diagnose.py](diagnose.py) reproduces the entire locked [s289 diagnosis](../s289/README.md)
and requires exact equality. [Input pins](input-sha256.json) bind that diagnosis,
its code, the historical player identity and the ranking authority. Recursive
checks retain the s279/s267/s261 provenance, 8,290 events, 61 display samples,
and 122 actor rows matching s255 on 14 fields. These are historical observations,
not new captures or native allocation proof. No old evidence was changed.

The seven archived AS2 source bindings and all events36–48 are retained in
[diagnosis.json](diagnosis.json). Root8 reports frame1/total2 and root9 reports
frame0/total0 at `_level0.game.p1.mc.AImain`, depth -16383. Those paths, depths,
sequential object reads and AS2 equalities do not resolve native referents.
Contiguous logged events do not establish complete native lifecycle coverage.

[facility.json](facility.json) records four fresh, bounded LLDB queries on the
receipt-matching executable, SHA-256
`8d4c1f5934adae809b5f4ce4f6ca7c64d4260df46bb3eb9c41fe32be2ee905be`:

| Query | Result | Missing prerequisite |
| --- | --- | --- |
| Type `DisplayObjectContainer` | Empty lookup, exit 1 | Parent/depth slot layout |
| Type `MovieClipObject` | Empty lookup, exit 1 | Saved AS2 reference layout |
| `GetInstanceAtDepth`, `GetChildAtDepth`, `ResolveMovieClip`, `MovieClipReference` symbols | Empty lookup, exit 1 | Independent native resolvers |
| `AllocMovieClip`, `FreeMovieClip`, `DisplayObjectPool`, `DestroyMovieClip` symbols | Empty lookup, exit 1 | Object/pool lifetime hooks |

These candidate names are **search hypotheses**, not known player class names.
Every transcript reaches successful x86_64 target creation before the empty
lookup. The binary was hashed before querying. Empty lookups do not prove that
objects or resolvers are absent, nor that stripped-binary analysis is impossible.
No allocator import inventory is offered as runtime proof. No player launch,
process attach, SWF build or fresh capture occurred.

## Controls and ordered generations

The retained AS2 controls at events21–23 are `retained,true,true`,
`replaced,true,false`, and `retained_content_deleted,true,false`. They precede
the target unload and live outside the game tree. Source statements establish
`removeMovieClip`, same-name/depth creation and `delete replacement.identity`.
**Property deletion is not content clearing.** Neither the equal results nor
token loss distinguish native lifetime, retention, replacement or saved referents.

The report separates three still-unqualified control obligations:

- Actual retained-content clearing needs independently resolved slot and saved
  referent before/after, the real clear operation, and continuous pool lifetime
  evidence establishing retention. Pointer equality cannot establish it.
- Same-name/depth replacement needs the old generation, observed remove and
  actual destruction/free ordering, the new generation and independently resolved
  saved referent. Removal must not be assumed to free an object immediately.
- Free/reuse needs coverage started before control allocation and an observed
  old-generation end preceding a new generation at the reused address. Generic
  malloc/free interception may miss internal pools. Unexercised reuse, gaps or
  unknown ordering remain unproved; never invent generations from pointer values.

These are requirements for a future experiment, not a synthetic ledger or an
accepting trace schema. All seven native observation fields remain null.
Native controls were not executed because their resolver/coverage prerequisite
is missing. The fixed-evidence diagnostic cannot accept a new capture by changing
flags or metadata; new native evidence requires independent analysis.

The next discriminator remains s289's: derive byte-pinned parent/depth and saved
reference resolvers with independent layouts and live provenance on the pinned
player; qualify complete object/pool coverage on actual controls, then capture
unchanged s261 input at source-equivalent boundaries. Keep run/source/engine
hashes and actual event order. Root8/9 are historical observations, not prescribed
future capture roots.

## Gates, source-first and scope

| Requirement | Exit | Code |
| --- | --- | --- |
| Evidence audit | 0 | `S298_DIAGNOSIS_OK` |
| Native slot/saved reference | 1 | `S298_SLOT_REFERENCE_UNPROVED` |
| Actual retained-content clearing | 1 | `S298_CONTENT_CLEARING_UNPROVED` |
| Replacement generations | 1 | `S298_REPLACEMENT_UNPROVED` |
| Allocation/free/pool reuse identity | 1 | `S298_POOL_GENERATIONS_UNPROVED` |

No pointer-only identity, 0→1 alias, token-loss identity, unloaded exemption or
import-inventory-as-runtime proof. These exclusions are explicit in the diagnosis.
Only s298 and proportionate tracking files change. No edits under s254–s297,
game/scripts, runtime, contracts, shared sampler, thresholds or validators.
Ranks 1–7 and 9 are not executed. No deployment or production admission.

Source-first answers stay locked to s289/s261: Yijiao Sprite455 frame1 initCtrl
unload, Sprite3 frame1 stop with no frame2 DoAction, retained parent placement,
no invented label-end return, source invariants distinguished from allocation
identity, and historical same-input AS2 observations without native identity.
Incomplete native evidence authorizes no runtime implementation or completed
product task.

## Reproduce and validation

```sh
PYTHONPATH=. python3 evidence/sampling-upgrade/s298/diagnose.py --output /tmp/s298.json
# Each requirement independently expects exit 1:
PYTHONPATH=. python3 evidence/sampling-upgrade/s298/diagnose.py --output /tmp/s298-slot.json --require-slot-reference
PYTHONPATH=. python3 evidence/sampling-upgrade/s298/diagnose.py --output /tmp/s298-clear.json --require-content-clearing
PYTHONPATH=. python3 evidence/sampling-upgrade/s298/diagnose.py --output /tmp/s298-replace.json --require-replacement
PYTHONPATH=. python3 evidence/sampling-upgrade/s298/diagnose.py --output /tmp/s298-generation.json --require-allocation-identity
PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s298 -p 'test_*.py'
PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s289 -p 'test_*.py'
PYTHONPATH=. python3 -m unittest tools.tests.test_aimain_native_resolver_gap tools.tests.test_aimain_allocation_identity tools.tests.test_aimain_content_clearing tools.tests.test_aimain_unload_identity tools.tests.test_display_source_frame_diagnosis tools.tests.test_sampling_native tools.tests.test_sampling_display tools.tests.test_display_completion_default tools.tests.test_import_guards
python3 tools/verify.py
python3 tools/check_handoff.py
```

[Gates](gates.json), [project checks](project-checks.json),
[scope audit](scope-audit.json), [manifest audit](manifest-audit.json) and
[session timing](session-timing.json) record actual outcomes and measured costs.
Initial reading/design and person-days remain unknown. No Godot or contract check
applies to this evidence-only change. Tests protect rejection boundaries and
historical evidence; they do not demonstrate native allocation behavior.

Validation: **87 tests pass** (10 new, 6 retained s289, 71 retained tests).
Integrity, handoff and diff checks pass; all four proof requirements retain exit 1.
