# s346 — AFTER-s344 rank #2: Independent ones clock

Base: `ac99df4d090d97409df7a9f58f039a7f99e93ea5` (s345 #223 squash).
Branch: `feat/s346-ones-clock`. Authority: [unchanged AFTER-s344 rank #2](../next-fix-priority-after-s344.md).
Only rank #2 executes under this goal. The table's “ranks 2+ planning” describes
s345; it is not rewritten. Rank #1 delivery stays closed; ranks 3+ remain planning.
`production_admitted=false`; `native_parity_proven=false`; M0-02 pending.
**Honest-unproved: no ten-frame target-entry route or independent outer lifetime channel.**

## Independent route attempted

Unlike s337's failed NUL-delimited name search, this attempt starts from the
receipt-pinned numeric native dispatch instructions. No names are searched.
The s303 dispatcher is reused as a static byte anchor only; no Chad experiment
or other rank is executed. [extract_native.py](extract_native.py) verifies the
complete binary hash and Mach-O metadata, rechecks the retained dispatcher/table,
then extracts a distinct numeric arm and callee prefix. The intended candidate
is opcode `0x9f` (GotoFrame2); the numeric route, rather than that semantic label,
is what these bytes establish. There is no claim that the actual ones method
call compiles to or executes this opcode.

[Byte-bound result](native-route.json), all addresses module-relative and unslid:

- Dispatcher `0x124a77–0x124a98` computes unsigned `opcode-4`, admits at most
  `0x9b`, reads a signed 32-bit offset from table `0x12cf44` and jumps to table+offset.
- For `0x9f`, the table entry is `0x12d1b0`; it resolves to `0x125f31`.
- [Arm](dispatch_arm.txt), `0x125f31–0x125f4a` (25 bytes): RSI gets the address
  of caller `[rbp-0x160]`; RDI gets qword `[rbp-0x558]`; RDX gets R9;
  RBX preserves R8. The direct call at `0x125f45` resolves to `0x1204c0`.
- [Callee prefix](callee_prefix.txt), `0x1204c0–0x1204e9` (41 bytes): incoming
  RDX/RSI/RDI are copied into R15/R12/RBX. EAX reads dword `[rbx+0x520]`;
  `test eax,eax; je 0x120504` ends the retained window. Fallthrough is `0x1204e9`.
  Neither successor is expanded. Discovery inspected up to 128 bytes at each
  start; only these bounded prefixes are retained and analyzed.

The 66 new instruction bytes are independently re-read from the locked disk
player, SHA-256 `8d4c1f5934adae809b5f4ce4f6ca7c64d4260df46bb3eb9c41fe32be2ee905be`.
They prove a static table→arm→callee-prefix relation, not actual execution,
target selection, frame entry, a native method resolver or ten-frame coverage.
The pre-existing dispatcher/table bytes are retained validation, not new progress.
The callsite-to-opcode join, continuation to the frame-entry effect and live
module/run binding remain missing. Actionless frames 2–10 cannot be inferred
from reaching an action interpreter, and even frame1 remains unqualified.

## Independent outer lifetime and controls

R9→RDX→R15 is independently readable register transport, **not outer identity**.
No ones object layout, allocation/removal/replacement hooks, loaded object
association or uninterrupted generation is derived. The numeric route supplies
no independent outer lifetime channel. No separate live lifetime experiment was
run; this is not an exhaustive search or proof that such a channel is impossible.
Helper generations, path/depth, glyph identity and a stable pointer do not fill
this gap.

[diagnose.py](diagnose.py) pins all s337 artifacts and reproduces its complete
locked diagnosis, recursively retaining the historical 26,828 events and existing
ones tooling. No historical report is reclassified as new progress. All ten
qualification rows remain unchanged/null for independent entry and order. The
four controls—isolated repeated target, changed target, same-depth replacement,
observer off/on—are explicitly unexecuted/unqualified. Fresh capture is blocked
before launch. Zero independent runtime observations and zero mechanism/product
obligations are closed.

Next evidence must join an actual ones caller to the executable frame-entry
effect for all ten targets, independently derive outer lifetime and bind both
to the same loaded module/run. Only then qualify the four controls, observing
selection, entry and following root/callback order with the independent channel
surviving observer off/on. Then, and only then, attempt fresh capture.

## Gates and reproduction

| Mode | Expected exit | Result |
| --- | --- | --- |
| Base diagnosis | 0 | S346_DIAGNOSIS_OK, admission false |
| --require-target-entry | 1 | S346_BYTE_BOUND_TARGET_ENTRY_UNPROVED |
| --require-outer-lifetime | 1 | S346_INDEPENDENT_OUTER_LIFETIME_UNPROVED |
| --require-independent-controls | 1 | S346_INDEPENDENT_CONTROLS_UNPROVED |
| --require-child-clock | 1 | S346_CHILD_CLOCK_UNPROVED |
| --require-fresh-capture | 1 | S346_FRESH_CAPTURE_BLOCKED |

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 evidence/sampling-upgrade/s346/diagnose.py --output /tmp/s346.json
# Each proof flag above separately must exit 1.
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s346 -p 'test_*.py'
python3 tools/verify.py
python3 tools/check_handoff.py
# Read-only re-extraction; use the receipt-matching installed player:
PYTHONDONTWRITEBYTECODE=1 python3 evidence/sampling-upgrade/s346/extract_native.py '/Users/fengkx/me/code/flash-player/Flash Player.app/Contents/MacOS/Flash Player Debugger' --output-dir /tmp/s346-reextract
```

[Gates](gates.json) and [project checks](project-checks.json) record actual
commands, exit codes, durations and logs. Re-extraction must match the entire
native record and both disassembly logs. Tests reject binary substitution,
route/provenance mutation, altered complete prior replay and fabricated proof;
register relations are locked to exact instruction bytes, not an assumed schedule.
Retained s337/s328/s319/s310/s301/s292/s282 and shared ones/countdown/sampling
checks are validation only. No contract/Godot checks apply without interface or
runtime changes.

## Source-first and custody

1. Retained s292/s337 source: Sprite1810 frame1 has `stop();`; frames2–10 have
   no actions. No empty actions are inserted or treated as neutral.
2. Outer Sprite1813 depth3 is distinct from glyph depth1 MOVE. Neither a glyph
   nor a helper generation is used as entry or native outer lifetime.
3. The timer uses `gotoAndStop`; no synthetic clock or label-end reset is added.
4. Tests protect byte provenance and honest unknowns, not invented scheduling.
5. No fresh original/Godot same-input comparison; native parity remains false.

Only s346 and minimal STATUS/SAMPLING_UPGRADE/tasks/manifest tracking change.
All prior s254–s345 trees, authority tables, game/, scripts/, runtime, contracts,
shared sampler/threshold/validator remain unchanged. No re-ranking, other-rank
execution, scene repair, cross-run images, build, player launch, attach, memory
read, capture, ready marking, merge or deployment.

[Input pins](input-sha256.json), [scope audit](scope-audit.json),
[manifest audit](manifest-audit.json) and [artifact hashes](artifact-sha256.json)
retain custody. Artifact index excludes itself and caches. [Timing](session-timing.json)
records implementation/check elapsed time, excluding initial reading/design and
later commit/push/PR. Person-days remain unknown. Package delivery is not
mechanism proof or product closure.

Validation: **118 tests pass**. Base exit 0; five individual proof gates and
combined proof gate exit 1. Re-extraction is byte-identical. Integrity, handoff
and whitespace checks exit 0. Scope audit confirms protected diffs are zero.
