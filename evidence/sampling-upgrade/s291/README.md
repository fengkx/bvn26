# s291 — Post-s290 rerank + rank1 body-push structural qualification

Baseline: `origin/master` `975defcd0a9e6c80a3b938bc27ee14964e4459b8` (#168).
Branch: `feat/s291-after-s290-rerank`. Authority:
[AFTER-s290 rank1](../next-fix-priority-after-s290.md).
**Only rank 1 is executed in s291. Ranks 2+ are planning only.**
`production_admitted=false`; `native_parity_proven=false`; M0-02 pending.
Evidence-only; zero product obligations closed. The s282–s290 deliveries stay closed.

The new table reviews all nine AFTER-s281 deliveries and their s273–s281
predecessors. [Ranking pins](ranking-basis-sha256.json) retain that basis.
Body-push moves first because s283's complete archived function graphs permit
a concrete static discriminator without a new native facility. Digit entry and
completion follow; Chad's byte-pinned authored control moves ahead of UI/Loader.
This is not an ordering by probability of an accepting gate.

## Result: conditional structural correspondence, observer still unqualified

[diagnose.py](diagnose.py) re-executes unchanged s283 → s273 → s264 validation,
including all 5,437 historical events and archived function extraction; the
result must equal the locked s283 diagnosis. It then compares the **whole**
original/candidate Sprite638 `on_enterframe` function, not just the hitTest site.
Input pins also bind the new authority and archived pcode/full-frame exports.

| Structural audit | Result |
| --- | --- |
| Original / candidate expanded nodes | 485 / 543 |
| Explicit candidate deletions | 8 owner pushes + eight 5-node observer envelopes + four 3-node local initializations = 60 |
| Explicit original deletion | Two consecutive Not instructions at the doDashX guard |
| Remaining nodes | 483 on each side; every instruction and ordered successor matches under the stated register map |
| Register correspondence, candidate → original | 0→0, 2→1, 3→2, 4→6, 5→4, 6→3, 7→8, 8→5, 9→11, 10→10, 11→7, 12→9 |
| Exits / collision calls | All six explicit returns, terminal edges and the single hitTest retained |
| Function headers | Different, retained verbatim; register counts 12/13 and flag changes are not normalized away |

[diagnosis.json](diagnosis.json) includes every deletion's original candidate
indices/instructions, every residual node's original/candidate index and branch
successors, plus every register use/write index. Labels are resolved by the
unchanged s283 projector; only Push packing and integral spelling receive its
existing normalization. No string, call, write, return or remaining branch is
silently discarded. Branch destinations are translated through explicitly
removed straight-line nodes, including the terminal function boundary.

This is a **hypothetical erasure audit**, not a bytecode patch, interpreter,
complete equivalence proof or runnable capture build. Four assumptions remain:

1. Changed flags/preloads must bind corresponding registers to equivalent live
   activations. Whole-body syntactic correspondence alone cannot prove that.
2. `s283Value` must return its input without mutations, exceptions, reentrancy,
   lifetime or scheduling effects. s283 never installed a helper. Removing its
   calls in this audit does not prove those properties or dynamic once-only use.
3. The four added local initializations must be unobservable in the actual
   activation. They are explicitly accounted for, not declared harmless.
4. Removing double-Not before If must preserve coercion on the actual values.
   This audit does not execute AVM1 or certify that semantic transformation.

Thus `conditional_body_graph_equal=true`, but
`activation_correspondence_proved=false`, `observer_qualified=false` and
`external_callsite_execution_proved=false`. Historical site execution remains
**null**, not false; no geometry eligibility exemption follows. Both proof
requirements honestly exit1 with `S291_OBSERVER_UNPROVED`.

The new result narrows s283's undifferentiated full-function diff to exact,
reviewable transformations and four outstanding proof obligations. It does not
turn absent observations into evidence. A future cut must independently qualify
those activation/erasure assumptions and the bounded helper, then use natural
executed/skipped controls and same-run operand lifetimes. Static addresses,
source expression counts and equal sampled actor state cannot replace that work.

## Source-first and scope

1. The complete callback/caller and frame4–7 empty-script map remain locked in
   s273; s283 provides full exported opcodes, guards and target-before-receiver
   order. This audit retains all preceding side effects and later movement.
2. The wrapper places Sprite638 at depth1, new, not MOVE; body/P1 bdmn placements
   and initialization markers remain s273/s264 evidence, not live operand identity.
3. Explicit returns, branches, conditional goto/play and terminal fallthrough
   are retained; no label-end reset is invented.
4. Tests reject altered registers, writes, branches, observer envelopes, erased
   control flow, missing initialization/return and changed input hashes. They
   protect the evidence boundary and do not assert guessed collision outcomes.
5. The unchanged s64 tape's historical run lacks this callsite observation;
   there is no new original/Godot comparison. No runtime change is authorized.

Zero new builds, helper installations, player launches, captures or images.
No extra hitTest, receiver exemption, early initialization, tick41 or collision
rollout. Only s291, the new priority table and proportionate tracking change.
s254–s290, game/scripts, runtime/contracts, shared sampler/threshold/validator,
receipts and baseline tapes stay unchanged. No ranks2+ execution, merge or deployment.

## Reproduction and validation

```sh
PYTHONPATH=. python3 evidence/sampling-upgrade/s291/diagnose.py --output /tmp/s291.json
PYTHONPATH=. python3 evidence/sampling-upgrade/s291/diagnose.py --output /tmp/s291-observer.json --require-observer # exit 1
PYTHONPATH=. python3 evidence/sampling-upgrade/s291/diagnose.py --output /tmp/s291-call.json --require-external-callsite # exit 1
PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s291 -p 'test_*.py'
PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s283 -p 'test_*.py'
python3 tools/verify.py
python3 tools/check_handoff.py
```

[Gates](gates.json) retain exact commands/costs, including the retained tool tests
and historical callsite rejection. [Project checks](project-checks.json),
[scope audit](scope-audit.json), [manifest audit](manifest-audit.json) and
[timing](session-timing.json) retain actual outcomes. Initial reading/design,
future qualification/capture cost and person-days are unmeasured. No Godot or
contract checks apply because no implementation or contract changed.

Validation: **85 tests pass** (10 new, 10 retained s283, 65 retained tools).
Diagnosis, integrity, handoff and diff checks exit0; both new proof gates and
the retained historical callsite requirement exit1 as expected.
