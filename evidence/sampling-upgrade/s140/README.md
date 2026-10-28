# s140 — Daitu attack: Native receipt

Only `daitu__attack__neutral__ground__near`, unchanged s140 generated tape.
Base `9986ce10`; branch `feat/sampling-daitu-attack-one-cell`.
`production_admitted=false`; `native_parity_proven=false`.

## Result

5188 native events; receipt revalidation and Godot required-native selected execution pass (1/324). Full campaign rejects other missing receipts.

See acceptance.json and the original receipt/build/raw trace. Missing receipt,
sample, box, node, image, entry or marker negatives are retained in this folder's
gate-proof.json or negative-proof.json as appropriate. Original inputs are restored
and revalidated. No incomplete source inventory was removed to obtain a pass.

92 focused + 25 import guard + 19 probe tests pass (136 distinct tests shared
across all seven dimensions); logs and integrity/handoff/contracts are in s140.
No gameplay/runtime changes. Source-bound Daitu Sprite458/PlaceObject2_21_31
is the sole probe binding addition; source changes and ambiguous matches reject.

[Shared reproduction and limits](../s140/REPRODUCTION.md).
Capture completeness is not gameplay/pixel parity. Independent captures do not
prove clock/random/phase equivalence; exact AS ownership remains incomplete.

## Character review map

- [s141: Global geometry](../s141/README.md)
- [s142: Child display list and camera](../s142/README.md)
- [s143: BitmapData and RGBA](../s143/README.md)
- [s144: DoAction entry coverage](../s144/README.md)
- [s145: Clip-action handler coverage](../s145/README.md)
- [s146: Call-site and branch observations](../s146/README.md)
