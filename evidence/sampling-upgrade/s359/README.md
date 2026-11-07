# s359 — AFTER-s353 rank #6: P2 body-push

Base: `f57490ff` (s358 #236 squash). Branch: `feat/s359-body-push`.
Authority: [unchanged AFTER-s353 table, rank #6](../next-fix-priority-after-s353.md).
Ranks 1–5 are delivered evidence cuts; ranks 7+ remain planning only. No re-ranking.
`production_admitted=false`; `native_parity_proven=false`; M0-02 pending.

## Independent attempt and result

**Receipt-matching candidate recovery and independent loaded-body/scope/invocation
association with uninterrupted this/root/parent generations remain unproved.**
No erasure measurement was performed; zero mechanism/product obligations closed.

The new [recovery route](recover_candidate.py) searches the pinned base's reachable
Git objects, selecting the SWF paths reported by `git rev-list --objects` and hashing
actual blob bytes with SHA-256. This is an archive recovery route independent of
s349's SWF debug-tag inventory. It neither reconstructs nor launches a candidate.
The [record](recovery-route.json) retains each object ID, reported path, length and
hash, the complete listing digest and the exact receipt-path observation.

- 65 SWF-named blobs were checked; none matches the s283 candidate receipt hash
  `02089de774d202446491ce8e0afc58a3e0fcd7ad508dcf463668175d91163eb7`.
- The receipt-pinned `/private/tmp/bvn-s283-qualification-r02/candidate.swf`
  is still absent at observation time. Expected hash comes from the unchanged
  [compile receipt](../s283/build-audit.json), not a new build or pcode inference.
- The original yihu SWF is present in the searched archive and matches its receipt;
  this is a positive search control, not candidate recovery or live identity.
- No candidate bytes were recovered; loaded body, defining scope, invocation pair
  and uninterrupted generations remain null. There is no new native observation.

This negative result is bounded to the reported SWF paths reachable from one
commit and the exact receipt path. Git reports one path per object: alternate
names, non-SWF-named blobs, dangling objects, other refs, external archives and
process memory are outside this search. It does not establish global absence or
debugger impossibility. Even a hash match would establish disk-byte custody only;
it would not establish a loaded definition, scope or actual invocation.
The preliminary path-filtered Git enumeration produced no blobs; it was rejected
as an inadequate recovery search. The retained route enumerates the complete
reachable object list first and then selects reported SWF paths.

## Proof boundary

[Binding attempt](binding-attempt.json) keeps the original/candidate run, input,
loaded body, defining scope, invocation/activation and scope/this/root/parent
generations unknown. All eight retained initialization/access/call/overwrite/
return/body-end/dashing/coercion boundaries retain null values and measurements.
The complete [s349 diagnosis](../s349/diagnosis.json) is replayed unchanged,
including the retained chain and 5,437 historical events; that is validation,
not new progress. No prior header, dataflow or debug-tag inventory is re-labelled
as a new observation.

Next required evidence is an authentic candidate copy matching the receipt and
an independent loaded-body/defining-scope/invocation association for a same-input
original/candidate pair, with uninterrupted this/root/parent generations. Only
then measure initialization-to-overwrite/actual-return effects through opaque
operations, including actual dashing operands and coercion. Structural body end
is not dispatcher return. Helper effects and natural executed/skipped off/on
controls remain unexecuted. No coercion assumptions, early initialization,
receiver exemption, extra hitTest or tick41; no reconstruction as qualification.

## Reproduction and checks

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 evidence/sampling-upgrade/s359/diagnose.py --output /tmp/s359.json
PYTHONDONTWRITEBYTECODE=1 python3 evidence/sampling-upgrade/s359/recover_candidate.py --output /tmp/s359-recovery.json
PYTHONDONTWRITEBYTECODE=1 python3 evidence/sampling-upgrade/s359/recheck_recovery.py
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s359 -p 'test_*.py'
python3 tools/verify.py
python3 tools/check_handoff.py
```

Base diagnosis exit 0 means evidence consistency only. Seven individual proof
flags and their combined invocation exit 1: `--require-candidate-recovery`,
`--require-invocation-generations`, `--require-activation-erasure`,
`--require-coercion-erasure`, `--require-helper-effects`, `--require-off-on`,
`--require-external-callsite`. Invalid evidence fails separately with
`S359_EVIDENCE_INVALID`. No proof override or trace import exists.

[Input pins](input-sha256.json) lock all s349 files and inherited inputs plus the
authority. [Route pins](route-sha256.json) lock the recovery code and record.
The portable archive recheck compares immutable Git bytes; historical temporary
absence need not persist on another machine. Tool paths are repository-relative;
the only external candidate path is taken from its locked receipt. Python and
Git are used from PATH; no local SDK or debugger path is required.

[Gates](gates.json), [project checks](project-checks.json) and their text logs
record actual exits/durations. Unit tests protect custody and reject fabricated
binding, recovery, coercion and erasure claims; they do not model gameplay.
Retained suites run unchanged. No runtime/contract change requires Godot or
contract checks. [Scope audit](scope-audit.json) records zero protected diffs;
[manifest audit](manifest-audit.json) records only tracking hash updates.
[Artifact index](artifact-sha256.json) excludes itself and caches.

## Source-first and scope

1. Locked s283 callbacks and s273 caller/frame mapping remain authoritative:
   `scripts/fighter/yihu.json` → `DefineSprite_638/frame_1/DoAction.as`.
2. Retained Sprite638 depth1 placement is new, not MOVE; no new live lifetime.
3. Explicit returns and structural body end remain distinct from dispatcher return.
4. Tests protect evidence unknowns, not invented game behavior.
5. No new same-input original/Godot comparison; native parity remains unproved.

Only s359 and minimal STATUS/SAMPLING_UPGRADE/tasks/manifest tracking change.
All prior s254–s358 trees, authority tables, locked inputs, runtime, contracts,
shared sampler/threshold/validator are unchanged. Zero builds, player launches,
attaches, memory reads, helper installations or captures. The only executed rank
is #6. [Timing](session-timing.json) records packaging/check wall time since
implementation-start, excluding initial reading and later commit/push/PR;
person-days remain unknown. Delivery is a Draft PR, with no ready marking or merge.

Final local validation: **143 tests pass**. Archive recheck, integrity, handoff
and whitespace checks exit 0; base exit 0; seven proof flags and combined exit 1.
