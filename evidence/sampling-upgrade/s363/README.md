# s363 — After-s362 re-rank + rank #1 Chad first destination prefix

Base: `f222cce04f72c71d59ce81dac1dbe556f4951576` (s362 #240 squash).
Branch: `feat/s363-after-s362-rerank`.
Authority: [AFTER-s362 rank #1](../next-fix-priority-after-s362.md).
AFTER-s353 ranks 1–9 delivered as s354–s362 stay closed. Only the new rank #1
executes; ranks 2+ are planning only. `production_admitted=false`;
`native_parity_proven=false`; M0-02 pending; zero mechanism/product obligations closed.

## Ranking and retained replay

[Ranking pins](ranking-basis-sha256.json) bind complete s354–s362 READMEs and
diagnoses and every prior priority table. The new authority ranks concrete
source-bounded discriminators, independent observations, downstream prerequisites,
then facility cost, not likelihood of green gates. Chad has a precise new entry
selected by lowest table index; allocation moves above Terminal/Yulong because
s360 supplies an independently bounded direct call. UI moves above P2 because
s361 supplies process/window metadata while P2 still lacks candidate bytes.
No other-rank probe runs. Old deliveries do not discharge unproved mechanisms.

[Diagnosis](diagnose.py) hashes every s354 artifact, replays its **complete locked
report**, and embeds it unchanged, recursively retaining the historical chain.
This is retention validation, not new progress. All prior trees and tables remain
unchanged. Input and ranking hashes are verified on every diagnosis.

## New bounded disk observation

s354 table index 0 resolves to module-relative `0xd227d`. This is the selection
rule fixed before discovery, not a search for a favorable branch. The new
[discovery tool](discover_prefix.py) asks LLDB for exactly one instruction at a
time and stops at the first control transfer, with a 64-byte safety bound. It
observed **11 bytes / four instructions** in `[0xd227d,0xd2288)`:

| Address | Bytes | Operation |
| --- | --- | --- |
| 0xd227d | 89 d8 | EAX = EBX, zero-extend RAX |
| 0xd227f | 83 e0 07 | EAX &= 7, zero-extend RAX |
| 0xd2282 | 48 83 f8 07 | Compare RAX with 7 |
| 0xd2286 | 75 08 | JNE +8, target 0xd2290; fallthrough 0xd2288 |

The static predicate is **(incoming RBX & 7) != 7**. Neither successor is read
or decoded. No other table index or callee is expanded. Incoming RBX, executed
index, chosen target, value type, alias relations and live generations remain
unknown. In particular, the mask does not establish an AVM tag/type system.
No effect, exceptional exit, ownership, return or actual execution is proved.
The already retained default route is not substituted for this route's registers.

[Disassembly](selected-disassembly.txt) and [tool receipt](disassembly-receipt.json)
retain actual commands, exits, timings and debugger path/hash/version. The player
path comes from the locked s303 receipt (mounted copy); its full SHA-256 is
`8d4c1f5934adae809b5f4ce4f6ca7c64d4260df46bb3eb9c41fe32be2ee905be`.
The complete binary hash and Mach-O metadata are checked before extraction.
[Portable extractor](extract_native.py) retains exactly those 11 bytes in
[native-prefix.json](native-prefix.json). Whole-file reads are custody checks,
not analysis of successor code. LLDB target creation reads disk only; no player
process is launched or attached. Generated LLDB symbols are not source identities.
The initial output-parser failure and correction are recorded in
[discovery note](discovery-note.txt); that request exposed only the first instruction.

## Gates and reproduction

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 evidence/sampling-upgrade/s363/diagnose.py --output /tmp/s363.json
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s363 -p 'test_*.py'
PYTHONDONTWRITEBYTECODE=1 python3 evidence/sampling-upgrade/s363/extract_native.py --output /tmp/s363-prefix.json
python3 tools/verify.py
python3 tools/check_handoff.py
```

Portable diagnosis needs no installed player or disassembler. Optional disk
re-extraction defaults to the pinned s303 receipt path; `--binary` accepts another
path only if the full binary hash matches. New tools are repository-relative;
the debugger path is receipt-pinned. Discovery writes its own new receipts;
do not rerun it over this historical package. Re-extract into a temporary path.

Base diagnosis exits **0** for custody/static consistency. Each of the following
flags and their combined invocation exit **1**:

- `--require-external-effects`
- `--require-value-ownership`
- `--require-live-binding`
- `--require-cursor-convention`
- `--require-retained-invocation`

Codes are `S363_<FLAG>_UNPROVED`; invalid evidence separately reports
`S363_EVIDENCE_INVALID`. All inherited live observations remain null, not zero.
There is no proof-import override. Complete locked s354 replay remains distinct
from the new prefix. [run_checks.py](run_checks.py) records actual gates, local
mutation tests, complete predecessor test commands, disk re-extraction equality,
verify, handoff and whitespace checks in [gates](gates.json) and
[project checks](project-checks.json). Tests reject every rehashed byte mutation,
provenance/bounds changes, fabricated proof and complete prior-report drift.
These are evidence integrity tests, not synthetic positive native proof.

## Source-first and custody

1. Complete Chad authored bodies/operands remain locked through s354's chain;
   new native instructions do not add or infer frame semantics.
2. No new PlaceObject/MOVE or lifetime evidence; registers are not generations.
3. A branch destination is not authored return or observed dispatcher completion.
4. Tests lock exact source bytes, operand arithmetic and unknowns, not gameplay guesses.
5. No fresh original/Godot same-input comparison; acceptance remains unproved.

Zero builds, player launches, attaches, live memory reads, captures or new images.
Only the new authority, s363 and minimal STATUS/SAMPLING_UPGRADE/tasks/manifest
tracking change. game/, scripts/, runtime, contracts, shared sampler/threshold/
validator, prior tables and every s254–s362 tree have zero diff. No contract/Godot
check applies to this evidence-only cut. No deployment, ready transition or merge.

[Input pins](input-sha256.json), [route pins](route-sha256.json),
[scope audit](scope-audit.json), [manifest audit](manifest-audit.json) and
[artifact index](artifact-sha256.json) retain custody. Artifact index excludes
itself and caches. [Timing](session-timing.json) measures implementation,
discovery, packaging and checks; initial reading/design, branch creation and
later commit/push/PR are excluded. Person-days remain unknown.

Next work needs an independent live module/worker/cursor/invocation association
and actual value/effect/ownership observations; this static branch alone supplies
none. Further code expansion requires a separate bounded cut. Evidence delivery
closes only s363, not Chad, M0-02 or product acceptance.

Validation: **185 tests pass**. Base exit0; five individual and combined proof
gates exit1. Exact disk re-extraction, verify.py, check_handoff.py and whitespace
checks exit0. Scope audit confirms zero protected-path differences.
