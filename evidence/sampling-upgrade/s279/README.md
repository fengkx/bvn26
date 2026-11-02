# s279 — AImain native slot/reference and allocation facility (unproved)

Base: master `d49485dd63c34524e1d1e04220f7733870f12f01` / #156.
Exclusive authority: [AFTER-s272 rank 7](../next-fix-priority-after-s272.md).
`production_admitted=false`; `native_parity_proven=false`; M0-02 pending.
Zero product obligations closed; no runtime implementation is justified.

**The requested slot/saved-reference resolver and native allocation/free
qualification remain unproved.** This is an evidence-only diagnosis. Four
allocator import trampolines are now byte-pinned, but they are not an AImain
resolver, object allocator/destructor or calibrated generation ledger.

## Locked observations

[diagnose.py](diagnose.py) verifies [input pins](input-sha256.json), reruns the
unchanged s267 → s261 analysis and retains all 8,290 events / 61 display samples.
The historical 122 actor rows / 14 fields still match s255; this is not a new
capture or Godot parity. No archive, receipt, tape or prior slice is resealed.

| Site/control | Retained observation | Missing native discriminator |
| --- | --- | --- |
| Last nonzero: event36/root8 | AImain frame1/total2, depth -16383 | Slot referent, saved-reference referent and generation |
| First zero: event44/root9 | AImain frame0/total0, same observed path/depth | Same resolver and complete intervening lifecycle history |
| Retained-content control candidate | One token property deleted; AS2 true,false | Actual content-clear operation with independently observed retention |
| Same-name/depth replacement | Explicit remove/create; AS2 true,false | Alloc/free generations and saved-reference resolution, including reuse |

The two AS2 signals remain indistinguishable. Property loss is not allocation
identity. A source-retained placement does not exclude internal replacement.
The roots are observed boundaries, not the clearing instruction or a promise
that a future capture will have the same root numbers.

## Bounded facility extension

[audit_facility.py](audit_facility.py) verifies the exact s261 player SHA-256
`8d4c1f5934adae809b5f4ce4f6ca7c64d4260df46bb3eb9c41fe32be2ee905be`.
[Facility records](facility/audit.json) retain exact commands, exits, timings and
transcript hashes. Module UUID: `067C4CFE-5B2A-3424-AAA0-1FAE2DF056EB` (x86_64).

- Module-scoped depth/member/reference/unload candidate breakpoints resolve
  zero locations (pending). LLDB exit0 means the pending request was created.
- `MovieClipObject` type and allocator symbol-name lookup return exit1.
  These bounded queries do not prove that reverse engineering is impossible.
- The indirect symbol table does expose calloc/free/malloc/realloc imports.
  [pin_imports.py](pin_imports.py) parses Mach-O sections, maps their addresses
  to file offsets, retains six-byte x86_64 `ff25` trampolines and the eight-byte
  initial pointer slots, and checks each RIP-relative destination against the
  matching indirect symbol. [Byte pins](allocator-import-pins.json) retain this
  derivation. These are unslid on-disk addresses, not live pointers.

| Import | Unslid trampoline | Indirect pointer slot |
| --- | --- | --- |
| calloc | 0x100fb6498 | 0x1014b3248 |
| free | 0x100fb65c4 | 0x1014b33d8 |
| malloc | 0x100fb66e4 | 0x1014b3558 |
| realloc | 0x100fb6894 | 0x1014b3798 |

System allocator interception alone would not prove object allocation/free:
internal pools may reuse objects without calling these imports. No target
object layout, allocator/destructor, pool coverage or saved-reference binding
has been derived. No lifecycle event is captured. Historical debugger startup
success does not resolve these missing relationships.

Zero new SWF builds, player launches, attaches or captures. No binary patch,
signing or security change. Repeating an AS2-only capture cannot supply the
missing native discriminator. Measured static/check cost is retained; future
resolver/capture cost is unknown. This is a bounded prerequisite failure,
not completion of the requested native facility.

## Next discriminator

1. Derive parent/depth lookup and saved-AS2-reference dereference independently
   on this module. Pin module-relative addresses, bytes, object layout and live
   provenance linking each result to AImain. The import table is only a starting
   point; generic renderer addresses and AS2 paths cannot substitute.
2. Establish allocation/destruction and internal pool reuse coverage before
   creating controls. Record a complete generation ledger, including frees and
   address reuse. Pointer equality alone is insufficient.
3. Qualify that resolver and ledger on actual retained-content clearing and
   explicit same-name/depth replacement. Observe retention and saved referents
   independently; do not rename the token-deletion control as content clearing.
4. Capture unchanged s261 input at source-equivalent last-nonzero/first-zero
   boundaries, preserving full event order, actual roots, engine/source/adapter
   hashes and both controls in the same run. Missing events keep the gate red.

No accepting native-trace schema or guessed resolver is introduced. Even a
qualified identity would not by itself justify frame0→1 or an unloaded exemption.

## Source-first and scope

s261 supplies the source answers: Yijiao Sprite455 frame1 initCtrl unload,
Sprite3 frame1 stop, no frame2 DoAction, retained parent placement; the original
same-input observations above still lack native identity. No runtime behavior
is inferred and no gameplay changes. No 0→1 alias, token-loss identity,
pointer-only identity, unloaded exemption or threshold relaxation.

Only s279 evidence, its focused tests and requested tracking files change.
Other ranks, s254–s278, priority authority, strict validators, contracts and
production code remain untouched. No merge or deployment.

## Reproduce

```sh
PYTHONPATH=. python3 evidence/sampling-upgrade/s279/diagnose.py --output /tmp/s279.json
PYTHONPATH=. python3 evidence/sampling-upgrade/s279/diagnose.py --output /tmp/s279-required.json --require-allocation-identity # expected exit 1
python3 -m unittest tools.tests.test_aimain_native_resolver_gap tools.tests.test_aimain_allocation_identity tools.tests.test_aimain_content_clearing tools.tests.test_aimain_unload_identity tools.tests.test_display_source_frame_diagnosis tools.tests.test_sampling_native tools.tests.test_sampling_display tools.tests.test_display_completion_default tools.tests.test_import_guards
python3 tools/verify.py
python3 tools/check_handoff.py
/tmp/bvn-s276-venv/bin/python tools/validate_contracts.py
```

Portable diagnosis/tests use retained files and launch no player. Optional
static reproduction needs the receipt-pinned installed binary:

```sh
python3 evidence/sampling-upgrade/s279/audit_facility.py --output /tmp/s279-facility-new
python3 evidence/sampling-upgrade/s279/pin_imports.py --output /tmp/s279-imports.json
```

The second command uses the retained indirect-symbol transcript and independently
reads the installed binary. Receipt/full-display commands use the unchanged
[s261 restore recipe](../s261/README.md); no receipt repair. Results, exact
commands and durations are in [gates.json](gates.json) and
[project-checks.json](project-checks.json). Scope, manifest changes and session
interval are recorded alongside them. No Godot test applies to this evidence-only cut.

Validation: **71 focused tests pass**. Diagnosis, original receipt, integrity,
handoff and contracts exit0. Allocation identity exits1. Full display exits1
with **169 unresolved source/hierarchy obligations** after restoring the original
XML cache. The first missing-cache exit1 is retained separately and is not
counted as a product rejection. No threshold or validator was changed.
