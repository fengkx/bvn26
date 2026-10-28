# s178 — Lanran attack: BitmapData and RGBA

Only `lanran__attack__neutral__ground__near`, unchanged s175 generated tape.
Base `5e1b186c`; branch `feat/sampling-lanran-attack-one-cell`.
`production_admitted=false`; `native_parity_proven=false`.

## Result

61 native and 61 actual Godot images, 600x400 opaque RGBA. Strict gate exits 1: 0/61 exact; 17599336 differing channels, 6833010 differing pixels; max channel delta 255. No alignment, cropping, reference rewriting or tolerance.

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

Visual inspection of the retained tick-13 pair shows native HUD countdown 47 versus Godot 59 and different character edge rasterization. This is an observation, not a causal attribution or permission to align/crop images. External-clock and rendering-phase equivalence remain unresolved.
