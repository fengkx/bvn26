# s97 — Neji attack: Call-site and branch observations

One character PR, exactly `neji__attack__neutral__ground__near`, unchanged s91 tape.
Base `d96007053404dca228b326e0db2aa0656a77e627`; branch `feat/sampling-neji-attack-one-cell`.
`production_admitted=false`; `native_parity_proven=false`.

## Result

10,892 events, 61/61 root samples; 453 complete invocations (409 false / 44 true with paired calls). 1 additional invocation lacks complete boundaries; see exact tick, sequence, path and phases in callsite-summary.json. Selected-boundary gate exits 1. 623 unvisited / 415 uninstrumented source items retained.

Removing each of six phase markers from actual complete invocations rejects; full-stream missing event/sample and deleted obligations reject. The local grammar tests do not remove incomplete invocations from the full report. Original report/receipt revalidate.

Review callsite-summary.json, actions.json.gz, ownership-gate.txt and negative-proof.json, plus acceptance.json and native receipt/build/capture artifacts.
Full residual lists remain intact; no allowlists, tolerances, reference rewriting
or runtime/gameplay changes. 85 focused + 25 importer guard + 19 probe tests
pass (129 distinct tests shared across these seven dimensions). Logs and final
integrity/handoff/contracts results live in [s91](../s91/README.md).

## Reproduction and limits

See [shared reproduction and evidence contract](../s91/REPRODUCTION.md) for exact
commands, paths, hashes and archive restoration. Each native run has its own
environment record; neither pixels nor observations are synthetic substitutes.
Capture completeness does not prove native parity. Source gaps, sampled lifetime
limits, clock/render-phase differences and full AS ownership remain explicit.
No geometry/image/ownership gap is waived by success in another dimension.

## Next discriminator

Record doAllAction exit and receiver lifecycle at the incomplete invocation to
distinguish nonreturn from observer loss. Do not fabricate call_after/end.
Callee bodies, other branches, dynamic dispatch and Godot ownership remain unproven.
