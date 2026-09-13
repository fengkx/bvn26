# Sakura and Ino rendered key frames r01

Godot 4.7.2 rendered these six source-referenced display-list frames in a non-headless macOS OpenGL/Metal compatibility session. Fighter captures use Sakura source sprite 630 at frames 1 (站立), 10 (走), and 20 (瞬步). Helper captures activate the selected `松本`/Jinye runtime instance at frame 2, then inspect frames 2, 20, and 38. The frame-38 source timeline contains StartSound IDs 49 and 50; the helper visual probe disables timeline sound playback, so this packet is visual evidence only.

Original source references were exported directly from the locked SWFs with JPEXS FFDec 26.2.1: `sakura/flash-sprite-630-frame-1.png` is DefineSprite_630 frame 1 (exported at 337×424); `jinye/flash-shape-2-frame-2.png` is source DefineShape 2, the sole placed object in Jinye root frame 2 (30×55). The source files are Sakura `game/fighter/Sakura.swf`, SHA-256 `7d5d060ea9949f54535f801abd3ebdb23de5e7fc7cd5644186f7d805a47ba544`, and Jinye `game/fighter/fz/jinye.swf`, SHA-256 `03736bfd2ef7e9b79f958971fc7192ea641653039212e29793ed291c56bfa62a`. The Godot frame images and FFDec references depict the same source-defined frame content under different canvas/placement conditions: FFDec exports the isolated source sprite/shape bounds; Godot captures the scene viewport at the probe's explicit actor position. The matched visible silhouettes and poses are a finite content check, not a pixel-aligned original Flash screenshot or full visual-parity claim.

The source frames were selected directly for image inspection; this probe does not claim natural-timeline transition or combat presentation parity. Sakura's frames have no StartSound tags, and sound output was set to the Dummy driver. Each trace records the display server and screenshot paths. PNG SHA-256 values:

| Character | Frame | SHA-256 |
|---|---:|---|
| Sakura | 1 | `f1775c09d6611f966b5603dead8b8e1eb328f316f3b5e9a21852054663f1584e` |
| Sakura | 10 | `62d2f91db1bdfd5c8ca6585ed7e11b9614f52b82a423f6d8344c08615e8759b8` |
| Sakura | 20 | `ce861aabb10eb0f8454db5c1c3ee465b8f7f668637ea102a32effb4ebeab24ce` |
| Jinye | 2 | `b602b74d269917547ab52ec19b7dad40ba0e3e26e79e6c027dcab5e5a2a41a34` |
| Jinye | 20 | `c1cf1cf74881dacb237f9c6672a7e5878ee488f21514ca2e00c573b388596a0d` |
| Jinye | 38 | `abc51a3b9437548dd0e9fd9f5f79a6ed6b1b623460ecb30f3a5ffa48596d7e1a` |
| Sakura source FFDec reference | 1 | `019d6d570a7feeba38fbb49dcd9f5db736547e4e346f898c57d497f68afbdf0f` |
| Jinye source FFDec reference | 2 | `09cf6e820294976a208272713176a87f056fe4a3da082cb88bc961ff867a53c7` |

Traces and rendered images are retained in the `sakura/` and `jinye/` subdirectories. Original Flash StartSound capture for Sakura is coordinated separately with the shared source-tag observer; this report does not close audio acceptance.
