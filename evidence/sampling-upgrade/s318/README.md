# s318 — Post-s317 rerank + rank1 Yulong initializer exposure frontier

Base: current origin/master `90ddc6cb245d0508eb340423bba58f80e167e01c`
(s317 #195). Branch: `feat/s318-after-s317-rerank`.
Authority: [AFTER-s317 rank #1](../next-fix-priority-after-s317.md).
**Only rank 1 is executed in s318. Ranks 2+ are planning only.**
`production_admitted=false`; `native_parity_proven=false`; M0-02 pending.
Evidence-only, honest-unproved; zero product obligations closed.
s309–s317 deliveries remain closed; their unproved mechanisms remain gaps.

## Ranking and new bounded result

[Ranking pins](ranking-basis-sha256.json) bind s300–s317 READMEs/diagnoses and
all previous priority tables. The new table prioritizes concrete source-bounded
discriminators, independent observations, downstream prerequisites, then facility
cost. It does not rank by likelihood of passing a proof gate. Loader moves above
body-push after the wrapper inventory; Yulong retains first place for a new
finite question about initialized slots, not a repeat of explicit-read coverage.
No rank2+ experiments, facility queries, builds or captures run.

[diagnose.py](diagnose.py) checks [input pins](input-sha256.json), reproduces the
entire locked s309 diagnosis and recursively revalidates its 5,214 historical
events. That replay is validation only. The new audit traverses the complete
unprojected functions from immediately after each added initialization until the
first explicit same-role store or Return. It retains **every** intervening node,
not just a selected list of supposedly observable opcodes. All graph edges are
considered without asserting branch feasibility. Each node has a concrete graph
path from the cut entry. The original comparison starts at its corresponding
array push, node8; earlier afterFix setup is outside this region, not erased from
the function. Both complete graphs and all 80 conditional correspondence pairs
are checked before comparison.

| Role / archive initializer | First overwrite archive → original | Return before overwrite archive → original | Region nodes archive / original |
| --- | --- | --- | --- |
| `_loc2_`, node9 / offset5859 | 26 → 20 | 90 → 86 | 19 / 15 |
| `_loc4_`, node12 / offset5868 | 33 → 27 | 90 → 86 | 23 / 22 |

Coordinates are expanded decoded nodes and uncompressed SWF offsets, never live
PCs, frames or observed execution order. The candidate-only nodes retained in
these regions are 10/11/12/13 and 13 respectively: the remaining initializer
envelopes. Every mapped region node and terminal boundary corresponds to the
original region. These comparisons use the already conditional mapping; they do
not discharge its erasure premise.

The graph's enumeration-end branch reaches Push null / Return (89/90), with both
initialized slots still lacking an explicit overwrite. This is **structural
reachability**, not an observed empty enumeration or actual native return. There
is no explicit CallMethod in either region; the hitTest call at candidate node42
is beyond both overwrite boundaries. The regions nevertheless include Enumerate2,
Equals2 and GetMember; the second also includes Add2. These are instruction facts,
not claims of actual hidden access or absence of effects. The audit does not
classify any opcode as harmless or equate absence of CallMethod with no reentrancy.

This newly bounds the exposure question left by s309. Its static nine-read
overwrite result remains closed and valid: absence of a read is compatible with
a path reaching return before overwrite. No proof of safe initialization erasure,
live slot identity, scope binding or activation visibility follows. No operand
stack, exception edges, coercion semantics, native scheduler or broad interpreter
is added. Cyclic graph traversal terminates; this is not a proof of runtime
termination. [Diagnosis](diagnosis.json) retains every frontier and witness.

## Honest gates and next discriminator

| Requirement | Exit | Code |
| --- | --- | --- |
| Fixed-evidence frontier audit | 0 | `S318_DIAGNOSIS_OK` |
| Activation-visible erasure | 1 | `S318_ACTIVATION_ERASURE_UNPROVED` |
| Independent observer qualification | 1 | `S318_OBSERVER_UNPROVED` |
| Natural nested entry | 1 | `S318_NESTED_ENTRY_UNPROVED` |
| Direct parent removal dispatch | 1 | `S318_PARENT_REMOVAL_UNPROVED` |

Missing live observations remain unchanged/null. The analyzer accepts no live
trace or proof override; changing stored flags cannot qualify a witness. Invalid
pins/full graphs/correspondence fail as `S318_EVIDENCE_INVALID`.

Blocker: no independent live slot/scope binding or activation-visibility
observation across the enumeration/member/coercion and null-return boundaries.
Next qualify those bindings and effects for a retained invocation, including
no-overwrite and overwrite paths, without assuming hidden access exists or is
impossible. Only then qualify helper effects and observer-off/on before natural
nested entry/direct removal controls. No fresh capture is admitted by this audit.

## Source-first and scope

1. Complete Sprite2 six-function bounds stay locked in s294 and the complete
   getHitObj operands in s302/s309. This cut retains all region instructions.
2. Sprite345 frame188 depth28 k1atm (Sprite104), with depth2 mian (Sprite2), is a
   new placement; neither register role names nor paths prove native lifetime.
3. Sprite104 stops at1, conditionally goes to5, renames at5 and stops at10;
   Sprite345 removes depth28 at194. Both function returns remain explicit;
   no label end becomes a return or root bracket becomes removal dispatch.
4. Tests protect byte-derived graph facts and paths, not presumed gameplay or
   hidden effects. Independent backward reachability checks region membership;
   bypassing each real overwrite exposes the later call and both returns.
5. Only historical same-input evidence is revalidated. No new original/Godot
   comparison exists; runtime implementation and mechanism closure stay unproved.

Only the new authority, s318 and proportionate STATUS/SAMPLING_UPGRADE/tasks/
manifest updates change. No edits under s254–s317 or other evidence trees, game/,
scripts/, runtime, contracts, shared sampler/threshold/validator. No helper
installation, ancestor pn substitution, aliases, artificial calls/hitTest,
enlarged boxes or inferred eligibility. Zero new builds, launches and captures.
No merge, deployment or product admission. Ranks2+ remain planning only.

## Reproduce and validation

```sh
PYTHONPATH=. python3 evidence/sampling-upgrade/s318/diagnose.py --output /tmp/s318.json
# Each independently expects exit 1:
# --require-activation-erasure --require-observer --require-nested-entry --require-parent-removal
PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s318 -p 'test_*.py'
PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s309 -p 'test_*.py'
PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s302 -p 'test_*.py'
PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s294 -p 'test_*.py'
PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s285 -p 'test_*.py'
PYTHONPATH=. python3 -m unittest tools.tests.test_yulong_operand_boundary tools.tests.test_nested_owner_diagnosis tools.tests.test_yulong_k1atm_observer tools.tests.test_sampling_geometry tools.tests.test_sampling_native tools.tests.test_import_guards
python3 tools/verify.py
python3 tools/check_handoff.py
```

[Gates](gates.json), [project checks](project-checks.json), [scope audit](scope-audit.json),
[manifest audit](manifest-audit.json) and [timing](session-timing.json) retain actual
outcomes and costs. [Artifact hashes](artifact-sha256.json) cover every s318 file
except the index itself. Initial reading/design and person-days are unknown;
measured implementation/check time excludes later commit/push/PR work. No runtime
or contract change requires those additional checks. Development testing exposed
a missing full-map validation; the analyzer now validates every mapped node and
edge, including those outside the cut, and the negative mutation test passes.

Validation: **115 tests pass** (12 focused, 12 s309, 12 s302, 10 s294,
8 s285 and 61 retained tools). Base diagnosis exits0; all four proof gates
exit1. Integrity, handoff and diff whitespace checks pass. Green package checks
do not establish native preservation or complete M0-02.
