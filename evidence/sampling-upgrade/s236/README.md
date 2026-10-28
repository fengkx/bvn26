# s236 — Yijiao attack: Clip-action handler coverage

Only `yijiao__attack__neutral__ground__near`, unchanged s231 generated tape.
Base `70951935`; branch `feat/sampling-yijiao-attack-one-cell`.
`production_admitted=false`; `native_parity_proven=false`.

## Result

FAIL (exit 1): 61/61 samples; 2844 clip entries / 13 handlers; 626 unvisited and 416 uninstrumented obligations.

See acceptance.json, retained build/raw trace and gate/negative proof. Rejected
captures remain untrimmed. No source obligation or threshold was removed.
148 distinct focused/import-guard/probe tests pass; logs are in s231.
Only the source-bound Sprite455 frame-1 PlaceObject2_18_31 call-site selection
and its test change. No gameplay/Godot runtime changes.

[Shared reproduction and limits](../s231/REPRODUCTION.md).
