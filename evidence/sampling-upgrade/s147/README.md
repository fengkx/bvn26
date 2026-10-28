# s147 — Gaara attack: Native receipt

Only `gaara__attack__neutral__ground__near`, unchanged s147 generated tape.
Base `de0bbe51`; branch `feat/sampling-gaara-attack-one-cell`.
`production_admitted=false`; `native_parity_proven=false`.

## Result

5615 native events; receipt revalidation and Godot required-native selected execution pass (1/324). Full campaign rejects other missing receipts.

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

## Character review map

- [s148: Global geometry](../s148/README.md)
- [s149: Child display list and camera](../s149/README.md)
- [s150: BitmapData and RGBA](../s150/README.md)
- [s151: DoAction entry coverage](../s151/README.md)
- [s152: Clip-action handler coverage](../s152/README.md)
- [s153: Call-site and branch observations](../s153/README.md)
