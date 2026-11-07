# s354 — Post-s353 re-rank + rank #1 Chad bounded offset table

Base: `60dcfbd11953cbb107028a964cfd0a7b739091dd` (s353 #231 squash).
Branch: `feat/s354-after-s353-rerank`.
Authority: [AFTER-s353 rank #1](../next-fix-priority-after-s353.md).
Only new rank #1 executes; ranks 2+ are planning only. AFTER-s344 ranks 1–9
were delivered as s345–s353 and stay closed. `production_admitted=false`;
`native_parity_proven=false`; M0-02 pending; zero mechanism/product obligations closed.

## Ranking and retained replay

[Ranking pins](ranking-basis-sha256.json) cover s345–s353 complete diagnoses and
READMEs and all previous priority tables. Chad's exact table range/address rule
is the most concrete finite discriminator. Terminal moves ahead of Loader/P2
because s350 adds a byte-bound independent return arm; this does not establish
a callback identity. Ones remains an upstream scene prerequisite. Ranking is by
source-bounded discriminators, independent observations, downstream prerequisites,
then facility cost, not green-gate likelihood. No other-rank probe executes.

[Diagnosis](diagnose.py) pins every s345 artifact, replays its complete locked
report and embeds it unchanged, recursively retaining 9,493 historical events.
Retained validation is not new progress. No old tree or table is modified.

## New bounded disk result

[Extractor](extract_native.py) verifies the complete player SHA-256
`8d4c1f5934adae809b5f4ce4f6ca7c64d4260df46bb3eb9c41fe32be2ee905be`
and locked s303 Mach-O metadata before extracting exactly **76 table bytes** at
module-relative `[0xd2540,0xd258c)`. No instruction discovery or target disassembly.
Full-file reads for hash/metadata verification are custody only; the report's
`destination_bytes_read=0` means no destination window extracted/analyzed.
[Raw table](native-table.json) is portable; no local player is needed to diagnose.
The extraction command uses the receipt-pinned binary path, not a new tool path.

s345 supplies the rule: EDX zero-extends the incoming index; on unsigned EAX <=18,
RAX becomes module base + 0xd2540, MOVSXD loads the indexed signed dword into RDX,
ADD adds the table base, JMP RDX transfers. These instructions are retained facts,
not newly decoded bytes. The new dwords resolve to **eight distinct destinations**:

| Indices | Module-relative destination |
| --- | --- |
| 0 | 0xd227d |
| 1 | 0xd22c0 |
| 2 | 0xd22f2 |
| 3, 6, 7, 8, 9, 11, 12, 13, 14, 15, 16, 17 | 0xd2482 |
| 4 | 0xd2316 |
| 5 | 0xd23b7 |
| 10 | 0xd23c3 |
| 18 | 0xd23d3 |

All offsets are negative signed little-endian dwords relative to the **table
base**, not the individual entry. Twelve indices share 0xd2482, the already
retained s345 conditional-window start. This static convergence is new; its code
is not re-expanded or counted as new bytes. Its incoming register values on
these table routes are not inferred from s345's separate unsigned->18 route.
No AVM type/tag names are assigned to indices. Address calculation does not
prove execution, a valid live target, no faults, effects, ownership or return.
All target bodies, subsequent branches and callees remain outside this cut.

## Gates and reproduction

Base diagnosis exits 0 for custody and static-table consistency. Five proof
requirements each exit 1, as does their combined invocation:

- `--require-external-effects`: S354_EXTERNAL_EFFECTS_UNPROVED
- `--require-value-ownership`: S354_VALUE_OWNERSHIP_UNPROVED
- `--require-live-binding`: S354_LIVE_BINDING_UNPROVED
- `--require-cursor-convention`: S354_CURSOR_CONVENTION_UNPROVED
- `--require-retained-invocation`: S354_RETAINED_INVOCATION_UNPROVED

All ten inherited live observations remain null. Actual index/destination,
module/worker/activation/cursor joins and continuation outcome remain unproved.
There is no trace-import schema or proof override.

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 evidence/sampling-upgrade/s354/diagnose.py --output /tmp/s354.json
# Each proof flag above, separately or combined, must exit 1.
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s354 -p 'test_*.py'
python3 tools/verify.py
python3 tools/check_handoff.py
# Optional read-only extraction with the receipt-matching installed player:
PYTHONDONTWRITEBYTECODE=1 python3 evidence/sampling-upgrade/s354/extract_native.py '/Users/fengkx/me/code/flash-player/Flash Player.app/Contents/MacOS/Flash Player Debugger' --output /tmp/s354-table.json
```

[Gates](gates.json) and [project checks](project-checks.json) record actual commands,
exits and durations. Tests reject every one-byte mutation even if rehashed,
provenance/bounds drift, extra invented proof and changes anywhere in the complete
prior replay. Signed-offset tests distinguish table-base from entry-base arithmetic.
Retained Chad/continuation/sampling/import suites validate existing evidence only.
These tests are not synthetic positive native proof. Contracts and runtime are
unchanged, so no contract/Godot checks apply.

## Source-first and custody

1. Complete Chad authored bodies/operand bounds remain locked through s345's
   predecessor chain. The only addition is native table data, not frame semantics.
2. No PlaceObject/MOVE or lifetime evidence is added; registers do not name generations.
3. An indirect destination is neither authored return nor dispatcher continuation.
4. Tests lock exact bytes, signed arithmetic and unknowns, not gameplay assumptions.
5. No fresh original/Godot same-input comparison; mechanism acceptance remains unproved.

Zero builds, launches, attaches, live memory reads, captures or new images.
Only the new authority, s354 and minimal STATUS/SAMPLING_UPGRADE/tasks/manifest
tracking change. game/, scripts/, runtime, contracts, shared tools and every
s254–s353 tree have zero diff. Prior tables, including after-s344, stay closed.
No destination code, other rank, deployment, ready transition or merge.

[Input pins](input-sha256.json), [scope audit](scope-audit.json),
[manifest audit](manifest-audit.json) and [artifact index](artifact-sha256.json)
retain custody. Artifact index excludes itself/caches. [Timing](session-timing.json)
records implementation/check wall time, excluding initial reading/design and later
Git/PR operations; person-days remain unknown. Green checks are not product closure.

Validation: **179 tests pass**; base exit 0; five individual and combined proof
gates exit 1. Disk re-extraction is identical. verify.py, check_handoff.py and
whitespace checks exit 0. Scope audit confirms all protected diffs are zero.
