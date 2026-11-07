# s338 — AFTER-s335 rank #3: Yulong erasure

Base: `078c3877b617b3f3dfb410e76c49f4eebd2b0558` (s337 #215 squash).
Branch: `feat/s338-yulong-erasure`.
Authority: [AFTER-s335 rank #3](../next-fix-priority-after-s335.md).
Only rank #3 executes; no re-ranking. Rank #1 and #2 deliveries remain closed;
ranks #4+ remain planning. The authority's planning wording is historical and
is not rewritten by this slice.
`production_admitted=false`; `native_parity_proven=false`; M0-02 pending.

## Outcome: prerequisite still unproved

**No original/candidate activation pair, defining scope or erasure measurement
was obtained.** This is an unfulfilled measurement cut, packaged with honest
failure gates; it is not new mechanism proof. There are zero new independent
native observations and zero mechanism or product obligations closed.

[Binding attempt](binding-attempt.json) records the stop before live binding:
no independent replacement for the missing s329 activation/scope resolver was
obtained. No live experiment was executed. Run IDs, loaded bodies, same-input
tape association, activations, defining scopes and uninterrupted lifetimes all
remain null. Each initialization, enumeration, member-access, coercion, overwrite
and no-overwrite null-return boundary retains null paired events, slot states
and erasure measurement. Null is neither zero effect nor successful erasure.

This record is a blocked measurement ledger, not a trace, candidate activation
selection, new interface survey or new CFG result. No assertion is made that an
independent resolver is impossible, that opaque operations access the initialized
slots, or that their effects are harmless. Static reachability is not execution.
No observer was installed; observer controls remain unexecuted and unproved.

[Diagnosis](diagnosis.json) reproduces the **complete locked s329 diagnosis**,
including its recursive historical validation. The old CFG and adapter readings
are retained validation only, not progress credited to s338. Every s329 file and
its direct pinned inputs are sealed by [input hashes](input-sha256.json).
No prior proof or output is rewritten; no new CFG/interface audit is performed.
The only newly established results are package consistency, retained replay and
the actual local gate/test outcomes. None independently measures live behavior.

## Missing evidence before observer controls

An independent channel must first associate the actual loaded original/candidate
bodies with one same-input activation pair and each defining scope. It must
preserve invocation and scope lifetime continuously through initialization,
enumeration/member/coercion operations and the actual overwrite or return.
Measure paired slot visibility/effects at those boundaries without inventing
values or treating path/receiver/register identity as activation identity. An
observed overwrite path does not establish the no-overwrite return path.
Only after this prerequisite is proved can helper effects and observer off/on
controls be qualified. These are unmet requirements, not executed experiments.

## Gates and reproduction

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 evidence/sampling-upgrade/s338/diagnose.py --output /tmp/s338.json
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s338 -p 'test_*.py'
python3 tools/verify.py
python3 tools/check_handoff.py
```

Base diagnosis exits **0**, meaning evidence consistency only. Each flag below
independently exits **1** (and all combined also exit 1):

| Flag | Code |
| --- | --- |
| `--require-activation-pair` | `S338_ACTIVATION_PAIR_UNPROVED` |
| `--require-activation-scope` | `S338_ACTIVATION_SCOPE_UNPROVED` |
| `--require-activation-erasure` | `S338_ACTIVATION_ERASURE_UNPROVED` |
| `--require-observer` | `S338_OBSERVER_UNPROVED` |

There is no proof override or trace-import interface. Changed inputs, prior replay
or fabricated fields in this blocked record fail closed. Tests cover promotion
of pointers/paths/helpers, fabricated zero erasure, missing boundaries, prior
replay drift and individual/combined CLI gates. These are custody tests, not
synthetic Flash observations. Retained s329/s318/s309/s302/s294/s285 and the
Yulong/shared tool suites run unchanged. [Gates](gates.json) and
[project checks](project-checks.json) record commands, exits and timings.
No runtime or contract change requires Godot or contract validation.

## Source-first and custody

1. Complete Sprite2 function bounds and operands remain locked in s294/s302/s309/s318.
2. Sprite345 frame188 depth28 k1atm and its nested mian placement do not identify
   a native activation or defining scope.
3. Retained Sprite104 stop/goto/removal and explicit function returns are unchanged;
   no label end or missing event is treated as return.
4. New tests preserve unknowns and provenance, not assumed gameplay behavior.
5. No new original/Godot same-input comparison exists; native parity is unproved.

Zero builds, player launches, attaches, memory reads, helper installations or
captures. No extra hitTest, ancestor pn substitution, enlarged boxes, inferred
hidden access/harmlessness, early helper installation or observer qualification.
Only s338 and minimal STATUS/SAMPLING_UPGRADE/tasks/manifest tracking change.
All s254–s337 evidence, authority tables, game/, scripts/, runtime, contracts and
shared sampler/threshold/validator remain byte-identical.

[Scope audit](scope-audit.json), [manifest audit](manifest-audit.json) and
[artifact hashes](artifact-sha256.json) retain custody. The artifact index excludes
itself and caches. [Timing](session-timing.json) records measured implementation
and check wall time, excluding initial reading/design and later commit/push/PR;
person-days remain unknown. Delivery is a Draft PR only; no ready marking,
merge or deployment, and no product closure.

Validation: **124 tests pass**. Base exit 0; all four proof flags exit 1.
Integrity, handoff and whitespace checks exit 0. These are package results,
not independent binding, erasure proof or product acceptance.
