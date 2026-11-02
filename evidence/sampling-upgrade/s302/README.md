# s302 — AFTER-s299 rank #3: Yulong nested activation and dispatch

Base: origin/master `a866246aa4e1deedd0b802bb584b0ebc20ea31d8`
(s301 #179). Branch: `feat/s302-yulong-nested`.
Authority: [AFTER-s299 rank #3](../next-fix-priority-after-s299.md).
**Evidence-only, honest-unproved.** `production_admitted=false`;
`native_parity_proven=false`; M0-02 pending; zero product obligations closed.

Only Sprite345 frame188 depth28 k1atm (Sprite104) → depth2 mian (Sprite2),
ticks15–22 of the retained s275 tape. No new build, launch, capture or paired
control. Ranks 1–2 and 4+ are not executed. The locked s294 diagnosis is
reproduced exactly, including its 5,214-event historical validation chain.

## Complete bounded getHitObj audit

[diagnose.py](diagnose.py) consumes the original/archived function bytes recovered
by [s294](../s294/README.md). It checks complete byte coverage, instruction lengths,
constant-pool values, register operands and branch destinations, rejecting any
unhandled opcode or operand kind. It expands Push packets in their original
order, retaining raw bytes, file offsets and packet-part numbers. Every instruction
is represented: original **62 instructions / 229 bytes / 87 expanded nodes**;
archive **91 instructions / 316 bytes / 91 expanded nodes**.

| Role | Original register | s275 register |
| --- | --- | --- |
| Enumeration item | 0 | 0 |
| this | 1 | 1 |
| array | 9 | 2 |
| player | 13 | 3 |
| afterFix | 12 | 4 |
| ppw | 3 | 5 |
| `_loc2_` (array value) | 2 | 6 |
| `_loc4_` (candidate clip) | 4 | 7 |
| `_loc14_` (enumeration key) | 14 | 8 |

Both headers retain flags41; register counts remain 15→9. Parameter-role checks
are anchored to the actual headers. This table is a **static proposed role
correspondence**, not a live register/defining-activation binding. Unused original
register slots are not assumed to disappear invisibly.

The full ordered operand/control graph has an **80-node bijection only under
explicit projection premises**:

- Push grouping is expanded without changing value order; pool indexes resolve
  to strings, never compare by incidental index.
- Boolean Not/If polarity and Jump-only edges are normalized, with every rewrite
  recorded. Original candidate test uses Not/Not/If with a separate loop jump;
  the archive uses Not/If to the loop tail. True and false successors are compared
  separately, including enumeration exit and cleanup loops.
- The archive adds `Push undefined; StoreRegister; Pop` twice: register6
  (`_loc2_`) at body offsets26–34 and register7 (`_loc4_`) at35–43.
  These six nodes are **conditionally erased**, explicitly tagged
  `activation_visible_erasure_proved=false`. No activation erasure is proved.

The audit pairs every projected node and edge and rejects unmatched or unreachable
projected nodes. All six result fields, suffixes, enumeration cleanup, null return
and object return remain in order. The sole getHitObj CallMethod retains the
candidate argument, argument count1, `this` receiver and `hitTest` method operand
order. No extra call or hitTest is introduced. Node IDs and uncompressed offsets
are audit coordinates, **not native PCs or loaded action cursors**.

[diagnosis.json](diagnosis.json) includes both complete decoded sequences,
headers, register roles, rewrites, graphs and all node pairs. Conditional graph
identity is not complete operand/activation preservation: initializer erasure,
activation/scope/arguments/unused-slot visibility and instruction timing remain
unproved. No native invocation, returned value or eligibility follows from it.

## Explicit observer effects

The same report retains exact archived sources, archive paths and source hashes
for the Sprite2 initializer, frame188 callback, Sprite104 frames1/5/10, root frame10
sampler, `aiGeoStamp`, `aiK1Observe`, `aiEvent` and retained s275 helpers.
This is a source effect inventory, not complete transitive compiled preservation.

| Site | Added work or state | Remaining obligation |
| --- | --- | --- |
| aiGeoStamp | Conditional root serial increment; writes clip `__aiGeoId`, `__aiGeoSource`, `__aiGeoBirth` | Own-property/enumeration and lifetime visibility |
| aiK1Observe | Path guard, parent/list/function reads, String/escape conversions, logging | Getter/coercion/activation effects; no entry hook |
| s275Value | Wraps existing pause/receiver/target/result/played evaluations; reads value properties and logs before returning supplied value | Pass-through source does not prove neutrality |
| s275Boundary | Slot/stamp reads, getInstanceAtDepth and logging around goto/rename and at root sample | Root brackets are not direct removal dispatch |
| aiEvent | `++aiSeq`, getTimer, concatenation and trace | Independent timing/scheduling perturbation bound |

The **historical** aiK1Observe source also reads `grandparent.pn` for logging.
It is disclosed as an observer effect, never adopted as an ancestor pn substitute,
an alias or an eligibility criterion; this slice adds and executes none of those
reads. Direct `_parent` for mian remains Sprite104, not Sprite345. The audit does
not certify this historical observer as neutral or compliant proof instrumentation.
The unchanged original getHitObj body has no entry/operand hooks. Missing entry
records mean unknown, never zero invocations.

## Gates and next boundary

| Requirement | Expected exit | Code |
| --- | --- | --- |
| Reproducible bounded diagnosis | 0 | `S302_DIAGNOSIS_OK` |
| Complete correspondence | 1 | `S302_COMPLETE_CORRESPONDENCE_UNPROVED` |
| Observer effect qualification | 1 | `S302_OBSERVER_EFFECTS_UNPROVED` |
| Direct parent removal dispatch | 1 | `S302_REMOVAL_DISPATCH_UNPROVED` |
| Natural nested entry | 1 | `S302_NESTED_ENTRY_UNPROVED` |

The missing proof is activation-visible erasure plus independently bounded helper
effects, followed by loaded activation/operand and direct dispatch bindings for
this placement. No same-placement independent observer-off/on evidence exists;
`perturbation_bound`, entry/stack/register/scope and loaded-buffer observations
remain null. Direct removal/natural nested-entry paired controls stay blocked
before execution. This diagnostic is fixed-evidence analysis, not a trace admission
interface; toggling report fields cannot supply proof.

## Source-first and scope

1. Complete Sprite2 source and six compiled boundaries remain locked in s294;
   this slice decodes getHitObj in full. Relevant observer source is retained.
2. Frame188 and depth2 are new placements; no MOVE state inheritance or native
   allocation identity is inferred from stamps.
3. Sprite104 stops at1, conditionally goes to5, renames at5, stops at10;
   Sprite345 removes depth28 at194. Source tags/root brackets do not bind dispatch.
4. Tests protect exact source-derived operands/branches, byte coverage and
   unproved fields, with changed constants/registers/targets/missing bytes as
   negatives. No assumed gameplay behavior is made a regression expectation.
5. Only the retained native tape is revalidated; no fresh original or Godot
   comparison exists. Mechanism and native parity remain unproved.

No ancestor pn substitution, aliases, artificial call/hitTest, enlarged boxes,
other chains or inferred eligibility. Only s302 and proportionate tracking files
change. No edits under s254–s301, game/scripts, runtime, contracts, shared
sampler/threshold/validator; no merge, deployment or product closure.

## Reproduce

```sh
PYTHONPATH=. python3 evidence/sampling-upgrade/s302/diagnose.py --output /tmp/s302.json
# Each requirement independently expects exit 1:
PYTHONPATH=. python3 evidence/sampling-upgrade/s302/diagnose.py --output /tmp/s302-c.json --require-correspondence
PYTHONPATH=. python3 evidence/sampling-upgrade/s302/diagnose.py --output /tmp/s302-o.json --require-observer
PYTHONPATH=. python3 evidence/sampling-upgrade/s302/diagnose.py --output /tmp/s302-r.json --require-parent-removal
PYTHONPATH=. python3 evidence/sampling-upgrade/s302/diagnose.py --output /tmp/s302-e.json --require-nested-entry
PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s302 -p 'test_*.py'
PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s294 -p 'test_*.py'
PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s285 -p 'test_*.py'
PYTHONPATH=. python3 -m unittest tools.tests.test_yulong_operand_boundary tools.tests.test_nested_owner_diagnosis tools.tests.test_yulong_k1atm_observer tools.tests.test_sampling_geometry tools.tests.test_sampling_native tools.tests.test_import_guards
python3 tools/verify.py
python3 tools/check_handoff.py
```

[Gates](gates.json), [project checks](project-checks.json),
[scope](scope-audit.json), [manifest audit](manifest-audit.json),
[timing](session-timing.json) and [artifact hashes](artifact-sha256.json)
retain actual results, custody and measured costs. Artifact hashes exclude their
own index. Initial reading/design and person-days remain unknown; measured
implementation/validation time is not a person-day estimate. No runtime or
contract changes require Godot or contract checks.

Validation: **91 tests pass** (12 new, 10 retained s294, 8 retained s285,
61 retained tools). Diagnosis, integrity, handoff and diff checks exit0; all four
proof gates exit1. Slice delivery does not close the mechanism or M0-02.
