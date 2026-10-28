# s210 — Rukia attack: Native receipt

Only `rukia__attack__neutral__ground__near`, unchanged s210 generated tape.
Base `02919820`; branch `feat/sampling-rukia-attack-one-cell`.
`production_admitted=false`; `native_parity_proven=false`.

## Result

5074 native events; receipt revalidation and Godot required-native selected execution pass (1/324). Full campaign rejects other missing receipts.

See acceptance.json and the original receipt/build/raw trace. Missing receipt,
sample, box, node, image, entry or marker negatives are retained in this folder's
gate-proof.json or negative-proof.json as appropriate. Original inputs are restored
and revalidated. No incomplete source inventory was removed to obtain a pass.

100 focused + 25 import guard + 19 probe tests pass (144 distinct tests shared
across all seven dimensions); logs and integrity/handoff/contracts are in s210.
No gameplay/runtime changes. Source-bound Rukia Sprite533/PlaceObject2_16_31
is the sole probe binding addition; source changes and ambiguous matches reject.

[Shared reproduction and limits](../s210/REPRODUCTION.md).
Capture completeness is not gameplay/pixel parity. Independent captures do not
prove clock/random/phase equivalence; exact AS ownership remains incomplete.

## Character review map

- [s211: Global geometry](../s211/README.md)
- [s212: Child display list and camera](../s212/README.md)
- [s213: BitmapData and RGBA](../s213/README.md)
- [s214: DoAction entry coverage](../s214/README.md)
- [s215: Clip-action handler coverage](../s215/README.md)
- [s216: Call-site and branch observations](../s216/README.md)

Rejected native attempts and the initial Godot import/capture failure are retained; see character-acceptance.json and REPRODUCTION.md. No trace suffix was removed.
