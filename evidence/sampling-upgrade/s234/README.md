# s234 — Yijiao attack: BitmapData and RGBA

Only `yijiao__attack__neutral__ground__near`, unchanged s231 generated tape.
Base `70951935`; branch `feat/sampling-yijiao-attack-one-cell`.
`production_admitted=false`; `native_parity_proven=false`.

## Result

FAIL (exit 1): 61 native and 61 actual Godot viewport frames; 0/61 exact, 17818352 differing channels and 6910686 differing pixels. Maximum channel delta 255; no tolerance or image alignment.

See acceptance.json, retained build/raw trace and gate/negative proof. Rejected
captures remain untrimmed. No source obligation or threshold was removed.
148 distinct focused/import-guard/probe tests pass; logs are in s231.
Only the source-bound Sprite455 frame-1 PlaceObject2_18_31 call-site selection
and its test change. No gameplay/Godot runtime changes.

[Shared reproduction and limits](../s231/REPRODUCTION.md).

Visual inspection of retained tick 13 shows native countdown 47 versus Godot 59, with visible edge-rasterization differences. These are observations, not proven causal attribution; clock/render-phase equivalence remains open.
