# s110 — Yin attack: Clip-action handler coverage

Only `yin__attack__neutral__ground__near`, unchanged s105 generated tape.
Base `c50a6400`; branch `feat/sampling-yin-attack-one-cell`.
`production_admitted=false`; `native_parity_proven=false`.

## Result

61/61 samples; 2759 clip entries / 13 handlers. Full gate exits 1: 601 unvisited, 415 uninstrumented.

See acceptance.json and the original receipt/build/raw trace. Missing receipt,
sample, box, node, image, entry or marker negatives are retained in this folder's
gate-proof.json or negative-proof.json as appropriate. Original inputs are restored
and revalidated. No incomplete source inventory was removed to obtain a pass.

87 focused + 25 import guard + 19 probe tests pass (131 distinct tests shared
across all seven dimensions); logs and integrity/handoff/contracts are in s105.
No gameplay/runtime changes. Source-bound Yin Sprite435/PlaceObject2_16_31
is the sole probe binding addition; source changes and ambiguous matches reject.

[Shared reproduction and limits](../s105/REPRODUCTION.md).
Capture completeness is not gameplay/pixel parity. Independent captures do not
prove clock/random/phase equivalence; exact AS ownership remains incomplete.
