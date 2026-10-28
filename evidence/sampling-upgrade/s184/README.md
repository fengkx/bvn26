# s184 — Minren attack: Child display list and camera

Only `minren__attack__neutral__ground__near`, unchanged s182 generated tape.
Base `146dada0`; branch `feat/sampling-minren-attack-one-cell`.
`production_admitted=false`; `native_parity_proven=false`.

## Result

61/61 samples; 1539 nodes; full gate exits 1 with 167 source obligations: see source-gap-summary.json for exact reasons and paths. Dynamic masks/full camera remain unproven.

See acceptance.json and the original receipt/build/raw trace. Missing receipt,
sample, box, node, image, entry or marker negatives are retained in this folder's
gate-proof.json or negative-proof.json as appropriate. Original inputs are restored
and revalidated. No incomplete source inventory was removed to obtain a pass.

98 focused + 25 import guard + 19 probe tests pass (142 distinct tests shared
across all seven dimensions); logs and integrity/handoff/contracts are in s182.
No gameplay/runtime changes. Source-bound Minren Sprite764/PlaceObject2_16_31
is the sole probe binding addition; source changes and ambiguous matches reject.

[Shared reproduction and limits](../s182/REPRODUCTION.md).
Capture completeness is not gameplay/pixel parity. Independent captures do not
prove clock/random/phase equivalence; exact AS ownership remains incomplete.
