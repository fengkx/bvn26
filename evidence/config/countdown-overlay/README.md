Superseded by [the timer presentation repair](../timer-presentation/README.md): the finite countdown also needed the source digit assets wired to its state.

# Duplicate unlimited-time overlay

The HUD already draws the original bitmap 1812 at the authored timer placement (`HealthHud._draw`, `generated/main/health/presentation.json`). `MatchCountdown` also drew a font infinity at (267, 12), leaving a white upper arc visible above the bitmap.

The source `DefineSprite_1813/frame_1/DoAction.as` stops its timer timeline and selects 无限时 for maxtime=100 or mode=4; it does not add a second label. The existing source bitmap and its placement are retained. Only the duplicate Godot Label is hidden and emptied for those modes. The finite counter and source timer callbacks are unchanged; no clip placement or exit rule changes.

`config_flow_smoke.gd` passes: the 30-second label remains visible, and both unlimited and training modes hide the extra label and keep no timer. The original asset was visually inspected against the supplied screenshot. This is a duplicate-overlay repair, not full timer presentation acceptance.
