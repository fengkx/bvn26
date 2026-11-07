# s341 — AFTER-s335 rank #6: Terminal callback

Base: `30474236` (s340 #218 squash). Branch: `feat/s341-terminal-callback`.
Authority: [unchanged AFTER-s335 rank #6](../next-fix-priority-after-s335.md).
Only rank #6 executes; no re-ranking. Ranks 1–5 delivered as s336–s340 remain
closed; ranks 7+ planning only. Historical planning wording in the table is retained.
`production_admitted=false`; `native_parity_proven=false`; M0-02 pending.

## Result and evidence boundary

**Loaded closure/body, owner generation and activation through a
replacement-surviving dispatcher-continuation channel remain unproved.**
No independent live invocation was obtained. This is an unfulfilled binding cut
with honest failure gates, not completion of the terminal callback mechanism.
Zero builds, launches, attaches, memory reads, captures or product obligations closed.

[Binding attempt](binding-attempt.json) is a blocked measurement ledger, not an
executed trace. It targets the instrumentation root `onEnterFrame` installed by
archived `patches/main/frame_10/DoAction.as`, not an asserted authored gameplay
callback. Loaded closure/body, owner/defining-scope/closure generations, activation,
uninterrupted lifetime, replacement survival, matched dispatcher continuation and
outcome remain null. Boundary events for activation entry, done-producing invocation,
closing invocation, callback/logger replacement, quit request and dispatcher
continuation also remain null. Null does not assert that an operation did not execute.

[Diagnosis](diagnosis.json) reproduces the **complete locked s332 diagnosis**,
recursively validating s323/s314/s304 and retained terminal tooling. All s332 files
and its direct pinned inputs are [hash-pinned](input-sha256.json). Existing source
and facility conclusions, normal/held custody and suffix results are retained
validation only. No repeated adapter inventory is counted as new progress.
The only newly established results are package consistency and measured local
gate/test outcomes; zero new independent native observations.

The retained s332 host sink is independent of `aiEvent`, but that source fact
cannot associate loaded AVM closure/body, owner generation and activation through
replacement. Owned PID and disk hashes establish custody, not callback identity.
The deferred-quit source transform establishes ordering, not execution or outer
return. No new resolver or replacement-surviving channel was obtained here.
This bounded conclusion does not claim that a suitable facility cannot be built.

## Qualification order

First bind one executing closure/body to the archived callback, with uninterrupted
owner/closure generations and a unique activation from entry through replacement
to its dispatcher continuation. Preserve defining scope and distinguish normal
return, unwind and process termination. Done-producing and closing invocations
must remain separate even when display/fight counters coincide.

Then qualify observer-off and observer-on runs and their preservation comparison.
All three observations remain null; controls were not executed. Only after this
qualification may fresh terminal inventory run; inventory was not executed.
s314's five qualification requirements are retained unchanged in the diagnosis.
Even one qualified callback would not prove full terminal completeness.

No host timestamp or pointer as identity, assignment/inner-call marker as outer
return, silence-as-return, suffix threshold, trimming or random tape changes.
No trace import or proof override is accepted by this package.

## Reproduction and gates

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 evidence/sampling-upgrade/s341/diagnose.py --output /tmp/s341.json
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s341 -p 'test_*.py'
python3 tools/verify.py
python3 tools/check_handoff.py
```

Base diagnosis exit 0 means package consistency only. Each proof flag and their
combined invocation exit 1: `--require-independent-channel`,
`--require-logger-replacement`, `--require-callback-completion`,
`--require-off-on`, `--require-terminal-completeness`.
Distinct codes are `S341_<FLAG_WITH_UNDERSCORES>_UNPROVED`; changed pinned evidence
or invented observations fail separately with `S341_EVIDENCE_INVALID`.
Tests reject pointer/timestamp/source-hash identity, inner-call/assignment return,
silence, fabricated replacement survival and premature controls/inventory.
These protect evidence custody and unknowns, not guessed gameplay behavior.

Complete s332/s323/s314/s304/s293/s284 and retained shared terminal suites are
rerun unchanged. Actual commands, exits and costs: [gates](gates.json),
[project checks](project-checks.json), [timing](session-timing.json).
No runtime or contract changes require Godot or contract validation.

## Source-first and custody

1. Complete archived root frame action and exact callback hash remain in locked
   s304/s314 and s293 archive, with observer mappings retained by s323/s332.
2. No PlaceObject/MOVE or instance lifetime is changed or newly observed.
3. Explicit source return, structural body end and property replacement are not
   evidence of an active invocation returning to its dispatcher.
4. Tests preserve evidence and unknowns, not invented runtime invariants.
5. No new original/Godot same-input comparison; native parity remains unproved.

Only s341 plus minimal STATUS/SAMPLING_UPGRADE/tasks/manifest tracking changes.
All s254–s340 trees, authority tables, game/, scripts/, runtime, contracts and
shared sampler/threshold/validator remain byte-identical. No other rank executes.
[Scope audit](scope-audit.json), [manifest audit](manifest-audit.json) and
[artifact hashes](artifact-sha256.json) record custody. Artifact index excludes
itself and caches. Timing covers packaging/checks, excluding initial reading/design
and later commit/push/PR; person-days unknown. Draft only; no ready marking,
merge or deployment. Green package checks do not establish native parity.

Validation: **117 tests pass**. Base exit 0; five individual proof flags and
their combined invocation exit 1. Integrity, handoff and whitespace checks exit 0.
