# Sasuke/You vs Renji overlap fix r01

This focused production replay covers the user-reported Sasuke + You versus Renji
simultaneous Up+I and Up+U overlap. The public scheduler now advances helper
root timelines before fighter timelines in `_advance_fight`, preserving the
shared reverse registration dispatch. No character-specific branch, hitbox
fallback, delay, or registry sort change was added.

Commands (Godot 4.7.2 stable `ed1daf0bf`):

```sh
/private/tmp/godot-4.7.2/Godot.app/Contents/MacOS/Godot --headless --path godot -s res://tests/move_case_reference.gd --quit-after 1400 -- <fixture> <native.json>
python3 tools/probes/compare_mode_reference.py <source-events.jsonl.gz> <native.json> --output <fighter.json>
python3 tools/probes/compare_helper_reference.py <source-events.jsonl.gz> <native.json.helpers.json> --output <helper.json>
```

Both fixtures use the existing fixed source inputs under `renji-overlap-upI-r01`
and `renji-overlap-upU-r01`; those original red inputs and source events are
preserved. Each mode compares 602 fighter states and 602 helper rows with zero
differences. The former upI first difference at tick 63 is gone. Focused
`helper_pause_semantics`, `vs_com_helper_overlap`, `you_helper_callback_order`,
`source_repeat_contact_smoke`, `ai_hit_pause_smoke`, and
`tools/test_helper_super_overlap.py --godot ...` also pass.

This closes only the two reported overlap controls. Full character matrix,
visual/audio/Web parity, and SOP step E remain pending.

## Production hash

`godot/main.gd`: `829a3204758d7431f4da16f3eaef3d98f216cee4c1f889c6065d4b159a36027f`

## Focused You miss/hit and shared modes

Replayed against the preserved original source captures:

- You hit: 482 fighter states and 482 helper rows matched (`native-probe-you-r03.events.jsonl.gz`), using the reconstructed neutral fixture at x=350.
- You far miss: 362 fighter states and 362 helper rows matched (`native-probe-you-miss-far-r02.events.jsonl.gz`), using the preserved miss setup at x=800.
- `python3 tools/test_shared_modes.py --godot /private/tmp/godot-4.7.2/Godot.app/Contents/MacOS/Godot` passed both `pvp` and `training-timer` at 602 actor states; stdout is archived as `shared-modes.log`.

The reconstructed fixtures preserve the source probe setup (Sasuke + You,
You summon on ticks 10..13, 240-frame hit / 180-frame far miss windows). These
focused cases do not expand the full character matrix.

The source callback order and undefined-target observation supporting the overlap
fix are archived in [upI order r05](../renji-overlap-upI-order-r05/README.md).
