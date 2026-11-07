# s336 — Post-s335 re-rank + rank #1 Chad successor frontier

Base: `6e0c9b4ad6c588274cc4299a4725396963c764de` (origin/master,
s335 #213 squash). Branch: `feat/s336-after-s335-rerank`.
Authority: [AFTER-s335 rank #1](../next-fix-priority-after-s335.md).
**Only new rank #1 is executed; ranks 2+ are planning only.** AFTER-s326 ranks
1–9 delivered as s327–s335 stay closed. `production_admitted=false`;
`native_parity_proven=false`; M0-02 pending; zero product obligations closed.

## Ranking and retained validation

[Ranking pins](ranking-basis-sha256.json) bind s327–s335 READMEs/diagnoses and
all prior priority tables. Chad supplies two concrete byte-bound successors;
ones is an upstream scene prerequisite. The remaining interface assessments add
no independent live identities or qualified observations. Ranking considers
source-bounded discriminators, independent observations, downstream prerequisites,
then facility cost, never green-gate likelihood. No rank2+ experiment is executed.

[diagnose.py](diagnose.py) pins every s327 artifact, reproduces its entire locked
diagnosis and recursively revalidates the retained 9,493 historical events.
Its 68-byte entry block, s320's caller/argument relation and earlier results are
**retained validation, not new progress**. Every prior evidence tree is unchanged.

## New bounded result

[extract_native.py](extract_native.py) verifies full disk binary SHA-256
`8d4c1f5934adae809b5f4ce4f6ca7c64d4260df46bb3eb9c41fe32be2ee905be`
and complete retained Mach-O metadata/UUID before read-only extraction. No process
is launched, attached or read. Discovery was limited to 128 bytes at each s327
successor start; only instructions through the first transfer are retained and
analyzed. No subsequent transfer target is expanded.

[Native audit](native-audit.json) retains two windows: `0xd2244–0xd226d` (41 bytes,
12 instructions) and `0xd2254–0xd226d` (25 bytes, seven instructions). The second
is a shared suffix of the first. **Only 41 unique bytes / 12 unique instructions
are new.** The actual basic-block split is at the known join `0xd2254`: the
16-byte fallthrough prefix reaches the 25-byte shared block without a transfer.
Coordinates are unslid module-relative machine addresses, not SWF offsets or
observed PCs. See [fallthrough window](successor-0xd2244.txt) and
[taken window](successor-0xd2254.txt).

| Site / route | Byte-bound fact | Limit |
| --- | --- | --- |
| s327 `0xd2242` falls through to `0xd2244` when loaded low bits equal 7 | `rax = rbx`; clear low three bits; at `0xd224b` load qword from `[rax+0x18]`; set ecx to low three bits of loaded result | Conditional indirect read, not object layout, AVM type or valid pointer proof |
| s327 `0xd2242` branches directly to `0xd2254` otherwise | Incoming rax is retained rbx; ecx is its low-three-bit value | No extra memory read on this local route does not prove harmlessness |
| shared `0xd2254–0xd2264` | Mask eax with 31; if ecx differs from 2, replace eax with ecx; set ecx to 2 and edx to eax; compare eax with 18 | Raw numeric operations, no AVM type names or ownership inference |
| `0xd2267` | Unsigned JA to `0xd2482`, fallthrough `0xd226d` | Both new successors excluded; path feasibility and outcome unobserved |

The s320 caller at `0x126979` passes dispatcher-local `-0x550`, dispatcher r13
and dispatcher-local `-0x60` in rdi/rsi/rdx; retained s327 saves those into
r12/r14/r15 and loads rbx through r15. The new indirect read is derived from that
loaded qword, not a direct observation of the dispatcher slot's live contents.
Helper rbp remains distinct from dispatcher rbp. No stack/carrier/descriptor
alias or allocation generation is inferred.

There are no explicit calls, machine returns or direct memory writes in these
new windows. This does not establish termination, absence of faults/hidden
effects, preservation or authored return. Instruction order is conditional on
reaching each instruction without fault. The new discriminator is the local
indirect-read route versus the direct shared route, and their common unsigned
branch; it does not discharge the remaining continuation mechanism.

Diagnosis checks fixed byte/disassembly hashes, full instruction coverage,
overlap equality, signed rel32 displacement, both predecessor starts and the
complete retained argument/frontier audit. Offline replay needs no installed
binary. There is no accepting trace schema or proof override.

## Gates and reproduction

| Mode | Exit | Code |
| --- | --- | --- |
| Base diagnosis | 0 | S336_DIAGNOSIS_OK |
| --require-external-effects | 1 | S336_EXTERNAL_EFFECTS_UNPROVED |
| --require-value-ownership | 1 | S336_VALUE_OWNERSHIP_UNPROVED |
| --require-live-binding | 1 | S336_LIVE_BINDING_UNPROVED |
| --require-cursor-convention | 1 | S336_CURSOR_CONVENTION_UNPROVED |
| --require-retained-invocation | 1 | S336_RETAINED_INVOCATION_UNPROVED |

All ten retained live observations remain null. Both new successors, pointer
contents, faults, effects, ownership and live module/worker/activation/cursor
joins remain unproved. Any further static expansion needs a separately bounded
cut. A live retained invocation still requires independent identity bindings,
observer qualification and cursor convention; CPU entry alone is insufficient.

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 evidence/sampling-upgrade/s336/diagnose.py --output /tmp/s336.json
# Each proof flag above is run separately and must exit 1.
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s336 -p 'test_*.py'
python3 tools/verify.py
python3 tools/check_handoff.py
# Optional read-only extraction, outside the source tree:
PYTHONDONTWRITEBYTECODE=1 python3 evidence/sampling-upgrade/s336/extract_native.py '/Users/fengkx/me/code/flash-player/Flash Player.app/Contents/MacOS/Flash Player Debugger' --output-dir /tmp/s336-native
```

[Gates](gates.json) and [project checks](project-checks.json) record commands,
actual exits and subprocess durations. Tests reject every one-byte mutation even
when rehashed, modified bounds/provenance/disassembly, missing/extra windows,
prior frontier substitution, full-replay changes and invented proof. Retained
s327/s320/s311/s303/s295/s288 and Chad/continuation/sampling/import tests rerun.
These are source-byte and custody checks, not synthetic positive native proof.
No contract or Godot check applies because neither contracts nor runtime changes.

## Source-first and scope

1. Complete Chad authored bodies and operand bounds remain locked via
   s327 → s320 → s311/s303/s295. Only two native successor windows are added.
2. No PlaceObject/MOVE or placement lifetime is changed or newly proved.
   Register/stack locations do not identify authored instance generations.
3. Neither window has a machine return; no branch, label end, removal or silence
   is promoted to authored return or dispatcher continuation.
4. Tests lock source-byte operations and fail-closed reporting, not hypothetical
   gameplay, ownership, type names or scheduling.
5. Only historical same-input evidence is replayed; no fresh original/Godot
   comparison. Runtime implementation and mechanism acceptance remain unproved.

Allowed changes: new authority, s336, minimal STATUS/SAMPLING_UPGRADE/tasks and
manifest tracking. Zero-byte diffs for game/, scripts/, runtime, contracts,
shared sampler/threshold/validator and every s254–s335 tree. Historical tables
stay unchanged. No other helper or new frontier expansion, live launch/attach,
memory read, capture, build, deployment, ready marking or merge.

[Scope audit](scope-audit.json) compares the full baseline; [manifest audit](manifest-audit.json)
records reviewed tracking hashes. [Input hashes](input-sha256.json) and
[artifact hashes](artifact-sha256.json) preserve custody. Artifact index excludes
itself and caches. [Timing](session-timing.json) measures implementation/check
wall time, excluding initial reading/design and later commit/push/PR; person-days
remain unknown. Green package checks are not product acceptance.

Validation: **164 tests pass** across s336, its retained slice chain and shared
tools. Base diagnosis exits 0; all five proof flags exit 1. Integrity, handoff
and whitespace check outcomes are retained in project-checks.json. No live or
product acceptance is implied.
