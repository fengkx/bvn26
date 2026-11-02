# s300 — Post-s299 rerank + rank1 body-push initialization dataflow

Base: current origin/master `7b214c7f333c4dd33f39cfb7e27b1251e37ab981`
(s299 #177). Branch: `feat/s300-after-s299-rerank`.
Authority: [AFTER-s299 rank #1](../next-fix-priority-after-s299.md).
**Only rank 1 is executed in s300. Ranks 2+ are planning only.**
`production_admitted=false`; `native_parity_proven=false`; M0-02 pending.
Evidence-only; zero product obligations closed. s291–s299 deliveries stay closed.

## Ranking and exclusive result

[Ranking pins](ranking-basis-sha256.json) bind s282–s299 READMEs/diagnoses and
all prior priority tables. Body-push has a new finite discriminator in s291's
four explicit initialization deletions. Digit entry remains an upstream scene
prerequisite; Yulong's new complete function boundaries move it above Chad and
terminal completion. s293's independent pair is proved and is not repeated;
terminal ownership remains a separate gap. Ranking is not based on green gates.
No rank2+ experiment, facility query or capture was executed.

[diagnose.py](diagnose.py) replays unchanged s291 → s283 → s273 → s264,
including 5,437 historical events, and requires the complete locked s291 result.
JSON object keys alone are canonicalized for s291's integer register map; no
values, arrays or observations are normalized. [Input pins](input-sha256.json)
bind the authority, old code/diagnoses and complete exported pcode.

The **new** audit traverses the finite product of each complete archived CFG
and its last explicit StoreRegister for four candidate registers. It follows
both successors without assuming branch feasibility, converges across loops,
and records a concrete source-node path for every reaching definition. Entry
values use the sentinel -1; they are not assumed undefined. Calls remain the
archived CFG's nodes: this is not an interpreter, stack analysis or model of
exceptions, reentrancy, hidden activation access or native dispatch.

| Candidate register → original | Candidate initialization StoreRegister | Candidate reads → reaching explicit stores |
| --- | --- | --- |
| 7 → 8 | 234 | 355 → 353; 366 → 353 or 361 |
| 8 → 5 | 237 | 370 → 368; 379 and 388 → 368 or 376 |
| 9 → 11 | 240 | 396 → 381 |
| 12 → 9 | 432 | 447 and 478 → 444 |

All indices are **expanded archived pcode node indices**, not byte offsets,
loaded addresses, native PCs, frames or observed execution order. The full
original and candidate read sets, all reaching definitions, witness paths and
mapped correspondence are retained in [diagnosis.json](diagnosis.json).

Within this explicit graph, none of the four initializations or entry values
reaches any of the eight reads. Every read and reaching non-initialization store
maps to its original counterpart. This proves the bounded **static overwrite
property**, not safe removal of those instructions in a running activation.
The existing graph is verified in full before its correspondence is used; no
source, candidate build, erasure rule or old evidence is modified.

## Honest-unproved boundary

All of s291's four semantic assumptions remain unproved. This cut narrows the
initialization assumption to activation-visible behavior beyond explicit reads;
it does not discharge it. Different function headers are retained verbatim.
Live preload/scope binding, helper identity and mutation/exception/reentrancy/
lifetime/scheduling effects, double-Not coercion and independent observer-off/on
controls remain missing. Historical callsite execution is **null**, not false.
No geometry ineligibility or receiver exemption follows.

| Requirement | Exit | Code |
| --- | --- | --- |
| Reproducible archival/dataflow audit | 0 | `S300_DIAGNOSIS_OK` |
| Complete activation preservation | 1 | `S300_ACTIVATION_PRESERVATION_UNPROVED` |
| Observer qualification | 1 | `S300_OBSERVER_UNPROVED` |
| External callsite execution | 1 | `S300_EXTERNAL_CALLSITE_UNPROVED` |

The diagnostic is fixed-evidence analysis, not an accepting runtime trace schema.
New observations require independent qualification, not changed flags or counters.
Next: qualify header/preload/scope binding and activation-visible erasure before
installing a helper or attempting natural executed/skipped paired controls.

## Source-first and scope

1. Source callback/caller and empty frame4–7 map remain locked in s273; s283's
   full exports establish guards and target-before-receiver order. This audit
   uses the complete original/candidate functions, including earlier/later effects.
2. Sprite638 is a new depth1 placement, not MOVE. Existing body/P1 bdmn placement
   and initialization markers are historical facts, not live operand identity.
3. All six returns, branch successors and terminal function edges stay in the
   locked graph. No label-end return or invented timeline transition is added.
4. Tests check source-bound reads/stores, real bypass mutations, full graph and
   hash rejection, witness paths and an independent backward definition walk.
   Two explicitly synthetic graph tests check loop/unreachable-node handling;
   they assert no Flash schedule or gameplay outcome.
5. Historical native same-input observations are revalidated only. There is no
   new original/Godot comparison or runtime implementation authorization.

Only the new authority, s300 and proportionate tracking/manifest updates change.
No edits under s254–s299; no game/scripts, runtime, contracts, shared sampler,
threshold or validator changes. No helper installation, extra hitTest, early
initialization, receiver exemption, tick41 or collision rollout. Zero builds,
player launches, captures and images; no deployment or merge.

## Reproduce and checks

```sh
PYTHONPATH=. python3 evidence/sampling-upgrade/s300/diagnose.py --output /tmp/s300.json
# Each requirement independently expects exit 1:
PYTHONPATH=. python3 evidence/sampling-upgrade/s300/diagnose.py --output /tmp/s300-a.json --require-activation-preservation
PYTHONPATH=. python3 evidence/sampling-upgrade/s300/diagnose.py --output /tmp/s300-o.json --require-observer
PYTHONPATH=. python3 evidence/sampling-upgrade/s300/diagnose.py --output /tmp/s300-c.json --require-external-callsite
PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s300 -p 'test_*.py'
PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s291 -p 'test_*.py'
PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s283 -p 'test_*.py'
PYTHONPATH=. python3 -m unittest tools.tests.test_external_collision_callsite tools.tests.test_receiver_authored_query tools.tests.test_receiver_init_order tools.tests.test_p1_receiver_availability tools.tests.test_sampling_geometry tools.tests.test_sampling_native tools.tests.test_import_guards
python3 tools/verify.py
python3 tools/check_handoff.py
```

[Gates](gates.json), [project checks](project-checks.json), [scope audit](scope-audit.json),
[manifest audit](manifest-audit.json) and [timing](session-timing.json) record
actual outcomes and measured costs. [Artifact hashes](artifact-sha256.json) pin
analysis outputs and validation logs, excluding the hash index itself.
Initial reading/design and person-days remain unknown. No Godot or contract
check applies to this evidence-only change.

Validation: **97 tests pass** (12 new, 10 retained s291, 10 retained s283,
65 retained tools). Integrity, handoff and diff checks pass. The archival audit
exits 0; all three runtime proof requirements retain exit 1.
