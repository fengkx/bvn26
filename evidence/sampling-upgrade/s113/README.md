# s113 — Jianba attack: Global geometry

Only `jianba__attack__neutral__ground__near`, unchanged s112 generated tape.
Base `fe8d14fb`; branch `feat/sampling-jianba-attack-one-cell`.
`production_admitted=false`; `native_parity_proven=false`.

## Result

61/61 samples; {'hurt': 238, 'attack': 2} box records; 9 sampled instances. Native gate passes; Godot geometry comparison remains open.

See acceptance.json and the original receipt/build/raw trace. Missing receipt,
sample, box, node, image, entry or marker negatives are retained in this folder's
gate-proof.json or negative-proof.json as appropriate. Original inputs are restored
and revalidated. No incomplete source inventory was removed to obtain a pass.

88 focused + 25 import guard + 19 probe tests pass (132 distinct tests shared
across all seven dimensions); logs and integrity/handoff/contracts are in s112.
No gameplay/runtime changes. Source-bound Jianba Sprite514/PlaceObject2_13_31
is the sole probe binding addition; source changes and ambiguous matches reject.

[Shared reproduction and limits](../s112/REPRODUCTION.md).
Capture completeness is not gameplay/pixel parity. Independent captures do not
prove clock/random/phase equivalence; exact AS ownership remains incomplete.
