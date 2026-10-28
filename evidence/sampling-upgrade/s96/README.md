# s96 — Neji attack: Clip-action handler entries

One character PR, exactly `neji__attack__neutral__ground__near`, unchanged s91 tape.
Base `d96007053404dca228b326e0db2aa0656a77e627`; branch `feat/sampling-neji-attack-one-cell`.
`production_admitted=false`; `native_parity_proven=false`.

## Result

9,461 events, 61/61 samples, 3,045 clip entries across 11 handlers (350 fight-window entries); 447 DoAction entries / 26 blocks. Inventory 1,075 items, 660 instrumented. Full gate exits 1: 623 unvisited, 415 uninstrumented.

Missing clip event/sample and deleted source obligations reject; original stream/receipt revalidate.

Review clipaction-summary.json, visited-summary.json, doaction.json.gz and negative-proof.json, plus acceptance.json and native receipt/build/capture artifacts.
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

