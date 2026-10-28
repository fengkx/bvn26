# s175 — Lanran attack: Native receipt

Only `lanran__attack__neutral__ground__near`, unchanged s175 generated tape.
Base `5e1b186c`; branch `feat/sampling-lanran-attack-one-cell`.
`production_admitted=false`; `native_parity_proven=false`.

## Result

5570 native events; receipt revalidation and Godot required-native selected execution pass (1/324). Full campaign rejects other missing receipts.

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

## Character review map

- [s176: Global geometry](../s176/README.md)
- [s177: Child display list and camera](../s177/README.md)
- [s178: BitmapData and RGBA](../s178/README.md)
- [s179: DoAction entry coverage](../s179/README.md)
- [s180: Clip-action handler coverage](../s180/README.md)
- [s181: Call-site and branch observations](../s181/README.md)

The first two s177 traces were rejected for events beyond the completion boundary; their full raw logs and builds remain in s177. A fresh r03 run supplies the accepted receipt. Initial Godot cache/import failures remain in s175; subsequent execution/capture uses the populated cache.
