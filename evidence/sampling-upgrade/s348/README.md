# s348 — AFTER-s344 rank #4: Loader consumed bytes

Base: `85fdee81` (s347 #225 squash). Branch: `feat/s348-loader-consumed`.
Authority: [unchanged AFTER-s344 rank #4](../next-fix-priority-after-s344.md).
Only rank 4 executes. Ranks 1–3 deliveries stay closed; ranks 5+ planning only.
The table's historical planning wording is unchanged. No re-ranking.
`production_admitted=false`; `native_parity_proven=false`; M0-02 pending.

## Result: executed association remains unproved

No executed P1 consumer, immutable request generation, actual returned/consumed
ranges or target before inline advance was independently bound. Zero new runtime
observations and zero mechanism/product obligations closed. This is a failed
binding route with honest failure gates, not successful Loader qualification.

The independent attempt follows the unresolved external call before the retained
wrapper's final return-value copy. Unlike s339's blocked ledger, it reads the
receipt-pinned native callee's bytes; it does not repeat a caller/interface
inventory. The hypothesis was that the exit callee could expose an independently
usable request or buffer association before control returns to the candidate
consumer. The bounded route does not establish such an association.

[Extractor](extract_native.py) validates the full binary SHA-256
`8d4c1f5934adae809b5f4ce4f6ca7c64d4260df46bb3eb9c41fe32be2ee905be`
and Mach-O metadata, rereads the retained wrapper anchor, and extracts 50 new
bytes at module-relative `0x498d20–0x498d52` (end exclusive).
The initial discovery read was bounded to 128 bytes; only the first 50 bytes
through the tail transfer are retained/analyzed. No target callee is expanded.
[Native route](native-route.json) and [disassembly](exit_callee.txt) establish:

- Retained `0x4b35c8` loads `[rbx+0xa0]` into RDI; call `0x4b35cf` reaches
  `0x498d20` before the retained R13D→EAX copy. This anchor is old evidence.
- New callee saves RDI in RBX and passes its `+0x38` address to call `0x498d31`,
  whose destination is `0xfb680a`.
- Conditional on that call returning normally, `0x498d36` writes literal 1 to
  `[rbx+0x78]`, then passes the same `+0x38` address to call `0x498d3d` → `0xfb6816`.
- Conditional on the calls returning normally, the suffix restores saved
  registers and tail-jumps at `0x498d4d` → `0xfb67b0`, passing the entry argument
  plus 8 in RDI. No explicit RET occurs in this bounded window.

These are static operand/control-transfer relations, not executed transitions.
The first call already makes effects/preservation opaque; a tail jump is not an
observed return. No native class, lock semantics, request field, generation or
buffer ownership is assigned to these offsets. The byte write is not a returned
resource byte. No ABI convention proves live preservation. This route stops at
external effects and does not supply an independent live resolver; it does not
prove that another route is impossible.

The s321 caller's local `[rbp-0x29]` is still initialized to zero before its
one-byte read call. Neither the new callee nor replay resolves whether a later
load sees returned data or preserved initialization. Disk code bytes are not
consumed resource bytes. A mutable slot, static candidate, breakpoint hit,
configured filename or post-advance target cannot replace the required join.

[Binding attempt](binding-attempt.json) leaves all eight boundaries and live
fields null, including read status, partial/failed-read behavior and lifetime.
Null is neither a zero byte nor an empty range. Normal qualification is false;
wrong-resource control and observer qualification were not executed.

## Gates and reproduction

[Diagnosis](diagnosis.json) reproduces the complete locked s339 diagnosis and its
recursive Loader chain. [Input pins](input-sha256.json) cover every s339 file,
its direct pinned inputs, authority and extraction dependencies. This replay is
retained validation only, never new progress. [Route pins](route-sha256.json)
protect the separate extraction; tests additionally verify exact contiguous
instruction coverage and signed transfer targets. No trace-import/proof override.

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 evidence/sampling-upgrade/s348/diagnose.py --output /tmp/s348.json
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s348 -p 'test_*.py'
PYTHONDONTWRITEBYTECODE=1 python3 evidence/sampling-upgrade/s348/extract_native.py '/Users/fengkx/me/code/flash-player/Flash Player.app/Contents/MacOS/Flash Player Debugger' --output-dir /tmp/s348-reextract
python3 tools/verify.py
python3 tools/check_handoff.py
```

Base exits 0 for evidence consistency only. Each proof flag and the combined
invocation exit 1: `--require-consumer-request`,
`--require-returned-consumed-ranges`, `--require-pre-advance-target`,
`--require-loader-attestation`, `--require-wrong-resource-control`.
Codes: `S348_<UPPERCASE_FLAG_WITH_UNDERSCORES>_UNPROVED`.
Changed inputs or fabricated bindings fail with `S348_EVIDENCE_INVALID`.
[Gates](gates.json) and [checks](project-checks.json) record actual commands,
exits, logs and measured durations. Re-extraction must match route/log bytes.
Tests reject initialized-zero, disk-byte, mutable-slot and static-candidate
promotion, missing boundaries and premature controls. They are custody checks,
not synthetic Flash proof.

## Missing qualification and source-first

Next independently bind an actually executed P1 caller/consumer and immutable
request generation. Join real read status and returned ranges to consumed
subranges, including partial/failed reads; observe the target before
`loadStep++` invokes the next load inline. Preserve same-request initialization,
use, unload and replacement lifetimes; qualify observer effects. Only after
normal qualifies may a Yihu-for-Yijiao wrong-resource control execute with
expected Yijiao identity unchanged and actual errors/ranges retained.

1. Locked `scripts/main.json` → `DefineSprite_1900/frame_1/DoAction.as` remains
   the shared P1/P2/assist/sound Loader source; no script behavior changed.
2. No new PlaceObject/MOVE or instance-lifetime observation.
3. `LO.onLoadComplete(target)` ignores target and advances inline; no later slot
   is promoted to the prior target association.
4. Tests preserve source/native bytes and unknowns, not assumed successful reads.
5. No new original/Godot same-input run; native parity remains unproved.

Zero builds, launches, attaches, memory reads, helper installations or captures.
Only s348 and minimal STATUS/SAMPLING_UPGRADE/tasks/manifest tracking change.
All s254–s347 evidence, authority tables, game/, scripts/, runtime, contracts,
shared sampler/threshold/validator remain unchanged. No resealing or rollout.
Godot/contract checks are not applicable. Delivery is a Draft PR only; no ready
marking, merge or deployment. [Scope](scope-audit.json), [manifest audit](manifest-audit.json),
[artifact hashes](artifact-sha256.json) and [timing](session-timing.json) retain
custody. Artifact index excludes itself/caches. Timing excludes initial reading,
design/discovery and later commit/push/PR; person-days remain unknown.

Validation: **110 tests pass**. Base exit 0; five individual proof flags and
combined proof invocation exit 1. Re-extraction matches exactly. Integrity,
handoff and whitespace checks exit 0. Protected diffs are zero.
