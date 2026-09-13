# Rukia base frame 1 source/render reference r01

The locked source is `game/fighter/rukia.swf`, SHA-256
`c48d47a817dbf1b4fff9b333bb35d89debb64d0635e8d88b4a7d1228208194eb`. Root sprite 533 frame 1
places sprite 14 at depth 27; sprite 14 frame 1 contains only source shape 7, whose bounds are
31×47 pixels. `source/shape-7.svg` is the direct JPEXS FFDec 26.2.1 shape export. The PNG
`source/shape-7-reference.png` is a raster reference of that exported SVG, not a full Flash
runtime screenshot.

`godot/frame-1.png` is the non-headless Godot 4.7.2 macOS renderer capture from
`godot/tests/source_audiovisual_probe.gd`; it renders the generated Rukia fighter at the probe's
explicit position in a 1280×720 viewport. The trace is `godot/trace.json`. The two images show the
same source-defined shape in different compositions and scales; this is a finite shape/pose check,
not a pixel-aligned comparison or complete presentation-parity claim.

SHA-256 values:

| File | SHA-256 |
|---|---|
| `source/shape-7.svg` | `aa08331c1f16caf2f397cc1d03afda4dee3defe93a59f54bc4c670e4a2009792` |
| `source/shape-7-reference.png` | `55591cb98c4e17cfaa6db463722208a0a358ad010e5d0476fe79817f151a5c4b` |
| `godot/frame-1.png` | `c5b415513fcc9b214ad5488e80e21fe7b8af070e62b453e97ca33bbf5261da27` |
| `godot/trace.json` | `e13325997636487dfc2cc845c1e3d1dcbc1f6bb5230f00b77490abca4c050da5` |
