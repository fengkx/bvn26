# s177 — Lanran attack: Child display list and camera

Only `lanran__attack__neutral__ground__near`, unchanged s175 generated tape.
Base `5e1b186c`; branch `feat/sampling-lanran-attack-one-cell`.
`production_admitted=false`; `native_parity_proven=false`.

## Result

61/61 samples; 1531 nodes; full gate exits 1 with 167 source obligations: see source-gap-summary.json for exact reasons and paths. Dynamic masks/full camera remain unproven.

See acceptance.json and the original receipt/build/raw trace. Missing receipt,
sample, box, node, image, entry or marker negatives are retained in this folder's
gate-proof.json or negative-proof.json as appropriate. Original inputs are restored
and revalidated. No incomplete source inventory was removed to obtain a pass.

94 focused + 25 import guard + 19 probe tests pass (138 distinct tests shared
across all seven dimensions); logs and integrity/handoff/contracts are in s175.
No gameplay/runtime changes. Source-bound Lanran Sprite640/PlaceObject2_15_33
is the sole probe binding addition; source changes and ambiguous matches reject.

[Shared reproduction and limits](../s175/REPRODUCTION.md).
Capture completeness is not gameplay/pixel parity. Independent captures do not
prove clock/random/phase equivalence; exact AS ownership remains incomplete.
