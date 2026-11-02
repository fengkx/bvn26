# s313 — AFTER-s308 rank #5: Loader consumed bytes

Base: origin/master `435d7f2aa60ba81e5c754fc45c984ff4f92984af` (s312 #190).
Branch: `feat/s313-loader-attestation`.
Authority: [AFTER-s308 rank #5](../next-fix-priority-after-s308.md).
**Evidence-only, honest-unproved.** `production_admitted=false`;
`native_parity_proven=false`; M0-02 pending; zero product obligations closed.
Only rank #5 is executed. Ranks 1–4 and 6–9 are excluded.

## Result

The first thin cut remains blocked: **no actual P1 consumer or immutable request
generation is resolved**. No live return/consumption/target join is claimed.
The new result is a bounded audit of the unresolved consumer boundary, not a
successful attestation or a new capture. Normal is unqualified; no wrong-resource
control ran. Lack of a resolver does not prove that native debugging is impossible.

[diagnose.py](diagnose.py) pins every retained s306 file and reproduces its complete
locked diagnosis, recursively revalidating 5,503 historical events. The 432-byte
wrapper and its API operands/branches remain closed s306 results. This slice
adds the complete call/return inventory and six byte-bound boundary witnesses:

| Boundary | Static fact | Missing live evidence |
| --- | --- | --- |
| `0x1004b3552` | Candidate API return site, retained from s306 | Executed count, buffer ranges and P1 membership |
| `0x1004b35e6`, `0x1004b3595`, `0x1004b35d4` | Copies eax→r14d, r14d→r13d and r13d→eax | Actual values, caller continuation and byte consumption |
| `0x1004b35cf` | Exit call resolves to `0x100498d20`, before final return copy | Callee effects and preservation; no ABI-based live proof |
| `0x1004b35e5` | Sole explicit wrapper return | Executed caller and immutable request generation |
| `0x1004b35c0` | Cleanup path writes zero to rbx+0x18 | Stream lifetime and request ownership; this mutable slot is not a generation ID |
| `0x1004b3480/34d0/3573` | Three indirect calls use rax+0x400 | Actual targets and object types |

All **16** call sites, relative destinations, next-instruction addresses and the
single return are retained in [diagnosis.json](diagnosis.json). These are lexical
instruction facts, not an executed path or an exhaustive caller graph. No class,
request generation, lock semantics or consumption is inferred from rbx fields,
unnamed callees or return-register copies. No external callee was executed or
newly disassembled. Returned bytes and consumed bytes remain distinct unknowns.
The eight old observation fields plus consumed ranges and observer effects remain
null. Historical helper/initCtrl events and expected file hashes are not live
byte evidence. The diagnostic has no caller-supplied trace or proof override.

## Source-first and next prerequisite

1. Locked original/archived `scripts/main.json` →
   `DefineSprite_1900/frame_1/DoAction.as` shares one MovieClipLoader across P1,
   P2, both assists and sound. Source order is revalidated by s306's chain.
2. No new PlaceObject/MOVE or instance-lifetime evidence is obtained; a stream
   pointer or textual `_root.game[pr]` target does not establish native ownership.
3. `LO.onLoadComplete(target)` ignores target and calls `loadStep++` then
   `loadSteps[loadStep]()` inline. A later mutable current request may name the
   next load. No callback schedule or timeline exit is inferred.
4. Tests lock retained instruction/source facts and rejection boundaries only;
   they do not assert a synthetic successful association or gameplay behavior.
5. Historical same-input evidence is revalidated only. There is no new original
   run or Godot comparison, and the execution qualification remains incomplete.

Next, independently resolve one actual P1 consumer and immutable request
generation. Observe executed API returns and complete returned/consumed ranges
(or mapped ranges actually consumed), joined to the target **before** inline
loadStep advance. Qualify observer effects and same-request initialization/use,
unload and replacement separately. Only after normal qualifies may a separate
actual Yihu-for-Yijiao control run with expected Yijiao identity unchanged,
retaining supplied/returned/consumed bytes and errors. A breakpoint hit alone,
archive substitution, server delivery or static hash cannot establish this join.

## Gates and validation

| Requirement | Exit | Code |
| --- | --- | --- |
| Fixed-evidence audit | 0 | `S313_DIAGNOSIS_OK` |
| Actual P1 consumer/request generation | 1 | `S313_CONSUMER_REQUEST_UNPROVED` |
| Normal consumed-byte association | 1 | `S313_LOADER_ASSOCIATION_UNPROVED` |
| Target before inline advance | 1 | `S313_PRE_ADVANCE_TARGET_UNPROVED` |
| Separate wrong-resource control | 1 | `S313_WRONG_RESOURCE_BLOCKED` |

Changed pinned evidence exits 1 with `S313_EVIDENCE_INVALID`; it is not an
attestation failure disguised as a successful diagnosis.

```sh
PYTHONPATH=. python3 evidence/sampling-upgrade/s313/diagnose.py --output /tmp/s313.json
# Each flag independently expects exit 1:
# --require-consumer-request --require-loader-attestation
# --require-pre-advance-target --require-wrong-resource-control
PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s313 -p 'test_*.py'
PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s306 -p 'test_*.py'
PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s297 -p 'test_*.py'
PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s287 -p 'test_*.py'
PYTHONPATH=. python3 -m unittest tools.tests.test_loader_read_target_diagnosis tools.tests.test_loader_attestation_diagnosis tools.tests.test_capture_runtime_fighter tools.tests.test_sampling_native tools.tests.test_import_guards
python3 tools/verify.py
python3 tools/check_handoff.py
```

[Gates](gates.json), [checks](project-checks.json), [scope](scope-audit.json),
[manifest audit](manifest-audit.json), [timing](session-timing.json) and
[artifact hashes](artifact-sha256.json) retain outcomes. Hash index excludes
itself. Initial reading/design, initial diagnostic authoring and person-days are unknown;
the measured interval starts at the retained marker and excludes later commit/push/PR. No Godot/contract checks apply because neither changed.

Only s313 plus proportionate STATUS/SAMPLING_UPGRADE/tasks/manifest updates change.
No edits under s254–s312, game/, scripts/, runtime, contracts, shared sampler,
threshold or validator. No static hash as live bytes, mutable request proxy,
helper stamp, global counter, receipt resealing or rollout. Zero new builds,
launches, attaches, memory reads or captures. No other rank, merge or deployment.

Validation: **82 tests pass** (9 focused, 11 retained s306, 9 retained s297,
4 retained s287, 49 retained tools). Diagnosis exits 0; all four proof gates
exit 1. Integrity, handoff and whitespace checks pass. These checks do not
resolve the missing actual P1 consumer/request association.
