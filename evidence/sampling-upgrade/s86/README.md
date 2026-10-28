# s86 — Lee attack: Child display list and camera

One character PR, exactly `lee__attack__neutral__ground__near`, unchanged s84 tape.
Base `f378ca6493c252aabaf1619cfb3f7e179cdac298`; branch `feat/sampling-lee-attack-one-cell`.
`production_admitted=false`; `native_parity_proven=false`.

## Result

9,090 events, 61/61 samples, 1,506 MovieClip records, zero filter entries. Receipt/structure pass; full gate exits 1 with 122 AImain source-frame obligations (61 per actor).

Missing sample and actor node reject; restored samples/receipt revalidate. Dynamic mask remains unproven even if joins clear.

Review display.json.gz, source-gap-summary.json, source-exports.json and Lee source XML archive, plus acceptance.json and native receipt/build/capture artifacts.
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

