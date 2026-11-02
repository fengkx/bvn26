# s289 — AImain native allocation prerequisite (honest-unproved)

Base: `origin/master` `8c54258ebd9d69a0266bfaac0d85d22b6f3c0b5a` (#166, s288).
Branch: `feat/s289-aimain-allocation`.
Exclusive authority: [AFTER-s281 rank #8](../next-fix-priority-after-s281.md).
`production_admitted=false`; `native_parity_proven=false`; M0-02 pending.
Evidence-only; zero product obligations closed.

**Neither one native slot/saved-reference pair nor actual allocation/free/reuse
has been resolved.** Both proof requirements exit 1 with
`S289_NATIVE_ALLOCATION_UNPROVED`. This delivery audits the prerequisite failure;
it does not complete the requested native mechanism.

## Bounded evidence audit

[diagnose.py](diagnose.py) verifies [input pins](input-sha256.json), recomputes
locked [s279](../s279/README.md) through s267/s261 and requires exact equality
with its retained diagnosis. All 8,290 events and 61 display samples remain;
122 actor rows / 14 fields still match s255. These are historical observations,
not a new capture or native/Godot parity result.

The new audit binds seven specific AS2 statements to the hashed archived
`patches/main/frame_1/DoAction.as`: saved-reference assignment and read,
parent/depth lookup, named lookup, remove, replacement creation and property
deletion. Archive member lines and SHA-256 are in [diagnosis.json](diagnosis.json).
These are AS2 source locations, **not native resolver addresses or object layout**.
No repeated allocator inventory is offered as runtime proof.

The audit retains every event in the bounded root observation window:

| Events | Observation | Limitation |
| --- | --- | --- |
| 36–40, root8 | Identity plus parent/saved/depth/named object reads; AImain frame1/total2 | AS2 equality does not resolve the native referent |
| 41 | Input-next-display record | No allocation/free observation |
| 42–43 | Intro-body enter/exit records | No native lifecycle coverage or clearing instruction |
| 44–48, root9 | Identity plus the four object reads; AImain frame0/total0 | Same path/depth does not establish a retained generation |

The entire raw stream is checked for contiguous sequence and one run ID before
extracting this window. Contiguous **logged** events are not a complete native
lifecycle history. Reads in an observation group are sequential, not an atomic
snapshot. The 25 ms between identity markers is not a measured allocator bound.
Root8/9 are historical boundaries, not prescribed roots for a future capture.

Control events21–23 are retained independently. The initial retained control
reports `true,true`; explicit remove/create and property deletion both report
`true,false`. Source bindings show `saved.removeMovieClip()`, replacement at
`slot`, depth1, and `delete replacement.identity`. Deleting that property is
not actual content clearing. The controls are outside the game tree and run
before the target unload; they cannot establish native retention, destruction,
address reuse, or saved-reference binding. Their equality result cannot decide
whether a saved AS2 reference resolves through a path, proxy or another mechanism.

## Blocker and next discriminator

s279's pending name breakpoints and allocator byte pins remain historical facts.
No native resolver, object layout, lifecycle ledger, pool-coverage qualification
or qualified native control is available in the locked evidence. All seven native
observation fields are explicitly null. No new binary analysis, debugger attach,
player launch, SWF build or capture was performed. Failure of the historical name
queries does not prove that stripped-binary analysis is impossible.

The next experiment first needs byte-pinned parent/depth and saved-AS2-reference
resolvers on the receipt-pinned player, with independently derived layouts and
live provenance. Resolve the same target at both boundaries, then qualify actual
object allocation/destruction and internal pool reuse with a complete ordered
generation ledger. Generic system malloc/free interception may miss pooled
lifetimes; a recycled address must not become retained identity.

Use the same qualified resolver/ledger for actual retained-content clearing and
explicit same-name/depth replacement, observing saved referents independently.
If reuse is not exercised or lifecycle coverage has gaps, reuse remains unproved.
Only after both controls qualify should unchanged s261 input be captured at
source-equivalent boundaries with full run/source/engine hashes and event order.
No accepting native-trace schema or synthetic positive result is introduced.

## Source-first and scope

The five source-first answers stay locked to s261: Yijiao Sprite455 frame1
`initCtrl` unload; Sprite3 frame1 `stop` and no frame2 DoAction; retained parent
placement rather than a source remove/recreate; no invented label-end return;
source/control invariants separated from allocation identity; same-input original
AS2 observations exist but the native identity comparison is absent. No runtime
implementation is justified by these incomplete answers.

Only s289 and proportionate tracking files change. No edits under s254–s288,
`game/`, `scripts/`, runtime, contracts, shared samplers, thresholds or validators.
No execution of AFTER-s281 ranks1–7 or9. No pointer-only identity, 0→1 alias,
token-loss identity, unloaded exemption, production admission, merge or deployment.

## Reproduce

```sh
PYTHONPATH=. python3 evidence/sampling-upgrade/s289/diagnose.py --output /tmp/s289.json
PYTHONPATH=. python3 evidence/sampling-upgrade/s289/diagnose.py --output /tmp/s289-slot.json --require-slot-reference # expected exit 1
PYTHONPATH=. python3 evidence/sampling-upgrade/s289/diagnose.py --output /tmp/s289-allocation.json --require-allocation-identity # expected exit 1
PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s289 -p 'test_*.py'
PYTHONPATH=. python3 -m unittest tools.tests.test_aimain_native_resolver_gap tools.tests.test_aimain_allocation_identity tools.tests.test_aimain_content_clearing tools.tests.test_aimain_unload_identity tools.tests.test_display_source_frame_diagnosis tools.tests.test_sampling_native tools.tests.test_sampling_display tools.tests.test_display_completion_default tools.tests.test_import_guards
python3 tools/verify.py
python3 tools/check_handoff.py
```

[Gates](gates.json), [project checks](project-checks.json),
[scope audit](scope-audit.json), [manifest audit](manifest-audit.json) and
[timing](session-timing.json) retain exact outcomes and measured check costs.
Initial reading/design and future resolver/capture costs are unmeasured;
person-days remain unknown. No Godot or contract checks apply to this evidence-only
change. Tests protect evidence boundaries; they do not qualify native allocation.

Validation: **77 tests pass** (6 new + 71 retained). Diagnosis, input integrity,
handoff and diff checks exit0; both native proof requirements exit1 as expected.
