# s93 — Neji attack: Child display list and camera

One character PR, exactly `neji__attack__neutral__ground__near`, unchanged s91 tape.
Base `d96007053404dca228b326e0db2aa0656a77e627`; branch `feat/sampling-neji-attack-one-cell`.
`production_admitted=false`; `native_parity_proven=false`.

## Result

9,094 events, 61/61 samples, 1,505 MovieClip records, zero filter entries. Receipt/structure pass; full gate exits 1 with 122 AImain source-frame obligations (61 per actor).

Missing sample and actor node reject; restored samples/receipt revalidate. Dynamic mask remains unproven even if joins clear.

Review display.json.gz, source-gap-summary.json, source-exports.json and Neji source XML archive, plus acceptance.json and native receipt/build/capture artifacts.
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

