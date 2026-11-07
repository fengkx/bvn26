# s322 — AFTER-s317 rank #5: P2 body-push observer

Base: origin/master `6e67d78d` (s321 squash #199).
Branch: `feat/s322-body-push-observer`.
Authority: [unchanged AFTER-s317 rank #5](../next-fix-priority-after-s317.md).
Only rank #5 is executed; ranks 1–4 deliveries remain closed, ranks 6+ planning.
**Evidence-only, honest-unproved.** `production_admitted=false`;
`native_parity_proven=false`; M0-02 pending; zero product obligations closed.

## Outcome

Live defining scope and this/root/parent qualification is still **unproved**.
There is no independent live observation in this slice. No helper is installed
and no off/on control is run. Delivery is a bounded prerequisite audit, not a
qualified observer or completed rank-5 mechanism.

The complete locked [s312](../s312/README.md) diagnosis is reproduced, including
5,437 historical events. Its header/preload-name mapping and s300's four-store /
eight-read dataflow result are retained validation, **not new progress**.

The new result is an initializer-to-overwrite/return/body-end exposure audit of
both complete unprojected archived callbacks. It retains each intervening node,
all structural successors, and a witness path to every node. Candidate mapped
regions are checked against original regions using the locked correspondence.
This does not install, rewrite or erase any code. Calls are traversed only under
conditional normal continuation; exceptional/native edges and path feasibility
are not inferred. All indices below are expanded archived pcode nodes, not byte
offsets, frames, native PCs or actual execution order.

| Candidate register / initializer | First explicit overwrite | Returns before overwrite | Body end before overwrite | Calls before overwrite |
| --- | --- | --- | --- | --- |
| r7 / 234 | 353 | 430, 465, 481, 504 | 543 | 251, 275, 287, 310, 319, 321, 326, 443 |
| r8 / 237 | 368 | 430, 465, 481, 504 | 543 | same eight sites |
| r9 / 240 | 381 | 430, 465, 481, 504 | 543 | same eight sites |
| r12 / 432 | 444 | 504 | 543 | 443 |

The first three original regions start at node223 and contain calls271/385;
the last starts at376 and contains call385. Candidate calls251/275/287/310/319/326
are hypothetical observer envelopes; call321 corresponds to original271,
and call443 to original385. These are static sites, not executed invocations.
Scope/member operations are retained separately without classifying any as
harmless. A body-end sentinel is **not** an observed dispatcher return. The
regions show why explicit-read overwrite alone cannot establish that added
values are invisible to intermediate operations or exits. They do not prove
hidden access, a mutation, an exception, or a behavioral difference.

The new coercion cut connects original150–154 (`GetVariable("dashing")`, two
`Not`s, then `If`) with candidate162–164 (the scope read directly followed by
`If`). Branch operands and both successor edges are retained in
[diagnosis.json](diagnosis.json). Actual value, type and coercion effects remain
null. Matching spelling cannot identify the scope entry supplying that value;
no claim that the value is Boolean or that coercion is harmless is made.

## Independent binding prerequisite

| Required evidence for one retained invocation | Available / missing |
| --- | --- |
| Loaded original/candidate function body and defining scope chain with lifetime/generation | Archived bodies only; no independent live scope chain |
| Actual this, root and parent identity and changed suppression/preload visibility | s312 static names only; all live identities null |
| Activation slot state at initializer, intervening scope/member/call boundaries, overwrite and exits | New structural witnesses only; no independent activation observation |
| Value/type at the dashing scope read and coercion/branch effects | New source-bound cut only; actual operands null |
| Independent mutation, exception, reentrancy, lifetime and scheduling controls | Blocked pending binding and erasure qualification |
| Natural executed/skipped observer-off/on controls and same-run operand lifetimes | Blocked; historical callsite execution remains null, not false |

Do not use `s283Value`'s owner argument or a helper-written stamp to prove its
own identity or neutrality. A resolver must bind the loaded body, invocation,
defining scope, activation and this/root/parent generations independently; path
strings, register names and pointer equality alone are insufficient. Then
measure the initialization/coercion boundary before qualifying helper effects
and off/on controls. This package has no live resolver and accepts no external
trace or proof override. The missing facility is reported, not simulated.

## Source-first

1. Complete callbacks remain locked in s283 and the caller/frame map in s273;
   no partial collision window substitutes for complete callback evidence.
2. Retained Sprite638 new depth1 placement is not MOVE; it does not bind the
   current activation or live operands.
3. Six explicit returns and structural body-end remain distinct from native
   invocation return. No label-end or silence-based return is inferred.
4. Tests assert source-derived paths, edges, calls and rejection of mutation;
   they impose no gameplay/scheduling assumptions.
5. Historical same-input evidence is revalidated only; no new original/Godot
   comparison. Runtime and native parity remain unproved.

## Gates and reproduction

| Gate | Expected exit |
| --- | --- |
| Archived diagnosis (`S322_DIAGNOSIS_OK`) | 0 |
| `--require-scope-binding` | 1 |
| `--require-activation-erasure` | 1 |
| `--require-coercion-erasure` | 1 |
| `--require-helper-effects` | 1 |
| `--require-off-on` | 1 |
| `--require-external-callsite` | 1 |

Each proof flag emits its distinct `S322_*_UNPROVED` code. Invalid pinned
inputs emit `S322_EVIDENCE_INVALID`, not an unproved gate.

```sh
PYTHONPATH=. python3 evidence/sampling-upgrade/s322/diagnose.py --output /tmp/s322.json
# Repeat individually with each proof flag above: expected exit 1.
PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s322 -p 'test_*.py'
# Full retained test commands and measured results: project-checks.json
python3 tools/verify.py
python3 tools/check_handoff.py
```

[Gates](gates.json), [project checks](project-checks.json), [scope](scope-audit.json),
[manifest audit](manifest-audit.json), [timing](session-timing.json), and
[artifact hashes](artifact-sha256.json) retain measured results. Hash index excludes
itself and caches. Initial reading/design and person-days are unknown; measured
implementation excludes later commit/push/PR work.

Only s322 and minimal STATUS/SAMPLING_UPGRADE/tasks/manifest tracking change.
Prior s254–s321 evidence and the authority table remain byte-identical. No early
initialization, receiver exemption, extra hitTest, tick41, re-ranking, rank6+
experiment, runtime/contracts/shared sampler/threshold/validator change, build,
launch, attach, memory read or capture. No deployment, ready marking or merge.

Validation: **117 tests pass** (9 s322-tests, 11 s312-tests, 12 s300-tests, 10 s291-tests, 10 s283-tests, 65 retained-tests). Base diagnosis exits0; all six proof gates exit1. Integrity, handoff and whitespace checks exit0. Green package checks do not establish observer qualification.
