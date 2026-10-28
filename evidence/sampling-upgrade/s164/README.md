# s164 — Jiraiya attack: BitmapData and RGBA

Only `jiraiya__attack__neutral__ground__near`, unchanged s161 generated tape.
Base `5e1b186c`; branch `feat/sampling-jiraiya-attack-one-cell`.
`production_admitted=false`; `native_parity_proven=false`.

## Result

61 native and 61 actual Godot images, 600x400 opaque RGBA. Strict gate exits 1: 0/61 exact; 18612303 differing channels, 7163226 differing pixels; max channel delta 255. No alignment, cropping, reference rewriting or tolerance.

See acceptance.json and the original receipt/build/raw trace. Missing receipt,
sample, box, node, image, entry or marker negatives are retained in this folder's
gate-proof.json or negative-proof.json as appropriate. Original inputs are restored
and revalidated. No incomplete source inventory was removed to obtain a pass.

94 focused + 25 import guard + 19 probe tests pass (138 distinct tests shared
across all seven dimensions); logs and integrity/handoff/contracts are in s161.
No gameplay/runtime changes. Source-bound Jiraiya Sprite342/PlaceObject2_11_33
is the sole probe binding addition; source changes and ambiguous matches reject.

[Shared reproduction and limits](../s161/REPRODUCTION.md).
Capture completeness is not gameplay/pixel parity. Independent captures do not
prove clock/random/phase equivalence; exact AS ownership remains incomplete.

Tick 13 visual review confirms different timer text (native 49, Godot 59);
wall-clock/render-phase equivalence remains unproven. No time alignment or
reference correction is applied.
