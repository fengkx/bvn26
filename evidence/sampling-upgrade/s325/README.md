# s325 — AFTER-s317 rank #8: AImain allocation

Base: origin/master `93c306d177cc8f2dbafb52be73c049df5f9c0cd3` (s324, #202).
Branch: `feat/s325-aimain-allocation`.
Authority: [AFTER-s317 rank 8](../next-fix-priority-after-s317.md).
**Evidence-only, honest-unproved.** `production_admitted=false`;
`native_parity_proven=false`; M0-02 pending; zero product obligations closed.
Rank 9 stays planning. The authority table and s254–s324 are unchanged.

## Result

Independent native slot/reference layouts and live binding were **not derived**.
Actual retained-content clearing, replacement, free and reuse with uninterrupted
pool generations remain unproved. This package records a bounded prerequisite
investigation, not completion of the native thin cut. Base diagnosis exits 0;
all four proof-require modes exit 1.

New observation: the currently installed native player has the same SHA-256 as
s298's retained binary, `8d4c1f5934adae809b5f4ce4f6ca7c64d4260df46bb3eb9c41fe32be2ee905be`.
Fresh `nm -m` and `otool -l` outputs are retained alongside a direct read of its
Mach-O LC_SYMTAB using [collect_native.py](collect_native.py). The raw nlist entry
bytes, file offsets and names are in [native-symbol-table.json](native-symbol-table.json).
These are on-disk observations; no process attach, live memory read, build,
player launch or capture was performed.

The table contains 1,039 entries: 1,032 undefined imports, six section-defined
symbols, and one N_OPT/debug entry (`radr://5614542`) omitted by ordinary nm output.
Thus nm's 1,038 lines do not represent a missing allocation event or an incomplete
native generation. The six defined names are `_NXArgc`, `_NXArgv`, `___progname`,
`__mh_execute_header`, `_environ` and `_main`. No `__DWARF` segment is listed.
The module UUID is `067C4CFE-5B2A-3424-AAA0-1FAE2DF056EB`.

This inventory supplies no independent slot/reference layout or byte-bound
resolver. Imported allocators are not internal pool checkout/return coverage;
`_main` is not an AImain object resolver. Absence of named symbols/debug sections
does not prove layouts cannot be reverse engineered, and this is **not** an
exhaustive machine-code analysis or an external debug-file search. Disk hash/UUID
identity does not establish a loaded module, owner, AS2 referent or allocation
generation. No offsets, native types or generations are invented.

[diagnose.py](diagnose.py) cross-checks the two symbol inventories and entry bytes,
then reproduces the **entire** locked [s316 diagnosis](../s316/diagnosis.json).
Its historical 8,290 AIREF events, operand distinction and four observation gaps
are retained validation, not new progress or a fresh native run. All seven native
observations remain null. `saved == host.slot` and property-token loss remain
AS2 signals, not independent native retention/replacement evidence.

## Next discriminator and exclusions

The prerequisite remains two separately derived paths on the pinned binary:
parent/depth occupant lookup and saved AS2 reference dereference, with instruction
bytes, layouts, relative addresses, then live module/owner bindings. Only after
qualification may observation begin **before** control allocation and continue
through actual clearing, same-name/depth replacement and real free/reuse. It must
cover internal pool generations without gaps and retain actual deferred-free
ordering. Removal need not free immediately; unexercised reuse remains unproved.

No pointer-only identity, 0→1 alias, property deletion as clearing, token-loss
inference or unloaded exemption. No native controls were executed: they are
deferred behind unresolved layouts/live binding. No AS2 symbol-name guess or
malloc/free import is promoted into an accepting resolver.

Source-first answers remain locked in s316 → s307 → s298/s289/s261: Yijiao
Sprite455 frame1 initCtrl unload; Sprite3 frame1 stop and no frame2 DoAction;
retained parent placement; no invented label-end return; source invariants
separate from native identity; historical same-input AS2 evidence without native
allocation proof. No mechanism/runtime change or source-first completion claim.

## Reproduction and gates

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 evidence/sampling-upgrade/s325/diagnose.py --output /tmp/s325.json
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s325 -p 'test_*.py'
python3 tools/verify.py
python3 tools/check_handoff.py
```

| Mode | Exit | Meaning |
| --- | --- | --- |
| Base diagnosis | 0 | Reproducible audit only; admission and parity false |
| `--require-slot-reference` | 1 | `S325_SLOT_REFERENCE_UNPROVED` |
| `--require-content-clearing` | 1 | `S325_CONTENT_CLEARING_UNPROVED` |
| `--require-replacement` | 1 | `S325_REPLACEMENT_UNPROVED` |
| `--require-allocation-identity` | 1 | `S325_POOL_GENERATIONS_UNPROVED` |

Fresh collection is reproducible with the binary path recorded in
[native-inventory.json](native-inventory.json), its exact nm/otool commands, and:

```sh
python3 evidence/sampling-upgrade/s325/collect_native.py '/Users/fengkx/me/code/flash-player/Flash Player.app/Contents/MacOS/Flash Player Debugger' --output /tmp/s325-native-symbol-table.json
```

The collector refuses a different binary hash. Routine diagnosis uses retained
inputs and requires no installed player. Tests reject missing/reordered entries,
changed nlist bytes, imports relabeled as definitions, cross-binary provenance
and invented live binding. They do not assert hypothetical allocation behavior.
Retained s316/s307/s298/s289 and shared AImain/display/sampling tests also run.

[Gates](gates.json), [project checks](project-checks.json), [scope audit](scope-audit.json)
and [manifest audit](manifest-audit.json) record actual exits, timing and scope.
[Input hashes](input-sha256.json) pin authority, prior inputs and fresh inventories;
[artifact hashes](artifact-sha256.json) cover all slice files except the index itself.
[Session timing](session-timing.json) excludes unmeasured initial reading and
exploration; person-days remain unknown. Only this evidence tree and minimal
STATUS/SAMPLING_UPGRADE/tasks/manifest tracking change. No game/, scripts/,
runtime, contracts, shared sampler/threshold/validator changes, merge or deployment.

Validation: **115 tests pass**; base diagnosis exit 0; all four proof gates
exit 1; verify.py, check_handoff.py and whitespace checks pass. Fresh binary
collection reproduces the retained symbol-table artifact byte for byte.
