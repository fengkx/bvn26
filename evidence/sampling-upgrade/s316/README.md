# s316 — AFTER-s308 rank #8: AImain allocation

Base: origin/master `03b2e5df67adeddfb4a293d7009cc0b885b040d7` (post-s315 squash).
Branch: `feat/s316-aimain-allocation`.
Authority: [AFTER-s308 rank 8](../next-fix-priority-after-s308.md).
[s307 README](../s307/README.md) and [diagnosis](../s307/diagnosis.json) are locked prior.
**Evidence-only, honest-unproved.** `production_admitted=false`;
`native_parity_proven=false`; M0-02 pending; zero product obligations closed.

## Result: native derivation remains blocked

Independent native slot/reference layouts were **not derived**. Actual clearing,
replacement, free and reuse controls with uninterrupted ordered pool generations
remain unproved. The fixed-evidence audit exits 0; all four proof gates exit 1.
No product builds, player launches, process attaches, captures or symbol queries.
The requested native thin cut is not complete; this delivers its bounded evidence
and concrete blocker, not an accepting native resolver or synthetic ledger.

## What is newly audited

[diagnose.py](diagnose.py) reproduces the complete pinned s307 diagnosis (including
recursive prior evidence), then independently parses all 8,290 retained s261
AIREF events and binds the three control records to their complete archived
source expressions. Historical 61 display samples / 122 actor rows on 14 fields
remain prior observations, not a fresh capture.

The new [diagnosis](diagnosis.json) exposes an operand distinction and four
observation intervals. Source lines are in `patches/main/frame_1/DoAction.as`
inside s261's locked `native-build.tar.gz`:

| Event / source | Actual recorded comparison | What it cannot establish |
| --- | --- | --- |
| 21 / line51 | `saved == host.slot`, `host.slot.identity == token`: true,true | No pre-allocation native generation or independent referent |
| 22 / line55 | Same expressions: true,false after remove/create at52–54 | No old-generation end, replacement generation or free/reuse ordering |
| 23 / line59 | `retained == host.slot`, `host.slot.identity == secondToken`: true,false | Operands changed at56–57; line58 deletes only the identity property |

Thus events22/23 have identical booleans but compare different saved values.
They cannot be collapsed into a single reference-retention witness. Creation
at47–50 precedes the first control log; remove/create at52–54 and alias/delete
at56–58 each occur between logs; cleanup at60 follows the final control log.
None has native pool events. Null denotes absent observation, not zero events.

All AIREF sequences1–8290 are contiguous; the audit preserves events24–33
(before/after unload) and the complete root8/root9 window36–48, including
intervening input/intro events. Logger continuity is **not** uninterrupted native
allocation coverage. Sequential AS2 reads are not atomic snapshots. No 0→1 alias,
token-loss identity, unloaded exemption, pointer-only identity or source-route
independence is inferred. This audit adds no new source behavior claim to s307.

## Native qualification and next discriminator

The seven retained native observations remain null. The historical s298 empty
layout/symbol lookups are recursively revalidated, not rerun; their candidate
names neither establish native types nor prove reverse engineering impossible.
The bounded retained inputs supply no byte-bound slot/reference layout or live
pool facility. This is an evidence-set limitation, not a global impossibility
claim or a claim that all binaries were newly searched.

1. Derive native parent/depth occupant and saved AS2 referent separately, retaining
   instruction bytes, relative addresses, layout and live module/owner binding.
   Shared AS2 receiver origin, named slots and imported symbols do not qualify.
2. Begin complete object/pool checkout/return and allocation/destruction/free
   observation before control creation; system malloc/free alone is insufficient.
3. Qualify actual retained-content clearing and same-name/depth replacement with
   independent before/after resolutions. Observe actual deferred-free order;
   do not force removal to mean immediate free.
4. Observe real reuse through uninterrupted generations, then use the unchanged
   s261 input at source-equivalent last-nonzero/first-zero boundaries. A gap or
   unexercised reuse stays unproved.

Steps2–4 are deferred behind step1; there is no qualified facility in this locked
chain that makes a fresh build/launch warranted. No actual native control is
claimed executed by s316.

## Gates and validation

| Mode | Expected exit | Meaning |
| --- | --- | --- |
| Base diagnosis | 0 | Reproducible evidence audit only; both flags false |
| `--require-slot-reference` | 1 | `S316_SLOT_REFERENCE_UNPROVED` |
| `--require-content-clearing` | 1 | `S316_CONTENT_CLEARING_UNPROVED` |
| `--require-replacement` | 1 | `S316_REPLACEMENT_UNPROVED` |
| `--require-allocation-identity` | 1 | `S316_POOL_GENERATIONS_UNPROVED` |

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 evidence/sampling-upgrade/s316/diagnose.py --output /tmp/s316.json
# Add each --require-* flag above separately; each exits 1.
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s316 -p 'test_*.py'
python3 tools/verify.py
python3 tools/check_handoff.py
```

[Gates](gates.json) and [checks](project-checks.json) record actual commands,
exit codes and durations. Tests reject missing/reordered/cross-run logs,
renamed property deletion and changed source operands; they protect audit
boundaries, not hypothetical native behavior. Retained s307/s298/s289 and
allocation/display/sampling/import tests are also run.
[Input hashes](input-sha256.json) lock authority and prior inputs;
[artifact hashes](artifact-sha256.json) cover every s316 file except the index
itself. [Scope audit](scope-audit.json) and [manifest audit](manifest-audit.json)
record the reviewed allowed paths/hash changes. [Timing](session-timing.json)
records measured implementation/check time; initial reading/design and
person-days are unknown.

## Source-first and scope

The five source-first answers remain s307's locked s298/s289/s261 chain:
Yijiao Sprite455 frame1 initCtrl unload; Sprite3 frame1 stop and no frame2
DoAction; retained parent placement; no invented label-end return; source
invariants distinct from native identity; historical same-input AS2 capture
without native allocation proof. This cut changes no mechanism or runtime.

Only s316 and proportionate STATUS/SAMPLING_UPGRADE/tasks/manifest updates.
Empty diff on prior s254–s315 and all other evidence directories; ranks1–7 and9
are not executed. No game/, scripts/, runtime, contracts, shared sampler,
threshold or validator changes. No merge, deployment or product admission.

Validation: **107 tests pass** (10 s316, 10 s307, 10 s298, 6 s289,
71 retained tools). Base diagnosis exits 0; all four proof gates exit 1.
`tools/verify.py`, `tools/check_handoff.py` and diff whitespace checks pass.
