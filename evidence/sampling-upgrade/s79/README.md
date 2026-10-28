# s79 — Renji attack: Child display list and camera

One character PR, exactly `renji__attack__neutral__ground__near`, unchanged s77 tape.
Base `9ce1db68421d91f3ef0433d41d59b324f92344f7`; branch `feat/sampling-renji-attack-one-cell`.
`production_admitted=false`; `native_parity_proven=false`.

## Result

8,334 events, 61/61 samples, 1,527 MovieClip records, zero filter entries. Receipt/structure pass; full gate exits 1 with 167 obligations: 122 AImain source-frame gaps and 45 xgmc0 runtime-symbol gaps.

Missing sample and actor node reject; restored samples/receipt revalidate. Dynamic mask remains unproven even if joins clear.

Review display.json.gz, source-gap-summary.json, source-exports.json and Renji source XML archive, plus acceptance.json and native receipt/build/capture artifacts.
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

