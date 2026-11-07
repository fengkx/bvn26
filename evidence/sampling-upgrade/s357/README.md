# s357 — AFTER-s353 rank #4: Terminal callback

Base: `d12784cb` (s356 #234 squash). Branch: `feat/s357-terminal-callback`.
Authority: [unchanged AFTER-s353 rank #4](../next-fix-priority-after-s353.md).
Ranks 1–3 delivered as s354–s356 remain closed; ranks 5+ planning only.
No re-ranking. `production_admitted=false`; `native_parity_proven=false`;
M0-02 pending. Zero mechanism/product obligations closed.

## Result

**The loaded callback/owner/activation channel remains unproved.**
The independent numeric disk route extends the locked s350 return arm by one
bounded nonzero continuation, then stops at the next unresolved identity/effect
frontier. No retained adapter inventory is repeated as progress. No live callback
association, off/on qualification or fresh terminal inventory was obtained.

[Extractor](extract_native.py), [route](native-route.json) and
[disassembly](first_continuation.txt) record a fresh disk observation:

- Receipt-matching player SHA-256
  `8d4c1f5934adae809b5f4ce4f6ca7c64d4260df46bb3eb9c41fe32be2ee905be`,
  UUID `067c4cfe5b2a3424aaa01fae2df056eb`, image base `0x100000000`.
- Re-read and validate s350 dispatch/prefix bytes; these are retained validation.
  Select its nonzero fallthrough `0x125003`, not its zero target `0x12712a`.
- New bounded interval `[0x125003,0x125014)`: 17 bytes / three instructions.
  `cmp byte ptr [rax+0x40],0`; `mov rdx,[rbp-0x558]`;
  `jne 0x127146`, otherwise fall through to `0x125014`.
- This distinguishes the next byte predicate and branch operands. Neither field
  type nor relation to a loaded closure, owner or activation is established.
  Neither outgoing successor is pursued; no effect or outer return is inferred.

Initial discovery requested a 32-byte disassembly window and displayed two
following writes (the final instruction straddled that requested boundary).
Those displayed writes are **not** continuation/effect coverage. The retained
extractor reads exactly the 17-byte prefix, stops at its first branch and expands
neither successor. No callee, additional branch arm or other rank is investigated.

This route is independent of the replaceable `_root.aiEvent` property but is not
a usable observation channel merely because it is native code. Untyped addresses
and stack slots cannot identify generations. The first unresolved frontier is the
association of these values with the loaded archived callback and its uninterrupted
owner/closure/activation lifetime. No claim of debugger impossibility is made.
The explicit Return route does not establish structural-fallthrough, unwind or
process-termination coverage.

## Locked evidence and next requirement

[Diagnosis](diagnosis.json) embeds the **complete locked s350 diagnosis** and
recursively reproduces its retained tooling and s341 chain. This replay is not new
progress. [Input pins](input-sha256.json) bind all s350 artifacts, direct inputs
and authority; [route pins](route-sha256.json) bind the new byte observation.

[Binding attempt](binding-attempt.json) keeps loaded body, defining scope, owner
and closure generations, activation, replacement survival, dispatcher continuation
and outcome null. Its target is the archived instrumentation root `onEnterFrame`
in `patches/main/frame_10/DoAction.as`, not an asserted authored gameplay callback.
Entry, done-producing invocation, closing invocation, callback/logger replacement,
quit request and dispatcher continuation remain distinct unobserved boundaries.
Null is missing evidence, not absence of execution.

First independently resolve one loaded callback/body and uninterrupted owner,
closure and activation generations through replacement to the matching dispatcher
outcome. Then require observer off/on and preservation before terminal inventory.
Even one qualified callback would not prove terminal completeness. No pointer or
timestamp identity, inner-call marker as outer return, silence-as-return, suffix
threshold adjustment or tape change is accepted. No proof-import/override API.

## Reproduction

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 evidence/sampling-upgrade/s357/diagnose.py --output /tmp/s357.json
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s357 -p 'test_*.py'
PYTHONDONTWRITEBYTECODE=1 python3 evidence/sampling-upgrade/s357/extract_native.py "$PLAYER_BINARY" --output-dir /tmp/s357-native
PYTHONDONTWRITEBYTECODE=1 python3 evidence/sampling-upgrade/s357/recheck_native.py --binary "$PLAYER_BINARY"
python3 tools/verify.py
python3 tools/check_handoff.py
```

Diagnosis and tests use portable retained records. Optional extraction requires
LLVM-compatible `objdump` and any copy of the receipt-matching player; all other
binary bytes are rejected. Recheck defaults only to the pinned s346 receipt path;
`--binary` overrides it. Recorded extraction commands and log headers use
`<receipt-pinned-player>`. Host path is not identity. Missing facilities are errors,
not callback-absence evidence. Complete re-extraction records must match.

Base exit 0 means package consistency only. All five individual flags and their
combined invocation exit 1: `--require-independent-channel`,
`--require-logger-replacement`, `--require-callback-completion`, `--require-off-on`,
`--require-terminal-completeness`. Codes are `S357_<FLAG>_UNPROVED`;
invalid evidence separately fails as `S357_EVIDENCE_INVALID`.
[Gate receipts](gates.json) and [project checks](project-checks.json) record actual
exits, timings and output. Tests reject false identities, markers promoted to
execution, byte drift, changed prior results and premature off/on or inventory.
Retained s350 predecessor suites are rerun, with s350 itself and new s357 tests.

## Source-first and custody

1. Archived root source/callback hashes remain locked in the retained chain;
   numeric dispatch and this byte predicate do not bind loaded code.
2. No PlaceObject/MOVE or instance lifetime changed or newly observed.
3. Explicit Return, structural body end, replacement and dispatcher outcome stay
   distinct; no execution of any exit is claimed.
4. Tests protect custody and unknowns, not invented gameplay invariants.
5. No fresh original/Godot same-input comparison; parity unproved.

Only s357 and minimal STATUS/SAMPLING_UPGRADE/tasks/manifest tracking change.
Prior s254–s356, authority, game/, scripts/, runtime, contracts, shared samplers,
thresholds and validators remain byte-identical. Zero builds, launches, attaches,
memory reads, helper installations or captures. No runtime/contract changes need
Godot or contract checks. [Scope audit](scope-audit.json),
[manifest audit](manifest-audit.json), [artifact index](artifact-sha256.json) and
[timing](session-timing.json) record custody and measured packaging/check cost;
initial reading/discovery and later Git/PR work excluded, person-days unknown.
Draft PR only; no ready marking, merge or deployment.

Validation: **133 tests pass**. Base exit 0; five proof flags and combined exit 1.
Exact re-extraction, integrity, handoff and whitespace checks exit 0.
Protected paths have zero diff.
