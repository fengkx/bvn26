# s217 — Sasuke attack: Native receipt

Only `sasuke__attack__neutral__ground__near`, unchanged generated s217 tape.
Base `02919820`; branch `feat/sampling-sasuke-attack-one-cell`.
`production_admitted=false`; `native_parity_proven=false`.

## Result

PASS (exit 0): 5404 native events, 122 actor observations; required-native selected Godot execution passes (1/324). Full campaign rejects missing receipts. This is not a parity result.

Receipt, original build/raw trace and missing-data negative proofs are retained.
See acceptance.json and gate-proof.json.

100 focused + 25 import-guard + 19 probe tests pass (144 distinct tests shared
across all seven dimensions). Logs and integrity/handoff/contracts are in s217.
The only probe change binds `game/fighter/Sasuke.swf` Sprite603/PlaceObject2_16_31.
Its exact source body and ambiguity rejection are tested using `scripts/fighter/Sasuke.json`.
Other forms and gameplay/runtime code are unchanged.

[Shared reproduction and limits](../s217/REPRODUCTION.md).

## Character review map

- [s218: Global geometry](../s218/README.md)
- [s219: Child display list and camera](../s219/README.md)
- [s220: BitmapData and RGBA](../s220/README.md)
- [s221: DoAction entry coverage](../s221/README.md)
- [s222: Clip-action handler coverage](../s222/README.md)
- [s223: Call-site and branch observations](../s223/README.md)
