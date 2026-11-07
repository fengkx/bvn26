# s350 — AFTER-s344 rank #6: Terminal callback

Base: `423f0518` (s349 #227 squash). Branch: `feat/s350-terminal-callback`.
Authority: [unchanged AFTER-s344 rank #6](../next-fix-priority-after-s344.md).
Only rank #6 executes; ranks 1–5 delivered, ranks 7+ planning only.
Historical authority wording stays unchanged; no re-ranking.
`production_admitted=false`; `native_parity_proven=false`; M0-02 pending.

## Result and independent route

**Loaded closure/body, owner generation and activation through a channel that
survives logger replacement to dispatcher continuation remain unproved.**
No live callback association was obtained. Off/on qualification and fresh terminal
inventory were not executed. Zero mechanism/product obligations closed.

The new [extractor](extract_native.py) pursues a native numeric return-dispatch
route independent of the replaceable `_root.aiEvent` property. It reads the
receipt-pinned player from disk, verifies the complete retained s303 Mach-O
metadata, fetch/dispatch bytes and table, then selects numeric entry `0x3e`.
The [Adobe SWF specification](https://www.flashrealtime.com/content/dam/Adobe/en/devnet/swf/pdf/swf_file_format_spec_v10.pdf)
identifies ActionReturn as `0x3e`. That opcode association motivates the route;
it does not identify the executing callback or prove a normal outer return.
No retained observer adapter is inventoried again or installed.

[Native route](native-route.json) and [disassembly](return_arm_prefix.txt) record:

- Player SHA-256 `8d4c1f5934adae809b5f4ce4f6ca7c64d4260df46bb3eb9c41fe32be2ee905be`;
  Mach-O UUID `067c4cfe5b2a3424aaa01fae2df056eb`, image base `0x100000000`.
- Table `0x12cf44`, entry `0x12d02c`, signed relative displacement to `0x124fef`.
  The table/fetch bytes are retained validation, not new progress.
- New bounded prefix `[0x124fef, 0x125003)`: 20 bytes / four instructions.
  It loads `[rbp-0x568]`, dereferences offset `0x58`, tests the resulting value,
  and branches to `0x12712a` when zero; fallthrough is `0x125003`.
  These are raw register/access relations, not owner, closure or activation types.
- Discovery decoded at most 128 bytes from the numeric target. Only the first
  basic-block prefix is retained as the route; neither outgoing branch is followed.
  Discovery's later displayed instructions do not establish continuation coverage.

This is a **new static disk observation**, not a replacement-surviving observer,
loaded identity resolver or callback-completion measurement. The route stops at
its first branch without a binding between this generic interpreter path and the
archived root callback. No breakpoint is set and no player is launched or attached.
An explicit Return handler also cannot cover structural fallthrough, unwind or
process termination by assumption. A usable channel still requires independent
loaded-body and uninterrupted owner/closure generation resolution, activation
entry, replacement and matching dispatcher continuation/outcome. The selected
register slot or its pointer cannot provide that identity. No claim is made that
such a facility is impossible; this bounded attempt has not established it.

## Locked evidence and missing measurements

[Diagnosis](diagnosis.json) reproduces and embeds the **complete locked s341
result**, recursively validating s332/s323/s314/s304 and retained terminal tooling.
Old suffix, custody, serializer and source ordering results are validation only.
[Input pins](input-sha256.json) lock all s341 files and its direct inputs, authority
and native route dependencies. [Route pins](route-sha256.json) bind new code,
bytes and disassembly. Portable diagnosis uses retained bytes and pins; it does
not require the original developer's binary location or a live player.

[Binding attempt](binding-attempt.json) targets the instrumentation root
`onEnterFrame` installed by archived `patches/main/frame_10/DoAction.as`, not an
asserted authored gameplay callback. Loaded closure/body, owner/defining-scope/
closure generations, activation, lifetime, replacement survival, continuation and
outcome all remain null. Activation entry, done-producing invocation, closing
invocation, callback/logger replacement, quit request and dispatcher continuation
remain distinct unobserved boundaries. Null does not mean absence of execution.
Done and closing invocations cannot be identified by shared display/fight counters.

First bind the same loaded closure, owner generation and activation across logger
replacement to its dispatcher outcome. Then qualify observer off/on and preservation;
only then inventory. All three off/on witnesses are null. No host timestamp or
pointer identity, assignment/inner-call marker as outer return, silence-as-return,
suffix threshold, trimming or random tape changes. No proof override/trace import.
Even a qualified single callback would not prove terminal completeness.

## Reproduction and gates

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 evidence/sampling-upgrade/s350/diagnose.py --output /tmp/s350.json
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s350 -p 'test_*.py'
# Supply any local copy of the receipt-pinned player; the extractor rejects other bytes.
PYTHONDONTWRITEBYTECODE=1 python3 evidence/sampling-upgrade/s350/extract_native.py "$PLAYER_BINARY" --output-dir /tmp/s350-native
PYTHONDONTWRITEBYTECODE=1 python3 evidence/sampling-upgrade/s350/recheck_native.py --binary "$PLAYER_BINARY"
python3 tools/verify.py
python3 tools/check_handoff.py
```

The optional extraction needs LLVM-compatible `objdump` on PATH. Recorded command
arguments use `<receipt-pinned-player>`; log headers are normalized to that token.
The optional recheck defaults to the path in the pinned s346 receipt; `--binary`
overrides that location for other hosts. Missing local files are facility errors,
not observations of callback absence. The input SHA-256/UUID, relative addresses,
exact bytes and hashes carry custody,
not the host path. Re-extraction comparison excludes no route fields.

Base diagnose exit 0 means package consistency only. Each proof flag and their
combined invocation exit 1: `--require-independent-channel`,
`--require-logger-replacement`, `--require-callback-completion`, `--require-off-on`,
`--require-terminal-completeness`. Codes are `S350_<FLAG>_UNPROVED`; invalid pins
or invented witnesses fail separately as `S350_EVIDENCE_INVALID`.
[Gate receipts](gates.json) and [project checks](project-checks.json) record actual
commands, exits, timings and logs. Tests preserve unknowns, reject proxy identities,
source markers promoted to execution, changed route bytes and premature controls;
they do not encode assumed gameplay behavior. Unchanged s341/s332/s323/s314/s304/
s293/s284 and shared terminal suites are rerun. No runtime or contract change
requires Godot or contract validation.

## Source-first, scope and custody

1. Complete archived root action and callback hash remain in s304/s314/s293;
   the numeric opcode reference does not bind the loaded callback.
2. No PlaceObject/MOVE or instance lifetime is changed or newly observed.
3. Source explicit return, body end, property replacement and native dispatcher
   return remain separate; the disk branch proves none of their execution.
4. Tests protect evidence custody and unknowns, not invented runtime invariants.
5. No fresh original/Godot same-input comparison; parity remains unproved.

Only s350 and minimal STATUS/SAMPLING_UPGRADE/tasks/manifest tracking change.
All prior s254–s349 evidence, authority, game/, scripts/, runtime, contracts and
shared tooling remain byte-identical. Zero builds, launches, attaches, memory reads,
helper installations or captures; no other rank executes.
[Scope audit](scope-audit.json), [manifest audit](manifest-audit.json) and
[artifact index](artifact-sha256.json) retain custody. The artifact index excludes
itself and caches. [Timing](session-timing.json) measures packaging/checks, excluding
initial reading/discovery and later commit/push/PR; person-days unknown.
Draft PR only; no ready marking, merge or deployment. Green checks do not prove parity.

Validation: **125 tests pass**. Base exit 0; all five individual proof gates
and their combined invocation exit 1. Exact native route re-extraction matches.
Integrity, handoff and whitespace checks exit 0; protected diffs are zero.
