# s244 — Yulong attack: Call-site and branch observations

Only `yulong__attack__neutral__ground__near`, unchanged s238 generated tape.
Base `a703c337`; branch `feat/sampling-yulong-attack-one-cell`.
`production_admitted=false`; `native_parity_proven=false`.

## Result

FAIL (exit 1): 61/61 samples; 438 complete invocations (36 true / 402 false), 1 incomplete. Full AS/callee/Godot ownership remains unproven.

See acceptance.json, retained build/raw trace and gate/negative proof. Rejected
captures remain untrimmed. No source obligation or threshold was removed.
123 distinct focused/import-guard/probe tests pass; logs are in s238.
Only the source-bound Sprite345 frame-1 PlaceObject2_14_31 call-site selection
and its test change. No gameplay/Godot runtime changes.

[Shared reproduction and limits](../s238/REPRODUCTION.md).
