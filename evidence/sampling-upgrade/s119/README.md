# s119 — Juggo attack: Native receipt

Only `juggo__attack__neutral__ground__near`, unchanged s119 generated tape.
Base `6a92a7d7`; branch `feat/sampling-juggo-attack-one-cell`.
`production_admitted=false`; `native_parity_proven=false`.

## Result

5358 native events; receipt revalidation and Godot required-native selected execution pass (1/324). Full campaign rejects other missing receipts.

See acceptance.json and the original receipt/build/raw trace. Missing receipt,
sample, box, node, image, entry or marker negatives are retained in this folder's
gate-proof.json or negative-proof.json as appropriate. Original inputs are restored
and revalidated. No incomplete source inventory was removed to obtain a pass.

89 focused + 25 import guard + 19 probe tests pass (133 distinct tests shared
across all seven dimensions); logs and integrity/handoff/contracts are in s119.
No gameplay/runtime changes. Source-bound Juggo Sprite517/PlaceObject2_16_31
is the sole probe binding addition; source changes and ambiguous matches reject.

[Shared reproduction and limits](../s119/REPRODUCTION.md).
Capture completeness is not gameplay/pixel parity. Independent captures do not
prove clock/random/phase equivalence; exact AS ownership remains incomplete.

## Character review map

- [s120: Global geometry](../s120/README.md)
- [s121: Child display list and camera](../s121/README.md)
- [s122: BitmapData and RGBA](../s122/README.md)
- [s123: DoAction entry coverage](../s123/README.md)
- [s124: Clip-action handler coverage](../s124/README.md)
- [s125: Call-site and branch observations](../s125/README.md)
