# s148 — Gaara attack: Global geometry

Only `gaara__attack__neutral__ground__near`, unchanged s147 generated tape.
Base `de0bbe51`; branch `feat/sampling-gaara-attack-one-cell`.
`production_admitted=false`; `native_parity_proven=false`.

## Result

61/61 samples; {'hurt': 238, 'attack': 2} box records; 9 sampled instances. Native gate passes; Godot geometry comparison remains open.

See acceptance.json and the original receipt/build/raw trace. Missing receipt,
sample, box, node, image, entry or marker negatives are retained in this folder's
gate-proof.json or negative-proof.json as appropriate. Original inputs are restored
and revalidated. No incomplete source inventory was removed to obtain a pass.

93 focused + 25 import guard + 19 probe tests pass (137 distinct tests shared
across all seven dimensions); logs and integrity/handoff/contracts are in s147.
No gameplay/runtime changes. Source-bound Gaara Sprite673/PlaceObject2_20_31
is the sole probe binding addition; source changes and ambiguous matches reject.

[Shared reproduction and limits](../s147/REPRODUCTION.md).
Capture completeness is not gameplay/pixel parity. Independent captures do not
prove clock/random/phase equivalence; exact AS ownership remains incomplete.
