# s231 — Yijiao attack: Native receipt

Only `yijiao__attack__neutral__ground__near`, unchanged s231 generated tape.
Base `70951935`; branch `feat/sampling-yijiao-attack-one-cell`.
`production_admitted=false`; `native_parity_proven=false`.

## Result

FAIL (exit 1): native evidence: events beyond completion boundary. No receipt issued; zero admitted samples. Full raw trace and build retained.

See acceptance.json, retained build/raw trace and gate/negative proof. Rejected
captures remain untrimmed. No source obligation or threshold was removed.
148 distinct focused/import-guard/probe tests pass; logs are in s231.
Only the source-bound Sprite455 frame-1 PlaceObject2_18_31 call-site selection
and its test change. No gameplay/Godot runtime changes.

[Shared reproduction and limits](../s231/REPRODUCTION.md).

## Character review map

- [s232: Global geometry](../s232/README.md)
- [s233: Child display list and camera](../s233/README.md)
- [s234: BitmapData and RGBA](../s234/README.md)
- [s235: DoAction entry coverage](../s235/README.md)
- [s236: Clip-action handler coverage](../s236/README.md)
- [s237: Call-site and branch observations](../s237/README.md)
