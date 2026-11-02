# s303 — AFTER-s299 rank #4: Chad native dispatch candidate

Base: origin/master `27f70be588e72bcc0e260ce1d827559dc322b002`
(s302 #180). Branch: `feat/s303-chad-continuation`.
Authority: [AFTER-s299 rank #4](../next-fix-priority-after-s299.md).
**Evidence-only, honest-unproved.** `production_admitted=false`;
`native_parity_proven=false`; zero product obligations closed; M0-02 pending.

## Result

The locked [s295 diagnosis](../s295/README.md), including 9,493 historical events,
is reproduced exactly. This slice advances beyond empty name queries: it extracts
and audits a **static machine-code dispatch candidate** from the exact s266
receipt-pinned executable. It does **not** establish the requested native
activation resolver, loaded worker, measured cursor convention or retained
invocation. All five proof gates exit1. No instruction observations were attempted
before qualification; no build, player launch, process memory read or new capture.

[discovery.json](discovery.json) records the exploratory opcode-immediate search.
The comparison at module offset `0x1249c5` with `0x96`, neighboring `0x1c/0x4e`,
byte-fetch/long-action-length path and a Pop-like branch motivate the candidate.
These similarities are evidence for a candidate, not complete semantic proof or
an exhaustive search of all native paths. No new symbol/type name queries ran.

[audit_native.py](audit_native.py) checks the entire executable SHA-256 against
s266, parses the Mach-O header/segments/UUID, extracts five bounded byte regions
and runs objdump on the four code windows. [native-audit.json](native-audit.json)
retains exact bytes, file mapping, hashes, commands and measured extraction cost.
UUID is `067c4cfe5b2a3424aaa01fae2df056eb`; preferred `__TEXT` base is
`0x100000000`. Addresses below are **module-relative machine-code coordinates**,
not SWF offsets, actual loaded addresses or observed PCs. No ASLR slide is known.

## Byte-derived candidate

[diagnose.py](diagnose.py) checks pinned load/store/branch bytes and recomputes
the signed relative table entries; it does not accept a caller-supplied proof flag.

| Candidate site | Module offset | Static evidence |
| --- | --- | --- |
| Cursor load | `0x124726` | signed dword `[rbp-0x158]` into rax |
| Buffer descriptor | `0x12474d` | qword `[rbp-0x160]`; data pointer at +0, signed extent at +8 |
| Cursor update / fetch | `0x124784` / `0x12478d` | stores c+1 to cursor slot, then reads byte at data+c into r15d |
| Dispatch | `0x124a77`–`0x124a96` | unsigned `(opcode-4) <= 0x9b`; signed dword table offsets relative to `0x12cf44` |
| 0x52 / CallMethod candidate | `0x124c2b` | begins with candidate stack owner/count and three slot removals; downstream call semantics unresolved |
| 0x17 / Pop candidate | `0x125cab` | nonempty count at owner+0x520 decremented; eight-byte slot at storage owner+0x528 replaced with 2 |
| 0x4f / SetMember candidate | `0x125294` | passes candidate owner and r9 to helper `0x121450`; helper semantics unresolved |

The candidate owner is loaded from `[rbp-0x558]`. Value 2 is retained as a raw
machine value; this slice does not claim to decode its AVM tag. These are local
frame locations, not portable activation definitions or register4 locations.
The extent check explicitly allows sentinel -1; a pointer alone cannot establish
a finite loaded worker extent. The descriptor's allocation/lifetime is unresolved.

For the short-opcode path, the slot advances to c+1 before fetch uses old c;
r8d receives c+1. The high-bit path instead reads a little-endian 16-bit payload
length, advances the slot by two and adds payload length to r8d. Thus even this
candidate has multiple cursor-like values. This is a **local static relation**,
not a measured convention for the retained worker. Calls and external edges in
the retained windows are not a complete preservation or activation proof.

The archived 139-byte worker remains unique in its SWF; file offset589408 remains
both next CallMethod and current Pop. Static machine-code candidates do not bind
those coordinates to a live descriptor. Retain/remove use the same body; neither
archive uniqueness nor a successful historical post marker selects an activation.
Scope, operand values and register4 witness remain unbound. Root-defined controls
remain separate. Silence, removal and a body's last next-offset are not returns.

## Gates and blocker

| Requirement | Expected exit | Code |
| --- | --- | --- |
| Reproducible bounded diagnosis | 0 | `S303_DIAGNOSIS_OK` |
| Native dispatch/activation resolver | 1 | `S303_NATIVE_RESOLVER_UNPROVED` |
| Loaded worker binding | 1 | `S303_LOADED_BUFFER_UNPROVED` |
| Measured cursor convention | 1 | `S303_CURSOR_CONVENTION_UNPROVED` |
| One retained authored invocation | 1 | `S303_RETAINED_ACTIVATION_UNPROVED` |
| Three executed boundaries | 1 | `S303_INSTRUCTION_BOUNDARIES_UNPROVED` |

The concrete blocker is the missing defining-scope/register4/value and activation
identity layout, followed by actual loaded bytes/finite extent and cursor
measurements. No complete native resolver is delivered. Next work must qualify
that layout, verify a live module UUID/slide and code bytes, bind the full loaded
worker, measure fetch/dispatch cursors, and identify one retained authored
invocation with scope, stack and witness **before** observing CallMethod, Pop and
SetMember. Chad continuation still needs its own qualified transitions or actual
invalidation/unwind/resume evidence with the unchanged tape. No broad interpreter,
CPU-entry-as-AVM proof or root-worker equivalence is introduced.

## Source-first and scope

1. Locked s266/s278/s288/s295 source remains Sprite16 frame1 doAllAction, called
   from Sprite607 frame1 depth31 enterFrame. No gameplay behavior is inferred.
2. The helper is a new placement with linear frame13 removal; compiled body
   identity does not establish placement or activation lifetime.
3. The attack goes to183; predicates/doDropDown remain. No authored return is
   inferred from missing observations, removal, or native CPU entry/return.
4. Tests check source-bound ambiguity, native byte/table derivation and rejection
   of changed cursor increments, targets, stack offsets, mapping and custody.
   They do not turn a guessed gameplay result into an invariant.
5. Only historical same-input native evidence is revalidated; there is no fresh
   original/Godot comparison. Runtime changes and mechanism closure remain barred.

Only s303 and proportionate tracking/manifest files change. s254–s302, game/,
scripts/, runtime, contracts and shared sampler/threshold/validator stay unchanged.
Ranks 1–3 and 5+ are not executed. No production admission, merge or deployment.

## Reproduce

```sh
PYTHONPATH=. python3 evidence/sampling-upgrade/s303/diagnose.py --output /tmp/s303.json
# Each independently exits 1:
PYTHONPATH=. python3 evidence/sampling-upgrade/s303/diagnose.py --output /tmp/s303-r.json --require-native-resolver
PYTHONPATH=. python3 evidence/sampling-upgrade/s303/diagnose.py --output /tmp/s303-b.json --require-loaded-buffer
PYTHONPATH=. python3 evidence/sampling-upgrade/s303/diagnose.py --output /tmp/s303-c.json --require-cursor-convention
PYTHONPATH=. python3 evidence/sampling-upgrade/s303/diagnose.py --output /tmp/s303-a.json --require-retained-activation
PYTHONPATH=. python3 evidence/sampling-upgrade/s303/diagnose.py --output /tmp/s303-i.json --require-instruction-boundaries
PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s303 -p 'test_*.py'
PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s295 -p 'test_*.py'
PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s288 -p 'test_*.py'
PYTHONPATH=. python3 -m unittest tools.tests.test_chad_native_instruction_diagnosis tools.tests.test_chad_defining_context tools.tests.test_chad_register_control tools.tests.test_as_continuation_discriminator tools.tests.test_chad_lifecycle_observer tools.tests.test_call_exit_diagnosis tools.tests.test_sampling_callsite tools.tests.test_sampling_doaction tools.tests.test_sampling_native tools.tests.test_import_guards
python3 tools/verify.py
python3 tools/check_handoff.py
```

Replay needs no installed player. Optional `python3 evidence/sampling-upgrade/s303/audit_native.py`
requires the receipt-pinned executable and objdump; it performs static extraction
only and overwrites custody/timing artifacts. Review differences before repinning.
Large exploratory disassembly remains temporary, outside the source tree.

[Gates](gates.json), [project checks](project-checks.json), [scope](scope-audit.json),
[manifest audit](manifest-audit.json), [timing](session-timing.json) and
[artifact hashes](artifact-sha256.json) retain validation and custody.
Initial exploration/design and person-days are unknown; measured subprocess costs
are not an estimate of total effort. No runtime/contract checks are required.

Validation: **128 tests pass** (11 new, 8 retained s295, 4 retained s288,
105 retained tools). Diagnosis, integrity, handoff and diff checks exit0; all
five proof requirements exit1. Slice delivery closes no mechanism obligation.
