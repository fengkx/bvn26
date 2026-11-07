# s347 — AFTER-s344 rank #3: Yulong erasure

Base: `9592c66e` (s346 #224 squash). Branch: `feat/s347-yulong-erasure`.
Authority: [unchanged AFTER-s344 rank #3](../next-fix-priority-after-s344.md).
Only rank 3 executes; ranks 1–2 deliveries stay closed, ranks 4+ planning only.
The table's historical planning wording is not rewritten. No re-ranking.
`production_admitted=false`; `native_parity_proven=false`; M0-02 pending.

## Result: measurement prerequisite still unproved

No same-input original/candidate activation pair, defining scope or erasure
measurement was obtained. Zero independent runtime observations and zero
mechanism/product obligations closed. Null measurements are not zero effects.

The independent attempt starts from numeric opcode 142 (`0x8e`) in the locked
s294 original/candidate function headers, rather than repeating the s338 CFG
or adapter inventory. [extract_native.py](extract_native.py) checks the complete
receipt-pinned disk player and Mach-O metadata, re-reads the retained s303
numeric dispatcher/table and extracts a separate arm and first callee branch.
The shared dispatcher is an anchor only; no Chad or ones experiment executes.

[Native route](native-route.json), with module-relative, unslid addresses:

- Table `0x12cf44`, entry `0x12d16c` for unsigned `0x8e-4`, resolves to `0x124ad1`.
- [Dispatch arm](dispatch_arm.txt), `0x124ad1–0x124aec` (27 bytes): saves R9 at
  `[rbp-0x618]`, copies R8 to R14, passes address `[rbp-0x160]` in RDI and 1 in ESI;
  the direct call at `0x124ae7` resolves to `0x19e460`.
- [Callee prefix](callee_prefix.txt), `0x19e460–0x19e46e` (14 bytes): sets up RBP,
  compares byte `[rdi+0x16]` with zero, branches to `0x19e506` if unequal.
  Fallthrough is `0x19e46e`. Neither successor is expanded.

Discovery read at most 128 bytes at each start; the 41 retained instruction bytes
prove only this static numeric table/call/access relation. The binary SHA-256 is
`8d4c1f5934adae809b5f4ce4f6ca7c64d4260df46bb3eb9c41fe32be2ee905be`.
The retained source opcode motivates this route; it does not prove that a loaded
Yulong definition executes it. No AVM type, scope ownership, activation allocation
or lifetime is assigned to these addresses/registers. In particular, the passed
stack address and tested byte are not independently identified defining scopes.
The dispatcher/table and old source headers are retained context, not new proof.

The route stops before a loaded-body-to-definition association. It yields no
independent invocation or defining-scope channel, so no live pair was selected.
This is a bounded failed route, not a claim that independent resolution is
impossible. [Binding attempt](binding-attempt.json) keeps run/body/input tape,
activation/scope/lifetime and all six paired boundary states null: initialization,
enumeration, member access, coercion, overwrite, no-overwrite null return.
An overwrite-path observation would not establish the separate return path.
No observer was installed and no observer controls were executed.

Next evidence must independently associate the loaded original/candidate bodies,
same-input invocation pair and defining scopes, continuously preserving their
lifetimes through these six boundaries. Measure slot visibility/effects before
qualifying helper effects and observer off/on controls. No inferred harmlessness,
hidden access, early helper, extra hitTest, ancestor pn or enlarged boxes.

## Gates and reproduction

`diagnose.py` pins and reproduces the complete locked s338 diagnosis, recursively
retaining the prior Yulong tooling. Replay is validation only, not new progress.
There is no trace-import or proof override. Changed pins, prior diagnosis or
fabricated binding/boundary values fail closed.

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 evidence/sampling-upgrade/s347/diagnose.py --output /tmp/s347.json
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s347 -p 'test_*.py'
python3 tools/verify.py
python3 tools/check_handoff.py
PYTHONDONTWRITEBYTECODE=1 python3 evidence/sampling-upgrade/s347/extract_native.py '/Users/fengkx/me/code/flash-player/Flash Player.app/Contents/MacOS/Flash Player Debugger' --output-dir /tmp/s347-reextract
```

Base diagnosis exits 0 for package consistency only. Each of
`--require-activation-pair`, `--require-activation-scope`,
`--require-activation-erasure`, `--require-observer` exits 1, as does the combined
invocation. Codes are `S347_<UPPERCASE_FLAG_WITH_UNDERSCORES>_UNPROVED`.
[Gates](gates.json) and [project checks](project-checks.json) retain actual exits,
commands, durations and logs. Tests protect provenance, unknowns, false identity,
false zero erasure, missing boundaries and CLI gates; no synthetic behavior proof.
Re-extraction compares the entire route and both disassembly logs byte-for-byte.

## Source-first and custody

1. Complete Sprite2 functions/operands remain locked in s294/s302/s309/s318.
2. Sprite345 frame188 depth28 k1atm and nested mian placement do not identify
   native activation or defining scope.
3. Sprite104 stop/goto/removal and explicit returns are retained; label end or
   missing observations are not return.
4. Tests enforce source provenance and honest unknowns, not assumed gameplay.
5. No fresh original/Godot same-input comparison; parity remains unproved.

Zero builds, player launches, attaches, memory reads, helper installations or
captures. No runtime/contracts/shared sampler changes; Godot and contract checks
are not applicable. Only s347 and minimal STATUS/SAMPLING_UPGRADE/tasks/manifest
tracking change. All prior s254–s346 trees and priority tables remain unchanged.
[Input pins](input-sha256.json), [route pins](route-sha256.json),
[scope audit](scope-audit.json), [manifest audit](manifest-audit.json) and
[artifact hashes](artifact-sha256.json) retain custody. Artifact index excludes
itself/caches. [Timing](session-timing.json) measures implementation/check wall
time, excluding initial reading/design and later commit/push/PR; person-days unknown.
Delivery is a Draft PR only, no ready marking, merge, deployment or product closure.

Validation: **132 tests pass**. Base exit 0; four individual proof gates and
combined proof gate exit 1. Re-extraction matches exactly. Integrity, handoff
and whitespace checks exit 0. Protected diffs are zero.
