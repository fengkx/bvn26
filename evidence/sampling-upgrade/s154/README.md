# s154 — Itachi attack: Native receipt

Only `itachi__attack__neutral__ground__near`, unchanged s154 generated tape.
Base `5e1b186c`; branch `feat/sampling-itachi-attack-one-cell`.
`production_admitted=false`; `native_parity_proven=false`.

## Result

5179 native events; receipt revalidation and Godot required-native selected execution pass (1/324). Full campaign rejects other missing receipts.

See acceptance.json and the original receipt/build/raw trace. Missing receipt,
sample, box, node, image, entry or marker negatives are retained in this folder's
gate-proof.json or negative-proof.json as appropriate. Original inputs are restored
and revalidated. No incomplete source inventory was removed to obtain a pass.

94 focused + 25 import guard + 19 probe tests pass (138 distinct tests shared
across all seven dimensions); logs and integrity/handoff/contracts are in s154.
No gameplay/runtime changes. Source-bound Itachi Sprite294/PlaceObject2_11_33
is the sole probe binding addition; source changes and ambiguous matches reject.

[Shared reproduction and limits](../s154/REPRODUCTION.md).
Capture completeness is not gameplay/pixel parity. Independent captures do not
prove clock/random/phase equivalence; exact AS ownership remains incomplete.

## Character review map

- [s155: Global geometry](../s155/README.md)
- [s156: Child display list and camera](../s156/README.md)
- [s157: BitmapData and RGBA](../s157/README.md)
- [s158: DoAction entry coverage](../s158/README.md)
- [s159: Clip-action handler coverage](../s159/README.md)
- [s160: Call-site and branch observations](../s160/README.md)
