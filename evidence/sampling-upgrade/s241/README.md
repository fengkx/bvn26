# s241 — Yulong attack: BitmapData and RGBA

Only `yulong__attack__neutral__ground__near`, unchanged s238 generated tape.
Base `a703c337`; branch `feat/sampling-yulong-attack-one-cell`.
`production_admitted=false`; `native_parity_proven=false`.

## Result

FAIL (exit 1): 61 native and 61 actual Godot viewport frames; 0/61 exact, 17595960 differing channels and 6839571 differing pixels. Maximum channel delta 255; no tolerance or image alignment.

See acceptance.json, retained build/raw trace and gate/negative proof. Rejected
captures remain untrimmed. No source obligation or threshold was removed.
123 distinct focused/import-guard/probe tests pass; logs are in s238.
Only the source-bound Sprite345 frame-1 PlaceObject2_14_31 call-site selection
and its test change. No gameplay/Godot runtime changes.

[Shared reproduction and limits](../s238/REPRODUCTION.md).
