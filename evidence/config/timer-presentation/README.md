# Source timer presentation wiring

This supersedes the earlier duplicate-overlay-only diagnosis. The black HUD symbol was hardcoded to shape 1812 even in finite matches; the separate white Label was the only display following the actual countdown.

Source-first evidence: `DefineSprite_1813/frame_1/DoAction.as` stops the parent timeline, selects 无限时 for unlimited/training, or starts the 1000 ms callback. That callback selects `十` and `个` using digit+1. The new placements at parent frame 1 are two Sprite 1810 instances at authored offsets 33 and 408 twips; frame 10 replaces them with shape 1812. Parent frames 2–9 have no actions or placement changes. Sprite 1810 stops on frame 1, and its ten frames select shapes 1800–1809; its other frames contain no actions. Finite initial digits therefore retain frame 1 until the first callback. The existing original Config/timeout recordings retain the same source controller and timing behavior.

The importer now extracts both timer display lists, every digit frame, shape bounds and original raster assets. MatchCountdown is a nonvisual Node; its source-compiled goto_clip calls update the two digit frames. HealthHud renders these at the original nested placements and redraws after each callback. No timing, pause, energy or combat rule changed.

Native regression covers initial digits, 30→29, paused 29, every decrement through 10→09 and 01→00, timeout, unlimited and training. Actual Godot screenshots show 10, 09 and the unlimited symbol with no extra font overlay. This validates this presentation repair, not full combat parity.
