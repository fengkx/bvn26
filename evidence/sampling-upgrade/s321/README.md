# s321 — AFTER-s317 rank #4: Loader attestation caller candidate

Base: origin/master `49ccb1065788ef98ddf9facc5bb7a5ede003916e` (s320 #198).
Branch: `feat/s321-loader-attestation`.
Authority: [unchanged AFTER-s317 table, rank #4](../next-fix-priority-after-s317.md).
Only rank #4 is executed; ranks 1–3 deliveries stay closed and ranks 5+ remain
planning. **Evidence-only, honest-unproved.** `production_admitted=false`;
`native_parity_proven=false`; M0-02 pending; zero product obligations closed.

## Result and boundary

The first prerequisite remains **unproved**: no actual P1 consumer/caller or
immutable request generation has been resolved. Normal is unqualified and the
wrong-resource control was not executed. This is a bounded static candidate
investigation, not a successful Loader attestation or fresh capture.

The full locked [s313](../s313/README.md) diagnosis is reproduced, recursively
revalidating 5,503 historical events. Its 16 calls, sole return, wrapper operands
and mutable stream slot are retained results, not new progress.

New independent observation is limited to the receipt-matching binary file:
SHA-256 `8d4c1f5934adae809b5f4ce4f6ca7c64d4260df46bb3eb9c41fe32be2ee905be`,
UUID `067c4cfe5b2a3424aaa01fae2df056eb`. No live process was read or launched.
[extract_native.py](extract_native.py) verifies the full hash and Mach-O metadata,
scans exactly the `__text` section for E8/E9 rel32 byte patterns targeting the
locked wrapper, then extracts **83 bytes** at `0x100108f54–0x100108fa7` (exclusive
end). All addresses are unslid native virtual addresses, not live PCs or SWF
coordinates. The scan's five candidate file offsets are `0x108f68`, `0x108fca`,
`0x109437`, `0x109697`, `0x4b2e2c`. Pattern matches can occur inside instructions;
this is neither five proved callers nor a complete direct/indirect caller graph.
Only the first candidate's local window is decoded in this slice. The arbitrary
bounded window does not establish enclosing function entry or reachability.

| Static instruction evidence | What remains unproved |
| --- | --- |
| `0x100108f58` zeros local byte `[rbp-0x29]`; `0x100108f64` passes its address in rsi; edx is 1 | Actual buffer/request ownership and any live value |
| `0x100108f68` directly calls wrapper `0x1004b3440` | Executed caller, P1 membership and immutable request generation |
| `0x100108f6d` loads that byte into ecx, conditional on normal return | Whether the wrapper wrote it; failure may leave initialized zero |
| `0x100108f86/8a/90` shift/mask the byte-derived value and store to `[rbx+0x140]` | Meaning of that field, returned/consumed range provenance and lifetime |
| `0x100108fa1` calls through `[rax+0x400]` | Dynamic target, effects, return and later continuation |

This candidate is a buffer dereference, distinct from a return-register copy.
It still cannot be reported as **actual consumption of returned bytes**. The
initial local zero and the conditional handling of eax=-1 make that distinction
concrete. No native class, request identity, successful read or target binding
is inferred. The first opaque call is the wrapper itself; the subsequent window
is conditional on its normal return. No path feasibility, exception completeness
or activation preservation is proved.

[native-audit.json](native-audit.json) and [caller-window.txt](caller-window.txt)
retain extraction provenance and decoded bytes. [diagnose.py](diagnose.py) pins
all s313 files and the new extraction, checks the full 83-byte/20-instruction
coverage and signed call destination, and leaves every live observation null.
Offline diagnosis needs no mounted player binary. The extractor requires the
exact receipt binary; rerunning it changes measured costs and requires reviewed
pin updates, never silent resealing of historical receipts.

## Source-first and next prerequisite

1. Retained `scripts/main.json` → `DefineSprite_1900/frame_1/DoAction.as` shares
   MovieClipLoader across P1, P2, assists and sound; the locked chain checks order.
2. No new PlaceObject/MOVE or instance-lifetime evidence. Native field addresses
   do not identify the authored target or its generation.
3. `LO.onLoadComplete(target)` ignores target, increments `loadStep`, and invokes
   `loadSteps[loadStep]()` inline. A later mutable request can describe the next load.
4. Tests lock archived byte operands, coverage and rejection of unsupported
   promotion; they assert no guessed gameplay or successful association.
5. Only historical same-input evidence is replayed; no new original/Godot run.

Next resolve and independently bind an **executed** caller/consumer to one P1
request with immutable generation. Qualify observer effects, complete returned
and consumed ranges (or actually consumed mapped ranges), and target before
inline advance; separately bind same-request initialization/use/unload/replacement.
The new window supplies a candidate breakpoint location, not a resolver. A hit
alone is insufficient. Only after normal qualifies may an actual Yihu-for-Yijiao
control run with expected Yijiao identity unchanged and errors/ranges retained.

## Gates and validation

| Gate | Expected exit | Code |
| --- | --- | --- |
| Fixed-evidence diagnosis | 0 | `S321_DIAGNOSIS_OK` |
| `--require-consumer-request` | 1 | `S321_CONSUMER_REQUEST_UNPROVED` |
| `--require-loader-attestation` | 1 | `S321_LOADER_ASSOCIATION_UNPROVED` |
| `--require-pre-advance-target` | 1 | `S321_PRE_ADVANCE_TARGET_UNPROVED` |
| `--require-wrong-resource-control` | 1 | `S321_WRONG_RESOURCE_BLOCKED` |

Changed pinned evidence fails with `S321_EVIDENCE_INVALID`, not an unproved gate.
There is no caller-supplied trace or proof override.

```sh
PYTHONPATH=. python3 evidence/sampling-upgrade/s321/diagnose.py --output /tmp/s321.json
# Repeat with each proof flag above: each must exit 1.
PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s321 -p 'test_*.py'
# Retained slice and shared-tool commands: project-checks.json
python3 tools/verify.py
python3 tools/check_handoff.py
```

[Gates](gates.json), [checks](project-checks.json), [scope](scope-audit.json),
[manifest audit](manifest-audit.json), [timing](session-timing.json) and
[artifact hashes](artifact-sha256.json) record results. Hash index excludes itself
and caches. Measured implementation interval excludes initial reading/exploration
and later commit/push/PR work; person-days are unknown. No runtime or contract
changes, so no Godot/contract validation applies.

Only s321 and minimal STATUS/SAMPLING_UPGRADE/tasks/manifest tracking change.
All prior s254–s320 evidence, authority table, game/, scripts/, runtime, contracts,
shared sampler/threshold/validator remain byte-identical. No return-copy-as-
consumption, mutable-slot-as-generation, static-hash-as-live-bytes, helper stamp,
receipt resealing, rollout, re-ranking, other-rank experiment, ready marking,
merge or deployment. Zero builds, launches, attaches, memory reads or captures.

Validation result: **90 tests pass** (8 s321, 33 retained slice tests, 49 shared
tool tests). Base diagnosis exits 0; all four proof requirements exit 1.
Integrity, handoff and whitespace checks exit 0. These validate evidence integrity
and fail-closed reporting; actual Loader association remains unproved.
