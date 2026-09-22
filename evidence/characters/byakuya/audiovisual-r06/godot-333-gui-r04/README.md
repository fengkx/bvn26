# Byakuya frame333 GUI HUD rerender

This is the current GUI rerender after the source-bound energy HUD fix. The
fixture is the same dual-soul frame333 scene as r02. The source HUD root is
`game/main.swf:DefineSprite_1815/frame_1`; source load mapping is P1 character
1782 at depth 17 with matrix `(0.6065521,0.6065521,-651,8049)` and P2
character 1774 at depth 1 with matrix `(-0.6065521,0.6065521,12658,8049)` in
twips. P1 uses bss 1781 and P2 uses bss 1773.

The meter artwork is drawn with the source child placements from
`godot/generated/main/energy/presentation.json`. P2 reverses only the meter
artwork toward the centre; its authored `bss-p2` stock clip remains upright,
so the counter is not double-flipped. The latest ql sample is displayed on
the source-derived 300 ms cadence.

Capture command:

```text
/private/tmp/godot-4.7.2/Godot.app/Contents/MacOS/Godot --path godot -s res://tests/byakuya_visual_capture.gd -- 333 /private/tmp/byakuya-godot-333-gui-r04
```

This is focused Godot HUD evidence. It does not claim full native visual
parity; the source timer is 60 while this fixture reports Godot timer 59 and
the remaining wall-clock/placement phase is still outside this HUD fix.
