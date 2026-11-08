# s360 — AFTER-s353 rank #7: AImain relative reference

Base: `0453b6172279cbfbb9b2d74049f49a6ed38d5a00` (s359 #237 squash).
Branch: `feat/s360-aimain-reference`.
Authority: [unchanged AFTER-s353 rank #7](../next-fix-priority-after-s353.md).
Ranks 1–6 delivered; ranks 8+ planning only. No re-ranking.
`production_admitted=false`; `native_parity_proven=false`; M0-02 pending.

## Independent observation

**One static relative text-to-code association is proved; the parent/depth object
resolver and separate saved-reference native dereference remain unproved.**
Live generations and clearing/replacement/free/reuse/pool controls were not run.
Zero mechanism/product obligations closed; zero new native runtime observations.

The new [extractor](resolve_relative.py) checks the receipt-pinned player's
`__TEXT,__text` range `[0x100002000,0x100fb5801)` for exactly seven-byte REX.W
LEA RIP+signed-disp32 encodings targeting two already locked s343 addresses.
This is an independent relative-address route, not a repeated name or absolute
pointer inventory. It rejects any binary with a different SHA-256.

- The initial bounded target `getDepth` at `0x10107c9c2` has zero matching encodings.
- `_parent` at `0x10119efe1` has seven byte-pattern candidates. All are retained in
  [relative-attempt.json](relative-attempt.json); six remain unvalidated boundaries.
- Decode the candidate with the shortest distance from its LC_FUNCTION_STARTS
  predecessor (51 bytes), tie-breaking by address. The 96-byte function interval
  `[0x1000bfcc0,0x1000bfd20)` contains 30 instructions. The complete interval was
  inspected, including its remaining branch and return; no callee was expanded.
- At `0x1000bfcf3`, bytes `48 8d 35 e7 f2 0d 01` form
  `RSI = next_RIP(0x1000bfcfa) + signed_disp32(0x10df2e7) = 0x10119efe1`.
  `RBX -> RDI` follows, then the direct call at `0x1000bfcfd` targets
  `0x10005d960`. Its result byte is tested and a conditional branch follows.

The Mach-O function-start stream and section mapping provide disk boundaries.
[LLDB disassembly](selected-disassembly.txt) independently checks instruction
boundaries; [receipt](disassembly-receipt.json) pins the actual debugger and
command. Portable re-extraction uses only Python's standard library and exact
instruction bytes/boundaries; LLDB is not required for package diagnosis.
The binary path defaults to the unchanged s343 receipt; `--binary` permits an
arbitrary local path only when its bytes match that receipt.

This proves a code instruction forms the address of `_parent` text and passes it
to a call. It does **not** prove that call resolves a parent, implements depth
lookup, returns an object, or executes in AImain. No adjacent word is a function
pointer. The other six matches may start inside instructions. The negative depth
result covers only this encoding and exact address, not other encodings, relative
tables, enclosing-list-base references or runtime interning. Function symbols
printed by LLDB are generated labels, not recovered source identities.

## Separate saved-reference frontier

[Saved-reference attempt](saved-reference-attempt.json) is explicitly blocked
before native dereference. The retained `_global.s261Receiver -> saved` source
read does not locate or decode an AS2 value in the native process. Its native
location, representation, dereference instructions and result allocation generation
remain null. The new parent-text argument supplies none of these prerequisites;
neither that string, a stack/result slot nor the candidate callee is substituted
for a saved referent. No saved-name search, guessed address or new live measurement
was performed. This unresolved derivation is not counted as progress.

Next evidence must independently establish the native parent/depth resolver and
the saved-value representation/dereference. Then bind loaded-module, parent,
saved-value and result generations, followed by uninterrupted observation from
before allocation through actual content clearing, replacement, free and reuse,
including internal pool checkout/return and deferred-free ordering. No allocator
imports as pool coverage, pointer-only identity, deletion-as-clearing or token-loss
inference. Missing measurements are not observed negatives.

## Retention and reproduction

The complete locked s351 diagnosis is replayed and compared unchanged, including
its portable retained chain. This is retention validation, not new proof. Input
pins cover s351, its inherited inputs and the authority. Route pins cover the new
extractor, raw record, disassembly receipt and separate saved-reference attempt.

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 evidence/sampling-upgrade/s360/diagnose.py --output /tmp/s360.json
PYTHONDONTWRITEBYTECODE=1 python3 evidence/sampling-upgrade/s360/resolve_relative.py --binary /path/to/receipt-matching-player --check
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s360 -p 'test_*.py'
python3 tools/verify.py
python3 tools/check_handoff.py
```

Base exit 0 establishes package consistency only. `--require-relative-code-association`
exits 0 for the narrowly stated static byte relation. Six native proof flags exit 1:
`--require-parent-depth-resolver`, `--require-saved-reference`,
`--require-slot-reference`, `--require-content-clearing`, `--require-replacement`,
`--require-allocation-identity`. Combined flags exit 1. Invalid evidence is reported
separately as `S360_EVIDENCE_INVALID`; there is no proof override.
Tests reject changed custody, relative arithmetic and static-to-live promotion;
synthetic byte fixtures test extraction mechanics, not Flash semantics.

[Gates](gates.json), [project checks](project-checks.json), [scope audit](scope-audit.json),
[manifest audit](manifest-audit.json), [artifact hashes](artifact-sha256.json) and
[timing](session-timing.json) record actual exits, scope and measured work.
No runtime or contract change requires Godot or contract checks.

## Source-first and scope

1. Retained Yijiao Sprite455 frame1 initCtrl unload, Sprite3 frame1 stop and no
   frame2 DoAction remain authoritative; no new frame semantics inferred.
2. Original placement evidence is unchanged; no live placement/lifetime observed.
3. No timeline, label exit or scheduling changes.
4. Tests protect custody and unknowns, not guessed allocation behavior.
5. No fresh original/Godot same-input comparison; native parity remains unproved.

Only s360 and minimal STATUS/SAMPLING_UPGRADE/tasks/manifest tracking change.
All s254–s359 trees, authority tables, game/scripts, runtime, contracts and shared
sampler/threshold/validator remain unchanged. Zero builds, player launches,
attaches, process-memory reads, helper installations or captures. Disk-only LLDB
target creation is not a player launch. Timing excludes initial reading, branch
creation and subsequent commit/push/PR; person-days unknown. Draft PR only,
no ready marking, merge or deployment.

Final local validation: **143 tests pass**. Disk re-extraction, verify.py,
check_handoff.py and whitespace checks exit 0; base/static-association exit 0;
six native proof flags and their combined invocation exit 1 as expected.
