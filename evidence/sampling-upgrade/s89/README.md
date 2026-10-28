# s89 — Lee attack: Clip-action handler entries

One character PR, exactly `lee__attack__neutral__ground__near`, unchanged s84 tape.
Base `f378ca6493c252aabaf1619cfb3f7e179cdac298`; branch `feat/sampling-lee-attack-one-cell`.
`production_admitted=false`; `native_parity_proven=false`.

## Result

8,708 events, 61/61 samples, 2,814 clip entries across 11 handlers (351 fight-window entries); 413 DoAction entries / 26 blocks. Inventory 1,099 items, 684 instrumented. Full gate exits 1: 647 unvisited (461 blocks + 186 handlers), 415 uninstrumented.

Missing clip event/sample and deleted source obligations reject; original stream/receipt revalidate.

Review clipaction-summary.json, visited-summary.json, doaction.json.gz and negative-proof.json, plus acceptance.json and native receipt/build/capture artifacts.
Full residual lists remain intact; no allowlists, tolerances, reference rewriting
or runtime/gameplay changes. 84 focused + 25 importer guard + 19 probe tests
pass (128 distinct tests shared across these seven dimensions). Logs and final
integrity/handoff/contracts results live in [s84](../s84/README.md).

## Reproduction and limits

See [shared reproduction and evidence contract](../s84/REPRODUCTION.md) for exact
commands, paths, hashes and archive restoration. Each native run has its own
environment record; neither pixels nor observations are synthetic substitutes.
Capture completeness does not prove native parity. Source gaps, sampled lifetime
limits, clock/render-phase differences and full AS ownership remain explicit.
No geometry/image/ownership gap is waived by success in another dimension.

