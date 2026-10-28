# s83 — Renji attack: Call-site and branch observations

One character PR, exactly `renji__attack__neutral__ground__near`, unchanged s77 tape.
Base `9ce1db68421d91f3ef0433d41d59b324f92344f7`; branch `feat/sampling-renji-attack-one-cell`.
`production_admitted=false`; `native_parity_proven=false`.

## Result

10,074 events, 61/61 root samples; 448 complete invocations (405 false / 43 true with paired calls). Another tick-10 invocation (entry 7912, instance258) reaches call_before but lacks call_after/end. Selected-boundary gate exits 1. 608 unvisited / 417 uninstrumented source items retained.

Removing each of six phase markers from actual complete invocations rejects; full-stream missing event/sample and deleted obligations reject. The local grammar tests do not remove incomplete invocations from the full report. Original report/receipt revalidate.

Review callsite-summary.json, actions.json.gz, ownership-gate.txt and negative-proof.json, plus acceptance.json and native receipt/build/capture artifacts.
Full residual lists remain intact; no allowlists, tolerances, reference rewriting
or runtime/gameplay changes. 83 focused + 25 importer guard + 19 probe tests
pass (127 distinct tests shared across these seven dimensions). Logs and final
integrity/handoff/contracts results live in [s77](../s77/README.md).

## Reproduction and limits

See [shared reproduction and evidence contract](../s77/REPRODUCTION.md) for exact
commands, paths, hashes and archive restoration. Each native run has its own
environment record; neither pixels nor observations are synthetic substitutes.
Capture completeness does not prove native parity. Source gaps, sampled lifetime
limits, clock/render-phase differences and full AS ownership remain explicit.
No geometry/image/ownership gap is waived by success in another dimension.

## Next discriminator

Record the tick-10 doAllAction exit and receiver lifecycle to distinguish
nonreturn from observer loss. Do not fabricate call_after/end. Callee bodies,
other branches, dynamic dispatch and Godot ownership remain unproven.
