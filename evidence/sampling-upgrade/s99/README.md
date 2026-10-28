# s99 — Sakura attack: Global geometry

Only `sakura__attack__neutral__ground__near`, unchanged s98 generated tape.
Base `39c2c41a`; branch `feat/sampling-sakura-attack-one-cell`.
`production_admitted=false`; `native_parity_proven=false`.

## Result

61/61 samples; {'hurt': 238, 'attack': 2} box records; 9 sampled instances. Native gate passes; Godot geometry comparison remains open.

See acceptance.json and the original receipt/build/raw trace. Missing receipt,
sample, box, node, image, entry or marker negatives are retained in this folder's
gate-proof.json or negative-proof.json as appropriate. Original inputs are restored
and revalidated. No incomplete source inventory was removed to obtain a pass.

86 focused + 25 import guard + 19 probe tests pass (130 distinct tests shared
across all seven dimensions); logs and integrity/handoff/contracts are in s98.
No gameplay/runtime changes. Source-bound Sakura Sprite630/PlaceObject2_11_31
is the sole probe binding addition; source changes and ambiguous matches reject.

[Shared reproduction and limits](../s98/REPRODUCTION.md).
Capture completeness is not gameplay/pixel parity. Independent captures do not
prove clock/random/phase equivalence; exact AS ownership remains incomplete.
