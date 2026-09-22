# Byakuya frame333 GUI HUD rerender r06

This rerender uses the audited `DefineSprite_1815/frame_1` load mapping:

- P1: character 1782, depth 17, positive outer matrix, authored `bss1781`.
- P2: character 1774, depth 1, negative outer matrix, authored `bss1773`.

The P2 stock clip is transformed together with the source wrapper. This is
the first rerender after correcting the prior P1/P2 wrapper swap and the
separate counter transform. The image is focused Godot evidence only; the
qt color/frame correspondence against source 333 remains open.

Capture command:

```text
/private/tmp/godot-4.7.2/Godot.app/Contents/MacOS/Godot --path godot -s res://tests/byakuya_visual_capture.gd -- 333 /private/tmp/byakuya-godot-333-gui-r06
```
