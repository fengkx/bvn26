# s168 — Kakashi attack: Native receipt

Only `kakashi__attack__neutral__ground__near`, unchanged s168 generated tape.
Base `5e1b186c`; branch `feat/sampling-kakashi-attack-one-cell`.
`production_admitted=false`; `native_parity_proven=false`.

## Result

5121 native events; receipt revalidation and Godot required-native selected execution pass (1/324). Full campaign rejects other missing receipts.

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

## Character review map

- [s169: Global geometry](../s169/README.md)
- [s170: Child display list and camera](../s170/README.md)
- [s171: BitmapData and RGBA](../s171/README.md)
- [s172: DoAction entry coverage](../s172/README.md)
- [s173: Clip-action handler coverage](../s173/README.md)
- [s174: Call-site and branch observations](../s174/README.md)
