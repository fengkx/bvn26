# s95 — Neji attack: DoAction entry coverage

One character PR, exactly `neji__attack__neutral__ground__near`, unchanged s91 tape.
Base `d96007053404dca228b326e0db2aa0656a77e627`; branch `feat/sampling-neji-attack-one-cell`.
`production_admitted=false`; `native_parity_proven=false`.

## Result

6,224 events, 61/61 root samples, 429 entries across 26 source blocks; fight window 57 entries / 14 blocks. Inventory 1,075 items, 464 instrumented blocks. Full gate exits 1: 438 unvisited and 611 uninstrumented.

Missing entry/sample and removed source obligation reject; original collection and receipt revalidate.

Review visited-summary.json, doaction.json.gz, ownership-gate.txt and negative-proof.json, plus acceptance.json and native receipt/build/capture artifacts.
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

