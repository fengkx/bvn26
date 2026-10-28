# s161 — Jiraiya attack: Native receipt

Only `jiraiya__attack__neutral__ground__near`, unchanged s161 generated tape.
Base `5e1b186c`; branch `feat/sampling-jiraiya-attack-one-cell`.
`production_admitted=false`; `native_parity_proven=false`.

## Result

5481 native events; receipt revalidation and Godot required-native selected execution pass (1/324). Full campaign rejects other missing receipts.

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

## Character review map

- [s162: Global geometry](../s162/README.md)
- [s163: Child display list and camera](../s163/README.md)
- [s164: BitmapData and RGBA](../s164/README.md)
- [s165: DoAction entry coverage](../s165/README.md)
- [s166: Clip-action handler coverage](../s166/README.md)
- [s167: Call-site and branch observations](../s167/README.md)
