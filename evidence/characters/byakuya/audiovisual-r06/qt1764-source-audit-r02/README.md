# DefineSprite 1764 source audit r02

This is a read-only audit of the locked FFDec XML export. It does not modify `game/`, `scripts/`, HUD runtime code, or the importer.

## Source input

- XML: `/private/tmp/qt-audit/main.xml`
- SWF source: `game/main.swf`
- XML SHA-256: recorded in `source-sha256.txt`
- `DefineSprite_1764`: 301 `ShowFrameTag` entries
- `DefineSprite_1763`: 10 `ShowFrameTag` entries

## DefineSprite_1764 references and replacements

- Frame 1: depth 1 = 1754 (morph, RGB 41/170/231); depth 4 = 1756.
- Frames 2..100: depth 1 updates morph ratio.
- Frame 101: remove depth 1 (1754); place depth 1 = 1757 (RGB 41/170/231); place depth 2 = 1757.
- Frame 102: remove depth 2 (1757); place depth 2 = 1758 (morph, RGB 41/230/161).
- Frames 103..200: depth 2 updates morph ratio.
- Frame 201: remove depth 2 (1758); move/replace depth 1 = 1759 (RGB 41/230/161); place depth 2 = 1759.
- Frame 202: remove depth 2 (1759); place depth 2 = 1760 (morph, RGB 230/41/50).
- Frames 203..299: depth 2 updates morph ratio.
- Frame 300: remove depth 2 (1760); place depth 2 = 1761 (RGB 230/41/50).
- Frame 301: remove depth 2 (1761); place depth 2 = 1763 with ratio 300.

The direct reference set in 1764 is `{1754, 1756, 1757, 1758, 1759, 1760, 1761, 1763}`. Symbol 1762 is referenced by nested sprite 1763, not directly by 1764.

## Nested DefineSprite_1763

- Frame 1: depth 1 = 1761, RGB 230/41/50.
- Frame 5: move/replace depth 1 from 1761 to 1762, RGB 230/210/43.
- Frames 6..10: no further PlaceObject/RemoveObject changes.
- No DoActionTag or stop action exists inside 1763.

This establishes a real nested MovieClip and a source red-to-yellow transition. The observer's `instance416/417,currentframe=10` labels are instance paths emitted by `aiVisualWalk`; they are not character IDs. The observer reads `_currentframe`, then calls `stop()`, and recursively visits children whose AS2 type is `movieclip`.

## Correction

An earlier audit incorrectly concluded that 1764 had no nested MovieClip and treated observer instance numbers as source symbol IDs. That conclusion is withdrawn. The source XML proves nested sprite 1763 and its 10-frame timeline. This audit does not by itself assert how a static exporter handles the nested playhead; that remains an implementation/runtime question.
