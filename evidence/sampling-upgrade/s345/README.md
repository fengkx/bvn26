# s345 — Post-s344 re-rank + rank #1 Chad successor frontiers

Base: `92454e214aacca893b52032659bd8d5bd903f131` (origin/master,
s344 #222 squash). Branch: `feat/s345-after-s344-rerank`.
Authority: [AFTER-s344 rank #1](../next-fix-priority-after-s344.md).
**Only new rank #1 executes; ranks 2+ are planning only.** AFTER-s335 ranks
1–9 delivered as s336–s344 stay closed. `production_admitted=false`;
`native_parity_proven=false`; M0-02 pending; zero mechanism/product obligations closed.

## Ranking and retained replay

[Ranking pins](ranking-basis-sha256.json) bind s336–s344 READMEs/diagnoses and
all prior priority tables. Concrete byte boundaries keep Chad first; ones remains
an upstream scene prerequisite. Allocation moves above UI because s343 supplies
section-bound name locations for an executable-association discriminator, while
s342 supplies no window state. Text is not code; neither proves a live channel.
Ranking uses source-bounded discriminators, independent observations, downstream
prerequisites, then facility cost, never green-gate likelihood. No rank 2+ experiment
is executed, including no repeat name search or UI attempt.

[diagnose.py](diagnose.py) pins every s336 artifact and reproduces its complete
locked diagnosis, recursively revalidating 9,493 historical events. Prior windows,
caller arguments and observations are **retained validation, not new progress**.
Every prior evidence tree and authority table is unchanged.

## New bounded result

[extract_native.py](extract_native.py) verifies complete disk binary SHA-256
`8d4c1f5934adae809b5f4ce4f6ca7c64d4260df46bb3eb9c41fe32be2ee905be`
and retained Mach-O metadata/UUID before extraction. No player is launched,
attached or read. Discovery is bounded to 128 bytes at each successor start;
only instructions through the first transfer are retained and analyzed. Discovery
output beyond that transfer is not evidence of an expanded successor.

[Native audit](native-audit.json) retains disjoint windows `0xd226d–0xd227d`
(16 bytes, four instructions) and `0xd2482–0xd248c` (10 bytes, four instructions):
**26 unique bytes / eight instructions**. Coordinates are unslid module-relative
machine addresses, not SWF offsets or observed PCs.

| Site / route | Byte-bound fact | Limit |
| --- | --- | --- |
| s336 branch falls through to `0xd226d` when unsigned eax <= 18 | s336 wrote edx=eax, zero-extending the index, and ecx=2 | No observed input value or live execution |
| `0xd226d` | RIP-relative LEA computes module base + `0xd2540` | No table bytes are extracted or decoded |
| `0xd2274` | Load signed dword `[rax + 4*rdx]` into rdx, then add rax | Index bounded 0–18 on this incoming route; actual dword and result unknown |
| `0xd227b` | `jmp rdx` ends this window | No indirect destination is resolved or expanded |
| s336 branch directly reaches `0xd2482` when unsigned eax > 18 | `eax=ecx; eax &= 7; cmp eax,7` | Incoming ecx is 2 on this direct route, so comparison is unequal; other incoming paths excluded |
| `0xd248a` | `jne 0xd2499`, encoded fallthrough `0xd248c` | Static direct-route taken result only, not an observed jump; neither successor expanded |

See [indirect window](successor-0xd226d.txt) and
[conditional window](successor-0xd2482.txt). The s320 caller argument relation
is retained through s327/s336: helper r12/r14/r15 save caller rdi/rsi/rdx;
rbx holds the qword loaded through r15. Helper rbp is not dispatcher rbp.
The new table access overwrites rax/rdx locally; no stack/carrier/descriptor alias,
AVM type, allocation generation or ownership follows from those registers.

Neither new window has an explicit call, machine return or direct memory write.
This does not prove termination, absence of faults/hidden effects, preservation
or authored return. All instruction reasoning is conditional on reaching it
without fault. New progress is only the bounded indirect-versus-conditional
transfer discriminator; the continuation mechanism remains unproved.

Diagnosis validates fixed byte/disassembly hashes, complete instruction coverage,
RIP-relative and signed branch displacements, exact predecessor starts and the
full retained argument/frontier audit. Offline replay needs no installed binary.
There is no accepting trace-import schema or proof override.

## Gates and reproduction

| Mode | Exit | Code |
| --- | --- | --- |
| Base diagnosis | 0 | S345_DIAGNOSIS_OK |
| --require-external-effects | 1 | S345_EXTERNAL_EFFECTS_UNPROVED |
| --require-value-ownership | 1 | S345_VALUE_OWNERSHIP_UNPROVED |
| --require-live-binding | 1 | S345_LIVE_BINDING_UNPROVED |
| --require-cursor-convention | 1 | S345_CURSOR_CONVENTION_UNPROVED |
| --require-retained-invocation | 1 | S345_RETAINED_INVOCATION_UNPROVED |

All ten retained live observations remain null. Table contents, destinations,
faults, effects, ownership and live module/worker/activation/cursor joins remain
unproved. Further table/target expansion requires a separately bounded cut.
A retained invocation still needs independent identities, observer qualification
and cursor convention; CPU entry alone is insufficient.

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 evidence/sampling-upgrade/s345/diagnose.py --output /tmp/s345.json
# Run each proof flag above separately; each must exit 1.
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s345 -p 'test_*.py'
python3 tools/verify.py
python3 tools/check_handoff.py
# Optional read-only extraction, outside the source tree:
PYTHONDONTWRITEBYTECODE=1 python3 evidence/sampling-upgrade/s345/extract_native.py '/Users/fengkx/me/code/flash-player/Flash Player.app/Contents/MacOS/Flash Player Debugger' --output-dir /tmp/s345-native
```

[Gates](gates.json) and [project checks](project-checks.json) record actual commands,
exits and measured subprocess times, including combined proof flags and disk
re-extraction equality. Tests reject every one-byte mutation even if rehashed,
changed provenance/bounds/disassembly, missing/extra windows, predecessor
substitution, full-replay drift and invented proof. Retained s336/s327/s320/s311/
s303/s295/s288 and Chad/continuation/sampling/import tests run unchanged.
These are custody and machine-byte tests, not synthetic positive native proof.
No contract or Godot checks apply because contracts and runtime are unchanged.

## Source-first and scope

1. Complete Chad authored bodies/operand bounds remain locked via s336 → s327
   → s320/s311/s303/s295. Only the two native successor windows are added.
2. PlaceObject/MOVE and instance lifetimes are neither changed nor newly proved.
   Register and stack locations do not identify authored instance generations.
3. Neither window returns; no branch, label end, removal or silence is promoted
   to authored return or dispatcher continuation.
4. Tests lock byte operations and fail-closed reporting, not hypothetical gameplay,
   ownership, type names or scheduling.
5. Historical same-input evidence is replayed; no fresh original/Godot comparison.
   Runtime implementation and mechanism acceptance remain unproved.

Allowed changes: new authority, s345, minimal STATUS/SAMPLING_UPGRADE/tasks and
manifest tracking. Zero-byte diffs for game/, scripts/, runtime, contracts,
shared sampler/threshold/validator and every s254–s344 tree. Historical tables
remain unchanged. Zero builds, launches, attaches, live memory reads or captures.
No other helper, table or new frontier expansion, deployment, ready marking or merge.

[Scope audit](scope-audit.json) compares the full baseline; [manifest audit](manifest-audit.json)
records reviewed tracking hashes. [Input hashes](input-sha256.json) and
[artifact hashes](artifact-sha256.json) preserve custody. Artifact index excludes
itself and caches. [Timing](session-timing.json) measures implementation/check
wall time, excluding initial reading/design and later commit/push/PR; person-days
remain unknown. Green package checks are not product acceptance.

Validation: **173 tests pass**; base exit 0; five individual proof flags and
their combined invocation exit 1. Disk re-extraction matches; verify.py,
check_handoff.py and whitespace checks exit 0. These are package and byte-audit
results, not live or product acceptance.
