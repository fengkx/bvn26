# HUD geometry audit r01

This audit compares the locked source metadata with the current Godot HUD without changing production code.

The root `xuetiao` placement is present in the exported source XML at depth 71: it places `DefineSprite_1815` at `(-22,40)` twips with no root scale. `DefineSprite_1815/frame_1` then places the energy wrappers `1782/1774` with authored scales `+/-0.6065521`; it separately places HP container `1814` at scale `1.3007812`.

The generated `191x61` value is the bounds of background symbol `1748`, not the complete `1774/1782` composite. Recursive first-frame union from the locked XML gives both wrappers `[-4,-4,234.7,57]` pixels, or `238.7x61`. After the authored outer scale this is about `144.80x37.00` pixels. The source helper border uses a `44x61` texture and a `23x20` matrix; applying the energy wrapper scale to that pair gives about `30.69x37.00` pixels.

The current `godot/energy_bar.gd` uses a separate `0.5x0.5` helper transform, which produces about `25.30x30.50` pixels. `godot/main.tscn` also gives each energy Control a `134x32` layout box. These are concrete geometry differences consistent with the source and current screenshots.

The source `1774/1782` scripts only schedule `qitiao` every 300 ms and select `qt/bss` frames; the inspected scripts do not reset wrapper scale dynamically. The current helper uses a separate `0.5x0.5` Godot transform, which is a real transform difference, but the production fix remains pending until the complete child union and root-to-stage mapping are compared. The JSON records the XML hash and the exact acceptance boundary.
