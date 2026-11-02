# s307 — AFTER-s299 rank #8 AImain allocation (evidence-only, honest-unproved)

Base: origin/master `87b844c6` (s306 #184).
Branch: `feat/s307-aimain-allocation`.
Authority: [AFTER-s299 rank #8 only](../next-fix-priority-after-s299.md).
`production_admitted=false`; `native_parity_proven=false`; M0-02 pending.
Zero product obligations closed.

**Independent native slot/saved-reference resolvers were not derived.** Actual
clearing, replacement, free and reuse still lack complete ordered pool generations.
All four proof gates exit 1. Audit exit 0 means reproducible diagnosis only.

## What this cut adds

[diagnose.py](diagnose.py) reproduces the complete locked [s298 diagnosis](../s298/README.md)
with exact equality. [Input hashes](input-sha256.json) bind its code, report,
facility and recursive pins, the ranking authority and the s261 source archive.
The 8,290 events, 61 display samples and 122 actor rows on 14 fields are historical;
there is no fresh capture. No old evidence is edited.

Instead of repeating empty symbol queries, this cut audits the entire archived
`s261Describe`, `s261Observe` and `s261Controls` functions. [Source bounds](source-bounds.json)
pin the member and complete function ranges; [diagnosis](diagnosis.json) retains
every line, all explicit writes to the three saved globals, the distinct read
routes, and control operations/logs in source order. This is a source-level
resolver dependency audit, not a native resolver implementation or qualification.

All line numbers below refer to `patches/main/frame_1/DoAction.as` inside the
locked s261 archive, not production source:

| Route / operation | Bound evidence | Limit |
| --- | --- | --- |
| Saved reference | line23 saves receiver; line32 reads the global | AS2 value semantics do not reveal the native referent |
| Depth slot | lines24–25 save receiver parent/depth; lines31/33 query that slot | Different expression from saved reference, but shared receiver origin; no native parent/depth layout |
| Named slot | line34 reads parent.AImain | Neither an independent native resolver nor allocation identity |
| Observer | lines4–15 enumerate/sort children and coerce/read properties; lines35–39 emit sequential logs | Not an atomic native snapshot; no observer neutrality claim |
| Remove / replace | lines52–53 between control logs51/55 | Source operation order; no observed destruction/free/pool order |
| “Content deleted” | lines56–58 alias replacement, save its property, delete replacement.identity; log59 | Property deletion only, not actual content clearing |
| Cleanup | line60 removes host after final control log | No post-cleanup lifetime witness |

The full member contains exactly one explicit assignment to each saved receiver,
parent and depth global. This bounded syntactic fact does not exclude dynamic or
native mutation, path retargeting, or alias semantics. Log agreement, path/depth,
frame0/total0 and token loss do not manufacture native identities. The historical
root8/root9 window is retained unchanged, including all events36–48.

## Unmet native qualification

Seven native observations remain null; three retained control obligations remain
unqualified. No accepting synthetic ledger or configurable proof flag is added.
The fixed-evidence diagnostic cannot admit a new native trace without independent
analysis. Source bounds do not establish live code/module identity.

- Slot/reference: need byte-bound native layouts and independent live resolution
  of the parent/depth occupant and saved AS2 referent at the same source boundary.
- Actual content clearing: need the real clear operation, before/after independent
  resolutions, and uninterrupted object/pool coverage establishing retention.
- Replacement: need observed old/new generations and independent saved-reference
  resolution. Removal does not imply immediate destruction/free; record actual
  ordering, including deferred free, without forcing a guessed lifecycle.
- Free/reuse: coverage must begin before allocation, include internal pool
  checkout/return as well as destruction/free, and continue through observed reuse.
  Pointer reuse is not generation reuse. Unexercised reuse and gaps remain unproved.

The archive supplies none of the native layouts, loaded-module bindings or pool
ledger needed to discharge those obligations. This is a concrete evidence blocker,
not proof that native reverse engineering is impossible. No new player launch,
attach, build, capture, symbol-name query or import inventory was performed.
The next discriminator remains byte-pinned native resolver derivation and live
pool-aware qualification, followed by unchanged-input observation. The proposed
native controls were not executed because their prerequisites remain absent.

## Gates and reproduction

| Requirement | Exit | Code |
| --- | --- | --- |
| Evidence audit | 0 | `S307_DIAGNOSIS_OK` |
| Independent slot/saved reference | 1 | `S307_SLOT_REFERENCE_UNPROVED` |
| Actual retained-content clearing | 1 | `S307_CONTENT_CLEARING_UNPROVED` |
| Replacement generations | 1 | `S307_REPLACEMENT_UNPROVED` |
| Complete allocation/free/pool reuse | 1 | `S307_POOL_GENERATIONS_UNPROVED` |

```sh
PYTHONPATH=. python3 evidence/sampling-upgrade/s307/diagnose.py --output /tmp/s307.json
# Each independently expects exit 1:
PYTHONPATH=. python3 evidence/sampling-upgrade/s307/diagnose.py --output /tmp/s307.json --require-slot-reference
PYTHONPATH=. python3 evidence/sampling-upgrade/s307/diagnose.py --output /tmp/s307.json --require-content-clearing
PYTHONPATH=. python3 evidence/sampling-upgrade/s307/diagnose.py --output /tmp/s307.json --require-replacement
PYTHONPATH=. python3 evidence/sampling-upgrade/s307/diagnose.py --output /tmp/s307.json --require-allocation-identity
PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s307 -p 'test_*.py'
PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s298 -p 'test_*.py'
PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s289 -p 'test_*.py'
PYTHONPATH=. python3 -m unittest tools.tests.test_aimain_native_resolver_gap tools.tests.test_aimain_allocation_identity tools.tests.test_aimain_content_clearing tools.tests.test_aimain_unload_identity tools.tests.test_display_source_frame_diagnosis tools.tests.test_sampling_native tools.tests.test_sampling_display tools.tests.test_display_completion_default tools.tests.test_import_guards
python3 tools/verify.py
python3 tools/check_handoff.py
```

[Gates](gates.json), [checks](project-checks.json), [scope](scope-audit.json),
[manifest audit](manifest-audit.json) and [timing](session-timing.json) retain actual
outcomes. Tests protect evidence/rejection boundaries, not native allocation
behavior. Initial exploration/design and person-days remain unknown.

## Source-first and scope

The five source-first answers remain locked to s298/s289/s261: Yijiao Sprite455
frame1 initCtrl unload; Sprite3 frame1 stop and absent frame2 DoAction; retained
parent placement; no invented label-end return; source invariants separate from
native identity; historical same-input AS2 evidence without allocation proof.
Missing native evidence authorizes neither runtime implementation nor completion.

No pointer-only identity, 0→1 alias, token-loss identity, unloaded exemption or
import inventory as runtime proof. Only s307 and proportionate tracking/manifest
files change. No edits under s254–s306, game/, scripts/, runtime, contracts, shared
sampler, thresholds or validators. Ranks1–7 and9 are not executed. No merge,
deployment or production admission. M0-02 stays pending.

Validation: **97 tests pass** (10 focused, 10 retained s298, 6 retained s289,
71 retained allocation/display/sampling tests). Integrity, handoff and diff checks
pass; all four proof requirements retain exit 1.
