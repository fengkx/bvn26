# s221 — Sasuke attack: DoAction entry coverage

Only `sasuke__attack__neutral__ground__near`, unchanged generated s217 tape.
Base `02919820`; branch `feat/sampling-sasuke-attack-one-cell`.
`production_admitted=false`; `native_parity_proven=false`.

## Result

FAIL (exit 1): receipt and 61 samples pass; 428 entries / 30 visited blocks. Full coverage retains 596 unvisited and 662 uninstrumented source items.

Receipt, original build/raw trace and missing-data negative proofs are retained.
See acceptance.json and negative-proof.json.

100 focused + 25 import-guard + 19 probe tests pass (144 distinct tests shared
across all seven dimensions). Logs and integrity/handoff/contracts are in s217.
The only probe change binds `game/fighter/Sasuke.swf` Sprite603/PlaceObject2_16_31.
Its exact source body and ambiguity rejection are tested using `scripts/fighter/Sasuke.json`.
Other forms and gameplay/runtime code are unchanged.

[Shared reproduction and limits](../s217/REPRODUCTION.md).
