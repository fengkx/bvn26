# s320 — AFTER-s317 rank #3: Chad helper/exit continuation frontier

Base: origin/master `3f64b5fdefbc47fec73c3005db145aa0127db50a` (s319 #197).
Branch: `feat/s320-chad-continuation`.
Authority: [unchanged AFTER-s317 table, rank #3](../next-fix-priority-after-s317.md).
Only rank #3 is executed. Ranks 1–2 deliveries remain closed; ranks 4+ stay
planning. The table's planning statement describes s318, not this later slice.
**Evidence-only, honest-unproved.** `production_admitted=false`;
`native_parity_proven=false`; M0-02 pending. Zero product obligations closed.

## New evidence versus retained results

The full locked [s311](../s311/README.md) diagnosis is reproduced, recursively
checking 9,493 historical events. Its three candidate origins, three transfers,
six outgoing edges and worker/cursor ambiguity are prior findings, not new progress.

New static file extraction covers **1,049 bytes in four bounded windows** from
the receipt-matching Mach-O, SHA-256
`8d4c1f5934adae809b5f4ce4f6ca7c64d4260df46bb3eb9c41fe32be2ee905be`, UUID
`067c4cfe5b2a3424aaa01fae2df056eb`. All addresses below are unslid module-relative
machine coordinates, never SWF offsets or live PCs. No process was launched or
read. `frame` means the dispatcher's native rbp; helper rbp is a different frame.

[extract_native.py](extract_native.py) checks the full binary hash and Mach-O
metadata before extraction. [native-audit.json](native-audit.json) records raw
bytes, offsets, disassembly hashes, commands and costs. [diagnose.py](diagnose.py)
checks fixed byte/disassembly pins, complete instruction coverage, signed branch
targets and every non-call successor. Its offline diagnosis needs no mounted binary.

| New bounded window (exclusive end) | Independent static finding | Unproved boundary |
| --- | --- | --- |
| `0x1264b9–0x12657c` | The zero/one/two-slot exits fill remaining temporaries with raw 2; all four exits join at `0x1264db`. The join reads candidate stack-owner r13 fields and saves selected carrier r9 in r14. | No AVM meaning assigned to slot values or owner fields |
| `0x12696b–0x12698d` | One branch passes `&frame-0x550`, r13, `&frame-0x60` to `0xd2200`; the common next boundary passes r13 and `&frame-0x548` to `0x5f50`. | Both callees opaque; no continuation beyond the final call is covered |
| `0x98b8e0–0x98ba8c` | First carrier helper reads range/index fields, can write +0x8d0/+0x8d8, calls `0x994170` at two sites, has a backward page-step edge and a shared machine RET. | Loop termination, nested effects, exceptional exits and live return unknown |
| `0x12f580–0x12f708` | Second carrier helper has conditional raw counter/index writes and calls to `0x9929e0` / `0x98da30`; its final store writes through the incoming carrier-field pointer before machine RET. | No harmless-helper, retain/release, type-name or allocation-lifetime inference |

[relations.json](relations.json) retains the explicit operands and source spans.
The first helper receives the page-derived candidate and carrier+0x48; its rax
result becomes the second helper's rsi argument. The second helper also receives
carrier+0x48 and the address of the dispatcher's raw temporary 10. Its local body
reads the old field and new temporary and contains conditional memory updates.
The final store is a static destination relation, not proof that this invocation
executed or preserved any value/activation. Nested calls remain opaque.

The four stack branches now have structural paths to two first opaque call sites.
The carrier helpers expose four further call sites and two machine RETs. The
[diagnosis](diagnosis.json) retains every instruction, branch edge, first-frontier
witness path, conditional call-return successor and backward edge. First-frontier
traversal **stops at calls**, rather than assuming that they return. The complete
window inventory also contains instructions after calls, expressly conditional
on a normal return. Structural paths may be infeasible; no path-feasibility,
termination or exception completeness claim is made. In particular, the page
loop has no proved finite iteration bound. These are finite code windows, not a
proof of bounded dynamic execution or full external-path closure.

No direct operand in these windows reads the original `frame-0x160` descriptor
origin. This bounded absence is not non-aliasing or an indirect-access exclusion.
Stack owner, carrier and descriptor allocation/alias/lifetime joins remain null;
defining scope, register4, activation identity and helper preservation remain null.
The only independent new observations are static file bytes and their decoded
operands. There is **no new independent live observation**.

## Gates and next prerequisite

| Requirement | Exit | Code |
| --- | --- | --- |
| Fixed evidence diagnosis | 0 | `S320_DIAGNOSIS_OK` |
| `--require-external-effects` | 1 | `S320_EXTERNAL_EFFECTS_UNPROVED` |
| `--require-value-ownership` | 1 | `S320_VALUE_OWNERSHIP_UNPROVED` |
| `--require-live-binding` | 1 | `S320_LIVE_BINDING_UNPROVED` |
| `--require-cursor-convention` | 1 | `S320_CURSOR_CONVENTION_UNPROVED` |
| `--require-retained-invocation` | 1 | `S320_RETAINED_INVOCATION_UNPROVED` |

Resolve the newly explicit nested-call effects, exceptional paths and the
stack/carrier/descriptor ownership and lifetime relation before live binding.
Then independently bind module UUID/slide/code bytes, actual finite loaded
worker extent, measured cursor convention and one retained authored invocation
with defining scope/register4. The historical 139-byte worker and offset 589408
next-CallMethod/current-Pop ambiguity are unchanged. No raw type-tag names,
pointer-only identity, CPU-entry-as-AVM proof, silence/removal-as-return,
root-worker equivalence or broad interpreter is admitted. A machine RET never
serves as authored return evidence.

## Source-first and scope

1. Retained Chad source is Sprite16 frame1 `doAllAction`, called from Sprite607
   frame1 depth31 enterFrame, as locked s266/s278/s288/s295/s303/s311 record.
2. The helper is newly placed and linearly removed at frame13. Placement/removal
   cannot identify native activation lifetime.
3. The authored attack goes to183; predicates and doDropDown are unchanged.
   Neither these external branch paths nor native RETs prove authored return.
4. Tests protect exact archived byte operands/branches and unknowns. They do not
   turn a guessed type, lifetime or gameplay result into an invariant.
5. Only historical original evidence is revalidated. No new original/Godot
   same-input comparison exists; behavior/parity remains unproved.

Only s320 plus minimal STATUS/SAMPLING_UPGRADE/tasks/manifest tracking changes.
All s254–s319 evidence and the authority table remain byte-identical. No game/,
scripts/, runtime, contracts, shared sampler/threshold/validator edits. Zero
builds, player launches, memory reads, captures or images. No other-rank execution,
re-ranking, deployment, ready marking or merge.

## Reproduction and validation

```sh
PYTHONPATH=. python3 evidence/sampling-upgrade/s320/diagnose.py --output /tmp/s320.json
# Repeat independently with each proof flag above; all expect exit 1.
PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s320 -p 'test_*.py'
PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s311 -p 'test_*.py'
PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s303 -p 'test_*.py'
PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s295 -p 'test_*.py'
PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s288 -p 'test_*.py'
python3 tools/verify.py
python3 tools/check_handoff.py
```

[Gates](gates.json), [checks](project-checks.json), [scope](scope-audit.json),
[manifest audit](manifest-audit.json), [timing](session-timing.json) and
[artifact hashes](artifact-sha256.json) retain actual outcomes. Hash index excludes
itself and caches. Initial exploration/design and person-days are unknown;
measured implementation interval excludes subsequent commit/push/PR work.
The extractor can be rerun only with the exact receipt binary; extraction costs
will change. Offline diagnosis and tests do not re-extract or overwrite old proof.

Validation result: **147 tests pass** (9 s320, 33 retained slice tests, 105 shared
tool tests). Base diagnosis exits 0; all five proof requirements exit 1.
Integrity, handoff and whitespace checks exit 0. These checks validate the
evidence package; they do not prove Chad continuation or production parity.
