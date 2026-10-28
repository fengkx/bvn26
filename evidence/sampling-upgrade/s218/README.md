# s218 — Sasuke attack: Global geometry

Only `sasuke__attack__neutral__ground__near`, unchanged generated s217 tape.
Base `02919820`; branch `feat/sampling-sasuke-attack-one-cell`.
`production_admitted=false`; `native_parity_proven=false`.

## Result

FAIL (exit 1): all four captures rejected events beyond the completion boundary. No receipt issued; zero admitted geometry samples. Final full trace contains 63 geometry_begin and 249 geometry_box events, including the rejected suffix. No Godot geometry comparison claimed.

The unchanged capture validator rejects the complete raw trace; no receipt is manufactured. The dimension CLI also exits 1 because the required receipt is absent. All failed attempts, including their full suffixes and build/environment identity, are retained.
See acceptance.json and negative-proof.json.

100 focused + 25 import-guard + 19 probe tests pass (144 distinct tests shared
across all seven dimensions). Logs and integrity/handoff/contracts are in s217.
The only probe change binds `game/fighter/Sasuke.swf` Sprite603/PlaceObject2_16_31.
Its exact source body and ambiguity rejection are tested using `scripts/fighter/Sasuke.json`.
Other forms and gameplay/runtime code are unchanged.

[Shared reproduction and limits](../s217/REPRODUCTION.md).
