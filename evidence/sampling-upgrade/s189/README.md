# s189 — Orochimaru attack: Native receipt

Only `orochimaru__attack__neutral__ground__near`, unchanged s189 generated tape.
Base `146dada0`; branch `feat/sampling-orochimaru-attack-one-cell`.
`production_admitted=false`; `native_parity_proven=false`.

## Result

5543 native events; receipt revalidation and Godot required-native selected execution pass (1/324). Full campaign rejects other missing receipts.

See acceptance.json and the original receipt/build/raw trace. Missing receipt,
sample, box, node, image, entry or marker negatives are retained in this folder's
gate-proof.json or negative-proof.json as appropriate. Original inputs are restored
and revalidated. No incomplete source inventory was removed to obtain a pass.

98 focused + 25 import guard + 19 probe tests pass (142 distinct tests shared
across all seven dimensions); logs and integrity/handoff/contracts are in s189.
No gameplay/runtime changes. Source-bound Orochimaru Sprite541/PlaceObject2_16_31
is the sole probe binding addition; source changes and ambiguous matches reject.

[Shared reproduction and limits](../s189/REPRODUCTION.md).
Capture completeness is not gameplay/pixel parity. Independent captures do not
prove clock/random/phase equivalence; exact AS ownership remains incomplete.

## Character review map

- [s190: Global geometry](../s190/README.md)
- [s191: Child display list and camera](../s191/README.md)
- [s192: BitmapData and RGBA](../s192/README.md)
- [s193: DoAction entry coverage](../s193/README.md)
- [s194: Clip-action handler coverage](../s194/README.md)
- [s195: Call-site and branch observations](../s195/README.md)

The initial s191 completion-boundary failure is retained in full; the accepted retry uses build-r02. See the shared reproduction document.
