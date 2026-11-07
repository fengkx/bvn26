# s358 — AFTER-s353 rank #5: Loader consumer

Base: `77975d7b` (s357 #235 squash). Branch: `feat/s358-loader-consumer`.
Authority: [unchanged AFTER-s353 rank #5](../next-fix-priority-after-s353.md).
Ranks 1–4 delivered as s354–s357 remain closed; ranks 6+ planning only.
No re-ranking. `production_admitted=false`; `native_parity_proven=false`;
M0-02 pending. Zero mechanism/product obligations closed.

## Result: executed consumer association remains unproved

The independent route resolves **one import association**, not one executed P1
consumer. No immutable request generation, real returned/consumed ranges or
pre-inline-advance target was obtained. Normal qualification remains false;
wrong-resource control and observer qualification were not executed.

The hypothesis was that resolving s348's first opaque external call could expose
a request/read-return observation entry. Instead of repeating the caller/interface
inventory or copying the prior callee analysis as progress, [the extractor](extract_native.py)
reads the receipt-matching player's Mach-O section and indirect-symbol metadata:

- Full binary SHA-256 `8d4c1f5934adae809b5f4ce4f6ca7c64d4260df46bb3eb9c41fe32be2ee905be`,
  UUID `067c4cfe5b2a3424aaa01fae2df056eb`, image base `0x100000000`.
- The retained 50-byte s348 callee is reread as an anchor only. Its first call
  at `0x498d31` leads to `0xfb680a`; this call relation is old evidence.
- The new association selects exactly one aligned six-byte `__stubs` entry:
  index 684, bytes `ff25d0ce4f00`. The signed RIP-relative jump names a pointer
  slot at module-relative `0x14b36e0`, whose live value is **not** read.
- Section reserved1 plus stub index gives indirect-table entry 684; that dword
  selects symbol 936. Its nlist entry and NUL-terminated string identify the
  undefined external import `_pthread_mutex_lock` (type 1, section 0, value 0).
  Value 0 is an undefined-symbol metadata value, never consumed resource data.

[Native route](native-route.json) retains exact file offsets and bytes for the
selected section, table commands, indirect entry, symbol entry/string and stub.
No provider code, second call, tail-jump target or other rank is expanded.
The initial discovery read inspected load-command metadata only. The extractor
uses the existing s303 Mach-O parser without modifying it; no new disassembler
or installed helper is required. Symbol spelling does not prove execution,
loaded provider identity, lock acquisition, return status, field type, ownership
or lifetime. In particular `[rbx+0x38]` is not promoted to a request generation.
This route supplies no usable live resolver; it does not prove one impossible.

[Binding attempt](binding-attempt.json) keeps all eight boundaries and live fields
null, including partial/failed reads and uninterrupted initialization/use/unload/
replacement lifetime. Null is missing evidence, not a zero byte or empty range.
The s321 initialized-zero ambiguity is unchanged. Disk code bytes are not actual
returned or consumed bytes; mutable slots and static candidates are not identity
or execution. The retained tail jump is not an observed return.

## Custody and gates

[Diagnosis](diagnosis.json) embeds the complete locked s348 diagnosis and replays
its recursive Loader chain. That replay is retained validation only, not new
progress. [Input pins](input-sha256.json) cover all s348 files, direct pinned inputs,
parser, receipt and authority. [Route pins](route-sha256.json) protect this slice's
extractor, import observation and binding record. There is no proof-import override.
Tests reject fabricated measurements, initialized zero, disk bytes, mutable slots,
static execution, premature controls and corrupted import associations.

From the repository root:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 evidence/sampling-upgrade/s358/diagnose.py --output /tmp/s358.json
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s358 -p 'test_*.py'
PYTHONDONTWRITEBYTECODE=1 python3 evidence/sampling-upgrade/s358/recheck_native.py --binary "$PLAYER_BINARY"
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 evidence/sampling-upgrade/s358/run_checks.py
```

The binary argument accepts any location containing the receipt-matching binary;
omitting it uses the historical s266 receipt's engine path. All new tool paths
are repository-relative; extraction uses only Python standard-library operations,
so an exact copy of the binary can be rechecked on another platform. No host path
is treated as identity. `run_checks.py` uses that receipt default for re-extraction.

Base diagnose exit 0 means evidence consistency only. Five individual proof flags
and their combined invocation exit 1: `--require-consumer-request`,
`--require-returned-consumed-ranges`, `--require-pre-advance-target`,
`--require-loader-attestation`, `--require-wrong-resource-control`.
Codes are `S358_<UPPERCASE_FLAG_WITH_UNDERSCORES>_UNPROVED`.
Changed pinned evidence or fabricated bindings fail with `S358_EVIDENCE_INVALID`.
Actual commands, exits and durations are in [gates](gates.json) and
[project checks](project-checks.json); logs include the s348 retained test chain,
local unittest, re-extraction, verify, handoff and whitespace checks.

## Missing proof and source-first boundary

First independently bind an actually executed P1 consumer and immutable request
generation. Join real read status and returned ranges to consumed subranges,
including partial/failed reads, and capture the actual target before inline
`loadStep++` advances to the next load. Preserve uninterrupted target/request
lifetime and qualify observer effects. Only then execute a Yihu-for-Yijiao
wrong-resource control with expected Yijiao identity unchanged and real errors
and ranges retained. An import name does not discharge any of these joins.

1. Locked `scripts/main.json` → `DefineSprite_1900/frame_1/DoAction.as` is the
   shared Loader source. No per-frame behavior is changed.
2. No fresh PlaceObject/MOVE or instance-generation observation was obtained.
3. Retained `LO.onLoadComplete(target)` ignores target and advances inline;
   a later slot cannot identify the previous load's target.
4. Tests lock byte provenance and unobserved boundaries, not successful reads.
5. No fresh original/Godot same-input run; native parity remains unproved.

Zero builds, launches, attaches, memory reads, installations or captures.
Only s358 plus minimal STATUS/SAMPLING_UPGRADE/tasks/manifest tracking changes.
All s254–s357 evidence and priority tables remain unchanged, as do game/, scripts/,
runtime, contracts, shared sampler/threshold/validator. No resealing or rollout.
Godot and contract checks are not applicable. Delivery is a Draft PR; no ready
marking, merge or deployment. [Scope](scope-audit.json), [manifest audit](manifest-audit.json),
[artifact hashes](artifact-sha256.json) and [timing](session-timing.json) record
custody. Timing excludes initial reading/discovery and later Git/PR work;
person-days remain unknown. Artifact hashes exclude themselves and caches.

Validation: **119 tests pass** (9 s358 + 110 retained). Base exit 0; five
individual proof flags and the combined invocation exit 1. Re-extraction matches;
verify, handoff and whitespace checks exit 0. Protected-path diffs are zero.
