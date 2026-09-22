# Byakuya frame333 GUI HUD rerender r09

This rerender includes the source nested timeline under qt frame 301:
`DefineSprite_1763` has ten looping frames; frames 1-4 are red and frames
5-10 are yellow. The fixed tick fixture reaches child frame 10 at source
frame333, matching the native observation. P1/P2 wrapper mapping remains
P1=1782/nn1/bss1781 and P2=1774/nn2/bss1773.

The nested frames are exported by `build_energy_presentation.py` into
`godot/generated/main/energy/qt-nested/` and advanced by the HUD's source
child lifecycle. This focused GUI evidence does not claim timer parity.
