# s365 — AFTER-s362 rank #3: AImain allocation candidate prefix

Base: `e3133e94c741a868a3a05ef595158ffd34c68b4d` (s364 #242 squash).
Branch: `feat/s365-aimain-allocation`.
Authority: [unchanged AFTER-s362 rank #3](../next-fix-priority-after-s362.md).
Only rank #3 executes; ranks 1–2 delivered, ranks 4+ planning only. No re-ranking.
`production_admitted=false`; `native_parity_proven=false`; M0-02 pending.
Zero mechanism/product obligations closed; zero new live native observations.

## Independent observation

The selected s360 call at `0x1000bfcfd` targets `0x10005d960`. This cut
independently reads that target's first control-transfer prefix from the
receipt-matching disk binary, rather than repeating the text-reference inventory.
[Discovery](discover_prefix.py) requests one instruction at a time from LLDB,
with a 64-byte safety bound, and stops at the first control transfer.
[Raw disassembly](selected-disassembly.txt) and [receipt](disassembly-receipt.json)
retain all five commands, their exits, elapsed times and debugger hash/version.

Exactly **11 bytes / five instructions** were decoded:

| Unslid address | Bytes | Operation |
| --- | --- | --- |
| 0x10005d960 | 55 | Push RBP |
| 0x10005d961 | 48 89 e5 | RBP = RSP |
| 0x10005d964 | 31 c0 | EAX = 0; zero-extend RAX |
| 0x10005d966 | 48 85 ff | Test RDI & RDI |
| 0x10005d969 | 74 49 | JE +0x49; target 0x10005d9b4, fallthrough 0x10005d96b |

The predicate is **incoming RDI == 0**. The prefix neither dereferences RDI
nor consumes RSI (s360's text argument). The stack prologue does not locate an
AS2 saved reference. Zeroing EAX before a branch does not prove a returned value.
Neither successor is expanded. No other six candidates, callee, allocator import
or pool route is examined. No AVM type, parent resolver, actual execution or
allocation generation is established. This bounded result does not prove the
whole function lacks a resolver; behavior after the branch remains unknown.

[Portable extractor](extract_native.py) checks the complete binary SHA-256,
Mach-O metadata, file mapping and the locked LC_FUNCTION_STARTS stream. The entry
is a function start, with next start `0x10005d9c0`; this metadata bounds the prefix
without decoding the rest of the function. [Native prefix](native-prefix.json)
retains the exact bytes. Full-file reads establish custody, not successor analysis.
LLDB creates a disk target only; no player launch, attach or process-memory read.
Generated LLDB symbols are not source identities.

## Separate saved-reference prerequisite

[Saved-reference record](saved-reference-attempt.json) keeps the retained
`_global.s261Receiver -> saved` source route separate from the native prefix.
Native value location, representation, dereference instruction and resulting
allocation generation remain null. No stack/result slot or text argument is
substituted for the referent. This blocked prerequisite is not new proof.
Live generations and clearing/replacement/free/reuse/pool controls were not run.
No pointer identity, deletion-as-clearing or token-loss inference is permitted.
Allocator imports cannot establish internal pool coverage.

Next work requires independent parent/depth resolver semantics and saved-value
representation/dereference before binding loaded module, parent, saved-value and
result generations. Uninterrupted allocation-to-clearing/replacement/free/reuse
and internal pool/deferred-free observations remain necessary. Further code
expansion is outside this cut. Missing observations remain null, not negatives.

## Retention, gates and reproduction

The complete locked s360 diagnosis is replayed and embedded unchanged, including
its retained tool chain. This is retention validation only, not new progress.
[Input hashes](input-sha256.json) pin every s360 file, inherited inputs, s303
metadata/decoder and the unchanged authority. [Route hashes](route-sha256.json)
pin the new extractor/discovery/receipts/raw prefix/saved-reference record.

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 evidence/sampling-upgrade/s365/diagnose.py --output /tmp/s365.json
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s365 -p 'test_*.py'
PYTHONDONTWRITEBYTECODE=1 python3 evidence/sampling-upgrade/s365/extract_native.py --binary /path/to/receipt-matching-player --output /tmp/s365-prefix.json
python3 tools/verify.py
python3 tools/check_handoff.py
```

Diagnosis is portable and needs no local player or debugger. Optional disk
re-extraction accepts any path only if bytes match the pinned receipt. Discovery
uses the s343 receipt path and pins the actual debugger; do not rerun discovery
into this historical package. New tool paths are repository-relative.
Base diagnosis exit **0** means evidence consistency, not resolver success.
Each proof flag and their combined invocation exit **1**:
`--require-parent-depth-resolver`, `--require-saved-reference`,
`--require-slot-reference`, `--require-content-clearing`, `--require-replacement`,
`--require-allocation-identity`. Unproved codes are `S365_<FLAG>_UNPROVED`;
invalid custody separately reports `S365_EVIDENCE_INVALID`. No proof override.

[Checks runner](run_checks.py), [gates](gates.json), [project checks](project-checks.json)
record actual exits, complete retained predecessor tests, local mutation tests,
exact disk re-extraction equality, verify, handoff and whitespace checks.
Tests reject every rehashed prefix byte mutation, bounds/custody drift, fabricated
saved representation and complete prior-report drift. They test evidence integrity,
not guessed Flash behavior. An initial mutation-test construction error and its
correction are retained in [validation note](validation-note.txt) and
[initial test log](initial-s365-tests.txt); no proof gate was relaxed. [Scope](scope-audit.json), [manifest audit](manifest-audit.json),
[artifact hashes](artifact-sha256.json) and [timing](session-timing.json) retain custody
and measured cost; person-days unknown. Artifact hashes exclude themselves/caches.

## Source-first and scope

1. Retained Yijiao Sprite455 frame1 initCtrl unload, Sprite3 frame1 stop and no
   frame2 DoAction remain unchanged; no new per-frame semantic claim.
2. No new PlaceObject/MOVE or lifetime observation; registers are not generations.
3. Native JE is not authored label exit, return or dispatcher completion.
4. Tests protect exact disk evidence and unknowns, not guessed allocation behavior.
5. No fresh original/Godot same-input comparison; parity remains unproved.

Only s365 and minimal STATUS/SAMPLING_UPGRADE/tasks/manifest tracking change.
Every s254–s364 tree, all priority tables, game/, scripts/, runtime, contracts and
shared sampler/threshold/validator have zero diff. Zero builds, captures or live
measurements. No Godot/contract check applies to this evidence-only cut.
Timing covers implementation, discovery, packaging and local checks; excludes
initial reading/design and subsequent commit/push/PR. Draft PR only; no ready
transition, merge or deployment. Delivery closes this evidence cut only.

Final validation: **151 tests pass** (143 retained + 8 s365). Base exit0; six
individual and combined proof gates exit1. Disk re-extraction equality, verify.py,
check_handoff.py and whitespace checks exit0. Protected-path scope is unchanged.
