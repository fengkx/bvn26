# s172 — Kakashi attack: DoAction entry coverage

Only `kakashi__attack__neutral__ground__near`, unchanged s168 generated tape.
Base `5e1b186c`; branch `feat/sampling-kakashi-attack-one-cell`.
`production_admitted=false`; `native_parity_proven=false`.

## Result

61/61 samples; 383 entries / 30 blocks. Full gate exits 1: 453 unvisited, 609 uninstrumented.

See acceptance.json and the original receipt/build/raw trace. Missing receipt,
sample, box, node, image, entry or marker negatives are retained in this folder's
gate-proof.json or negative-proof.json as appropriate. Original inputs are restored
and revalidated. No incomplete source inventory was removed to obtain a pass.

94 focused + 25 import guard + 19 probe tests pass (138 distinct tests shared
across all seven dimensions); logs and integrity/handoff/contracts are in s168.
No gameplay/runtime changes. Source-bound Kakashi Sprite710/PlaceObject2_9_31
is the sole probe binding addition; source changes and ambiguous matches reject. Exact authored Kakashi path casing is retained.

[Shared reproduction and limits](../s168/REPRODUCTION.md).
Capture completeness is not gameplay/pixel parity. Independent captures do not
prove clock/random/phase equivalence; exact AS ownership remains incomplete.
