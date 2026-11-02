# s312 — AFTER-s308 rank #4: P2 body-push binding qualification

Base: origin/master `19aef574dbba5e574ffa492eabb6066dd6214f64` (s311 #189).
Branch: `feat/s312-body-push-observer`.
Authority: [AFTER-s308 rank #4](../next-fix-priority-after-s308.md).
**Evidence-only, honest-unproved.** `production_admitted=false`;
`native_parity_proven=false`; M0-02 pending. Zero product obligations closed.
Only rank #4 is executed; ranks 1–3 and 5–9 are excluded.

## Result and qualification boundary

[diagnose.py](diagnose.py) pins the complete s300 artifact set and reproduces
its locked diagnosis, recursively revalidating 5,437 historical events.
The four-initialization/eight-read overwrite result stays closed: it is retained
validation, not new work. The new audit decodes the archived callback headers,
checks preload name correspondence, inventories the full callbacks' scope/member
operations, calls and six returns each, and locates the observer/initialization
boundaries. [diagnosis.json](diagnosis.json) retains all node witnesses.

Header interpretation is tied to the official JPEXS **version26.2.1** source at
commit `792d2c2fc886ddac030c601d286cf179b11b59c4`, matching the archived exporter
version. The [retained reference source](ActionDefineFunction2.java) preserves its
license notice; only trailing whitespace is stripped, with both hashes in
[source provenance](source-provenance.json). It is documentation evidence, not an installed tool or executable.
[Upstream source](https://github.com/jindrapetrik/jpexs-decompiler/blob/792d2c2fc886ddac030c601d286cf179b11b59c4/libsrc/ffdec_lib/src/com/jpexs/decompiler/flash/action/swf7/ActionDefineFunction2.java)
provides `getASMSource` flag order and `getRegNames` preload naming. Both are
checked by the diagnostic; neither is evidence of native Flash activation state.

| Header fact | Original | Candidate |
| --- | --- | --- |
| register count | 12 | 13 |
| suppressThisFlag | true | false |
| preloadThisFlag | false | true |
| exporter-named preloads | r1 `_root`, r2 `_parent` | r1 `this`, r2 `_root`, r3 `_parent` |

All other flags match; both callbacks have zero parameters. The old register
map agrees for `_root` and `_parent`, so **static exporter preload-name
correspondence is proved**. This does not prove live object identity, defining
scope equivalence, or the consequences of changing `this` suppression.
The candidate reads r1 eight times and never explicitly stores it. Those reads
are the erased observer owner pushes; their actual live identity remains unknown.
The complete 485/543-node callbacks, not just the collision window, are checked
against s291 before using its correspondence. Unqualified function/variable and
member access remains visible in the inventory even where opcode names match.

Candidate initialization stores 234/237/240 occur lexically after observer calls
68/105 and before the other six observer calls; store432 occurs lexically after
all eight. These are **expanded archived pcode node indices**, not byte offsets,
frames or observed execution order. The audit does not assume these calls ran,
that indices form a feasible path, or that earlier observers see later stores.
This locates the scope/activation qualification surface; it does not repeat the
solved reaching-definition traversal or infer hidden effects from explicit reads.
Absence of an explicit store to r1 cannot prove no reentrancy or external mutation.

Live defining scope, `this`/root/parent identity, activation-visible erasure,
helper-effect observations and independent off/on observations remain **null**.
Double-Not coercion on actual values also remains unproved. No helper is installed
and no off/on capture is attempted while this prerequisite is unqualified.
Historical callsite execution stays null, not false; there is no receiver
exemption, geometry-ineligibility conclusion or observation of a skipped call.

## Gates and next prerequisite

| Requirement | Exit | Code |
| --- | --- | --- |
| Reproducible archived binding audit | 0 | `S312_DIAGNOSIS_OK` |
| Live scope binding | 1 | `S312_SCOPE_BINDING_UNPROVED` |
| Activation-visible erasure | 1 | `S312_ACTIVATION_ERASURE_UNPROVED` |
| Independent helper effects | 1 | `S312_HELPER_EFFECTS_UNPROVED` |
| Independent observer off/on | 1 | `S312_OFF_ON_UNPROVED` |
| External callsite execution | 1 | `S312_EXTERNAL_CALLSITE_UNPROVED` |

Next, qualify original/candidate defining scope and this/root/parent identities
for a retained invocation, including changed suppression and hidden activation
visibility. Establish initialization and double-Not erasure before independent
helper mutation/exception/reentrancy/lifetime/scheduling measurements. Only then
qualify natural executed/skipped observer-off/on controls with same-run operand
lifetimes. This diagnostic accepts no caller-supplied live trace or proof flag.
No static header decoder can discharge those missing observations.

## Source-first and scope

1. The complete callbacks and caller/empty frame4–7 map remain locked in s273,
   with full exports in s283. All earlier/later calls and scope operations are
   retained; matching textual accesses are not matching live scope bindings.
2. Sprite638 is a new depth1 placement, not MOVE. Historical body/P1 bdmn
   placement markers do not identify live operands or activation ownership.
3. All six returns and full terminal edges remain checked by the locked audit;
   no label-end return, timeline transition or execution from silence is inferred.
4. Tests assert source header fields/names, actual owner pushes, complete call
   inventory, lexical cuts and rejection of changed source/full-body evidence.
   They assert no invented gameplay outcome or live scheduling rule.
5. Historical same-input native evidence is revalidated only. There is no fresh
   original/Godot comparison; runtime and native parity stay unproved.

Only s312 and proportionate STATUS/SAMPLING_UPGRADE/tasks/manifest updates change.
No edits under s254–s311, game/, scripts/, runtime, contracts, shared sampler,
threshold or validator. No early initialization, receiver exemption, extra
hitTest, tick41, other-rank execution or runtime change. Zero builds, player
launches and captures. No deployment or merge. M0-02 stays pending.

## Reproduce and validation

```sh
PYTHONPATH=. python3 evidence/sampling-upgrade/s312/diagnose.py --output /tmp/s312.json
# Each flag independently expects exit 1:
# --require-scope-binding --require-activation-erasure --require-helper-effects
# --require-off-on --require-external-callsite
PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s312 -p 'test_*.py'
PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s300 -p 'test_*.py'
PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s291 -p 'test_*.py'
PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s283 -p 'test_*.py'
PYTHONPATH=. python3 -m unittest tools.tests.test_external_collision_callsite tools.tests.test_receiver_authored_query tools.tests.test_receiver_init_order tools.tests.test_p1_receiver_availability tools.tests.test_sampling_geometry tools.tests.test_sampling_native tools.tests.test_import_guards
python3 tools/verify.py
python3 tools/check_handoff.py
```

[Gates](gates.json), [checks](project-checks.json), [scope](scope-audit.json),
[manifest audit](manifest-audit.json), [timing](session-timing.json) and
[artifact hashes](artifact-sha256.json) record measured outcomes. Hash index excludes
itself. Initial reading/design and person-days are unknown; measured implementation
excludes later commit/push/PR work. No runtime or contract check applies.

Validation: **108 tests pass** (11 focused, 12 retained s300, 10 retained s291,
10 retained s283, 65 retained tools). Archived diagnosis exits0; all five proof
gates exit1. Integrity, handoff and whitespace checks pass. Green package checks
do not qualify the live body-push observer.
