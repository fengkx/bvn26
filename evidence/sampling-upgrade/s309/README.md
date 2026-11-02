# s309 — Post-s308 rerank + rank1 Yulong initialization dataflow

Base: current origin/master `93a45fa5a6a034b4125f6a984bb24639f18b6ff5`
(s308 #186). Branch: `feat/s309-after-s308-rerank`.
Authority: [AFTER-s308 rank #1](../next-fix-priority-after-s308.md).
**Only rank 1 is executed in s309. Ranks 2+ are planning only.**
`production_admitted=false`; `native_parity_proven=false`; M0-02 pending.
Evidence-only; zero product obligations closed. s300–s308 deliveries stay closed.

## Ranking and exclusive result

[Ranking pins](ranking-basis-sha256.json) bind s291–s308 READMEs/diagnoses and
all previous priority tables. Yulong moves first because s302 identifies two
specific conditional initializer erasures with complete function bytes and graph
correspondence. Ones remains an upstream scene prerequisite; Chad and Loader
now have native byte candidates. Body-push's explicit overwrite audit is closed,
terminal custody is closed, and UI/allocation/raster retain unmet prerequisites.
This ordering is not based on likelihood of a green gate. No rank2+ experiment,
facility query or capture ran; reading reports is ranking input only.

[diagnose.py](diagnose.py) verifies input/ranking hashes, replays the complete
unchanged s302 → s294 → s285 historical chain (5,214 events), and compares the
entire s302 result. A JSON round-trip canonicalizes integer object keys only;
values, arrays and observations are unchanged. [Input pins](input-sha256.json)
bind the authority and retained analyzer/report/pins. Recursive prior verification
binds the complete archived compiled functions and original source.

The **new** audit uses both complete **unprojected** decoded functions: original
87 expanded nodes and archive91. Jumps, Boolean operations and both initializers
remain present. A finite traversal over (node, last explicit StoreRegister)
follows every successor, including loop backedges, without assuming branch
feasibility. Each reaching definition has a concrete entry-to-read witness path.
The sentinel -1 denotes an unknown entry value, never assumed undefined.
The locked conditional 80-node bijection is used only to compare read/store
correspondence, not to remove initialization before analyzing it.

| Local role / archive → original register | Added archive initializer | Archive reads | Reaching store archive → original |
| --- | --- | --- | --- |
| `_loc2_` / 6 → 2 | node9, SWF offset5859 | 29, 51, 57, 63, 69, 75, 81 | 26 → 20 |
| `_loc4_` / 7 → 4 | node12, SWF offset5868 | 35, 38 | 33 → 27 |

Node IDs are expanded decoded pcode coordinates; offsets are uncompressed SWF
file offsets. Neither is a live address, native PC or observed execution order.
The corresponding original reads are 23/47/53/59/65/71/77 and 29/34.
All nine explicit reads have a later, corresponding definition. Neither added
initializer nor unknown entry value reaches a read in this graph. Full nodes,
headers, read sets, definitions and witness paths are in [diagnosis.json](diagnosis.json).

This proves the bounded **static overwrite property** and explicit-definition
correspondence. It does not prove that the writes can safely be erased in a live
activation. Calls are opaque graph nodes: the audit models no operand stack,
hidden activation access, exceptions, reentrancy, scope/arguments inspection,
unused slots, native scheduling or instruction timing. Headers retain register
counts15→9 and flags41; static role names do not establish live register binding.

## Honest-unproved boundary

The two erasures' activation-visible behavior remains unproved. Independent
header/preload/scope/arguments binding, helper mutation/coercion/logging effects,
observer-off/on preservation, direct removal dispatch and natural nested entry
remain absent. Historical observation fields stay null, not false. No eligibility
rule, native operand result or dispatch order follows from explicit dataflow.

| Requirement | Exit | Code |
| --- | --- | --- |
| Reproducible archival/dataflow audit | 0 | `S309_DIAGNOSIS_OK` |
| Complete activation preservation | 1 | `S309_ACTIVATION_PRESERVATION_UNPROVED` |
| Observer qualification | 1 | `S309_OBSERVER_UNPROVED` |
| Natural nested entry | 1 | `S309_NESTED_ENTRY_UNPROVED` |
| Direct parent removal dispatch | 1 | `S309_REMOVAL_DISPATCH_UNPROVED` |

The analyzer is fixed-evidence analysis, not an accepting runtime trace schema.
Changing proof flags cannot qualify a fresh observation. Next qualify live
activation-visible erasure and independent helper effects before installing any
observer or attempting direct removal/natural nested-entry paired controls.
The explicit-read discriminator is now closed; repeating it is not new progress.

## Source-first and scope

1. Complete Sprite2 source and six compiled function boundaries remain locked
   in s294; s302 decodes all getHitObj operands/branches. This cut preserves the
   entire original and archived function graphs, not a selected read window.
2. Sprite345 frame188 depth28 k1atm (Sprite104) and its depth2 mian (Sprite2)
   are new placements. No MOVE state inheritance, stamp-based allocation proof
   or additional placement is introduced. Scope remains retained ticks15–22.
3. Sprite104 stops at1, conditionally goes to5, renames at5 and stops at10;
   Sprite345 removes depth28 at194. Root brackets are not removal dispatch.
   Both getHitObj Return nodes remain; no label end becomes a return.
4. Tests check source-bound definitions/reads and actual witness edges; an
   independent backward traversal confirms all definitions. Bypassing each real
   store exposes the added initializer; removing the original store exposes an
   unknown entry. Synthetic loop/unreachable tests check the algorithm only.
   No assumed Flash schedule or gameplay outcome becomes a test invariant.
5. Only historical same-input native evidence is revalidated. No fresh original
   or Godot comparison exists. Runtime implementation and mechanism closure
   remain unauthorized by this incomplete evidence.

Only the new authority, s309 and proportionate STATUS/SAMPLING_UPGRADE/tasks/
manifest updates change. No edits under s254–s308; no game/scripts, runtime,
contracts, shared sampler/threshold/validator changes. No helper installation,
new compile/capture, ancestor pn substitution, aliases, artificial call/hitTest,
enlarged boxes, other chains or inferred eligibility. Zero builds, player
launches and captures; no merge, deployment or production admission.

## Reproduce and validation

```sh
PYTHONPATH=. python3 evidence/sampling-upgrade/s309/diagnose.py --output /tmp/s309.json
# Each requirement independently expects exit 1:
PYTHONPATH=. python3 evidence/sampling-upgrade/s309/diagnose.py --output /tmp/s309-a.json --require-activation-preservation
PYTHONPATH=. python3 evidence/sampling-upgrade/s309/diagnose.py --output /tmp/s309-o.json --require-observer
PYTHONPATH=. python3 evidence/sampling-upgrade/s309/diagnose.py --output /tmp/s309-e.json --require-nested-entry
PYTHONPATH=. python3 evidence/sampling-upgrade/s309/diagnose.py --output /tmp/s309-r.json --require-parent-removal
PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s309 -p 'test_*.py'
PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s302 -p 'test_*.py'
PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s294 -p 'test_*.py'
PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s285 -p 'test_*.py'
PYTHONPATH=. python3 -m unittest tools.tests.test_yulong_operand_boundary tools.tests.test_nested_owner_diagnosis tools.tests.test_yulong_k1atm_observer tools.tests.test_sampling_geometry tools.tests.test_sampling_native tools.tests.test_import_guards
python3 tools/verify.py
python3 tools/check_handoff.py
```

[Gates](gates.json), [project checks](project-checks.json), [scope audit](scope-audit.json),
[manifest audit](manifest-audit.json) and [timing](session-timing.json) record actual
results and measured costs. [Artifact hashes](artifact-sha256.json) cover analysis
outputs, code and validation logs, excluding the index itself. Initial reading/
design and person-days are unknown. No runtime/contract checks apply.

Validation: **103 tests pass** (12 focused, 12 retained s302, 10 retained s294,
8 retained s285 and 61 retained tools). Integrity, handoff and diff checks pass;
archival diagnosis exits0 and all four proof requirements retain exit1.
