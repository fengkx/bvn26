# s332 — AFTER-s326 rank #6: terminal callback prerequisite

Base: `4a6da57c` (s331 #209); branch: `feat/s332-terminal-callback`.
Authority: [unchanged AFTER-s326 rank #6](../next-fix-priority-after-s326.md).
Only rank 6 is executed. Ranks 1–5 deliveries stay closed; ranks 7+ planning only.
`production_admitted=false`; `native_parity_proven=false`; M0-02 pending.

## Result

The replacement-surviving loaded-closure/body, owner-generation and activation
channel through dispatcher continuation remains **unproved**. Zero independent
live invocations were observed. This is an evidence/facility gap delivery, not
completion of the terminal callback mechanism. Off/on qualification is blocked
before execution; terminal inventory is deferred until qualification.

[Diagnosis](diagnosis.json) records exact source excerpts and line spans for
three inspected adapters. These functions were read, not invoked:

| Adapter | Independent fact and missing binding |
| --- | --- |
| `probe_owned_debugger.debugger_script` | The host JSON sink does not call `aiEvent`. It records selected frame-zero CPU registers then detaches. Sink independence alone supplies neither loaded AVM closure/body identity nor uninterrupted owner/closure generation, activation entry or matched dispatcher continuation. |
| `probe_owned_debugger.probe` | Unique owned PID and disk build hashes protect custody. Waiting for a run profile uses AIREF. `script_factory` and `post_debugger` are extension points, not implemented identity resolvers or measured replacement survival. Process ownership is not callback-owner generation. |
| s284 `defer_quit` | The source transform moves quit after logger replacement. Source ordering cannot establish that replacement or quit ran, whether control returned, or observer preservation. No transform/build was invoked here. |

This bounded facility check adds no live proof and does not claim that a suitable
external facility cannot be built. All s323 files are hash-pinned; its complete
diagnosis is reproduced, recursively retaining s314/s304 and earlier terminal
evidence. The four observer applicability findings, host custody pair and suffix
results are **retained validation only**, never new s332 progress.

## Qualification boundary

Loaded closure/body, owner/defining-scope/closure generations, activation entry,
logger replacement, matched dispatcher continuation, outcome and survival remain
null. Observer-off, observer-on and their preservation comparison also remain
null. s314's five required qualified witnesses are carried forward unchanged.

A usable channel must independently bind one executing body to the archived
callback and retain the same owner/closure generation and invocation across
replacement through the dispatcher continuation. Done-producing and closing
invocations must remain distinct even when their display/fight counters coincide.
Normal return, unwind and process termination require distinct observed outcomes.
A host timestamp, source hash, pointer, assignment marker, inner-call marker or
silence cannot fill these joins. Only after the channel is bound may off/on effects
be qualified; only after that may fresh terminal inventory begin. No trace or
proof override is accepted by this package.

## Gates and reproduction

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 evidence/sampling-upgrade/s332/diagnose.py --output /tmp/s332.json
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest discover -s evidence/sampling-upgrade/s332 -p 'test_*.py'
python3 tools/verify.py
python3 tools/check_handoff.py
```

Base diagnosis exit 0 means package consistency only. Each requirement exits 1:
`--require-independent-channel`, `--require-logger-replacement`,
`--require-callback-completion`, `--require-off-on`,
`--require-terminal-completeness`. Each emits a distinct `S332_*_UNPROVED` code;
changed evidence emits `S332_EVIDENCE_INVALID`. Tests reject substituted prior or
adapter evidence and preserve unknowns and fail-closed gates. Retained s323,
s314, s304, s293, s284 and shared terminal tests are rerun.
Measured exits and costs: [gates](gates.json), [checks](project-checks.json),
[timing](session-timing.json). No runtime/contract change requires Godot or
contract checks. Green package checks do not prove product parity.

## Source-first and scope

1. Complete archived root frame action remains in locked s304/s314 and s293 archive;
   s323 retains its exact callback hash and observer source mappings.
2. No placement/MOVE or instance lifetime is changed or newly observed.
3. Explicit source return and body end are not observed dispatcher return.
4. Tests protect evidence custody and unknowns, not assumed gameplay behavior.
5. No new original/Godot same-input comparison; native parity stays unproved.

Only s332 plus minimal STATUS/SAMPLING_UPGRADE/tasks/manifest tracking changes.
Authority and every s254–s331 tree stay byte-identical, as do game/scripts,
runtime, contracts and shared sampler/threshold/validator. No re-ranking, other
rank experiment, suffix threshold, trimming, random tape change, receipt resealing
or full-AS claim. Zero builds, launches, attaches, memory reads, captures and
product obligations closed. Artifact index excludes itself and caches. Measured
packaging time excludes initial reading/design and subsequent commit/push/PR;
person-days unknown. Draft only; no ready marking, merge or deployment.
