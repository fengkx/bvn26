# s82 — Renji attack: Clip-action handler entries

One character PR, exactly `renji__attack__neutral__ground__near`, unchanged s77 tape.
Base `9ce1db68421d91f3ef0433d41d59b324f92344f7`; branch `feat/sampling-renji-attack-one-cell`.
`production_admitted=false`; `native_parity_proven=false`.

## Result

8,373 events, 61/61 samples, 2,802 clip entries across 13 handlers (345 fight-window entries); 413 DoAction entries / 29 blocks. Inventory 1,067 items, 650 instrumented. Full gate exits 1: 608 unvisited (444 blocks + 164 handlers), 417 uninstrumented.

Missing clip event/sample and deleted source obligations reject; original stream/receipt revalidate.

Review clipaction-summary.json, visited-summary.json, doaction.json.gz and negative-proof.json, plus acceptance.json and native receipt/build/capture artifacts.
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

