# s366 — AFTER-s362 rank #4: Terminal callback

Base: `3e48153c89da05466213621a2ef05ad8261034df` (s365 #243 squash).
Branch: `feat/s366-terminal-callback`.
Authority: [unchanged AFTER-s362 rank #4](../next-fix-priority-after-s362.md).
Only rank #4 executes; ranks 1–3 delivered, ranks 5+ planning only. No re-ranking.
`production_admitted=false`; `native_parity_proven=false`; M0-02 pending.
Zero mechanism/product obligations closed; zero new live native observations.

## Independent route and result

**Loaded callback/owner/activation association through dispatcher outcome remains
unproved.** This cut pursues a callback-name operand route independent of aiEvent
and of s357's explicit Return arm. It does not repeat the retained adapter inventory.
The new result is disk evidence, not a qualified observation channel.

[Extractor](extract_native.py) binds the entire receipt-matching player SHA-256,
locked section headers and LC_FUNCTION_STARTS bytes. An exact NUL-delimited ASCII
`onEnterFrame` search in `__TEXT,__cstring` yields one occurrence at file offset
`0x119f010` (unslid `0x10119f010`). Searching REX.W RIP-relative LEA encodings at
all byte alignments in `__TEXT,__text` yields one candidate at `0x100096147`.
This bounded encoding search does not cover all ways to reference a name.
Initial reconnaissance found three NUL-delimited occurrences in the whole file
(`0x119f010`, `0x158b678`, `0x158dc89`); only the cstring occurrence is pursued.
The latter two are not expanded or assigned semantics.

[Discovery](discover_route.py) requests one instruction at a time from LLDB,
stopping at the first control transfer with a 64-byte cap. The retained
[raw output](selected-disassembly.txt) and [receipt](disassembly-receipt.json)
record four commands, tool hash/version, exits and measured subprocess times.
The local candidate decodes as **22 bytes / four instructions**:

| Unslid address | Local decode |
| --- | --- |
| `0x100096147` | `RDX = RIP_next + 0x1108ec2 = 0x10119f010` |
| `0x10009614e` | `RDI = RBP - 0x2d0` |
| `0x100096155` | `RSI = R13` |
| `0x100096158` | Direct call candidate to `0x1000d2590` |

The extractor checks the exact bytes and independently recomputes RIP/call
arithmetic. Function-start metadata brackets the candidate between
`0x1000937b0` and `0x100097ef0`, but **no sequential decode from function entry**
is performed. Therefore instruction boundary/reachability remains unproved;
LLDB's generated symbol label is not an independent callback identity.
Neither callee nor continuation is decoded. Name/address formation, stack address
and R13 do not establish registration, dispatch, closure, owner, activation,
replacement survival or outcome. No native type or constructor is inferred.

The first missing prerequisite is an independently established executable binding
from this candidate (or another channel) to the archived callback body and its
uninterrupted owner/closure/activation generations. Establish dispatcher outcome
through callback/logger replacement before observer off/on; off/on preservation
must pass before inventory. Further native expansion is not performed in this cut.
No debugger-impossibility or global-absence inference follows from this result.

## Retained evidence and unproved gates

The **complete locked s357 diagnosis** is replayed and embedded unchanged, with
its retained tooling chain. This is retention validation, not new progress.
[Input pins](input-sha256.json) bind every s357 file, inherited inputs, reused
read-only metadata/decoder and unchanged authority. Reusing s360's byte-pattern
and ULEB helpers does not execute its allocation research or alter its evidence.
[Route pins](route-sha256.json) bind this cut's extractor, discovery and results.

[Binding attempt](binding-attempt.json) keeps loaded body, defining scope, owner,
closure, activation, replacement survival and matching dispatcher outcome null.
The target remains archived `patches/main/frame_10/DoAction.as` root
`onEnterFrame`, not an asserted authored gameplay callback. Entry, done-producing
invocation, closing invocation, callback replacement, logger replacement, quit
request and dispatcher continuation are distinct unobserved boundaries.
**Off/on and terminal inventory were not executed.** Null means missing evidence.

No explicit Return as structural fallthrough/unwind coverage, pointer/timestamp
identity, inner marker as outer return, silence, suffix threshold or tape changes
are accepted. No proof override/import interface is added. Even one qualified
callback would not establish terminal completeness.

## Reproduction and local validation

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 evidence/sampling-upgrade/s366/diagnose.py --output /tmp/s366.json
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s366 -p 'test_*.py'
PYTHONDONTWRITEBYTECODE=1 python3 evidence/sampling-upgrade/s366/extract_native.py --binary /path/to/receipt-matching-player --check
python3 tools/verify.py
python3 tools/check_handoff.py
```

Diagnosis needs no local player or debugger. Disk re-extraction accepts any path
with matching receipt bytes; its default is the pinned s343 receipt path.
Discovery records the resolved debugger path and hash. New script paths are
repository-relative. Do not rerun discovery/check packaging into historical
committed evidence; use a disposable checkout for report-producing scripts.

Base diagnosis exit **0** means evidence consistency, not callback proof.
Each flag and their combined invocation exit **1**:
`--require-independent-channel`, `--require-logger-replacement`,
`--require-callback-completion`, `--require-off-on`,
`--require-terminal-completeness`. Unproved codes use `S366_<FLAG>_UNPROVED`;
invalid custody separately reports `S366_EVIDENCE_INVALID`.

[Checks](run_checks.py), [gates](gates.json) and [project checks](project-checks.json)
retain actual exits and logs, complete predecessor unittest chain, local mutation
tests, exact disk re-extraction, verify, handoff and whitespace checks. Tests
protect byte custody, complete replay and missing witnesses; they do not encode
assumed Flash behavior. [Scope](scope-audit.json), [manifest audit](manifest-audit.json),
[artifact index](artifact-sha256.json) and [timing](session-timing.json) record
custody and measured cost. Person-days unknown; artifact index excludes itself
and caches. Timing excludes initial reading/design/reconnaissance and later commit/push/PR.

## Source-first and exclusive scope

1. Retained frame10 observer source remains the target; no new per-frame execution claim.
2. No PlaceObject/MOVE or uninterrupted lifetime evidence; disk names are not generations.
3. Candidate native call is not authored label exit, outer return, unwind or dispatcher outcome.
4. Tests lock disk bytes, missing measurements and prior evidence, not guessed gameplay.
5. No fresh original/Godot same-input comparison; parity remains unproved.

Only s366 and minimal STATUS/SAMPLING_UPGRADE/tasks/manifest tracking change.
All prior s254–s365 trees, all priority tables, game/, scripts/, runtime, contracts
and shared sampler/threshold/validator remain unchanged. No builds, launches,
attaches, memory reads, captures or live measurements. No Godot or contract check
applies to this evidence-only cut. Draft PR only; no ready transition or merge.
Delivery closes this evidence cut only, not the mechanism or product obligation.

Final local validation: **141 tests pass** (8 s366 plus 133 retained).
Base exit0; five individual and combined proof gates exit1. Disk re-extraction,
verify.py, check_handoff.py and whitespace checks exit0.
