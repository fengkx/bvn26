# s196 — Pain attack: Native receipt

Only `pain__attack__neutral__ground__near`, unchanged s196 generated tape.
Base `02919820`; branch `feat/sampling-pain-attack-one-cell`.
`production_admitted=false`; `native_parity_proven=false`.

## Result

5524 native events; receipt revalidation and Godot required-native selected execution pass (1/324). Full campaign rejects other missing receipts.

See acceptance.json and the original receipt/build/raw trace. Missing receipt,
sample, box, node, image, entry or marker negatives are retained in this folder's
gate-proof.json or negative-proof.json as appropriate. Original inputs are restored
and revalidated. No incomplete source inventory was removed to obtain a pass.

100 focused + 25 import guard + 19 probe tests pass (144 distinct tests shared
across all seven dimensions); logs and integrity/handoff/contracts are in s196.
No gameplay/runtime changes. Source-bound Pain Sprite573/PlaceObject2_18_33
is the sole probe binding addition; source changes and ambiguous matches reject.

[Shared reproduction and limits](../s196/REPRODUCTION.md).
Capture completeness is not gameplay/pixel parity. Independent captures do not
prove clock/random/phase equivalence; exact AS ownership remains incomplete.

## Character review map

- [s197: Global geometry](../s197/README.md)
- [s198: Child display list and camera](../s198/README.md)
- [s199: BitmapData and RGBA](../s199/README.md)
- [s200: DoAction entry coverage](../s200/README.md)
- [s201: Clip-action handler coverage](../s201/README.md)
- [s202: Call-site and branch observations](../s202/README.md)

Initial s197 geometry and s198 display captures failed the completion-boundary gate and are retained in full. Accepted captures use build-r02. Python dependency and Godot import preparation failures are also retained. See the reproduction document.
