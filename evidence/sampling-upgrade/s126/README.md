# s126 — Konan attack: Native receipt

Only `konan__attack__neutral__ground__near`, unchanged s126 generated tape.
Base `c567075b`; branch `feat/sampling-konan-attack-one-cell`.
`production_admitted=false`; `native_parity_proven=false`.

## Result

5120 native events; receipt revalidation and Godot required-native selected execution pass (1/324). Full campaign rejects other missing receipts.

See acceptance.json and the original receipt/build/raw trace. Missing receipt,
sample, box, node, image, entry or marker negatives are retained in this folder's
gate-proof.json or negative-proof.json as appropriate. Original inputs are restored
and revalidated. No incomplete source inventory was removed to obtain a pass.

90 focused + 25 import guard + 19 probe tests pass (134 distinct tests shared
across all seven dimensions); logs and integrity/handoff/contracts are in s126.
No gameplay/runtime changes. Source-bound Konan Sprite563/PlaceObject2_16_32
is the sole probe binding addition; source changes and ambiguous matches reject.

[Shared reproduction and limits](../s126/REPRODUCTION.md).
Capture completeness is not gameplay/pixel parity. Independent captures do not
prove clock/random/phase equivalence; exact AS ownership remains incomplete.

## Character review map

- [s127: Global geometry](../s127/README.md)
- [s128: Child display list and camera](../s128/README.md)
- [s129: BitmapData and RGBA](../s129/README.md)
- [s130: DoAction entry coverage](../s130/README.md)
- [s131: Clip-action handler coverage](../s131/README.md)
- [s132: Call-site and branch observations](../s132/README.md)
