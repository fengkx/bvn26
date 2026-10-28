# s220 — Sasuke attack: BitmapData and RGBA

Only `sasuke__attack__neutral__ground__near`, unchanged generated s217 tape.
Base `02919820`; branch `feat/sampling-sasuke-attack-one-cell`.
`production_admitted=false`; `native_parity_proven=false`.

## Result

FAIL (exit 1): 61 native and 61 actual Godot images, 600x400 opaque RGBA; 0/61 exact, 17732741 differing channels, 6864492 differing pixels, max channel delta 255. No alignment, cropping or tolerance.

Receipt, original build/raw trace and missing-data negative proofs are retained.
See acceptance.json and negative-proof.json.

100 focused + 25 import-guard + 19 probe tests pass (144 distinct tests shared
across all seven dimensions). Logs and integrity/handoff/contracts are in s217.
The only probe change binds `game/fighter/Sasuke.swf` Sprite603/PlaceObject2_16_31.
Its exact source body and ambiguity rejection are tested using `scripts/fighter/Sasuke.json`.
Other forms and gameplay/runtime code are unchanged.

[Shared reproduction and limits](../s217/REPRODUCTION.md).
