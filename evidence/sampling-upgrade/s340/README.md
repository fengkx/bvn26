# s340 — AFTER-s335 rank #5: P2 body-push erasure

Base: `55e718b2` (s339 #217 squash). Branch: `feat/s340-body-push-erasure`.
Authority: [unchanged AFTER-s335 rank #5](../next-fix-priority-after-s335.md).
Only rank #5 executes; no re-ranking. Ranks 1–4 deliveries remain closed;
ranks 6+ planning only. Historical planning wording in the authority is unchanged.
`production_admitted=false`; `native_parity_proven=false`; M0-02 pending.

## Outcome and limits

**Independent original/candidate invocation and generation binding, activation
erasure and coercion erasure remain unproved.** No independent live channel or
paired trace was obtained. This is an unfulfilled measurement cut with honest
failure gates, not new body-push proof. Zero independent native observations and
zero mechanism/product obligations closed. No build, player launch, attach,
memory read, helper installation or capture was performed.

[Binding attempt](binding-attempt.json) is a blocked measurement ledger, not an
executed invocation trace. Original/candidate runs, same input tape, loaded bodies,
invocations, activations, defining scopes, scope/this/root/parent generations,
uninterrupted lifetimes, suppression/preload visibility, actual dashing value/type,
coercion effects and external callsite execution remain null. Null external
callsite execution does not mean that the call did not execute.

Every initialization, scope/member access, intervening call, first overwrite,
return-before-overwrite, body-end, dashing-read and coercion/branch boundary has
null original/candidate events, slot states and erasure measurements. None is
an observed zero effect. Structural body end is not native dispatcher return.

[Diagnosis](diagnosis.json) reproduces the complete locked s331 diagnosis,
recursively revalidating s322 and retained body-push tooling, including 5,437
historical events. [Input hashes](input-sha256.json) pin every s331 file and its
direct pinned inputs. Replay is retained validation only. No duplicate header,
dataflow or interface inventory is counted as progress. The only newly established
results are package consistency and measured local gate/test outcomes; no claim
is made that a suitable independent live channel cannot be constructed.

## Missing evidence and control order

First independently bind one original/candidate loaded body and invocation to
its activation and defining scope, preserving uninterrupted scope/this/root/parent
generations. A path, CPU register, pointer equality, s283Value owner argument or
helper-written stamp cannot certify those bindings. Measure activation-visible
values from initialization through intervening accesses/calls to overwrite or
actual return, including exceptional/reentrant/lifetime/scheduling effects.

Retained s322 compares original dashing read with two Not operations then If
against the candidate scope read directly followed by If. This is a static cut,
not proof that the actual operand is Boolean or coercion is harmless. Its actual
value/type and effects must be measured within the independently bound pair.
Only after binding and activation/coercion erasure qualify may helper effects and
natural executed/skipped off/on controls run. Those controls were not executed.
No early initialization, receiver exemption, extra hitTest or tick41 is introduced.

## Reproduction and gates

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 evidence/sampling-upgrade/s340/diagnose.py --output /tmp/s340.json
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s340 -p 'test_*.py'
python3 tools/verify.py
python3 tools/check_handoff.py
```

Base diagnose exits 0 for package consistency only. Each proof flag and their
combined invocation exit 1: `--require-invocation-generations`,
`--require-activation-erasure`, `--require-coercion-erasure`,
`--require-helper-effects`, `--require-off-on`, `--require-external-callsite`.
Codes are `S340_<FLAG_WITH_UNDERSCORES>_UNPROVED`. Invalid pinned inputs or invented
measurements fail separately with `S340_EVIDENCE_INVALID`; no proof override or
trace-import path is accepted. Tests reject fabricated binding, Boolean/harmless
coercion assumptions, zero-erasure promotion and premature controls. These are
evidence custody tests, not synthetic gameplay observations.

Complete s331/s322/s312/s300/s291/s283 and retained shared body-push suites are
rerun unchanged. Actual commands, exits and costs: [gates](gates.json),
[project checks](project-checks.json). No runtime/contract change requires Godot
or contract checks.

## Source-first and custody

1. Complete callbacks remain in locked s283, with s273 caller/frame mapping;
   source: scripts/fighter/yihu.json → DefineSprite_638/frame_1/DoAction.as.
2. Retained Sprite638 depth1 new placement is not MOVE; no new live lifetime proof.
3. Explicit returns and structural body end stay distinct from dispatcher return.
4. Tests preserve evidence and unknowns, not guessed gameplay invariants.
5. No new original/Godot same-input comparison; native parity remains unproved.

Only s340 plus minimal STATUS/SAMPLING_UPGRADE/tasks/manifest tracking change.
All s254–s339 evidence, authority tables, game/, scripts/, runtime, contracts and
shared sampler/threshold/validator remain byte-identical. No other rank executes.
[Scope audit](scope-audit.json), [manifest audit](manifest-audit.json) and
[artifact hashes](artifact-sha256.json) record custody. Artifact index excludes
itself and caches. [Timing](session-timing.json) records measured packaging/check
wall time excluding initial reading/design and later commit/push/PR; person-days
unknown. Draft PR only; no ready marking, merge or deployment.

Validation: **127 tests pass**. Base exit 0; six individual proof flags and
their combined invocation exit 1. Integrity, handoff and whitespace checks exit 0.
These outcomes do not establish independent live binding or erasure.
