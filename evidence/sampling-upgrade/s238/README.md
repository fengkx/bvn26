# s238 — Yulong attack: Native receipt

Only `yulong__attack__neutral__ground__near`, unchanged s238 generated tape.
Base `a703c337`; branch `feat/sampling-yulong-attack-one-cell`.
`production_admitted=false`; `native_parity_proven=false`.

## Result

PASS (exit 0): 4742 native events, 122 actor observations. Required-native selected Godot execution passes (1/324); full campaign rejects missing receipts.

See acceptance.json, retained build/raw trace and gate/negative proof. Rejected
captures remain untrimmed. No source obligation or threshold was removed.
123 distinct focused/import-guard/probe tests pass; logs are in s238.
Only the source-bound Sprite345 frame-1 PlaceObject2_14_31 call-site selection
and its test change. No gameplay/Godot runtime changes.

[Shared reproduction and limits](../s238/REPRODUCTION.md).

## Character review map

- [s239: Global geometry](../s239/README.md)
- [s240: Child display list and camera](../s240/README.md)
- [s241: BitmapData and RGBA](../s241/README.md)
- [s242: DoAction entry coverage](../s242/README.md)
- [s243: Clip-action handler coverage](../s243/README.md)
- [s244: Call-site and branch observations](../s244/README.md)
