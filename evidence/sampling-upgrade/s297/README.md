# s297 — AFTER-s290 rank #7 Loader consumed bytes (evidence-only, unproved)

Base: origin/master `9ee71eaf6b73fffbe7277cf4d79fc4a412dab76d` (s296 #174).
Branch: `feat/s297-loader-attestation`.
Exclusive authority: [AFTER-s290 rank #7](../next-fix-priority-after-s290.md).
`production_admitted=false`; `native_parity_proven=false`; M0-02 pending.
Zero product obligations closed.

**The s259-normal P1 returned-byte/request/target association remains unproved.**
The normal prerequisite did not qualify; no wrong-resource experiment was run.
All three proof requirements exit 1 with distinct codes. A successful diagnosis
means the retained evidence was reproduced, not that loader attestation passed.

## Evidence and bounded result

[diagnose.py](diagnose.py) reproduces the entire locked [s287 diagnosis](../s287/README.md)
and checks exact report equality, including all 5,503 historical events,
receipt/archive provenance, original/archived loader source and four static
read-stub/indirect-slot pairs. [Input hashes](input-sha256.json) pin s287 and the
ranking authority; the prior diagnosis recursively checks its retained inputs.
Hashes are provenance checks only, never a substitute for live consumed bytes.
No old receipt, tape, archive or diagnosis was changed or resealed.

[facility.json](facility.json) retains four fresh, bounded LLDB queries against
the exact receipt-matching player executable (SHA-256
`8d4c1f5934adae809b5f4ce4f6ca7c64d4260df46bb3eb9c41fe32be2ee905be`):

| Query | Result | What it cannot establish |
| --- | --- | --- |
| Type `MovieClipLoader` | Empty lookup; exit 1 | Native consumer layout |
| Type `URLRequest` | Empty lookup; exit 1 | Immutable per-request identity |
| Type `CFReadStreamRef` | Empty lookup; exit 1 | Returned buffer/stream ownership |
| Symbols `ReadStream`, `LoadRequest`, `LoadContext`, `LoaderInfo`, `StreamConsumer` | Empty lookup; exit 1 | Consumer-to-request resolver |

The type names and symbol patterns are **search hypotheses**, not known class
names in this player. Each transcript shows successful x86_64 target creation
before the empty query. No lookup supplied a layout or callable resolver.
This does not prove that native analysis is impossible, that these objects do
not exist, or that any particular import serves P1. Static stubs were already
resolved by s287 and are not presented as new execution evidence.

Zero player launches, process attaches, SWF builds or fresh captures occurred.
The facility reads the executable on disk; it neither executes a P1 read nor
observes an API return. All eight live observation fields remain null in
[diagnosis.json](diagnosis.json). There is no manufactured positive control.

## Exact boundary and remaining blocker

Original and archived `scripts/main.json` at
`DefineSprite_1900/frame_1/DoAction.as` use one MovieClipLoader. P1 is followed
by P2, P1 assist, P2 assist and sound. The authored completion callback is:

```actionscript
LO.onLoadComplete = function(target)
{
   loadStep++;
   loadSteps[loadStep]();
};
```

It ignores `target` and installs no `onLoadInit` listener. This is source order,
not an observed callback schedule. A later read of a mutable current-request
field can name P2 after P1 completion has advanced the sequence. A loader
pointer, path equality, helper stamp or global counter cannot repair the join.

The missing prerequisite is a resolver for an **executed** P1 return and its
complete byte ranges (or actual mapped ranges and consumption), native consumer,
immutable request, and target before the authored inline advance. Preserve the
original callback body/order and input/random tapes; qualify observer effects.
Same-request init/use and unload/replacement must be observed separately, not
inferred from a same-path instance or a frame-1 stamp.

Only after independent normal qualification may an isolated actual
Yihu-for-Yijiao resource control run with expected Yijiao identity unchanged.
It must retain supplied/returned/consumed bytes, the same request/target boundary
and errors. Archive substitution, server delivery and disk hashes do not prove
what the player consumed. This fixed-evidence diagnosis cannot accept a new
capture; new execution needs independent analysis, not changed flags.

## Gates and scope

| Requirement | Exit | Code |
| --- | --- | --- |
| Evidence diagnosis | 0 | `S297_DIAGNOSIS_OK` |
| Normal consumed-byte association | 1 | `S297_LOADER_ASSOCIATION_UNPROVED` |
| Target before inline advance | 1 | `S297_PRE_ADVANCE_TARGET_UNPROVED` |
| Separate wrong-resource control | 1 | `S297_WRONG_RESOURCE_BLOCKED` |

No static hash/live-byte substitution, mutable request proxy, helper stamp,
global counter, receipt resealing or rollout is permitted in diagnosis or work.
Only `s297/` and proportionate tracking updates change. Ranks 1–6 and 8–9 are
not executed; s254–s296, game/scripts, runtime, contracts, shared sampler,
thresholds and validators remain unchanged. Source-first runtime qualification
is incomplete; no gameplay mechanism is implemented or marked complete.
No deployment or production admission.

```sh
PYTHONPATH=. python3 evidence/sampling-upgrade/s297/diagnose.py --output /tmp/s297.json
PYTHONPATH=. python3 evidence/sampling-upgrade/s297/diagnose.py --output /tmp/s297.json --require-loader-attestation # expected exit 1
PYTHONPATH=. python3 evidence/sampling-upgrade/s297/diagnose.py --output /tmp/s297.json --require-pre-advance-target # expected exit 1
PYTHONPATH=. python3 evidence/sampling-upgrade/s297/diagnose.py --output /tmp/s297.json --require-wrong-resource-control # expected exit 1
PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s297 -p 'test_*.py'
PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s287 -p 'test_*.py'
PYTHONPATH=. python3 -m unittest tools.tests.test_loader_read_target_diagnosis tools.tests.test_loader_attestation_diagnosis tools.tests.test_capture_runtime_fighter tools.tests.test_sampling_native tools.tests.test_import_guards
python3 tools/verify.py
python3 tools/check_handoff.py
```

All 62 tests pass (9 new, 4 retained s287, 49 retained loader/capture tests).
Integrity, handoff and diff checks pass; the three proof gates retain exit 1.

[Gates](gates.json), [project checks](project-checks.json),
[scope audit](scope-audit.json) and [manifest audit](manifest-audit.json) retain
actual outcomes. [Session timing](session-timing.json) records measured facility
and validation costs; initial reading/design and person-days remain unknown.
No Godot or contract check is required because neither implementation nor
contracts changed. Tests exercise evidence rejection boundaries, not invented
Flash behavior or a synthetic successful loader association.
