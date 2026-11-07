# s327 — Post-s326 re-rank + rank #1 Chad callee entry frontier

Base: `3b37d8a62bd1dbe5abe5760c4765fe77126881ce` (origin/master,
s326 #204 squash). Branch: `feat/s327-after-s326-rerank`.
Authority: [AFTER-s326 rank #1](../next-fix-priority-after-s326.md).
**Only new rank #1 is executed. Ranks 2+ are planning only.**
AFTER-s317 ranks 1–9 were delivered as s318–s326 and remain closed.
`production_admitted=false`; `native_parity_proven=false`; M0-02 pending.
Evidence-only, honest-unproved; zero product obligations closed.

## Ranking and retained evidence

[Ranking pins](ranking-basis-sha256.json) bind s318–s326 READMEs/diagnoses and
all prior priority tables. Chad moves first because s320 leaves a concrete
byte-bound callee and incoming argument relation; Yulong's finite exposure
analysis is delivered and its next observation needs a live activation facility.
Ones stays an upstream scene prerequisite. Ranking considers source-bounded
discriminators, independent observations, downstream prerequisites, then cost;
it does not favor green proof gates. No rank2+ facility queries or experiments run.

[diagnose.py](diagnose.py) pins every s320 artifact and reproduces its entire
locked diagnosis, recursively revalidating 9,493 historical events. That replay,
s320's 1,049 bytes/four windows, and earlier ownership/cursor ambiguity are
**retained validation, not new progress**. Prior evidence is unchanged.

## New bounded result

[extract_native.py](extract_native.py) verifies the receipt-matching binary's full
SHA-256 `8d4c1f5934adae809b5f4ce4f6ca7c64d4260df46bb3eb9c41fe32be2ee905be`
and Mach-O metadata/UUID `067c4cfe5b2a3424aaa01fae2df056eb` before extraction.
The installed binary is read only. No process is launched, attached or read.
The discovery disassembly requested 128 bytes at the already locked direct call
target; only the first block through its first transfer is retained and audited.
No subsequent block is expanded or used to infer behavior.

The new extraction is **68 bytes / 21 instructions**, module-relative
`0xd2200–0xd2244` (exclusive end). These are unslid machine coordinates,
not SWF offsets, live PCs or observed execution. The s320 call at `0x126979`
passes `&dispatcher_rbp-0x550`, `dispatcher_r13`, `&dispatcher_rbp-0x60`
in rdi/rsi/rdx respectively.

| Entry block site | Byte-bound fact | Limit |
| --- | --- | --- |
| 0xd2214 / 0xd2217 / 0xd221a | Saves rdx/rsi/rdi in r15/r14/r12 | Register correspondence, not an AVM identity |
| 0xd221d / 0xd2224 / 0xd2228 | Loads from RIP-relative pointer cell 0x14b1c58, dereferences that result, saves it in helper-local rbp-0x30 | Pointer contents, aliases and faults unknown; helper rbp is not dispatcher rbp |
| 0xd222c | Writes qword raw 2 through r12, the first incoming pointer | At this caller the direct destination is dispatcher-local -0x550; no AVM type, clearing or ownership meaning assigned |
| 0xd2234 | Reads qword through r15 into rbx | At this caller the direct source is dispatcher-local -0x60; not a live value observation |
| 0xd2237–0xd2242 | Tests loaded low 32 bits masked with 7 against 7; JNE targets 0xd2254, fallthrough 0xd2244 | Both successors are outside this exclusive cut; path feasibility and subsequent effects unknown |

There is no explicit call or RET in this first block. This does **not** establish
harmlessness, return, termination, absence of faults or hidden effects. Straight-line
order is conditional on entering and reaching each instruction without fault.
The direct write precedes the direct read in decoded order, but no executed
invocation or preservation has been observed. The raw mask/value is not named as
an AVM type. No stack/carrier/descriptor alias or allocation generation follows.

[Native audit](native-audit.json) and [disassembly](callee-entry.txt) retain bytes,
commands, full binary identity and measured extraction time. Diagnosis checks full
instruction coverage, fixed byte/disassembly hashes, signed branch displacement
and the exact retained caller argument/target instructions. It requires no installed
binary for offline replay. There is no accepting live-input schema or proof override.

## Gates and next boundary

| Mode | Exit | Code |
| --- | --- | --- |
| Base diagnosis | 0 | S327_DIAGNOSIS_OK |
| --require-external-effects | 1 | S327_EXTERNAL_EFFECTS_UNPROVED |
| --require-value-ownership | 1 | S327_VALUE_OWNERSHIP_UNPROVED |
| --require-live-binding | 1 | S327_LIVE_BINDING_UNPROVED |
| --require-cursor-convention | 1 | S327_CURSOR_CONVENTION_UNPROVED |
| --require-retained-invocation | 1 | S327_RETAINED_INVOCATION_UNPROVED |

All ten retained live observations remain null. Both branch continuations,
indirect pointer contents, exceptional paths, ownership/effects and live
module/worker/activation/cursor joins remain unproved. Further static expansion
would need its own bounded cut; it is not executed here. A live retained invocation
requires independently qualified module/worker and value/owner/descriptor bindings,
observer effects and cursor convention. CPU entry alone is insufficient.

## Source-first and scope

1. Complete Chad authored bodies/operand bounds stay locked through s320 →
   s311 → s303/s295; this cut adds only a native callee entry block.
2. No PlaceObject/MOVE or placement lifetime is changed or newly proved.
   Native registers/stack locations do not identify authored instance generations.
3. This block has no machine return. Neither its branch nor the caller's next
   instruction proves authored return or dispatcher continuation; no label-end,
   removal or silence is promoted to return.
4. Tests lock byte-derived operands, caller correspondence and fail-closed
   reporting, not hypothetical gameplay, ownership or scheduling.
5. Only historical same-input evidence is revalidated; no new original/Godot
   comparison. Runtime implementation and mechanism acceptance remain unproved.

Allowed changes: the new authority, s327 and minimal STATUS/SAMPLING_UPGRADE/
tasks/manifest tracking. Zero-byte diffs for game/, scripts/, runtime, contracts,
shared sampler/threshold/validator and every s254–s326 tree. The after-s317 table
remains historical and unchanged. No other callee, broad interpreter, invented
AVM type, pointer-only identity, root-worker equivalence, build, live launch,
attach, memory read, capture, deployment, ready marking or merge.

## Reproduction and validation

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 evidence/sampling-upgrade/s327/diagnose.py --output /tmp/s327.json
# Each proof flag above is run separately and must exit 1.
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s327 -p 'test_*.py'
python3 tools/verify.py
python3 tools/check_handoff.py
# Optional read-only re-extraction into a separate temporary directory:
python3 evidence/sampling-upgrade/s327/extract_native.py '/Users/fengkx/me/code/flash-player/Flash Player.app/Contents/MacOS/Flash Player Debugger' --output-dir /tmp/s327-native
```

[Gates](gates.json) and [project checks](project-checks.json) retain commands,
actual exits and times, including s320/s311/s303/s295/s288 and shared Chad,
continuation, sampling and import tests. Local tests reject rehashed byte mutation,
wrong binary/bounds, altered disassembly, caller substitution, any full-prior
mismatch and proof promotion. They do not manufacture positive native proof.
No contract/Godot checks apply because neither contracts nor runtime changes.

[Scope audit](scope-audit.json) compares with the full baseline SHA;
[manifest audit](manifest-audit.json) records reviewed tracking hash updates.
[Input hashes](input-sha256.json) and [artifact hashes](artifact-sha256.json)
retain custody; artifact index excludes itself and caches. [Timing](session-timing.json)
measures implementation/check time, excluding initial reading/design and later
commit/push/PR work; person-days remain unknown. Green package gates are not
product acceptance.

Validation: **155 tests pass** (8 s327, 42 retained slice tests and 105 shared
tool tests). Base diagnosis exits 0; all five proof flags exit 1. Integrity,
handoff and whitespace checks are recorded in project-checks.json. No native
execution, continuation or product acceptance is implied.
