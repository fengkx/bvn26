# HUD geometry source audit r01

Read-only extraction from the locked FFDec XML `/private/tmp/qt-audit/main.xml`; no HUD/runtime/importer files were edited.

## Raw bounds (twips)

- DefineShape2 1748: `Xmin=0, Xmax=3820, Ymin=0, Ymax=1220` (191.0 x 61.0 px at 20 twips/px).
- DefineShape 1756: `0..2800, 0..360` (140.0 x 18.0 px).
- DefineShape 1759: `6..2806, 0..360` (140.0 x 18.0 px; 6-twip left origin).
- DefineShape 1762: `0..2800, 0..360` (140.0 x 18.0 px).
- DefineShape 1772 (final frame of sprite 1773): `Xmin=-13, Xmax=487, Ymin=0, Ymax=760` (25.0 x 38.0 px).
- DefineShape 1780 (final frame of sprite 1781): `0..480, 0..760` (24.0 x 38.0 px).

## Relevant source placements

- Sprite 1774 places 1748 at `(874,-80)`, 1764 at `(1674,580)`, and sprite 1773 at `(1094,160)`.
- Sprite 1782 places 1748 at `(874,-80)`, 1764 at `(1674,580)`, and sprite 1781 at `(1094,160)`.
- Sprite 1815 frame 1 places sprite 1774 at `scaleX=-0.6065521, scaleY=0.6065521, translate=(12658,8049)` and sprite 1782 at `scaleX=0.6065521, scaleY=0.6065521, translate=(-651,8049)`.
- Sprite 1815 frame 1 also places 1814 at `scaleX=scaleY=1.3007812, translate=(121,-1782)`.
- The root placement of 1815 is named `xuetiao`, depth 71, ratio 55, matrix `translate=(-22,40)` with no scale/rotation.

## Conversion

Use the source RECT endpoints in twips, apply each placement MATRIX as an affine transform, then convert the final bounds by dividing coordinates by 20. Do not infer PNG origin or offsets from nominal image dimensions. Sprite 1764 frame 301 has depth 1 shape 1759 and depth 2 sprite 1763; its raw content extent is `X=6..2806, Y=0..360` before its parent matrix. The generated `qt/301.png` is 141x18, which is an export raster size and does not replace the source bounds.
