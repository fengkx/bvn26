# s339 — AFTER-s335 rank #4: Loader consumed bytes

Base: `8a3de319` (s338 #216 squash). Branch: `feat/s339-loader-consumed-bytes`.
Authority: [AFTER-s335 rank #4](../next-fix-priority-after-s335.md).
Only rank #4 executes; no re-ranking. Ranks 1–3 deliveries stay closed; ranks 5+
remain planning only. The authority table's historical planning wording is unchanged.
`production_admitted=false`; `native_parity_proven=false`; M0-02 pending.

## Outcome and independent observations

**The requested executed consumer/request/range/target association remains
unproved.** No independent live channel or trace was obtained. This is an
unfulfilled measurement cut with honest failure gates, not new Loader proof.
Zero new independent native observations and zero mechanism/product obligations
closed. No player launch, attach, memory read, build or capture was performed.

[Binding attempt](binding-attempt.json) is a blocked measurement ledger, not an
execution trace. Executed caller and P1 consumer, immutable request generation,
read return, returned/consumed ranges, partial/failed-read behavior, target before
inline advance, uninterrupted lifetime and observer effects remain null. The
read-entry/read-return/consumer-use/pre-inline-advance/initialization/use/unload/
replacement boundaries retain null events, generations and measurements. Null
is neither an empty returned range nor an observed zero byte.

[Diagnosis](diagnosis.json) reproduces the complete locked s330 diagnosis and its
recursive retained Loader validation. All s330 files and direct pinned inputs
are locked by [input hashes](input-sha256.json). This replay is retained validation,
not a fresh interface audit or progress toward live consumption. The only newly
established results are package consistency and actual local gate/test outcomes.
No claim is made that a suitable independent channel is impossible to construct.

Retained s321 identifies static call `0x100108f68` and a local at `rbp-0x29`
initialized to zero before the call. Its later byte load cannot distinguish a
returned byte from preserved initialization. Disk bytes do not establish live
consumption; a mutable stream slot does not establish request generation; a
static candidate or breakpoint hit alone does not establish P1 execution identity.
No old proof is resealed or relabeled as new progress.

## Missing evidence and control order

Independently bind one actually executed caller/consumer to an immutable P1
request generation. Join actual read status and returned ranges to consumed
subranges of that same request, including partial/failed reads. Observe the target
before `loadStep++` invokes the next load inline. Preserve same-request
initialization/use/unload/replacement and qualify observer effects. No pointer,
path, configured filename or post-advance slot substitutes for those bindings.

Normal qualification is false. Only after normal qualifies may a Yihu-for-Yijiao
wrong-resource control run with expected Yijiao identity unchanged and actual
error/range evidence. That control was not executed here. These are missing
requirements, not proposed experiments reported as results.

## Gates and reproduction

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 evidence/sampling-upgrade/s339/diagnose.py --output /tmp/s339.json
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s339 -p 'test_*.py'
python3 tools/verify.py
python3 tools/check_handoff.py
```

Base diagnose exits 0 for evidence consistency only. Each proof flag exits 1,
as do all combined: `--require-consumer-request`,
`--require-returned-consumed-ranges`, `--require-pre-advance-target`,
`--require-loader-attestation`, `--require-wrong-resource-control`.
Codes are `S339_<FLAG_WITH_UNDERSCORES>_UNPROVED`. Changed pinned inputs or
fabricated fields fail separately with `S339_EVIDENCE_INVALID`. There is no
trace-import or proof override. Tests reject disk-byte, initialized-zero,
mutable-slot, static-candidate and premature control promotion; these are custody
tests, not synthetic Flash observations. Complete s330 and retained Loader/shared
suites run unchanged. Commands, actual exits and costs are in [gates](gates.json)
and [project checks](project-checks.json).

## Source-first and custody

1. Locked `scripts/main.json` → `DefineSprite_1900/frame_1/DoAction.as` remains
   the shared P1/P2/assist/sound Loader source; no script behavior is changed.
2. No new PlaceObject/MOVE or native instance lifetime observation was obtained.
3. `LO.onLoadComplete(target)` ignores target and advances the next load inline;
   no later mutable slot is promoted to the prior target association.
4. Tests preserve unknowns and provenance, not assumed successful reads.
5. No new original/Godot same-input comparison; native parity remains unproved.

Only s339 and minimal STATUS/SAMPLING_UPGRADE/tasks/manifest tracking change.
All s254–s338 trees, authority tables, game/, scripts/, runtime, contracts and
shared sampler/threshold/validator remain byte-identical. No runtime or contract
changes require Godot/contract validation. No rollout, deployment, ready marking
or merge. Delivery is a Draft PR only.

[Scope audit](scope-audit.json), [manifest audit](manifest-audit.json) and
[artifact hashes](artifact-sha256.json) record custody. The artifact index excludes
itself and caches. [Timing](session-timing.json) records measured packaging/check
wall time, excluding initial reading/design and later commit/push/PR; person-days
remain unknown.

Validation: **100 tests pass**. Base exit 0; five proof flags and their
combined invocation exit 1. Integrity, handoff and whitespace checks exit 0.
These results do not establish live Loader association or product acceptance.
