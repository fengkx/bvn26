# s331 — AFTER-s326 rank #5: P2 body-push observer prerequisite

Base: `eee4a0abc53c8cfab008d8693363579e5d7e2c55` (s330 #208).
Branch: `feat/s331-body-push-observer`.
Authority: [unchanged AFTER-s326 rank #5](../next-fix-priority-after-s326.md).
Ranks 1–4 deliveries remain closed; ranks 6+ planning only. No re-ranking.
`production_admitted=false`; `native_parity_proven=false`; M0-02 pending.

## Result and limits

Independent live defining scope, this/root/parent generations and activation/
coercion erasure remain **unproved**. This is a facility qualification gap report,
not a qualified observer. There are zero new independent native observations.

[Diagnosis](diagnosis.json) retains exact function source and line spans for the
three inspected adapters. `debugger_script` reads selected frame-zero CPU
registers then detaches; it supplies no AVM body/scope/activation resolver or
uninterrupted object generations. s283 `instrument` passes `this` to the proposed
`s283Value` wrappers; that owner argument cannot independently certify its own
identity or neutrality. s283 `build` compiles and exports disk pcode, without
measuring live activation or coercion. These functions were read, not invoked.
This conclusion is bounded to these adapters, not a claim that a suitable native
facility cannot be built. No new header/dataflow audit is counted as progress.

Every s322 file is pinned and its complete diagnosis replayed, recursively
revalidating the retained body-push evidence and 5,437 historical events. That is
retained validation only. Initialization-to-call/overwrite/return/body-end paths
and the dashing two-Not versus direct-If cut remain s322's findings. Structural
body end is not an observed dispatcher return; spelling and register/pointer
identity cannot establish scope or object generation. No old proof is relabelled.

## Qualification boundary

All loaded-body/invocation/scope and this/root/parent generation fields are null.
Separate original/candidate measurements remain null at initialization,
scope/member accesses, intervening calls, first overwrite, pre-overwrite returns,
body end, dashing read, and coercion/branch. These are required observation
boundaries, not newly observed executions. Suppression/preload visibility,
actual value/type, coercion effects and erasure are likewise unknown.

The first unmet prerequisite is an independent binding of one loaded original/
candidate body and invocation to defining scope plus uninterrupted this/root/
parent lifetimes. A future channel must observe activation-visible values and
mutation/exception/reentrancy/lifetime/scheduling effects across the retained
boundaries, without using helper-written stamps as identity. Only after that
binding and activation/coercion erasure qualify may helper effects and natural
executed/skipped off/on controls be measured. No helper was installed and no
control was run. External callsite execution stays unknown, not false.

## Reproduction and gates

```sh
PYTHONPATH=. python3 evidence/sampling-upgrade/s331/diagnose.py --output /tmp/s331.json
PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s331 -p 'test_*.py'
python3 tools/verify.py
python3 tools/check_handoff.py
```

Base diagnose exits 0 for package consistency only. Each proof requirement exits
1: `--require-scope-binding`, `--require-activation-erasure`,
`--require-coercion-erasure`, `--require-helper-effects`, `--require-off-on`,
`--require-external-callsite`. Invalid pinned input fails separately with
`S331_EVIDENCE_INVALID`; no trace/proof override is accepted.
Measured commands, exits and costs: [gates](gates.json),
[project checks](project-checks.json). Local tests reject altered evidence and
verify fail-closed proof flags; the s322/s312/s300/s291/s283 and retained shared
body-push tests are rerun. No runtime or contract change requires Godot or
contract checks.

## Source-first and custody

1. Complete callbacks remain in locked s283, with s273 caller/frame mapping;
   source is `scripts/fighter/yihu.json` → `DefineSprite_638/frame_1/DoAction.as`.
2. Retained Sprite638 depth1 new placement is not MOVE; no new live lifetime proof.
3. Explicit returns and structural body end remain distinct from dispatcher return.
4. Tests enforce evidence integrity and unknowns, not guessed gameplay semantics.
5. No new original/Godot same-input comparison; native parity remains unproved.

Only s331 plus minimal STATUS/SAMPLING_UPGRADE/tasks/manifest tracking changes.
All prior s254–s330 trees, authority table, game/scripts, runtime, contracts and
shared sampler/threshold/validator remain unchanged. No early initialization,
receiver exemption, extra hitTest or tick41. Zero builds, player launches,
attaches, memory reads, captures or product obligations closed. Scope and manifest
hash changes are audited; artifact index excludes itself and caches. Measured
packaging time excludes initial reading/design and later commit/push/PR work;
person-days unknown. Draft only; no ready marking, merge or deployment.
